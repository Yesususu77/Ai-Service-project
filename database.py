import sqlite3

def init_db():
    conn = sqlite3.connect("vibe_writer.db")
    cursor = conn.cursor()
    
    # 1. 사용자 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. 분석 기록 테이블 생성 (user_id 추가)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            novel_id INTEGER,
            content TEXT,
            mood_label TEXT,
            mood_score REAL,
            bgm_url TEXT,
            sfx_trigger TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()

import sqlite3

# [추가] 뮤직덱 테이블 생성 함수
def create_music_deck_table():
    conn = sqlite3.connect('editmuse.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS music_deck (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,                  # 'FREE' 또는 'PREMIUM'
            title TEXT,                 # 음악 제목
            mood TEXT,                  # 분위기
            input_log TEXT,             # 원인이 된 문장
            music_url TEXT,             # 음악 파일 경로
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# [추가] 뮤직덱 데이터 저장 함수
def save_to_deck(m_type, title, mood, text, url="pending"):
    conn = sqlite3.connect('editmuse.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO music_deck (type, title, mood, input_log, music_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (m_type, title, mood, text, url))
    conn.commit()
    conn.close()
