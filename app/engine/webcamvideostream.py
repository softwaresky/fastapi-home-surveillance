import cv2


class WebcamVideoStream:

    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src)
        self.stopped = False

    def read(self):

        while True:

            if self.stopped:
                return

            grabbed, frame = self.stream.read()
            yield frame

    def close(self):
        pass
