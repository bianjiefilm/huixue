<template>
  <div class="essay-task">
    <div class="task-header">
      <div class="task-meta">
        <a-tag :color="config.color">
          <template #icon>
            <FileTextOutlined />
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
      <div class="essay-question">
        <div class="question-content">
          <h3>题目要求</h3>
          <p>{{ task.question }}</p>
        </div>

        <div v-if="task.wordLimit" class="word-limit">
          <a-alert
            :message="`字数限制: ${wordCount}${task.wordLimit.min ? `/${task.wordLimit.min}` : ''}-${task.wordLimit.max || '不限'}`"
            :type="isWordLimitValid ? 'info' : 'warning'"
            show-icon
          />
        </div>

        <div v-if="task.gradingCriteria.length > 0" class="grading-criteria">
          <h4>评分标准</h4>
          <ul>
            <li v-for="criteria in task.gradingCriteria" :key="criteria">
              {{ criteria }}
            </li>
          </ul>
        </div>
      </div>

      <div class="essay-answer">
        <div class="answer-header">
          <h3>我的答案</h3>
          <div class="answer-meta">
            <span class="word-count">字数: {{ wordCount }}</span>
            <a-button
              v-if="!isPreview"
              type="text"
              size="small"
              @click="clearAnswer"
            >
              清空
            </a-button>
          </div>
        </div>

        <div class="editor-container">
          <RichTextEditor
            v-model:content="answer"
            :readonly="isPreview"
            :placeholder="'请在这里输入你的答案...'"
            :min-height="200"
            @change="handleContentChange"
          />
        </div>
      </div>

      <div v-if="isTeacher && task.sampleAnswer" class="sample-answer">
        <a-collapse>
          <a-collapse-panel key="1" header="参考答案（教师可见）">
            <div class="sample-content" v-html="task.sampleAnswer"></div>
          </a-collapse-panel>
        </a-collapse>
      </div>

      <div class="task-actions">
        <a-space>
          <a-button
            v-if="!isPreview"
            type="primary"
            :loading="submitting"
            :disabled="!isAnswerValid"
            @click="submitTask"
          >
            提交答案
          </a-button>
          <a-button
            v-if="!isPreview"
            @click="saveDraft"
          >
            保存草稿
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 教师评分区域 -->
    <div v-if="isTeacher && submission && submission.status === 'completed'" class="teacher-grading">
      <a-card title="教师评分" class="grading-card">
        <div class="grading-form">
          <a-form layout="vertical">
            <a-form-item label="分数">
              <a-input-number
                v-model:value="teacherScore"
                :min="0"
                :max="task.points"
                :precision="1"
                style="width: 120px"
                @change="calculateGrade"
              />
              <span class="max-score"> / {{ task.points }}分</span>
            </a-form-item>

            <a-form-item label="评语">
              <a-textarea
                v-model:value="teacherComments"
                :rows="4"
                placeholder="请输入评语..."
              />
            </a-form-item>

            <a-form-item>
              <a-space>
                <a-button
                  type="primary"
                  :loading="grading"
                  @click="submitGrade"
                >
                  提交评分
                </a-button>
                <a-button @click="previewGrade">
                  预览评分
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </div>

        <div v-if="gradePreview" class="grade-preview">
          <a-divider />
          <h4>评分预览</h4>
          <div class="preview-content">
            <p><strong>得分：</strong>{{ teacherScore }}/{{ task.points }}分</p>
            <p><strong>评语：</strong>{{ teacherComments || '暂无评语' }}</p>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 学生查看评分结果 -->
    <div v-if="!isTeacher && submission && submission.status === 'completed'" class="grade-result">
      <a-card title="评分结果" class="result-card">
        <div class="result-content">
          <div class="score-display">
            <div class="score-value">{{ submission.score || 0 }}</div>
            <div class="score-max">/{{ task.points }}</div>
            <div class="score-label">分</div>
          </div>

          <div v-if="(submission as any).teacherComments" class="teacher-feedback">
            <h4>教师评语</h4>
            <p>{{ (submission as any).teacherComments }}</p>
          </div>

          <div class="submission-info">
            <p><strong>提交时间：</strong>{{ formatDate(submission.submittedAt) }}</p>
            <p><strong>评分时间：</strong>{{ formatDate((submission as any).evaluatedAt) }}</p>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import type { EssayTask, EssaySubmission, TaskComponentProps } from '@/types/task'
import { TASK_TYPE_CONFIGS, TASK_DIFFICULTY_CONFIGS } from '@/types/task'
import { FileTextOutlined } from '@ant-design/icons-vue'
import RichTextEditor from '../common/RichTextEditor.vue'

interface Props extends TaskComponentProps<EssayTask> {}

const props = withDefaults(defineProps<Props>(), {
  isPreview: false,
  isTeacher: false
})

const emit = defineEmits<{
  submit: [submission: Partial<EssaySubmission>]
  save: [draft: Partial<EssaySubmission>]
}>()

// 响应式数据
const answer = ref('')
const submitting = ref(false)
const grading = ref(false)
const teacherScore = ref<number | undefined>()
const teacherComments = ref('')
const gradePreview = ref(false)

// 计算属性
const config = computed(() => TASK_TYPE_CONFIGS[props.task.type])
const difficultyConfig = computed(() => TASK_DIFFICULTY_CONFIGS[props.task.difficulty])

const wordCount = computed(() => {
  // 简单计算字数，实际应该解析HTML内容
  return answer.value.replace(/<[^>]*>/g, '').trim().length
})

const isWordLimitValid = computed(() => {
  if (!props.task.wordLimit) return true

  const count = wordCount.value
  const min = props.task.wordLimit.min || 0
  const max = props.task.wordLimit.max

  return count >= min && (!max || count <= max)
})

const isAnswerValid = computed(() => {
  return answer.value.trim().length > 0 && isWordLimitValid.value
})

// 初始化数据
onMounted(() => {
  if (props.submission) {
    const essaySubmission = props.submission as EssaySubmission
    answer.value = essaySubmission.answer

    if (props.isTeacher && essaySubmission.teacherScore !== undefined) {
      teacherScore.value = essaySubmission.teacherScore
      teacherComments.value = essaySubmission.teacherComments || ''
    }
  }
})

// 监听答案变化
watch(() => props.submission, (newSubmission) => {
  if (newSubmission) {
    const essaySubmission = newSubmission as EssaySubmission
    answer.value = essaySubmission.answer

    if (props.isTeacher && essaySubmission.teacherScore !== undefined) {
      teacherScore.value = essaySubmission.teacherScore
      teacherComments.value = essaySubmission.teacherComments || ''
    }
  }
}, { deep: true })

// 方法
const handleContentChange = (content: string) => {
  answer.value = content
}

const clearAnswer = () => {
  Modal.confirm({
    title: '确认清空',
    content: '确定要清空所有内容吗？此操作无法撤销。',
    onOk: () => {
      answer.value = ''
    }
  })
}

const saveDraft = () => {
  if (!answer.value.trim()) {
    message.warning('答案为空，无法保存草稿')
    return
  }

  const draft: Partial<EssaySubmission> = {
    taskId: props.task.id,
    answer: answer.value,
    wordCount: wordCount.value
  }

  if (props.onSave) {
    props.onSave(draft)
  }

  message.success('草稿已保存')
}

const submitTask = async () => {
  if (!isAnswerValid.value) {
    if (!isWordLimitValid.value) {
      message.error('答案字数不符合要求，请检查后重新提交')
    } else {
      message.error('请先输入答案')
    }
    return
  }

  submitting.value = true

  try {
    const submission: Partial<EssaySubmission> = {
      taskId: props.task.id,
      status: 'completed',
      answer: answer.value,
      wordCount: wordCount.value,
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

const calculateGrade = () => {
  if (teacherScore.value !== undefined) {
    const percentage = (teacherScore.value / props.task.points) * 100
    console.log(`评分: ${teacherScore.value}/${props.task.points} (${percentage.toFixed(1)}%)`)
  }
}

const submitGrade = async () => {
  if (teacherScore.value === undefined || teacherScore.value < 0 || teacherScore.value > props.task.points) {
    message.error('请输入有效的分数')
    return
  }

  grading.value = true

  try {
    // 这里应该调用API提交评分
    // await submitGradeAPI(props.submission!.id, {
    //   score: teacherScore.value,
    //   comments: teacherComments.value
    // });

    message.success('评分提交成功')

    // 更新本地数据
    if (props.submission) {
      (props.submission as EssaySubmission).teacherScore = teacherScore.value
      (props.submission as EssaySubmission).teacherComments = teacherComments.value
    }
  } catch (error) {
    console.error('评分提交失败:', error)
    message.error('评分提交失败，请重试')
  } finally {
    grading.value = false
  }
}

const previewGrade = () => {
  gradePreview.value = true
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '未评分'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.essay-task {
  max-width: 1000px;
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

.essay-question {
  margin-bottom: 32px;
}

.question-content h3 {
  margin: 0 0 12px 0;
  color: #f3f4f6;
}

.question-content p {
  margin: 0;
  line-height: 1.6;
  color: #4b5563;
}

.word-limit {
  margin: 16px 0;
}

.grading-criteria {
  margin-top: 16px;
}

.grading-criteria h4 {
  margin: 0 0 8px 0;
  color: #f3f4f6;
}

.grading-criteria ul {
  margin: 0;
  padding-left: 20px;
}

.grading-criteria li {
  margin-bottom: 4px;
  color: #4b5563;
}

.essay-answer {
  margin-bottom: 24px;
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.answer-header h3 {
  margin: 0;
  color: #f3f4f6;
}

.answer-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.word-count {
  font-size: 14px;
  color: #6b7280;
}

.editor-container {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  overflow: hidden;
}

.sample-answer {
  margin-bottom: 24px;
}

.sample-content {
  padding: 16px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.task-actions {
  text-align: center;
}

.teacher-grading {
  margin-top: 24px;
}

.grading-card {
  border-left: 4px solid #faad14;
}

.grading-form {
  max-width: 600px;
}

.max-score {
  margin-left: 8px;
  color: #6b7280;
}

.grade-preview {
  margin-top: 24px;
}

.grade-result {
  margin-top: 24px;
}

.result-card {
  border-left: 4px solid #52c41a;
}

.result-content {
  text-align: center;
}

.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 24px;
}

.score-value {
  font-size: 48px;
  font-weight: bold;
  color: #1890ff;
}

.score-max {
  font-size: 24px;
  color: #6b7280;
}

.score-label {
  margin-left: 8px;
  font-size: 18px;
  color: #6b7280;
}

.teacher-feedback {
  margin-bottom: 24px;
  text-align: left;
}

.teacher-feedback h4 {
  margin: 0 0 8px 0;
  color: #f3f4f6;
}

.teacher-feedback p {
  margin: 0;
  color: #4b5563;
  line-height: 1.6;
}

.submission-info {
  text-align: left;
  color: #6b7280;
  font-size: 14px;
}

.submission-info p {
  margin: 4px 0;
}

@media (max-width: 768px) {
  .answer-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .score-value {
    font-size: 36px;
  }

  .score-max {
    font-size: 18px;
  }

  .task-meta {
    flex-wrap: wrap;
  }
}
</style>
