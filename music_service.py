import sqlite3

def add_to_music_deck(chapter_id, input_text, ai_response):
    """
    AI가 분석한 결과를 뮤직덱 데이터베이스에 저장합니다.
    """
    conn = sqlite3.connect('editmuse.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO music_deck (type, title, mood, input_log, music_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            "PREMIUM",                         # 유료 생성 기능이므로 PREMIUM으로 저장
            ai_response.get("theme_name", "Untitled Theme"),
            ai_response.get("summary_mood"),
            input_text[:50] + "...",           # 분석의 원인이 된 텍스트 요약
            ai_response.get("music_url", "pending") # 실제 음악 파일 경로
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB 저장 오류: {e}")
        return False
    finally:
        conn.close()