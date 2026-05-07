import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Selenium WebDriver 설정 (Chrome)
options = webdriver.ChromeOptions()
# options.add_argument('--headless') # 브라우저 창 없이 실행할 경우 활성화
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# 타겟 URL 설정 (BGM Factory 라이브러리)
base_url = "https://bgmfactory.com/ko/music/library?searchtype=track&type=all&order=recommend&customtag=363&page={}"

titles = []
tags_list = []

# 데이터 수집 루프 (1~10페이지)
for page in range(1, 11):
    driver.get(base_url.format(page))
    
    # 서버 부하 방지 및 페이지 로딩 대기
    time.sleep(random.uniform(5, 8))

    # 곡 정보가 포함된 컨테이너 요소 탐색
    tracks = driver.find_elements(By.CSS_SELECTOR, ".track-tpbox")
    print(f"Page {page}: {len(tracks)} tracks discovered.")

    for track in tracks:
        try:
            # 곡 제목 및 태그 텍스트 추출
            title = track.find_element(By.CSS_SELECTOR, ".track-self_title").text
            tags = track.find_elements(By.CSS_SELECTOR, ".track-tag_item")
            tag_text = [t.text for t in tags]

            titles.append(title)
            tags_list.append(", ".join(tag_text))

        except Exception as e:
            # 개별 항목 추출 실패 시 로그 출력 후 스킵
            print(f"Error parsing track: {e}")
            continue

    # 페이지 전환 전 추가 대기 시간 설정 (Anti-Bot 방지)
    time.sleep(random.uniform(6, 10))

driver.quit()

# 수집된 데이터를 DataFrame으로 변환 및 CSV 저장
df = pd.DataFrame({
    "Title": titles,
    "Tags": tags_list
})

# 인코딩 설정 (BOM 포함 UTF-8)
output_path = "C:/Users/abc/Desktop/bgm_tracks100.csv"
df.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Data collection completed. Saved to: {output_path}")
