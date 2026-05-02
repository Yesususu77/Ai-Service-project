import google.generativeai as genai
import json

# 1. API 설정
API_KEY = "YOUR_GEMINI_API_KEY" 
genai.configure(api_key=API_KEY)

def generate_chapter_theme(chapter_content: str, user_tokens: int):
    """
    한 장이 종료된 후, 유료 토큰을 사용하여 고퀄리티 테마곡 구성을 생성합니다.
    """
    # 토큰 체크 로직 (나중에 추가 구상해야 함)
    if user_tokens < 1:
        return {"error": "Insufficient tokens. Please recharge."}

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 한 장의 전체 내용을 요약하여 '테마'를 추출하는 프롬프트
    prompt = f"""
    너는 소설의 한 챕터를 분석해 그 장을 대표하는 '엔딩 테마곡'을 설계하는 음악 감독이야.
    아래 챕터의 전체 내용을 읽고, 이 이야기에 가장 어울리는 고퀄리티 테마곡 파라미터를 작성해줘.
    
    [챕터 내용]
    "{chapter_content}"
    
    결과는 반드시 아래 JSON 형식으로만 응답해:
    {{
        "theme_name": "테마곡 제목 (국문)",
        "summary_mood": "챕터 전체를 관통하는 핵심 감정",
        "musical_structure": "곡의 구조 (예: Intro-A-B-Climax-Outro)",
        "genre": "추천 장르",
        "bpm": "추천 BPM",
        "instruments": ["사용될 주요 악기 3개 이상"],
        "ai_music_prompt": "음악 생성 AI(Lyria 등)에 입력할 아주 상세한 영문 묘사 (100자 내외)"
    }}
    """

    try:
        # 유료 기능이므로 안정적인 생성을 위해 약간의 창의성(temperature) 부여
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(temperature=0.7)
        )
        
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        result = json.loads(clean_json)
        
        from database import save_to_deck
        save_to_deck(
            m_type="PREMIUM", 
            title=result.get("theme_name"), 
            mood=result.get("summary_mood"), 
            text=chapter_content[:50] # 앞부분만 기록
        )

        # 성공 시 토큰 차감 대상임을 표시
        result["token_consumed"] = True
        return result
        
    except Exception as e:
        return {"error": str(e)}

# 2. 실행 예시 (토큰이 있다고 가정)
if __name__ == "__main__":
    chapter_text = "주인공은 결국 긴 여행 끝에 전설의 나무 아래 도착했다. 하지만 그곳에는 기대했던 보물 대신 낡은 일기장 하나만이 놓여 있었다..."
    current_tokens = 10  # 예린님의 유저 데이터에서 가져올 값
    
    theme_result = generate_chapter_theme(chapter_text, current_tokens)
    print(theme_result)


