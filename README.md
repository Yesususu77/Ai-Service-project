# EditMuse! AI System Architecture & Design

본 문서는 EditMuse!의 핵심인 AI 감정 분석 및 BGM/SFX 매핑 로직의 설계 사양을 담고 있습니다.

## 1. AI 분석 엔진 (Prompt Engineering)
사용자 텍스트를 분석하여 음악적 파라미터로 변환하기 위해 고도로 정제된 **Strict Prompting** 기술을 적용했습니다.

- **Persona**: 한국 웹소설 전문 음악 감독
- **Output Format**: Pydantic 기반의 엄격한 JSON 스키마 준수
- **Style Context**: 스타일별 악기 및 효과음 가이드라인 분리

## 2. 감정 매핑 로직 (The 10-Mood System)
시스템의 안정성을 위해 감정 분석의 범위를 아래 10가지 핵심 감정으로 제한(Strict Mapping)합니다.

| 감정 | 설명 | 주요 악기/분위기 |
| :--- | :--- | :--- |
| **긴장** | 긴박한 대치 상황 | 빠른 현악기 피치카토 |
| **로맨틱** | 고백, 설렘 | 부드러운 피아노, 플룻 |
| **슬픔** | 이별, 고립, 쓸쓸함 | 대금, 첼로 솔로 |
| ... | (중략) | ... |

## 3. 시스템 안정화 기술 (Reliability)
단순 분석을 넘어 서비스의 사용자 경험(UX)을 높이기 위한 로직을 포함합니다.

- **Request ID Tracking**: 레이스 컨디션 방지를 통한 응답 순서 보장
- **Mood Stabilization Buffer**: 감정이 급격하게 튀는 현상을 막기 위한 버퍼링 시스템
- **SFX Cooldown**: 동일 효과음의 중복 재생을 막는 30초 쿨다운 타이머

## 4. Core Files
- `app/core/prompts.py`: 마스터 시스템 프롬프트 관리
- `app/core/config.py`: 시스템 전역 파라미터 및 상수 설정
- `app/core/utils.py`: AI 응답 데이터 검증 및 클램핑 로직
