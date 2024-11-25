import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from game_schedule.service import ScheduleService

schedule_service = ScheduleService()


async def update_game_schedule():
    print("스케쥴 실행중...")
    await schedule_service.update_schedule("epl")
    print("완료")


async def main():
    """
    reference: https://github.com/agronholm/apscheduler/blob/3.x/examples/schedulers/asyncio_.py
    """
    # Run at 00:00 on the first day of each month
    trigger = CronTrigger(day="1", hour="0", minute="0")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(update_game_schedule  , trigger=trigger)
    scheduler.start()

    print("Press Ctrl+{} to exit".format("Break" if os.name == "nt" else "C"))

    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
