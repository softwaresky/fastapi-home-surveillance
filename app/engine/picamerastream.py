from picamera.array import PiRGBArray
from picamera import PiCamera

class PiVideoStream:

    def __init__(self, resolution=(320, 240), framerate=32, **kwargs):
        # initialize the camera
        self.camera = PiCamera()

        # set camera parameters
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.camera.vflip = True
        self.camera.hflip = True

        # set optional camera parameters (refer to PiCamera docs)
        for (arg, value) in kwargs.items():
            setattr(self.camera, arg, value)

        # initialize the stream
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)

    def start(self):
        self.camera.start_preview()

    def read(self):
        f = next(self.stream)
        self.rawCapture.truncate(0)
        return f.array

    def stop(self):
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()
