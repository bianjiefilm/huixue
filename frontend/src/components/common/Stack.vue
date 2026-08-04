<template>
  <div
    class="hx-stack"
    :class="`hx-stack--${direction}`"
    :style="{ gap: `var(--hx-space-${gap})`, alignItems: align }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    gap?: 1 | 2 | 3 | 4 | 5 | 6 | 7
    direction?: 'vertical' | 'horizontal'
    align?: string
  }>(),
  { gap: 4, direction: 'vertical', align: 'stretch' }
)
</script>

<style scoped>
.hx-stack {
  display: flex;
}
.hx-stack--vertical {
  flex-direction: column;
}
.hx-stack--horizontal {
  flex-direction: row;
  flex-wrap: wrap;
}
</style>
