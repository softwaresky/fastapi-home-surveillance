import cv2

class WebcamVideoStream:

	def __init__(self, src=0, resolution=(320, 240)):

		# initialize the video camera stream and read the first frame
		# from the stream
		self.stream = cv2.VideoCapture(src)
		self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
		self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

	def start(self):
		_, frame = self.stream.read()
		pass


	def read(self):
		# return the frame most recently read
		_, frame = self.stream.read()
		# cv2.flip(frame, 0)
		return cv2.flip(frame, -1)

	def stop(self):
		# indicate that the thread should be stopped
		self.stream.release()