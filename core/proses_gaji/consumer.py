from aiokafka import AIOKafkaConsumer

from core.config import KAFKA_GROUP_ID, KAFKA_SERVER, PENGGAJIAN_TOPIC
from core.proses_gaji import proses_gaji
from icecream import ic


async def consume_proses_gaji():
    consumer = AIOKafkaConsumer(
        PENGGAJIAN_TOPIC, group_id=KAFKA_GROUP_ID, bootstrap_servers=KAFKA_SERVER,
        session_timeout_ms=60000,
        heartbeat_interval_ms=20000
    )
    await consumer.start()
    try:
        async for msg in consumer:
            batch_id = msg.value.decode("utf-8")
            ic(batch_id)
            proses_gaji.execute(batch_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('Exception: ', e, flush=True)
    finally:
        await consumer.stop()
