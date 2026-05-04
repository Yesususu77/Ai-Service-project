import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_passage(text: str):
    prompt = f"""
    아래 문장을 분석해서 JSON으로 반환:

    {{
      "mood": ["감정"],
      "energy": 1~5,
      "sfx": ["효과음"],
      "errors": [{{"type":"grammar","original":"","fix":""}}]
    }}

    문장: "{text}"
    """

    try:
        res = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        text = res.choices[0].message.content
        clean = text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

    except Exception as e:
        print("GPT 오류:", e)
        return None