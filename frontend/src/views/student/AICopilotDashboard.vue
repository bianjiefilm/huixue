<template>
  <div class="copilot-dashboard">
    <!-- 主内容区 -->
    <div class="copilot-main">
      <!-- 头部 -->
      <header class="copilot-header">
        <div class="header-left">
          <h1 class="welcome-title">{{ userName }}，欢迎回来</h1>
          <p class="welcome-subtitle">您的AI学习副驾已准备就绪</p>
        </div>
        <div class="header-right">
          <div class="notification-bell" @click="showNotifications">
            <BellOutlined />
            <span v-if="criticalCount > 0" class="notification-badge">{{ criticalCount }}</span>
          </div>
          <a-input-search
            v-model:value="searchQuery"
            placeholder="搜索知识库..."
            style="width: 250px"
            @search="handleSearch"
          />
        </div>
      </header>

      <!-- 内容网格 -->
      <div class="content-grid">
        <!-- 活跃学习路径 -->
        <section class="section-paths">
          <div class="section-header">
            <h2 class="section-title">活跃学习路径</h2>
            <a href="#/classroom" class="view-all">
              查看全部 <RightOutlined />
            </a>
          </div>
          <ActiveLearningPaths :paths="displayPaths" :loading="loading.dashboard" />
        </section>

        <!-- 底部网格：认知档案 + 优先情报 -->
        <div class="bottom-grid">
          <!-- 认知档案 -->
          <section class="section-profile">
            <CognitiveProfile
              :skills="skillNodes"
              :loading="loading.dashboard"
              :ai-summary="aiSkillSummary"
            />
          </section>

          <!-- 优先情报 -->
          <section class="section-intel">
            <PriorityIntel
              :deadlines="upcomingDeadlines"
              :recommendations="pathRecommendations"
              :loading="loading.dashboard"
            />
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  RightOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { useAICopilotStore } from '@/stores/aiCopilot'
import ActiveLearningPaths from '@/components/ai-copilot/ActiveLearningPaths.vue'
import CognitiveProfile from '@/components/ai-copilot/CognitiveProfile.vue'
import PriorityIntel from '@/components/ai-copilot/PriorityIntel.vue'

// Stores
const userStore = useUserStore()
const copilotStore = useAICopilotStore()

// 用户信息
const userName = computed(() => {
  const name = userStore.userInfo?.realname || userStore.userInfo?.name || userStore.userInfo?.username
  return name || '同学'
})
const userId = computed(() => userStore.userId?.toString() || '1')

// Store 状态
const loading = computed(() => copilotStore.loading)
const skillNodes = computed(() => copilotStore.skillNodes)
const aiSkillSummary = computed(() => copilotStore.aiSkillSummary)
const upcomingDeadlines = computed(() => copilotStore.upcomingDeadlines)
const pathRecommendations = computed(() => copilotStore.pathRecommendations)
const criticalCount = computed(() => copilotStore.criticalCount)

// 显示前 4 个学习路径
const displayPaths = computed(() => copilotStore.activePaths.slice(0, 4))

// 搜索
const searchQuery = ref('')

const handleSearch = (query: string) => {
  console.log('搜索:', query)
  message.info('搜索功能即将上线')
}

// 通知
const showNotifications = () => {
  if (criticalCount.value > 0) {
    message.warning(`您有 ${criticalCount.value} 个紧急截止日期需要关注！`)
  } else {
    message.success('暂无紧急通知')
  }
}

// 初始化
onMounted(async () => {
  await copilotStore.initializeDashboard(userId.value, userName.value)
})
</script>

<style scoped>
/* 亮色主题 CSS 变量定义 */
.copilot-dashboard {
  --copilot-bg-primary: #f5f5f5;
  --copilot-bg-secondary: #ffffff;
  --copilot-bg-tertiary: #fafafa;
  --copilot-text-primary: rgba(0, 0, 0, 0.85);
  --copilot-text-secondary: rgba(0, 0, 0, 0.65);
  --copilot-text-tertiary: rgba(0, 0, 0, 0.45);
  --copilot-border-default: #d9d9d9;
  --copilot-border-accent: #1890ff;
  --copilot-accent-cyan: #1890ff;
  --copilot-accent-pink: #eb2f96;
  --copilot-accent-green: #52c41a;
  --copilot-gradient-primary: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  --copilot-font-size-xs: 12px;
  --copilot-font-size-sm: 13px;
  --copilot-font-size-base: 14px;
  --copilot-font-size-lg: 18px;
  --copilot-font-size-2xl: 32px;
  --copilot-radius-md: 8px;
  --copilot-transition-fast: 150ms ease;
  --copilot-transition-normal: 250ms ease;

  min-height: 100%;
  background: var(--copilot-bg-primary);
  color: var(--copilot-text-primary);
}

/* 主内容区 */
.copilot-main {
  padding: 24px;
  overflow-y: auto;
}

/* 头部 */
.copilot-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
}

.header-left {
  flex: 1;
}

.welcome-title {
  font-size: var(--copilot-font-size-2xl);
  font-weight: 700;
  margin: 0 0 8px 0;
  background: var(--copilot-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-subtitle {
  font-size: var(--copilot-font-size-base);
  color: var(--copilot-text-secondary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-bell {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-secondary);
  cursor: pointer;
  transition: all var(--copilot-transition-normal);
}

.notification-bell:hover {
  border-color: var(--copilot-border-accent);
  color: var(--copilot-accent-cyan);
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: var(--copilot-accent-pink);
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

/* 内容网格 */
.content-grid {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-paths {
  width: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: var(--copilot-font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--copilot-text-primary);
}

.view-all {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-accent-cyan);
  text-decoration: none;
  transition: opacity var(--copilot-transition-fast);
}

.view-all:hover {
  opacity: 0.8;
}

/* 底部网格 */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

.section-profile,
.section-intel {
  min-height: 400px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .copilot-main {
    padding: 16px;
  }

  .copilot-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-right {
    width: 100%;
  }
}
</style>
