import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/runs': 'http://127.0.0.1:8000',
      '/ingest-manifests': 'http://127.0.0.1:8000',
      '/optimization': 'http://127.0.0.1:8000',
      '/campaigns': 'http://127.0.0.1:8000',
      '/export': 'http://127.0.0.1:8000'
    }
  }
})
