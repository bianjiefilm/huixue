<template>
  <div class="test-real-data">
    <h1>🧪 真实数据连接测试</h1>

    <div class="test-section">
      <h2>API连接状态</h2>
      <div class="status-card" :class="{ success: apiConnected, error: !apiConnected }">
        <h3>{{ apiConnected ? '✅ 后端API连接正常' : '❌ 后端API连接失败' }}</h3>
        <p v-if="apiConnected">后端服务运行在 http://localhost:8000</p>
        <p v-else>请确保后端服务已启动</p>
      </div>
    </div>

    <div class="test-section">
      <h2>任务数据测试</h2>
      <button @click="testTaskData" :loading="loading.task" class="test-btn">
        测试获取任务数据
      </button>

      <div v-if="taskData" class="data-display">
        <h3>任务详情：</h3>
        <pre>{{ JSON.stringify(taskData, null, 2) }}</pre>
      </div>

      <div v-if="taskError" class="error-display">
        <h3>错误信息：</h3>
        <p>{{ taskError }}</p>
      </div>
    </div>

    <div class="test-section">
      <h2>用户认证测试</h2>
      <button @click="testLogin" :loading="loading.login" class="test-btn">
        测试登录API
      </button>

      <div v-if="loginData" class="data-display">
        <h3>登录响应：</h3>
        <pre>{{ JSON.stringify(loginData, null, 2) }}</pre>
      </div>

      <div v-if="loginError" class="error-display">
        <h3>错误信息：</h3>
        <p>{{ loginError }}</p>
      </div>
    </div>

    <div class="test-section">
      <h2>Mock数据状态</h2>
      <div class="status-card" :class="{ success: !isMockEnabled, warning: isMockEnabled }">
        <h3>{{ isMockEnabled ? '⚠️ Mock数据已启用' : '✅ Mock数据已禁用' }}</h3>
        <p v-if="isMockEnabled">请禁用mock数据以使用真实API</p>
        <p v-else>前端已正确配置使用真实API数据</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getTaskDetail } from '@/api/challenge'
import { post } from '@/utils/request'

// 响应式数据
const apiConnected = ref(false)
const isMockEnabled = ref(false)
const loading = ref({
  task: false,
  login: false
})

const taskData = ref(null)
const taskError = ref('')
const loginData = ref(null)
const loginError = ref('')

// 测试任务数据
const testTaskData = async () => {
  loading.value.task = true
  taskError.value = ''
  taskData.value = null

  try {
    const response = await getTaskDetail('38', 6)
    taskData.value = response
    apiConnected.value = true
    console.log('Task data response:', response)
  } catch (error: any) {
    taskError.value = error.message || '获取任务数据失败'
    apiConnected.value = false
    console.error('Task data error:', error)
  } finally {
    loading.value.task = false
  }
}

// 测试登录API
const testLogin = async () => {
  loading.value.login = true
  loginError.value = ''
  loginData.value = null

  try {
    const response = await post('/api/login', {
      username: 'admin',
      password: 'admin123'
    })
    loginData.value = response
    apiConnected.value = true
    console.log('Login response:', response)
  } catch (error: any) {
    loginError.value = error.message || '登录测试失败'
    apiConnected.value = false
    console.error('Login error:', error)
  } finally {
    loading.value.login = false
  }
}

// 检查mock状态
const checkMockStatus = () => {
  // 检查是否导入了mock模块
  try {
    // 如果能找到mock相关的内容，说明可能启用了mock
    const mockScripts = document.querySelectorAll('script[src*="mock"]')
    isMockEnabled.value = mockScripts.length > 0
  } catch (e) {
    isMockEnabled.value = false
  }
}

onMounted(() => {
  checkMockStatus()
})
</script>

<style scoped>
.test-real-data {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.test-section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #e1e4e8;
  border-radius: 8px;
  background: #fafbfc;
}

.test-section h2 {
  margin-top: 0;
  color: #24292e;
  font-size: 18px;
  font-weight: 600;
}

.status-card {
  padding: 15px;
  border-radius: 6px;
  margin-top: 10px;
}

.status-card.success {
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  color: #52c41a;
}

.status-card.error {
  background: #fff2f0;
  border: 1px solid #ffccc7;
  color: #ff4d4f;
}

.status-card.warning {
  background: #fffbe6;
  border: 1px solid #ffe58f;
  color: #faad14;
}

.status-card h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.test-btn {
  background: #1890ff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  margin-top: 10px;
}

.test-btn:hover {
  background: #40a9ff;
}

.test-btn[loading] {
  opacity: 0.6;
  cursor: not-allowed;
}

.data-display {
  margin-top: 15px;
  padding: 15px;
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
}

.data-display h3 {
  margin-top: 0;
  color: #24292e;
  font-size: 16px;
}

.data-display pre {
  background: white;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  line-height: 1.4;
  border: 1px solid #d1d5db;
}

.error-display {
  margin-top: 15px;
  padding: 15px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 6px;
  color: #ff4d4f;
}

.error-display h3 {
  margin-top: 0;
  font-size: 16px;
}

.error-display p {
  margin-bottom: 0;
  font-family: monospace;
  font-size: 14px;
}
</style>

