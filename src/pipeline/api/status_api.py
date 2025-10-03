# src/api/status_api.py
from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
from fastapi import FastAPI
from pipeline.daemon.status import get_latest_status

app = FastAPI()

@app.get("/status")
def read_status():
    return get_latest_status()
