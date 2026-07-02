// 最小化启动文件，用于排查问题
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'

// 创建一个最简单的App组件
const MinimalApp = {
  template: `
    <div>
      <h1>最小化测试页面</h1>
      <p>如果你能看到这个页面，说明Vue应用基本功能正常。</p>
      <router-link to="/login">前往登录页</router-link>
      <hr>
      <router-view></router-view>
    </div>
  `
}

const pinia = createPinia()
const app = createApp(MinimalApp)

app.use(pinia)
app.use(router)

app.mount('#app')

console.log('最小化应用已启动')