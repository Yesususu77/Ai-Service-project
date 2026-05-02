from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from database import init_db

app = FastAPI()

# 서버 시작 시 DB 초기화
@app.on_event("startup")
def startup_event():
    init_db()

class AnalysisRequest(BaseModel):
    novel_id: int
    content: str

# DB 연결 유틸리티
def get_db_connection():
    conn = sqlite3.connect("vibe_writer.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def root():
    return {"message": "EditMuse Backend is running!"}

# 데이터 저장 API
@app.post("/analyze/save")
async def save_analysis(request: AnalysisRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 임시 데이터로 저장 테스트
        cursor.execute("""
            INSERT INTO analysis_history (novel_id, content, mood_label, mood_score)
            VALUES (?, ?, ?, ?)
        """, (request.novel_id, request.content, "감성적", 0.85))
        
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        
        return {"status": "success", "id": new_id, "message": "분석 결과가 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 히스토리 조회 API
@app.get("/novel/{novel_id}/history")
async def get_novel_history(novel_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_history WHERE novel_id = ? ORDER BY created_at DESC", (novel_id,))
        rows = cursor.fetchall()
        conn.close()
        return {"novel_id": novel_id, "history": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))