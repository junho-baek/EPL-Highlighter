from datetime import datetime, timedelta, timezone
import json
import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from aiokafka import AIOKafkaConsumer

from common.kafka.dto.chat_message import ChatMessage
from common.kafka.config import (
    KAFKA_BROKER, 
    EPL_TOPIC_NAME, 
    NBA_TOPIC_NAME, 
    WKOVO_TOPIC_NAME
)
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


async def process_statistic(chat_model):
    source_id = chat_model.source_id
    source_type = chat_model.source_type
    interval_start_time = datetime.strptime(chat_model.interval_start_time, "%Y-%m-%dT%H:%M:%S%z")
    interval_end_time = datetime.strptime(chat_model.interval_end_time, "%Y-%m-%dT%H:%M:%S%z")

    query = {
        "interval_start_time": interval_start_time,
        "interval_end_time": interval_end_time,
        "source_id": source_id,
        "source_type": source_type,
    }

    chat_statistic = await db.chat_statistic.find_one(query)
    if chat_statistic is None:
        chat_statistic = {
            "interval_start_time": interval_start_time,
            "interval_end_time": interval_end_time,
            "source_id": source_id,
            "source_type": source_type,
            "count": 0,
        }
    chat_statistic["count"] += 1

    await db.chat_statistic.update_one(
        query, {"$set": chat_statistic}, upsert=True
    )


async def is_duplicate_message(db, chat):
    # 메시지 고유 식별자 생성
    existing_message = await db.chat.find_one({
        "time": chat["time"],
        "author": chat["author"],
        "message": chat["message"]
    })
    return existing_message is not None


async def consume_chat(broker_host: str):
    client = AsyncIOMotorClient('mongodb://root:mymogopassword@localhost:17017')
    db = client.epl_highlighter
    
    try:
        # 여러 토픽을 한번에 구독
        consumer = AIOKafkaConsumer(
            EPL_TOPIC_NAME,
            NBA_TOPIC_NAME,
            WKOVO_TOPIC_NAME,
            bootstrap_servers=[broker_host],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='chat_consumer_group',
            auto_offset_reset='earliest'
        )
        
        await consumer.start()
        print(f"Kafka 컨슈머 시작됨 - 토픽: EPL, NBA, WKOVO")
        
        async for message in consumer:
            try:
                chat = message.value
                topic = message.topic
                print(f"메시지 수신됨 (토픽: {topic}): {chat}")
                
                # MongoDB에서 중복 체크
                if await is_duplicate_message(db, chat):
                    print(f"중복 메시지 스킵: {chat['time']}-{chat['author']}-{chat['message']}")
                    continue
                
                # ISO 형식 문자열을 datetime으로 파싱
                time = datetime.strptime(chat["time"], "%Y-%m-%dT%H:%M:%S%z")
                
                # 인터벌 시간 계산
                interval_start_time, interval_end_time = get_time_interval(time)
                
                chat_model = ChatModel(
                    source_id=chat["source_id"],
                    source_type=chat["source_type"],
                    time=chat["time"],
                    message=chat["message"],
                    author=chat["author"],
                    interval_start_time=interval_start_time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    interval_end_time=interval_end_time.strftime("%Y-%m-%dT%H:%M:%S%z")
                )
                
                # MongoDB에 저장
                await db.chat.insert_one(chat_model.__dict__)
                print(f"MongoDB에 저장됨: {chat['time']}-{chat['author']}-{chat['message']}")
                
                # 통계 처리
                await process_statistic(chat_model)
                print(f"통계 처리됨: {interval_start_time} ~ {interval_end_time}")
                
            except Exception as e:
                print(f"메시지 처리 중 에러 발생: {e}")
                continue
                
    except Exception as e:
        print(f"Kafka 컨슈머 에러: {e}")
    finally:
        await consumer.stop()
        client.close()


if __name__ == "__main__":
    # 토픽 파라미터 제거
    asyncio.run(consume_chat(KAFKA_BROKER))
