from sqlalchemy import Column, Integer, String, Text
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    nickname = Column(String)

class MusicDeck(Base):
    __tablename__ = "music_deck"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, index=True)
    type       = Column(String)   # "FREE" | "PREMIUM"
    title      = Column(String)
    mood       = Column(String)
    input_log  = Column(String)
    music_url  = Column(String)
    created_at = Column(String, default="CURRENT_TIMESTAMP")

# ─── 이 부분이 빠져있어서 에러가 난 겁니다! ───
class BgmTrack(Base):
    __tablename__ = "bgm_tracks"

    id = Column(Integer, primary_key=True, index=True)
    Title = Column(String)
    bpm = Column(Integer)
    emotion = Column(String)
    genre = Column(String)
    Tags = Column(Text)   # 아까 캡처에서 본 Tags 컬럼
    url = Column(String)    # 아까 캡처에서 본 url 컬럼
    safe_filename = Column(String)
    license = Column(String)
