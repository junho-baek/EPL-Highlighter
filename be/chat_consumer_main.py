from datetime import datetime, timedelta
import json

from common.model import ChatModel
from common.mongodb.client import db
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER
from kafka import KafkaConsumer


def process_statistic(chat: ChatModel):
    now = datetime.now()

    TIME_INTERVAL_MINUTE = 5

    time = now.replace(second=0, microsecond=0)
    time -= timedelta(minutes=now.minute % TIME_INTERVAL_MINUTE)

    source_id = chat["source_id"]
    source_type = chat["source_type"]

    query = {
        "time": time,
        "source_id": source_id,
        "source_type": source_type,
    }

    chat_statistic = db.chat_statistic.find_one(query)
    if chat_statistic is None:
        chat_statistic = {
            "time": time,
            "source_id": source_id,
            "source_type": source_type,
            "count": 0,
        }
    chat_statistic["count"] += 1

    db.chat_statistic.update_one(
        query, {"$set": chat_statistic}, upsert=True)


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
            process_statistic(chat)

    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_chat(KAFKA_BROKER, EPL_TOPIC_NAME)
