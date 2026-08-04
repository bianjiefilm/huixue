<template>
  <div 
    class="dark-card" 
    :class="[
      `dark-card--${variant}`,
      { 'dark-card--hoverable': hoverable },
      { 'dark-card--glow': glow }
    ]"
  >
    <div v-if="$slots.header" class="dark-card__header">
      <slot name="header" />
    </div>
    <div class="dark-card__body" :class="{ 'dark-card__body--no-padding': noPadding }">
      <slot />
    </div>
    <div v-if="$slots.footer" class="dark-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'default' | 'elevated' | 'bordered'
  hoverable?: boolean
  glow?: boolean
  noPadding?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
  hoverable: true,
  glow: false,
  noPadding: false
})
</script>

<style scoped>
.dark-card {
  background: var(--copilot-bg-secondary);
  border-radius: var(--copilot-radius-lg);
  overflow: hidden;
  transition: all var(--copilot-transition-normal);
}

.dark-card--default {
  border: 1px solid var(--copilot-border-default);
}

.dark-card--elevated {
  background: var(--copilot-bg-elevated);
  box-shadow: var(--copilot-shadow-md);
}

.dark-card--bordered {
  border: 1px solid var(--copilot-border-accent);
  background-image: var(--copilot-gradient-card);
}

.dark-card--hoverable:hover {
  border-color: var(--copilot-border-accent);
  transform: translateY(-2px);
  box-shadow: var(--copilot-shadow-lg);
}

.dark-card--glow {
  box-shadow: var(--copilot-shadow-glow-cyan);
}

.dark-card--glow:hover {
  box-shadow: var(--copilot-shadow-glow-cyan);
}

.dark-card__header {
  padding: var(--copilot-spacing-md) var(--copilot-spacing-lg);
  border-bottom: 1px solid var(--copilot-border-muted);
}

.dark-card__body {
  padding: var(--copilot-spacing-lg);
}

.dark-card__body--no-padding {
  padding: 0;
}

.dark-card__footer {
  padding: var(--copilot-spacing-md) var(--copilot-spacing-lg);
  border-top: 1px solid var(--copilot-border-muted);
  background: var(--copilot-bg-tertiary);
}
</style>

