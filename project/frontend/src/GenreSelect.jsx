import { useState } from 'react'
import './GenreSelect.css'

const GENRES = [
  { id: 1, icon: '🏯', name: '동양풍', desc: '피리 · 가야금 · 타악\n무협 · 사극 · 동양 판타지' },
  { id: 2, icon: '🏰', name: '오케스트라', desc: '현악 · 관악 · 합창\n서양 판타지 · 로판' },
  { id: 3, icon: '🎹', name: '감성 피아노', desc: '피아노 · 어쿠스틱\n현대 로맨스 · 일상' },
  { id: 4, icon: '🌑', name: '다크 앰비언트', desc: '긴장 · 불협화음\n스릴러 · 공포' },
  { id: 5, icon: '☕', name: '로파이 힐링', desc: '로파이 · 잔잔한 어쿠스틱\n일상 · 치유' },
  { id: 6, icon: '🎭', name: '코믹', desc: '경쾌 · 유머러스\n개그 · 일상 코미디' },
]

export default function GenreSelect({ onStart }) {
  const [selected, setSelected] = useState(2)

  return (
    <div className="genre-page">
      <div className="genre-header">
        <h1 className="genre-title">어떤 음악과 함께 쓸까요?</h1>
        <p className="genre-sub">글의 분위기에 어울리는 음악 스타일을 선택해주세요</p>
        <p className="genre-sub">언제든지 변경할 수 있어요</p>
      </div>

      <div className="genre-grid">
        {/* 첫 번째 줄 3개 */}
        <div className="genre-row">
          {GENRES.slice(0, 3).map(genre => (
            <div
              key={genre.id}
              className={`genre-card ${selected === genre.id ? 'active' : ''}`}
              onClick={() => setSelected(genre.id)}
            >
              {selected === genre.id && <span className="genre-check">✓</span>}
              <span className="genre-icon">{genre.icon}</span>
              <span className="genre-name">{genre.name}</span>
              <span className="genre-desc">
                {genre.desc.split('\n').map((line, i) => (
                  <span key={i}>{line}<br /></span>
                ))}
              </span>
            </div>
          ))}
        </div>

        {/* 두 번째 줄 2개 (가운데 정렬) */}
        <div className="genre-row">
          {GENRES.slice(3, 6).map(genre => (
            <div
              key={genre.id}
              className={`genre-card ${selected === genre.id ? 'active' : ''}`}
              onClick={() => setSelected(genre.id)}
            >
              {selected === genre.id && <span className="genre-check">✓</span>}
              <span className="genre-icon">{genre.icon}</span>
              <span className="genre-name">{genre.name}</span>
              <span className="genre-desc">
                {genre.desc.split('\n').map((line, i) => (
                  <span key={i}>{line}<br /></span>
                ))}
              </span>
            </div>
          ))}
        </div>
      </div>

      <button className="genre-start-btn" onClick={onStart}>
        집필 시작하기 →
      </button>
    </div>
  )
}