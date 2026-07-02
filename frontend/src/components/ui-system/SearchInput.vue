<template>
  <div class="search-input" :class="{ 'search-input--focused': isFocused }">
    <SearchOutlined class="search-input__icon" />
    <input
      ref="inputRef"
      type="text"
      class="search-input__field"
      :value="modelValue"
      :placeholder="placeholder"
      @input="handleInput"
      @focus="isFocused = true"
      @blur="isFocused = false"
      @keydown.enter="handleEnter"
    />
    <div v-if="modelValue" class="search-input__clear" @click="handleClear">
      <CloseCircleFilled />
    </div>
    <div v-if="shortcut" class="search-input__shortcut">
      {{ shortcut }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { SearchOutlined, CloseCircleFilled } from '@ant-design/icons-vue'

interface Props {
  modelValue: string
  placeholder?: string
  shortcut?: string
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: 'Search knowledge base...',
  shortcut: ''
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'search', value: string): void
  (e: 'clear'): void
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const isFocused = ref(false)

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

const handleEnter = () => {
  emit('search', props.modelValue)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  inputRef.value?.focus()
}

const focus = () => {
  inputRef.value?.focus()
}

defineExpose({ focus })
</script>

<style scoped>
.search-input {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--copilot-bg-tertiary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-lg);
  transition: all var(--copilot-transition-normal);
}

.search-input--focused {
  border-color: var(--copilot-accent-cyan);
  box-shadow: 0 0 0 3px var(--copilot-accent-cyan-dim);
}

.search-input__icon {
  color: var(--copilot-text-tertiary);
  font-size: 16px;
  flex-shrink: 0;
}

.search-input--focused .search-input__icon {
  color: var(--copilot-accent-cyan);
}

.search-input__field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-base);
  font-family: var(--copilot-font-family);
}

.search-input__field::placeholder {
  color: var(--copilot-text-tertiary);
}

.search-input__clear {
  display: flex;
  align-items: center;
  color: var(--copilot-text-tertiary);
  cursor: pointer;
  transition: color var(--copilot-transition-fast);
}

.search-input__clear:hover {
  color: var(--copilot-text-secondary);
}

.search-input__shortcut {
  padding: 2px 8px;
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-sm);
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
  font-family: var(--copilot-font-mono);
}
</style>

