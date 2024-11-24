import dataclasses
import json
from datetime import datetime, timedelta

from be.common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER
import pytchat
from kafka import KafkaProducer

from common.model.ChatModel import ChatModel


def produce_chat(
    video_id: str, expire_datetime: datetime, broker_host: str, topic: str
):
    """
    :param video_id: 네이버 페이지 아이디 (https://www.youtube.com/watch?v={video_id})
    :param expire_datetime: 클롤링을 중단할 시각
    :param broker_host:  카프카 호스트 docker-compse.yml 에 나와있듯 localhost:19092 (변동가능)
    :param topic: 카프카 토픽
    """
    producer = KafkaProducer(
        bootstrap_servers=broker_host,
        value_serializer=lambda chat_model: json.dumps(
            dataclasses.asdict(chat_model)
        ).encode("utf-8"),
    )
    chat_crawler = pytchat.create(video_id=video_id)

    while chat_crawler.is_alive() and datetime.now() < expire_datetime:
        for c in chat_crawler.get().sync_items():
            chat: ChatModel = ChatModel(
                time=c.datetime, author=c.author.name, message=c.message
            )

            producer.send(topic, value=chat)

            print(
                f"""Sent: [{
                    c.datetime}]-[{c.author.name}]-[{c.message}] to topic: {topic}"""
            )
    producer.close()


if __name__ == "__main__":
    produce_chat(
        "FN-wSx3ryg0", datetime.now() + timedelta(days=3), KAFKA_BROKER, EPL_TOPIC_NAME
    )
