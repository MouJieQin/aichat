// src/composables/useTheme.ts
import { ref, watchEffect, computed } from 'vue';

export const useTheme = () => {
  const getOperationSystemTheme = (): string => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  const operationSystemTheme = ref(getOperationSystemTheme());

  // 从本地存储或系统设置获取初始主题
  const theme = ref(localStorage.theme as string || getOperationSystemTheme());

  // 设置主题
  const setTheme = (newTheme: string) => {
    theme.value = newTheme;
  }

  // 初始化主题
  const initTheme = () => {
    if (theme.value === 'auto') {
      document.documentElement.classList.toggle('dark', operationSystemTheme.value === 'dark');
    } else {
      document.documentElement.classList.toggle('dark', theme.value === 'dark');
    }
  };

  // 监听系统主题变化
  const watchSystemTheme = () => {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      operationSystemTheme.value = e.matches ? 'dark' : 'light';
    });
  };

  // 计算属性：获取主题名称（用于切换按钮）
  const themeName = computed(() => {
    if (theme.value === 'auto') {
      return '跟随系统'
    }
    return theme.value === 'light' ? '浅色模式' : '深色模式'
  }
  );

  // 保存主题到本地存储
  watchEffect(() => {
    localStorage.theme = theme.value;
    initTheme();
  });

  return {
    theme,
    setTheme,
    initTheme,
    watchSystemTheme,
    themeName
  };
};