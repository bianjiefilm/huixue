<template>
  <button 
    class="glow-button" 
    :class="[
      `glow-button--${variant}`,
      `glow-button--${size}`,
      { 'glow-button--loading': loading },
      { 'glow-button--disabled': disabled }
    ]"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="glow-button__spinner" />
    <span v-if="$slots.icon && !loading" class="glow-button__icon">
      <slot name="icon" />
    </span>
    <span class="glow-button__text">
      <slot />
    </span>
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false
})

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

const handleClick = (event: MouseEvent) => {
  emit('click', event)
}
</script>

<style scoped>
.glow-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: var(--copilot-radius-md);
  font-family: var(--copilot-font-family);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--copilot-transition-normal);
  position: relative;
  overflow: hidden;
}

/* Sizes */
.glow-button--sm {
  padding: 6px 12px;
  font-size: var(--copilot-font-size-sm);
}

.glow-button--md {
  padding: 10px 20px;
  font-size: var(--copilot-font-size-base);
}

.glow-button--lg {
  padding: 14px 28px;
  font-size: var(--copilot-font-size-md);
}

/* Primary variant */
.glow-button--primary {
  background: var(--copilot-gradient-primary);
  color: white;
  box-shadow: 0 4px 15px rgba(0, 217, 255, 0.3);
}

.glow-button--primary:hover:not(:disabled) {
  box-shadow: 0 6px 25px rgba(0, 217, 255, 0.5);
  transform: translateY(-2px);
}

.glow-button--primary:active:not(:disabled) {
  transform: translateY(0);
}

/* Secondary variant */
.glow-button--secondary {
  background: var(--copilot-bg-tertiary);
  color: var(--copilot-text-primary);
  border: 1px solid var(--copilot-border-default);
}

.glow-button--secondary:hover:not(:disabled) {
  border-color: var(--copilot-accent-cyan);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

/* Ghost variant */
.glow-button--ghost {
  background: transparent;
  color: var(--copilot-accent-cyan);
  border: 1px solid var(--copilot-accent-cyan);
}

.glow-button--ghost:hover:not(:disabled) {
  background: var(--copilot-accent-cyan-dim);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

/* Danger variant */
.glow-button--danger {
  background: var(--copilot-accent-pink);
  color: white;
  box-shadow: 0 4px 15px rgba(255, 107, 157, 0.3);
}

.glow-button--danger:hover:not(:disabled) {
  box-shadow: 0 6px 25px rgba(255, 107, 157, 0.5);
  transform: translateY(-2px);
}

/* Disabled state */
.glow-button--disabled,
.glow-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* Loading state */
.glow-button--loading {
  pointer-events: none;
}

.glow-button__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.glow-button__icon {
  display: flex;
  align-items: center;
  font-size: 1.1em;
}
</style>

