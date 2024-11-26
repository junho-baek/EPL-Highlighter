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
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER, NBA_TOPIC_NAME, WKOVO_TOPIC_NAME


schedule_service = ScheduleService()

# MongoDB 클라이언트 생성
client = AsyncIOMotorClient('mongodb://root:mymogopassword@localhost:17017', serverSelectionTimeoutMS=5000)
db = client.epl_highlighter

async def init_mongodb():
    try:
        # 연결 테스트
        await client.admin.command('ping')
        print("MongoDB 연결 성공")
        return True
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # MongoDB 연결 및 인덱스 초기화
    try:
        if not await init_mongodb():
            raise Exception("MongoDB 연결 실패")
            
        await init_db()
        print("MongoDB 인덱스 초기화 완료")
        
        # 스케줄 서비스 초기화
        await schedule_service.init()
        
        # Kafka 태스크 시작
        await asyncio.sleep(5)
        kafka_task = asyncio.create_task(kafka_to_socket())
        
        yield
    finally:
        if 'kafka_task' in locals():
            kafka_task.cancel()
            try:
                await kafka_task
            except asyncio.CancelledError:
                pass
        client.close()


app = FastAPI(lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 프론트엔드 주소
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO 서버 설정
sio = AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000"],  # 프론트엔드 주소
    logger=True,
    engineio_logger=True
)

# Socket.IO를 FastAPI에 마운트 (경로 변경)
socket_app = ASGIApp(sio)
app.mount("/socket.io", socket_app)  # /socket.io 경로로 변경

# MongoDB 인덱스 초기화
async def init_db():
    await db.chat.create_index([("source_id", 1)])
    await db.chat.create_index([("time", 1)])
    
    # 중복 체크를 위한 복합 인덱스 추가
    await db.chat.create_index([
        ("time", 1),
        ("author", 1),
        ("message", 1)
    ])

# MongoDB를 통한 중복 체크 함수
async def is_duplicate_socket_message(chat):
    existing_message = await db.chat.find_one({
        "time": chat["time"],
        "author": chat["author"],
        "message": chat["message"]
    })
    return existing_message is not None

# Kafka 컨슈머 재시도 로직
async def kafka_to_socket():
    while True:
        try:
            consumer = AIOKafkaConsumer(
                EPL_TOPIC_NAME,
                NBA_TOPIC_NAME,
                WKOVO_TOPIC_NAME,
                bootstrap_servers=[KAFKA_BROKER],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                group_id='socket_group',
                auto_offset_reset='latest'
            )
            await consumer.start()
            
            async for message in consumer:
                try:
                    chat = message.value
                    game_id = chat.get('source_id')
                    topic = message.topic
                    
                    if game_id:
                        is_duplicate = await is_duplicate_socket_message(chat)
                        if is_duplicate:
                            print(f"Socket: 중복 메시지 스킵: {chat['time']}-{chat['author']}-{chat['message']}")
                            continue
                        
                        print(f"소켓 메시지 전송 (토픽: {topic}): room={game_id}")
                        await sio.emit('chat', chat, room=game_id)
                        
                except Exception as e:
                    print(f"메시지 처리 중 오류: {e}")
            
        except Exception as e:
            print(f"Kafka consumer error: {e}")
            await asyncio.sleep(5)  # 재연결 전 대기
            continue
        finally:
            await consumer.stop()


@app.get("/update_schedule/{category}")
async def update_schedule(category: str):
    return await schedule_service.update_schedule(category)


@app.get("/schedules/{category}")
async def get_schedules(category: str):
    return await schedule_service.get_schedules(category)


@app.get("/reactions/{game_id}")
async def get_reactions(game_id: str):
    try:
        print(f"Fetching reactions for game_id: {game_id}")
        chats = db.chat.find({"source_id": game_id}).sort("time", 1)
        
        time_buckets = {}
        messages = []
        count = 0
        
        async for chat in chats:
            count += 1
            try:
                # KST 타임존 정보를 UTC로 변환
                time_str = chat.get("time")
                if '+0900' in time_str:
                    time_str = time_str.replace('+0900', '+09:00')
                
                chat_time = datetime.fromisoformat(time_str)
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
        
        print(f"Found {count} messages for game_id: {game_id}")
        
        sorted_reactions = [
            {"time": k, "count": v} 
            for k, v in sorted(time_buckets.items())
        ]
            
        return {
            "reactions": sorted_reactions,
            "messages": sorted(messages, key=lambda x: x["time"])
        }
    except Exception as e:
        print(f"Error in get_reactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/highlights/{game_id}")
async def get_highlights(game_id: str):
    try:
        chats = db.chat.find({"source_id": game_id}).sort("time", 1)
        time_buckets = {}
        
        async for chat in chats:
            time_str = chat.get("time")
            if '+0900' in time_str:
                time_str = time_str.replace('+0900', '+09:00')
            
            chat_time = datetime.fromisoformat(time_str)
            bucket = chat_time.replace(second=0, microsecond=0)
            bucket = bucket.replace(minute=bucket.minute - bucket.minute % 2)
            
            bucket_str = bucket.isoformat()
            time_buckets[bucket_str] = time_buckets.get(bucket_str, 0) + 1
        
        # 반응량이 가장 많은 상위 5개 구간을 하이라이트로 선정
        sorted_reactions = sorted(
            [{"time": k, "count": v} for k, v in time_buckets.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:5]
        
        return {
            "reactions": sorted_reactions,
            "highlights": sorted_reactions  # 현재는 동일하게 반환
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@sio.on('connect')
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.on('join')
async def join(sid, game_id):
    print(f"Client {sid} joined room {game_id}")
    await sio.enter_room(sid, game_id)
    print(f"Rooms for client {sid}: {sio.rooms(sid)}")

