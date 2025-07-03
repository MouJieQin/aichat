<!-- src/components/ThemeToggle.vue -->
<template>
  <button
    class="theme-toggle-btn"
    @click="toggleTheme"
    :aria-label="`切换到${themeName}`"
    :title="`切换到${themeName}`"
  >
    <i :class="['fa', themeIcon, 'fa-lg']"></i>
    <span class="ml-2 hidden sm:inline">{{ themeName }}</span>
  </button>
</template>

<script lang="ts" setup>
import { useTheme } from '@/common/use-theme';

const { toggleTheme, themeIcon, themeName } = useTheme();
</script>

<style scoped>
.theme-toggle-btn {
  @apply flex items-center justify-center px-4 py-2 rounded-full transition-all duration-300 
         hover:bg-gray-200 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 
         focus:ring-primary dark:focus:ring-primary-dark;
}
</style>