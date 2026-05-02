import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_current_mood(text: str):
    """실시간 문장 분석 및 컬러 코드 반환 기능입니다."""
    if not text.strip():
        return {"mood": "중립", "color": "#FFFFFF"}

    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    아래 문장의 감정을 분석해서 '무드'와 어울리는 '헥사 컬러'를 JSON으로 응답해.
    문장: "{text}"
    결과 형식: {{"mood": "감정단어", "color": "#코드"}}
    """
    try:
        response = model.generate_content(prompt, generation_config={"temperature": 0.3})
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"mood": "분석 불가", "color": "#808080"}