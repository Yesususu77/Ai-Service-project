from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    StyleChangeRequest,
    StyleChangeResponse,
)
from app.services import openai_service, validator, session_manager, resource_matcher
from app.utils import trigger

router = APIRouter()


# ──────────────────────────────────────────────
# POST /analyze
# ──────────────────────────────────────────────

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    """
    텍스트를 분석하여 mood, energy, sfx, bgm을 반환한다.

    처리 흐름:
    a) 문장 종결 또는 디바운스 조건 확인
    b) 새 request_id 생성 (레이스 컨디션 방지)
    c) OpenAI API 호출
    d) 최신 요청 여부 확인
    e) 실패 시 폴백 반환
    f) 결과 검증 및 정제
    g) BGM 트랙 및 SFX URL 조회
    h) 결과 저장 후 반환
    """
    text = req.text
    style = req.style
    user_id = req.user_id
    prev_text = req.prev_text

    # a) 트리거 조건 확인
    if not trigger.is_sentence_end(text) and not trigger.should_debounce(text, prev_text):
        raise HTTPException(
            status_code=400,
            detail="분석 트리거 조건 미충족"
        )

    # b) 새 request_id 생성
    request_id = session_manager.set_request_id(user_id)

    # c) OpenAI API 호출
    raw = await openai_service.call_openai_with_retry(text, style)

    # d) 최신 요청 여부 확인
    if not session_manager.is_latest_request(user_id, request_id):
        raise HTTPException(
            status_code=409,
            detail="구버전 요청 폐기"
        )

    # e) OpenAI 실패 시 폴백 처리
    if raw is None:
        fallback = session_manager.get_fallback_result(user_id)
        if fallback:
            bgm = await resource_matcher.fetch_bgm_track(
                fallback["mood"], fallback["energy"]
            )
            sfx_urls = resource_matcher.get_sfx_urls(fallback["sfx"])
            return AnalyzeResponse(
                **fallback,
                bgm=bgm,
                sfx_urls=sfx_urls,
                is_fallback=True,
            )
        raise HTTPException(
            status_code=503,
            detail="AI 분석 실패 및 폴백 결과 없음"
        )

    # f) 결과 검증 및 정제
    result = validator.validate_result(raw, style)

    # g) BGM 및 SFX URL 조회
    bgm = await resource_matcher.fetch_bgm_track(result["mood"], result["energy"])
    sfx_urls = resource_matcher.get_sfx_urls(result["sfx"])

    # h) 결과 저장
    session_manager.save_valid_result(user_id, result)

    return AnalyzeResponse(
        **result,
        bgm=bgm,
        sfx_urls=sfx_urls,
        is_fallback=False,
    )


# ──────────────────────────────────────────────
# POST /style-change
# ──────────────────────────────────────────────

@router.post("/style-change", response_model=StyleChangeResponse)
async def style_change(req: StyleChangeRequest):
    """
    스타일 변경 시 세션 상태를 초기화한다.
    last_valid_result는 유지되며 나머지는 리셋된다.
    """
    session_manager.reset_session_on_style_change(req.user_id)
    return StyleChangeResponse(
        success=True,
        message=f"스타일이 {req.new_style}(으)로 변경되었습니다."
    )


# ──────────────────────────────────────────────
# GET /sfx-cooldown/{user_id}/{sfx_keyword}
# ──────────────────────────────────────────────

@router.get("/sfx-cooldown/{user_id}/{sfx_keyword}")
async def sfx_cooldown(user_id: str, sfx_keyword: str):
    """
    특정 SFX 키워드가 쿨다운 중인지 확인한다.
    """
    on_cooldown = session_manager.check_sfx_cooldown(user_id, sfx_keyword)
    return {"keyword": sfx_keyword, "on_cooldown": on_cooldown}


# ──────────────────────────────────────────────
# POST /sfx-played
# ──────────────────────────────────────────────

class SfxPlayedRequest(BaseModel):
    user_id: str
    sfx_keyword: str


@router.post("/sfx-played")
async def sfx_played(req: SfxPlayedRequest):
    """
    SFX가 재생되었음을 기록하여 쿨다운을 시작한다.
    """
    session_manager.update_sfx_cooldown(req.user_id, req.sfx_keyword)
    return {"success": True}