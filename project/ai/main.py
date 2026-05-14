import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket, WebSocketDisconnect # 추가
from fastapi.responses import HTMLResponse # 추가
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from app.core.prompts import MASTER_SYSTEM_PROMPT
from app.core import config

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 추가 시작
connected_clients = []

async def log_to_clients(message: str):
    """연결된 모든 모니터링 페이지로 로그 전송"""
    for client_ws in connected_clients:
        try:
            await client_ws.send_text(message)
        except:
            continue
# 여기까지 추가

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AnalyzeRequest(BaseModel):
    text: str
    style: str = "oriental"


@app.post("/predict")
def predict(req: AnalyzeRequest):
    try:
        # await log_to_clients(f"요청 수신: {req.text[:30]}...") # 삭제
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                {"role": "user",   "content": req.text[-500:]}
            ],
            temperature=0.2
        )
        raw = json.loads(response.choices[0].message.content)

        valid_moods = [m for m in raw.get("mood", []) if m in config.VALID_MOODS]
        energy = max(1, min(5, raw.get("energy", 3)))
        sfx = raw.get("sfx", [])[:config.MAX_SFX_COUNT]
        await log_to_clients(f" 분석 완료: {valid_moods}") # 추가
        return {
            "mood":   valid_moods or config.DEFAULT_MOOD,
            "energy": energy,
            "sfx":    sfx,
            "errors": raw.get("errors", [])
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok"}

# 이하 전체 추가
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text() # 연결 유지
    except WebSocketDisconnect:
        connected_clients.remove(websocket)

@app.get("/logs", response_class=HTMLResponse)
async def get_log_page():
    return """
    <html>
        <body style="background: #121212; color: #00ff00; font-family: monospace; padding: 20px;">
            <h3>🚀 Real-time User Activity Logs</h3>
            <div id="log" style="border: 1px solid #333; height: 500px; overflow-y: scroll; padding: 10px; background: #000;"></div>
            <script>
                const ws = new WebSocket(`ws://${window.location.host}/ws/logs`);
                ws.onmessage = (e) => {
                    const logDiv = document.getElementById('log');
                    const line = document.createElement('div');
                    line.textContent = `[${new Date().toLocaleTimeString()}] ${e.data}`;
                    logDiv.appendChild(line);
                    logDiv.scrollTop = logDiv.scrollHeight;
                };
            </script>
        </body>
    </html>
    """
