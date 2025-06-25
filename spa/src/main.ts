import '@/style.css'
// import App from './App.vue'

import 'element-plus/theme-chalk/dark/css-vars.css'
import 'element-plus/dist/index.css'

import App from '@/App.vue'
import ElementPlus from 'element-plus'
import {createApp} from 'vue'

const app = createApp(App)
app.use(ElementPlus).mount('#app')
