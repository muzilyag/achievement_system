import asyncio
import httpx
import os
from sqlalchemy.future import select
from src.database import async_session_maker
from src.models import OutboxEvent

WEBHOOK_URL = os.getenv("WEBHOOK_URL")


async def process_outbox():
    while True:
        async with async_session_maker() as db:
            query = select(OutboxEvent).where(OutboxEvent.status == "PENDING").limit(10)
            events = (await db.execute(query)).scalars().all()

            if not events:
                await asyncio.sleep(2)
                continue

            async with httpx.AsyncClient() as client:
                for event in events:
                    try:
                        response = await client.post(WEBHOOK_URL, json=event.payload, timeout=5.0)
                        response.raise_for_status()

                        event.status = "PROCESSED"
                        event.error_message = None
                        print(f"RELAY: Reward sent successfully (Event ID: {event.id})")

                    except Exception as e:
                        event.error_message = str(e)
                        print(f"RELAY: Failed to send reward (Event ID: {event.id}): {e}")

            await db.commit()

        await asyncio.sleep(1)

if __name__ == "__main__":
    print("Outbox Relay Service started...")
    asyncio.run(process_outbox())
