<template>
  <div
    class="hx-content-card"
    :class="[
      `hx-content-card--${size}`,
      { 'hx-content-card--hoverable': hoverable },
    ]"
  >
    <div v-if="$slots.header" class="hx-content-card__header">
      <slot name="header" />
    </div>
    <div class="hx-content-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="hx-content-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ size?: 'sm' | 'md'; hoverable?: boolean }>(),
  { size: 'md', hoverable: false }
)
</script>

<style scoped>
.hx-content-card {
  background: var(--hx-color-bg-container);
  border: 1px solid var(--hx-color-border-muted);
  border-radius: var(--hx-radius-md);
  box-shadow: var(--hx-shadow-sm);
  overflow: hidden;
}
.hx-content-card--md .hx-content-card__body,
.hx-content-card--md .hx-content-card__header,
.hx-content-card--md .hx-content-card__footer {
  padding: var(--hx-space-5);
}
.hx-content-card--sm .hx-content-card__body,
.hx-content-card--sm .hx-content-card__header,
.hx-content-card--sm .hx-content-card__footer {
  padding: var(--hx-space-4);
}
.hx-content-card__header {
  border-bottom: 1px solid var(--hx-color-border-muted);
}
.hx-content-card__footer {
  border-top: 1px solid var(--hx-color-border-muted);
}
.hx-content-card--hoverable {
  transition: box-shadow var(--hx-transition-normal), transform var(--hx-transition-fast);
}
.hx-content-card--hoverable:hover {
  box-shadow: var(--hx-shadow-md);
  transform: translateY(-1px);
}
</style>
