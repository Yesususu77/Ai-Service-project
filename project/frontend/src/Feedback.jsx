import { useState } from 'react'
import './Feedback.css'

const PURPOSES = ['작가', '취미', '학생', '직장인', '기타']
const AGE_GROUPS = ['10대', '20대', '30대', '40대', '50대 이상']

export default function Feedback({ onDone }) {
  const BE_URL = 'https://backend-service-egef.onrender.com'
  const [rating, setRating] = useState(0)
  const [hoverRating, setHoverRating] = useState(0)
  const [age, setAge] = useState('')
  const [purpose, setPurpose] = useState('')
  const [satisfactions, setSatisfactions] = useState([])
  const [improvements, setImprovements] = useState('')
  const [recommend, setRecommend] = useState(null)
  const [submitted, setSubmitted] = useState(false)

  const handleSubmit = async () => {        
    if (rating === 0) return
    try {
      await fetch(`${BE_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating,
          age,
          purpose,
          satisfactions: satisfactions.join(', '),
          improvements,
          recommend
        })
      })
    } catch (e) {
      console.error('피드백 저장 실패', e)
    }
    setSubmitted(true)
  }                                          

  const SATISFACTION_OPTIONS = [
    'BGM 추천이 글과 잘 맞았어요',
    '집필에 집중할 수 있었어요',
    '인터페이스가 직관적이에요',
    '글꼴/테마 커스텀이 좋았어요',
    '맞춤법 검사가 유용했어요',
  ]

  const toggleSatisfaction = (item) => {
    setSatisfactions(prev =>
      prev.includes(item) ? prev.filter(s => s !== item) : [...prev, item]
    )
  }

  if (submitted) {
    return (
      <div className="feedback-page">
        <div className="feedback-done">
          <div className="feedback-done-icon">🩷</div>
          <h2>소중한 피드백 감사해요!</h2>
          <p>여러분의 의견이 뮤즈 에디터를 더 좋게 만들어요</p>
          <button className="feedback-submit-btn" onClick={onDone}>
            에디터로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="feedback-page">
      <div className="feedback-header">
        <h1 className="feedback-title">서비스 피드백</h1>
        <p className="feedback-sub">뮤즈 에디터를 사용해보셨나요? 솔직한 의견을 들려주세요 🩷</p>
      </div>

      <div className="feedback-card">

        {/* 별점 */}
        <div className="feedback-section">
          <div className="feedback-label">전체 만족도</div>
          <div className="star-row">
            {[1,2,3,4,5].map(star => (
              <span
                key={star}
                className={`star ${star <= (hoverRating || rating) ? 'active' : ''}`}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHoverRating(star)}
                onMouseLeave={() => setHoverRating(0)}
              >★</span>
            ))}
            <span className="star-label">
              {rating === 1 ? '별로예요' : rating === 2 ? '아쉬워요' : rating === 3 ? '보통이에요' : rating === 4 ? '좋아요' : rating === 5 ? '최고예요!' : ''}
            </span>
          </div>
        </div>

        {/* 나이대 */}
        <div className="feedback-section">
          <div className="feedback-label">나이대</div>
          <div className="chip-row">
            {AGE_GROUPS.map(a => (
              <button
                key={a}
                className={`chip ${age === a ? 'active' : ''}`}
                onClick={() => setAge(a)}
              >{a}</button>
            ))}
          </div>
        </div>

        {/* 글쓰기 목적 */}
        <div className="feedback-section">
          <div className="feedback-label">글쓰기 목적</div>
          <div className="chip-row">
            {PURPOSES.map(p => (
              <button
                key={p}
                className={`chip ${purpose === p ? 'active' : ''}`}
                onClick={() => setPurpose(p)}
              >{p}</button>
            ))}
          </div>
        </div>

        {/* 만족한 점 */}
        <div className="feedback-section">
          <div className="feedback-label">만족한 점 (복수 선택 가능)</div>
          <div className="chip-row">
            {SATISFACTION_OPTIONS.map(s => (
              <button
                key={s}
                className={`chip ${satisfactions.includes(s) ? 'active' : ''}`}
                onClick={() => toggleSatisfaction(s)}
              >{s}</button>
            ))}
          </div>
        </div>

        {/* 추천 의향 */}
        <div className="feedback-section">
          <div className="feedback-label">주변에 추천하고 싶으신가요?</div>
          <div className="chip-row">
            {['네, 추천할게요!', '글쎄요', '아니요'].map(r => (
              <button
                key={r}
                className={`chip ${recommend === r ? 'active' : ''}`}
                onClick={() => setRecommend(r)}
              >{r}</button>
            ))}
          </div>
        </div>

        {/* 자유 의견 */}
        <div className="feedback-section">
          <div className="feedback-label">개선되었으면 하는 점 / 자유 의견</div>
          <textarea
            className="feedback-textarea"
            placeholder="불편했던 점, 추가됐으면 하는 기능, 전반적인 소감 등 자유롭게 적어주세요"
            value={improvements}
            onChange={e => setImprovements(e.target.value)}
            rows={4}
          />
        </div>

        <button
          className="feedback-submit-btn"
          onClick={handleSubmit}
          disabled={rating === 0}
          style={{ opacity: rating === 0 ? 0.5 : 1 }}
        >
          피드백 제출하기
        </button>
        {rating === 0 && <p className="feedback-hint">별점을 선택해주세요!</p>}
      </div>
    </div>
  )
}
