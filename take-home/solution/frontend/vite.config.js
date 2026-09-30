import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The frontend only talks to our backend. In dev, /api is proxied to FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:8000' },
  },
  test: { environment: 'jsdom' },
})
