<template>
  <span 
    class="priority-badge" 
    :class="[`priority-badge--${type}`, { 'priority-badge--pulse': pulse }]"
  >
    <component :is="iconComponent" v-if="showIcon" class="priority-badge__icon" />
    <span class="priority-badge__text">{{ displayText }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { 
  ClockCircleOutlined, 
  WarningOutlined, 
  StarOutlined,
  CheckCircleOutlined,
  FireOutlined
} from '@ant-design/icons-vue'

interface Props {
  type: 'deadline' | 'skill_gap' | 'optional' | 'mandatory' | 'completed'
  text?: string
  showIcon?: boolean
  pulse?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showIcon: true,
  pulse: false
})

const typeConfig = {
  deadline: {
    text: '优先：截止日期临近',
    icon: ClockCircleOutlined
  },
  skill_gap: {
    text: '优先：需要加强',
    icon: FireOutlined
  },
  optional: {
    text: '拓展课程',
    icon: StarOutlined
  },
  mandatory: {
    text: '必修',
    icon: WarningOutlined
  },
  completed: {
    text: '已完成',
    icon: CheckCircleOutlined
  }
}

const displayText = computed(() => props.text || typeConfig[props.type]?.text || props.type)
const iconComponent = computed(() => typeConfig[props.type]?.icon || WarningOutlined)
</script>

<style scoped>
.priority-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--copilot-radius-full);
  font-size: var(--copilot-font-size-xs);
  font-weight: 600;
  letter-spacing: 0.3px;
}

.priority-badge__icon {
  font-size: 12px;
}

/* Deadline - 黄色/橙色 */
.priority-badge--deadline {
  background: var(--copilot-accent-yellow-dim);
  color: var(--copilot-accent-yellow);
  border: 1px solid rgba(210, 153, 34, 0.3);
}

/* Skill Gap - 粉色/品红 */
.priority-badge--skill_gap {
  background: var(--copilot-accent-pink-dim);
  color: var(--copilot-accent-pink);
  border: 1px solid rgba(255, 107, 157, 0.3);
}

/* Optional - 青色 */
.priority-badge--optional {
  background: var(--copilot-accent-cyan-dim);
  color: var(--copilot-accent-cyan);
  border: 1px solid rgba(0, 217, 255, 0.3);
}

/* Mandatory - 紫色 */
.priority-badge--mandatory {
  background: var(--copilot-accent-purple-dim);
  color: var(--copilot-accent-purple);
  border: 1px solid rgba(163, 113, 247, 0.3);
}

/* Completed - 绿色 */
.priority-badge--completed {
  background: var(--copilot-accent-green-dim);
  color: var(--copilot-accent-green);
  border: 1px solid rgba(63, 185, 80, 0.3);
}

/* 脉冲动画 */
.priority-badge--pulse {
  animation: badge-pulse 2s ease-in-out infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
