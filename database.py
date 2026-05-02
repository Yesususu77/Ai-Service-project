import sqlite3

def init_db():
    conn = sqlite3.connect("vibe_writer.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            novel_id INTEGER,
            content TEXT,
            mood_label TEXT,
            mood_score REAL,
            bgm_url TEXT,
            sfx_trigger TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()