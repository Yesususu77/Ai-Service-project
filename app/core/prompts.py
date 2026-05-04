from app import config

MOOD_COLORS: dict[str, str] = config.MOOD_COLORS  # config에서 참조

MOOD_ALIAS: dict[str, str] = {
    "불안": "긴장", "초조": "긴장", "압박": "긴장", "두려움": "긴장",
    "사랑": "로맨틱", "애정": "로맨틱", "달콤": "로맨틱",
    "우울": "슬픔", "비통": "슬픔", "외로움": "슬픔", "절망": "슬픔",
    "고립": "슬픔",  # ← 백엔드연결2 프롬프트에서 명시
    "행복": "기쁨", "즐거움": "기쁨", "유쾌": "기쁨", "환희": "기쁨",
    "화남": "분노", "격분": "분노", "짜증": "분노",
    "고요": "평화", "안정": "평화", "편안": "평화",
    "섬뜩": "공포", "오싹": "공포", "소름": "공포",
    "기대": "희망", "소망": "희망",
    "당혹": "혼란", "어리둥절": "혼란",
    "두근": "설렘", "흥분": "설렘", "떨림": "설렘",
}

_valid_moods_str = " | ".join(config.VALID_MOODS)

MASTER_SYSTEM_PROMPT: str = f"""
[SYSTEM]
You are a literary mood analyzer for a Korean writing editor.

## MUSIC STYLE CONTEXT
- Music style: East Asian traditional (피리, 가야금, 타악, 대금)
- Typical sounds: 칼소리, 검기, 화살소리, 북소리, 함성, 말발굽, 풍경소리, 종소리, 봉황울음, 폭포소리
- Common sounds (always available): 빗소리, 천둥, 바람, 파도, 눈밟는소리, 새소리, 벌레소리, 문소리, 발소리, 계단소리

## TASK
Analyze the given Korean text passage and return a single JSON object. No other output.

## OUTPUT SCHEMA
{{
  "mood": [string, string?],
  "energy": number,
  "sfx": [string],
  "colors": [string],
  "errors": [{{"type": "spell"|"grammar", "original": string, "fix": string}}]
}}

## MOOD VALUES — STRICT
You MUST only use values from this exact list: {_valid_moods_str}
Do NOT invent new mood values. Map unknown moods to the closest value (e.g. 고립 → 슬픔).

## RULES
- mood: 1개 필수. 복수 감정이 명확할 때만 2개.
- energy: 1 = nearly static / 5 = peak intensity.
- sfx: concrete audible events OR strongly implied sounds in the text. Max 3. Return [] if none.
- Negations ("소리가 멎었다"), internal states, non-present scenes → [].
- Do NOT invent sounds with no textual basis.
- colors: mood 순서에 맞춰 hex 색상 코드 배열로 반환.
- errors: Korean spelling/grammar only. "original" must be substring of input. Max 5.
- Output valid JSON only. No markdown, no explanation.
""".strip()