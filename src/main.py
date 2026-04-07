from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.schemas import EventPayload, AchievementCreate, AchievementRead
from src.database import engine, get_db
import src.models as models
from src.rabbitmq import rabbitmq_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await rabbitmq_client.connect()
    yield
    await rabbitmq_client.close()

app = FastAPI(title="Achievement System", lifespan=lifespan)


@app.post("/achievements", response_model=AchievementRead)
async def create_achievement(achievement: AchievementCreate, db: AsyncSession = Depends(get_db)):
    new_ach = models.Achievement(**achievement.model_dump())
    db.add(new_ach)
    outbox_event = models.OutboxEvent(
        event_type="ACHIEVEMENT_CREATED",
        payload={
            "name": new_ach.name,
            "target_value": new_ach.target_value,
            "reward_id": new_ach.reward_id
        }
    )
    db.add(outbox_event)
    await db.commit()
    await db.refresh(new_ach)
    return new_ach


@app.post("/events")
async def receive_event(event: EventPayload):
    await rabbitmq_client.publish_event(event.model_dump())
    return {"status": "ok", "data": event.model_dump()}


@app.get("/progress/{player_id}")
async def get_player_progress(player_id: str, db: AsyncSession = Depends(get_db)):
    query = select(models.PlayerProgress).where(models.PlayerProgress.player_id == player_id)
    result = await db.execute(query)
    progress_records = result.scalars().all()
    return [
            {
                "achievement_id": p.achievement_id,
                "current_value": p.current_value,
                "is_completed": p.is_completed
            }
            for p in progress_records
    ]
