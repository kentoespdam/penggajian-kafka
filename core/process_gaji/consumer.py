import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import KAFKA_GROUP_ID, KAFKA_SERVER, KAFKA_TOPIC, LOGGER
from core.process_gaji.main import execute


async def consume_proses_gaji():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        group_id=KAFKA_GROUP_ID,
        enable_auto_commit=False,
        value_deserializer=lambda x: x.decode("utf-8"),
        max_poll_records=10,
        session_timeout_ms=60000,
        heartbeat_interval_ms=20000
    )
    await consumer.start()
    try:
        async for msg in consumer:
            batch_id = msg.value
            LOGGER.info(f"Consuming batch ID: {batch_id}")
            await execute(batch_id)
            await consumer.commit()
            LOGGER.info(f"Committed offset {msg.offset} for partition {msg.partition}")
            LOGGER.info(f"Task {batch_id} processed successfully")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception: ', e, flush=True)
    finally:
        await consumer.stop()

def start_consumer_in_background():
    async def _start_consumer():
        await consume_proses_gaji()

    return asyncio.create_task(_start_consumer())