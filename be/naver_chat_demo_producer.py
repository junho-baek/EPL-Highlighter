import json
from datetime import datetime, timedelta, timezone
import time
import asyncio
from typing import Generator

from common.kafka.dto.chat_message import ChatMessage

from common.kafka.config import (
    KAFKA_BROKER, 
    EPL_TOPIC_NAME, 
    NBA_TOPIC_NAME, 
    WKOVO_TOPIC_NAME
)
from kafka import KafkaProducer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import kafka.errors

# 데모용 경기 일정 데이터
DEMO_SCHEDULES = [
    {
        'timestamp': datetime(2024, 11, 26, 21, 0).replace(tzinfo=timezone(timedelta(hours=9))),
        'page_id': '2024112627',
        'topic': NBA_TOPIC_NAME,
        'description': '시카고 워싱턴'
    },
    {
        'timestamp': datetime(2024, 11, 26, 23, 30).replace(tzinfo=timezone(timedelta(hours=9))),
        'page_id': '2024112610050850203',
        'topic': EPL_TOPIC_NAME,
        'description': '풀럼 vs 울버햄튼'
    },
    {
        'timestamp': datetime(2024, 11, 26, 23, 30).replace(tzinfo=timezone(timedelta(hours=9))),
        'page_id': '2024112614',
        'topic': NBA_TOPIC_NAME,
        'description': '마이애미 '
    }
]

def get_web_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

async def crawl_comments(page_id: str, driver: WebDriver) -> Generator[ChatMessage, None, None]:
    url = f"https://m.sports.naver.com/game/{page_id}/cheer"
    driver.get(url)
    time.sleep(3)
    
    prev_comments = set()  # 이전에 수집한 댓글들을 저장
    retry_count = 0  # 동일한 결과가 나온 횟수를 카운트
    
    while True:
        current_comments = set()
        comments = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_comment")
        
        for comment_element in comments:
            try:
                content = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_contents").text
                author = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_name").text
                time_posted = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_date").get_attribute("data-value")
                
                if not time_posted:
                    time_posted = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S%z")
                
                comment_key = f"{author}:{content}:{time_posted}"
                current_comments.add(comment_key)
                
                if comment_key not in prev_comments:
                    yield ChatMessage(
                        source_id=page_id,
                        source_type="naver",
                        time=time_posted,
                        message=content,
                        author=author
                    )
            except Exception as e:
                print(f"댓글 파싱 중 오류 발생: {str(e)}")
                continue
        
        if current_comments == prev_comments:
            retry_count += 1
            if retry_count >= 3:  # 3번 연속으로 동일한 결과가 나오면
                print(f"3번 연속 동일한 결과 감지. 다음 크롤링으로 넘어갑니다.")
                break
        else:
            retry_count = 0  # 다른 결과가 나오면 카운트 리셋
            
        prev_comments = current_comments
        time.sleep(5)

async def produce_chat(page_id: str, expire_datetime: datetime, broker_host: str, topic: str, description: str):
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=broker_host,
                value_serializer=lambda x: json.dumps(x.to_dict()).encode('utf-8'),
                api_version=(0, 10, 1),  # API 버전 명시
                request_timeout_ms=5000,  # 타임아웃 설정
                retry_backoff_ms=1000     # 재시도 간격
            )
            
            try:
                driver = get_web_driver()
                print(f"[{description}] 채팅 수집 시작")
                
                while datetime.now(timezone(timedelta(hours=9))) < expire_datetime:
                    for chat in crawl_comments(page_id, driver):
                        producer.send(topic, value=chat)
                        print(f"[{description}] 메시지 전송: [{chat.time}] {chat.author}: {chat.message}")
                        await asyncio.sleep(0.5)
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"[{description}] 채팅 수집 중 오류 발생: {e}")
            finally:
                producer.close()
                driver.quit()
                print(f"[{description}] 채팅 수집 완료")
                return  # 정상 종료
                
        except kafka.errors.NoBrokersAvailable:
            retry_count += 1
            print(f"카프카 브로커 연결 실패 (시도 {retry_count}/{max_retries})")
            if retry_count < max_retries:
                print(f"5초 후 재시도...")
                await asyncio.sleep(5)
            else:
                print(f"[{description}] 최대 재시도 횟수 초과. 작업을 종료합니다.")
                return
        except Exception as e:
            print(f"[{description}] 예상치 못한 오류 발생: {e}")
            return

async def main():
    print("네이버 스포츠 채팅 데모 수집기 시작...")
    print(f"카프카 브로커 주소: {KAFKA_BROKER}")  # 브로커 주소 출력
    
    if not DEMO_SCHEDULES:
        print("수집할 경기가 없습니다.")
        return
        
    print(f"\n총 {len(DEMO_SCHEDULES)}개의 경기 채팅을 동시에 수집합니다.")
    
    tasks = []
    for schedule in DEMO_SCHEDULES:
        match_time = schedule['timestamp'].strftime("%Y년 %m월 %d일 %H:%M")
        expire_time = (schedule['timestamp'] + timedelta(hours=2)).strftime("%H:%M")
        
        print(f"\n[{match_time}] {schedule['description']} 경기")
        print(f"경기 ID: {schedule['page_id']}")
        print(f"수집 종료 예정 시각: {expire_time}")
        
        task = asyncio.create_task(
            produce_chat(
                page_id=schedule['page_id'],
                expire_datetime=schedule['timestamp'] + timedelta(hours=2),
                broker_host=KAFKA_BROKER,
                topic=schedule['topic'],
                description=schedule['description']
            )
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    print("\n모든 경기 채팅 수집이 완료되었습니다.")

if __name__ == "__main__":
    asyncio.run(main())