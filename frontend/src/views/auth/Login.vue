<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-area">
        <img src="@/assets/logo.png" alt="Logo" class="logo" />
        <h1 class="platform-title">慧学</h1>
      </div>
      
      <a-form
        :model="loginForm"
        @finish="handleLogin"
        class="login-form"
      >
        <a-form-item
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input 
            v-model:value="loginForm.username" 
            placeholder="用户名/手机号" 
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>
        
        <a-form-item
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password 
            v-model:value="loginForm.password" 
            placeholder="密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <!--
        <a-form-item name="remember">
          <a-checkbox v-model:checked="loginForm.remember">记住我</a-checkbox>
          <a class="login-form-forgot" href="javascript:;">忘记密码</a>
        </a-form-item>-->
        
        <a-form-item>
          <a-button 
            type="primary" 
            html-type="submit" 
            class="login-form-button" 
            size="large"
            :loading="loading"
          >
            登录
          </a-button>
          <!--<div class="register-link">
            没有账号？<a href="javascript:;">立即注册</a>
          </div>-->
        </a-form-item>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

const loginForm = ref({
  username: '',
  password: '',
  remember: false
});

const loading = ref(false);

const handleLogin = async () => {
  loading.value = true;
  try {
    await userStore.login({
      username: loginForm.value.username,
      password: loginForm.value.password
    });
    
    message.success('登录成功');
    
    // 根据用户角色决定默认跳转路径
    let defaultPath = '/course';  // 学生默认
    const userRole = userStore.userInfo?.role;
    if (userRole === 'teacher') {
      defaultPath = '/classroom';  // 教师默认进入我的课堂
    } else if (userRole === 'admin') {
      defaultPath = '/admin/dashboard';  // 管理员进入仪表盘
    }
    
    // 获取重定向路径
    const redirectPath = route.query.redirect as string || defaultPath;
    // 避免重定向到登录页
    if (redirectPath === '/login') {
      router.push(defaultPath);
    } else {
      router.push(redirectPath);
    }
  } catch (error) {
    console.error('Login error:', error);
    message.error('登录失败，请检查用户名和密码');
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: var(--hx-space-5);
  background: var(--hx-color-bg-layout);
  box-sizing: border-box;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--hx-space-6) var(--hx-space-5);
  background: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-lg);
  box-shadow: var(--hx-shadow-md);
  border: 1px solid var(--hx-color-border-muted);
}

.logo-area {
  text-align: center;
  margin-bottom: var(--hx-space-6);
}

.logo {
  height: 64px;
  margin-bottom: var(--hx-space-4);
}

.platform-title {
  font-size: var(--hx-font-size-xl);
  font-weight: 600;
  color: var(--hx-color-text-primary);
  margin: 0;
}

.login-form {
  width: 100%;
}

.login-form-forgot {
  float: right;
}

.login-form-button {
  width: 100%;
}

.register-link {
  margin-top: var(--hx-space-4);
  text-align: center;
}
</style> 