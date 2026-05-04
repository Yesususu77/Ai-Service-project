import random

# 간단한 매핑 (확장 가능)
BGM_MAP = {
    "긴장": ["tension_1.mp3", "tension_2.mp3"],
    "로맨틱": ["romance_1.mp3"],
    "슬픔": ["sad_1.mp3"],
    "액션": ["action_1.mp3"],
    "평화": ["calm_1.mp3"],
    "신비": ["mystery_1.mp3"],
    "공포": ["horror_1.mp3"],
    "희망": ["hope_1.mp3"],
    "분노": ["anger_1.mp3"],
    "코믹": ["comic_1.mp3"],
}


BASE_URL = "https://storage.vibe.com/"


def recommend_bgm(mood_label: str):
    tracks = BGM_MAP.get(mood_label)

    if not tracks:
        tracks = BGM_MAP["평화"]

    selected = random.choice(tracks)
    return BASE_URL + selected