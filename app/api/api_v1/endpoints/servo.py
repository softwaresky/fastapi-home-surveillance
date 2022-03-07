import pprint
import time
from typing import Any, Optional
from fastapi import APIRouter, WebSocket, HTTPException
from app.engine.servo_controller import ServoController
from app.engine.thread_controller import controller
from app.schemas.servo import ServoUpdate


router = APIRouter()

def get_servo_object() -> ServoController:

    if hasattr(controller.motion_detector, "servo") and controller.motion_detector.servo:
        return controller.motion_detector.servo
    elif controller.servo_controller:
        return controller.servo_controller
    else:
        raise Exception("Missing servo controller object")

@router.put("/move/")
async def move_by_axis(
        servo_ctrl: ServoUpdate
) -> Any:
    try:
        servo_object = get_servo_object()
        await servo_object.move_async(**servo_ctrl.dict())
        data = await servo_object.get_data()
    except Exception as err:
        raise HTTPException(status_code=404, detail=err)

    return {
        "success": "OK",
        "message": "Successfully moved.",
        "data": data
    }

@router.get("/info")
async def get_info() -> Any:
    try:
        return await get_servo_object().get_data()
    except Exception as err:
        raise HTTPException(status_code=404, detail=err)