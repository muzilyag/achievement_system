import os
import json
import asyncio
import aio_pika
from sqlalchemy.future import select
from src.database import async_session_maker
from src.models import Achievement, PlayerProgress

RABBITMQ_URL = os.getenv("RABBITMQ_URL")

from sqlalchemy.ext.asyncio import AsyncSession

class AchievementManager:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def handle_event(self, event: dict) -> None:
        query = select(Achievement).where(Achievement.action_type == event["action_type"])
        result = await self.db.execute(query)
        achievements = result.scalars().all()

        for ach in achievements:
            prog_query = select(PlayerProgress).where(
                PlayerProgress.player_id == event["player_id"],
                PlayerProgress.achievement_id == ach.id
            )
            prog_result = await self.db.execute(prog_query)
            progress = prog_result.scalars().first()

            if not progress:
                progress = PlayerProgress(
                    player_id=event["player_id"],
                    achievement_id=ach.id,
                    current_value=0,
                    is_completed=False
                )
                self.db.add(progress)

            progress.increment(event["value"])
            
            just_completed = progress.check_completion(ach.target_value)

            if just_completed:
                print(f"REWARD TRIGGER: Send {ach.reward_id} to {event['player_id']}")
                # TODO: Здесь в будущем будет запись в таблицу outbox_events

        await self.db.commit()


async def process_event(event_data: dict) -> None:
    async with async_session_maker() as db:
        manager = AchievementManager(db)
        await manager.handle_event(event_data)


async def main() -> None:
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue("events_queue", durable=True)
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await process_event(json.loads(message.body.decode()))

if __name__ == "__main__":
    asyncio.run(main())
