<template>
  <div class="welcome">
    <h1>欢迎使用慧学</h1>
    <p>请点击上方的"课程实践"导航按钮进入课程实践页面</p>
    <a-button type="primary" size="large">
      <router-link to="/course">进入课程实践</router-link>
    </a-button>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useUserStore } from '../stores/user';

const userStore = useUserStore();

// 检查登录状态
const checkLoginStatus = () => {
  if (userStore.isLoggedIn) {
    console.log('用户已登录:', userStore.userInfo.username);
  } else {
    console.log('用户未登录');
  }
};

// 生命周期钩子
onMounted(() => {
  checkLoginStatus();
});
</script>

<style scoped>
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 200px);
  text-align: center;
  padding: 0 20px;
}

.welcome h1 {
  font-size: 32px;
  margin-bottom: 20px;
  color: var(--color-text-1);
}

.welcome p {
  font-size: 18px;
  margin-bottom: 30px;
  color: var(--color-text-3);
}

/* 响应式布局 */
@media (max-width: 768px) {
  .welcome h1 {
    font-size: 24px;
  }
  
  .welcome p {
    font-size: 16px;
  }
}
</style> 