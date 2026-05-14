import { useState, useRef } from 'react'
import './App.css'
import Login from './Login'
import GenreSelect from './GenreSelect'
import MyWritings from './MyWritings'
import Feedback from './Feedback'

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

const MOOD_COLORS = {
  긴장: '#c0392b', 로맨틱: '#e84393', 평화: '#27ae60', 공포: '#8e44ad',
}

const BE_URL = 'https://backend-service-egef.onrender.com'

export default function App() {
  const savedData = (() => {
  const currentId = localStorage.getItem('muse_current')
  if (!currentId) return null
  const list = JSON.parse(localStorage.getItem('muse_writings') || '[]')
  return list.find(w => w.id === currentId) || null
  })()

  const [currentWritingId, setCurrentWritingId] = useState(savedData?.id || null)
  const [storyTitle, setStoryTitle] = useState(savedData?.storyTitle || '')
  const [chapters, setChapters] = useState(savedData?.chapters || [{ id: 1, title: '1장' }])
  const [chapterParagraphs, setChapterParagraphs] = useState(savedData?.chapterParagraphs || { 1: [{ id: 1, text: '' }] })
  const [activeChapter, setActiveChapter] = useState(1)
  const [editingTitle, setEditingTitle] = useState(false)
  
  const [page, setPage] = useState('login')
  const [selectedGenre, setSelectedGenre] = useState(savedData?.selectedGenre || null)
  const [isDark, setIsDark] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [currentFont, setCurrentFont] = useState(FONTS[0])
  const [showFontMenu, setShowFontMenu] = useState(false)

  const [storyTitle, setStoryTitle] = useState(savedData?.storyTitle || '')
  const [chapters, setChapters] = useState(savedData?.chapters || [{ id: 1, title: '1장' }])
  const [chapterParagraphs, setChapterParagraphs] = useState(savedData?.chapterParagraphs || { 1: [{ id: 1, text: '' }] })
  const [activeChapter, setActiveChapter] = useState(1)       
  const [editingTitle, setEditingTitle] = useState(false)     

  const [currentTrack, setCurrentTrack] = useState(null)
  const [currentMood, setCurrentMood] = useState('평화')
  const [bgm, setBgm] = useState(true)
  const [sfx, setSfx] = useState(true)
  const [all, setAll] = useState(true)
  const [bgmVol, setBgmVol] = useState(65)
  const [sfxVol, setSfxVol] = useState(50)
  const [allVol, setAllVol] = useState(75)
  const [isPlaying, setIsPlaying] = useState(false)

  const [checkResults, setCheckResults] = useState([])
  const [isChecking, setIsChecking] = useState(false)
  const [saveStatus, setSaveStatus] = useState('')

  const paraRefs = useRef({})
  const audioRef = useRef(null)
  const [currentBgmUrl, setCurrentBgmUrl] = useState(null)
  const [currentBgmTitle, setCurrentBgmTitle] = useState('')
  const [bgmHistory, setBgmHistory] = useState([])
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
      
      const currentPara = paragraphs.find(p => p.id === paraId)
      if (currentPara?.text.trim()) analyzeMood(currentPara.text)
      
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
      const response = await fetch(`${BE_URL}/api/analyze/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: allText,
          style: 'dramatic',
          user_id: 'guest',
          prev_text: ''
        })
      })
      const data = await response.json()

      // mood 업데이트
      if (data.mood && data.mood.length > 0) {
        setCurrentMood(data.mood[0])
      }

      const results = (data.errors || []).map(e => ({
        section: e.type === 'spell' ? '맞춤법' : '문법',
        labelClass: e.type === 'spell' ? 'spelling' : 'context',
        color: e.type === 'spell' ? '#c06060' : '#c28b82',
        word: e.original,
        suggestion: e.fix,
        location: '본문'
      }))
      setCheckResults(results)
    } catch (err) {
      alert('분석 중 오류가 발생했어요.')
    } finally {
      setIsChecking(false)
    }
  }

  const analyzeMood = async (text) => {
  if (!text.trim()) return
  try {
    const response = await fetch(`${BE_URL}/api/analyze/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: text,
        style: 'dramatic',
        user_id: 'guest',
        prev_text: ''
      })
    })
    const data = await response.json()

    if (data.mood && data.mood.length > 0) {
      setCurrentMood(data.mood[0])
    }

    if (data.bgm && data.bgm.url) {
      setCurrentBgmUrl(data.bgm.url)
      setCurrentBgmTitle(data.bgm.Title || '')
      console.log('BGM Title:', data.bgm.Title)
      setBgmHistory(prev => {
        // 중복 제거 후 앞에 추가 (최대 10개)
        const filtered = prev.filter(t => t !== (data.bgm.Title || ''))
        return [data.bgm.Title || '', ...filtered].slice(0, 10)
      })
      if (audioRef.current) {
        audioRef.current.src = data.bgm.url
        audioRef.current.volume = bgmVol / 100
        audioRef.current.play().catch(e => console.log('재생 실패:', e))
        setIsPlaying(true)
  }
}
  } catch (err) {
    console.error('무드 분석 실패', err)
  }
}

  // 적용 버튼: 본문에서 original → fix로 교체
  const handleApply = (word, suggestion) => {
    setChapterParagraphs(prev => ({
      ...prev,
      [activeChapter]: prev[activeChapter].map(p => ({
        ...p,
        text: p.text.replaceAll(word, suggestion)
      }))
    }))
  }

  // 저장 버튼
  const handleSave = () => {
  try {
    const list = JSON.parse(localStorage.getItem('muse_writings') || '[]')
    const id = currentWritingId || Date.now().toString()
    const saveData = {
      id,
      storyTitle,
      chapters,
      chapterParagraphs,
      selectedGenre,
      savedAt: new Date().toLocaleString('ko-KR')
    }
    const idx = list.findIndex(w => w.id === id)
    if (idx >= 0) list[idx] = saveData
    else list.push(saveData)
    localStorage.setItem('muse_writings', JSON.stringify(list))
    localStorage.setItem('muse_current', id)
    setCurrentWritingId(id)
    setSaveStatus('저장됨 ✓')
    setTimeout(() => setSaveStatus(''), 2000)
  } catch {
    setSaveStatus('저장 실패')
  }
}

  const now = new Date()
  const timeStr = `오늘 오후 ${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`

  if (page === 'login') return <Login onLogin={() => setPage('writings')} />
  if (page === 'writings') return (
  <MyWritings
    onContinue={(w) => {
      setCurrentWritingId(w.id)
      setStoryTitle(w.storyTitle || '')
      setChapters(w.chapters || [{ id: 1, title: '1장' }])
      setChapterParagraphs(w.chapterParagraphs || { 1: [{ id: 1, text: '' }] })
      setSelectedGenre(w.selectedGenre || null)
      setActiveChapter(1)
      localStorage.setItem('muse_current', w.id)
      setPage('editor')
    }}
    onNewWrite={() => {
      setCurrentWritingId(null)
      setStoryTitle('')
      setChapters([{ id: 1, title: '1장' }])
      setChapterParagraphs({ 1: [{ id: 1, text: '' }] })
      setSelectedGenre(null)
      setActiveChapter(1)
      localStorage.removeItem('muse_current')
      setPage('genre')
    }}
  />
)
  if (page === 'genre') return (
    <GenreSelect onStart={(genre) => {
      setSelectedGenre(genre)
      setPage('editor')
    }} />
  )
  if (page === 'feedback') return <Feedback onDone={() => setPage('editor')} />

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
          <button className="save-btn" onClick={handleSave}>
            {saveStatus || '저장'}
          </button>
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
                    onChange={e => {
                      ctrl.setVol(Number(e.target.value))
                      if (ctrl.name === 'BGM' && audioRef.current) {
                        audioRef.current.volume = Number(e.target.value) / 100
                      }
                      if (ctrl.name === '전체' && audioRef.current) {
                        audioRef.current.volume = Number(e.target.value) / 100
                      }
                    }}
                    className="volume-slider"
                  />
                  <button
                    className={`toggle ${ctrl.val ? 'on' : 'off'}`}
                    onClick={() => {
                      ctrl.set(!ctrl.val)
                      if (ctrl.name === 'BGM' && audioRef.current) {
                        audioRef.current.muted = ctrl.val  // 현재값 반전
                      }
                      if (ctrl.name === '전체' && audioRef.current) {  
                        audioRef.current.muted = ctrl.val
                      }
                    }}
                  />
              </div>
            ))}
            </div>
            <div className="audio-section track-section">
              <div className="section-label">추천 음악 목록 <span>▲</span></div>
              <div className="track-list">
                {bgmHistory.length > 0 ? (
                  bgmHistory.map((title, i) => (
                    <div key={i} className={`track-item ${i === 0 ? 'active' : ''}`}>
                      <span className="track-num">{String(i + 1).padStart(2, '0')}</span>
                      <div className="track-info">
                        <div className="track-title">{title}</div>
                        <div className="track-meta">{i === 0 ? '재생 중' : '이전 재생'}</div>
                      </div>
                      {i === 0 && (
                        <button
                          className="tool-btn"
                          style={{ fontSize: '12px', padding: '4px 8px' }}
                          onClick={() => {
                            if (!audioRef.current) return
                            if (isPlaying) {
                              audioRef.current.pause()
                              setIsPlaying(false)
                            } else {
                              audioRef.current.play()
                              setIsPlaying(true)
                            }
                          }}
                        >
                          {isPlaying ? '⏸' : '▶'}
                        </button>
                      )}
                    </div>
                  ))
                  ) : (
                    <div className="checking-msg">음악 데이터 준비 중</div>
                  )}
              </div>
            </div>
          </aside>
        )}

        {/* 중앙 에디터 */}
        <div className="editor-panel">
          <div className="editor-topbar">
            <div className="mood-indicator">
              <span className="mood-dot" style={{ background: MOOD_COLORS[currentMood] || '#888' }} />
              <span className="mood-label">현재 무드 : </span>
              <span className="mood-value" style={{ color: MOOD_COLORS[currentMood] || '#888' }}>{currentMood}</span>
            </div>
            <div className="editor-toolbar">
              <button className="tool-btn" onClick={handleSpellCheck} disabled={isChecking}>
                {isChecking ? '검사 중...' : '맞춤법 검사'}
              </button>

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
                {chapters.find(c => c.id === activeChapter)?.title} · {saveStatus || '자동 저장됨'} · {timeStr}
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
                <CheckCard key={i} item={item} onApply={handleApply} />
              ))}
              <div className="check-section">
                <div className="sidebar-sub-title">음악 장르</div>
                <div className="genre-grid">
                  {selectedGenre ? (
                    <div className="genre-row">
                      <span className="genre-key">선택 장르</span>
                      <span className="genre-val">{selectedGenre}</span>
                    </div>
                  ) : (
                    <div className="genre-row">
                      <span className="genre-key">장르 미선택</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="sidebar-bottom">
              <div className="sidebar-bottom-row">
                <button className="sidebar-sm-btn" onClick={handleSave}>저장</button>
                <button className="sidebar-sm-btn" onClick={() => setPage('writings')}>글 목록</button>
              </div>
              <button className="sidebar-theme-btn" onClick={() => setPage('feedback')}>
                테마곡 생성 / 피드백
              </button>
            </div>
          </aside>
        )}

      </main>

      <footer className="statusbar">
        <span>▶ 재생 중 · {paragraphs.length}문단</span>
        <span className="char-count">공백 포함 {totalChars.toLocaleString()}자</span>
      </footer>

      {/* BGM 오디오 */}
      <audio ref={audioRef} loop />

    </div>
  )
}

function CheckCard({ item, onApply }) {
  const [dismissed, setDismissed] = useState(false)
  const [applied, setApplied] = useState(false)
  if (dismissed) return null
  return (
    <div className="check-section">
      <div className={`check-section-label ${item.labelClass}`}>{item.section}</div>
      <div className="check-card" style={{ borderLeftColor: item.color }}>
        <div className="check-word" style={{ color: item.color }}>{item.word}</div>
        <div className="check-arrow">→ {item.suggestion}</div>
        <div className="check-location">{item.location}</div>
        <div className="check-actions">
          <button
            className="check-btn accept"
            onClick={() => { onApply(item.word, item.suggestion); setApplied(true) }}
            disabled={applied}
          >
            {applied ? '적용됨 ✓' : '적용'}
          </button>
          <button className="check-btn dismiss" onClick={() => setDismissed(true)}>무시</button>
        </div>
      </div>
    </div>
  )
}
