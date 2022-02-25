from picamera.array import PiRGBArray
from picamera import PiCamera
from threading import Thread


class PiVideoStream:

	def __init__(self, resolution=(320, 240), framerate=32, **kwargs):
		# initialize the camera
		self.camera = PiCamera()

		# set camera parameters
		self.camera.resolution = resolution
		self.camera.framerate = framerate

		# set optional camera parameters (refer to PiCamera docs)
		for (arg, value) in kwargs.items():
			setattr(self.camera, arg, value)

		# initialize the stream
		self.rawCapture = PiRGBArray(self.camera, size=resolution)
		self.stream = self.camera.capture_continuous(self.rawCapture,
			format="bgr", use_video_port=True)

		# initialize the frame and the variable used to indicate
		# if the thread should be stopped
		self.frame = None
		self.stopped = False

	def start(self):
		# start the thread to read frames from the video stream
		self.camera.start_preview()

		# t = Thread(target=self._update, args=())
		# t.daemon = True
		# t.start()
		# return self

	def _update(self):
		# keep looping infinitely until the thread is stopped

		for f in self.stream:
			# grab the frame from the stream and clear the stream in
			# preparation for the next frame
			self.frame = f.array
			self.rawCapture.truncate(0)

			# if the thread indicator variable is set, stop the thread
			# and resource camera resources
			if self.stopped:
				self.stream.close()
				self.rawCapture.close()
				self.camera.close()
				return

	def read_old(self):
		return self.frame

	def read(self):
		f = next(self.stream)
		print (len(self.stream))
		self.rawCapture.truncate(0)
		return f.array

	def stop(self):
		self.stream.close()
		self.rawCapture.close()
		self.camera.close()