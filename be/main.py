from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작시 data 디렉토리 확인 및 생성
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # EPL 스케줄 데이터 확인
    try:
        with open('data/epl_schedule.json', 'r'):
            pass
    except FileNotFoundError:
        await update_schedule('epl')
        
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

def crawl_schedule(category='epl'):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        matches = []
        today = datetime.now()
        current_month = today.month
        current_year = today.year
        
        # 스포츠 종목에 따른 URL 구조 설정
        sport_type = "wfootball" if category == "epl" else "basketball"
        
        for i in range(6):
            target_month = (current_month + i) % 12 or 12
            target_year = current_year + (current_month + i - 1) // 12
            
            date = datetime(target_year, target_month, 1).strftime("%Y-%m-%d")
            url = f"https://m.sports.naver.com/{sport_type}/schedule/index?category={category}&date={date}"
            driver.get(url)
            time.sleep(2)
            
            elements = driver.find_elements(By.CSS_SELECTOR, ".ScheduleLeagueType_title__2Kalm")
            match_elements = driver.find_elements(By.CSS_SELECTOR, ".ScheduleLeagueType_match_list__1-n6x")
            
            for date_element, match_element in zip(elements, match_elements):
                match_date = date_element.text
                li_elements = match_element.find_elements(By.CSS_SELECTOR, "li")
                
                for li in li_elements:
                    try:
                        match_time = li.find_element(By.CSS_SELECTOR, ".MatchBox_time__nIEfd")
                        match_status = li.find_element(By.CSS_SELECTOR, ".MatchBox_status__2pbzi")
                        match_area = li.find_element(By.CSS_SELECTOR, ".MatchBox_match_area__39dEr")
                        match_areas = match_area.find_elements(By.CSS_SELECTOR, ".MatchBoxTeamArea_team__3aB4O")
                        link = match_area.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                        actual_time = match_time.get_attribute("textContent").strip().split("\n")[-1][-5:]
                        
                        # URL에서 날짜 추출 (YYYYMMDD)
                        match_date = link.split('/')[4][:8]
                        year = match_date[:4]
                        month = match_date[4:6]
                        day = match_date[6:8]
                        
                        # 표준 날짜/시간 형식으로 변환
                        match_info = {
                            "date": f"{year}-{month}-{day}",  # ISO 형식 (YYYY-MM-DD)
                            "time": actual_time,  # 24시간 형식 (HH:MM)
                            "status": match_status.text,
                            "home_team": match_areas[0].text,
                            "away_team": match_areas[1].text,
                            "league": category.upper(),
                            "cheer_url": f"{link}/cheer",
                            "timestamp": f"{year}-{month}-{day}T{actual_time}:00+09:00"  # ISO 8601
                        }
                        matches.append(match_info)
                        
                    except Exception as e:
                        print(f"매치 파싱 오류: {e}")
                        continue
                        
            time.sleep(1)
            
        return matches
        
    finally:
        driver.quit()

@app.get("/update_schedule/{category}")
async def update_schedule(category: str):
    try:
        matches = crawl_schedule(category)
        
        # JSON 파일로 저장
        filename = f"data/{category.lower()}_schedule.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({"matches": matches}, f, ensure_ascii=False, indent=2)
            
        return {"status": "success", "matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schedules/{category}")
async def get_schedules(category: str):
    try:
        filename = f"data/{category.lower()}_schedule.json"
        with open(filename, 'r', encoding='utf-8') as f:
            schedules = json.load(f)
        return schedules
    except FileNotFoundError:
        # 파일이 없으면 새로 크롤링
        return await update_schedule(category)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))