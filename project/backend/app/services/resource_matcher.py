import os
import httpx
import random
import json
from urllib.parse import quote

# ──────────────────────────────────────────────
# Supabase 설정 (환경변수 관리)
# ──────────────────────────────────────────────
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

_SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ──────────────────────────────────────────────
# 매핑 규칙 (AI 감정 -> DB 카테고리)
# ──────────────────────────────────────────────
MOOD_TO_EMOTION = {
    "긴장":   "긴장",
    "분노":   "분노",
    "공포":   "공포",
    "슬픔":   "슬픔",
    "기쁨":   "기쁨",
    "설렘":   "기쁨",
    "로맨틱": "기쁨",
    "희망":   "액션",
    "신비":   "신비",
    "평화":   "기타",
    "혼란":   "기타",
    "액션":   "액션",
    "코믹":   "기쁨",
}

SFX_FILE_MAP: dict[str, str] = {
    "천둥": "assets/sfx/thunder.mp3",
    "심장박동": "assets/sfx/heartbeat.mp3",
    "경고음": "assets/sfx/warning.mp3",
    "폭발음": "assets/sfx/explosion.mp3",
    "긴장음": "assets/sfx/tension.mp3",
    "바람": "assets/sfx/wind.mp3",
    "빗소리": "assets/sfx/rain.mp3",
    "새소리": "assets/sfx/birds.mp3",
    "파도소리": "assets/sfx/waves.mp3",
    "풀벌레": "assets/sfx/crickets.mp3",
    "피아노": "assets/sfx/piano.mp3",
    "바이올린": "assets/sfx/violin.mp3",
    "속삭임": "assets/sfx/whisper.mp3",
    "설렘음": "assets/sfx/flutter.mp3",
    "종소리": "assets/sfx/bell.mp3",
    "비명": "assets/sfx/scream.mp3",
    "삐걱임": "assets/sfx/creak.mp3",
    "발소리": "assets/sfx/footsteps.mp3",
    "숨소리": "assets/sfx/breathing.mp3",
    "으스스한음": "assets/sfx/eerie.mp3",
    "총성": "assets/sfx/gunshot.mp3",
    "엔진음": "assets/sfx/engine.mp3",
    "충돌음": "assets/sfx/crash.mp3",
    "사이렌": "assets/sfx/siren.mp3",
    "질주음": "assets/sfx/dash.mp3",
    "클릭": "assets/sfx/click.mp3",
    "알림음": "assets/sfx/notification.mp3",
    "전환음": "assets/sfx/transition.mp3",
}

# ──────────────────────────────────────────────
# BGM 트랙 랜덤 조회 로직
# ──────────────────────────────────────────────
async def fetch_bgm_track(mood: list[str], energy: int) -> dict | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: Supabase 설정이 누락되었습니다.")
        return None

    # 1. 감정어 결정
    primary_mood = mood[0] if mood else "평화"
    db_emotion = MOOD_TO_EMOTION.get(primary_mood, "기타")
    encoded_emotion = quote(db_emotion)

    async with httpx.AsyncClient(timeout=5) as client:
        # [수정 포인트] limit=1 삭제 -> 해당 감정 모든 곡 가져오기
        url = (
            f"{SUPABASE_URL}/rest/v1/bgm_tracks"
            f"?emotion=eq.{encoded_emotion}&select=Title,url,emotion,genre,bpm"
        )
        
        try:
            response = await client.get(url, headers=_SUPABASE_HEADERS)
            response.raise_for_status()
            results = response.json()
            
            if results:
                # [핵심] 결과 리스트 중 랜덤하게 하나 선택
                selected_track = random.choice(results)
                print(f"DEBUG: 감정 [{db_emotion}] 조회 성공 -> {len(results)}곡 중 '{selected_track['Title']}' 선택")
                return selected_track
            
            print(f"DEBUG: 감정 [{db_emotion}]에 해당하는 곡이 DB에 없습니다.")

        except Exception as e:
            print(f"DEBUG: 1차 쿼리 실패 ({db_emotion}) -> {e}")

        # 2차 쿼리: 1차 실패 시 '기타' 혹은 전체에서 랜덤하게 1개
        fallback_url = f"{SUPABASE_URL}/rest/v1/bgm_tracks?select=Title,url,emotion,genre,bpm"
        try:
            response = await client.get(fallback_url, headers=_SUPABASE_HEADERS)
            results = response.json()
            if results:
                return random.choice(results)
        except Exception as e:
            print(f"DEBUG: 최종 폴백 쿼리 실패 -> {e}")
            return None

    return None

# ──────────────────────────────────────────────
# SFX 리스트 반환 로직
# ──────────────────────────────────────────────
async def get_sfx_urls(sfx_list: list[str]) -> list[dict]:
    """
    SFX 키워드 목록을 Supabase sfx_tracks 테이블에서 조회하여 URL로 변환한다.
    """
    if not SUPABASE_URL or not SUPABASE_KEY or not sfx_list:
        return []

    result = []
    async with httpx.AsyncClient(timeout=5) as client:
        for keyword in sfx_list:
            encoded_keyword = quote(keyword)
            url = (
                f"{SUPABASE_URL}/rest/v1/sfx_tracks"
                f"?keyword=eq.{encoded_keyword}&limit=1&select=title,url,keyword"
            )
            try:
                response = await client.get(url, headers=_SUPABASE_HEADERS)
                response.raise_for_status()
                data = response.json()
                if data:
                    result.append({
                        "keyword": keyword,
                        "url": data[0]["url"]
                    })
            except (httpx.HTTPStatusError, httpx.RequestError):
                continue

    return result
