import pylivestream.api as pls
import pylivestream


py_audio = pls.stream_microphone(ini_file="pylivestream.ini", websites=["localhost"], assume_yes=True)

