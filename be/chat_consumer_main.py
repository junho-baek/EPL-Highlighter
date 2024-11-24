import json

from common.model import ChatModel
from common.mongodb.client import db
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER
from kafka import KafkaConsumer


def consume_chat(broker_host: str, topic: str):
    """
    :param broker_host:  카프카 호스트 docker-compse.yml 에 나와있듯 localhost:19092 (변동가능)
    :param topic: 카프카 토픽
    """
    # Kafka Consumer 생성
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=broker_host,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="test-group",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),  # 메시지 디코딩
    )

    # 메시지 소비
    try:
        for record in consumer:
            chat: ChatModel = record.value
            time, author, message = chat["time"], chat["author"], chat["message"]

            print(
                f"""Received: [{time}]-[{author}]-[{message}] from topic: {topic}"""
            )

            db.chat.insert_one(chat)

    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_chat(KAFKA_BROKER, EPL_TOPIC_NAME)
