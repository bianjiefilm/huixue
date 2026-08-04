<script setup lang="ts">
// 导入主题配置
import { currentTheme, initTheme } from './utils/theme';
import { message } from 'ant-design-vue';
import zhCN from 'ant-design-vue/es/locale/zh_CN';
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'

// 初始化主题
initTheme();

dayjs.locale('en')

// 配置全局消息
message.config({
  top: '60px',
  duration: 3,
  maxCount: 3,
});
</script>

<template>
  <!-- 使用ConfigProvider包裹整个应用，应用全局配置 -->
  <a-config-provider :theme="currentTheme.theme" :components="currentTheme.components" :locale="zhCN">
    <router-view />
  </a-config-provider>
</template>

<style>
html, body {
  margin: 0;
  padding: 0;
  font-family: var(--hx-font-family);
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  direction: ltr !important;
}

#app {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

a {
  text-decoration: none;
  color: inherit;
}

.course-card {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
}

/* 确保消息容器不受潜在覆盖的影响 */
.ant-message {
  position: fixed !important;
  top: 8px !important;
  left: 50% !important;
  transform: translateX(-50%) !important;
  right: auto !important;
  bottom: auto !important;
  z-index: 1010 !important;
  width: auto !important;
  max-width: calc(100% - 32px) !important;
  text-orientation: initial !important;
  writing-mode: horizontal-tb !important;
}
</style>
