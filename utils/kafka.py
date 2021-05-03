import json


def delivery_report(err, decoded_message, original_message):
    if err is not None:
        print(err)


def confluent_producer_async(producer, messages, keys, topic):
    for msg in messages:
        key = "|".join([str(msg.get(k)) for k in keys])
        value = json.dumps(msg, default=str)

        producer.produce(
            topic,
            value,
            key,
            callback=lambda err, decoded_message, original_message=msg: delivery_report(  # noqa
                err, decoded_message, original_message
            ),
        )

    producer.flush()
