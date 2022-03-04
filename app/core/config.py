import secrets
from typing import Any, Dict, List, Optional
from pydantic import AnyHttpUrl, BaseSettings
import os

class Settings(BaseSettings):

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "home-surveillance"

    MEDIA_DIR: Optional[str] = os.path.abspath("./output/")
    MOTION_THRESHOLD: Optional[float] = 7.0
    NOISE_THRESHOLD: Optional[float] = 1.0 # default was 0.005
    DO_RECORD: Optional[bool] = True
    DO_MERGE: Optional[bool] = True
    VIDEO_FORMAT: Optional[str] = "mp4"
    AUDIO_FORMAT: Optional[str] = "wav"
    OBSERVER_LENGTH: Optional[int] = 5

    SERVO_PIN_MAP: Optional[dict] = {
        # "pan_pin": 11, # BOARD
        "pan_pin": 17, # BCM
        # "tilt_pin": 18 # BOARD
        "tilt_pin": 24 # BCM
    }

    DHT_PIN = 4

    # SQLALCHEMY_DATABASE_URI: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()