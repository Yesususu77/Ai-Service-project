# 10종 감정 리스트 (사용자님 설계 준수)
VALID_MOODS = ["긴장", "로맨틱", "슬픔", "액션", "평화", "신비", "공포", "희망", "분노", "코믹"]

# SFX 관련 설정
MAX_SFX_COUNT = 3
SFX_COOLDOWN_SEC = 30  # 30초 내 동일 효과음 중복 방지

# 에너지 범위
ENERGY_RANGE = (1, 5)

# 분석 쿨다운 (문장 끝 감지 시 1초 대기 등 사용자님 설계 반영)
ANALYSIS_COOLDOWN = 1.0
DEBOUNCE_INTERVAL = 1.5
