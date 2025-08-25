import asyncio
from typing import Optional, Set

from aiokafka import AIOKafkaConsumer
from core.config import KAFKA_SERVER, KAFKA_TOPIC, KAFKA_GROUP_ID, LOGGER
from core.process_gaji.main import execute


class KafkaItemConsumer:
    """
    Kafka consumer wrapper that manages start/stop lifecycle and message processing.
    Executes per-message processing in background threads to avoid blocking the event loop.
    """

    def __init__(self, max_concurrency: int = 4) -> None:
        self.bootstrap_servers: str = KAFKA_SERVER
        self.topic: str = KAFKA_TOPIC
        self.group_id: str = KAFKA_GROUP_ID
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._inflight: Set[asyncio.Task] = set()
        self._semaphore: Optional[asyncio.Semaphore] = asyncio.Semaphore(max_concurrency)

    async def start(self) -> None:
        """
        Initialize the Kafka consumer and start the background consumption loop.
        """
        if self.consumer is not None:
            LOGGER.warning("Kafka consumer already started")
            return

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            value_deserializer=lambda x: x.decode("utf-8"),
            enable_auto_commit=False,
        )
        await self.consumer.start()
        LOGGER.info(f"Kafka consumer started for topic={self.topic}, group_id={self.group_id}")

        # Start consumption loop as background task and keep a handle for graceful shutdown.
        self._task = asyncio.create_task(self._consume_loop(), name="kafka-consume-loop")

    async def _consume_loop(self) -> None:
        """
        Internal loop that receives messages and dispatches them for processing.
        """
        assert self.consumer is not None, "Consumer must be started before consuming"

        try:
            async for msg in self.consumer:
                try:
                    LOGGER.info(f"Received message on {msg.topic}@{msg.partition} offset={msg.offset}: {msg.value}")
                    # Schedule background processing (non-blocking)
                    self._schedule_processing(str(msg.value))
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    LOGGER.exception(f"Error scheduling message at offset={msg.offset}: {exc}")
        except asyncio.CancelledError:
            LOGGER.info("Consumption loop cancelled; stopping consumer...")
            raise
        except Exception as exc:
            LOGGER.exception(f"Fatal error in consumption loop: {exc}")
        finally:
            # Stop the underlying consumer if we own it.
            if self.consumer is not None:
                try:
                    await self.consumer.stop()
                    LOGGER.info("Kafka consumer stopped")
                except Exception as exc:
                    LOGGER.exception(f"Error while stopping Kafka consumer: {exc}")

    def _schedule_processing(self, batch_root_id: str) -> None:
        """
        Schedule processing of a single message in the background with concurrency control.
        """

        async def _runner() -> None:
            assert self._semaphore is not None
            async with self._semaphore:
                await self._process_message(batch_root_id)

        task = asyncio.create_task(_runner(), name=f"process-{batch_root_id}")
        self._inflight.add(task)
        task.add_done_callback(self._inflight.discard)

    async def _process_message(self, batch_root_id: str) -> None:
        """
        Process a message payload in a background thread to avoid blocking the event loop.
        """
        try:
            await asyncio.to_thread(execute, batch_root_id)
            LOGGER.info(f"Processed batch root ID: {batch_root_id}")
        except asyncio.CancelledError:
            LOGGER.info(f"Processing cancelled for batch root ID: {batch_root_id}")
            raise
        except Exception as exc:
            LOGGER.exception(f"Error processing batch root ID {batch_root_id}: {exc}")

    async def close(self) -> None:
        """
        Gracefully stop the consumption task and Kafka consumer, then wait for all in-flight tasks.
        """
        # Cancel background consume loop if running.
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                LOGGER.exception(f"Error awaiting consumption task shutdown: {exc}")
        self._task = None

        # Ensure the consumer is stopped.
        if self.consumer is not None:
            try:
                await self.consumer.stop()
                LOGGER.info("Kafka consumer stopped")
            except Exception as exc:
                LOGGER.exception(f"Error while stopping Kafka consumer: {exc}")
            finally:
                self.consumer = None

        # Await all in-flight processing tasks.
        if self._inflight:
            try:
                await asyncio.gather(*list(self._inflight), return_exceptions=True)
            finally:
                self._inflight.clear()


async def start_consumer() -> KafkaItemConsumer:
    """
    Factory to create and start a KafkaItemConsumer.
    Returns the consumer instance so the caller can close it on shutdown.
    """
    consumer = KafkaItemConsumer()
    await consumer.start()
    return consumer
