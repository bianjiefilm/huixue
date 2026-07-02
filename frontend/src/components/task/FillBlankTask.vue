<template>
  <div class="fill-blank-task">
    <div class="task-header">
      <div class="task-meta">
        <a-tag :color="config.color">
          <template #icon>
            <FormOutlined />
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
      <div class="fill-blank-content">
        <p v-for="(segment, index) in contentSegments" :key="index" class="content-segment">
          <span v-if="segment.type === 'text'">{{ segment.content }}</span>
          <a-input
            v-else-if="segment.type === 'blank'"
            v-model:value="answers[segment.blankId]"
            :placeholder="segment.placeholder"
            :maxlength="100"
            class="blank-input"
            @change="handleAnswerChange"
          />
        </p>
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
            <a-tag :color="submission.score === task.points ? 'success' : 'warning'">
              {{ submission.score }}/{{ task.points }}分
            </a-tag>
          </div>
        </template>

        <div class="blank-results">
          <div
            v-for="blank in task.blanks"
            :key="blank.id"
            class="blank-result-item"
          >
            <div class="blank-label">{{ blank.placeholder }}:</div>
            <div class="blank-answer">
              <span class="student-answer">{{ getStudentAnswer(blank.id) }}</span>
              <a-tag
                v-if="getBlankResult(blank.id)"
                :color="getBlankResult(blank.id)?.isCorrect ? 'success' : 'error'"
                size="small"
              >
                {{ getBlankResult(blank.id)?.isCorrect ? '正确' : '错误' }}
              </a-tag>
            </div>
            <div v-if="isTeacher && blank.correctAnswers.length > 0" class="correct-answer">
              正确答案: {{ blank.correctAnswers.join(' 或 ') }}
            </div>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { FillBlankTask, FillBlankSubmission, TaskComponentProps } from '@/types/task'
import { TASK_TYPE_CONFIGS, TASK_DIFFICULTY_CONFIGS } from '@/types/task'
import { CheckCircleOutlined, FormOutlined } from '@ant-design/icons-vue'

interface Props extends TaskComponentProps<FillBlankTask> {}

const props = withDefaults(defineProps<Props>(), {
  isPreview: false,
  isTeacher: false
})

const emit = defineEmits<{
  submit: [submission: Partial<FillBlankSubmission>]
  save: [draft: Partial<FillBlankSubmission>]
}>()

// 响应式数据
const answers = ref<Record<string, string>>({})
const showExplanation = ref(false)
const submitting = ref(false)

// 计算属性
const config = computed(() => TASK_TYPE_CONFIGS[props.task.type])
const difficultyConfig = computed(() => TASK_DIFFICULTY_CONFIGS[props.task.difficulty])

const contentSegments = computed(() => {
  const segments: Array<{ type: 'text' | 'blank'; content?: string; placeholder?: string; blankId?: string }> = []
  let content = props.task.content
  let lastIndex = 0

  // 找到所有的占位符
  props.task.blanks.forEach(blank => {
    const placeholder = `__${blank.placeholder}__`
    const index = content.indexOf(placeholder, lastIndex)

    if (index !== -1) {
      // 添加占位符前的文本
      if (index > lastIndex) {
        segments.push({
          type: 'text',
          content: content.slice(lastIndex, index)
        })
      }

      // 添加输入框
      segments.push({
        type: 'blank',
        placeholder: blank.placeholder,
        blankId: blank.id
      })

      lastIndex = index + placeholder.length
    }
  })

  // 添加剩余的文本
  if (lastIndex < content.length) {
    segments.push({
      type: 'text',
      content: content.slice(lastIndex)
    })
  }

  return segments
})

// 初始化答案
onMounted(() => {
  if (props.submission) {
    const fillBlankSubmission = props.submission as FillBlankSubmission
    fillBlankSubmission.answers.forEach(answer => {
      answers.value[answer.blankId] = answer.answer
    })
  }
})

// 方法
const handleAnswerChange = () => {
  // 自动保存草稿
  if (props.onSave) {
    const draft: Partial<FillBlankSubmission> = {
      taskId: props.task.id,
      answers: props.task.blanks.map(blank => ({
        blankId: blank.id,
        answer: answers.value[blank.id] || ''
      }))
    }
    props.onSave(draft)
  }
}

const submitTask = async () => {
  // 验证答案
  const hasAllAnswers = props.task.blanks.every(blank => answers.value[blank.id]?.trim())

  if (!hasAllAnswers) {
    message.warning('请填写所有空白处后再提交')
    return
  }

  submitting.value = true

  try {
    const submission: Partial<FillBlankSubmission> = {
      taskId: props.task.id,
      status: 'completed',
      answers: props.task.blanks.map(blank => ({
        blankId: blank.id,
        answer: answers.value[blank.id].trim()
      })),
      submittedAt: new Date().toISOString(),
      maxScore: props.task.points
    }

    if (props.onSubmit) {
      await props.onSubmit(submission)
    }

    message.success('答案提交成功！')
  } catch (error) {
    console.error('提交失败:', error)
    message.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

const getStudentAnswer = (blankId: string): string => {
  if (props.submission) {
    const fillBlankSubmission = props.submission as FillBlankSubmission
    const answer = fillBlankSubmission.answers.find(a => a.blankId === blankId)
    return answer?.answer || ''
  }
  return answers.value[blankId] || ''
}

const getBlankResult = (blankId: string) => {
  if (props.submission) {
    const fillBlankSubmission = props.submission as FillBlankSubmission
    return fillBlankSubmission.answers.find(a => a.blankId === blankId)
  }
  return null
}
</script>

<style scoped>
.fill-blank-task {
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

.fill-blank-content {
  margin-bottom: 24px;
}

.content-segment {
  display: inline;
  margin: 0;
  line-height: 2;
  font-size: 16px;
}

.blank-input {
  width: 120px;
  margin: 0 4px;
  display: inline-block;
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

.blank-results {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.blank-result-item {
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.blank-label {
  font-weight: 500;
  color: #f3f4f6;
  margin-bottom: 8px;
}

.blank-answer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.student-answer {
  font-style: italic;
  color: #666;
  flex: 1;
}

.correct-answer {
  font-size: 12px;
  color: #52c41a;
  font-weight: 500;
}

@media (max-width: 768px) {
  .content-segment {
    font-size: 14px;
  }

  .blank-input {
    width: 100px;
  }

  .task-meta {
    flex-wrap: wrap;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
