import datetime
import pprint
import sys
import wave
import pyaudio
import subprocess
import os
import time
import audioop
import math
import struct
import threading
import numpy as np
from collections import deque

from app.engine import utils
from app.engine.base_class import ThreadBase

SHORT_NORMALIZE = (1.0/32768.0)

# Generates the .wav file header for a given set of samples and specs
def gen_header(sampleRate, bitsPerSample, channels):
    datasize = 2000 * 10 ** 6
    o = bytes("RIFF", 'ascii')  # (4byte) Marks file as RIFF
    o += (datasize + 36).to_bytes(4, 'little')  # (4byte) File size in bytes excluding this and RIFF marker
    o += bytes("WAVE", 'ascii')  # (4byte) File type
    o += bytes("fmt ", 'ascii')  # (4byte) Format Chunk Marker
    o += (16).to_bytes(4, 'little')  # (4byte) Length of above format data
    o += (1).to_bytes(2, 'little')  # (2byte) Format type (1 - PCM)
    o += (channels).to_bytes(2, 'little')  # (2byte)
    o += (sampleRate).to_bytes(4, 'little')  # (4byte)
    o += (sampleRate * channels * bitsPerSample // 8).to_bytes(4, 'little')  # (4byte)
    o += (channels * bitsPerSample // 8).to_bytes(2, 'little')  # (2byte)
    o += (bitsPerSample).to_bytes(2, 'little')  # (2byte)
    o += bytes("data", 'ascii')  # (4byte) Data Chunk Marker
    o += (datasize).to_bytes(4, 'little')  # (4byte) Data size in bytes
    return o

def generate_wav_byes(raw_data=bytes(), format=pyaudio.paFloat32, channels=1, rate=44100):
    """
    Create WAVE-file from raw audio chunks

    @param bytes raw
    @return bytes
    """
    # Check if input format is supported
    if format not in (pyaudio.paFloat32, pyaudio.paInt16):
        raise Exception("Unsupported format")

    # Convert raw audio bytes to typed array
    samples = np.frombuffer(raw_data, dtype=np.float32)

    # Get sample size
    sample_size = pyaudio.get_sample_size(format)

    # Get data-length
    byte_count = (len(samples)) * sample_size

    # Get bits/sample
    bits_per_sample = sample_size * 8

    # Calculate frame-size
    frame_size = int(channels * ((bits_per_sample + 7) / 8))

    # Container for WAVE-content
    wav = bytearray()

    # Start RIFF-Header
    wav.extend(struct.pack('<cccc', b'R', b'I', b'F', b'F'))
    # Add chunk size (data-size minus 8)
    wav.extend(struct.pack('<I', byte_count + 0x2c - 8))
    # Add RIFF-type ("WAVE")
    wav.extend(struct.pack('<cccc', b'W', b'A', b'V', b'E'))

    # Start "Format"-part
    wav.extend(struct.pack('<cccc', b'f', b'm', b't', b' '))
    # Add header length (16 bytes)
    wav.extend(struct.pack('<I', 0x10))
    # Add format-tag (e.g. 1 = PCM, 3 = FLOAT)
    wav.extend(struct.pack('<H', 3))
    # Add channel count
    wav.extend(struct.pack('<H', channels))
    # Add sample rate
    wav.extend(struct.pack('<I', rate))
    # Add bytes/second
    wav.extend(struct.pack('<I', rate * frame_size))
    # Add frame size
    wav.extend(struct.pack('<H', frame_size))
    # Add bits/sample
    wav.extend(struct.pack('<H', bits_per_sample))

    # Start data-part
    wav.extend(struct.pack('<cccc', b'd', b'a', b't', b'a'))
    # Add data-length
    wav.extend(struct.pack('<I', byte_count))

    # Add data
    for sample in samples:
        wav.extend(struct.pack("<f", sample))

    return bytes(wav)


class NoiseDetector(ThreadBase):

    def __init__(self,
                 do_record: bool = True,
                 do_convert: bool = False,
                 use_other_to_record: bool = False,
                 media_dir: str = "",
                 audio_format: str = "wav",
                 observer_length: int = 5,
                 threshold: float = 0.005,
                 servo_is_moving=None):

        super(self.__class__, self).__init__()

        self.name = str(self.__class__.__name__)
        self.log_manager = utils.LogManager(self.name)

        self.media_dir = media_dir
        self.audio_format = audio_format
        self.observer_length = observer_length
        # self.FORMAT = pyaudio.paFloat32
        self.FORMAT = pyaudio.paInt16
        self.RATE = 44100  # Hz, so samples (bytes) per second
        self.CHUNK_SIZE = 1024  # How many bytes to read from mic each time (stream.read()) ex: (samples rate)/6000 * 1024
        self.CHUNKS_PER_SEC = math.floor(self.RATE / self.CHUNK_SIZE)  # How many chunks make a second? (16.000 bytes/s, each chunk is 1.024 bytes, so 1s is 15 chunks)
        self.CHANNELS = 1
        self.HISTORY_LENGTH = 2  # Seconds of audio cache for prepending to records to prevent chopped phrases (history length + observer length = min record length)
        self.chunk = b""
        self.audio = pyaudio.PyAudio()
        self.stream = self.get_stream()
        # self.threshold = self.determine_threshold()
        self.threshold = threshold
        self.servo_is_moving = servo_is_moving
        self.detect_noise = False
        self.records = []
        self.do_record = do_record
        self.do_convert = do_convert
        self.force_recording = False
        self.use_other_to_record = use_other_to_record
        self.is_saved = False
        self._value = 0.0
        self.current_file = ""
        self.last_file = ""
        self.deque_history = deque(maxlen=self.HISTORY_LENGTH * self.CHUNKS_PER_SEC)
        self.deque_observer = deque(maxlen=self.observer_length * self.CHUNKS_PER_SEC)
        self.lst_buffer_data = []

    def __del__(self):

        if self.stream:
            self.stream.stop_stream()
            if self.audio:
                self.audio.close(self.stream)
                self.audio.terminate()

        # del self.stream
        # del self.audio


    def get_stream(self):
        return self.audio.open(format=self.FORMAT,
                               channels=self.CHANNELS,
                               rate=self.RATE,
                               input=True,
                               frames_per_buffer=self.CHUNK_SIZE)


    def determine_threshold(self):

        self.log_manager.log("Determining threshold...")

        lst_res = []
        for x in range(50):
            block = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            rms = self.get_rms(block)
            lst_res.append(rms)

        threshold = (sum(lst_res) / len(lst_res)) * 2

        self.log_manager.log("Setting threshold to: {0}".format(threshold))

        return threshold

    def get_rms(self, block):
        # RMS amplitude is defined as the square root of the
        # mean over time of the square of the amplitude.
        # so we need to convert this string of bytes into
        # a string of 16-bit samples...

        # we will get one short out for each
        # two chars in the string.
        count = len(block) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, block)

        # iterate over the block.
        sum_squares = 0.0
        for sample in shorts:
            # sample is a signed short in +/- 32768.
            # normalize it to 1.0
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n

        return math.sqrt(sum_squares / count)

    def get_rms_old(self, block):
        """
        Calculate Root Mean Square (noise level) for audio chunk

        @param bytes block
        @return float
        """
        np_type = np.float32 if self.FORMAT == pyaudio.paFloat32 else np.int16
        d = np.frombuffer(block, np_type).astype(np_type)
        # d = np.frombuffer(block, np_type).astype(np.float32)
        sum_value = (d * d).sum()
        result = np.sqrt((d * d).sum() / len(d))
        if sum_value:
            try:
                result = np.sqrt((d * d).sum() / len(d))
            except RuntimeWarning:
                result = audioop.rms(block, 2)
        return result

    @property
    def value(self):
        return self._value if self._value > self.threshold else 0.0

    def start_recording(self):

        if not (self.use_other_to_record and self.current_file):
            self.current_file = os.path.join(self.media_dir, f".{utils.get_timestamp()}.{self.audio_format}")

        if self.current_file:
            dst_dir = os.path.dirname(self.current_file)

            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)

            self.log_manager.log("Noise detected! Recording...")

    def stop_recording(self):

        self.last_file = self.current_file

        self.records = []
        self.current_file = ""

    def is_recording(self):
        return len(self.records) > 0

    def get_rms_data_info(self):

        return {
            "max": max(self.deque_observer),
            "min": min(self.deque_observer),
            "avg": sum(self.deque_observer) / len(self.deque_observer)
        }

    def get_chunk(self):
        # return gen_header(self.RATE, self.audio.get_sample_size(self.FORMAT) * 8, self.CHANNELS) + self.chunk if self.chunk_count == 1 else self.chunk
        # return np.frombuffer(self.chunk, np.uint8).tolist()
        return self.chunk

    def gen_header(self):
        return gen_header(self.RATE, self.audio.get_sample_size(self.FORMAT) * 8, self.CHANNELS)

    def run(self):

        # deque_observer = deque(maxlen=self.observer_length * self.CHUNKS_PER_SEC)
        # self.deque_history = deque(maxlen=self.HISTORY_LENGTH * self.CHUNKS_PER_SEC)

        self.log_manager.log("Listening...")

        self.is_running = True

        try:
            while self.is_running:

                if self.servo_is_moving and self.servo_is_moving():
                    self.deque_observer.clear()
                    self.deque_history.clear()
                    continue

                self.chunk = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)

                self.deque_history.append(self.chunk)

                rms = self.get_rms(self.chunk)
                self.deque_observer.append(rms)

                self._value = rms
                self.detect_noise = sum([x > self.threshold for x in self.deque_observer]) > 0

                if self.do_record:
                    self.do_recording()

            self.is_running = False

        except KeyboardInterrupt:
            self.log_manager.log("Interrupted!")
            self.is_running = False


    def do_recording(self):

        if (self.use_other_to_record and self.force_recording) or (not self.use_other_to_record and self.detect_noise):
            if not self.is_recording():
                self.start_recording()

            self.records.append(self.chunk)

        elif self.is_recording():
            # self._thread_save(self.current_file)
            self.lst_buffer_data.append((NoiseDetector.save_audio, self.get_function_kwargs()))

            self.stop_recording()
            self.log_manager.log("Listening...")

    def get_function_kwargs(self):
        return {
            "file_path": self.current_file,
            "channels": self.CHANNELS,
            "rate": self.RATE,
            "sample_format": self.audio.get_sample_size(self.FORMAT),
            "records": self.records
        }

    @staticmethod
    def save_audio(file_path="", records=[], sample_format=0, channels=1, rate=44100, log_manager: utils.LogManager = None):

        if file_path and records:

            # open the file in 'write bytes' mode
            wf = wave.open(file_path, "wb")
            # set the channels
            wf.setnchannels(channels)
            # set the sample format
            wf.setsampwidth(sample_format)
            # set the sample rate
            wf.setframerate(rate)
            # write the frames as bytes
            wf.writeframes(b"".join(records))
            # close the file
            wf.close()

            # data = b''.join(records)
            # with open(file_path, "wb+") as f:
            #     f.write(generate_wav_byes(raw_data=data, format=format, channels=channels, rate=rate))

            if log_manager:
                log_manager.log(f"Saved audio: {file_path}")

            return True

        return False

    def _thread_save(self):

        # self.log_manager.log(f"Saving audio: {file_path}")
        # self.is_saved = False
        #
        # if file_path and self.records:
        #     NoiseDetector.save_audio(file_path=file_path,
        #                              records=self.records,
        #                              format=self.FORMAT,
        #                              channels=self.CHANNELS,
        #                              rate=self.RATE)
        #
        #     if self.do_convert:
        #         self.convert_to_mp3(file_path)
        #
        #     self.is_saved = True

        # records=[], format=pyaudio.paFloat32, channels=1, rate=44100, log_manager: utils.LogManager = None
        t = threading.Thread(target=NoiseDetector.save_audio, kwargs=self.get_function_kwargs(), daemon=True)
        t.start()

    def convert_to_mp3(self, file_path=""):

        self.log_manager.log("Converting audio...")

        try:
            mp3_file = "{0}.mp3".format(os.path.splitext(file_path)[0])

            lst_cmd = []
            lst_cmd.append("ffmpeg")
            lst_cmd.append("-i {}".format(file_path))
            lst_cmd.append("-f mp3")
            lst_cmd.append("{}".format(mp3_file))

            p = subprocess.Popen(" ".join(lst_cmd), shell=True)
            (output, err) = p.communicate()

            if os.path.exists(file_path):
                p.wait()
                os.remove(file_path)

            self.current_file = mp3_file

        except subprocess.CalledProcessError:
            self.log_manager.log("Error converting audio")


# def main():
#
#     nd = NoiseDetector(media_dir=os.path.abspath("../../output/"), do_record=True)
#     time.sleep(1)
#     nd.start()

# if __name__ == '__main__':
#     main()
