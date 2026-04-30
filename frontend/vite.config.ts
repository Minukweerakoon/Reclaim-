import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

const kuameshaTarget = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
const voshanTarget = process.env.VITE_VOSHAN_API_URL || 'http://127.0.0.1:5100';

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
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/validate': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/health': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/results': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/metrics': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/ws': {
        target: kuameshaTarget.replace('http://', 'ws://'),
        ws: true,
      },
      '/items/process': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/items': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/xai': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
      '/reports': {
        target: kuameshaTarget,
        changeOrigin: true,
      },
    },
  },
})