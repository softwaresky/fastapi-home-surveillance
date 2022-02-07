import os
import sys
import uvicorn

this_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if this_dir not in sys.path:
    sys.path.append(this_dir)

from app import main

# os.environ["PA_ALSA_PLUGHW"] = "1"
from pathlib import Path
uvicorn.run(f"{Path(__file__).stem}:app", host='0.0.0.0', port=9909, log_level="info", reload=True)