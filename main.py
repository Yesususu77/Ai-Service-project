from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from database import init_db

app = FastAPI()

# 서버 시작 시 DB 초기화
@app.on_event("startup")
def startup_event():
    init_db()

# --- 데이터 모델 ---
class UserCreate(BaseModel):
    username: str
    password: str

class AnalysisRequest(BaseModel):
    user_id: int
    novel_id: int
    content: str

# --- DB 연결 유틸리티 ---
def get_db_connection():
    conn = sqlite3.connect("vibe_writer.db")
    conn.row_factory = sqlite3.Row
    return conn

# --- API 엔드포인트 ---

@app.get("/")
def root():
    return {"message": "EditMuse Backend with User System is running!"}

# 1. 회원가입
@app.post("/signup")
async def signup(user: UserCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user.username, user.password))
        conn.commit()
        conn.close()
        return {"message": "회원가입 성공"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")

# 2. 로그인 (성공 시 user_id 반환)
@app.post("/login")
async def login(user: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (user.username, user.password))
    user_record = cursor.fetchone()
    conn.close()
    
    if user_record:
        return {"message": "로그인 성공", "user_id": user_record["id"]}
    else:
        raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 틀렸습니다.")

# 3. 사용자별 문장 분석 결과 저장
# main.py의 save_analysis 함수를 이 코드로 교체하세요
@app.post("/analyze/save")
async def save_analysis(request: AnalysisRequest):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 데이터가 잘 들어오는지 확인용 로그 (터미널에 찍힙니다)
        print(f"저장 시도: user_id={request.user_id}, novel_id={request.novel_id}")
        
        cursor.execute("""
            INSERT INTO analysis_history (user_id, novel_id, content, mood_label, mood_score)
            VALUES (?, ?, ?, ?, ?)
        """, (request.user_id, request.novel_id, request.content, "분석 전", 0.0))
        
        conn.commit()
        new_id = cursor.lastrowid
        return {"status": "success", "history_id": new_id}
        
    except Exception as e:
        # 에러가 나면 터미널에 정확한 이유를 출력합니다
        print(f"저장 중 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=f"DB 저장 실패: {str(e)}")
    finally:
        if conn:
            conn.close()

# 4. 특정 사용자의 특정 소설 히스토리 조회
@app.get("/novel/{novel_id}/history")
async def get_novel_history(novel_id: int, user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM analysis_history 
        WHERE novel_id = ? AND user_id = ? 
        ORDER BY created_at DESC
    """, (novel_id, user_id))
    rows = cursor.fetchall()
    conn.close()
    return {"history": [dict(row) for row in rows]}

from fastapi import FastAPI
import sqlite3
from database import create_music_deck_table # 위에서 만든 함수 임포트

app = FastAPI()

# 서버 시작 시 테이블이 없으면 생성
@app.on_event("startup")
def on_startup():
    create_music_deck_table()

# [추가] 프론트엔드에서 뮤직덱 리스트를 가져가는 API
@app.get("/api/music-deck")
async def get_music_deck():
    conn = sqlite3.connect('editmuse.db')
    conn.row_factory = sqlite3.Row # 결과를 딕셔너리 형태로 변환
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM music_deck ORDER BY created_at DESC')
    rows = cursor.fetchall()
    
    deck_list = [dict(row) for row in rows]
    conn.close()
    
    return {"items": deck_list}