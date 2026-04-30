from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, auth
from app.database import get_db

router = APIRouter()


# 회원가입
@router.post("/signup", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = auth.hash_password(user.password)

    new_user = models.User(
        username=user.username,
        password=hashed_pw,
        nickname=user.nickname
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# 로그인
@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()

    if not db_user or not auth.verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "login success",
        "user_id": db_user.id
    }
