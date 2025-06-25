import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    server: {
        proxy: {
            '/ai-api': {
                target: 'http://127.0.0.1:11434',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/ai-api/, '/api')
            },
            '/api': {
                target: 'http://127.0.0.1:5000',
                changeOrigin: true,
            }
        }
    }
})