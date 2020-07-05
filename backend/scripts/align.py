import cv2
import numpy as np
from .util import *

MAX_FEATURES = 5000
GOOD_MATCH_PERCENT = 0.22
AVG_MATCH_DIST_CUTOFF = 47 # Lower cutoff is more strict
FPL = 5 # Finetune pixel limit; max number of pixels to finetune region locations


class AlignmentError(Exception):
	"""Raised when alignment error is too high"""
	def __init__(self, msg):
		self.msg = msg

def global_align(im1, im2):
	"""
	Args:
		im1 (numpy.ndarray): image to align
		im2 (numpy.ndarray): template image
	Returns:
		im1reg (numpy.ndarray): aligned version of im1
		im_matches (numpy.ndarray): debug image showing the common features used for alignment
		h (numpy.ndarray): matrix describing homography
		align_score (float): average max distance, lower is better
	"""

	assert isinstance(im1, np.ndarray) and isinstance(im2, np.ndarray)

	# 1) Instantiate CV2 alignment objects
	orb = cv2.ORB_create(MAX_FEATURES)
	matcher = cv2.DescriptorMatcher_create(cv2.DESCRIPTOR_MATCHER_BRUTEFORCE_HAMMING)
	# 2) Compute key points, descriptors, and matches for im1 and im2
	key_points_1, descriptors_1 = compute_descriptors(im1, orb)
	key_points_2, descriptors_2 = compute_descriptors(im2, orb)
	(matches, avg_match_dist) = compute_matches(descriptors_1, descriptors_2, matcher)
	# 3) Validate the matches for quality
	if avg_match_dist > AVG_MATCH_DIST_CUTOFF:
	    print("Average match distance of %d exceeds match distance cutoff of %d." \
			% (avg_match_dist, AVG_MATCH_DIST_CUTOFF))
	    raise AlignmentError("GLOBAL ALIGNMENT WARNING: Poor image alignment!\n\
	    Please confirm you are using the right form, and upload a new image.")
	# 4) Use the matches to compute + apply the homography
	(im1_warp, h) = compute_and_apply_homography(im1, im2, key_points_1, key_points_2, matches)
	# 5) Check homography for improvement
	key_points_warp, descriptors_warp = compute_descriptors(im1_warp, orb)
	(_, avg_match_dist_warp) = compute_matches(descriptors_warp, descriptors_2, matcher)
	if avg_match_dist_warp > avg_match_dist: 
		# The perspective warp reduced the average match quality OR "the original image was shit" -Dan
		raise AlignmentError("Poor image alignment! Applying homography reduced \n \
		the alignment score. Please confirm camera image quality.")
	# 6) Finally, draw top matches (for debug purposes)
	drawn_matches = cv2.drawMatches(im1, key_points_1, im2, key_points_2, matches, None)

	return im1_warp, drawn_matches, h, avg_match_dist


def local_align(im1, im2, form):
	"""
	Aligns each question group of the form individually, and puts all of the regions
	together for final output 
	Args:
		im1 (numpy.ndarray): image to align
		im2 (numpy.ndarray): template image
	Returns:
		im_aligned (numpy.ndarray): locally aligned version of im1
	"""

	# Project mark locations from template onto input image
	project_mark_locations(im2[:,:,0], form)
	# Initialize an empty numpy array to fill in with locally aligned regions
	im_aligned = np.zeros_like(im2, dtype=np.uint8)
	# Loop through every question group and align the corresponding regions of
	# im1 and im2 
	for group in form.question_groups:
		# Get question group regions
		w, h, x, y = (group.w, group.h, group.x, group.y)
		im1_region = im1[y:y+h, x:x+w,:]
		im2_region = im2[y:y+h, x:x+w,:]
		# Align the two regions using the global_align funciton
		try:
			(im_warp, _, _, _) = global_align(im1_region, im2_region)
		except AlignmentError:
			raise AlignmentError("GLOBAL ALIGNMENT WARNING: Error in Local Alignment.")
		# Write the aligned region into the final output image
		im_aligned[y:y+h, x:x+w,:] = im_warp

	return im_aligned


def finetune(input_image, template_image, response_region):
	"""
	Args:
		input_image (numpy.ndarray): target image
		template_image (numpy.ndarray): template image
		response_region (ResponseRegion): describes location of checkbox
	Returns:
		mutates response region x and y attritibute to account for translation
	"""

	alpha = 0.5
	w, h, x, y = (response_region.w, response_region.h, response_region.x, response_region.y)
	x_offset, y_offset = int(alpha * w), int(alpha * h)
	crop = template_image[max(0,y-y_offset//2) : y+h+y_offset//2, max(0,x-x_offset//2) : x+w+x_offset//2]
	ref = input_image[max(0,y-y_offset) : y+h+y_offset, max(0,x-x_offset) : x+w+x_offset]

	res = cv2.matchTemplate(crop, ref, cv2.TM_CCOEFF_NORMED)
	_, _, min_loc, max_loc = cv2.minMaxLoc(res)

	# Compute the number of pixes to finetune in the x and y dimensions
	finetune_x = max_loc[0] - x_offset//2
	finetune_y = max_loc[1] - y_offset//2
	# Finetune response region coordinates, within pixel limit
	# I.e. finetune_x or finetune_y exceed FPL, adjust by FPL. This avoids gross adjustments
	# in the location of checkboxes at this stage in the alignment process. 
	response_region.x += max(-FPL, min(finetune_x, FPL))
	response_region.y += max(-FPL, min(finetune_y, FPL))


#########################################
### Helper Functions for global_align ###
#########################################
def compute_descriptors(im, orb):
	"""Compute descriptors and key points for input image

	Args:
		im (numpy.ndarray): image to align
		orb (CV2 ORB object): object to detect and compute features
	Returns:
		key_points(List[KeyPoint]): key points in im
		descriptors(List[Descriptor]): descriptors of features in im
	"""
	# Convert images to grayscale
	im_gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
	# Compute key points and descriptors
	key_points, descriptors = orb.detectAndCompute(im_gray, None)
	return (key_points, descriptors)

def compute_matches(descriptors_1, descriptors_2, matcher):
	""" Compute matches based on two sets of descriptors

	Args:
		descriptors_1 (List[Descriptor]): descriptors for im1
		descriptors_2 (List[Descriptor]): descriptors for im2
		matcher (CV2 Matcher object): object to compute matches

	Returns:
		matches (List[CV2 Match object])
		avg_match_dist (Int)
	"""
	# Match features
	matches = matcher.match(descriptors_1, descriptors_2, None)
	# Sort matches by score
	matches.sort(key=lambda x: x.distance, reverse=False)
	# Remove not so good matches
	num_good_matches = int(len(matches) * GOOD_MATCH_PERCENT)
	matches = matches[:num_good_matches]
	# Validate the matches for quality
	match_distances = [m.distance for m in matches]
	avg_match_dist = np.median(match_distances)
	return (matches, avg_match_dist)

def compute_and_apply_homography(im1, im2, key_points_1, key_points_2, matches):
	"""Compute and apply homography based on key points and matches between im1 and im2

	Args:
		im1 (numpy.ndarray): image to align
		im2 (numppy.ndarray): template image
		key_points_1 (List[KeyPoints]): key points for im1
		key_points_2 (List[KeyPoints]): key points for im2
		matches (List[CV2 Match object]): list of Matches

	Raises:
		AlignmentError: Computing the homography resulted in an alignment error

	Returns:
		im1_warp [numpy.ndarray]: im1 with homography applied
		h [numpy.ndarray]: matrix describing homography
	"""
	# Extract location of good matches
	points_1 = np.zeros((len(matches), 2), dtype=np.float32)
	points_2 = np.zeros((len(matches), 2), dtype=np.float32)
	for i, match in enumerate(matches):
		points_1[i, :] = key_points_1[match.queryIdx].pt
		points_2[i, :] = key_points_2[match.trainIdx].pt
	# Find homography
	try:
		h, mask = cv2.findHomography(points_1, points_2, cv2.RANSAC)
	except:
		raise AlignmentError("GLOBAL ALIGNMENT WARNING: Inproper Homography in Alignment!\n \
		Please confirm you are using the right form, and upload a new image.")
	# Apply homography
	height, width, _ = im2.shape
	im1_warp = cv2.warpPerspective(im1, h, (width, height))
	return (im1_warp, h)

