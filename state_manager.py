sessions = {}

def init_session(session_id):
    sessions[session_id] = {
        "buffer": [],
        "last_analysis": None,
        "last_time": 0,
        "cooldown": 1.0,
        "style": "default"
    }

def get_session(session_id):
    return sessions.get(session_id)

def reset_session(session_id, style):
    init_session(session_id)
    sessions[session_id]["style"] = style