from kafka import KafkaConsumer
from config import KAFKA_SERVER, PENGGAJIAN_TOPIC

consumer = KafkaConsumer(
    PENGGAJIAN_TOPIC, group_id=PENGGAJIAN_TOPIC, bootstrap_servers=KAFKA_SERVER
)

for message in consumer:
    print(
        "%s:%d:%d: key=%s value=%s"
        % (
            message.topic,
            message.partition,
            message.offset,
            message.key,
            message.value.decode("utf-8"),
        )
    )
