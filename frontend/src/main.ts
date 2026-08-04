// @ts-nocheck
// Fix for @vue-office/docx polluting window.setImmediate with a broken polyfill
if (typeof window !== 'undefined' && typeof window.setImmediate === 'undefined') {
  window.setImmediate = function(callback: any, ...args: any[]) {
    setTimeout(() => callback(...args), 0);
  } as any;
}

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// 导入 Ant Design Vue
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'

// Design tokens 真源，再加载亮色布局覆盖
import './assets/styles/tokens.css'
import './assets/styles/theme-light.css'

// 忽略 React 库在开发模式下的 defaultProps 警告
const originalConsoleError = console.error;
console.error = (...args) => {
  if (typeof args[0] === 'string' && (
    args[0].includes('Support for defaultProps will be removed') ||
    args[0].includes('Warning: NP: Support for defaultProps') ||
    args[0].includes('Warning: Connect(ABe): Support for defaultProps')
  )) {
    return;
  }
  originalConsoleError(...args);
};

const originalConsoleWarn = console.warn;
console.warn = (...args) => {
  if (typeof args[0] === 'string' && (
    args[0].includes('Support for defaultProps will be removed')
  )) {
    return;
  }
  originalConsoleWarn(...args);
};

console.log('Starting Vue app with Ant Design Vue...')

// 关键修复：检查是否在 iframe 内且 URL 包含代理路径
// 如果是，则不初始化 Vue Router，让浏览器直接处理页面
const isInIframe = typeof window !== 'undefined' && window.top !== window.self;
const isProxyUrl = typeof window !== 'undefined' && window.location.href.includes('/api/v1/environments/proxy/');
const isProxyIframe = isInIframe && isProxyUrl;

console.log('环境检查:', {
  isInIframe,
  isProxyUrl,
  isProxyIframe,
  currentUrl: typeof window !== 'undefined' ? window.location.href : 'undefined',
  referrer: typeof document !== 'undefined' ? document.referrer : 'undefined'
});

// 如果是代理 iframe，不初始化 Vue 应用，让浏览器直接显示代理返回的内容
if (isProxyIframe) {
  console.log('⚠️ 检测到代理 iframe，跳过 Vue 应用初始化，让浏览器直接处理页面');
  // 不执行任何 Vue 初始化代码
  // 页面将直接显示代理返回的 HTML（Superset）
} else {
  try {
    // 创建应用实例
    const pinia = createPinia()
    const app = createApp(App)

    // 使用插件
    app.use(pinia)
    app.use(router)
    app.use(Antd)

    console.log('Mounting app...')
    // 挂载应用
    app.mount('#app')
    console.log('Vue app mounted successfully!')
  } catch (error) {
    console.error('Error starting Vue app:', error)
    // 如果有错误，显示在页面上
    const appElement = document.getElementById('app')
    if (appElement) {
      appElement.innerHTML = `<div style="color: red; padding: 20px;">Vue应用启动失败: ${(error as Error).message}</div>`
    }
  }
}
