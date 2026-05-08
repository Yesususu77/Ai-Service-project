from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import get_db
from app.models import MusicDeck, BgmTrack 
import os, json, random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
router = APIRouter()

# ── [상태 관리] 감정이 같으면 음악을 유지하기 위한 전역 변수 ──
current_bgm_state = {
    "last_mood": None,
    "last_url": None
}

def recommend_bgm(mood_label: str, db: Session) -> str:
    """
    1. 동일 감정 유지 로직: 감정이 변하지 않았으면 기존 URL 반환
    2. Tags 검색 로직: Supabase bgm_tracks 테이블의 Tags 컬럼에서 감정 키워드 매칭
    3. 스토리지 기반 URL 반환: 테이블의 'url' 컬럼 값을 사용하여 재생
    """
    global current_bgm_state

    # [1] 감정이 유지되는 경우 (재생 중인 곡 유지)
    if mood_label == current_bgm_state["last_mood"] and current_bgm_state["last_url"]:
        return current_bgm_state["last_url"]

    # [2] 감정이 바뀌었을 경우 (새로운 곡 랜덤 추천)
    # Tags 컬럼에서 '#희망', '#슬픔' 등 mood_label이 포함된 행을 찾음
    track = db.query(BgmTrack).filter(
        BgmTrack.Tags.like(f"%{mood_label}%")
    ).order_by(func.random()).first()
    
    # [3] 안전장치: 해당 감정의 곡이 없을 경우 '잔잔' 태그로 대체 검색
    if not track:
        track = db.query(BgmTrack).filter(
            BgmTrack.Tags.like("%잔잔%")
        ).order_by(func.random()).first()
    
    # [4] URL 결정
    # 테이블의 url 컬럼에 스토리지의 Public URL이 이미 들어가 있으므로 그대로 사용
    new_url = track.url if track else "https://storage.vibe.com/default_calm.mp3"

    # [5] 상태 업데이트 (다음 비교를 위해)
    current_bgm_state["last_mood"] = mood_label
    current_bgm_state["last_url"] = new_url

    return new_url


# ── 내 음악 조회 (저장된 덱 확인) ──
@router.get("/my-music")
def my_music(user_id: int, db: Session = Depends(get_db)):
    items = db.query(MusicDeck).filter(MusicDeck.user_id == user_id).all()
    return {"items": items}


# ── 음악 덱에 저장 유틸 ──
def save_to_deck(db: Session, user_id: int, m_type: str,
                 title: str, mood: str, text: str, url: str):
    item = MusicDeck(
        user_id=user_id, type=m_type, title=title,
        mood=mood, input_log=text, music_url=url
    )
    db.add(item)
    db.commit()


# ── 프리미엄: 챕터 테마 생성 (OpenAI 연동) ──
class PremiumRequest(BaseModel):
    content: str
    tokens: int
    user_id: int

@router.post("/generate-chapter-theme")
async def generate_chapter_theme(data: PremiumRequest, db: Session = Depends(get_db)):
    if data.tokens < 1:
        raise HTTPException(400, "토큰 부족")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    prompt = f"""
    소설의 분위기를 분석하여 음악 테마 JSON을 생성하세요.
    내용: {data.content}
    
    JSON 형식만 응답:
    {{
     "theme_name": "창의적인 제목",
     "summary_mood": "핵심 감정",
     "lyria_prompt": "음악 생성을 위한 구체적인 영어 프롬프트"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Lyria 실 생성 전 가상 URL (랜덤 식별자 추가)
        music_url = f"https://storage.vibe.com/generated/theme_{random.randint(100, 999)}.mp3"
        
        save_to_deck(db, data.user_id, "PREMIUM",
                     result.get("theme_name"), result.get("summary_mood"),
                     data.content[:50], music_url)
        
        result["music_url"] = music_url
        return result
        
    except Exception as e:
        raise HTTPException(500, f"AI 생성 실패: {str(e)}")
