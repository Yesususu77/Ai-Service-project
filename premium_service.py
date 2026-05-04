import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from database import save_to_deck

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_music_mock(prompt: str):
    # 임시 URL 나중에 변경 !!!!!!!!!!!!!!!!!!!!!
    return f"https://fake-music/{hash(prompt)}.mp3"

def generate_chapter_theme(content: str, tokens: int):

    if tokens < 1:
        return {"error": "토큰 부족"}

    prompt = f"""
소설 기반 음악 생성 JSON:

{content}

{{
 "theme_name": "",
 "summary_mood": "",
 "lyria_prompt": ""
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content
        clean = raw.replace("```json", "").replace("```", "")
        result = json.loads(clean)

        music_url = generate_music_mock(result["lyria_prompt"])

        save_to_deck(
            "PREMIUM",
            result.get("theme_name"),
            result.get("summary_mood"),
            content[:50],
            music_url
        )

        result["music_url"] = music_url
        return result

    except Exception as e:
        print("Premium 오류:", e)
        return {"error": "AI 실패"}