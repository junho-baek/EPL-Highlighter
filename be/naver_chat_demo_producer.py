import json
from datetime import datetime, timedelta, timezone
import time
from typing import Generator

from common.kafka.dto.chat_message import ChatMessage
from common.kafka.config import EPL_TOPIC_NAME, KAFKA_BROKER
from kafka import KafkaProducer
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 데모용 경기 ID 목록
DEMO_GAMES = [
    {
        "id": "2024112509",  # 맨유 vs 에버턴
        "date": "2024-11-26"
    },
    {
        "id": "2024112610050850203",  # 풀럼 vs 울버햄튼
        "date": "2024-11-26"
    }
]

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
            
            # data-value는 이미 ISO 형식이므로 변환 없이 그대로 사용
            if not time_posted:  # time_posted가 없는 경우에만 현재 시간 사용
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

def produce_demo_chat(game_id: str, broker_host: str = KAFKA_BROKER, topic: str = EPL_TOPIC_NAME):
    producer = KafkaProducer(
        bootstrap_servers=broker_host,
        value_serializer=lambda x: json.dumps(x.to_dict()).encode('utf-8')
    )
    
    try:
        driver = get_web_driver()
        for chat in crawl_comments(game_id, driver):
            producer.send(topic, value=chat)
            print(f"Sent: [{chat.time}]-[{chat.author}]-[{chat.message}] to topic: {topic}")
            time.sleep(0.5)  # 메시지 간 간격 추가
            
    except Exception as e:
        print(f"Error producing message: {e}")
    finally:
        producer.close()
        driver.quit()

if __name__ == "__main__":
    for game in DEMO_GAMES:
        print(f"\nStarting demo producer for game {game['id']} ({game['date']})")
        produce_demo_chat(game["id"])
        print(f"Finished processing game {game['id']}")
        time.sleep(2)  # 게임 간 간격 