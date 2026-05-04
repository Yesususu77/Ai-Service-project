import sqlite3

DB_NAME = "editmuse.db"

def create_tables():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 유저
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # 음악 저장 (user_id 추가 핵심)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS music_deck (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        title TEXT,
        mood TEXT,
        input_log TEXT,
        music_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_to_deck(user_id, m_type, title, mood, text, url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO music_deck (user_id, type, title, mood, input_log, music_url)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, m_type, title, mood, text, url))

    conn.commit()
    conn.close()