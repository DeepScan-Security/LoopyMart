import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env variables based on mode
  const env = loadEnv(mode, process.cwd(), '')
  
  // API backend URL (default to localhost:8001 for development)
  const apiTarget = env.VITE_API_URL || 'http://127.0.0.1:8001'
  
  return {
    plugins: [
      vue(),
      vueDevTools(),
    ],
    server: {
      host: '127.0.0.1',
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
        '/static': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/robots.txt': {
          target: apiTarget,
          changeOrigin: true,
        },
        '/vendor': {
          target: apiTarget,
          changeOrigin: true,
        },
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
  }
})
