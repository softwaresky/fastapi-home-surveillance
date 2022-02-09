from fastapi import APIRouter
import time
from app.engine.thread_controller import controller

from app.api.api_v1.endpoints import stream, archive, servo

api_router = APIRouter()

api_router.include_router(servo.router, prefix="/servo", tags=["servo"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])

@api_router.on_event("startup")
def startup_router():
    time.sleep(1)
    controller.start()
    pass


@api_router.on_event("shutdown")
def shutdown_router():
    controller.stop_children_threads()    # all threads can't be stopped
    controller.is_running = False
    controller.join()
    pass