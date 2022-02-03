from typing import Optional
from pydantic import BaseModel

class ServoBase(BaseModel):
    sides: str = None
    angle: Optional[int] = None

class ServoUpdate(ServoBase):
    pass