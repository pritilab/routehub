import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    // Docker bind mounts on Windows don't emit file events — poll instead,
    // otherwise the dev server serves stale modules after edits.
    watch: { usePolling: true, interval: 300 },
    proxy: {
      '/api': {
        // In docker compose the backend is reachable by service name
        target: process.env.DOCKER ? 'http://backend:8000' : 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
