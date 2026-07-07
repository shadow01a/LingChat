<template>
  <StartList>
    <StartItem @click="() => emit('start-game')">开始游戏</StartItem>
    <StartItem @click="() => emit('open-settings', 'save')">继续游戏</StartItem>
    <StartItem @click="() => emit('open-settings')">设置</StartItem>
    <StartItem @click="() => emit('open-credits')">致谢</StartItem>
    <StartItem @click="exitGame">退出游戏</StartItem>
  </StartList>
</template>

<script setup lang="ts">
import '../base'

const emit = defineEmits<{
  (e: 'start-game'): void
  (e: 'open-settings', tab?: string): void
  (e: 'open-credits'): void
}>()

declare global {
  interface Window {
    pywebview?: {
      api?: {
        exit_app?: () => void
      }
    }
  }
}

// 退出游戏：优先调用 WebView API，如果不可用则回退到 window.close()
function exitGame() {
  if (window.pywebview?.api?.exit_app) {
    window.pywebview.api.exit_app()
  } else {
    window.close()
  }
}
</script>

<style scoped></style>
