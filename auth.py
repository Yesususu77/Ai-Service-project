from datetime import datetime, timedelta
from jose import jwt, JWTError

SECRET_KEY = "super-secret-key"
ALGORITHM = "HS256"

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["user_id"]
    except JWTError:
        return None