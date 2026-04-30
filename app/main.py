import os
import requests
from fastapi import FastAPI, HTTPException
from app.database import engine, Base
from app.routes.user import router as user_router
from app.routes.analyze import router as analyze_router 

app = FastAPI()

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(user_router, prefix="/api/user")
app.include_router(analyze_router, prefix="/api/analyze")

# 환경변수 (기본값 포함)
AI_URL = os.getenv("AI_URL", "http://ai:8001/predict")

@app.get("/api")
def call_ai():
    try:
        # AI 서버 호출
        response = requests.get(AI_URL, timeout=5)
        response.raise_for_status()

        # JSON 반환
        return response.json()

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI server error: {str(e)}")