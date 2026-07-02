<template>
  <div class="judge-task">
    <div class="task-header">
      <div class="task-meta">
        <a-tag :color="config.color">
          <template #icon>
            <CheckCircleOutlined />
          </template>
          {{ config.name }}
        </a-tag>
        <a-tag :color="difficultyConfig.color">
          {{ difficultyConfig.name }}
        </a-tag>
        <span class="points">{{ task.points }}分</span>
      </div>
      <div class="task-title">{{ task.title }}</div>
    </div>

    <div class="task-content">
      <div class="question-content">
        <p>{{ task.question }}</p>
      </div>

      <div class="options-section">
        <a-radio-group
          v-model:value="selectedAnswer"
          :disabled="isPreview || submission?.status === 'completed'"
          @change="handleAnswerChange"
        >
          <a-radio value="true" class="option-item">
            <span class="option-label">A.</span>
            <span class="option-text">正确</span>
          </a-radio>
          <a-radio value="false" class="option-item">
            <span class="option-label">B.</span>
            <span class="option-text">错误</span>
          </a-radio>
        </a-radio-group>
      </div>

      <div v-if="task.explanation && showExplanation" class="task-explanation">
        <a-alert
          message="答案解析"
          :description="task.explanation"
          type="info"
          show-icon
        />
      </div>

      <div class="task-actions">
        <a-space>
          <a-button
            v-if="!isPreview"
            type="primary"
            :loading="submitting"
            :disabled="!selectedAnswer"
            @click="submitTask"
          >
            提交答案
          </a-button>
          <a-button v-if="task.explanation" @click="showExplanation = !showExplanation">
            {{ showExplanation ? '隐藏' : '查看' }}解析
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 提交结果 -->
    <div v-if="submission && submission.status === 'completed'" class="submission-result">
      <a-card size="small" class="result-card">
        <template #title>
          <div class="result-header">
            <span>提交结果</span>
            <a-tag :color="submission.score === task.points ? 'success' : 'error'">
              {{ submission.score }}/{{ task.points }}分
            </a-tag>
          </div>
        </template>

        <div class="result-content">
          <div class="answer-info">
            <p><strong>你的答案：</strong>{{ getAnswerText(selectedAnswer) }}</p>
            <p><strong>正确答案：</strong>{{ getAnswerText(task.correctAnswer) }}</p>
            <a-tag
              :color="selectedAnswer === task.correctAnswer.toString() ? 'success' : 'error'"
              size="small"
            >
              {{ selectedAnswer === task.correctAnswer.toString() ? '回答正确' : '回答错误' }}
            </a-tag>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { JudgeTask, JudgeSubmission, TaskComponentProps } from '@/types/task'
import { TASK_TYPE_CONFIGS, TASK_DIFFICULTY_CONFIGS } from '@/types/task'
import { CheckCircleOutlined } from '@ant-design/icons-vue'

interface Props extends TaskComponentProps<JudgeTask> {}

const props = withDefaults(defineProps<Props>(), {
  isPreview: false,
  isTeacher: false
})

const emit = defineEmits<{
  submit: [submission: Partial<JudgeSubmission>]
  save: [draft: Partial<JudgeSubmission>]
}>()

// 响应式数据
const selectedAnswer = ref<string>('')
const showExplanation = ref(false)
const submitting = ref(false)

// 计算属性
const config = computed(() => TASK_TYPE_CONFIGS[props.task.type])
const difficultyConfig = computed(() => TASK_DIFFICULTY_CONFIGS[props.task.difficulty])

// 初始化数据
onMounted(() => {
  if (props.submission) {
    const judgeSubmission = props.submission as JudgeSubmission
    selectedAnswer.value = judgeSubmission.answer.toString()
  }
})

// 方法
const handleAnswerChange = () => {
  // 自动保存草稿
  if (props.onSave) {
    const draft: Partial<JudgeSubmission> = {
      taskId: props.task.id,
      answer: selectedAnswer.value === 'true'
    }
    props.onSave(draft)
  }
}

const submitTask = async () => {
  if (!selectedAnswer.value) {
    message.warning('请选择答案后再提交')
    return
  }

  submitting.value = true

  try {
    const answer = selectedAnswer.value === 'true'
    const isCorrect = answer === props.task.correctAnswer
    const score = isCorrect ? props.task.points : 0

    const submission: Partial<JudgeSubmission> = {
      taskId: props.task.id,
      status: 'completed',
      answer,
      score,
      maxScore: props.task.points,
      submittedAt: new Date().toISOString()
    }

    if (props.onSubmit) {
      await props.onSubmit(submission)
    }

    message.success(isCorrect ? '回答正确！' : '回答错误，请查看解析')
  } catch (error) {
    console.error('提交失败:', error)
    message.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

const getAnswerText = (answer: boolean | string): string => {
  if (typeof answer === 'string') {
    return answer === 'true' ? '正确' : '错误'
  }
  return answer ? '正确' : '错误'
}
</script>

<style scoped>
.judge-task {
  max-width: 800px;
}

.task-header {
  margin-bottom: 24px;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.points {
  font-weight: 500;
  color: #1890ff;
}

.task-title {
  font-size: 18px;
  font-weight: 500;
  color: #f3f4f6;
}

.task-content {
  background: #fafafa;
  padding: 24px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.question-content {
  margin-bottom: 24px;
}

.question-content p {
  margin: 0;
  line-height: 1.6;
  color: #f3f4f6;
  font-size: 16px;
}

.options-section {
  margin-bottom: 24px;
}

.option-item {
  display: block;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.option-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.option-item.ant-radio-wrapper-checked {
  border-color: #1890ff;
  background: #f0f8ff;
}

.option-label {
  font-weight: 500;
  color: #f3f4f6;
  margin-right: 8px;
}

.option-text {
  color: #4b5563;
}

.task-explanation {
  margin-bottom: 24px;
}

.task-actions {
  text-align: center;
}

.submission-result {
  margin-top: 24px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-content {
  margin-top: 16px;
}

.answer-info p {
  margin: 8px 0;
  color: #4b5563;
}

.answer-info p:first-child {
  margin-top: 0;
}

@media (max-width: 768px) {
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .option-item {
    padding: 10px 12px;
  }

  .option-text {
    font-size: 14px;
  }
}
</style>

