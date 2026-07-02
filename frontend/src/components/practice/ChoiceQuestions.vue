<template>
  <div class="choice-questions-editor">
    <div class="questions-header">
      <h4>选择题设置</h4>
      <a-button
        type="primary"
        size="small"
        @click="addQuestion"
        :disabled="questions.length >= maxCount"
      >
        <template #icon><PlusOutlined /></template>
        添加选择题
      </a-button>
    </div>

    <div class="questions-list">
      <a-card
        v-for="(question, index) in questions"
        :key="index"
        :title="`选择题 ${index + 1}`"
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

        <a-form-item label="题型" required>
          <a-radio-group v-model:value="question.question_type">
            <a-radio value="single">单选题</a-radio>
            <a-radio value="multiple">多选题</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="题干" required>
          <MarkdownEditor
            v-model:value="question.question_content"
            :height="200"
            placeholder="请输入选择题题干，支持Markdown格式"
          />
        </a-form-item>

        <a-form-item label="选项" required>
          <div class="options-container">
            <div
              v-for="(option, optIndex) in question.options"
              :key="optIndex"
              class="option-item"
            >
              <a-input-group compact>
                <a-input
                  style="width: 60px"
                  :value="getOptionLabel(optIndex)"
                  disabled
                />
                <a-input
                  v-model:value="option.text"
                  placeholder="请输入选项内容"
                  style="flex: 1"
                />
                <a-button
                  type="text"
                  danger
                  @click="removeOption(index, optIndex)"
                  :disabled="question.options.length <= 2"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-input-group>
            </div>
            <a-button
              type="dashed"
              block
              @click="addOption(index)"
              :disabled="question.options.length >= 10"
            >
              <template #icon><PlusOutlined /></template>
              添加选项
            </a-button>
          </div>
        </a-form-item>

        <a-form-item label="正确答案" required>
          <div v-if="question.question_type === 'single'">
            <a-radio-group
              :value="getSingleAnswerValue(index)"
              @change="handleSingleAnswerChange(index, $event)"
            >
              <a-radio
                v-for="(option, optIndex) in question.options"
                :key="optIndex"
                :value="optIndex"
              >
                {{ option.key }}
              </a-radio>
            </a-radio-group>
          </div>
          <div v-else>
            <a-checkbox-group
              :value="getMultipleAnswerValue(index)"
              @change="handleMultipleAnswerChange(index, $event)"
            >
              <a-checkbox
                v-for="(option, optIndex) in question.options"
                :key="optIndex"
                :value="optIndex"
              >
                {{ option.key }}
              </a-checkbox>
            </a-checkbox-group>
            <div class="form-hint">多选题请选择所有正确答案</div>
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
          <span v-if="question.question_type === 'multiple'" class="score-hint">
            多选题建议设置较高分值
          </span>
        </a-form-item>
      </a-card>
    </div>

    <div class="questions-hint">
      <a-alert
        message="选择题说明"
        type="info"
        show-icon
      >
        <template #description>
          <ul>
            <li>每个关卡可设置 {{ minCount }}-{{ maxCount }} 道选择题</li>
            <li>每道题可设置 2-10 个选项</li>
            <li>单选题只有一个正确答案，多选题可有多个正确答案</li>
            <li>多选题评分规则：全部选对得满分，选错或漏选不得分</li>
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
import { ref, computed, watch } from 'vue';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import MarkdownEditor from './MarkdownEditor.vue';

export interface ChoiceOption {
  key: string;
  text: string;
  is_correct: boolean;
}

export interface ChoiceQuestion {
  question_type: 'single' | 'multiple';
  question_content: string;
  options: ChoiceOption[];
  explanation?: string;
  score: number;
}

const props = withDefaults(defineProps<{
  modelValue?: ChoiceQuestion[];
  minCount?: number;
  maxCount?: number;
}>(), {
  minCount: 1,
  maxCount: 10
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: ChoiceQuestion[]): void;
}>();

// 使用v-model
const questions = computed({
  get: () => props.modelValue || [{
    question_type: 'single',
    question_content: '',
    options: [
      { key: 'A', text: '', is_correct: true },
      { key: 'B', text: '', is_correct: false },
      { key: 'C', text: '', is_correct: false },
      { key: 'D', text: '', is_correct: false }
    ],
    explanation: '',
    score: 10
  }],
  set: (value) => emit('update:modelValue', value)
});

// 计算总分
const totalScore = computed(() => {
  return questions.value.reduce((sum, q) => sum + q.score, 0);
});

// 获取选项标签（A、B、C...）
const getOptionLabel = (index: number) => {
  return String.fromCharCode(65 + index);
};

// 获取单选题当前选中的值
const getSingleAnswerValue = (questionIndex: number): number | undefined => {
  const question = questions.value[questionIndex];
  if (!question) return undefined;
  const correctIndex = question.options.findIndex(opt => opt.is_correct);
  return correctIndex >= 0 ? correctIndex : undefined;
};

// 获取多选题当前选中的值
const getMultipleAnswerValue = (questionIndex: number): number[] => {
  const question = questions.value[questionIndex];
  if (!question) return [];
  return question.options
    .map((opt, index) => opt.is_correct ? index : -1)
    .filter(index => index >= 0);
};

// 添加选择题
const addQuestion = () => {
  if (questions.value.length >= props.maxCount) return;
  
  questions.value = [...questions.value, {
    question_type: 'single',
    question_content: '',
    options: [
      { key: 'A', text: '', is_correct: true },
      { key: 'B', text: '', is_correct: false },
      { key: 'C', text: '', is_correct: false },
      { key: 'D', text: '', is_correct: false }
    ],
    explanation: '',
    score: 10
  }];
};

// 删除选择题
const removeQuestion = (index: number) => {
  if (questions.value.length <= props.minCount) return;
  
  questions.value = questions.value.filter((_, i) => i !== index);
};

// 添加选项
const addOption = (questionIndex: number) => {
  const question = questions.value[questionIndex];
  if (question.options.length >= 10) {
    message.warning('每道题最多10个选项');
    return;
  }
  
  const nextKey = String.fromCharCode(65 + question.options.length);
  question.options.push({ key: nextKey, text: '', is_correct: false });
};

// 删除选项
const removeOption = (questionIndex: number, optionIndex: number) => {
  const question = questions.value[questionIndex];
  if (question.options.length <= 2) {
    message.warning('每道题至少需要2个选项');
    return;
  }
  
  // 删除选项
  question.options.splice(optionIndex, 1);
  
  // 重新设置选项标签
  question.options.forEach((option, index) => {
    option.key = String.fromCharCode(65 + index);
  });
  
  // 如果删除的是唯一正确答案，设置第一个为正确答案
  const hasCorrectAnswer = question.options.some(opt => opt.is_correct);
  if (!hasCorrectAnswer && question.options.length > 0) {
    question.options[0].is_correct = true;
  }
};

// 处理单选答案变化
const handleSingleAnswerChange = (questionIndex: number, event: any) => {
  const question = questions.value[questionIndex];
  const selectedIndex = event.target.value;
  
  // 清除所有正确答案
  question.options.forEach(opt => opt.is_correct = false);
  // 设置选中的为正确答案
  if (question.options[selectedIndex]) {
    question.options[selectedIndex].is_correct = true;
  }
};

// 处理多选答案变化
const handleMultipleAnswerChange = (questionIndex: number, checkedValues: number[]) => {
  const question = questions.value[questionIndex];
  
  // 清除所有正确答案
  question.options.forEach(opt => opt.is_correct = false);
  // 设置选中的为正确答案
  checkedValues.forEach(index => {
    if (question.options[index]) {
      question.options[index].is_correct = true;
    }
  });
};

// 监听题型变化
watch(questions, (newQuestions) => {
  newQuestions.forEach(question => {
    if (question.question_type === 'single') {
      // 单选题只保留一个正确答案
      const correctOptions = question.options.filter(opt => opt.is_correct);
      if (correctOptions.length > 1) {
        // 清除所有正确答案，只保留第一个
        question.options.forEach(opt => opt.is_correct = false);
        const firstCorrectIndex = question.options.findIndex(opt => correctOptions[0] === opt);
        if (firstCorrectIndex >= 0) {
          question.options[firstCorrectIndex].is_correct = true;
        }
      }
    }
  });
}, { deep: true });
</script>

<style scoped>
.choice-questions-editor {
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

.options-container {
  width: 100%;
}

.option-item {
  margin-bottom: 8px;
}

.form-hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.score-hint {
  margin-left: 8px;
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

:deep(.ant-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.ant-radio-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>