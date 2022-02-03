import pprint
from typing import Any, Optional
from fastapi import APIRouter
from app.engine.thread_controller import controller
from app.schemas.servo import ServoUpdate



router = APIRouter()

@router.post("/move/")
def move_by_axis(
        servo_ctrl: ServoUpdate
) -> Any:
    try:
        controller.servo_controller.move(**servo_ctrl.dict())

    except Exception as err:
        return {
            "success": "Error",
            "message": f"{err}",
            "data": {}
        }

    return {
        "success": "OK",
        "message": "Successfully moved.",
        "data": controller.servo_controller.get_data()
    }
