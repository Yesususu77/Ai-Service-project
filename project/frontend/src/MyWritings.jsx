import { useState, useEffect } from 'react'
import './MyWritings.css'

export default function MyWritings({ onContinue, onNewWrite }) {
  const [writings, setWritings] = useState([])

  useEffect(() => {
    const saved = JSON.parse(localStorage.getItem('muse_save') || 'null')
    if (saved) {
      setWritings([{
        id: 1,
        title: saved.storyTitle || '제목 없음',
        chapter: `${saved.chapters?.length || 1}장까지`,
        date: saved.savedAt || '',
        genre: saved.selectedGenre || '장르 미선택'
      }])
    }
  }, [])

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
