// 调试用的最简单入口文件
import { createApp } from 'vue'
import { createPinia } from 'pinia'

console.log('开始创建Vue应用...');

// 创建一个最简单的根组件
const App = {
  template: `
    <div>
      <h1>调试模式</h1>
      <p>如果你能看到这个页面，说明Vue应用基本正常。</p>
      <p>当前时间: {{ currentTime }}</p>
      <a href="/login">前往登录页</a>
    </div>
  `,
  data() {
    return {
      currentTime: new Date().toLocaleString()
    }
  },
  mounted() {
    console.log('App mounted successfully!');
    // 每秒更新时间，证明应用在运行
    setInterval(() => {
      this.currentTime = new Date().toLocaleString();
    }, 1000);
  }
}

try {
  const app = createApp(App);
  const pinia = createPinia();
  
  app.use(pinia);
  
  console.log('准备挂载应用...');
  app.mount('#app');
  console.log('应用挂载成功！');
} catch (error) {
  console.error('应用创建失败:', error);
}