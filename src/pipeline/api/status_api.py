# src/api/status_api.py
from fastapi import FastAPI
from src.pipeline.daemon.status import get_latest_status

app = FastAPI()

@app.get("/status")
def read_status():
    return get_latest_status()
