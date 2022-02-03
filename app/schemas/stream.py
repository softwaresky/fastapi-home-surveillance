from typing import Optional
from pydantic import BaseModel

class StreamBase(BaseModel):
    audio_threshold: Optional[float] = None
    video_threshold: Optional[float] = None
    observer_length: Optional[int] = None

class StreamSettings(StreamBase):
    pass