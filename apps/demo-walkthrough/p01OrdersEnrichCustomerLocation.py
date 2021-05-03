import json
import os
from sqlalchemy import create_engine
from utils.db import sql_lookup
from utils.kafka import confluent_producer_async
from utils.msk import get_msk_records, msk_producer, extract_dms_records, get_msk_avro_records


TOPIC_IN = os.environ['TOPIC_IN']
TOPIC_OUT = os.environ['TOPIC_OUT']
KAFKA_BOOTSTRAP_SERVERS_READ = os.environ['KAFKA_BOOTSTRAP_SERVERS_READ']
KAFKA_BOOTSTRAP_SERVERS_WRITE = os.environ['KAFKA_BOOTSTRAP_SERVERS_WRITE']
DB_LOOKUP_CONN_STRING = os.environ["MYSQL_CONN_STRING"]


def main(event, context):

    # Get record from MSK topic
    records = get_msk_records(event)
    countInputRecords = len(records)

    # Initialize external services database connections
    lookup_engine = create_engine(DB_LOOKUP_CONN_STRING, echo=True)

    try:
        # Lookup attributes from external services
        get_customer_location = sql_lookup(
            engine=lookup_engine,
            sql="""
                SELECT
                    c.customer_name AS `Customer`,  /*We need to cast lookup field(s) to match incoming topic field(s)*/
                    c.address,
                    c.longitude,
                    c.latitude
                FROM customers c
                WHERE (c.customer_name) IN :values
            """,
            records=records,
            key_fields=['Customer', ],
            default={
                "address": None,
                "longitude": None,
                "latitude": None,
            }
        )

    except Exception as e:
        message = "Failed with error {e}"
        raise e

    out_records = [r for r in get_customer_location]

    message = f"Success processing {countInputRecords} records."
    print(message)

    countOutputRecords = len(out_records)

    message = f"Success processing {countOutputRecords} records."
    print(message)

    # Produce output records to Kafka
    # Initialize Kafka producer
    p = msk_producer(broker_urls=KAFKA_BOOTSTRAP_SERVERS_WRITE)
    topic = TOPIC_OUT
    keys = ['OrderNo', ]
    confluent_producer_async(p, out_records, keys, topic)

    body = {
        "message": message,
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
