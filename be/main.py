from contextlib import asynccontextmanager

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from game_schedule.service import ScheduleService


schedule_service = ScheduleService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await schedule_service.init()

    yield


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
