from typing import Any, List, Dict, Generator
import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, Response, Header
from fastapi.responses import FileResponse
from app.core.config import settings
from app.engine import utils

router = APIRouter()

def get_file_info(file_path=""):
    dict_data = {}
    if file_path and os.path.exists(file_path):
        dict_data["filename"] = file_path
        dict_data["size"] = os.stat(file_path).st_size
        dict_data["size_str"] = utils.sizeof_fmt(os.stat(file_path).st_size, "B")
        dict_data["extension"] = os.path.splitext(file_path)[-1]
        dict_data["created"] = os.stat(file_path).st_ctime
        dict_data["created_str"] = datetime.datetime.fromtimestamp(os.stat(file_path).st_ctime).strftime("%Y-%m-%d %H:%M:%S")

    return dict_data

@router.get('/')
def read_archives():
    lst_result = []

    if os.path.exists(settings.MEDIA_DIR):
        for file_ in os.listdir(settings.MEDIA_DIR):
            lst_result.append(get_file_info(file_path=os.path.join(settings.MEDIA_DIR, file_)))

    return lst_result

@router.get("/{file_path:path}")
def read_file_info(
        file_path: str = ""
) -> Dict:
    return get_file_info(file_path=file_path)

@router.delete("/{filename:path}/delete")
def archive_delete(
        filename: str = ""
) -> Any:

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Empty filename!",
        )
    else:
        file_path = os.path.join(settings.MEDIA_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"This {file_path} doesn't exists!",
            )
        else:
            os.remove(file_path)

            return {
                "file_path": file_path,
                "is_exists": os.path.exists(file_path)
            }


@router.get("/{filename:path}/stream")
def archive_play(
        filename: str = ""
) -> Any:

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Empty filename!",
        )
    else:
        file_path = os.path.join(settings.MEDIA_DIR, filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=400,
                detail=f"This {filename} doesn't exists!",
            )
        else:
            return FileResponse(file_path)


# @app.route('/archive/play/<string:filename>')
# def archive_play(filename):
# 	# return send_file('archive/' + filename)
# 	return send_file('media/' + filename)

# @router.get("/play/{filename:path}")
# async def video_endpoint(filename: str, range: str = Header(None)):
#
#     if not filename or os.path.exists(filename):
#         raise HTTPException(
#             status_code=400,
#             detail=f"This {filename} doesn't exists!",
#         )
#
#     chunk_size = 1024 * 1024
#     start, end = range.replace("bytes=", "").split("-")
#     start = int(start)
#     end = int(end) if end else start + chunk_size
#     with open(filename, "rb") as video:
#         video.seek(start)
#         data = video.read(end - start)
#         filesize = str(filename.stat().st_size)
#         headers = {
#             'Content-Range': f'bytes {str(start)}-{str(end)}/{filesize}',
#             'Accept-Ranges': 'bytes'
#         }
#         return Response(data, status_code=206, headers=headers, media_type="video/mp4")

