import { ref, watch } from 'vue';
import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    theme: localStorage.theme as string || 'auto',
  }),
  actions: {
    setTheme(newTheme: string) {
      this.theme = newTheme;
      localStorage.theme = this.theme;
    }
  }
})

export const useTheme = () => {

  const themeStore = useThemeStore();

  watch(() => themeStore.theme, () => {
    initTheme();
  })

  const getOperationSystemTheme = (): string => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  const operationSystemTheme = ref(getOperationSystemTheme());

  // 初始化主题
  const initTheme = () => {
    if (themeStore.theme === 'auto') {
      document.documentElement.classList.toggle('dark', operationSystemTheme.value === 'dark');
    } else {
      document.documentElement.classList.toggle('dark', themeStore.theme === 'dark');
    }
  };

  // 监听系统主题变化
  const watchSystemTheme = () => {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
      operationSystemTheme.value = e.matches ? 'dark' : 'light';
      if (themeStore.theme === 'auto') {
        document.documentElement.classList.toggle('dark', operationSystemTheme.value === 'dark');
      }
    });
  };

  return {
    initTheme,
    watchSystemTheme,
  };
};

