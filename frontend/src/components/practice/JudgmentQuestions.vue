<template>
  <div class="judgment-questions-editor">
    <div class="questions-header">
      <h4>判断题设置</h4>
      <a-button
        type="primary"
        size="small"
        @click="addQuestion"
        :disabled="questions.length >= maxCount"
      >
        <template #icon><PlusOutlined /></template>
        添加判断题
      </a-button>
    </div>

    <div class="questions-list">
      <a-card
        v-for="(question, index) in questions"
        :key="index"
        :title="`判断题 ${index + 1}`"
        size="small"
        style="margin-bottom: 16px"
      >
        <template #extra>
          <a-button
            type="text"
            danger
            size="small"
            @click="removeQuestion(index)"
            :disabled="questions.length <= minCount"
          >
            <template #icon><DeleteOutlined /></template>
          </a-button>
        </template>

        <a-form-item label="题干" required>
          <MarkdownEditor
            v-model:value="question.question_content"
            :height="200"
            placeholder="请输入判断题题干，支持Markdown格式"
          />
        </a-form-item>

        <a-form-item label="正确答案" required>
          <a-radio-group v-model:value="question.correct_answer">
            <a-radio :value="true">正确</a-radio>
            <a-radio :value="false">错误</a-radio>
          </a-radio-group>
          <div class="form-hint">
            设置本题的正确答案是"正确"还是"错误"
          </div>
        </a-form-item>

        <a-form-item label="答案解析">
          <a-textarea
            v-model:value="question.explanation"
            placeholder="可选：输入答案解析，帮助学生理解"
            :auto-size="{ minRows: 2, maxRows: 4 }"
          />
        </a-form-item>

        <a-form-item label="分值">
          <a-input-number
            v-model:value="question.score"
            :min="1"
            :max="100"
            addon-after="分"
            style="width: 120px"
          />
        </a-form-item>
      </a-card>
    </div>

    <div class="questions-hint">
      <a-alert
        message="判断题说明"
        type="info"
        show-icon
      >
        <template #description>
          <ul>
            <li>每个关卡可设置 {{ minCount }}-{{ maxCount }} 道判断题</li>
            <li>题干支持Markdown格式，可包含代码、图片等</li>
            <li>学生需要判断题目描述是"正确"还是"错误"</li>
            <li>建议为每道题设置答案解析，帮助学生理解</li>
          </ul>
        </template>
      </a-alert>
    </div>

    <div class="questions-summary">
      <a-statistic
        title="题目总数"
        :value="questions.length"
        suffix="题"
        style="margin-right: 24px; display: inline-block"
      />
      <a-statistic
        title="总分值"
        :value="totalScore"
        suffix="分"
        style="display: inline-block"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import MarkdownEditor from './MarkdownEditor.vue';

export interface JudgmentQuestion {
  question_content: string;
  correct_answer: boolean;
  explanation?: string;
  score: number;
}

const props = withDefaults(defineProps<{
  modelValue?: JudgmentQuestion[];
  minCount?: number;
  maxCount?: number;
}>(), {
  minCount: 1,
  maxCount: 10
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: JudgmentQuestion[]): void;
}>();

// 使用v-model
const questions = computed({
  get: () => props.modelValue || [{
    question_content: '',
    correct_answer: true,
    explanation: '',
    score: 10
  }],
  set: (value) => emit('update:modelValue', value)
});

// 计算总分
const totalScore = computed(() => {
  return questions.value.reduce((sum, q) => sum + q.score, 0);
});

// 添加判断题
const addQuestion = () => {
  if (questions.value.length >= props.maxCount) {
    message.warning(`最多只能添加 ${props.maxCount} 道判断题`);
    return;
  }

  questions.value = [...questions.value, {
    question_content: '',
    correct_answer: true,
    explanation: '',
    score: 10
  }];
};

// 删除判断题
const removeQuestion = (index: number) => {
  if (questions.value.length <= props.minCount) return;
  
  questions.value = questions.value.filter((_, i) => i !== index);
};
</script>

<style scoped>
.judgment-questions-editor {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.questions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.questions-header h4 {
  margin: 0;
}

.questions-list {
  margin-bottom: 16px;
}

.form-hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.questions-hint ul {
  margin: 8px 0;
  padding-left: 20px;
}

.questions-hint li {
  margin: 4px 0;
  color: rgba(0, 0, 0, 0.65);
}

.questions-summary {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #d9d9d9;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

:deep(.ant-form-item-label) {
  padding-bottom: 4px;
}
</style>