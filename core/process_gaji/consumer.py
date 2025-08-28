import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import LOGGER


async def heavy_task_execution():
    LOGGER.info("Starting heavy task execution")
    await asyncio.sleep(10)
    LOGGER.info("Heavy task execution completed")


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
            asyncio.create_task(heavy_task_execution())
    finally:
        await consumer.stop()
