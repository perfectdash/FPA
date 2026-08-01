import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env variables from process.env and .env files
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react()],
    server: {
      port: 3000,
      proxy: {
        '/api/v1/transactions': {
          target: env.INGESTION_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          secure: false
        },
        '/api': {
          target: env.BACKEND_API_URL || env.VITE_API_URL || 'http://localhost:8001',
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
