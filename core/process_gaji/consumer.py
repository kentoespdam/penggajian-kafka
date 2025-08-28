import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import LOGGER
from core.process_gaji.main import execute


async def consume_proses_gaji(consumer: AIOKafkaConsumer, stop_event: asyncio.Event):
    try:
        while not stop_event.is_set():
            try:
                msg = await consumer.getone()
            except Exception as e:
                LOGGER.error(e)
                continue

            payload = msg.value
            await consumer.commit()
            LOGGER.info(f"Received message: {payload}")
            asyncio.create_task(execute(payload))
    finally:
        await consumer.stop()
