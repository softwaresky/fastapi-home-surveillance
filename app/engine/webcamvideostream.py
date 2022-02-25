import cv2

class WebcamVideoStream:

	def __init__(self, src=0):

		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)

	def start(self):
		_, frame = self.stream.read()
		pass


	def read(self):
		# return the frame most recently read
		_, frame = self.stream.read()
		return frame

	def stop(self):
		# indicate that the thread should be stopped
		self.stream.release()