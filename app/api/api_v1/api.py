from fastapi import APIRouter

from app.api.api_v1.endpoints import stream, archive, servo

api_router = APIRouter()

api_router.include_router(servo.router, prefix="/servo", tags=["servo"])
api_router.include_router(stream.router, prefix="/stream", tags=["stream"])
api_router.include_router(archive.router, prefix="/archive", tags=["archive"])
