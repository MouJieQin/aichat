import '@/style.css'

import 'element-plus/theme-chalk/dark/css-vars.css'
import 'element-plus/dist/index.css'

import App from '@/App.vue'
import router from '@/router'
import ElementPlus from 'element-plus'
import { createPinia } from 'pinia'
import { createApp } from 'vue'
import 'element-plus/dist/index.css'


const app = createApp(App)
const pinia = createPinia()
app.use(router).use(ElementPlus).use(pinia).mount('#app')
