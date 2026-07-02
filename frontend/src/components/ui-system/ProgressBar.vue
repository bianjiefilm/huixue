<template>
  <div class="progress-bar" :class="[`progress-bar--${size}`, `progress-bar--${variant}`]">
    <div class="progress-bar__track">
      <div 
        class="progress-bar__fill" 
        :style="{ width: `${clampedPercent}%` }"
      >
        <div v-if="animated" class="progress-bar__shimmer" />
      </div>
    </div>
    <div v-if="showLabel" class="progress-bar__label">
      <span class="progress-bar__text">{{ label || `${clampedPercent}%` }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  percent: number
  size?: 'sm' | 'md' | 'lg'
  variant?: 'default' | 'gradient' | 'success' | 'warning' | 'danger'
  showLabel?: boolean
  label?: string
  animated?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  percent: 0,
  size: 'md',
  variant: 'gradient',
  showLabel: true,
  animated: true
})

const clampedPercent = computed(() => Math.min(100, Math.max(0, props.percent)))
</script>

<style scoped>
.progress-bar {
  display: flex;
  align-items: center;
  gap: var(--copilot-spacing-sm);
}

.progress-bar__track {
  flex: 1;
  background: var(--copilot-bg-tertiary);
  border-radius: var(--copilot-radius-full);
  overflow: hidden;
}

.progress-bar--sm .progress-bar__track { height: 4px; }
.progress-bar--md .progress-bar__track { height: 8px; }
.progress-bar--lg .progress-bar__track { height: 12px; }

.progress-bar__fill {
  height: 100%;
  border-radius: var(--copilot-radius-full);
  transition: width 0.5s ease;
  position: relative;
  overflow: hidden;
}

.progress-bar--default .progress-bar__fill {
  background: var(--copilot-accent-cyan);
}

.progress-bar--gradient .progress-bar__fill {
  background: var(--copilot-gradient-progress);
}

.progress-bar--success .progress-bar__fill {
  background: var(--copilot-accent-green);
}

.progress-bar--warning .progress-bar__fill {
  background: var(--copilot-accent-yellow);
}

.progress-bar--danger .progress-bar__fill {
  background: var(--copilot-accent-pink);
}

.progress-bar__shimmer {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.3) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.progress-bar__label {
  min-width: 40px;
  text-align: right;
}

.progress-bar__text {
  font-size: var(--copilot-font-size-sm);
  font-weight: 600;
  color: var(--copilot-accent-cyan);
}
</style>

