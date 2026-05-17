import os
import time
import httpx
import asyncio
import json
from collections import defaultdict
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
from app.database import engine, Base
from app.routes.user import router as user_router
from app.routes.analyze import router as analyze_router
from app.routes.music import router as music_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.feedback import router as feedback_router
from app.routes.writings import router as writings_router

app = FastAPI()

# ── 실시간 로그 ──
connected_clients = set()
log_queue = []  # SSE용 로그 버퍼

async def log_to_clients(message: str):
    log_queue.append(message)
    if len(log_queue) > 500:  # 최대 500줄 유지
        log_queue.pop(0)
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

SKIP_PATHS = {"/logs", "/ws/logs", "/stats", "/", "/health", "/api/log", "/admin/dashboard", "/admin/stream"}

@app.middleware("http")
async def tracking_middleware(request: Request, call_next):
    path = request.url.path
    if path in SKIP_PATHS:
        return await call_next(request)

    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    referrer = request.headers.get("referer", "direct")
    session_id = request.cookies.get("session_id", "no-session")

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
    allow_origins=["https://frontend-service-dogk.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(user_router, prefix="/api/user")
app.include_router(analyze_router, prefix="/api/analyze")
app.include_router(music_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")
app.include_router(writings_router, prefix="/api")

AI_URL = os.getenv("AI_URL", "http://ai:8001/predict")

@app.get("/api")
async def call_ai():
    start_time = time.time()
    async with httpx.AsyncClient() as client:
        try:
            await log_to_clients("📡 AI 서버 호출 시작")
            response = await client.get(AI_URL, timeout=10.0)
            duration = round(time.time() - start_time, 2)
            response.raise_for_status()
            await log_to_clients(f"✅ AI 응답 완료 ({duration}s)")
            return response.json()
        except httpx.HTTPStatusError as e:
            await log_to_clients(f"⚠️ AI 서버 오류: {e.response.status_code} | 데이터 형식 확인 필요")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            await log_to_clients(f"❌ 오류 발생: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def stats():
    return {
        "ccu": len(active_users),
        "rate_limit_status": {ip: len(times) for ip, times in request_counts.items()}
    }

@app.post("/api/log")
async def receive_log(request: Request):
    body = await request.json()
    msg = body.get("msg", "")
    await log_to_clients(msg)
    return {"ok": True}

# ── SSE 스트림 (무료 플랜 대응) ──
@app.get("/admin/stream")
async def admin_stream(request: Request):
    async def event_generator():
        last_index = len(log_queue)
        while True:
            if await request.is_disconnected():
                break
            current_index = len(log_queue)
            if current_index > last_index:
                for msg in log_queue[last_index:current_index]:
                    yield {"data": msg}
                last_index = current_index
            await asyncio.sleep(0.5)
    return EventSourceResponse(event_generator())

# ── WebSocket (유료 플랜용 유지) ──
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data != "ping":
                await log_to_clients(f"{data}")
            else:
                await websocket.send_text("🟢 pong")
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        connected_clients.discard(websocket)

@app.get("/logs")
async def get_log_page():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Real-time Logs</title>
            <style>
                body { background: #121212; color: #00ff00; font-family: 'Courier New', monospace; padding: 20px; padding-bottom: 80px; }
                #log { border: 1px solid #333; height: 70vh; overflow-y: auto; padding: 15px; background: #000; border-radius: 5px; }
                .line { margin-bottom: 5px; border-bottom: 1px solid #1a1a1a; padding-bottom: 2px; }
                .time { color: #888; margin-right: 10px; }
                .error { color: #ff4444; }
                .warn  { color: #ffaa00; }
                .info  { color: #00ff00; }
                #status { margin-bottom: 10px; color: #888; font-size: 13px; }
                .footer { position: fixed; bottom: 0; left: 0; width: 100%; background: #0a0a0a; border-top: 1px solid #222; padding: 12px 20px; box-sizing: border-box; color: #555; font-family: Arial, sans-serif; font-size: 11px; display: flex; justify-content: space-between; align-items: center; }
                .footer-links a { color: #666; text-decoration: none; margin-left: 12px; }
                .footer-links a:hover { color: #888; }
            </style>
        </head>
        <body>
            <h3>🚀 AI Model Activity Monitor</h3>
            <div id="status">⏳ 연결 중...</div>
            <div id="log"></div>
            <div class="footer">
                <div>Data provided by IFI CLAIMS Patent Services</div>
                <div class="footer-links">
                    <a href="#">About</a>
                    <a href="#">Send Feedback</a>
                    <a href="#">Public Datasets</a>
                    <a href="#">Terms</a>
                    <a href="#">Privacy Policy</a>
                    <a href="#">Help</a>
                </div>
            </div>
            <script>
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

                let activeTime = 0;
                let lastActive = Date.now();
                let isActive = false;
                function markActive() { lastActive = Date.now(); isActive = true; }
                setInterval(() => {
                    if (isActive && Date.now() - lastActive < 5000) { activeTime++; }
                    else { isActive = false; }
                }, 1000);
                document.addEventListener('mousemove', markActive);
                document.addEventListener('scroll', markActive);
                document.addEventListener('keydown', markActive);

                function appendLog(text) {
                    const logDiv = document.getElementById('log');
                    const line = document.createElement('div');
                    line.className = 'line';
                    let cls = 'info';
                    if (text.includes('❌') || text.includes('🚫') || text.includes('model_timeout') || text.includes('safety_filter')) cls = 'error';
                    else if (text.includes('⚠️') || text.includes('user_cancel')) cls = 'warn';
                    line.innerHTML = `<span class="time">[${new Date().toLocaleTimeString()}]</span><span class="${cls}"> ${text}</span>`;
                    logDiv.appendChild(line);
                    logDiv.scrollTop = logDiv.scrollHeight;
                }

                // SSE 연결 (무료 플랜 대응)
                const es = new EventSource('/admin/stream');
                es.onopen = () => {
                    document.getElementById('status').textContent = `✅ 연결됨 (SSE) | session: ${sessionId}`;
                };
                es.onmessage = (e) => appendLog(e.data);
                es.onerror = () => {
                    document.getElementById('status').textContent = '🔴 SSE 연결 끊김. 재연결 중...';
                };

                setInterval(() => {
                    document.getElementById('status').textContent =
                        `✅ 연결됨 | session: ${sessionId} | 활성시간: ${activeTime}s`;
                }, 1000);
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Live User Logs</title>
        <style>
            body { background-color: #121212; color: #e0e0e0; font-family: 'Courier New', Courier, monospace; padding: 20px; }
            h2 { color: #00ff66; border-bottom: 1px solid #333; padding-bottom: 10px; }
            #log-box { background-color: #1e1e1e; border: 1px solid #333; border-radius: 5px; height: 500px; overflow-y: auto; padding: 15px; font-size: 14px; line-height: 1.6; }
            .log-line { margin-bottom: 8px; border-bottom: 1px dashed #2a2a2a; padding-bottom: 4px; color: #00ff66; }
        </style>
    </head>
    <body>
        <h2>📊 실시간 유저 활동 모니터링</h2>
        <div id="log-box"></div>
        <script>
            const logBox = document.getElementById('log-box');
            const eventSource = new EventSource('/admin/stream');
            eventSource.onmessage = function(event) {
                const line = document.createElement('div');
                line.className = 'log-line';
                line.innerText = event.data;
                logBox.appendChild(line);
                logBox.scrollTop = logBox.scrollHeight;
            };
            eventSource.onerror = function() {
                console.log("연결이 끊겼거나 서버가 꺼졌습니다.");
            };
        </script>
    </body>
    </html>
    """
