import re
from app import config

# ──────────────────────────────────────────────
# 문장 종결 패턴 (사전 컴파일)
# 대상 문자: '.', '!', '?', '。', '！', '？', '\n'
# ──────────────────────────────────────────────

SENTENCE_END_PATTERN = re.compile(r'[.!?。！？\n]$')


def is_sentence_end(text: str) -> bool:
    """
    텍스트가 문장 종결 문자로 끝나는지 확인한다.

    Args:
        text: 확인할 문자열

    Returns:
        종결 문자로 끝나면 True, 아니면 False

    Example:
        is_sentence_end("안녕하세요.")  -> True
        is_sentence_end("안녕하세요")   -> False
        is_sentence_end("정말?")        -> True
    """
    if not text:
        return False
    return bool(SENTENCE_END_PATTERN.search(text))


def should_debounce(text: str, prev_text: str) -> bool:
    """
    두 텍스트의 길이 차이가 DEBOUNCE_THRESHOLD_CHARS 이상이면 디바운스가 필요하다고 판단한다.

    - 짧은 시간에 100자 이상 변화가 있었으면 True 반환.
    - 변화량이 적으면 False 반환.

    Args:
        text:      현재 텍스트
        prev_text: 이전 텍스트

    Returns:
        디바운스 필요 시 True, 불필요 시 False

    Example:
        should_debounce("a" * 200, "a" * 50)  -> True  (차이 150자)
        should_debounce("a" * 60,  "a" * 50)  -> False (차이 10자)
    """
    return abs(len(text) - len(prev_text)) >= config.DEBOUNCE_THRESHOLD_CHARS


def extract_recent_context(text: str) -> str:
    """
    텍스트의 마지막 TEXT_SLICE_LENGTH(500)자만 반환한다.

    - GPT에 전달할 텍스트 양을 제한하기 위해 사용한다.
    - 텍스트가 500자 이하이면 전체를 그대로 반환한다.

    Args:
        text: 원본 텍스트 전체

    Returns:
        마지막 500자 문자열

    Example:
        extract_recent_context("가" * 600) -> "가" * 500
        extract_recent_context("짧은텍스트") -> "짧은텍스트"
    """
    return text[-config.TEXT_SLICE_LENGTH:]