import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same relative /api/... paths work in both `npm run dev` (via this
    // proxy) and the production build (served same-origin by FastAPI) -
    // no separate API base URL to configure per environment.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
  },
})
