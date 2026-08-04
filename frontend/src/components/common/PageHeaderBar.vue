<template>
  <div class="hx-page-header">
    <div class="hx-page-header__row">
      <div class="hx-page-header__titles">
        <a-button v-if="showBack" type="text" class="hx-page-header__back" @click="onBack">
          ← 返回
        </a-button>
        <div>
          <h1 class="hx-page-header__title">{{ title }}</h1>
          <p v-if="subtitle" class="hx-page-header__subtitle">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.actions" class="hx-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="$slots.extra" class="hx-page-header__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const props = withDefaults(
  defineProps<{ title: string; subtitle?: string; showBack?: boolean }>(),
  { showBack: false }
)
const router = useRouter()
const onBack = () => router.back()
</script>

<style scoped>
.hx-page-header {
  margin-bottom: var(--hx-space-5);
}
.hx-page-header__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--hx-space-4);
  flex-wrap: wrap;
}
.hx-page-header__titles {
  display: flex;
  align-items: flex-start;
  gap: var(--hx-space-2);
  min-width: 0;
}
.hx-page-header__title {
  margin: 0;
  font-size: var(--hx-font-size-lg);
  font-weight: 600;
  color: var(--hx-color-text-primary);
  line-height: 1.3;
}
.hx-page-header__subtitle {
  margin: var(--hx-space-1) 0 0;
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
}
.hx-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--hx-space-2);
  align-items: center;
}
.hx-page-header__extra {
  margin-top: var(--hx-space-4);
}
</style>
