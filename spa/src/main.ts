import '@/style.css'

import 'element-plus/theme-chalk/dark/css-vars.css'
import 'element-plus/dist/index.css'

import App from '@/App.vue'
import router from '@/router'
import ElementPlus from 'element-plus'
import { createApp } from 'vue'
import 'element-plus/dist/index.css'
import { useTheme } from '@/common/use-theme';


const { initTheme, watchSystemTheme } = useTheme();
// 初始化主题
initTheme();
watchSystemTheme();
const app = createApp(App)
app.use(router).use(ElementPlus).mount('#app')
