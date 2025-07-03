// src/composables/useTheme.ts
import { ref, watchEffect, computed } from 'vue';

export const useTheme = () => {
  // 从本地存储或系统设置获取初始主题
  const theme = ref(localStorage.theme || 
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  );

  // 初始化主题
  const initTheme = () => {
    document.documentElement.classList.toggle('dark', theme.value === 'dark');
  };

  // 监听系统主题变化
  const watchSystemTheme = () => {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      if (!localStorage.theme) { // 仅当用户未手动设置主题时跟随系统
        theme.value = e.matches ? 'dark' : 'light';
      }
    });
  };

  // 切换主题
  const toggleTheme = () => {
    theme.value = theme.value === 'dark' ? 'light' : 'dark';
  };

  // 计算属性：检查当前是否为深色模式
  const isDark = computed(() => theme.value === 'dark');

  // 计算属性：获取主题图标（用于切换按钮）
  const themeIcon = computed(() => 
    isDark.value ? 'fa-sun' : 'fa-moon'
  );

  // 计算属性：获取主题名称（用于切换按钮）
  const themeName = computed(() => 
    isDark.value ? '浅色模式' : '深色模式'
  );

  // 保存主题到本地存储
  watchEffect(() => {
    localStorage.theme = theme.value;
    document.documentElement.classList.toggle('dark', theme.value === 'dark');
  });

  return {
    theme,
    toggleTheme,
    initTheme,
    watchSystemTheme,
    isDark,
    themeIcon,
    themeName
  };
};