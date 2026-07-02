import './assets/main.css'
import './assets/responsive.css'
import './assets/antd-theme.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

// 创建应用实例
const pinia = createPinia()
const app = createApp(App)

// 使用插件
app.use(pinia)
app.use(router)
app.use(Antd)

// 挂载应用
app.mount('#app')

console.log('Vue应用已启动')
