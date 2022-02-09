import os.path
import pprint
import json
from fastapi import FastAPI, WebSocket
from fastapi.requests import Request
from fastapi.responses import Response, FileResponse, StreamingResponse
# from sse_starlette.sse import EventSourceResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
from pydantic import BaseModel, ValidationError
import time
import threading
from typing import Any
# from fastapi_socketio import SocketManager
from starlette.middleware.cors import CORSMiddleware
from logging import info

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.schemas.servo import ServoUpdate
from app.engine import utils
from app.engine.thread_controller import controller

app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# socket_manager = SocketManager(app=app, mount_location="/socket.io")

# sio = socketio.AsyncServer(async_mode='asgi')
# sio = socketio.Server(async_mode='threading')
# sio_asgi_app = socketio.ASGIApp(sio, app)
# app.mount("/socket.io", sio_asgi_app)

# app.add_route("/socket.io/", route=sio_asgi_app, methods=['GET', 'POST'])
# app.add_websocket_route("/socket.io/", sio_asgi_app)


static_dir = utils.get_static_dir()
print (f"static_dir: {static_dir}")

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory="templates")

# add CORS so our web page can connect to our api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_STR)


# @sio.on("connect")
# async def connect(sid, environ):
#     print (f"sid............")
#     pprint.pprint(sid)
#     await sio.emit("sound", {"chunk": "Alooooo"})
#     print("connected")


# @socket_manager.on('connect')
# async def connect(sid, *args, **kwargs):
#     print (f"sid: {sid}")
#     await socket_manager.emit("sound", {"chunk": "Alooooo"})


# @app.get("/event-sound")
# async def get_sound_event(request: Request):
#     async def _generate_data():
#
#         while True:
#             if await request.is_disconnected():
#                 print("client disconnected!!!")
#                 break
#             sound = controller.noise_detector.get_chunk()
#             # dict_data = {}
#             # dict_data["chunk"] = f"{count}"
#             # json_data = json.dumps(dict_data)
#             # yield f"data:{json_data}\n\n"
#             yield dict(data=sound)
#             await asyncio.sleep(0.05)
#             # time.sleep(0.05)
#             # time.sleep(2)
#     return EventSourceResponse(_generate_data())

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#
#     while True:
#         await asyncio.sleep(0.05)
#         sound = controller.noise_detector.get_chunk()
#         # opus = controller.noise_detector.get_opus()
#
#         # await websocket.send(base64.)
#         # await websocket.send_json(payload)
#         # await websocket.send_text(str(sound))
#         await websocket.send_bytes(sound)

# @app.get("/audio-feed")
# def audio_feed():
#
#
#
#     return StreamingResponse()

# class SoundStreamThread(threading.Thread):
#     def __init__(self):
#         self.delay = 1
#         super(self.__class__, self).__init__()
#
#
#     def run(self):
#         count = 0
#         while True:
#             print (sio.emit('sound', data={'chunk': count}))
#             count += 1
#             # time.sleep(0.05)
#             time.sleep(2)
#
#
# sound_stream_t = SoundStreamThread()
# sound_stream_t.start()

# @sio.on("sound")
# async def chat_message(sid, data):
#     print("message ", data)
#     await sio.emit('sound', room={'chunk': 1})

# sio = socketio.AsyncServer(
#     async_mode="asgi", cors_allowed_origins="*"
# )

# @sio.on("connect")
# def on_connect():
#     print ("Connect")
#

# @sio.on("disconnect")
# def on_disconnect():
#     print ("Client disconnected")

# @app.get("/stream-audio")
# async def stream_audio():
#     event_generator = None
#     return EventSourceResponse(event_generator)


@app.get("/")
def index(request: Request):
    # file_path = os.path.join(dir_, "index.html")
    file_path = "/static/index.html"
    return templates.TemplateResponse("index.html", context={"request": request})
    # return FileResponse(file_path, media_type='text/html')
