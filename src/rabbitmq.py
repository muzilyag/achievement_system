import json
import os
import aio_pika
from aio_pika.abc import AbstractConnection, AbstractChannel

RABBITMQ_URL = os.getenv("RABBITMQ_URL")


class RabbitMQClient:
    def __init__(self):
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(RABBITMQ_URL)
        self.channel = await self.connection.channel()

    async def close(self):
        if self.connection:
            await self.connection.close()

    async def publish_event(self, event_dict: dict) -> None:
        if not self.channel:
            raise RuntimeError("RabbitMQ channel is not initialized")
        queue = await self.channel.declare_queue("events_queue", durable=True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(body=json.dumps(event_dict).encode()),
            routing_key=queue.name,
        )


rabbitmq_client = RabbitMQClient()
