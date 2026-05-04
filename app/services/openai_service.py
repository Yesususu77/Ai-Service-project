import os
import asyncio
import json
import httpx

from app import config

# ──────────────────────────────────────────────
# 시스템 프롬프트 생성
# ──────────────────────────────────────────────

from app.core.prompts import MASTER_SYSTEM_PROMPT

def build_system_prompt(style: str) -> str:
    """
    MASTER_SYSTEM_PROMPT를 반환한다.
    style 파라미터는 하위 호환성을 위해 유지하나 현재는 사용하지 않음.
    """
    return MASTER_SYSTEM_PROMPT


# ──────────────────────────────────────────────
# OpenAI API 호출 (재시도 포함)
# ──────────────────────────────────────────────

async def call_openai_with_retry(text: str, style: str) -> dict | None:
    """
    OpenAI API를 비동기로 호출하고, 실패 시 재시도한다.

    - 입력 텍스트는 마지막 TEXT_SLICE_LENGTH(500)자만 사용한다.
    - 타임아웃: OPENAI_TIMEOUT_SECONDS(5초)
    - 실패 시 OPENAI_RETRY_DELAYS 간격으로 최대 OPENAI_MAX_RETRIES(2)회 재시도.
    - 모든 재시도 실패 시 None 반환 (예외를 밖으로 던지지 않음).

    Args:
        text:  분석할 소설 텍스트 (전체)
        style: 스타일 키 (예: "dramatic")

    Returns:
        GPT 응답을 파싱한 dict, 또는 실패 시 None
    """
    # 마지막 N자만 추출
    sliced_text = text[-config.TEXT_SLICE_LENGTH:]

    system_prompt = build_system_prompt(style)
    api_key = os.environ.get("OPENAI_API_KEY", "")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": config.OPENAI_MODEL,
        "temperature": config.OPENAI_TEMPERATURE,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": sliced_text},
        ],
    }

    last_exception = None

    # 최초 1회 + 재시도 OPENAI_MAX_RETRIES회
    for attempt in range(config.OPENAI_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=config.OPENAI_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)

        except httpx.TimeoutException as e:
            last_exception = e

        except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError, KeyError) as e:
            last_exception = e

        # 마지막 시도가 아니면 딜레이 후 재시도
        if attempt < config.OPENAI_MAX_RETRIES:
            delay_ms = config.OPENAI_RETRY_DELAYS[attempt]
            await asyncio.sleep(delay_ms / 1000)

    # 모든 재시도 실패
    return None