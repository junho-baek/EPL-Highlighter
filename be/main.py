from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

app = FastAPI()


# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용 (배포 시 특정 도메인으로 제한)
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 HTTP 헤더 허용
)

class Match(BaseModel):
    match_name: str

# Selenium으로 YouTube 검색 수행
def search_youtube(match_name):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service("/path/to/chromedriver"), options=options)

    try:
        # 유튜브 검색 URL
        search_url = f"https://www.youtube.com/results?search_query={match_name}"
        driver.get(search_url)
        time.sleep(3)  # 페이지 로드 대기

        # 검색 결과 수집
        search_results = []
        videos = driver.find_elements(By.XPATH, "//a[@id='video-title']")
        for video in videos[:5]:  # 상위 5개 결과만 반환
            title = video.get_attribute("title")
            link = video.get_attribute("href")
            if title and link:
                search_results.append({"title": title, "link": link})

        return search_results
    finally:
        driver.quit()

@app.post("/search_youtube")
async def search_youtube_endpoint(match: Match):
    try:
        results = search_youtube(match.match_name)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))