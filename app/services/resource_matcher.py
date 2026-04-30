import os
import httpx

from app import config

# ──────────────────────────────────────────────
# Supabase 설정
# ──────────────────────────────────────────────

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")

_SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ──────────────────────────────────────────────
# SFX 키워드 → 영문 파일명 변환 규칙
# 한국어 키워드를 영문 파일명으로 매핑
# 규칙: 키워드를 의미에 맞는 영단어로 변환 후 소문자_언더스코어 형식 사용
# ──────────────────────────────────────────────

SFX_FILE_MAP: dict[str, str] = {
    # dramatic
    "천둥":     "assets/sfx/thunder.mp3",
    "심장박동": "assets/sfx/heartbeat.mp3",
    "경고음":   "assets/sfx/warning.mp3",
    "폭발음":   "assets/sfx/explosion.mp3",
    "긴장음":   "assets/sfx/tension.mp3",

    # calm
    "바람":     "assets/sfx/wind.mp3",
    "빗소리":   "assets/sfx/rain.mp3",
    "새소리":   "assets/sfx/birds.mp3",
    "파도소리": "assets/sfx/waves.mp3",
    "풀벌레":   "assets/sfx/crickets.mp3",

    # romantic
    "피아노":   "assets/sfx/piano.mp3",
    "바이올린": "assets/sfx/violin.mp3",
    "속삭임":   "assets/sfx/whisper.mp3",
    "설렘음":   "assets/sfx/flutter.mp3",
    "종소리":   "assets/sfx/bell.mp3",

    # horror
    "비명":     "assets/sfx/scream.mp3",
    "삐걱임":   "assets/sfx/creak.mp3",
    "발소리":   "assets/sfx/footsteps.mp3",
    "숨소리":   "assets/sfx/breathing.mp3",
    "으스스한음": "assets/sfx/eerie.mp3",

    # action
    "총성":     "assets/sfx/gunshot.mp3",
    "엔진음":   "assets/sfx/engine.mp3",
    "충돌음":   "assets/sfx/crash.mp3",
    "사이렌":   "assets/sfx/siren.mp3",
    "질주음":   "assets/sfx/dash.mp3",

    # common
    "클릭":     "assets/sfx/click.mp3",
    "알림음":   "assets/sfx/notification.mp3",
    "전환음":   "assets/sfx/transition.mp3",
}


# ──────────────────────────────────────────────
# BGM 트랙 조회
# ──────────────────────────────────────────────

async def fetch_bgm_track(mood: list[str], energy: int) -> dict | None:
    """
    Supabase의 bgm_tracks 테이블에서 mood와 energy에 맞는 BGM 트랙을 조회한다.

    - 1차 쿼리: energy + mood 첫 번째 값 모두 일치하는 트랙 조회
    - 결과 없으면 2차 쿼리: energy만 일치하는 트랙 조회
    - 최종적으로도 없으면 None 반환

    Args:
        mood:   감정 리스트 (첫 번째 값을 우선 사용)
        energy: 에너지 값 (1~5)

    Returns:
        BGM 트랙 dict {"id", "title", "url", "mood", "energy"} 또는 None
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None

    primary_mood = mood[0] if mood else ""

    async with httpx.AsyncClient(timeout=5) as client:

        # 1차 쿼리: energy + mood 조건
        if primary_mood:
            url = (
                f"{SUPABASE_URL}/rest/v1/bgm_tracks"
                f"?energy=eq.{energy}&mood=eq.{primary_mood}&limit=1"
            )
            try:
                response = await client.get(url, headers=_SUPABASE_HEADERS)
                response.raise_for_status()
                results = response.json()
                if results:
                    return results[0]
            except (httpx.HTTPStatusError, httpx.RequestError):
                return None

        # 2차 쿼리: energy 조건만
        url = f"{SUPABASE_URL}/rest/v1/bgm_tracks?energy=eq.{energy}&limit=1"
        try:
            response = await client.get(url, headers=_SUPABASE_HEADERS)
            response.raise_for_status()
            results = response.json()
            if results:
                return results[0]
        except (httpx.HTTPStatusError, httpx.RequestError):
            return None

    return None


# ──────────────────────────────────────────────
# SFX 키워드 → URL 변환
# ──────────────────────────────────────────────

def get_sfx_urls(sfx_list: list[str]) -> list[dict]:
    """
    SFX 키워드 목록을 실제 오디오 파일 경로로 변환한다.

    - SFX_FILE_MAP에 없는 키워드는 결과에서 제외한다.

    Args:
        sfx_list: SFX 키워드 문자열 리스트

    Returns:
        [{"keyword": "천둥", "url": "assets/sfx/thunder.mp3"}, ...] 형태의 리스트

    Example:
        get_sfx_urls(["천둥", "없는키워드"]) -> [{"keyword": "천둥", "url": "assets/sfx/thunder.mp3"}]
    """
    result = []
    for keyword in sfx_list:
        url = SFX_FILE_MAP.get(keyword)
        if url:
            result.append({"keyword": keyword, "url": url})
    return result