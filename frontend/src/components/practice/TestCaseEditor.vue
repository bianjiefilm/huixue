<template>
  <div class="test-case-editor">
    <div class="test-case-header">
      <h4>测试集</h4>
      <div class="test-case-actions">
        <a-checkbox v-model:checked="allVisible" @change="toggleAllVisible">
          测试集对学生可见
        </a-checkbox>
        <a-button
          type="primary"
          size="small"
          @click="addTestCase"
          :disabled="testCases.length >= maxCount"
        >
          <template #icon><PlusOutlined /></template>
          新建测试集
        </a-button>
      </div>
    </div>

    <div class="test-case-list">
      <a-card
        v-for="(testCase, index) in testCases"
        :key="index"
        :title="`测试集 ${index + 1}`"
        size="small"
        style="margin-bottom: 16px"
      >
        <template #extra>
          <a-button
            type="text"
            danger
            size="small"
            @click="removeTestCase(index)"
            :disabled="testCases.length <= minCount"
          >
            <template #icon><DeleteOutlined /></template>
          </a-button>
        </template>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="测试输入" required>
              <a-textarea
                v-model:value="testCase.input_data"
                placeholder="请输入测试输入数据"
                :auto-size="{ minRows: 3, maxRows: 6 }"
              />
            </a-form-item>
          </a-col>
          
          <a-col :span="12">
            <a-form-item label="预期输出" required>
              <a-textarea
                v-model:value="testCase.expected_output"
                placeholder="请输入预期输出结果"
                :auto-size="{ minRows: 3, maxRows: 6 }"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16" style="margin-top: 16px">
          <a-col :span="12">
            <a-form-item label="匹配规则">
              <a-radio-group v-model:value="testCase.match_rule">
                <a-radio value="exact">完全匹配</a-radio>
                <a-radio value="regex">正则匹配</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
          
          <a-col :span="12">
            <a-form-item label="对学生可见">
              <a-switch :checked="!testCase.is_hidden" @change="(val) => testCase.is_hidden = !val" />
              <span class="visibility-hint">
                {{ testCase.is_hidden ? '学生不可查看此测试集' : '学生可查看输入和预期结果' }}
              </span>
            </a-form-item>
          </a-col>
        </a-row>
      </a-card>
    </div>

    <div class="test-case-hint">
      <a-alert
        message="测试集说明"
        type="info"
        show-icon
      >
        <template #description>
          <ul>
            <li>测试集用于自动评测学生代码，输入通过标准输入流传入</li>
            <li>完全匹配：实际输出与预期输出必须完全相同（包括空格、换行）</li>
            <li>正则匹配：使用正则表达式匹配输出结果</li>
            <li>可设置 {{ minCount }}-{{ maxCount }} 个测试集</li>
          </ul>
        </template>
      </a-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import type { TestCase } from '@/api/practice';

const props = withDefaults(defineProps<{
  modelValue?: TestCase[];
  minCount?: number;
  maxCount?: number;
}>(), {
  minCount: 1,
  maxCount: 10
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: TestCase[]): void;
}>();

// 使用v-model
const testCases = computed({
  get: () => props.modelValue || [{
    input_data: '',
    expected_output: '',
    is_hidden: false,
    match_rule: 'exact'
  }],
  set: (value) => emit('update:modelValue', value)
});

// 全部可见状态
const allVisible = computed({
  get: () => testCases.value.every(tc => !tc.is_hidden),
  set: (value) => {
    testCases.value = testCases.value.map(tc => ({
      ...tc,
      is_hidden: !value
    }));
  }
});

// 切换全部可见
const toggleAllVisible = (e: any) => {
  const visible = e.target.checked;
  testCases.value = testCases.value.map(tc => ({
    ...tc,
    is_hidden: !visible
  }));
};

// 添加测试集
const addTestCase = () => {
  if (testCases.value.length >= props.maxCount) return;
  
  testCases.value = [...testCases.value, {
    input_data: '',
    expected_output: '',
    is_hidden: false,
    match_rule: 'exact'
  }];
};

// 删除测试集
const removeTestCase = (index: number) => {
  if (testCases.value.length <= props.minCount) return;
  
  testCases.value = testCases.value.filter((_, i) => i !== index);
};
</script>

<style scoped>
.test-case-editor {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.test-case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.test-case-header h4 {
  margin: 0;
}

.test-case-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.test-case-list {
  margin-bottom: 16px;
}

.visibility-hint {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.test-case-hint ul {
  margin: 8px 0;
  padding-left: 20px;
}

.test-case-hint li {
  margin: 4px 0;
  color: rgba(0, 0, 0, 0.65);
}

:deep(.ant-form-item) {
  margin-bottom: 8px;
}

:deep(.ant-form-item-label) {
  padding-bottom: 4px;
}
</style>