from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import sqlite3
import time

# api 키 받기 전까지 주석
# from analysis_service import analyze_passage
# from bgm_service import update_buffer, should_change_bgm
from state_manager import init_session, get_session, reset_session
# from recommend_service import recommend_bgm
# from premium_service import generate_chapter_theme
from database import create_tables, save_to_deck
from auth import create_token, decode_token

app = FastAPI()


# ---------------- 모델 ----------------
class User(BaseModel):
    username: str
    password: str

class AnalyzeRequest(BaseModel):
    session_id: str
    text: str

class StyleRequest(BaseModel):
    session_id: str
    style: str

class PremiumRequest(BaseModel):
    content: str
    tokens: int


# ---------------- DB 초기화 ----------------
@app.on_event("startup")
def startup():
    create_tables()


# ---------- 회원가입 ----------
@app.post("/api/signup")
def signup(user: User):
    conn = sqlite3.connect("editmuse.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (user.username, user.password)
        )
        conn.commit()
        return {"message": "signup success"}
    except:
        raise HTTPException(400, "이미 존재하는 아이디")
    finally:
        conn.close()


# ---------- 로그인 ----------
@app.post("/api/login")
def login(user: User):
    conn = sqlite3.connect("editmuse.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=? AND password=?",
        (user.username, user.password)
    )

    result = cursor.fetchone()
    conn.close()

    if not result:
        raise HTTPException(401, "로그인 실패")

    token = create_token(result[0])

    return {"access_token": token}


# ---------------- 유저 인증 ----------------
def get_user_id(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user_id = decode_token(token)

    if not user_id:
        raise HTTPException(401, "Invalid token")

    return user_id


# ---------------- 스타일 변경 ----------------
@app.post("/api/style-change")
def change_style(data: StyleRequest):
    reset_session(data.session_id, data.style)
    return {"status": "reset"}


# ---------- 분석 ----------
@app.post("/api/analyze")
def analyze(data: AnalyzeRequest, user_id: int = get_user_id):

    session = get_session(data.session_id)

    if not session:
        init_session(data.session_id)
        session = get_session(data.session_id)

    now = time.time()

    if now - session["last_time"] < session["cooldown"]:
        return {"skip": True}

    session["last_time"] = now

    # 임시(나중에 지우고 지피티 거 넣어) result = analyze_passage(data.text)
    result = {
        "mood": ["긴장"],
        "energy": 3,
        "sfx": [],
        "errors": []
    }

    if not result:
        return session["last_analysis"] or {"error": "analysis failed"}
    
    session["last_analysis"] = result
    mood = result["mood"][0]

        # 🔥 버퍼 처리
    buffer = update_buffer(session["buffer"], mood)

    change, dominant = should_change_bgm(buffer)

    # 🔥 BGM 추천
    bgm_url = None
    if change:
        bgm_url = recommend_bgm(dominant)

    # 🔥 저장
    save_to_deck(user_id, "FREE", "auto", mood, data.text[:50], bgm_url or "pending")

    return {
        "mood": result["mood"],
        "energy": result["energy"],
        "sfx": result["sfx"],
        "errors": result["errors"],
        "change_bgm": change,
        "bgm_mood": dominant if change else None,
        "bgm_url": bgm_url
    }


# ---------------- 내 음악 ----------------
@app.get("/api/my-music")
def my_music(user_id: int = get_user_id):
    conn = sqlite3.connect("editmuse.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM music_deck WHERE user_id=?",
        (user_id,)
    )

    data = cursor.fetchall()
    conn.close()

    return {"items": data}

  

# 유료 API 나중에 주석 해제
@app.post("/api/generate-chapter-theme")
def premium(data: PremiumRequest):
    # return generate_chapter_theme(data.content, data.tokens)
    # 키 받으면 지우기
    return {"message": "Premium service is currently disabled (API Key pending)"}