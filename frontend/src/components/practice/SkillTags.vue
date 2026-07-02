<template>
  <div class="skill-tags-input">
    <a-select
      ref="selectRef"
      v-model:value="selectedTags"
      mode="tags"
      :placeholder="placeholder"
      :max-tag-count="maxCount"
      :max-tag-text-length="20"
      :disabled="disabled"
      @change="handleChange"
      style="width: 100%"
    >
      <template #tagRender="{ value, closable, onClose }">
        <a-tag
          :closable="closable && !disabled"
          @close="onClose"
          :color="getTagColor(value)"
        >
          {{ value }}
        </a-tag>
      </template>
    </a-select>
    
    <div v-if="showHint" class="skill-tags-hint">
      <span :class="{ 'error': selectedTags.length >= maxCount }">
        已添加 {{ selectedTags.length }} / {{ maxCount }} 个技能标签
      </span>
      <span v-if="selectedTags.length >= maxCount" class="error">
        已达到最大限制
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { message } from 'ant-design-vue';

const props = withDefaults(defineProps<{
  value?: string[];
  maxCount?: number;
  placeholder?: string;
  disabled?: boolean;
  showHint?: boolean;
  existingTags?: string[]; // 课程内已存在的标签，用于去重检查
}>(), {
  maxCount: 5,
  placeholder: '输入技能标签后按回车添加',
  disabled: false,
  showHint: true,
  existingTags: () => []
});

const emit = defineEmits<{
  (e: 'update:value', value: string[]): void;
  (e: 'change', value: string[]): void;
}>();

const selectRef = ref();

// 选中的标签
const selectedTags = computed({
  get: () => props.value || [],
  set: (value) => {
    emit('update:value', value);
    emit('change', value);
  }
});

// 标签颜色
const tagColors = [
  'blue',
  'green',
  'orange',
  'purple',
  'cyan'
];

// 获取标签颜色
const getTagColor = (tag: string) => {
  const index = selectedTags.value.indexOf(tag);
  return tagColors[index % tagColors.length];
};

// 处理标签变化
const handleChange = (values: string[]) => {
  // 检查是否超过最大数量
  if (values.length > props.maxCount) {
    message.warning(`最多只能添加${props.maxCount}个技能标签`);
    selectedTags.value = values.slice(0, props.maxCount);
    return;
  }
  
  // 检查新增的标签
  const newTags = values.filter(v => !selectedTags.value.includes(v));
  
  for (const tag of newTags) {
    // 检查标签长度
    if (tag.length > 20) {
      message.warning('技能标签不能超过20个字符');
      selectedTags.value = selectedTags.value.filter(t => t !== tag);
      return;
    }
    
    // 检查是否与已存在的标签重复
    if (props.existingTags.includes(tag)) {
      message.warning(`技能标签"${tag}"在课程中已存在，不可重复`);
      selectedTags.value = selectedTags.value.filter(t => t !== tag);
      return;
    }
    
    // 检查是否包含特殊字符
    const invalidChars = /[<>\"'&]/;
    if (invalidChars.test(tag)) {
      message.warning('技能标签不能包含特殊字符');
      selectedTags.value = selectedTags.value.filter(t => t !== tag);
      return;
    }
  }
  
  selectedTags.value = values;
};

// 清空标签
const clear = () => {
  selectedTags.value = [];
};

// 暴露方法
defineExpose({
  clear
});
</script>

<style scoped>
.skill-tags-input {
  width: 100%;
}

.skill-tags-hint {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  display: flex;
  justify-content: space-between;
}

.skill-tags-hint .error {
  color: #ff4d4f;
}

:deep(.ant-select-selector) {
  min-height: 32px;
}

:deep(.ant-tag) {
  margin: 2px 4px 2px 0;
  padding: 0 7px;
  font-size: 12px;
  line-height: 20px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}
</style>