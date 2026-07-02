<template>
  <div class="cognitive-profile">
    <DarkCard variant="bordered" :hoverable="false">
      <template #header>
        <div class="profile-header">
          <h3 class="profile-title">认知档案</h3>
        </div>
      </template>

      <div class="profile-content">
        <!-- 技能星座区域 -->
        <div class="constellation-section">
          <div class="section-label">
            <StarOutlined class="label-icon" />
            <span>技能星座</span>
          </div>
          <p class="section-description">
            基于您的学习数据聚合生成的知识图谱
          </p>
          
          <!-- AI 评语 -->
          <p v-if="aiSummary" class="ai-summary">
            <RobotOutlined class="ai-icon" />
            {{ aiSummary }}
          </p>
          
          <!-- 加载状态 -->
          <div v-if="loading" class="constellation-loading">
            <div class="loading-spinner" />
            <span>正在分析您的技能...</span>
          </div>
          
          <!-- 可视化 -->
          <div v-else-if="skills.length > 0" class="constellation-wrapper">
            <SkillConstellation :skills="skills" />
          </div>
          
          <!-- 空状态 -->
          <div v-else class="constellation-empty">
            <RobotOutlined class="empty-icon" />
            <p>完成课程任务，解锁您的技能星座！</p>
          </div>
        </div>

        <!-- 技能标签 -->
        <div class="skill-tags">
          <span 
            v-for="skill in topSkills" 
            :key="skill.id"
            class="skill-tag"
            :class="getSkillClass(skill.mastery)"
          >
            {{ skill.name }}
          </span>
        </div>
      </div>
    </DarkCard>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { StarOutlined, RobotOutlined } from '@ant-design/icons-vue'
import { DarkCard } from '@/components/ui-system'
import SkillConstellation from './SkillConstellation.vue'
import type { SkillNode } from '@/stores/aiCopilot'

interface Props {
  skills: SkillNode[]
  loading?: boolean
  aiSummary?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  aiSummary: ''
})

const topSkills = computed(() => {
  return [...props.skills]
    .sort((a, b) => b.mastery - a.mastery)
    .slice(0, 6)
})

const getSkillClass = (mastery: number) => {
  if (mastery >= 80) return 'skill-tag--mastered'
  if (mastery >= 60) return 'skill-tag--proficient'
  if (mastery >= 40) return 'skill-tag--learning'
  return 'skill-tag--beginner'
}
</script>

<style scoped>
.cognitive-profile {
  height: 100%;
}

.cognitive-profile :deep(.dark-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.cognitive-profile :deep(.dark-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.profile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-title {
  font-size: var(--copilot-font-size-lg);
  font-weight: 600;
  margin: 0;
  color: var(--copilot-text-primary);
}

.profile-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.constellation-section {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--copilot-font-size-md);
  font-weight: 600;
  color: var(--copilot-text-primary);
  margin-bottom: 4px;
}

.label-icon {
  color: var(--copilot-accent-cyan);
}

.section-description {
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-text-secondary);
  margin: 0 0 12px;
}

.ai-summary {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  background: var(--copilot-accent-cyan-dim);
  border: 1px solid var(--copilot-border-accent);
  border-radius: var(--copilot-radius-md);
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-accent-cyan);
  margin-bottom: 16px;
  line-height: 1.4;
}

.ai-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.constellation-wrapper {
  flex: 1;
  min-height: 250px;
  background: var(--copilot-bg-primary);
  border-radius: var(--copilot-radius-md);
  overflow: hidden;
}

.constellation-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: var(--copilot-text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--copilot-border-default);
  border-top-color: var(--copilot-accent-cyan);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.constellation-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 40px;
  background: var(--copilot-bg-primary);
  border-radius: var(--copilot-radius-md);
}

.empty-icon {
  font-size: 32px;
  color: var(--copilot-text-tertiary);
}

.constellation-empty p {
  margin: 0;
  color: var(--copilot-text-secondary);
  font-size: var(--copilot-font-size-sm);
}

/* 技能标签 */
.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--copilot-border-muted);
}

.skill-tag {
  padding: 6px 12px;
  border-radius: var(--copilot-radius-full);
  font-size: var(--copilot-font-size-xs);
  font-weight: 500;
  border: 1px solid;
  transition: all var(--copilot-transition-fast);
}

.skill-tag:hover {
  transform: translateY(-2px);
}

.skill-tag--mastered {
  background: var(--copilot-accent-green-dim);
  color: var(--copilot-accent-green);
  border-color: rgba(63, 185, 80, 0.3);
}

.skill-tag--proficient {
  background: var(--copilot-accent-cyan-dim);
  color: var(--copilot-accent-cyan);
  border-color: rgba(0, 217, 255, 0.3);
}

.skill-tag--learning {
  background: var(--copilot-accent-yellow-dim);
  color: var(--copilot-accent-yellow);
  border-color: rgba(210, 153, 34, 0.3);
}

.skill-tag--beginner {
  background: var(--copilot-bg-tertiary);
  color: var(--copilot-text-secondary);
  border-color: var(--copilot-border-default);
}
</style>
