from picamera.array import PiRGBArray
from picamera import PiCamera


class PiCameraStream:

    def __init__(self, resolution=(320, 240), framerate=32, **kwargs):
        # initialize the camera
        self.camera = PiCamera()

        # set camera parameters
        self.camera.vflip = True
        self.camera.hflip = True
        self.camera.resolution = resolution
        self.camera.framerate = framerate

        # set optional camera parameters (refer to PiCamera docs)
        for (arg, value) in kwargs.items():
            setattr(self.camera, arg, value)

        # initialize the stream
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
                                                     format="bgr",
                                                     use_video_port=True)

        self.frame = None
        self.stopped = False

    def read(self):

        for f in self.stream:

            if self.stopped:
                return

            yield f.array
            self.rawCapture.truncate(0)

    def close(self):
        self.stopped = True
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()