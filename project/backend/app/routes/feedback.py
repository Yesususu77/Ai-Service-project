from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.database import SessionLocal

router = APIRouter()

class FeedbackCreate(BaseModel):
    username: str = ''
    rating: int
    age: str = ''
    purpose: str = ''
    satisfactions: str = ''
    improvements: str = ''
    recommend: str = ''

@router.post("/feedback")
def save_feedback(data: FeedbackCreate):
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO feedback (username, rating, age, purpose, satisfactions, improvements, recommend)
            VALUES (:username, :rating, :age, :purpose, :satisfactions, :improvements, :recommend)
            ON CONFLICT (username) DO UPDATE SET
                rating = EXCLUDED.rating,
                age = EXCLUDED.age,
                purpose = EXCLUDED.purpose,
                satisfactions = EXCLUDED.satisfactions,
                improvements = EXCLUDED.improvements,
                recommend = EXCLUDED.recommend,
                created_at = CURRENT_TIMESTAMP
        """), data.dict())
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()

@router.get("/feedback/{username}")
def get_feedback(username: str):
    db = SessionLocal()
    try:
        result = db.execute(
            text("SELECT * FROM feedback WHERE username = :username"),
            {"username": username}
        ).fetchone()
        if result:
            return dict(result._mapping)
        return {}
    finally:
        db.close()
