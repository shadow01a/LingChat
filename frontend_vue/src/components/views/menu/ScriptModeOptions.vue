<template>
  <StartList>
    <StartItem
      v-for="(script, index) in currentPageScripts"
      :key="script.script_name"
      @click="selectScript(script)"
    >
      {{ script.script_name }}
    </StartItem>

    <!-- 占位 -->
    <StartItem v-for="n in pageSize - currentPageScripts.length" :key="'placeholder-' + n" disabled>
      {{ '\u00A0' }}
    </StartItem>

    <!-- 分页控制 -->
    <div class="pagination-controls">
      <StartItem @click="currentPage--" :disabled="currentPage === 1"><</StartItem>
      <StartItem disabled style="font-size: 28px">{{ currentPage }} / {{ totalPages }}</StartItem>
      <StartItem @click="currentPage++" :disabled="currentPage === totalPages">></StartItem>
      <!-- 返回按钮 -->
      <StartItem @click="backToGameModeMenu" :disabled="false">返回</StartItem>
    </div>
  </StartList>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { type ScriptSummary } from '@/api/services/script-info'
import { scriptHandler } from '@/api/websocket/handlers/script-handler'
import { useGameStore } from '@/stores/modules/game'

const emit = defineEmits<{
  (e: 'back'): void
}>()

const props = defineProps({
  scripts: {
    type: Array as () => ScriptSummary[],
    default: [],
  },
})

const router = useRouter()
const gameStore = useGameStore()

const currentPage = ref(1)
const pageSize = 3

interface MenuItem {
  label: string
  action: () => void
  disabled?: boolean
}

const selectScript = async (script: ScriptSummary) => {
  await router.push('/chat')

  const command = `/开始剧本 ${script.script_name}`
  gameStore.enterStoryMode(script.script_name)

  scriptHandler.sendMessage(command)
}

const backToGameModeMenu = () => {
  emit('back')
}

const totalPages = computed(() => {
  return Math.ceil(props.scripts.length / pageSize)
})

const currentPageScripts = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  const end = start + pageSize
  return props.scripts.slice(start, end)
})
</script>

<style scoped></style>
