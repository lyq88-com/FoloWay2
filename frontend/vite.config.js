import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

// vite.config.js 必须位于项目根目录（即 UNI_INPUT_DIR），
// uni CLI 才会加载自定义配置；否则回退到插件内置默认配置。
export default defineConfig({
  plugins: [uni()],
  // 使用 modern sass API，消除 legacy-js-api 弃用警告
  css: {
    preprocessorOptions: {
      scss: {
        api: 'modern'
      }
    }
  },
  server: {
    port: 8080,
    host: '0.0.0.0',
    // H5 开发期代理：
    //  /api/register  /api/login  /api/health  → Flask 鉴权后端（端口 5000）
    //  /api/v1/*                               → 现有 FastAPI 业务后端（端口 8000）
    // 真机/小程序下不走此 proxy，需在 api/auth.js 中改用绝对地址
    // 注意：target 必须用 127.0.0.1 而不是 localhost。
    // Node 17+ 将 localhost 解析为 IPv6 (::1)，而后端只监听 IPv4 (0.0.0.0)，
    // 用 localhost 会导致代理连接失败返回 500。
    proxy: {
      '/ai': {
        // 循途AI聊天后端 ai_server.py（Flask, 端口 5001）
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      '/api/v1': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      },
      '/api/register': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/api/login': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      },
      '/api/health': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true
      }
    }
  }
})
