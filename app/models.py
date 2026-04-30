from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)  # 고유 식별번호
    username = Column(String, unique=True, index=True)  # 로그인 ID
    password = Column(String)  # 비밀번호 (해시 저장)
    nickname = Column(String)  # 이름(닉네임)