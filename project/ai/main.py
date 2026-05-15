import os
import json
import asyncio # 추가
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
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

# 연결된 클라이언트를 관리할 집합 (중복 방지)
connected_clients = set()

async def log_to_clients(message: str):
    """연결된 모든 클라이언트에 브로드캐스트"""
    if not connected_clients:
        return
    # 리스트 복사본을 만들어 순회 (런타임 에러 방지)
    for client_ws in list(connected_clients):
        try:
            await client_ws.send_text(message)
        except Exception:
            connected_clients.remove(client_ws)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class AnalyzeRequest(BaseModel):
    text: str
    style: str = "oriental"

@app.post("/predict")
async def predict(req: AnalyzeRequest): # async로 변경 권장
    try:
        await log_to_clients(f"📥 요청 수신: {req.text[:20]}...")
        
        # OpenAI 호출 (동기 방식인 경우 유지, 비동기 권장)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": MASTER_SYSTEM_PROMPT},
                {"role": "user", "content": req.text[-500:]}
            ],
            temperature=0.2
        )
        raw = json.loads(response.choices[0].message.content)
        
        valid_moods = [m for m in raw.get("mood", []) if m in config.VALID_MOODS]
        await log_to_clients(f"✅ 분석 완료: {valid_moods}")
        
        return {
            "mood": valid_moods or config.DEFAULT_MOOD,
            "energy": max(1, min(5, raw.get("energy", 3))),
            "sfx": raw.get("sfx", [])[:config.MAX_SFX_COUNT],
            "errors": raw.get("errors", [])
        }
    except Exception as e:
        await log_to_clients(f"❌ 에러 발생: {str(e)}")
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}

# --- 실시간 로그 관련 ---

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지를 기다리며 연결 유지
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception:
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/logs") # response_class 생략 가능 (HTMLResponse 반환 시 자동 처리)
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
                // 현재 프로토콜에 따라 ws 또는 wss 결정 (Render 배포 환경 대응)
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const ws = new WebSocket(`${protocol}//${window.location.host}/ws/logs`);
                
                ws.onmessage = (e) => {
                    const logDiv = document.getElementById('log');
                    const line = document.createElement('div');
                    line.className = 'line';
                    line.innerHTML = `<span class="time">[${new Date().toLocaleTimeString()}]</span> \${e.data}`;
                    logDiv.appendChild(line);
                    logDiv.scrollTop = logDiv.scrollHeight;
                };
                
                ws.onclose = () => {
                    console.log("WebSocket 연결 종료. 재시도 중...");
                    setTimeout(() => location.reload(), 3000);
                };
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
