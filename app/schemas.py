from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    nickname: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    nickname: str

    class Config:
        orm_mode = True

        

class AnalyzeRequest(BaseModel):
    text: str           # 분석할 전체 텍스트
    style: str          # 선택된 스타일 (예: "dramatic")
    user_id: str        # 세션 구분용 사용자 ID
    prev_text: str = "" # 이전 텍스트 (디바운스 판단용, 기본값 빈문자열)

class AnalyzeResponse(BaseModel):
    mood: list[str]
    energy: int
    sfx: list[str]
    errors: list
    bgm: dict | None        # BGM 트랙 정보 (없을 수 있음)
    sfx_urls: list[dict]    # SFX 키워드별 URL 목록
    is_fallback: bool = False  # 폴백 결과 여부

class StyleChangeRequest(BaseModel):
    user_id: str
    new_style: str

class StyleChangeResponse(BaseModel):
    success: bool
    message: str