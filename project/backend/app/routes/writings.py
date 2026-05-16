from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.database import SessionLocal
import json

router = APIRouter()

class WritingCreate(BaseModel):
    id: str
    username: str
    story_title: str = ''
    chapters: list = []
    chapter_paragraphs: dict = {}
    selected_genre: str = ''

@router.post("/writings")
def save_writing(data: WritingCreate):
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO writings (id, username, story_title, chapters, chapter_paragraphs, selected_genre, saved_at)
            VALUES (:id, :username, :story_title, :chapters, :chapter_paragraphs, :selected_genre, CURRENT_TIMESTAMP)
            ON CONFLICT (id) DO UPDATE SET
                story_title = EXCLUDED.story_title,
                chapters = EXCLUDED.chapters,
                chapter_paragraphs = EXCLUDED.chapter_paragraphs,
                selected_genre = EXCLUDED.selected_genre,
                saved_at = CURRENT_TIMESTAMP
        """), {
            "id": data.id,
            "username": data.username,
            "story_title": data.story_title,
            "chapters": json.dumps(data.chapters, ensure_ascii=False),
            "chapter_paragraphs": json.dumps(data.chapter_paragraphs, ensure_ascii=False),
            "selected_genre": data.selected_genre
        })
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@router.get("/writings/{username}")
def get_writings(username: str):
    db = SessionLocal()
    try:
        results = db.execute(
            text("SELECT * FROM writings WHERE username = :username ORDER BY saved_at DESC"),
            {"username": username}
        ).fetchall()
        return [dict(r._mapping) for r in results]
    finally:
        db.close()
