import time
import threading
from uuid import uuid4

from app import config

# ──────────────────────────────────────────────
# 세션 저장소 (메모리 기반)
# 추후 Redis 등으로 교체 시 아래 함수 인터페이스만 유지하면 됨
# ──────────────────────────────────────────────

_store: dict[str, dict] = {}
_lock = threading.Lock()


def _default_session() -> dict:
    return {
        "current_request_id": None,   # 현재 진행 중인 요청의 UUID
        "last_valid_result":  None,   # 마지막으로 성공한 분석 결과
        "mood_buffer":        [],     # 감정 안정화용 최근 감정 누적 목록
        "sfx_cooldown":       {},     # {sfx_keyword: 마지막재생_timestamp}
        "pending_debounce":   False,  # 디바운스 대기 중 여부
    }


# ──────────────────────────────────────────────
# 세션 조회
# ──────────────────────────────────────────────

def get_session(user_id: str) -> dict:
    """
    user_id에 해당하는 세션을 반환한다.
    세션이 없으면 기본값으로 초기화 후 반환한다.

    Args:
        user_id: 사용자 식별자

    Returns:
        세션 dict
    """
    with _lock:
        if user_id not in _store:
            _store[user_id] = _default_session()
        return _store[user_id]


# ──────────────────────────────────────────────
# 요청 ID 관리 (레이스 컨디션 방지)
# ──────────────────────────────────────────────

def set_request_id(user_id: str) -> str:
    """
    새 request_id(UUID4)를 생성하여 세션에 저장하고 반환한다.
    이전 요청은 자동으로 무효화된다.

    Args:
        user_id: 사용자 식별자

    Returns:
        새로 생성된 request_id 문자열
    """
    new_id = str(uuid4())
    with _lock:
        session = _store.setdefault(user_id, _default_session())
        session["current_request_id"] = new_id
    return new_id


def is_latest_request(user_id: str, request_id: str) -> bool:
    """
    인자로 받은 request_id가 현재 세션의 최신 요청인지 확인한다.
    일치하지 않으면 구버전 응답이므로 폐기 신호(False)를 반환한다.

    Args:
        user_id:    사용자 식별자
        request_id: 확인할 요청 ID

    Returns:
        최신 요청이면 True, 아니면 False
    """
    with _lock:
        session = _store.get(user_id)
        if session is None:
            return False
        return session["current_request_id"] == request_id


# ──────────────────────────────────────────────
# 결과 저장 및 폴백
# ──────────────────────────────────────────────

def save_valid_result(user_id: str, result: dict) -> None:
    """
    성공한 분석 결과를 세션에 저장한다.
    mood_buffer에 감정을 추가하며 최대 10개를 유지한다.

    Args:
        user_id: 사용자 식별자
        result:  validate_result()로 정제된 분석 결과 dict
    """
    with _lock:
        session = _store.setdefault(user_id, _default_session())
        session["last_valid_result"] = result

        new_moods = result.get("mood", [])
        session["mood_buffer"] = (session["mood_buffer"] + new_moods)[-10:]


def get_fallback_result(user_id: str) -> dict | None:
    """
    마지막으로 성공한 분석 결과를 반환한다.
    저장된 결과가 없으면 None을 반환한다.

    Args:
        user_id: 사용자 식별자

    Returns:
        last_valid_result dict 또는 None
    """
    with _lock:
        session = _store.get(user_id)
        if session is None:
            return None
        return session["last_valid_result"]


# ──────────────────────────────────────────────
# 스타일 변경 시 세션 초기화
# ──────────────────────────────────────────────

def reset_session_on_style_change(user_id: str) -> None:
    """
    스타일 변경 시 관련 세션 상태를 초기화한다.
    last_valid_result는 유지하고 나머지를 리셋한다.

    Args:
        user_id: 사용자 식별자
    """
    with _lock:
        session = _store.setdefault(user_id, _default_session())
        last = session["last_valid_result"]
        _store[user_id] = _default_session()
        _store[user_id]["last_valid_result"] = last


# ──────────────────────────────────────────────
# SFX 쿨다운 관리
# ──────────────────────────────────────────────

def check_sfx_cooldown(user_id: str, sfx_keyword: str) -> bool:
    """
    해당 SFX 키워드가 쿨다운 중인지 확인한다.

    - 마지막 재생 후 config.SFX_COOLDOWN_SECONDS(30초) 이내면 True(재생 불가).
    - 그 외엔 False(재생 가능).

    Args:
        user_id:     사용자 식별자
        sfx_keyword: 확인할 효과음 키워드

    Returns:
        쿨다운 중이면 True, 재생 가능하면 False
    """
    with _lock:
        session = _store.get(user_id)
        if session is None:
            return False
        last_played = session["sfx_cooldown"].get(sfx_keyword)
        if last_played is None:
            return False
        return (time.time() - last_played) < config.SFX_COOLDOWN_SECONDS


def update_sfx_cooldown(user_id: str, sfx_keyword: str) -> None:
    """
    SFX 키워드의 마지막 재생 시각을 현재 시각으로 갱신한다.

    Args:
        user_id:     사용자 식별자
        sfx_keyword: 재생된 효과음 키워드
    """
    with _lock:
        session = _store.setdefault(user_id, _default_session())
        session["sfx_cooldown"][sfx_keyword] = time.time()