<template>
  <div class="page-container">
    <slot></slot>
  </div>
</template>

<script setup lang="ts">
// 无需额外的逻辑
</script>

<style scoped>
.page-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  box-sizing: border-box;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .page-container {
    padding: 0 16px;
  }
}

@media (max-width: 768px) {
  .page-container {
    padding: 0 12px;
  }
}
</style> 