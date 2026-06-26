import asyncio
from datetime import date, datetime

from confluent_kafka import Producer, Consumer, TopicPartition, cimpl
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import SerializationContext, MessageField

SHARED_KAFKA_CLIENT_PROPS = {
    "bootstrap.servers": "kafka.local.sipgate.com:29092",
    "security.protocol": "SASL_SSL",
    "sasl.mechanism": 'SCRAM-SHA-256',
    "sasl.username": "python-runner",
    "sasl.password": "crq6HPocZQSo",
    "ssl.ca.location": "/certs/ca-cert.pem",
}


def epoch_day(d: date) -> int:
    epoch_sec = datetime(year=d.year, month=d.month, day=d.day).timestamp()
    epoch_day = epoch_sec / (24 * 3600)
    return int(epoch_day)


def epoch_milli(d: datetime) -> int:
    return int(d.timestamp()) * 1000


def generic_source_part(db: str, table: str, created: datetime) -> dict:
    return {
        "version": "3.1.2.Final",
        "connector": "mysql",
        "name": "numbering.internal.cdc.dbnms",
        "snapshot": "false",
        "db": db,
        "table": table,
        "ts_ms": epoch_milli(created),
        "ts_us": epoch_milli(created) * 1000,
        "ts_ns": epoch_milli(created) * 1000 * 1000,
        "server_id": 0,
        "file": "mysql-bin.277229",
        "pos": 16668676,  # seems as irrelevant as the other meta info... is it?
        "row": 0,
        "thread": 1,
    }


def publish_avro_record(schema_registry_client: SchemaRegistryClient, producer: Producer, topic: str, key_schema_filename: str, key: dict[str, any], value_schema_filename: str, value: dict[str, any]) -> None:
    with open("/python-runner/e2e_tests/avro-schemata/" + key_schema_filename) as f:
        key_schema_str = f.read()
    with open("/python-runner/e2e_tests/avro-schemata/" + value_schema_filename) as f:
        value_schema_str = f.read()

    avro_key_serializer = AvroSerializer(schema_registry_client, key_schema_str, conf={"auto.register.schemas": True})
    avro_value_serializer = AvroSerializer(schema_registry_client, value_schema_str, conf={"auto.register.schemas": True})

    producer.produce(
        topic=topic,
        key=avro_key_serializer(key, SerializationContext(topic, MessageField.KEY)),
        value=avro_value_serializer(value, SerializationContext(topic, MessageField.VALUE)),
    )

    producer.flush()


async def likely_latest_msg_offset(consumer: Consumer, topic: str) -> int:
    offset = -1
    unchanged_for_iterations = 0
    while unchanged_for_iterations < 20:
        last_offset = offset
        _, high_watermark_offset = consumer.get_watermark_offsets(TopicPartition(topic, 0), timeout=1.0)
        # wierdly the high watermark offset is offset + 1
        offset = high_watermark_offset - 1

        if last_offset == offset:
            unchanged_for_iterations += 1

        await asyncio.sleep(0.500)

    return offset


def consume(consumer: Consumer, msg_count: int) -> list[cimpl.Message]:
    msgs: list[cimpl.Message] = []
    while len(msgs) < msg_count:
        msgs += consumer.consume(1, timeout=1.0)

    return msgs
