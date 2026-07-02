<template>
  <div class="priority-intel">
    <DarkCard variant="bordered" :hoverable="false">
      <template #header>
        <h3 class="intel-title">优先情报</h3>
      </template>

      <div class="intel-content">
        <!-- 即将到期 -->
        <section class="intel-section">
          <h4 class="section-title">
            <ClockCircleOutlined class="section-icon" />
            即将到期
          </h4>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-placeholder">
            <div class="skeleton-item" v-for="i in 2" :key="i" />
          </div>

          <!-- 截止日期列表 -->
          <div v-else-if="deadlines.length > 0" class="deadlines-list">
            <div 
              v-for="deadline in displayDeadlines" 
              :key="deadline.id"
              class="deadline-item"
              :class="{ 'deadline-item--critical': deadline.isCritical }"
            >
              <div class="deadline-date">
                <span class="date-month">{{ formatMonth(deadline.dueDate) }}</span>
                <span class="date-day">{{ formatDay(deadline.dueDate) }}</span>
              </div>
              <div class="deadline-info">
                <span class="deadline-title">{{ deadline.title }}</span>
                <span class="deadline-remaining" :class="getRemainingClass(deadline)">
                  {{ formatRemaining(deadline) }}
                </span>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <CheckCircleOutlined class="empty-icon" />
            <span>暂无紧急截止日期</span>
          </div>
        </section>

        <!-- 新路径推荐 -->
        <section class="intel-section">
          <h4 class="section-title">
            <BulbOutlined class="section-icon" />
            学习路径推荐
          </h4>

          <div v-if="recommendations.length > 0" class="recommendations-list">
            <div 
              v-for="rec in recommendations" 
              :key="rec.courseId"
              class="recommendation-item"
            >
              <div class="rec-icon">
                <StarOutlined />
              </div>
              <div class="rec-content">
                <span class="rec-title">{{ rec.title }}</span>
                <span class="rec-reason">{{ rec.reason }}</span>
              </div>
            </div>
          </div>

          <!-- 默认推荐 -->
          <div v-else class="recommendations-list">
            <div class="recommendation-item">
              <div class="rec-icon">
                <StarOutlined />
              </div>
              <div class="rec-content">
                <span class="rec-title">人工智能伦理入门</span>
                <span class="rec-reason">
                  基于您的技能图谱，这门拓展课程与您的学习路径高度匹配
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </DarkCard>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  ClockCircleOutlined, 
  CheckCircleOutlined, 
  BulbOutlined,
  StarOutlined 
} from '@ant-design/icons-vue'
import { DarkCard } from '@/components/ui-system'
import type { UpcomingDeadline, PathRecommendation } from '@/stores/aiCopilot'

interface Props {
  deadlines: UpcomingDeadline[]
  recommendations: PathRecommendation[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// 显示前 5 个截止日期
const displayDeadlines = computed(() => props.deadlines.slice(0, 5))

// 日期格式化
const formatMonth = (dateStr?: string) => {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
  return months[date.getMonth()]
}

const formatDay = (dateStr?: string) => {
  if (!dateStr) return '--'
  const date = new Date(dateStr)
  return date.getDate().toString().padStart(2, '0')
}

const formatRemaining = (deadline: UpcomingDeadline) => {
  if (deadline.isCritical) {
    return `紧急：还剩 ${deadline.daysRemaining} 天`
  }
  return `还剩 ${deadline.daysRemaining} 天`
}

const getRemainingClass = (deadline: UpcomingDeadline) => {
  if (deadline.isCritical) return 'remaining--critical'
  if (deadline.daysRemaining <= 5) return 'remaining--warning'
  return ''
}
</script>

<style scoped>
.priority-intel {
  height: 100%;
}

.priority-intel :deep(.dark-card) {
  height: 100%;
}

.intel-title {
  font-size: var(--copilot-font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--copilot-text-primary);
}

.intel-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.intel-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--copilot-font-size-base);
  font-weight: 600;
  color: var(--copilot-text-primary);
  margin: 0 0 12px;
}

.section-icon {
  color: var(--copilot-accent-cyan);
}

/* 截止日期列表 */
.deadlines-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.deadline-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--copilot-bg-primary);
  border-radius: var(--copilot-radius-md);
  border: 1px solid var(--copilot-border-muted);
  transition: all var(--copilot-transition-normal);
}

.deadline-item:hover {
  border-color: var(--copilot-border-accent);
}

.deadline-item--critical {
  border-color: rgba(255, 107, 157, 0.3);
  background: rgba(255, 107, 157, 0.05);
}

.deadline-date {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 8px;
  background: var(--copilot-bg-tertiary);
  border-radius: var(--copilot-radius-sm);
}

.date-month {
  font-size: var(--copilot-font-size-xs);
  font-weight: 600;
  color: var(--copilot-accent-pink);
}

.date-day {
  font-size: var(--copilot-font-size-lg);
  font-weight: 700;
  color: var(--copilot-text-primary);
}

.deadline-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.deadline-title {
  font-size: var(--copilot-font-size-sm);
  font-weight: 500;
  color: var(--copilot-text-primary);
}

.deadline-remaining {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-secondary);
}

.remaining--critical {
  color: var(--copilot-accent-pink);
  font-weight: 600;
}

.remaining--warning {
  color: var(--copilot-accent-yellow);
}

/* 推荐列表 */
.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--copilot-bg-primary);
  border-radius: var(--copilot-radius-md);
  border: 1px solid var(--copilot-border-muted);
  transition: all var(--copilot-transition-normal);
  cursor: pointer;
}

.recommendation-item:hover {
  border-color: var(--copilot-accent-green);
  background: var(--copilot-accent-green-dim);
}

.rec-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--copilot-accent-green-dim);
  border-radius: var(--copilot-radius-sm);
  color: var(--copilot-accent-green);
  font-size: 16px;
}

.rec-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rec-title {
  font-size: var(--copilot-font-size-sm);
  font-weight: 600;
  color: var(--copilot-text-primary);
}

.rec-reason {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-accent-green);
  line-height: 1.4;
}

/* 加载状态 */
.loading-placeholder {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-item {
  height: 64px;
  background: linear-gradient(90deg, var(--copilot-bg-tertiary) 25%, var(--copilot-bg-secondary) 50%, var(--copilot-bg-tertiary) 75%);
  background-size: 200% 100%;
  border-radius: var(--copilot-radius-md);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 空状态 */
.empty-state {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: var(--copilot-bg-primary);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-secondary);
  font-size: var(--copilot-font-size-sm);
}

.empty-icon {
  color: var(--copilot-accent-green);
}
</style>
