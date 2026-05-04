from app import config


from app.core.prompts import MOOD_ALIAS

def filter_moods(mood_list: list) -> list[str]:
    """
    GPT가 반환한 감정 목록을 필터링한다.
    - VALID_MOODS에 있으면 그대로 사용
    - MOOD_ALIAS에 있으면 유효 감정으로 변환
    - 둘 다 아니면 제외
    - 결과가 비면 DEFAULT_MOOD 반환
    """
    if not isinstance(mood_list, list):
        return config.DEFAULT_MOOD

    filtered = []
    for m in mood_list:
        if m in config.VALID_MOODS:
            filtered.append(m)
        elif m in MOOD_ALIAS:
            filtered.append(MOOD_ALIAS[m])

    return filtered if filtered else config.DEFAULT_MOOD


def clamp_energy(energy) -> int:
    """
    energy 값을 정수로 변환하고 유효 범위로 클램핑한다.

    - float/int 모두 허용하며 round()로 반올림한다.
    - config.ENERGY_MIN(1) ~ config.ENERGY_MAX(5) 범위를 벗어나면 경계값으로 고정한다.
    - 변환 실패 시 기본값 3을 반환한다.

    Args:
        energy: GPT 응답의 energy 값 (int, float, str 등)

    Returns:
        1~5 사이의 정수

    Example:
        clamp_energy(3.7)  -> 4
        clamp_energy(0)    -> 1
        clamp_energy(99)   -> 5
        clamp_energy("bad") -> 3
    """
    try:
        value = round(float(energy))
        return max(config.ENERGY_MIN, min(config.ENERGY_MAX, value))
    except (TypeError, ValueError):
        return 3


def filter_sfx(sfx_list: list, style: str) -> list[str]:
    """
    GPT가 반환한 SFX 목록에서 허용된 키워드만 필터링한다.

    - config.VALID_SFX[style] + config.COMMON_SFX 에 있는 키워드만 남긴다.
    - style이 VALID_SFX에 없으면 COMMON_SFX만 기준으로 필터링한다.
    - 최대 config.MAX_SFX_COUNT(3)개까지만 반환한다.

    Args:
        sfx_list: GPT 응답의 sfx 리스트
        style:    현재 스타일 키 (예: "dramatic")

    Returns:
        허용된 SFX 키워드 리스트 (최대 3개)

    Example:
        filter_sfx(["천둥", "클릭", "unknown"], "dramatic") -> ["천둥", "클릭"]
    """
    if not isinstance(sfx_list, list):
        return []

    allowed = set(config.VALID_SFX.get(style, [])) | set(config.COMMON_SFX)
    filtered = [s for s in sfx_list if s in allowed]
    return filtered[:config.MAX_SFX_COUNT]


def normalize_errors(errors) -> list:
    """
    GPT 응답의 errors 필드를 정규화한다.

    - None이거나 리스트가 아니면 빈 리스트를 반환한다.
    - 그 외엔 그대로 반환한다.

    Args:
        errors: GPT 응답의 errors 값

    Returns:
        리스트 형태의 errors

    Example:
        normalize_errors(None)           -> []
        normalize_errors("error string") -> []
        normalize_errors(["err1"])       -> ["err1"]
    """
    if not isinstance(errors, list):
        return []
    return errors


def validate_result(raw: dict, style: str) -> dict:
    """
    GPT 응답 dict를 시스템에서 바로 사용할 수 있도록 정제한다.

    - 위 4개 함수를 조합하여 각 필드를 검증 및 정규화한다.
    - raw에 키가 없을 경우 안전한 기본값을 사용한다.

    Args:
        raw:   GPT 응답을 파싱한 dict
        style: 현재 스타일 키

    Returns:
        정제된 결과 dict
        {"mood": list, "energy": int, "sfx": list, "errors": list}

    Example:
        validate_result({"mood": ["기쁨"], "energy": 6, "sfx": ["천둥"], "errors": None}, "dramatic")
        -> {"mood": ["기쁨"], "energy": 5, "sfx": ["천둥"], "errors": []}
    """
    return {
        "mood":   filter_moods(raw.get("mood", [])),
        "energy": clamp_energy(raw.get("energy", 3)),
        "sfx":    filter_sfx(raw.get("sfx", []), style),
        "errors": normalize_errors(raw.get("errors")),
    }