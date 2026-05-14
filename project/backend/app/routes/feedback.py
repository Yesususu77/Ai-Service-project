from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text
from app.database import SessionLocal

router = APIRouter()

class FeedbackCreate(BaseModel):
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
            INSERT INTO feedback (rating, age, purpose, satisfactions, improvements, recommend)
            VALUES (:rating, :age, :purpose, :satisfactions, :improvements, :recommend)
        """), data.dict())
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()
