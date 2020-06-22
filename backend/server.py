from app import *
from flask import request, render_template, jsonify, Response
import argparse
import json
import os
from scripts import *
import time
import cv2
import platform
import webbrowser
from math import inf

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/settings/')
def settings():
	return render_template('settings.html')

@app.route('/create/', methods=['GET', 'POST'])
def create():
	if request.method == "GET":
		return render_template('create.html')
	if request.method == "POST":
		name = request.form['name']
		num_pages = int(request.form['number'])
		# To Do: construct name.json of length number and update global templates
		return render_template('annotate.html', name=name, num_pages=num_pages)


@app.route('/new_form/', methods=['POST', 'GET'])
def new_form():
	if request.method == 'POST':
		files = request.files.getlist("file")
		pages_to_send_back = []
		encoder = FormTemplateEncoder()
		for page_num, file in enumerate(files, start=1):
			# 1) Construct a name/path for the file
			timestamp = "_" + str(time.time())
			page_name = "page_" + str(page_num) + timestamp + ".jpeg"
			upload_location = str(Path.cwd() / "backend" / "static" / page_name)
			# 2) Save the file to that path
			file.save(upload_location)
			# 3) Create an Form object to send back to the frontend
			# TODO (sud): parametrize the form_name
			form_name = "new-form" + "_page_" + str(page_num)
			(x, y) = util.get_image_dimensions(upload_location)
			processed_form = Form(form_name, page_name, y, x, [QuestionGroup()])
			encoded_form = encoder.default(processed_form)
			pages_to_send_back.append(encoded_form)
	return json_status("success", pages=pages_to_send_back)

# To Do: Remove file_path from the upload.  That way new form is just needing
# name and num_pages.  We will do standard function from name => file_path (i.e. lower-case
# and replace spaces with hyphens).
@app.route('/upload/<form>', methods=['GET', 'POST'])
def upload(form):
	template = templates[form]
	name = template["name"]
	num_pages = len(template["pages"])
	return render_template('upload.html', name=name, num_pages=num_pages, file_path=form)

@app.route('/save/<file>', methods=['POST'])
def save_response(file):
	try:
		# NOTE: form is an array of jsons
		# TODO: write_form_to_csv should take in a file name (ex. delivery) and an array of jsons
		# and should append a row to file.csv with concatenated jsons from array.
		loaded_json = json.loads(request.data)
		decoded_form = decode_form(loaded_json)
		write_form_to_csv(decoded_form, file)

		# now that we saved this form we need a new unique identifier for the next form
		if app.config["SAVE_DEBUG"]:
			app.config["DEBUG_WRITE_ID"] += 1

		return jsonify(status='success')
	except AlignmentError as err:
		return jsonify(error_msg=err.msg, status='error')


def camera_index():
	# camera indexing is 0 on Macs 1 otherwise
	return 0 if platform.system() == "Darwin" else 1

# Capture live stream via OpenCV
# TODO: (sud) select video feed based on selection on frontend
# class Camera(object):
#     def __init__(self):
#
#         # with capture_stdout() as output:
#         #camera_index()
#         # CAP_DSHOW is ** VERY IMPORTANT ** for ensuring that the frames from
#         # the camera are pulled in at maximum resolution
#         # DO NOT remove without testing extensively first
#         cap = cv2.VideoCapture(0) # , cv2.CAP_DSHOW
#         time.sleep(2) # Wait a couple seconds for the campera to connect
#         assert cap.isOpened(), "Failed to connect to OpenCV. Could not connect to Camera"
#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2000)
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2000)
#         test, frame = cap.read()
#         cv2.imwrite("test_frame.jpg", frame)
#         # print("Cam Connection Test Passed: " + str(test))
#         print('Resolution: ' + str(frame.shape[0]) + ' x ' + str(frame.shape[1]))
#         self.stream = cap

_input = 0
def write_prediction(image, align_score, blurry_score):
	global _input
	cv2.imwrite("./_input" + str(_input) + "_align_" + str(align_score) + "_blur_" + str(blurry_score) + ".png", image)
	_input += 1


def json_status(status_str, remaining_frames="", pages=None):
	pages = pages if pages is not None else []
	resp = {}
	resp["status"] = status_str
	resp["remaining_frames"] = remaining_frames
	resp["pages"] = pages
	return jsonify(resp)

def reset_globals():
	global good_frames_captured
	global best_aligned_image
	global best_align_score
	good_frames_captured = 0
	best_aligned_image = None
	best_align_score = inf
	return None


def get_image_from_request(request, page_number=0):
	file = request.files.getlist("file")[page_number]
	# 1) Construct a name/path for the file
	timestamp = "_" + str(time.time())
	page_name = "page_" + str(page_number) + timestamp + ".jpeg"
	upload_location = str(Path.cwd() / "backend" / "static" / page_name)
	# 2) Save the file to that path
	file.save(upload_location)
	# 3) Read in the image using OpenCV
	image = util.read_image(upload_location)
	return (upload_location, image)


def write_debug_stream_image(form_name, page_number, image):
	# generate a unique ID for the current stream of images if it doesnt already exist
	out_folder = get_output_folder()
	if "DEBUG_WRITE_ID" not in app.config:
		debug_id = 0
		while os.path.isdir(out_folder + "/" + form_name + "_" + str(debug_id)):
			debug_id += 1
		app.config["DEBUG_WRITE_ID"] = debug_id

	directory_name = out_folder + "/" + form_name + "_" + str(app.config["DEBUG_WRITE_ID"])
	if not os.path.isdir(directory_name):
		os.mkdir(directory_name)

	# generate a unique ID for the current image in the stream
	stream_id = 0
	while True:
		file_name = directory_name + "/" + "page_" + str(page_number) + "_stream_" + str(stream_id) + ".jpeg"
		if not os.path.isfile(file_name):
			break
		stream_id += 1

	cv2.imwrite(file_name, image)


@app.route('/check_alignment/<form_name>/<page_number>', methods=['GET', 'POST'])
def check_alignment(form_name, page_number):
	global vs
	global cam
	global sec_btw_captures
	global good_frames_captured
	global good_frames_to_capture_before_processing
	global best_aligned_image
	global best_align_score

	time.sleep(sec_btw_captures) # wait before processing frame

	template = templates[form_name]["pages"][int(page_number)]
	template_image = template.image
	if isinstance(template_image, str):
		template_image = util.read_image(template_image)

	assert template_image is not None

	if request.method == "GET":
		# Grab a frame from the live camera feed
		#_, frame = cam.stream.read()
		frame = vs.read()
		cv2.imwrite("frame.jpg", frame)
	else:
		# Parse the request for an uploaded file
		_, frame = get_image_from_request(request, int(page_number))
		reset_globals()

	if app.config["SAVE_DEBUG"]:
		write_debug_stream_image(form_name, int(page_number), frame)

	try:
		start = time.time()
		aligned_image, aligned_diag_image, h, align_score = align.align_images(frame, template_image)

		is_blurry, blurry_score = compute_blurriness(aligned_image)
		# Uncomment to write out image with align_score & blurry_score
		# write_prediction(aligned_image, align_score, blurry_score)
		if is_blurry:
			good_frames_captured = 0
			print("Too blurry", blurry_score)
			return json_status("unaligned")

		if not is_blurry:
			good_frames_captured = good_frames_captured + 1
			# because it is difficult to combine alignment & blurriness
			# into one heuristic just use best alignment score for now.
			if align_score < best_align_score:
				best_align_score = align_score
				best_aligned_image = aligned_image

			if (request.method == "GET") and (good_frames_captured < good_frames_to_capture_before_processing):
				num_remaining_frames = good_frames_to_capture_before_processing - good_frames_captured
				remaining_frames_str = str(num_remaining_frames - 1) if num_remaining_frames != 1 else "Processing..."
				return json_status("aligned", remaining_frames=remaining_frames_str)
			else:
				# Run mark recognition on aligned image
				answered_questions, clean_input = omr.recognize_answers(best_aligned_image, template_image, template)
				# Write output
				aligned_filename = util.write_aligned_image("original_frame.jpg", aligned_image)
				# Create Form object with result, and JSONify to be sent to front end
				processed_form = Form(template.name, aligned_filename, template.w, template.h, answered_questions)
				encoder = FormTemplateEncoder()
				encoded_form = encoder.default(processed_form)
				encoded_form['status'] = "success"
				end = time.time()
				print("\n\n\n It took %.2f to run the process script." % (end - start))
				# Reset the global counters
				reset_globals()
				return jsonify(encoded_form)

	except AlignmentError:
		reset_globals()
		# Uncomment the line below for live alignment debug in console
		print("Alignment Error!")
		return json_status("unaligned")

def upload_all_templates():
	# Populate the "templates" and "template_images" Python dictionaries with
	# modeled Python "Form" objects
	global templates

	# TODO: loop through all files *.json from forms/json_annotations
	for file in ["delivery", "antenatal", "covid", "admission"]:
		path_to_json_file = str(Path.cwd() / "backend" / "forms" / "json_annotations" / (file + ".json"))
		templates[file] = read_multipage_json_to_form(path_to_json_file)

# Set up global variables
#cam = Camera()
sec_btw_captures = 1
good_frames_captured = 0
good_frames_to_capture_before_processing = 3
best_aligned_image = None
best_align_score = inf # lower alignment score is better
templates = {}

##### Video Streaming Code ###
# import the necessary packages
from threading import Thread
import threading
import numpy as np

class WebcamVideoStream:
	def __init__(self, src=0, name="WebcamVideoStream"):
		# initialize the video camera stream and read the first frame
		# from the stream
		cap = cv2.VideoCapture(src)
		# TODO: here we up the resolution of frames that are taken in.
		# A high resolution is necessary for the alignment to work, but
		# this slows down the streaming process. We should find a way to
		# stream lower quality pictures to the front-end, but also pull in
		# high quality versions for alignment/processing on the backend.
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, 11111)
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 11111)
		self.stream = cap
		(self.grabbed, self.frame) = self.stream.read()

		# initialize the thread name
		self.name = name

		# initialize the variable used to indicate if the thread should
		# be stopped
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, name=self.name, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			time.sleep(.01)

			# if the thread indicator variable is set, stop the thread
			if self.stopped:
				return

			# otherwise, read the next frame from the stream
			(self.grabbed, self.frame) = self.stream.read()

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stopped = True



vs = WebcamVideoStream(src=1).start()
time.sleep(2.0)

def generate():
	# grab global references to the output frame and lock variables
	global vs
	# loop over frames from the output stream
	while True:
		frame = np.rot90(vs.read())
		resized = cv2.resize(frame, (720, 1280), interpolation = cv2.INTER_AREA)
		# frame = vs.read()
		# frame = imutils.resize(frame, width=400)
		(flag, encodedImage) = cv2.imencode(".jpg", resized)

		# frame = imutils.resize(frame, width=400)
		# # wait until the lock is acquired
		# with lock:
		# 	# check if the output frame is available, otherwise skip
		# 	# the iteration of the loop
		# 	if outputFrame is None:
		# 		continue
		# 	# encode the frame in JPEG format
		# 	(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
		# 	# ensure the frame was successfully encoded
		# 	if not flag:
		# 		continue
		# yield the output frame in the byte format
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
			bytearray(encodedImage) + b'\r\n')


@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")
##### End Video Streaming Code ###

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('--port', nargs='?', const=1, type=int, default=8000)
	parser.add_argument('--upload_folder', nargs='?', const=1, default=None)
	parser.add_argument('--save-debug', dest='save_debug', action='store_true')
	parser.set_defaults(save_debug=False)
	args = parser.parse_args()
	if args.upload_folder:
		app.config['UPLOAD_FOLDER'] = str(args.upload_folder)
	app.config["SAVE_DEBUG"] = args.save_debug

	upload_all_templates()

	webbrowser.open('http://localhost:' + str(args.port))
	app.run(host='0.0.0.0', port=args.port)
