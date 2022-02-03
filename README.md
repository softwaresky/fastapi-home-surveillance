# fastapi-home-surveillance

Home surveillance/security camera(s). 
Movement and noise detection solved by application algorithm using **cv2**. 
Dynamic camera, move in two axes rotation **Pan** and **Tilt**.
Auto recording triggered by move or noise and save/archive it on disc.
Merging audio and video file in one file.
Convert video into **H.264** encoding with (**.mp4**) format.


## [Requirements](/app/requirements.txt)

### Hardware
- Raspberry Pi 2 or higher
- Camera Module for RsPi
- USB mini microphone adapter
- Movement:
  - 1x **Nylon FPV pan/tilt** - Camera Mount Platform
  - 2x **SG90 9g Servo** - Servo motor(s)
- **AM2302B** Sensor for temperature and humidity

### Libraries
- opencv-contrib-python
- PyAudio
- fastapi
- uvicorn
- aiofiles
- picamera


## Todo

### Back-End
 - Stop recording or detecting when the camera is moving
 - Add sensor for movement for optimized movement solving
 - Add sensor for noise for optimized noise solving
 - Login with some token
 - Creating DB for statistic

### Front-End
- Viewing real-time from the camera(s) 
- Move the camera(s) from front-end
- UI for archive files