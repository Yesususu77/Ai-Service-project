import './MyWritings.css'

const SAMPLE_WRITINGS = [
  { id: 1, title: '붉은 실의 끝에서', chapter: '3장까지', date: '2025.05.01', genre: '오케스트라' },
  { id: 2, title: '안녕하세요', chapter: '1장까지', date: '2025.05.08', genre: '로파이 힐링' },
  { id: 3, title: '미완성 이야기', chapter: '2장까지', date: '2025.04.28', genre: '감성 피아노' },
]

export default function MyWritings({ onContinue, onNewWrite }) {
  return (
    <div className="writings-page">
      <div className="writings-header">
        <h1 className="writings-title">뮤즈 에디터</h1>
        <p className="writings-sub">이어서 쓸까요, 새로 시작할까요?</p>
      </div>

      <div className="writings-card">
        <div className="writings-section-title">이전에 쓰던 글</div>

        <div className="writings-list">
          {SAMPLE_WRITINGS.map(w => (
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
          ))}
        </div>

        <button className="writings-new-btn" onClick={onNewWrite}>
          + 새로 쓰기
        </button>
      </div>
    </div>
  )
}