import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',   // ← Docker 컨테이너 외부 접근 허용
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://backend:8000',  // ← 백엔드 컨테이너로 프록시
        changeOrigin: true,
      }
    }
  }
})