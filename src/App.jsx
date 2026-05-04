import { useState, useRef } from 'react'
import './App.css'

const FONTS = [
  { name: '나눔명조', label: '나눔명조', family: "'Nanum Myeongjo', serif" },
  { name: '나눔고딕', label: '나눔고딕', family: "'Nanum Gothic', sans-serif" },
  { name: '본명조', label: '본명조', family: "'Noto Serif KR', serif" },
  { name: '본고딕', label: '본고딕', family: "'Noto Sans KR', sans-serif" },
  { name: 'Georgia', label: 'Georgia', family: "Georgia, serif" },
  { name: 'Playfair', label: 'Playfair Display', family: "'Playfair Display', serif" },
  { name: 'Lora', label: 'Lora', family: "'Lora', serif" },
  { name: 'Merriweather', label: 'Merriweather', family: "'Merriweather', serif" },
]

const TRACKS = [ ]

const MOOD_COLORS = {
  긴장: '#c0392b', 로맨틱: '#e84393', 평화: '#27ae60', 공포: '#8e44ad',
}

export default function App() {
  const [isDark, setIsDark] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [currentFont, setCurrentFont] = useState(FONTS[0])
  const [showFontMenu, setShowFontMenu] = useState(false)

  const [chapters, setChapters] = useState([{ id: 1, title: '1장' }])
  const [activeChapter, setActiveChapter] = useState(1)
  const [storyTitle, setStoryTitle] = useState('')
  const [editingTitle, setEditingTitle] = useState(false)
  const [chapterParagraphs, setChapterParagraphs] = useState({ 1: [{ id: 1, text: '' }] })

  const [currentTrack, setCurrentTrack] = useState(null)
  const [currentMood] = useState('긴장')
  const [bgm, setBgm] = useState(true)
  const [sfx, setSfx] = useState(true)
  const [all, setAll] = useState(true)
  const [bgmVol, setBgmVol] = useState(65)
  const [sfxVol, setSfxVol] = useState(50)
  const [allVol, setAllVol] = useState(75)

  const [checkResults, setCheckResults] = useState([])
  const [isChecking, setIsChecking] = useState(false)

  const paraRefs = useRef({})
  const paragraphs = chapterParagraphs[activeChapter] || [{ id: 1, text: '' }]

  const totalChars = paragraphs.reduce((acc, p) => acc + p.text.length, 0)

  const handleParaChange = (paraId, value) => {
    setChapterParagraphs(prev => ({
      ...prev,
      [activeChapter]: prev[activeChapter].map(p =>
        p.id === paraId ? { ...p, text: value } : p
      )
    }))
  }

  const handleParaKeyDown = (e, paraId) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      const newId = Date.now()
      setChapterParagraphs(prev => {
        const paras = prev[activeChapter]
        const idx = paras.findIndex(p => p.id === paraId)
        return {
          ...prev,
          [activeChapter]: [
            ...paras.slice(0, idx + 1),
            { id: newId, text: '' },
            ...paras.slice(idx + 1)
          ]
        }
      })
      setTimeout(() => paraRefs.current[newId]?.focus(), 50)
    }
    if (e.key === 'Backspace') {
      const paras = chapterParagraphs[activeChapter]
      const current = paras.find(p => p.id === paraId)
      if (current.text === '' && paras.length > 1) {
        e.preventDefault()
        const idx = paras.findIndex(p => p.id === paraId)
        const prevPara = paras[idx - 1]
        setChapterParagraphs(prev => ({
          ...prev,
          [activeChapter]: prev[activeChapter].filter(p => p.id !== paraId)
        }))
        if (prevPara) setTimeout(() => paraRefs.current[prevPara.id]?.focus(), 50)
      }
    }
  }

  const addChapter = () => {
    const newId = chapters.length + 1
    setChapters(prev => [...prev, { id: newId, title: `${newId}장` }])
    setChapterParagraphs(prev => ({ ...prev, [newId]: [{ id: Date.now(), text: '' }] }))
    setActiveChapter(newId)
  }

  const handleSpellCheck = async () => {
    const allText = paragraphs.map(p => p.text).join('\n')
    if (!allText.trim()) return alert('먼저 글을 작성해주세요!')
    setIsChecking(true)
    setCheckResults([])
    try {
      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          messages: [{
            role: 'user',
            content: `아래 소설 텍스트를 분석해서 JSON 배열로만 응답해줘. 다른 말은 절대 하지마.
분석 항목:
1. 맞춤법 오류 (section: "맞춤법", labelClass: "spelling", color: "#c06060")
2. 문맥 제안 (section: "문맥 제안", labelClass: "context", color: "#c28b82")
3. 설정 오류 (section: "설정 오류", labelClass: "setting", color: "#b8956a")
각 항목은 { section, labelClass, color, word, suggestion, location } 형태로.
결과가 없으면 빈 배열 [] 반환.
텍스트:
${allText}`
          }]
        })
      })
      const data = await response.json()
      const text = data.content?.[0]?.text || '[]'
      const clean = text.replace(/```json|```/g, '').trim()
      const parsed = JSON.parse(clean)
      setCheckResults(parsed)
    } catch (err) {
      alert('맞춤법 검사 중 오류가 발생했어요.')
    } finally {
      setIsChecking(false)
    }
  }

  const now = new Date()
  const timeStr = `오늘 오후 ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`

  return (
    <div className={`app ${isDark ? 'dark' : 'light'}`}>

      {/* 상단 바 */}
      <header className="topbar">
        <div className="topbar-left" style={{ opacity: isFullscreen ? 0 : 1, pointerEvents: isFullscreen ? 'none' : 'auto' }}>
          <span className="logo">뮤즈 에디터</span>
          <span className="beta-badge">beta</span>
        </div>
        <div className="topbar-center">
          {!isFullscreen && <>
            <span className="story-title-tab">서론</span>
            {chapters.map(ch => (
              <button
                key={ch.id}
                className={`chapter-tab ${activeChapter === ch.id ? 'active' : ''}`}
                onClick={() => setActiveChapter(ch.id)}
              >
                {ch.title}
              </button>
            ))}
            <button className="chapter-tab add-tab" onClick={addChapter}>+</button>
          </>}
        </div>
        <div className="topbar-right" style={{ opacity: isFullscreen ? 0 : 1, pointerEvents: isFullscreen ? 'none' : 'auto' }}>
          <button className={`theme-toggle ${isDark ? 'dark-on' : 'light-on'}`} onClick={() => setIsDark(!isDark)}>
            <span className="theme-toggle-knob" />
          </button>
          <button className="save-btn">저장</button>
        </div>
      </header>

      {/* 메인 3분할 */}
      <main className="main-layout">

        {/* 좌측 오디오 패널 */}
        {!isFullscreen && (
          <aside className="audio-panel">
            <div className="audio-section">
              <div className="section-label">오디오 컨트롤</div>
              {[
                { icon: '♪', name: 'BGM', val: bgm, set: setBgm, vol: bgmVol, setVol: setBgmVol },
                { icon: '⚡', name: 'SFX', val: sfx, set: setSfx, vol: sfxVol, setVol: setSfxVol },
                { icon: '◎', name: '전체', val: all, set: setAll, vol: allVol, setVol: setAllVol },
              ].map(ctrl => (
                <div className="control-row" key={ctrl.name}>
                  <span className="ctrl-icon">{ctrl.icon}</span>
                  <span className="ctrl-name">{ctrl.name}</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={ctrl.vol}
                    onChange={e => ctrl.setVol(Number(e.target.value))}
                    className="volume-slider"
                  />
                      <button className={`toggle ${ctrl.val ? 'on' : 'off'}`} onClick={() => ctrl.set(!ctrl.val)} />
                </div>
              ))}
            </div>
            <div className="audio-section track-section">
              <div className="section-label">추천 음악 목록 <span>▲</span></div>
              <div className="track-list">
                {TRACKS.map((track, i) => (
                  <div key={track.id} className={`track-item ${currentTrack.id === track.id ? 'active' : ''}`} onClick={() => setCurrentTrack(track)}>
                    <span className="track-num">{String(i + 1).padStart(2, '0')}</span>
                    <div className="track-info">
                      <div className="track-title">{track.title}</div>
                      <div className="track-meta">{track.duration} · {track.genre}</div>
                      <span className="mood-tag" style={{ background: MOOD_COLORS[track.mood] + '28', color: MOOD_COLORS[track.mood] }}>{track.mood}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        )}

        {/* 중앙 에디터 */}
        <div className="editor-panel">
          <div className="editor-topbar">
            <div className="mood-indicator">
              <span className="mood-dot" style={{ background: MOOD_COLORS[currentMood] }} />
              <span className="mood-label">현재 무드 : </span>
              <span className="mood-value" style={{ color: MOOD_COLORS[currentMood] }}>{currentMood}</span>
              <span className="mood-sublabel"> · 2문단 연속 긴장</span>
            </div>
            <div className="editor-toolbar">
              <button className="tool-btn" onClick={handleSpellCheck} disabled={isChecking}>
                {isChecking ? '검사 중...' : '맞춤법 검사'}
              </button>

              {/* 글꼴 드롭다운 */}
              <div className="font-selector">
                <button className="tool-btn font-btn" onClick={() => setShowFontMenu(!showFontMenu)}>
                  <span style={{ fontFamily: currentFont.family }}>가</span>
                  &nbsp;{currentFont.name} ▾
                </button>
                {showFontMenu && (
                  <div className="font-dropdown">
                    {FONTS.map(font => (
                      <button
                        key={font.name}
                        className={`font-option ${currentFont.name === font.name ? 'active' : ''}`}
                        style={{ fontFamily: font.family }}
                        onClick={() => { setCurrentFont(font); setShowFontMenu(false) }}
                      >
                        {font.label}
                        <span className="font-preview">가나다 Abc</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button className="tool-btn fullscreen-btn" onClick={() => setIsFullscreen(!isFullscreen)}>
                {isFullscreen ? '↙ 나가기' : '↗ 전체화면'}
              </button>
            </div>
          </div>

          <div className="editor-scroll">
            <div className="editor-content" style={{ fontFamily: currentFont.family }}>

              {editingTitle ? (
                <input
                  className="title-input"
                  value={storyTitle}
                  onChange={e => setStoryTitle(e.target.value)}
                  onBlur={() => setEditingTitle(false)}
                  onKeyDown={e => e.key === 'Enter' && setEditingTitle(false)}
                  placeholder="제목을 입력하세요"
                  autoFocus
                />
              ) : (
                <h1
                  className={`story-heading ${!storyTitle ? 'placeholder' : ''}`}
                  onClick={() => setEditingTitle(true)}
                >
                  {storyTitle || '제목을 입력하세요'}
                </h1>
              )}

              <div className="story-meta">
                {chapters.find(c => c.id === activeChapter)?.title} · 자동 저장됨 · {timeStr}
              </div>

              {paragraphs.map((para, idx) => (
                <div key={para.id} className="para-block">
                  <div className="para-label">문단 {idx + 1}</div>
                  <textarea
                    ref={el => paraRefs.current[para.id] = el}
                    className="para-textarea"
                    value={para.text}
                    onChange={e => handleParaChange(para.id, e.target.value)}
                    onKeyDown={e => handleParaKeyDown(e, para.id)}
                    placeholder={idx === 0 ? '첫 문장을 써보세요... (엔터로 문단 추가)' : '계속 쓰세요...'}
                    rows={1}
                    style={{ fontFamily: currentFont.family }}
                  />
                  {idx === 0 && para.text.length > 0 && currentTrack && (
                    <div className="para-track">
                      <span className="track-note">♪</span>
                      <span className="track-name">선정된 음악 : {currentTrack.title}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 우측 사이드바 */}
        {!isFullscreen && (
          <aside className="sidebar-panel">
            <div className="sidebar-topbar">
              <span className="sidebar-title">맞춤법 · 문맥</span>
              <span className="sidebar-arrow">▲</span>
            </div>
            <div className="sidebar-scroll">
              {isChecking && <div className="checking-msg">🔍 분석 중...</div>}
              {!isChecking && checkResults.length === 0 && (
                <div className="checking-msg">맞춤법 검사 버튼을 눌러주세요</div>
              )}
              {checkResults.map((item, i) => (
                <CheckCard key={i} item={item} />
              ))}
              <div className="check-section">
                <div className="sidebar-sub-title">장르 · 설정</div>
                <div className="genre-grid">
                  {[['장르', '스릴러'], ['배경', '현대 도시'], ['시점', '3인칭'], ['무드 전환', '3문단 후']].map(([k, v]) => (
                    <div className="genre-row" key={k}>
                      <span className="genre-key">{k}</span>
                      <span className="genre-val">{v}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </aside>
        )}

      </main>

      <footer className="statusbar">
        <span>▶ 재생 중 · {paragraphs.length}문단</span>
        <span className="char-count">공백 포함 {totalChars.toLocaleString()}자</span>
      </footer>

    </div>
  )
}

function CheckCard({ item }) {
  const [dismissed, setDismissed] = useState(false)
  if (dismissed) return null
  return (
    <div className="check-section">
      <div className={`check-section-label ${item.labelClass}`}>{item.section}</div>
      <div className="check-card" style={{ borderLeftColor: item.color }}>
        <div className="check-word" style={{ color: item.color }}>{item.word}</div>
        <div className="check-arrow">→ {item.suggestion}</div>
        <div className="check-location">{item.location}</div>
        <div className="check-actions">
          <button className="check-btn accept">적용</button>
          <button className="check-btn dismiss" onClick={() => setDismissed(true)}>무시</button>
        </div>
      </div>
    </div>
  )
}