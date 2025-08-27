import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import KAFKA_TOPIC, KAFKA_SERVER, KAFKA_GROUP_ID, LOGGER
from core.process_gaji.main import execute


async def main():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        group_id=KAFKA_GROUP_ID,
        enable_auto_commit=False,
        value_deserializer=lambda x: x.decode("utf-8"),
        max_poll_records=1,

        # Heartbeat and session
        session_timeout_ms=45000,  # 45 seconds
        heartbeat_interval_ms=15000,  # 15 seconds
        max_poll_interval_ms=300000,  # 5 minutes

        # Isolation level
        isolation_level="read_committed",
    )

    await consumer.start()
    LOGGER.info("Kafka consumer started, waiting for messages...")
    try:
        async for msg in consumer:
            asyncio.create_task(execute(msg.value))
            await consumer.commit()
    finally:
        await consumer.stop()
        LOGGER.info("Kafka consumer stopped")


if __name__ == "__main__":
    asyncio.run(main())
