/**
 * 🎵 EditMuse! Core Analysis Engine
 * Architecture & Algorithm Design by suin-ai
 * 
 * 주요 기능: 실시간 텍스트 분석, 감정 안정화 버퍼, 
 *          레이스 컨디션 방지, 스타일별 SFX 필터링
 */

// --- 1. 설정 및 상수 데이터 (Configuration) ---
const VALID_MOODS = ["긴장", "로맨틱", "슬픔", "액션", "평화", "신비", "공포", "희망", "분노", "코믹"];

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
 * AI 시스템 프롬프트 동적 생성
 */
function buildSystemPrompt(style) {
    const STYLE_GUIDE = {
        oriental: "- Music style: East Asian traditional (피리, 가야금, 타악, 대금)\n- Typical sounds: 칼소리, 검기, 화살소리, 북소리, 함성, 말발굽, 풍경소리, 종소리, 봉황울음, 폭포소리",
        orchestral: "- Music style: Western classical / orchestral\n- Typical sounds: 금속충돌, 방패소리, 마법이펙트, 폭발, 성문소리, 횃불소리, 드래곤울음, 교회종소리",
        piano: "- Music style: Emotional piano / acoustic\n- Typical sounds: 카페소음, 핸드폰진동, 키보드소리, 자동차소리, 와인잔소리, 엘리베이터소리",
        dark: "- Music style: Dark ambient / tension\n- Typical sounds: 심장소리, 숨소리, 삐걱소리, 유리깨지는소리, 총성, 비명, 사이렌",
        lofi: "- Music style: Lofi / healing\n- Typical sounds: 식기소리, 요리소리, 고양이소리, 강아지소리, 시냇물소리, 커피내리는소리",
    };

    const guide = STYLE_GUIDE[style] || STYLE_GUIDE["piano"];
    const COMMON_SFX = VALID_SFX.common.join(", ");

    return `You are a literary mood analyzer for a Korean writing editor.
## MUSIC STYLE CONTEXT
${guide}
- Common sounds: ${COMMON_SFX}
## TASK: Analyze passage and return valid JSON only.
## MOOD VALUES (STRICT): 긴장, 로맨틱, 슬픔, 액션, 평화, 신비, 공포, 희망, 분노, 코믹
## RULES: Map invalid moods like 'lonely' to '슬픔'. Energy 1-5. Max 3 SFX. No negations.`;
}

/**
 * [API 호출] GPT-4o-mini를 통한 텍스트 분석
 */
async function analyzePassage(text, style = "piano", retries = 2) {
    const requestId = ++currentRequestId;
    
    for (let attempt = 0; attempt <= retries; attempt++) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);

        try {
            const response = await fetch("https://api.openai.com/v1/chat/completions", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${process.env.OPENAI_KEY}`
                },
                body: JSON.stringify({
                    model: "gpt-4o-mini",
                    temperature: 0.2,
                    max_tokens: 250,
                    response_format: { type: "json_object" },
                    messages: [
                        { role: "system", content: buildSystemPrompt(style) },
                        { role: "user", content: `[PASSAGE]\n${text.slice(-500)}` }
                    ]
                }),
                signal: controller.signal
            });

            clearTimeout(timeout);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            const content = data?.choices?.[0]?.message?.content;
            if (!content) throw new Error("Empty response");

            const result = validateResult(JSON.parse(content), style);

            // 레이스 컨디션 체크: 가장 최신 요청만 반영
            if (requestId !== currentRequestId) return null;

            lastValidResult = result;
            return result;

        } catch (err) {
            clearTimeout(timeout);
            if (attempt === retries) {
                console.error("Analysis failed:", err);
                return requestId === currentRequestId ? lastValidResult : null;
            }
            // 점진적 재시도 대기 (500ms, 1000ms)
            await new Promise(r => setTimeout(r, 500 * (attempt + 1)));
        }
    }
}

/**
 * 응답 데이터 검증 및 필터링 (Strict Rules 적용)
 */
function validateResult(result, style = "piano") {
    // 1. 감정 검증
    result.mood = (result.mood || []).filter(m => VALID_MOODS.includes(m));
    if (result.mood.length === 0) result.mood = ["평화"];

    // 2. 에너지 보정 (1~5)
    result.energy = Math.min(5, Math.max(1, Math.round(result.energy || 3)));

    // 3. SFX 교차 검증
    const allowed = [...VALID_SFX.common, ...(VALID_SFX[style] || [])];
    result.sfx = (result.sfx || []).filter(s => allowed.includes(s)).slice(0, 3);

    // 4. 에러 객체 보장
    result.errors = result.errors || [];
    
    return result;
}

/**
 * [입력 트리거] 사용자 타이핑 감지 및 분석 실행 제어
 */
export function onTextChange(text, style, callback) {
    const endsWithSentence = /[.!?…\n]$/.test(text.trim());
    const charDiff = Math.abs(text.length - lastAnalyzedLength);

    // 조건 1: 문장이 끝났을 때 (1초 쿨다운)
    if (endsWithSentence && !cooldownTimer) {
        cooldownTimer = setTimeout(() => {
            executeAnalysis(text, style, callback);
            cooldownTimer = null;
        }, 1000);
        return;
    }

    // 조건 2: 100자 이상 변화 시 (1.5초 디바운스)
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
 * [후처리] 감정 안정화 및 BGM/SFX 연동
 */
function postProcess(result, callback) {
    // 1. 효과음 재생
    result.sfx.forEach(playSFX);

    // 2. BGM 전환 로직 (Warm-up & Buffer)
    const currentMood = result.mood[0];
    
    if (isFirstAnalysis) {
        isFirstAnalysis = false;
        moodBuffer.push(currentMood);
        callback(result); // 즉시 반영
        return;
    }

    moodBuffer.push(currentMood);
    if (moodBuffer.length > BUFFER_SIZE) moodBuffer.shift();

    // 버퍼 내 동일 감정 70% 이상 시 전환 (3개 중 3개 또는 2개 일치)
    const freq = {};
    moodBuffer.forEach(m => freq[m] = (freq[m] || 0) + 1);
    
    const dominantMood = Object.entries(freq).find(([_, v]) => v / moodBuffer.length >= 0.7);
    
    if (dominantMood) {
        callback(result);
    }
}

/**
 * 효과음 중복 재생 방지 (30초 쿨다운)
 */
function playSFX(keyword) {
    const now = Date.now();
    if (now - (sfxCooldown.get(keyword) || 0) < 30000) return;
    
    sfxCooldown.set(keyword, now);
    console.log(`[SFX Play] ${keyword}`); 
    // 실제 재생은 프론트엔드 Web Audio API에서 처리
}

/**
 * 스타일 변경 시 시스템 리셋
 */
export function onStyleChange(newStyle, text, callback) {
    moodBuffer.length = 0;
    sfxCooldown.clear();
    clearTimeout(cooldownTimer);
    clearTimeout(debounceTimer);
    cooldownTimer = null;
    debounceTimer = null;
    lastAnalyzedLength = 0;
    lastValidResult = null;
    currentRequestId = 0;
    isFirstAnalysis = true;

    executeAnalysis(text, newStyle, callback);
}
