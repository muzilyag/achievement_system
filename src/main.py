from fastapi import FastAPI
from typing import Any
from contextlib import asynccontextmanager
from src.schemas import EventPayload
from src.database import engine, Base 
import src.models

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Achievement System", lifespan=lifespan)


@app.post("/events")
async def receive_event(event: EventPayload) -> dict[str, Any]:
    return {
        "status": "ok",
        "message": "System is running!",
        "data": event.model_dump()
    }
