import os
import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.database import engine, Base
from app.routes.user import router as user_router
from app.routes.analyze import router as analyze_router 
from app.routes.music import router as music_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.feedback import router as feedback_router

app = FastAPI()

# 실시간 로그 클라이언트 관리
connected_clients = set()

async def log_to_clients(message: str):
    for client_ws in list(connected_clients):
        try:
            await client_ws.send_text(message)
        except Exception:
            connected_clients.remove(client_ws)

@app.get("/")
def root():
    return {"message": "server running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(user_router, prefix="/api/user")
app.include_router(analyze_router, prefix="/api/analyze")
app.include_router(music_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")

AI_URL = os.getenv("AI_URL", "http://ai:8001/predict")

@app.get("/api")
async def call_ai():
    async with httpx.AsyncClient() as client:
        try:
            await log_to_clients("📡 AI 서버 호출 중...")
            response = await client.get(AI_URL, timeout=10.0)
            response.raise_for_status()
            await log_to_clients("✅ AI 응답 수신 완료")
            return response.json()
        except httpx.ConnectError:
            await log_to_clients("❌ AI 서버 연결 실패")
            raise HTTPException(status_code=503, detail="AI 서버에 연결할 수 없습니다.")
        except httpx.TimeoutException:
            await log_to_clients("⏱️ AI 서버 타임아웃")
            raise HTTPException(status_code=504, detail="AI 분석 시간이 초과되었습니다.")
        except httpx.HTTPStatusError as e:
            await log_to_clients(f"⚠️ AI 서버 오류: {e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=f"AI 서버 응답 오류: {e.response.text}")
        except Exception as e:
            await log_to_clients(f"❌ 예외 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=f"예상치 못한 오류 발생: {str(e)}")

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)

@app.get("/logs")
async def get_log_page():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Real-time Logs</title>
            <style>
                body { background: #121212; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
                #log { border: 1px solid #333; height: 80vh; overflow-y: auto; padding: 15px; background: #000; border-radius: 5px; }
                .line { margin-bottom: 5px; border-bottom: 1px solid #1a1a1a; padding-bottom: 2px; }
                .time { color: #888; margin-right: 10px; }
            </style>
        </head>
        <body>
            <h3>🚀 AI Model Activity Monitor</h3>
            <div id="log"></div>
            <script>
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);
                ws.onmessage = (e) => {
                    const logDiv = document.getElementById('log');
                    const line = document.createElement('div');
                    line.className = 'line';
                    line.innerHTML = `<span class="time">[${new Date().toLocaleTimeString()}]</span> ${e.data}`;
                    logDiv.appendChild(line);
                    logDiv.scrollTop = logDiv.scrollHeight;
                };
                ws.onclose = () => setTimeout(() => location.reload(), 3000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
