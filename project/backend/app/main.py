import os
import httpx  # requests 대신 httpx 사용 (비동기 통신용)
from fastapi import FastAPI, HTTPException
from app.database import engine, Base
from app.routes.user import router as user_router
from app.routes.analyze import router as analyze_router 
from app.routes.music import router as music_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 설정 (프론트엔드 연동 필수)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 시작 시 DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 등록
app.include_router(user_router, prefix="/api/user")
app.include_router(analyze_router, prefix="/api/analyze")
app.include_router(music_router, prefix="/api")

# 환경변수 (AI 분석 서버 주소)
AI_URL = os.getenv("AI_URL", "http://ai:8001/predict")

@app.get("/api")
async def call_ai():
    """
    AI 분석 서버와 비동기로 통신하여 결과를 반환합니다.
    requests 대신 httpx를 사용하여 분석 중에도 서버가 멈추지 않도록(Non-blocking) 설계했습니다.
    """
    async with httpx.AsyncClient() as client:
        try:
            # AI 서버 호출 (비동기 대기)
            response = await client.get(AI_URL, timeout=10.0)
            
            # 응답 상태 코드가 200이 아니면 예외 발생
            response.raise_for_status()

            # 성공 시 JSON 결과 반환
            return response.json()

        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="AI 서버에 연결할 수 없습니다. 서버 상태를 확인하세요.")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="AI 분석 시간이 초과되었습니다.")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"AI 서버 응답 오류: {e.response.text}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"예상치 못한 오류 발생: {str(e)}")
