import os
import time
import httpx
import asyncio
from collections import defaultdict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from app.database import engine, Base
from app.routes.user import router as user_router
from app.routes.analyze import router as analyze_router
from app.routes.music import router as music_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.feedback import router as feedback_router

app = FastAPI()

# ── 실시간 로그 ──
connected_clients = set()

async def log_to_clients(message: str):
    for ws in list(connected_clients):
        try:
            await ws.send_text(message)
        except Exception:
            connected_clients.discard(ws)

# ── CCU / Rate Limit ──
active_users = set()
request_counts = defaultdict(list)
RATE_LIMIT = 200
RATE_WINDOW = 60

SKIP_PATHS = {"/logs", "/ws/logs", "/stats", "/", "/health"}  # ✅ NEW: 로그/헬스체크 경로 미들웨어 스킵

@app.middleware("http")
async def tracking_middleware(request: Request, call_next):
    path = request.url.path

    # ✅ NEW: 내부 경로는 추적 제외
    if path in SKIP_PATHS:
        return await call_next(request)

    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", "direct")
    session_id = request.cookies.get("session_id", "no-session")  # ✅ NEW: 세션 ID

    # Rate Limit
    now = time.time()
    request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < RATE_WINDOW]
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        await log_to_clients(f"🚫 Rate limit 초과: {client_ip}")
        return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
    request_counts[client_ip].append(now)

    active_users.add(client_ip)
    await log_to_clients(
        f"👥 CCU: {len(active_users)} | session: {session_id} | {path} | "
        f"Referrer: {referrer} | UA: {user_agent[:80]}"
    )

    response = await call_next(request)
    active_users.discard(client_ip)
    return response

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
            raise HTTPException(status_code=500, detail=f"예상치 못한 오류: {str(e)}")

@app.get("/stats")
async def stats():
    return {
        "ccu": len(active_users),
        "rate_limit_status": {ip: len(times) for ip, times in request_counts.items()}
    }

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=25.0)
            except asyncio.TimeoutError:
                await websocket.send_text("🟢 ping")  # 연결 유지용
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=25.0)
            except asyncio.TimeoutError:
                await websocket.send_text("🟢 ping")  # 연결 유지용
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)

@app.get("/logs")
async def get_log_page():
    # ✅ NEW: session_id 쿠키 발급 + 활성 시간 측정 + error_type 색상 구분
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Real-time Logs</title>
            <style>
                body { background: #121212; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; }
                #log { border: 1px solid #333; height: 75vh; overflow-y: auto; padding: 15px; background: #000; border-radius: 5px; }
                .line { margin-bottom: 5px; border-bottom: 1px solid #1a1a1a; padding-bottom: 2px; }
                .time { color: #888; margin-right: 10px; }
                .error { color: #ff4444; }
                .warn  { color: #ffaa00; }
                .info  { color: #00ff00; }
                #status { margin-bottom: 10px; color: #888; font-size: 13px; }
            </style>
        </head>
        <body>
            <h3>🚀 AI Model Activity Monitor</h3>
            <div id="status">⏳ 연결 중...</div>
            <div id="log"></div>
            <script>
                // ✅ NEW: session_id 쿠키 발급
                function getOrCreateSession() {
                    let sid = document.cookie.split('; ').find(r => r.startsWith('session_id='));
                    if (!sid) {
                        const id = 'sess_' + Math.random().toString(36).substr(2, 9);
                        document.cookie = `session_id=${id}; path=/; max-age=86400`;
                        return id;
                    }
                    return sid.split('=')[1];
                }
                const sessionId = getOrCreateSession();

                // ✅ NEW: 활성 시간 측정 (마우스/스크롤 이벤트 기반)
                let activeTime = 0;
                let lastActive = Date.now();
                let isActive = false;
                function markActive() {
                    lastActive = Date.now();
                    if (!isActive) {
                        isActive = true;
                    }
                }
                setInterval(() => {
                    if (isActive && Date.now() - lastActive < 5000) {
                        activeTime++;
                    } else {
                        isActive = false;
                    }
                }, 1000);
                document.addEventListener('mousemove', markActive);
                document.addEventListener('scroll', markActive);
                document.addEventListener('keydown', markActive);

                // WebSocket 연결
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                let ws;
                function connect() {
                    ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);

                    ws.onopen = () => {
                        document.getElementById('status').textContent = `✅ 연결됨 | session: ${sessionId}`;
                        // ✅ 연결 유지용 ping
                        setInterval(() => { if (ws.readyState === 1) ws.send('ping'); }, 20000);
                    };

                    ws.onmessage = (e) => {
                        const logDiv = document.getElementById('log');
                        const line = document.createElement('div');
                        line.className = 'line';
                        // ✅ NEW: error_type 색상 구분
                        let cls = 'info';
                        if (e.data.includes('❌') || e.data.includes('🚫') || e.data.includes('model_timeout') || e.data.includes('safety_filter')) cls = 'error';
                        else if (e.data.includes('⚠️') || e.data.includes('user_cancel')) cls = 'warn';
                        line.innerHTML = `<span class="time">[${new Date().toLocaleTimeString()}]</span><span class="${cls}"> ${e.data}</span>`;
                        logDiv.appendChild(line);
                        logDiv.scrollTop = logDiv.scrollHeight;
                    };

                    ws.onclose = () => {
                        document.getElementById('status').textContent = '🔴 연결 끊김. 재연결 중...';
                        setTimeout(connect, 3000);
                    };

                    ws.onerror = () => ws.close();
                }
                connect();

                // ✅ NEW: 활성 시간 주기적 표시
                setInterval(() => {
                    document.getElementById('status').textContent =
                        `✅ 연결됨 | session: ${sessionId} | 활성시간: ${activeTime}s`;
                }, 1000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
