from fastapi import FastAPI
from typing import Any
from src.schemas import EventPayload

app = FastAPI(title="Achivement System")


@app.post("/events")
async def receive_event(event: EventPayload) -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "System is runnig!",
        "data": event.model_dump()
    }
