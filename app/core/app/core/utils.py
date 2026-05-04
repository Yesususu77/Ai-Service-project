from app.core import config

def validate_ai_response(raw_response: dict) -> dict:
    """
    AI의 응답이 사용자 설계(Strict Rules)를 준수하는지 검증하고 교정한다.
    """
    # 1. 감정(Mood) 검증: 리스트에 없는 감정은 제거하거나 기본값으로 대체
    valid_moods = [m for m in raw_response.get("mood", []) if m in config.VALID_MOODS]
    if not valid_moods:
        valid_moods = config.DEFAULT_MOOD

    # 2. 에너지(Energy) 검증: 범위를 벗어나면 최소/최대값으로 클램핑
    raw_energy = raw_response.get("energy", 3)
    energy = max(config.ENERGY_RANGE[0], min(config.ENERGY_RANGE[1], raw_energy))

    # 3. SFX 개수 제한: 설계대로 최대 3개까지만 허용
    sfx = raw_response.get("sfx", [])[:config.MAX_SFX_COUNT]

    return {
        "mood": valid_moods,
        "energy": energy,
        "sfx": sfx,
        "errors": raw_response.get("errors", [])
    }
