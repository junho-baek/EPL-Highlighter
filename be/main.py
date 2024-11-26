from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, HTTPException
from socketio import AsyncServer, ASGIApp
from kafka import KafkaConsumer
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

from game_schedule.service import ScheduleService
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER


schedule_service = ScheduleService()

# MongoDB 연결 설정
client = AsyncIOMotorClient('mongodb://localhost:27017')
db = client.epl_highlighter  # 데이터베이스 이름


@asynccontextmanager
async def lifespan(app: FastAPI):
    # data 디렉토리 생성 및 초기 스케줄 데이터 로드
    await schedule_service.init()
    
    try:
        # Kafka 백그라운드 태스크 시작 전 잠시 대기
        await asyncio.sleep(5)  # Kafka 서버 준비 대기
        kafka_task = asyncio.create_task(kafka_to_socket())
        yield
    finally:
        # 종료 시 태스크 정리
        kafka_task.cancel()
        try:
            await kafka_task
        except asyncio.CancelledError:
            pass


app = FastAPI(lifespan=lifespan)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/update_schedule/{category}")
async def update_schedule(category: str):
    return await schedule_service.update_schedule(category)


@app.get("/schedules/{category}")
async def get_schedules(category: str):
    return await schedule_service.get_schedules(category)


@app.get("/reactions/{game_id}")
async def get_reactions(game_id: str):
    try:
        chats = db.chat.find({"source_id": game_id})
        
        time_buckets = {}
        messages = []
        
        async for chat in chats:
            try:
                chat_time = datetime.fromisoformat(chat.get("time"))
                # 2분 단위로 시간 버킷 생성
                bucket = chat_time.replace(second=0, microsecond=0)
                bucket = bucket.replace(minute=bucket.minute - bucket.minute % 2)
                
                bucket_str = bucket.isoformat()
                time_buckets[bucket_str] = time_buckets.get(bucket_str, 0) + 1
                
                messages.append({
                    "time": chat.get("time"),
                    "author": chat.get("author"),
                    "message": chat.get("message"),
                    "source_type": chat.get("source_type")
                })
            except ValueError as e:
                print(f"Error processing chat time: {e}")
                continue
        
        # 시간순 정렬된 반응량 데이터
        sorted_reactions = [
            {"time": k, "count": v} 
            for k, v in sorted(time_buckets.items())
        ]
            
        return {
            "reactions": sorted_reactions,
            "messages": sorted(messages, key=lambda x: x["time"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000"],  # 프론트엔드 주소 명시
    logger=True,
    engineio_logger=True
)
socket_app = ASGIApp(sio, app)
app = socket_app  # 여기서 app을 교체

# Kafka에서 메시지를 읽어서 Socket.IO로 전송하는 백그라운드 태스크
async def kafka_to_socket():
    try:
        consumer = AIOKafkaConsumer(
            EPL_TOPIC_NAME,
            bootstrap_servers=[KAFKA_BROKER],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            group_id='socket_group',
            auto_offset_reset='latest'  # 최신 메시지부터 받기
        )
        await consumer.start()
        
        async for message in consumer:
            try:
                game_id = message.value.get('source_id')
                if game_id:
                    print(f"Sending message to room {game_id}: {message.value}")
                    await sio.emit('chat', message.value, room=game_id)
            except Exception as e:
                print(f"Error processing message: {e}")
                print(f"Message value: {message.value}")
    except Exception as e:
        print(f"Kafka consumer error: {e}")
    finally:
        await consumer.stop()

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.on('join')
async def join(sid, game_id):
    print(f"Client {sid} joined room {game_id}")
    await sio.enter_room(sid, game_id)
    print(f"Rooms for client {sid}: {sio.rooms(sid)}")

