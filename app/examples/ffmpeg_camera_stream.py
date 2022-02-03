import cv2
import pyaudio
import subprocess as sp

def cv2_pipe_input_ffmpeg():
    rtsp_server = 'udp://0.0.0.0:5689/test.ffm'  # push server (output server)

    # pull rtsp data, or your cv cap.  (input server)
    cap = cv2.VideoCapture(0)

    sizeStr = str(int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))) + \
              'x' + str(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    command = ['ffmpeg',
               '-re',
               '-s', sizeStr,
               '-r', str(fps),  # rtsp fps (from input server)
               # You can change ffmpeg parameter after this item.
               '-pix_fmt', 'yuv420p',
               '-i', '-',
               '-r', '30',  # output fps
               '-g', '50',

               '-c:v', 'libx264',
               '-b:v', '2M',
               '-bufsize', '64M',
               '-maxrate', "4M",
               '-preset', 'veryfast',
               '-f', 'mpegts',
               '-flush_packets', '0',
               rtsp_server]



    print (" ".join(command))

    process = sp.Popen(command, stdin=sp.PIPE)

    while cap.isOpened():
        ret, frame = cap.read()
        ret2, frame2 = cv2.imencode('.png', frame)
        process.stdin.write(frame2.tobytes())


def pyaudio_pipe_input_ffmpeg():
    # rtsp_server = 'udp://192.168.100.12:5689'  # push server (output server)
    rtsp_server = 'rtp://0.0.0.0:5689/test.ffm'  # push server (output server)

    # ffmpeg -f alsa -i hw:0 -acodec libmp3vlame -f mp2 udp://192.168.100.8:5689

    command = ['ffmpeg',
               '-re',
               '-f', 'f32le',
               '-i', '-',
               '-ar', '44100',
               '-ac', '1',  # stereo (set to '1' for mono)
               '-acodec', 'pcm_f32le',
               '-acodec', 'libmp3lame',
               '-f', 'rtp',
               rtsp_server]

    print (" ".join(command))

    process = sp.Popen(command, stdin=sp.PIPE)

    audio = pyaudio.PyAudio()
    stream = audio.open(format=pyaudio.paFloat32, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    stream.start_stream()
    while stream.is_active():
        chunk = stream.read(1024, exception_on_overflow=False)
        process.stdin.write(chunk)



if __name__ == "__main__":
    # cv2_pipe_input_ffmpeg()
    pyaudio_pipe_input_ffmpeg()
    # TODO: Da probam da streamam nezavisno od cv2 i pyaudio
    """
    ffmpeg -s 720x720 -f video4linux2 -i /dev/video0 -r 25 -f alsa -i hw:0 -c:v libx264 -an -f mpegts udp://0.0.0.0:5688/video  -vn -c:a aac -strict -2 -f rtp rtp://0.0.0.0:5689/audio
    """

    # ffmpeg -f v4l2 -thread_queue_size 32 -i /dev/video0 -f alsa -thread_queue_size 2048  -i hw:0 -profile:v high -pix_fmt yuvj420p -level:v 4.1 -preset ultrafast -tune zerolatency -vcodec libx264 -r 10 -b:v 512k -s 640x360 -acodec aac -strict -2 -ac 2 -ab 32k -ar 44100 -f mpegts -flush_packets 0 udp://192.168.100.12:5689?pkt_size=1316
    pass
