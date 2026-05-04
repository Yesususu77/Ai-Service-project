/**
 * 🎵 EditMuse! Core Analysis Engine
 * Architecture & Algorithm Design by suin-ai
 * 
 * 주요 기능: 실시간 텍스트 분석, 감정 안정화 버퍼, 
 *           레이스 컨디션 방지, 스타일별 SFX 필터링, 에러 핸들링
 */

// --- 1. 설정 및 상수 데이터 (Configuration) ---
const VALID_MOODS = ["긴장", "로맨틱", "슬픔", "액션", "평화", "신비", "공포", "희망", "분노", "코믹", "분석 불가"];

// 감정별 컬러 매핑 테이블 (suin-ai 설계)
const MOOD_COLORS = {
    "긴장": "#FF4500", "로맨틱": "#FFC0CB", "슬픔": "#4682B4",
    "액션": "#D2691E", "평화": "#98FB98", "희망": "#FFD700",
    "공포": "#4B0082", "분노": "#B22222", "신비": "#9370DB", 
    "코믹": "#ADFF2F", "분석 불가": "#808080"
};

const VALID_SFX = {
    common: ["빗소리", "천둥", "바람", "파도", "눈밟는소리", "새소리", "벌레소리", "문소리", "발소리", "계단소리"],
    oriental: ["칼소리", "검기", "화살소리", "북소리", "함성", "말발굽", "풍경소리", "종소리", "봉황울음", "폭포소리"],
    orchestral: ["금속충돌", "방패소리", "마법이펙트", "폭발", "성문소리", "횃불소리", "드래곤울음", "교회종소리"],
    piano: ["카페소음", "핸드폰진동", "키보드소리", "자동차소리", "와인잔소리", "엘리베이터소리"],
    dark: ["심장소리", "숨소리", "삐걱소리", "유리깨지는소리", "총성", "비명", "사이렌"],
    lofi: ["식기소리", "요리소리", "고양이소리", "강아지소리", "시냇물소리", "커피내리는소리"],
};

// --- 2. 상태 관리 변수 (Internal State) ---
let lastValidResult = null;
let currentRequestId = 0;
let isFirstAnalysis = true;
let lastAnalyzedLength = 0;
let cooldownTimer = null;
let debounceTimer = null;
const moodBuffer = [];
const sfxCooldown = new Map();

const BUFFER_SIZE = 3;
const DEBOUNCE_CHARS = 100;

/**
 * [API 호출] 통합 분석 엔진 (백엔드 연동)
 */
async function analyzePassage(text, style = "piano", retries = 2) {
    const requestId = ++currentRequestId;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);

        try {
            // 백엔드의 통합 분석 API 호출 (suin-ai 아키텍처 반영)
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: text.slice(-500), style }),
                signal: controller.signal
            });

            clearTimeout(timeout);

            // 서버 에러(500 등) 발생 시에도 우리 규격대로 응답 처리
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            
            // 레이스 컨디션 체크
            if (requestId !== currentRequestId) return null;

            // 데이터 검증 및 컬러 매핑 추가
            const result = validateResult(data, style);
            lastValidResult = result;
            return result;

        } catch (err) {
            clearTimeout(timeout);
            console.error(`Attempt ${attempt + 1} failed:`, err);

            if (attempt === retries) {
                // [최종 에러 핸들링] 모든 재시도 실패 시 "분석 불가" 상태 반환
                const fallback = {
                    mood: ["분석 불가"],
                    energy: 3,
                    sfx: [],
                    color: MOOD_COLORS["분석 불가"],
                    errors: ["네트워크 연결 확인 필요"]
                };
                return requestId === currentRequestId ? fallback : null;
            }
            await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
        }
    }
}

/**
 * 응답 데이터 검증 및 컬러 매핑
 */
function validateResult(result, style = "piano") {
    // 1. 감정 검증 및 컬러 매칭
    result.mood = (result.mood || []).filter(m => VALID_MOODS.includes(m));
    if (result.mood.length === 0) result.mood = ["평화"];
    
    // 메인 감정에 따른 컬러 할당 (suin-ai 방식)
    result.color = MOOD_COLORS[result.mood[0]] || "#808080";

    // 2. 에너지 보정 (1~5)
    result.energy = Math.min(5, Math.max(1, Math.round(result.energy || 3)));

    // 3. SFX 교차 검증
    const allowed = [...VALID_SFX.common, ...(VALID_SFX[style] || [])];
    result.sfx = (result.sfx || []).filter(s => allowed.includes(s)).slice(0, 3);

    return result;
}

/**
 * [입력 트리거] 사용자 타이핑 감지
 */
export function onTextChange(text, style, callback) {
    const endsWithSentence = /[.!?…\n]$/.test(text.trim());
    const charDiff = Math.abs(text.length - lastAnalyzedLength);

    if (endsWithSentence && !cooldownTimer) {
        cooldownTimer = setTimeout(() => {
            executeAnalysis(text, style, callback);
            cooldownTimer = null;
        }, 1000);
        return;
    }

    if (charDiff >= DEBOUNCE_CHARS) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            executeAnalysis(text, style, callback);
        }, 1500);
    }
}

async function executeAnalysis(text, style, callback) {
    lastAnalyzedLength = text.length;
    const result = await analyzePassage(text, style);
    if (result) {
        postProcess(result, callback);
    }
}

/**
 * [후처리] 감정 안정화 및 최종 렌더링
 */
function postProcess(result, callback) {
    result.sfx.forEach(playSFX);

    const currentMood = result.mood[0];
    
    if (isFirstAnalysis) {
        isFirstAnalysis = false;
        moodBuffer.push(currentMood);
        callback(result);
        return;
    }

    moodBuffer.push(currentMood);
    if (moodBuffer.length > BUFFER_SIZE) moodBuffer.shift();

    const freq = {};
    moodBuffer.forEach(m => freq[m] = (freq[m] || 0) + 1);
    
    const dominantMood = Object.entries(freq).find(([_, v]) => v / moodBuffer.length >= 0.7);
    
    if (dominantMood || currentMood === "분석 불가") {
        callback(result);
    }
}

function playSFX(keyword) {
    const now = Date.now();
    if (now - (sfxCooldown.get(keyword) || 0) < 30000) return;
    sfxCooldown.set(keyword, now);
    console.log(`[SFX Play] ${keyword}`); 
}

export function onStyleChange(newStyle, text, callback) {
    moodBuffer.length = 0;
    sfxCooldown.clear();
    isFirstAnalysis = true;
    executeAnalysis(text, newStyle, callback);
}
