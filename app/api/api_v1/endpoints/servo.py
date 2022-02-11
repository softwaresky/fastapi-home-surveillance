import pprint
import time
from typing import Any, Optional
from fastapi import APIRouter, WebSocket
from app.engine.thread_controller import controller
from app.schemas.servo import ServoUpdate


router = APIRouter()

@router.on_event("startup")
def startup_router():
    time.sleep(1)
    controller.start()
    pass


@router.on_event("shutdown")
def shutdown_router():
    controller.stop_children_threads()    # all threads can't be stopped
    controller.is_running = False
    controller.join()
    pass

@router.put("/move/")
async def move_by_axis(
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