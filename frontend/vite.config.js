import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api/cameras': {
        target: 'http://localhost:5057',
        changeOrigin: true,
      },
      '/api/ws': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
