<template>
  <button @click="$emit('click')" :disabled="disabled">
    <slot />
  </button>
</template>

<script setup lang="ts">
const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['click'])
</script>

<style scoped>
@font-face {
  font-family: 'Maoken Assorted Sans';
  src: url('/fonts/MaokenAssortedSans.woff2') format('woff2');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

button {
  background: transparent;
  color: white;
  border: none;
  margin-top: 15px;
  padding: 5px;
  font-size: clamp(32px, 4vw, 72px);
  font-family:
    'Maoken Assorted Sans',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    Roboto,
    'Helvetica Neue',
    Arial,
    sans-serif;
  cursor: pointer;
  text-align: justify;
  text-align-last: justify;
  white-space: nowrap;
  transition:
    transform 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28),
    color 0.3s ease,
    text-shadow 0.3s ease;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

button:hover {
  color: #f0f0f0;
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.4);
  transform: translateY(-8px) scale(1.05);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button:hover:disabled {
  color: white;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}
</style>
