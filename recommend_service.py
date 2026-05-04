import sqlite3
import random

def recommend_bgm(mood: str):
    conn = sqlite3.connect("editmuse.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT music_url FROM music_deck
        WHERE mood = ?
    """, (mood,))

    results = cursor.fetchall()
    conn.close()

    if not results:
        return None

    return random.choice(results)[0]