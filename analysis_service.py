import json, os
from openai import OpenAI
from dotenv import load_dotenv

from app.core.config import *
from app.core.prompts import MASTER_SYSTEM_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_passage(text: str, style: str = "default"):
    prompt = f"""
    문장을 분석해서 JSON으로 반환:

    {{
      "mood": ["감정"],
      "energy": 1~5,
      "sfx": ["효과음"],
      "errors": []
    }}

    문장: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content