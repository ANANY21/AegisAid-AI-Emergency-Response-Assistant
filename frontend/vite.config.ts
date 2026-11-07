import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: Number(process.env.PORT) || 8080,
    allowedHosts: [
      'cozy-wonder-production.up.railway.app',
      '.railway.app',
      '.up.railway.app',
      'localhost',
      '127.0.0.1'
    ]
  }
})
