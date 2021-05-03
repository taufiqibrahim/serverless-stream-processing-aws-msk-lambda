import base64
import dateutil.parser as dp
import json
import os
from collections import OrderedDict
from copy import deepcopy
from datetime import datetime
from urllib.parse import quote
from sqlalchemy import text
from confluent_kafka import Consumer, Producer, KafkaException
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import SerializationContext


SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL')


def get_msk_records(event):
    event_records = event.get('records')
    records = list()
    for erk, erv in event_records.items():
        for r in erv:
            val = r.get('value')
            if val:
                try:
                    record = json.loads(base64.b64decode(val).decode('utf8'))
                    records.append(record)
                except Exception as e:
                    print('*' * 80)
                    print(r)
                    print('*' * 80)
                    print(str(e))
                    raise e

    number_of_records = len(records)
    print(f"Got {number_of_records} from MSK")
    return records


def get_msk_avro_records(event, topic):
    subject = "%s-value" % topic
    schema_registry_conf = {"url": SCHEMA_REGISTRY_URL}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    registered_schema = schema_registry_client.get_latest_version(subject)
    schema_str = registered_schema.schema.schema_str
    deserializer = AvroDeserializer(schema_str=schema_str,
                                    schema_registry_client=schema_registry_client)
    ctx = SerializationContext(topic=topic, field=None)
    event_records = event.get('records')
    records = list()
    for erk, erv in event_records.items():
        for r in erv:
            val = r.get('value')
            if val:
                try:
                    record = deserializer(value=base64.b64decode(val), ctx=ctx)
                    records.append(record)
                except Exception as e:
                    print('*' * 80)
                    print(r)
                    print('*' * 80)
                    print(str(e))
                    raise e

    number_of_records = len(records)
    print(f"Got {number_of_records} from MSK")
    return records


def msk_producer(broker_urls=None):
    if broker_urls:
        _broker_urls = broker_urls
    else:
        _broker_urls = os.environ['AWS_MSK_BOOTSTRAP_SERVERS_1']
    p_conf = {
        'bootstrap.servers': _broker_urls,
        'compression.type': 'gzip',
        #   'debug': 'topic,msg,broker',
        'queue.buffering.max.messages': 1000,
        'queue.buffering.max.ms': 100,
        # 'batch.num.messages': 50,
        'default.topic.config': {'acks': 'all'}
    }
    p = Producer(**p_conf)
    return p


def extract_dms_records(records, lowercase=False, include_metadata=False):
    extracts = list()
    for r in records:
        data = r.get("data", None)
        metadata = r.get("metadata", None)

        if data is not None:

            if isinstance(metadata, dict):
                timestamp = metadata.get("timestamp")
                data['timestamp'] = timestamp

            if include_metadata:
                if metadata is not None:
                    data.update(metadata)

            if lowercase:
                extract = {k.lower(): v for k, v in data.items()}
            else:
                extract = data
            extracts.append(extract)

    return extracts
