<template>
    <!-- <ThemeToggle /> -->
    <main id="app" class="flex-grow container mx-auto px-4 py-8" >
      <router-view id="app" />
    </main>
</template>

<script lang="ts" setup>
// 导入并初始化主题
import { onMounted } from 'vue';
import { useTheme } from '@/common/use-theme';
import ThemeToggle from '@/components/ThemeToggle.vue';

const { initTheme, watchSystemTheme } = useTheme();

onMounted(() => {
  initTheme();
  watchSystemTheme();
});
</script>