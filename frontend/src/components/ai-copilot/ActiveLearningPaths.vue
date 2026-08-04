<template>
  <div class="learning-paths">
    <!-- 加载状态 -->
    <div v-if="loading" class="paths-loading">
      <div v-for="i in 4" :key="i" class="path-skeleton">
        <div class="skeleton-image" />
        <div class="skeleton-content">
          <div class="skeleton-line short" />
          <div class="skeleton-line" />
          <div class="skeleton-line medium" />
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="paths.length === 0" class="paths-empty">
      <RocketOutlined class="empty-icon" />
      <h3>暂无活跃学习路径</h3>
      <p>加入课堂开始您的学习之旅！</p>
    </div>

    <!-- 路径卡片 -->
    <div v-else class="paths-grid">
      <div 
        v-for="path in paths" 
        :key="path.id" 
        class="path-card"
        @click="navigateToPath(path)"
      >
        <!-- 封面图 -->
        <div class="path-cover">
          <img 
            v-if="path.coverImage" 
            :src="path.coverImage" 
            :alt="path.title"
          />
          <div v-else class="cover-placeholder">
            <div class="cover-pattern" />
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="path-content">
          <!-- 课程代码 -->
          <span class="path-code">{{ path.code }}</span>
          
          <!-- 标题 -->
          <h3 class="path-title">{{ path.title }}</h3>
          
          <!-- 优先级标签 -->
          <PriorityBadge 
            v-if="path.priority !== 'completed'"
            :type="path.priority"
            :text="getPriorityText(path)"
            :pulse="path.priority === 'deadline'"
          />
          
          <!-- AI 推荐理由 -->
          <p v-if="path.priorityReason" class="path-reason">
            <RobotOutlined class="ai-icon" />
            {{ path.priorityReason }}
          </p>

          <!-- 进度 -->
          <div class="path-progress">
            <span class="progress-label">学习进度</span>
            <div class="progress-row">
              <ProgressBar 
                :percent="path.progress" 
                :variant="getProgressVariant(path)"
                :show-label="false"
                size="sm"
              />
              <span class="progress-value">{{ path.progress }}%</span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <button class="path-action">
            继续学习
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RocketOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { useRouter } from 'vue-router'
import { PriorityBadge, ProgressBar } from '@/components/ui-system'
import type { LearningPath } from '@/stores/aiCopilot'

interface Props {
  paths: LearningPath[]
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

const router = useRouter()

const getPriorityText = (path: LearningPath) => {
  if (path.priority === 'deadline') {
    return path.daysRemaining !== undefined 
      ? `紧急：还剩 ${path.daysRemaining} 天`
      : '优先：截止日期临近'
  }
  if (path.priority === 'skill_gap') {
    return '优先：需要加强'
  }
  if (path.priority === 'optional') {
    return '拓展课程'
  }
  return path.isMandatory ? '必修' : '选修'
}

const getProgressVariant = (path: LearningPath) => {
  if (path.priority === 'deadline') return 'warning'
  if (path.priority === 'skill_gap') return 'danger'
  return 'gradient'
}

const navigateToPath = (path: LearningPath) => {
  router.push(`/classroom/${path.classroomId}/course/${path.courseId}`)
}
</script>

<style scoped>
.learning-paths {
  width: 100%;
}

/* 网格布局 */
.paths-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--hx-space-4);
}

/* 路径卡片 */
.path-card {
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--copilot-transition-normal);
}

.path-card:hover {
  border-color: var(--copilot-border-accent);
  transform: translateY(-4px);
  box-shadow: var(--copilot-shadow-lg), var(--copilot-shadow-glow-cyan);
}

/* 封面图 */
.path-cover {
  height: 140px;
  overflow: hidden;
  position: relative;
}

.path-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%);
  position: relative;
  overflow: hidden;
}

.cover-pattern {
  position: absolute;
  inset: 0;
  background-image: 
    radial-gradient(circle at 20% 30%, rgba(0, 217, 255, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(255, 107, 157, 0.1) 0%, transparent 50%);
  animation: pattern-move 8s ease-in-out infinite;
}

@keyframes pattern-move {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 1; }
}

/* 卡片内容 */
.path-content {
  padding: 16px;
}

.path-code {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.path-title {
  font-size: var(--copilot-font-size-md);
  font-weight: 600;
  margin: 8px 0 12px;
  color: var(--copilot-text-primary);
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.path-reason {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-secondary);
  margin: 12px 0;
  padding: 8px;
  background: var(--copilot-bg-tertiary);
  border-radius: var(--copilot-radius-sm);
  line-height: 1.4;
}

.ai-icon {
  color: var(--copilot-accent-cyan);
  flex-shrink: 0;
  margin-top: 2px;
}

/* 进度 */
.path-progress {
  margin: 16px 0;
}

.progress-label {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
  display: block;
  margin-bottom: 6px;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-row :deep(.progress-bar) {
  flex: 1;
}

.progress-value {
  font-size: var(--copilot-font-size-sm);
  font-weight: 600;
  color: var(--copilot-accent-cyan);
  min-width: 40px;
  text-align: right;
}

/* 操作按钮 */
.path-action {
  width: 100%;
  padding: 10px;
  background: transparent;
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--copilot-transition-normal);
}

.path-action:hover {
  background: var(--copilot-accent-cyan-dim);
  border-color: var(--copilot-accent-cyan);
  color: var(--copilot-accent-cyan);
}

/* 加载骨架屏 */
.paths-loading {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.path-skeleton {
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-lg);
  overflow: hidden;
}

.skeleton-image {
  height: 140px;
  background: linear-gradient(90deg, var(--copilot-bg-tertiary) 25%, var(--copilot-bg-secondary) 50%, var(--copilot-bg-tertiary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

.skeleton-content {
  padding: 16px;
}

.skeleton-line {
  height: 12px;
  background: var(--copilot-bg-tertiary);
  border-radius: 6px;
  margin-bottom: 12px;
}

.skeleton-line.short { width: 40%; }
.skeleton-line.medium { width: 70%; }

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 空状态 */
.paths-empty {
  text-align: center;
  padding: 60px 20px;
  background: var(--copilot-bg-secondary);
  border: 1px dashed var(--copilot-border-default);
  border-radius: var(--copilot-radius-lg);
}

.empty-icon {
  font-size: 48px;
  color: var(--copilot-accent-cyan);
  margin-bottom: 16px;
}

.paths-empty h3 {
  font-size: var(--copilot-font-size-lg);
  color: var(--copilot-text-primary);
  margin: 0 0 8px;
}

.paths-empty p {
  font-size: var(--copilot-font-size-base);
  color: var(--copilot-text-secondary);
  margin: 0;
}
</style>
