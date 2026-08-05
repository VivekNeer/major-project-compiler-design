import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Build straight into the FastAPI static dir; dev server proxies the API.
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../compiler/web/static',
    emptyOutDir: true,
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8080',
    },
  },
})
