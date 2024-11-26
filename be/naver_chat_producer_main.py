import dataclasses
import json
import multiprocessing
import time
from datetime import datetime, timedelta
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


def produce_chat(page_id: str, expire_datetime: datetime, broker_host: str, topic: str):
    """
    :param page_id: 네이버 페이지 아이디 (https://m.sports.naver.com/game/{page_id}/cheer)
    :param expire_datetime: 클롤링을 중단할 시각
    :param broker_host:  카프카 호스트 docker-compse.yml 에 나와있듯 localhost:19092 (변동가능)
    :param topic: 카프카 토픽
    """
    producer = KafkaProducer(
        bootstrap_servers=broker_host,
        value_serializer=lambda x: json.dumps(x.to_dict()).encode('utf-8')
    )
    for comment in crawl_comment(page_id, get_web_driver()):
        if expire_datetime < datetime.now():
            break
        chat = ChatMessage(
            source_id=page_id,
            source_type="naver",
            time=comment.time,
            author=comment.author,
            message=comment.message
        )
        producer.send(topic, value=chat)
        print(
            f"""Sent: [{
                comment.time}]-[{comment.author}]-[{comment.message}] to topic: {topic}"""
        )
    producer.close()


def get_web_driver() -> WebDriver:
    user_agent = "Mozilla/5.0 (Linux; Android 9; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.83 Mobile Safari/537.36"

    options = Options()
    options.add_argument("user-agent=" + user_agent)
    options.add_argument("--window-size=1600,1000")
    # options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )


def crawl_comment(page_id: str, driver: WebDriver) -> Generator[ChatMessage, None, None]:
    """
    :param page_id: 네이버 페이지 아이디 (https://m.sports.naver.com/game/{page_id}/cheer)
    """
    # 페이지 로드
    url = f"https://m.sports.naver.com/game/{page_id}/cheer"
    driver.get(url)
    time.sleep(3)

    # 이벤트 발행하는 javascript 실행
    driver.execute_script(javascript)

    # 일단 쌓여있는 댓글들 크롤링
    comments = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_comment")
    for comment_element in comments:
        try:
            content = comment_element.find_element(
                By.CSS_SELECTOR, ".u_cbox_contents"
            ).text
            author = comment_element.find_element(
                By.CSS_SELECTOR, ".u_cbox_name").text
            time_posted = comment_element.find_element(
                By.CSS_SELECTOR, ".u_cbox_date"
            ).get_attribute("data-value")
            yield ChatMessage(
                source_id=page_id,
                source_type="naver",
                time=time_posted,
                message=content,
                author=author)
        except Exception as e:
            print(f"댓글 파싱 중 오류 발생: {str(e)}")

    # 최근에 업로드된 댓글들 크롤링
    while True:
        try:
            # JavaScript에서 저장한 새로운 댓글 데이터 가져오기
            new_comments = driver.execute_script(
                "return window.newComments || [];")

            print(f"new_comments length: {len(new_comments)}")

            if new_comments:
                # 새로운 댓글 처리 후 배열 비우기
                driver.execute_script("window.newComments = [];")
                for comment in new_comments:
                    print("새로운 댓글이 추가되었습니다!")
                    print(comment)
                    yield ChatMessage(
                        source_id=page_id,
                        source_type="naver",
                        time=comment["time"],
                        message=comment["content"],
                        author=comment["author"],
                    )
            time.sleep(1)  # CPU 사용량 감소를 위한 짧은 대기
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            continue


javascript = """
const targetNode = document.querySelector('.u_cbox_list');
const config = { childList: true, subtree: true };

const callback = function(mutationsList, observer) {
    for(let mutation of mutationsList) {
        if (mutation.type === 'childList') {
            mutation.addedNodes.forEach(node => {
                if (node.classList && node.classList.contains('u_cbox_comment')) {
                    // 새로운 댓글의 정보를 수집
                    const content = node.querySelector('.u_cbox_contents').textContent;
                    const author = node.querySelector('.u_cbox_name').textContent;
                    const time = node.querySelector('.u_cbox_date').getAttribute('data-value');

                    // Python으로 데이터를 전달하기 위해 window 객체에 저장
                    if (!window.newComments) window.newComments = [];
                    window.newComments.push({
                        content: content,
                        author: author,
                        time: time
                    });

                    // Python에서 감지할 수 있는 커스텀 이벤트 발생
                    document.dispatchEvent(new CustomEvent('newComment'));
                }
            });
        }
    }
};

const observer = new MutationObserver(callback);
observer.observe(targetNode, config);
"""

if __name__ == "__main__":
    for page_id in ("2024112414", "2024112510050850197"):
        p = multiprocessing.Process(
            target=produce_chat,
            args=(page_id, datetime.now() + timedelta(days=3),
                  KAFKA_BROKER, EPL_TOPIC_NAME),
        )
        p.start()
