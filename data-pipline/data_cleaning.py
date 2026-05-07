import pandas as pd
import re
import sqlite3

# 데이터 로드 (수집된 원본 BGM 데이터)
df = pd.read_csv("C:/Users/abc/Desktop/bgm_tracks100.csv")

def extract_bpm(tags):
    """태그 문자열 내에서 BPM 수치를 추출"""
    match = re.search(r'(\d+)\s*BPM', str(tags))
    return int(match.group(1)) if match else None

def classify_emotion(tags, bpm):
    """태그 키워드 및 BPM 기반 감정 라벨링 로직"""
    tags = str(tags)

    # 1차 키워드 매핑
    if "#밝은" in tags or "#신나는" in tags:
        return "기쁨"
    elif "#잔잔한" in tags:
        return "슬픔"
    elif "#긴장" in tags or "#미스터리" in tags:
        return "공포"
    elif "#오케스트라" in tags:
        return "웅장"
    elif "#몽환" in tags:
        return "몽환"

    # 2차 BPM 기반 보정
    if bpm:
        if bpm >= 140:
            return "분노"
        elif bpm >= 120:
            return "긴박"
        elif bpm <= 90:
            return "슬픔"

    return "기타"

def clean_filename(title):
    """시스템 호출 시 인코딩 에러 방지를 위한 파일명 정규화"""
    title = str(title).lower()
    title = re.sub(r'[^a-z0-9가-힣 ]', '', title)
    title = title.replace(" ", "_")
    return title

def extract_license(tags):
    """저작권 및 라이선스 정보 추출"""
    tags = str(tags)
    if "#CC-BY" in tags: return "CC-BY"
    if "#기증저작물" in tags: return "기증저작물"
    if "#BGM팩토리" in tags: return "BGM팩토리"
    if "#공유마당" in tags: return "공유마당"
    return "기타"

def classify_genre_multi(tags):
    """다중 장르 태그 분석 (Oriental, Orchestral, Piano 등)"""
    tags = str(tags)
    genres = []

    if "#전통악기" in tags or "#민속악기" in tags: genres.append("Oriental")
    if "#오케스트라" in tags or "#현악기" in tags: genres.append("Orchestral")
    if "#피아노" in tags: genres.append("Piano")
    if "#어두운" in tags or "#슬픈" in tags: genres.append("Dark")
    if "#몽환적인" in tags: genres.append("Lofi")

    return ", ".join(genres) if genres else "Other"

# 데이터 전처리 파이프라인 가동
df["bpm"] = df["Tags"].apply(extract_bpm)
df["emotion"] = df.apply(lambda x: classify_emotion(x["Tags"], x["bpm"]), axis=1)
df["safe_filename"] = df["Title"].apply(clean_filename)
df["license"] = df["Tags"].apply(extract_license)
df["genre"] = df["Tags"].apply(classify_genre_multi)

# 최종 데이터 스키마 구성
df_final = df[["Title", "bpm", "emotion", "genre", "license", "Tags", "safe_filename"]]

# 결과 저장 (CSV 및 SQLite Export)
df_final.to_csv("C:/Users/abc/Desktop/final_music_dataset.csv", index=False, encoding="utf-8-sig")

with sqlite3.connect("C:/Users/abc/Desktop/music.db") as conn:
    df_final.to_sql("music", conn, if_exists="replace", index=False)

print("Data Preprocessing Completed: CSV and DB generated.")
