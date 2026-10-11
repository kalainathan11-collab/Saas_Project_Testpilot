import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vitest/config'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rolldownOptions: {
      output: {
        codeSplitting: {
          groups: [
            { name: 'chartjs', test: /node_modules[\/](chart\.js|react-chartjs-2)[\/]/, priority: 30 },
            { name: 'framer-motion', test: /node_modules[\/](framer-motion|motion-dom|motion-utils)[\/]/, priority: 20 },
            { name: 'vendor', test: /node_modules[\/](react|react-dom|react-router|react-router-dom|scheduler|axios)[\/]/, priority: 10 },
          ],
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: false,
    css: false,
  },
})
