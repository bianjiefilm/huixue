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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  /* 确保全局文本方向为水平 */
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  -webkit-writing-mode: horizontal-tb !important;
  -ms-writing-mode: lr-tb !important;
  direction: ltr !important;
  unicode-bidi: normal !important;
}

#app {
  width: 100%;
  height: 100%;
  overflow-x: hidden; /* 防止水平溢出 */
}

a {
  text-decoration: none;
  color: inherit;
}

/* 确保标签文本水平显示 */
.arco-tag {
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  -webkit-writing-mode: horizontal-tb !important;
  -ms-writing-mode: lr-tb !important;
  direction: ltr !important;
  unicode-bidi: normal !important;
  transform: none !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  position: relative !important;
  left: 0 !important;
}

/* Arco Design组件全局修复 */
.arco-radio-button, .arco-checkbox, .arco-tabs-tab, .arco-dropdown-option, 
.arco-menu-item, .arco-card, .arco-input, .arco-select-option, .arco-form-item {
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  -webkit-writing-mode: horizontal-tb !important;
  direction: ltr !important;
  position: relative !important;
  left: 0 !important;
  transform: none !important;
  float: none !important;
}

/* 修复Radio点击后的布局崩溃 */
.arco-radio-group .arco-radio-button,
.arco-radio-checked,
.arco-radio-button-checked,
.arco-radio-button.arco-radio-checked {
  transform: none !important;
  position: relative !important;
  left: 0 !important;
  float: none !important;
  display: inline-flex !important;
}

/* 修复栅格系统在移动设备上的特定问题 */
.arco-row {
  margin-left: -12px !important;
  margin-right: -12px !important;
  display: flex !important;
  flex-wrap: wrap !important;
}
  
.arco-col {
  padding-left: 12px !important;
  padding-right: 12px !important;
  position: relative !important;
  left: 0 !important;
  transform: none !important;
  float: none !important;
}

@media (max-width: 768px) {
  .arco-row {
    margin-left: -8px !important;
    margin-right: -8px !important;
  }
  
  .arco-col {
    padding-left: 8px !important;
    padding-right: 8px !important;
  }
  
  /* 重置筛选值的移动端布局 */
  .filter-content .arco-radio-group,
  .filter-content .arco-radio-button {
    transform: none !important;
    position: relative !important;
    left: 0 !important;
    text-orientation: mixed !important;
    writing-mode: horizontal-tb !important;
  }
}

/* 统一卡片组件的高度设置 */
.course-card {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  position: relative !important;
  left: 0 !important;
  transform: none !important;
  width: 100% !important;
}

/* 全局修复点击筛选后的布局偏移问题 */
.filter-content .arco-radio-button.arco-radio-checked {
  position: relative !important;
  left: 0 !important;
  transform: none !important;
  float: none !important;
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  -webkit-writing-mode: horizontal-tb !important;
}

/* 防止变形元素影响全局布局 */
.arco-radio-group,
.arco-radio-button,
.card-content,
.direction-tag,
.course-title,
.course-info,
.course-card,
.card-cover {
  position: relative !important;
  left: 0 !important;
  transform: none !important;
  float: none !important;
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
}

/* 确保消息容器不受潜在覆盖的影响 */
.ant-message {
  position: fixed !important; /* 确保定位上下文 */
  /* 覆盖任何可能的错误定位 */
  top: 8px !important; /* Antdv默认顶部位置 */
  left: 50% !important;
  transform: translateX(-50%) !important;
  right: auto !important;
  bottom: auto !important;
  z-index: 1010 !important; /* Antdv默认z-index */
  width: auto !important; /* 让内容决定宽度 */
  max-width: calc(100% - 32px) !important; /* 防止溢出 */
  /* 重置任何可能冲突的文本方向样式 */
  text-orientation: initial !important;
  writing-mode: horizontal-tb !important;
}
</style>
