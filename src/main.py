from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas import EventPayload, AchievementCreate, AchievementRead
from src.database import get_db
import src.models as models
from src.rabbitmq import rabbitmq_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbitmq_client.connect()
    yield
    await rabbitmq_client.close()

app = FastAPI(title="Achievement System", lifespan=lifespan)

@app.post("/achievements", response_model=AchievementRead)
async def create_achievement(achievement: AchievementCreate, db: AsyncSession = Depends(get_db)):
    new_ach = models.Achievement(**achievement.model_dump())
    db.add(new_ach)
    await db.commit()
    await db.refresh(new_ach)
    return new_ach

@app.post("/events")
async def receive_event(event: EventPayload):
    await rabbitmq_client.publish_event(event.model_dump())
    return {"status": "ok", "data": event.model_dump()}
