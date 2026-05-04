from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MusicDeck
import os, json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# ── BGM 추천 (백엔드연결2 bgm_service) ──
import random

BGM_MAP = {
    "긴장": ["tension_1.mp3", "tension_2.mp3"],
    "로맨틱": ["romance_1.mp3"],
    "슬픔": ["sad_1.mp3"],
    "액션": ["action_1.mp3"],
    "평화": ["calm_1.mp3"],
    "신비": ["mystery_1.mp3"],
    "공포": ["horror_1.mp3"],
    "희망": ["hope_1.mp3"],
    "분노": ["anger_1.mp3"],
    "코믹": ["comic_1.mp3"],
}
BASE_URL = "https://storage.vibe.com/"

def recommend_bgm(mood_label: str) -> str:
    tracks = BGM_MAP.get(mood_label, BGM_MAP["평화"])
    return BASE_URL + random.choice(tracks)


# ── 테마 곡 추천 (백엔드연결2 recommend_service) ──
def recommend_theme_songs(mood: str, is_premium: bool):
    base_tracks = [
        {"title": "운명의 서막", "url": "https://storage.vibe.com/theme_01.mp3"},
        {"title": "어둠의 그림자", "url": "https://storage.vibe.com/theme_02.mp3"},
        {"title": "마지막 결전", "url": "https://storage.vibe.com/theme_03.mp3"},
        {"title": "희망의 빛", "url": "https://storage.vibe.com/theme_04.mp3"},
        {"title": "고요한 끝", "url": "https://storage.vibe.com/theme_05.mp3"},
    ]
    return base_tracks[:5 if is_premium else 3]


# ── 내 음악 조회 ──
@router.get("/my-music")
def my_music(user_id: int, db: Session = Depends(get_db)):
    items = db.query(MusicDeck).filter(MusicDeck.user_id == user_id).all()
    return {"items": items}


# ── 음악 덱에 저장 (내부 유틸) ──
def save_to_deck(db: Session, user_id: int, m_type: str,
                 title: str, mood: str, text: str, url: str):
    item = MusicDeck(
        user_id=user_id, type=m_type, title=title,
        mood=mood, input_log=text, music_url=url
    )
    db.add(item)
    db.commit()


# ── 프리미엄: 챕터 테마 생성 ──
class PremiumRequest(BaseModel):
    content: str
    tokens: int
    user_id: int

@router.post("/generate-chapter-theme")
def generate_chapter_theme(data: PremiumRequest, db: Session = Depends(get_db)):
    if data.tokens < 1:
        raise HTTPException(400, "토큰 부족")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"""
소설 기반 음악 생성 JSON:
{data.content}
{{
 "theme_name": "",
 "summary_mood": "",
 "lyria_prompt": ""
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        result = json.loads(raw.replace("```json", "").replace("```", ""))
        music_url = f"https://fake-music/{hash(result['lyria_prompt'])}.mp3"
        save_to_deck(db, data.user_id, "PREMIUM",
                     result.get("theme_name"), result.get("summary_mood"),
                     data.content[:50], music_url)
        result["music_url"] = music_url
        return result
    except Exception as e:
        raise HTTPException(500, f"AI 실패: {e}")