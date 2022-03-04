import os
import cv2
import numpy as np
import math
import time
import datetime
from collections import deque
from app.engine import utils
from app.engine.base_class import ThreadBase

from .videostream import VideoStream
from .servo_controller import ServoController

class MotionDetector(ThreadBase):

    def __init__(self,
                 camera_source_index: int = 0,
                 observer_length: int = 5,
                 threshold: float = 7.0,
                 force_fps: int = 24,
                 media_dir: str = "",
                 do_record: bool = False,
                 use_other_to_record: bool = False,
                 video_format: str = "mp4",
                 dht_function = None,
                 servo_is_moving = None,
                 servo: ServoController = None):

        super(self.__class__, self).__init__()

        self.name = str(self.__class__.__name__)
        self.log_manager = utils.LogManager(self.name)
        self.media_dir = media_dir

        self.observer_length = observer_length
        self.threshold = threshold
        self.video_capture = None
        self.force_fps = force_fps if force_fps else self.get_fps()
        self._frame_rate = self.force_fps

        self.records = []
        self.do_record = do_record
        self.is_saved = False
        self.video_format = video_format
        self.width, self.height = (640, 480)
        self.current_frame = None
        self.orig_frame = None
        self.current_timestamp = None
        self.video_text = ""
        self.detect_motion = False
        self.writer = None
        self._value = 0.0
        self.current_file = ""
        self.last_file = ""
        self.use_other_to_record = use_other_to_record
        self.force_recording = False
        self.dht_function = dht_function
        self.servo_is_moving = servo_is_moving


        self.stream = VideoStream(src=camera_source_index,
                                  framerate=self.force_fps,
                                  resolution=(self.width, self.height),
                                  use_pi_camera=True)

        self.lst_buffer_data = []
        self.is_running = False

        self.servo = servo

    def __del__(self):

        self.is_running = False

        if self.stream:
            self.stream.stop()
            del self.stream

        if self.video_capture:
            self.video_capture.release()

    def get_fps(self):
        number_of_frames = 60
        start_time = time.time()

        for i in range(number_of_frames):
            frame = self.stream.read()
            if frame is not None:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_blur = cv2.GaussianBlur(frame_gray, (21, 21), 0)

        return number_of_frames / (time.time() - start_time)

    def get_function_kwargs(self):
        return {
            "file_path": self.current_file,
            "width": self.width,
            "height": self.height,
            "records": self.records
        }

    @staticmethod
    def get_video_capture():
        video = cv2.VideoCapture(0)
        time.sleep(0.5)
        return video

    @property
    def value(self):
        return self._value if self._value > 0.0 else 0.0

    def get_frame(self):
        if self.current_frame is not None:
            ret, jpeg = cv2.imencode('.jpg', self.current_frame)
            return jpeg.tobytes()
        return None

    @staticmethod
    def save_video(file_path="", records=[], width=0, height=0):

        if records:

            if not width and not height:
                height, width = records[0][1].shape[:2]

            frame_rate = round(len(records) / (records[-1][0] - records[0][0]))
            zero_timestamp = records[0][0]
            time_step = 1 / frame_rate
            timestamp_value = 0

            # Define the codec and create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Be sure to use lower case
            writer = cv2.VideoWriter(file_path, fourcc, frame_rate, (width, height))

            while timestamp_value <= records[-1][0] - zero_timestamp:
                closest_timestamp_, frame_data_ = min(records,
                                                      key=lambda x: abs((x[0] - zero_timestamp) - timestamp_value))
                writer.write(frame_data_)
                timestamp_value += time_step

            writer.release()

            return True

        return False

    def start_recording(self):

        if not (self.use_other_to_record and self.current_file):
            self.current_file = os.path.join(self.media_dir, f".{utils.get_timestamp()}.{self.video_format}")

        if self.current_file:
            dst_dir = os.path.dirname(self.current_file)

            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            self.log_manager.log("Motion detected! Recording...")

    def stop_recording(self):
        if self.writer and self.writer.isOpened():
            self.writer.release()

        self.writer = None
        self.records = []
        self.last_file = self.current_file
        self.current_file = ""

    def is_recording(self):
        return len(self.records) > 0

    def do_recording(self):
        if (self.use_other_to_record and self.force_recording) or (not self.use_other_to_record and self.detect_motion):

            if not self.is_recording():
                self.start_recording()

            self.is_saved = False
            self.records.append((self.current_timestamp, self.current_frame))

        elif self.is_recording():
            if self.writer and self.writer.isOpened():
                self.writer.release()

            # self._save_video(file_path=self.current_file, records=self.records)
            # MotionDetector.save_video(file_path=self.current_file, records=self.records)
            self.lst_buffer_data.append((MotionDetector.save_video, self.get_function_kwargs()))

            self.stop_recording()
            self.log_manager.log("Observing...")

    def run(self) -> None:

        self.is_running = False

        self.log_manager.log("Camera preparing...")
        self.stream.start()
        time.sleep(2)
        self._frame_rate = self.get_fps()
        self._frame_rate = round(self._frame_rate)
        self.log_manager.log(f"FPS calculated: {self._frame_rate}")
        self.log_manager.log("Observing...")
        frame_deque = deque(maxlen=60)
        deque_observer = deque(maxlen=self.observer_length * int(self._frame_rate))
        frame_blur = None
        previous_frame_blur = None
        self.is_running = True

        # keep looping infinitely until the thread is stopped

        while self.is_running:

            if not self.is_running:
                break

            frame = self.stream.read()
            if not isinstance(frame, np.ndarray):
                continue

            full_frame = frame.copy()
            add_time = time.time()
            self.current_timestamp = time.time()

            frame_deque.append(self.current_timestamp)

            if self.do_record:

                if self.servo and self.servo.is_moving() or self.servo_is_moving and self.servo_is_moving():
                    add_time = time.time() + (1 * 1000)

                if self.current_timestamp < add_time:
                    deque_observer.clear()
                    previous_frame_blur = None
                    continue

                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame_blur = cv2.GaussianBlur(frame_gray, (21, 21), 0)

                if previous_frame_blur is None:
                    previous_frame_blur = frame_blur
                    continue

                frame_delta = cv2.absdiff(previous_frame_blur, frame_blur)
                frame_threshold = cv2.threshold(frame_delta, 15, 255, cv2.THRESH_BINARY)[1]
                kernel = np.ones((5, 5), np.uint8)
                frame_dilated = cv2.dilate(frame_threshold, kernel, iterations=4)
                res = frame_dilated.astype(np.uint8)
                motion_percentage = (np.count_nonzero(res) * 100) / res.size
                deque_observer.append(motion_percentage)
                self._value = motion_percentage

                time_diff = frame_deque[-1] - frame_deque[0]
                fps = round(len(frame_deque) / time_diff, 1) if len(frame_deque) > 0 and time_diff > 0.0 else 0.0
                video_text = "Temp: {temperature} deg. C  | Hum: {humidity}%".format(
                    **self.dht_function()) if self.dht_function else ""
                video_text = f"{datetime.datetime.now(): %Y-%m-%d %H:%M:%S} | {video_text} [{fps} fps]"
                cv2.rectangle(full_frame, (0, 0), (self.width, 30), (0, 0, 0), -1)
                cv2.putText(full_frame, video_text, (0, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 255), 1, cv2.LINE_AA)

                # # frame_w = frame.shape[1]
                # # frame_h = frame.shape[0]
                # frame_cx = int(self.width / 2)
                # frame_cy = int(self.height / 2)
                #
                # all_points = []
                # contours, hierarchy = cv2.findContours(frame_dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                # for cnt_ in contours:
                #     if cv2.contourArea(cnt_) > 50:
                #         all_points += list(cnt_)
                #
                # if all_points:
                #     all_points_array = np.array(all_points)
                #     (x, y, w, h) = cv2.boundingRect(all_points_array)
                #
                #     cnt_cx = int((x + w + x) / 2)
                #     cnt_cy = int((y + h + y) / 2)
                #
                #     length_x = abs(frame_cx - cnt_cx)
                #     direction_x = "E" if cnt_cx < frame_cx else "W"
                #     length_y = abs(frame_cy - cnt_cy)
                #     direction_y = "N" if cnt_cy < frame_cy else "S"
                #
                #     # print(f"{direction_x} => {(length_x / frame_cx) * 100}%, {direction_y} => {(length_y / frame_cy) * 100}%")
                #
                #     cv2.circle(full_frame, (cnt_cx, cnt_cy), 5, (0, 0, 255), 1)
                #     cv2.circle(full_frame, (frame_cx, frame_cy), 10, (0, 255, 255), 1)
                #     cv2.rectangle(full_frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            self.current_frame = full_frame
            self.detect_motion = sum([x > self.threshold for x in deque_observer]) > 0
            self.do_recording()

            previous_frame_blur = frame_blur



# def main():
#     thread_video = MotionDetector(do_record=True, media_dir=os.path.abspath("../../output/"))
#     print(f"{thread_video}: {thread_video.is_alive()}")
#     thread_video.start()

# if __name__ == '__main__':
#     main()
