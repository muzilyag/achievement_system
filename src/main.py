import os
import json
import asyncio
import aio_pika
from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.schemas import EventPayload, AchievementCreate, AchievementRead
from src.database import engine, get_db
import src.models as models
from src.rabbitmq import rabbitmq_client

active_connections = {}

async def listen_notifications():
    try:
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        connection = await aio_pika.connect_robust(rabbitmq_url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange("realtime_notifications", aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue("", exclusive=True)
        await queue.bind(exchange)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    data = json.loads(message.body.decode())
                    pid = data.get("player_id")
                    if pid in active_connections:
                        await active_connections[pid].send_json(data)
    except Exception as e:
        print(f"RabbitMQ Listener Error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    await rabbitmq_client.connect()
    task = asyncio.create_task(listen_notifications())
    yield
    task.cancel()
    await rabbitmq_client.close()

app = FastAPI(title="Achievement System", lifespan=lifespan)

@app.post("/achievements", response_model=AchievementRead)
async def create_achievement(achievement: AchievementCreate, db: AsyncSession = Depends(get_db)):
    new_ach = models.Achievement(**achievement.model_dump())
    db.add(new_ach)
    outbox_event = models.OutboxEvent(
        event_type="ACHIEVEMENT_CREATED",
        payload={
            "status": "success",
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
    return {
        "status": "success",
        "player_id": player_id,
        "data": [
            {
                "achievement_id": p.achievement_id,
                "current_value": p.current_value,
                "is_completed": p.is_completed
            }
            for p in progress_records
        ]
    }

@app.delete("/progress/{player_id}/reset_all")
async def reset_all_progress(player_id: str, db: AsyncSession = Depends(get_db)):
    query = delete(models.PlayerProgress).where(models.PlayerProgress.player_id == player_id)
    result = await db.execute(query)
    await db.commit()
    return {
        "status": "success",
        "player_id": player_id,
        "action": "full_reset",
        "message": f"Весь прогресс для игрока {player_id} был успешно удален"
    }

@app.delete("/progress/{player_id}/{achievement_id}")
async def delete_player_progress(player_id: str, achievement_id: int, db: AsyncSession = Depends(get_db)):
    query = delete(models.PlayerProgress).where(
            models.PlayerProgress.player_id == player_id,
            models.PlayerProgress.achievement_id == achievement_id
    )
    await db.execute(query)
    await db.commit()
    return {
        "status": "success",
        "player_id": player_id,
        "achievement_id": achievement_id,
        "message": f"Прогресс достижения {achievement_id} для игрока {player_id} сброшен"
    }

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await websocket.accept()
    active_connections[player_id] = websocket
    try:
        while True:
            await websocket.receive_bytes()
    except WebSocketDisconnect:
        pass
    finally:
        active_connections.pop(player_id, None)
