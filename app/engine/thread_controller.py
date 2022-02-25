import os
import time
from app.engine import motion_detector
from app.engine import noise_detector
from app.engine import dht_detector
from app.engine import media_file_manager
from app.engine import servo_controller
from app.engine import utils
from app.engine.base_class import ThreadBase

from app.core.config import settings


class ThreadController(ThreadBase):

    def __init__(self,
                 do_record: bool = False,
                 do_merge: bool = False,
                 media_dir: str = "",
                 video_format: str = "mp4",
                 audio_format: str = "wav",
                 motion_threshold: float = 7.0,
                 observer_length: int = 5,
                 servo_pin_map=None,
                 noise_threshold=0.005,
                 dht_pin=4):

        super(self.__class__, self).__init__()

        if servo_pin_map is None:
            servo_pin_map = {
                "pan_pin": 11,
                "tilt_pin": 18
            }

        self.name = str(self.__class__.__name__)
        self.log_manager = utils.LogManager(self.name)

        self.do_record = do_record
        self.do_merge = do_merge
        self.record_state = False
        self.video_format = video_format
        self.audio_format = audio_format
        self.media_dir = media_dir
        self.current_file = ""
        self._lst_threads = []

        self.dht_detector = None
        self.dht_detector = dht_detector.DhtDetector(dht_pin=dht_pin)

        self.servo_controller = None
        self.servo_controller = servo_controller.ServoController(**servo_pin_map)

        self.motion_detector = None
        self.motion_detector = motion_detector.MotionDetector(do_record=self.do_record,
                                                              use_other_to_record=self.do_merge,
                                                              video_format=self.video_format,
                                                              threshold=motion_threshold,
                                                              observer_length=observer_length,
                                                              media_dir=self.media_dir,
                                                              dht_function=self.dht_detector.get_data if self.dht_detector else None,
                                                              servo_is_moving=self.servo_controller.is_moving if self.servo_controller else None)

        self.motion_detector_web = None
        self.motion_detector_web = motion_detector.MotionDetector(camera_source_index=1,
                                                                  do_record=self.do_record,
                                                                  use_other_to_record=self.do_merge,
                                                                  video_format=self.video_format,
                                                                  threshold=motion_threshold,
                                                                  observer_length=observer_length,
                                                                  media_dir=self.media_dir,
                                                                  dht_function=self.dht_detector.get_data if self.dht_detector else None)
        self.noise_detector = None
        self.noise_detector = noise_detector.NoiseDetector(do_convert=False,
                                                           do_record=self.do_record,
                                                           use_other_to_record=self.do_merge,
                                                           audio_format=self.audio_format,
                                                           observer_length=observer_length,
                                                           threshold=noise_threshold,
                                                           media_dir=self.media_dir)

        self.media_file_manager = None
        self.media_file_manager = media_file_manager.MediaFileManager()

        if self.dht_detector: self._lst_threads.append(self.dht_detector)
        if self.servo_controller: self._lst_threads.append(self.servo_controller)
        if self.motion_detector: self._lst_threads.append(self.motion_detector)
        if self.noise_detector: self._lst_threads.append(self.noise_detector)
        if self.media_file_manager: self._lst_threads.append(self.media_file_manager)
        if self.motion_detector_web: self._lst_threads.append(self.motion_detector_web)

        self.fill_do_record()

    def stop_children_threads(self):
        self.log_manager.log("Stop children threads.")

        for thread_ in self._lst_threads:
            if thread_:
                thread_.is_running = False
                # thread_.join()

    def start_children_threads(self):

        self.log_manager.log("Start children threads.")

        for thread_ in self._lst_threads:
            if thread_ and not thread_.is_running:
                thread_.is_running = True
                thread_.start()

    def fill_do_record(self):
        if self.motion_detector:
            self.motion_detector.do_record = self.do_record
        if self.noise_detector:
            self.noise_detector.do_record = self.do_record

    def switch_record_state(self):
        self.do_record = not self.do_record
        self.fill_do_record()

    def get_record_path_name(self):
        return os.path.join(self.media_dir, utils.get_timestamp())

    def loop_functions(self):

        if not self.do_merge:
            return

        if not self.do_record:
            return

        state_noise = self.noise_detector and self.noise_detector.detect_noise
        state_motion = self.motion_detector and self.motion_detector.detect_motion

        record_state = state_noise or state_motion

        if self.record_state != record_state:  # change
            self.record_state = record_state

            if self.record_state:
                record_file_name = self.get_record_path_name()
                dir_name = os.path.dirname(record_file_name)
                base_name = os.path.basename(record_file_name)

                self.current_file = f"{record_file_name}.{self.video_format}"
                if self.motion_detector:
                    self.motion_detector.current_file = os.path.join(dir_name,
                                                                     f".{base_name}_video.{self.video_format}")
                if self.noise_detector:
                    self.noise_detector.current_file = os.path.join(dir_name, f".{base_name}_audio.{self.audio_format}")

                if self.motion_detector and self.noise_detector and self.media_file_manager:
                    self.media_file_manager.add_item(func=media_file_manager.MediaFileManager.merge_video_and_audio,
                                                     dict_kwargs={
                                                         "video_file": self.motion_detector.current_file,
                                                         "audio_file": self.noise_detector.current_file,
                                                         "output_file": self.current_file
                                                     })

            if self.motion_detector:
                self.motion_detector.force_recording = record_state
            if self.noise_detector:
                self.noise_detector.force_recording = record_state

        if self.media_file_manager:
            # Executing functions from motion detector
            if self.motion_detector and self.motion_detector.lst_buffer_data:
                for func_, dict_kwargs_ in self.motion_detector.lst_buffer_data:
                    self.media_file_manager.add_item(func=func_, dict_kwargs=dict_kwargs_)
                self.motion_detector.lst_buffer_data.clear()

            # Executing functions from noise detector
            if self.noise_detector and self.noise_detector.lst_buffer_data:
                for func_, dict_kwargs_ in self.noise_detector.lst_buffer_data:
                    self.media_file_manager.add_item(func=func_, dict_kwargs=dict_kwargs_)
                self.noise_detector.lst_buffer_data.clear()

    def is_ready(self):
        return len([thread_ for thread_ in self._lst_threads if not thread_.is_running]) == 0

    def run(self):

        self.start_children_threads()
        self.is_running = True

        try:
            while self.is_running:
                self.loop_functions()
                time.sleep(0.5)

        except KeyboardInterrupt as e:
            self.is_running = False
            self.stop_children_threads()


controller = ThreadController(do_record=settings.DO_RECORD,
                              do_merge=settings.DO_MERGE,
                              media_dir=settings.MEDIA_DIR,
                              video_format=settings.VIDEO_FORMAT,
                              audio_format=settings.AUDIO_FORMAT,
                              motion_threshold=settings.MOTION_THRESHOLD,
                              noise_threshold=settings.NOISE_THRESHOLD,
                              observer_length=settings.OBSERVER_LENGTH,
                              servo_pin_map=settings.SERVO_PIN_MAP,
                              dht_pin=settings.DHT_PIN)


def main():
    def _calculate_inputs(input_str=""):
        input_str = input_str.strip()
        split_input = input_str.split(" ")
        sides = input_str
        angle = None
        if len(split_input) == 2:
            sides = split_input[0]
            angle = split_input[-1]
            if angle.isdigit():
                angle = int(angle)

        return sides, angle

    os.environ["PA_ALSA_PLUGHW"] = "1"
    # thread_controller = ThreadController(media_dir=os.path.abspath("../../output/"))
    time.sleep(1)
    global controller
    controller.start()

    while True:
        try:

            if controller.is_ready():
                input_str = input("Sides and angle: ")
                sides, angle = _calculate_inputs(input_str=input_str)
                controller.servo_controller.move(sides=sides, angle=angle)

        except KeyboardInterrupt:
            del controller
            break

# if __name__ == '__main__':
#     main()
