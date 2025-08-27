import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import LOGGER
from core.process_gaji.main import execute


async def consume_proses_gaji(consumer: AIOKafkaConsumer):
    try:
        async for msg in consumer:
            batch_id = msg.value
            LOGGER.info(f"Consuming batch ID: {batch_id}")
            asyncio.create_task(execute(batch_id))
            await consumer.commit()
            LOGGER.info(f"Committed offset {msg.offset} for partition {msg.partition}")
            LOGGER.info(f"Task {batch_id} processed successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception: ', e, flush=True)
    finally:
        await consumer.stop()
