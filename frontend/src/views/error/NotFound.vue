<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <div class="error-code">404</div>
      <h1 class="error-title">页面不存在</h1>
      <p class="error-description">
        抱歉，您访问的页面不存在或已被删除。
      </p>
      <div class="action-buttons">
        <router-link to="/">
          <a-button type="primary" size="large">
            <template #icon><home-outlined /></template>
            返回首页
          </a-button>
        </router-link>
        <a-button @click="goBack" size="large" style="margin-left: 16px;">
          <template #icon><rollback-outlined /></template>
          返回上一页
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { HomeOutlined, RollbackOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const goBack = () => {
  router.back();
};
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.not-found-content {
  text-align: center;
  padding: 48px;
}

.error-code {
  font-size: 144px;
  font-weight: bold;
  color: #1890ff;
  line-height: 1;
  margin-bottom: 24px;
}

.error-title {
  font-size: 32px;
  color: rgba(0, 0, 0, 0.85);
  margin-bottom: 16px;
}

.error-description {
  font-size: 16px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 32px;
}

.action-buttons {
  margin-top: 32px;
}
</style> 