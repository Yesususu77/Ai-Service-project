import asyncio
from datetime import datetime

class LogManager:
    def __init__(self):
        # 실시간으로 로그를 전달할 비동기 큐
        self.queue = asyncio.Queue()

    async def log(self, user_id: str, message: str):
        # 내가 원하는 포맷으로 로그 가공 (시간 | 유저ID | 내용)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{now}] [User: {user_id}] {message}"
        
        # 큐에 로그 집어넣기
        await self.queue.put(log_entry)

    async def stream(self):
        while True:
            # 큐에 새로운 로그가 들어올 때까지 대기했다가 가져옴
            log_entry = await self.queue.get()
            yield f"data: {log_entry}\n\n"

# 전역 객체로 생성해서 어디서든 불러다 쓸 수 있게 함
log_manager = LogManager()
