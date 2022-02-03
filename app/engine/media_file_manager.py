import os
import sys
import subprocess
import time
import hashlib
import math

from app.engine import utils
from app.engine.base_class import ThreadBase

def get_md5(file_path=""):

    result = hashlib.md5()
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as file_:
            result.update(file_.read())

    return result.hexdigest()

def check_merge(video_file="", audio_file=""):

    pair = ()

    for i in range(2):

        if not (os.path.exists(video_file) and os.path.exists(audio_file)):
            continue

        video_file_obj = File(video_file)
        audio_file_obj = File(audio_file)

        value = (video_file_obj, audio_file_obj)
        if pair == value:
            # self.merge_video_and_audio(video_file_, audio_file_, output_file_)
            return True

        pair = value
        time.sleep(2)

class File:

    def __init__(self, file_path=""):
        self.path = file_path
        self.size = os.stat(file_path).st_size
        self.last_modified = os.path.getmtime(file_path)

    def as_dict(self):
        return self.__dict__

    def __eq__(self, other):
        return self.path == other.path and \
               math.isclose(self.size, other.size) and \
               math.isclose(self.last_modified, other.last_modified)

class MediaFileManager(ThreadBase):

    def __init__(self):
        super(self.__class__, self).__init__()

        self.name = str(self.__class__.__name__)
        self.log_manager = utils.LogManager(self.name)
        self.lst_item = []
        self.is_running = False

    def add_item(self, func=None, dict_kwargs={}):
        # self.lst_item.append(data)
        self.log_manager.log(f"Add function: {func}")
        self.lst_item.append((func, dict_kwargs))

    def run(self) -> None:

        self.is_running = True

        while self.is_running:

            lst_executed = []

            for func_, dict_kwargs_ in self.lst_item:

                try:
                    dict_kwargs_tmp = {}
                    for key_ in dict_kwargs_:
                        if isinstance(dict_kwargs_[key_], (str, int, float)):
                            dict_kwargs_tmp[key_] = dict_kwargs_[key_]

                    # self.log_manager.log(f"Executing {func_} | {dict_kwargs_tmp}")
                    if func_(**dict_kwargs_):
                        self.log_manager.log(f"Successfully executed {func_}")
                        lst_executed.append((func_, dict_kwargs_))
                except Exception as err:
                    self.log_manager.error(f"{err}")

            for item_ in lst_executed:
                self.lst_item.remove(item_)

            time.sleep(1)

    @staticmethod
    def merge_video_and_audio(video_file="", audio_file="", output_file="", *args):

        try:
            if video_file and audio_file and output_file:
                if not check_merge(video_file=video_file, audio_file=audio_file):
                    return False

                command = f"ffmpeg -i {video_file} -loglevel error -i {audio_file} -c:v libx264 -crf 22 -preset slow -c:a aac -b:a 192k -ac 2 {output_file}"

                p = subprocess.Popen(command, shell=True)
                (output, err) = p.communicate()

                for file_ in [video_file, audio_file]:
                    if os.path.exists(file_):
                        p.wait()
                        os.remove(file_)

                return True

        except subprocess.CalledProcessError:
            raise Exception("Error converting merging files!")

    def run_old(self) -> None:

        self.is_running = True

        while self.is_running:

            lst_merged_items_ = []
            dict_files = {}

            for video_file_, audio_file_, output_file_ in self.lst_item:

                if not (os.path.exists(video_file_) and os.path.exists(audio_file_)):
                    continue

                key_ = (video_file_, audio_file_, output_file_)

                # hashed_md5 = f"{get_md5(video_file_)}-{get_md5(audio_file_)}"

                video_file_obj = File(video_file_)
                audio_file_obj = File(audio_file_)

                value = (video_file_obj, audio_file_obj)
                if key_ not in dict_files:
                    dict_files[key_] = value
                    # dict_files[key_] = hashed_md5
                else:
                    # if dict_files[key_][0] == video_file_obj and dict_files[key_][1] == audio_file_obj:
                    # if dict_files[key_] == hashed_md5:
                    if dict_files[key_] == value:
                        self.merge_video_and_audio(video_file_, audio_file_, output_file_)
                        lst_merged_items_.append(key_)

                # dict_files[key_] = hashed_md5
                dict_files[key_] = value

            self.lst_item = list(set(self.lst_item) - set(lst_merged_items_))
            del lst_merged_items_

            time.sleep(1)


# def main():
#     dict_data = {}
#     dict_data["video_file"] = r"C:/Users/Softwaresky/PycharmProjects/fastapi-home-surveillance/output/.20210412_213406_audio.wav"
#     dict_data["audio_file"] = r"C:/Users/Softwaresky/PycharmProjects/fastapi-home-surveillance/output/.20210412_213406_video.mp4"
#     dict_data["output_file"] = r"C:/Users/Softwaresky/PycharmProjects/fastapi-home-surveillance/output/20210412_213406.mp4"
#     # merge_video_and_audio(**dict_data)
#     pass


# if __name__ == '__main__':
#     main()