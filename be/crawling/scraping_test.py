import time
from datetime import datetime, date

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

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


def get_web_driver() -> WebDriver:
    options = Options()
    options.add_argument("--window-size=1300,1000")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()), options=options
    )


def crawl_schedule(driver: WebDriver, target_date: date, category="epl"):
    date_str: str = target_date.strftime("%Y-%m-%d")
    url = f"https://m.sports.naver.com/wfootball/schedule/index?category={category}&date={date_str}"
    # get page
    try:
        driver.get(url)
        time.sleep(2)
    except Exception as e:
        print("driver.get(url) error")
        raise e

    # parse page
    elements = driver.find_elements(By.CSS_SELECTOR, ".ScheduleLeagueType_title__2Kalm")
    match_elements = driver.find_elements(
        By.CSS_SELECTOR, ".ScheduleLeagueType_match_list__1-n6x"
    )

    for date_element, match_element in zip(elements, match_elements):
        print(f"\n[{date_element.text}] 경기일정:")  # 날짜 출력
        # li 요소들 찾기
        li_elements = match_element.find_elements(By.CSS_SELECTOR, "li")
        for idx, li in enumerate(li_elements):
            match_time = li.find_element(By.CSS_SELECTOR, ".MatchBox_time__nIEfd")
            match_status = li.find_element(By.CSS_SELECTOR, ".MatchBox_status__2pbzi")
            match_area = li.find_element(By.CSS_SELECTOR, ".MatchBox_match_area__39dEr")
            match_areas = match_area.find_elements(
                By.CSS_SELECTOR, ".MatchBoxTeamArea_team__3aB4O"
            )
            link = match_area.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
            actual_time = (
                match_time.get_attribute("textContent").strip().split("\n")[-1][-5:]
            )

            print(f"경기날짜: {date_element.text}")
            print(f"경기 시간: {actual_time}")
            print(f"경기 상태: {match_status.text}")
            print(f"매치 정보: 홈 {match_areas[0].text} vs 원정 {match_areas[1].text}")
            print(f"응원 링크: {link}/cheer")
            print("-" * 50)


def get_new_comments():
    def parse_comment(comment_element):
        """댓글 요소를 파싱하는 함수"""
        content = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_contents").text
        author = comment_element.find_element(By.CSS_SELECTOR, ".u_cbox_name").text
        time_posted = comment_element.find_element(
            By.CSS_SELECTOR, ".u_cbox_date"
        ).get_attribute("data-value")
        return {"author": author, "content": content, "time": time_posted}

    # cbox_module
    # cbox_module
    # cbox_module_wai_u_cbox_content_wrap_tabpanel > ul

    driver = get_web_driver()
    # url = "https://m.sports.naver.com/game/202411230450124/cheer"
    url = "https://m.sports.naver.com/game/2024112463551271675/cheer"
    driver.get(url)
    time.sleep(5)
    driver.execute_script(javascript)
    comments = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_comment")
    for comment in comments:
        try:
            comment_data = parse_comment(comment)
            print(f"작성자: {comment_data['author']}")
            print(f"내용: {comment_data['content']}")
            print(f"시간: {comment_data['time']}")
            print("-" * 50)
        except Exception as e:
            print(f"댓글 파싱 중 오류 발생: {str(e)}")
    print("fuck")
    while True:
        try:
            # JavaScript에서 저장한 새로운 댓글 데이터 가져오기
            new_comments = driver.execute_script("return window.newComments || [];")
            print(f"new_comments length: {len(new_comments)}")
            if new_comments:
                # 새로운 댓글 처리 후 배열 비우기
                driver.execute_script("window.newComments = [];")
                for comment in new_comments:
                    print("\n새로운 댓글이 추가되었습니다!")
                    print(f"작성자: {comment['author']}")
                    print(f"내용: {comment['content']}")
                    print(f"시간: {comment['time']}")
                    print("-" * 50)
            time.sleep(1)  # CPU 사용량 감소를 위한 짧은 대기
        except KeyboardInterrupt:
            print("\n모니터링을 종료합니다.")
            break
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            continue


# crawl_schedule(get_web_driver(), category='epl', target_date=datetime.now().date())
get_new_comments()
