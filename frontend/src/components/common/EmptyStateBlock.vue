<template>
  <div class="hx-empty">
    <a-empty :description="description">
      <template v-if="title" #image>
        <span class="hx-empty__title">{{ title }}</span>
      </template>
      <div v-if="$slots.action" class="hx-empty__action">
        <slot name="action" />
      </div>
    </a-empty>
  </div>
</template>

<script setup lang="ts">
defineProps<{ description: string; title?: string }>()
</script>

<style scoped>
.hx-empty {
  padding: var(--hx-space-7) var(--hx-space-5);
}
.hx-empty__title {
  font-size: var(--hx-font-size-md);
  color: var(--hx-color-text-secondary);
}
.hx-empty__action {
  margin-top: var(--hx-space-4);
}
</style>
