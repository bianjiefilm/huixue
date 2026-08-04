<template>
  <div class="hx-page-shell" :class="`hx-page-shell--${maxWidth}`">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ maxWidth?: 'default' | 'wide' | 'fluid' }>(),
  { maxWidth: 'default' }
)
</script>

<style scoped>
.hx-page-shell {
  width: 100%;
  margin: 0 auto;
  padding: var(--hx-space-5);
  box-sizing: border-box;
}
.hx-page-shell--default {
  max-width: 1200px;
}
.hx-page-shell--wide {
  max-width: 1440px;
}
.hx-page-shell--fluid {
  max-width: none;
}
@media (max-width: 768px) {
  .hx-page-shell {
    padding: var(--hx-space-3);
  }
}
</style>
