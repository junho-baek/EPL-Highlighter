from datetime import datetime, timedelta
import json

from kafka import KafkaConsumer

from common.kafka.dto.chat_message import ChatMessage
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER
from common.mongodb.client import db
from common.model.chat_model import ChatModel


TIME_INTERVAL_MINUTE = 5


def get_time_interval(time: datetime) -> tuple[datetime, datetime]:
    interval_start_time = time.replace(second=0, microsecond=0)
    interval_start_time -= timedelta(minutes=time.minute %
                                     TIME_INTERVAL_MINUTE)

    interval_end_time = interval_start_time + \
        timedelta(minutes=TIME_INTERVAL_MINUTE)

    return interval_start_time, interval_end_time


def process_statistic(chat: ChatModel):
    source_id = chat.source_id
    source_type = chat.source_type
    interval_start_time = chat.interval_start_time
    interval_end_time = chat.interval_end_time

    query = {
        "interval_start_time": interval_start_time,
        "interval_end_time": interval_end_time,
        "source_id": source_id,
        "source_type": source_type,
    }

    chat_statistic = db.chat_statistic.find_one(query)
    if chat_statistic is None:
        chat_statistic = {
            "interval_start_time": interval_start_time,
            "interval_end_time": interval_end_time,
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
            chat: ChatMessage = record.value
            time_str, author, message = chat["time"], chat["author"], chat["message"]

            print(
                f"""Received: [{time_str}]-[{author}]-[{message}] from topic: {topic}"""
            )

            time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S%z")
            (interval_start_time, interval_end_time) = get_time_interval(time)

            chat_model = ChatModel(
                source_id=chat["source_id"],
                source_type=chat["source_type"],
                time=time,
                message=message,
                author=author,
                interval_start_time=interval_start_time,
                interval_end_time=interval_end_time,
            )

            db.chat.insert_one(chat_model.__dict__)
            process_statistic(chat_model)

    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        consumer.close()


if __name__ == "__main__":
    consume_chat(KAFKA_BROKER, EPL_TOPIC_NAME)
