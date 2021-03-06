# import the necessary packages
from threading import Thread
import threading
import numpy as np
import cv2
import time

FRAME_RATE = 10 # frames per second

class Camera:
	def __init__(self, src=0, name="Camera"):
		# Initialize the video camera stream
		cap = cv2.VideoCapture(src)
		cap.set(cv2.CAP_PROP_FRAME_WIDTH, 11111)
		cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 11111)
		self.stream = cap

		# Test and Display Initial camera image quality.
		(_, test_frame) = self.stream.read()
		self.width_quality, self.height_quality, _  = test_frame.shape
		print("Camera Image Quality: %i x %i" % (self.width_quality, self.height_quality))

		# Define a "NULL FRAME", which is the frame that the camera defaults
		# to when it is stopped
		self.NULL_FRAME = np.zeros((self.width_quality,self.height_quality,3)).astype(np.uint8)

		# Initialize local variables
		self.name = name # Camera object name
		self.frame = self.NULL_FRAME # Reset frame
		self.stopped = True # Manages camera state
		self.frame_delay = 1 / FRAME_RATE

	def start(self):
		self.stopped = False
		# start the thread to read frames from the video stream
		t = Thread(target=self.update, name=self.name, args=())
		t.daemon = True
		t.start()
		return self

	def update(self):
		# keep looping infinitely until the thread is stopped
		while True:
			# If the thread indicator variable is set, stop the thread
			if self.stopped:
				return
			# Delay based on frame rate
			time.sleep(self.frame_delay)
			# Read the next frame from the stream
			(ret, frame) = self.stream.read()
			if ret:
				self.frame = frame

	def read(self):
		# return the frame most recently read
		return self.frame

	def stop(self, fade_to_black = True):
		# indicate that the thread should be stopped
		self.stopped = True
		# Fade to black, or stop on this frame
		if fade_to_black:
			time.sleep(self.frame_delay)
			self.frame = self.NULL_FRAME


	def close_hardware_connection(self):
		# Close the connection to the camera hardware
		self.stop()
		self.stream.release()

	def stream_quality_preserved(self):
		# Check if the given width and height are greater than or equal to
		# the quality at the time of origination. If not, return False
		current_width, current_height, _ = self.frame.shape
		print("Image Quality: %i x %i" % (current_width, current_height))
		return ((current_width >= self.width_quality) or (current_height >= self.height_quality))
