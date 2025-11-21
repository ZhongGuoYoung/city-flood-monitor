// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url)),
        },
    },
    server: {
        port: 8080, // 看你原来 devServer 用几号端口
        proxy: {
            '^/api': {
                target: 'http://localhost:9000', // FastAPI 后端地址
                changeOrigin: true,
                ws: true, //支持 WebSocket/SSE
            },
        },
    },
})
