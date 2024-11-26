import json
from datetime import datetime, timedelta, timezone
import time
from typing import Generator
import os

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

def get_web_driver() -> WebDriver:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def crawl_comments(page_id: str, driver: WebDriver) -> Generator[ChatMessage, None, None]:
    url = f"https://m.sports.naver.com/game/{page_id}/cheer"
    driver.get(url)
    time.sleep(3)
    
    comments = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_comment")
    for comment_element in comments:
        try:
            content = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_contents").text
            author = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_name").text
            time_posted = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_date").get_attribute("data-value")
            
            if not time_posted:
                time_posted = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S%z")
            
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

def produce_chat(page_id: str, expire_datetime: datetime, broker_host: str, topic: str):
    producer = KafkaProducer(
        bootstrap_servers=broker_host,
        value_serializer=lambda x: json.dumps(x.to_dict()).encode('utf-8')
    )
    
    try:
        driver = get_web_driver()
        while datetime.now(timezone(timedelta(hours=9))) < expire_datetime:
            for chat in crawl_comments(page_id, driver):
                producer.send(topic, value=chat)
                print(f"메시지 전송: [{chat.time}] {chat.author}: {chat.message}")
                time.sleep(0.5)
            time.sleep(5)
            
    except Exception as e:
        print(f"채팅 수집 중 오류 발생: {e}")
    finally:
        producer.close()
        driver.quit()

def load_schedules():
    schedules = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    schedule_files = {
        'WKOVO': (os.path.join(base_dir, 'data', 'wkovo_schedule.json'), WKOVO_TOPIC_NAME),
        'NBA': (os.path.join(base_dir, 'data', 'nba_schedule.json'), NBA_TOPIC_NAME),
        'EPL': (os.path.join(base_dir, 'data', 'epl_schedule.json'), EPL_TOPIC_NAME)
    }
    
    now = datetime.now(timezone(timedelta(hours=9)))
    
    for league, (file_path, topic) in schedule_files.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for match in data['matches']:
                    match_time = datetime.fromisoformat(
                        match['timestamp'].replace('Z', '+00:00')
                    ).astimezone(timezone(timedelta(hours=9)))
                    
                    if match_time > now:
                        page_id = match['cheer_url'].split('/')[-2]
                        schedules.append({
                            'timestamp': match_time,
                            'page_id': page_id,
                            'topic': topic
                        })
        except FileNotFoundError:
            print(f"Warning: Schedule file not found for {league}: {file_path}")
            continue
    
    return schedules

if __name__ == "__main__":
    print("네이버 스포츠 채팅 수집기 시작...")
    schedules = load_schedules()
    
    if not schedules:
        print("수집할 경기가 없습니다.")
        exit(0)
        
    print(f"\n총 {len(schedules)}개의 경기 채팅을 수집합니다.")
    
    for schedule in schedules:
        match_time = schedule['timestamp'].strftime("%Y년 %m월 %d일 %H:%M")
        expire_time = (schedule['timestamp'] + timedelta(hours=2)).strftime("%H:%M")
        
        print(f"\n[{match_time}] 경기 채팅 수집 시작")
        print(f"경기 ID: {schedule['page_id']}")
        print(f"수집 종료 예정 시각: {expire_time}")
        
        produce_chat(
            page_id=schedule['page_id'],
            expire_datetime=schedule['timestamp'] + timedelta(hours=2),
            broker_host=KAFKA_BROKER,
            topic=schedule['topic']
        )
        print(f"[{schedule['page_id']}] 경기 채팅 수집 완료")
        time.sleep(2)
    
    print("\n모든 경기 채팅 수집이 완료되었습니다.")
