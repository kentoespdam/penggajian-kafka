from aiokafka import AIOKafkaConsumer

from core.config import KAFKA_GROUP_ID, KAFKA_SERVER, KAFKA_TOPIC, LOGGER
from core.process_gaji.main import execute


async def consume_proses_gaji():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC, group_id=KAFKA_GROUP_ID, bootstrap_servers=KAFKA_SERVER,
        session_timeout_ms=60000,
        heartbeat_interval_ms=20000,
        auto_offset_reset="latest"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            batch_id = msg.value.decode("utf-8")
            LOGGER.info(f"Consuming batch ID: {batch_id}")
            execute(batch_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception: ', e, flush=True)
    finally:
        await consumer.stop()
