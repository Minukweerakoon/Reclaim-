import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const voshanTarget = process.env.VITE_VOSHAN_PROXY_TARGET || 'http://127.0.0.1:5000';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
    dedupe: ['react', 'react-dom', 'react/jsx-runtime'],
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'react/jsx-runtime', '@tanstack/react-query'],
  },
  server: {
    proxy: {
      // Voshan (suspicious behaviour detection) – must come before generic /api
      '/api/voshan': {
        target: voshanTarget,
        changeOrigin: true,
        ws: true,
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/validate': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/results': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      },
      '/items/process': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: true,
      },
      '/items': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/xai': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/reports': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})