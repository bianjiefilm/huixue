<template>
  <PageShell max-width="wide" class="copilot-dashboard">
    <PageHeaderBar
      :title="`${userName}，欢迎回来`"
      subtitle="您的AI学习副驾已准备就绪"
    >
      <template #actions>
        <div class="header-actions">
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
      </template>
    </PageHeaderBar>

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
        <section class="section-profile">
          <CognitiveProfile
            :skills="skillNodes"
            :loading="loading.dashboard"
            :ai-summary="aiSkillSummary"
          />
        </section>

        <section class="section-intel">
          <PriorityIntel
            :deadlines="upcomingDeadlines"
            :recommendations="pathRecommendations"
            :loading="loading.dashboard"
          />
        </section>
      </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  RightOutlined
} from '@ant-design/icons-vue'
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
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
/* 浅色布局：依赖 layout 背景，禁止满屏深色 */
.copilot-dashboard {
  background: transparent;
  color: var(--hx-color-text-primary);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--hx-space-4);
}

.notification-bell {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--hx-color-bg-container);
  border: 1px solid var(--hx-color-border);
  border-radius: var(--hx-radius-sm);
  color: var(--hx-color-text-secondary);
  cursor: pointer;
  transition: all var(--hx-transition-normal);
}

.notification-bell:hover {
  border-color: var(--hx-color-primary);
  color: var(--hx-color-primary);
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  background: #eb2f96;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.content-grid {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-4);
}

.section-paths {
  width: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--hx-space-4);
}

.section-title {
  font-size: var(--hx-font-size-md);
  font-weight: 600;
  margin: 0;
  color: var(--hx-color-text-primary);
}

.view-all {
  display: flex;
  align-items: center;
  gap: var(--hx-space-1);
  font-size: var(--hx-font-size-sm);
  color: var(--hx-color-primary);
  text-decoration: none;
  transition: opacity var(--hx-transition-fast);
}

.view-all:hover {
  opacity: 0.8;
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: var(--hx-space-4);
}

.section-profile,
.section-intel {
  min-height: 400px;
}

@media (max-width: 1200px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-actions {
    width: 100%;
  }
}
</style>
