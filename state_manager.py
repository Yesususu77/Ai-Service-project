import time
from app.core.config import SFX_COOLDOWN_SEC

# -------------------------
# 세션 저장소 (메모리 기반)
# -------------------------
_sessions = {}


def init_session(session_id: str):
    _sessions[session_id] = {
        "last_sfx_time": {}
    }


def get_session(session_id: str):
    return _sessions.get(session_id)


def reset_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]


# -------------------------
# SFX 관리 클래스
# -------------------------
class StateManager:
    def filter_sfx(self, session_id: str, sfx_list):
        now = time.time()

        session = _sessions.get(session_id)
        if not session:
            init_session(session_id)
            session = _sessions[session_id]

        last_sfx_time = session["last_sfx_time"]

        filtered = []

        for sfx in sfx_list:
            last_time = last_sfx_time.get(sfx, 0)

            if now - last_time >= SFX_COOLDOWN_SEC:
                filtered.append(sfx)
                last_sfx_time[sfx] = now

        return filtered


state_manager = StateManager()