def recommend_theme_songs(mood: str, is_premium: bool):
    base_tracks = [
        {"title": "운명의 서막", "url": "https://storage.vibe.com/theme_01.mp3"},
        {"title": "어둠의 그림자", "url": "https://storage.vibe.com/theme_02.mp3"},
        {"title": "마지막 결전", "url": "https://storage.vibe.com/theme_03.mp3"},
        {"title": "희망의 빛", "url": "https://storage.vibe.com/theme_04.mp3"},
        {"title": "고요한 끝", "url": "https://storage.vibe.com/theme_05.mp3"},
    ]

    limit = 5 if is_premium else 3
    return base_tracks[:limit]