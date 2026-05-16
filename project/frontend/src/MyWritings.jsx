import { useState, useEffect } from 'react'
import './MyWritings.css'

export default function MyWritings({ onContinue, onNewWrite, username, BE_URL }) {
  const [writings, setWritings] = useState([])

  useEffect(() => {
  // 1. localStorage 먼저 표시
  const list = JSON.parse(localStorage.getItem('muse_writings') || '[]')
  setWritings(list.map(w => ({
    id: w.id,
    title: w.storyTitle || '제목 없음',
    chapter: `${w.chapters?.length || 1}장까지`,
    date: w.savedAt || '',
    genre: w.selectedGenre || '장르 미선택',
    storyTitle: w.storyTitle,
    chapters: w.chapters,
    chapterParagraphs: w.chapterParagraphs,
    selectedGenre: w.selectedGenre,
  })))

  // 2. DB에서 불러오기 (localStorage보다 오래된 경우 무시)
  if (!username) return
  fetch(`${BE_URL}/api/writings/${username}`)
    .then(r => r.json())
    .then(data => {
      if (data && data.length > 0) {
        const localList = JSON.parse(localStorage.getItem('muse_writings') || '[]')
        
        const merged = data.map(dbItem => {
  const localItem = localList.find(l => l.id === dbItem.id)

  if (localItem && localItem.savedAt) {
    // DB 시간을 Date로 변환
    const dbTime = new Date(dbItem.saved_at).getTime()
    // localStorage 시간을 Date로 변환 (한국어 형식 처리)
    const localTime = new Date(localItem.savedAt).getTime()

    console.log('dbTime:', dbTime, 'localTime:', localTime)  // 확인용

    // localTime이 유효하고 DB보다 최신이면 로컬 사용
    if (!isNaN(localTime) && localTime > dbTime) {
      console.log('로컬 사용:', localItem.savedAt)
      return localItem
    }
  }

  // DB 사용
  return {
    id: dbItem.id,
    storyTitle: dbItem.story_title,
    chapters: dbItem.chapters,
    chapterParagraphs: dbItem.chapter_paragraphs,
    selectedGenre: dbItem.selected_genre,
    savedAt: dbItem.saved_at
  }
})

        // localStorage에 없는 DB 항목 추가
        localList.forEach(l => {
          if (!merged.find(m => m.id === l.id)) merged.push(l)
        })

        setWritings(merged.map(w => ({
          id: w.id,
          title: w.storyTitle || '제목 없음',
          chapter: `${w.chapters?.length || 1}장까지`,
          date: w.savedAt || '',
          genre: w.selectedGenre || '장르 미선택',
          storyTitle: w.storyTitle,
          chapters: w.chapters,
          chapterParagraphs: w.chapterParagraphs,
          selectedGenre: w.selectedGenre,
        })))
      }
    })
    .catch(() => {})
}, [username])

  return (
    <div className="writings-page">
      <div className="writings-header">
        <h1 className="writings-title">뮤즈 에디터</h1>
        <p className="writings-sub">이어서 쓸까요, 새로 시작할까요?</p>
      </div>
      <div className="writings-card">
        <div className="writings-section-title">이전에 쓰던 글</div>
        <div className="writings-list">
          {writings.length === 0 ? (
            <div className="writing-empty">저장된 글이 없어요</div>
          ) : (
            writings.map(w => (
              <div key={w.id} className="writing-item">
                <div className="writing-info">
                  <div className="writing-name">{w.title}</div>
                  <div className="writing-meta">{w.chapter} · {w.date} · {w.genre}</div>
                </div>
                <button
                  className="writing-continue-btn"
                  onClick={() => onContinue(w)}
                >
                  이어쓰기
                </button>
              </div>
            ))
          )}
        </div>
        <button className="writings-new-btn" onClick={onNewWrite}>
          + 새로 쓰기
        </button>
      </div>
    </div>
  )
}
