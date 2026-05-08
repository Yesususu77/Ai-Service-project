from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func # 랜덤 정렬을 위해 추가
from app.database import get_db
from app.models import MusicDeck, Music  # Music 모델이 있다고 가정 (DB 테이블)
import os, json, random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# ── BGM 추천 로직 (DB 연동 버전으로 업그레이드) ──

def recommend_bgm(mood_label: str, db: Session) -> str:
    """
    고정된 리스트가 아니라, DB에 저장된 100여 곡 중 
    해당 감정에 맞는 곡을 랜덤으로 하나 추출합니다.
    """
    # 1. DB에서 해당 감정(mood)을 가진 곡들을 무작위로 하나 선택
    track = db.query(Music).filter(Music.mood == mood_label).order_by(func.random()).first()
    
    # 2. 만약 해당 감정에 맞는 곡이 DB에 없다면 '평화' 감정에서 랜덤 추출 (예외 방지)
    if not track:
        track = db.query(Music).filter(Music.mood == "평화").order_by(func.random()).first()
    
    # 3. 곡이 존재하면 해당 URL 반환, 아예 없으면 기본 fallback URL 반환
    if track:
        return track.music_url
    return "https://storage.vibe.com/default_calm.mp3"


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
async def generate_chapter_theme(data: PremiumRequest, db: Session = Depends(get_db)):
    if data.tokens < 1:
        raise HTTPException(400, "토큰 부족")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # GPT에게 더 명확한 JSON 형식을 요구하도록 프롬프트 보강
    prompt = f"""
    Analyze the following novel content and provide a theme song metadata in JSON format.
    Content: {data.content}
    
    Return ONLY JSON:
    {{
     "theme_name": "Something Creative",
     "summary_mood": "Overall Emotion",
     "lyria_prompt": "Detailed musical description for AI generation"
    }}
    """
    
    try:
        # 비동기 처리가 권장되나 현재 구조에 맞춰 작성
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" } # JSON 모드 강제 (GPT-4o 지원)
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # 실제 Lyria API 연동 전까지는 해시 기반의 가상 URL 생성
        music_url = f"https://storage.vibe.com/generated/{random.randint(1000, 9999)}.mp3"
        
        save_to_deck(db, data.user_id, "PREMIUM",
                     result.get("theme_name"), result.get("summary_mood"),
                     data.content[:50], music_url)
        
        result["music_url"] = music_url
        return result
        
    except Exception as e:
        raise HTTPException(500, f"AI 생성 실패: {str(e)}")
