from datetime import datetime

from aiokafka import AIOKafkaConsumer

from core.config import LOGGER, PENGGAJIAN_TOPIC, KAFKA_SERVER, KAFKA_GROUP_ID
from core.enums import PROCESS_GAJI_STATUS
from core.process_gaji.phase1 import process_master
from core.process_gaji.phase2 import calculate_gaji_detail
from core.process_gaji.phase4 import build_potongan_gaji


async def consume_proses_gaji():
    consumer = AIOKafkaConsumer(
        PENGGAJIAN_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        group_id=KAFKA_GROUP_ID,
        session_timeout_ms=60000,
        heartbeat_interval_ms=3000,
    )
    await consumer.start()
    try:
        async for msg in consumer:
            batch_root_id = msg.value.decode("utf-8")
            LOGGER.info(f"Received message: {batch_root_id}")
            execute(batch_root_id)
    except Exception as e:
        LOGGER.error(e)
    finally:
        await consumer.stop()


def execute(batch_root_id: str) -> None:
    """Execute the gaji process."""
    start_time = datetime.now()
    phase1_status = process_master(batch_root_id)

    if phase1_status != PROCESS_GAJI_STATUS.SUCCESS:
        LOGGER.error(f"process gaji status: {phase1_status.value}")
        return

    LOGGER.info("\n=========================================================\n")

    phase2_status = calculate_gaji_detail(batch_root_id)
    if phase2_status != PROCESS_GAJI_STATUS.SUCCESS:
        LOGGER.error(f"calculate gaji detail status: {phase2_status.value}")
        return

    end_time = datetime.now()
    LOGGER.info(f"process gaji finished in {end_time - start_time}")

    LOGGER.info("\n=========================================================\n")
    # phase 3

    LOGGER.info("\n=========================================================\n")
    # phase 4
    build_potongan_gaji(batch_root_id)

    build_potongan_gaji(batch_root_id)
