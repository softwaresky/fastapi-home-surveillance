from typing import Any, List, Dict, Generator, Optional
import time
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse, StreamingResponse
from app.core.config import settings
from app.schemas.stream import StreamSettings
from app.engine.thread_controller import controller

router = APIRouter()


@router.on_event("startup")
def startup_router():
    time.sleep(1)
    controller.start()
    pass


@router.on_event("shutdown")
def shutdown_router():
    # controller.stop_children_threads()    # all threads can't be stopped
    controller.is_running = False
    controller.join()
    pass


@router.post("/switch-record-state")
def switch_record_state():
    controller.switch_record_state()
    return {
        "is_recorded": controller.do_record
    }


@router.get("/get-record-state")
def get_record_state():
    return {
        "is_recorded": controller.do_record
    }


@router.get("/video-feed")
def video_feed():
    def gen_video() -> Generator:
        while True:
            frame = b""
            if controller.motion_detector:
                frame = controller.motion_detector.get_frame()

            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    return StreamingResponse(
        gen_video(),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@router.get("/audio-feed")
def audio_feed():

    def gen_sound() -> Generator:

        first_run = True

        prev_data = b""
        while controller.noise_detector:
            if first_run:
                first_run = False
                data = controller.noise_detector.gen_header() + controller.noise_detector.get_chunk()
            else:
                data = controller.noise_detector.get_chunk()

            if prev_data != data:
                yield (data)
                prev_data = data


    return StreamingResponse(content=gen_sound(),
                             media_type="audio/wav")


@router.get("/get-audio-rms")
def get_audio_rms():
    return controller.noise_detector.get_rms_data_info()


@router.post("/set-settings")
def set_settings(
        stream_settings: StreamSettings
) -> StreamSettings:
    if stream_settings.audio_threshold:
        controller.noise_detector.threshold = stream_settings.audio_threshold
    if stream_settings.video_threshold:
        controller.motion_detector.threshold = stream_settings.video_threshold
    if stream_settings.observer_length:
        controller.motion_detector.observer_length = stream_settings.observer_length
        controller.noise_detector.observer_length = stream_settings.observer_length

    return stream_settings
