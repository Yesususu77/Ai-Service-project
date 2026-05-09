import { useState } from 'react'
import './Login.css'

export default function Login({ onLogin }) {
  const [tab, setTab] = useState('login')
  const [id, setId] = useState('')
  const [pw, setPw] = useState('')
  const [nickname, setNickname] = useState('')
  const [agreed, setAgreed] = useState(false)

  const BE_URL = 'https://backend-service-egef.onrender.com'

  const handleSubmit = async () => {
    if (tab === 'signup' && !agreed) return
    if (!id.trim()) return alert('아이디를 입력해주세요.')
    if (!pw.trim()) return alert('비밀번호를 입력해주세요.')
    if (tab === 'signup' && !nickname.trim()) return alert('닉네임을 입력해주세요.')
    if (tab === 'signup' && !agreed) return alert('이용약관에 동의해주세요.')
    try {
      const endpoint = tab === 'login' ? '/api/user/login' : '/api/user/signup'
      const body = tab === 'login'
        ? { username: id, password: pw }
        : { username: id, password: pw, nickname: nickname || id }

      const res = await fetch(`${BE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      if (!res.ok) {
        const err = await res.json()
        alert(err.detail || '오류가 발생했어요.')
        return
      }
      onLogin()
    } catch {
      alert('서버 연결 오류가 발생했어요.')
    }
  }

  return (
    <div className="login-page">
      <div className="login-header">
        <h1 className="login-logo">뮤즈 에디터 <span className="login-beta">BETA</span></h1>
        <p className="login-sub">글과 음악이 함께하는 집필 공간</p>
      </div>

      <div className="login-card">
        <div className="login-tabs">
          <button className={`login-tab ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>로그인</button>
          <button className={`login-tab ${tab === 'signup' ? 'active' : ''}`} onClick={() => setTab('signup')}>회원가입</button>
        </div>

        {/* 소셜 로그인 버튼 */}
        <div className="social-section">
          <button className="social-btn kakao">
            <span className="social-icon">💬</span>
            카카오로 {tab === 'login' ? '로그인' : '시작하기'}
          </button>
          <button className="social-btn google">
            <span className="social-icon">G</span>
            구글로 {tab === 'login' ? '로그인' : '시작하기'}
          </button>
        </div>

        <div className="divider"><span>또는</span></div>

        {/* 일반 로그인/회원가입 */}
        <div className="login-form">
          <label className="login-label">아이디</label>
          <input
            className="login-input"
            placeholder="아이디를 입력하세요"
            value={id}
            onChange={e => setId(e.target.value)}
          />
          <label className="login-label">비밀번호</label>
          <input
            className="login-input"
            type="password"
            placeholder="비밀번호를 입력하세요"
            value={pw}
            onChange={e => setPw(e.target.value)}
          />

          {tab === 'signup' && (
            <>
              <label className="login-label">닉네임</label>
              <input
                className="login-input"
                placeholder="닉네임을 입력하세요"
                value={nickname}
                onChange={e => setNickname(e.target.value)}
              />
            </>
          )}

          {tab === 'signup' && (
            <div className="agree-box">
              <label className="agree-row">
                <input type="checkbox" checked={agreed} onChange={e => setAgreed(e.target.checked)} />
                <span>이용약관 및 개인정보 수집에 동의합니다 <span className="agree-required">(필수)</span></span>
              </label>
              <p className="agree-detail">
                서비스 이용 시 기기 식별 정보(기기 고유값, IP 등)가 수집될 수 있으며, 수집된 정보는 중복 가입 방지 및 서비스 보안 목적으로만 활용됩니다.
                <span className="agree-link"> 전문 보기</span>
              </p>
            </div>
          )}

          <button
            className="login-btn"
            onClick={handleSubmit}
            disabled={tab === 'signup' && !agreed}
            style={{ opacity: tab === 'signup' && !agreed ? 0.5 : 1 }}
          >
            {tab === 'login' ? '로그인' : '가입하고 시작하기'}
          </button>
        </div>

        <div className="login-footer">
          <p>글을 쓰는 순간, 음악이 흐릅니다.</p>
          <p>회원 정보는 안전하게 암호화되어 저장됩니다</p>
        </div>
      </div>
    </div>
  )
}
