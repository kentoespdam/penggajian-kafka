import asyncio

from aiokafka import AIOKafkaConsumer

from core.config import KAFKA_SERVER, KAFKA_TOPIC, KAFKA_GROUP_ID, LOGGER
from core.process_gaji.main import execute


class KafkaItemConsumer:
    def __init__(self):
        self.bootstrap_servers = KAFKA_SERVER
        self.topic=KAFKA_TOPIC
        self.group_id = KAFKA_GROUP_ID
        self.consumer = None


    async def start(self):
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda x: x.decode('utf-8')
        )
        await self.consumer.start()

    async def consume_message(self):
        try:
            async for msg in self.consumer:
                LOGGER.info(f"Received message: {msg.value}")
                batch_root_id=msg.value
                execute(batch_root_id)
                LOGGER.info(f"Processed batch root ID: {batch_root_id}")
        except Exception as e:
            LOGGER.error(e)
        finally:
            await self.consumer.stop()

    async def close(self):
        await self.consumer.stop()


async def start_consumer():
    consumer = KafkaItemConsumer()
    await consumer.start()
    asyncio.create_task(consumer.consume_message())
    return consumer