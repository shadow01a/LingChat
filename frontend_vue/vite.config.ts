import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": "/src",
    },
  },
  server: {
    proxy: {
      // 代理普通 HTTP API 请求
      "/api": {
        target: "http://localhost:8765",
        changeOrigin: true,
      },
      // 代理 WebSocket 连接
      "/ws": {
        target: "ws://localhost:8765", // WebSocket 地址
        changeOrigin: true,
        ws: true, // 启用 WebSocket 代理
      },
    },
  },
});
