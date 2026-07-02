<template>
  <div class="file-upload-task">
    <div class="task-header">
      <div class="task-meta">
        <a-tag :color="config.color">
          <template #icon>
            <UploadOutlined />
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
      <div class="task-instructions">
        <h3>作业要求</h3>
        <p>{{ task.instructions }}</p>

        <div class="file-requirements">
          <h4>文件要求</h4>
          <div class="requirements-list">
            <div class="requirement-item">
              <span class="label">允许格式：</span>
              <span class="value">{{ allowedTypesText }}</span>
            </div>
            <div class="requirement-item">
              <span class="label">文件大小：</span>
              <span class="value">最大 {{ formatFileSize(task.fileRequirements.maxSize) }}</span>
            </div>
            <div class="requirement-item">
              <span class="label">文件数量：</span>
              <span class="value">最多 {{ task.fileRequirements.maxFiles }} 个文件</span>
            </div>
          </div>
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

      <!-- 文件上传区域 -->
      <div class="file-upload-section">
        <div class="upload-header">
          <h3>上传文件</h3>
          <div class="upload-info">
            已上传 {{ uploadedFiles.length }}/{{ task.fileRequirements.maxFiles }} 个文件
          </div>
        </div>

        <!-- 文件列表 -->
        <div v-if="uploadedFiles.length > 0" class="uploaded-files">
          <div
            v-for="file in uploadedFiles"
            :key="file.id"
            class="file-item"
          >
            <div class="file-info">
              <div class="file-icon">
                <FileTextOutlined />
              </div>
              <div class="file-details">
                <div class="file-name">{{ file.name }}</div>
                <div class="file-meta">
                  {{ formatFileSize(file.size) }} · {{ formatDate(file.uploadedAt) }}
                </div>
              </div>
            </div>
            <div class="file-actions">
              <a-button
                type="text"
                size="small"
                @click="previewFile(file)"
              >
                预览
              </a-button>
              <a-button
                type="text"
                size="small"
                danger
                @click="removeFile(file.id)"
              >
                删除
              </a-button>
            </div>
          </div>
        </div>

        <!-- 上传区域 -->
        <div v-if="canUploadMore" class="upload-area">
          <a-upload-dragger
            v-model:file-list="fileList"
            :multiple="task.fileRequirements.maxFiles > 1"
            :max-count="remainingSlots"
            :accept="acceptTypes"
            :before-upload="beforeUpload"
            @change="handleFileChange"
            :disabled="uploading"
          >
            <div class="upload-content">
              <UploadOutlined class="upload-icon" />
              <div class="upload-text">
                <p>点击或拖拽文件到此处上传</p>
                <p class="upload-hint">
                  支持 {{ allowedTypesText }} 格式，单个文件不超过 {{ formatFileSize(task.fileRequirements.maxSize) }}
                </p>
              </div>
            </div>
          </a-upload-dragger>
        </div>

        <div v-if="!canUploadMore && uploadedFiles.length === 0" class="no-files">
          <a-empty description="请上传至少一个文件" />
        </div>
      </div>

      <div class="task-actions">
        <a-space>
          <a-button
            v-if="!isPreview"
            type="primary"
            :loading="submitting"
            :disabled="!canSubmit"
            @click="submitTask"
          >
            提交作业
          </a-button>
          <a-button
            v-if="!isPreview && uploadedFiles.length > 0"
            @click="clearAllFiles"
          >
            清空文件
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
                <a-button @click="downloadAllFiles">
                  下载全部文件
                </a-button>
              </a-space>
            </a-form-item>
          </a-form>
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

          <div class="submitted-files">
            <h4>提交的文件</h4>
            <div class="file-list">
              <div
                v-for="file in getSubmittedFiles()"
                :key="file.id"
                class="submitted-file-item"
              >
                <div class="file-info">
                  <FileTextOutlined />
                  <span>{{ file.name }}</span>
                  <span class="file-size">({{ formatFileSize(file.size) }})</span>
                </div>
                <a-button
                  type="link"
                  size="small"
                  @click="downloadFile(file)"
                >
                  下载
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message, Modal, UploadFile } from 'ant-design-vue'
import type { FileUploadTask, FileUploadSubmission, TaskComponentProps } from '@/types/task'
import { TASK_TYPE_CONFIGS, TASK_DIFFICULTY_CONFIGS } from '@/types/task'
import { UploadOutlined, FileTextOutlined } from '@ant-design/icons-vue'

interface Props extends TaskComponentProps<FileUploadTask> {}

const props = withDefaults(defineProps<Props>(), {
  isPreview: false,
  isTeacher: false
})

const emit = defineEmits<{
  submit: [submission: Partial<FileUploadSubmission>]
  save: [draft: Partial<FileUploadSubmission>]
}>()

// 响应式数据
const fileList = ref<UploadFile[]>([])
const uploadedFiles = ref<Array<{
  id: string
  name: string
  url: string
  size: number
  uploadedAt: string
}>>([])
const uploading = ref(false)
const submitting = ref(false)
const grading = ref(false)
const teacherScore = ref<number | undefined>()
const teacherComments = ref('')

// 计算属性
const config = computed(() => TASK_TYPE_CONFIGS[props.task.type])
const difficultyConfig = computed(() => TASK_DIFFICULTY_CONFIGS[props.task.difficulty])

const allowedTypesText = computed(() => {
  return props.task.fileRequirements.allowedTypes
    .map(type => type.replace('.', '').toUpperCase())
    .join(', ')
})

const acceptTypes = computed(() => {
  return props.task.fileRequirements.allowedTypes.join(',')
})

const canUploadMore = computed(() => {
  return uploadedFiles.value.length < props.task.fileRequirements.maxFiles
})

const remainingSlots = computed(() => {
  return props.task.fileRequirements.maxFiles - uploadedFiles.value.length
})

const canSubmit = computed(() => {
  return uploadedFiles.value.length > 0 && !uploading.value
})

// 初始化数据
onMounted(() => {
  if (props.submission) {
    const fileUploadSubmission = props.submission as FileUploadSubmission
    uploadedFiles.value = fileUploadSubmission.files

    if (props.isTeacher && fileUploadSubmission.teacherScore !== undefined) {
      teacherScore.value = fileUploadSubmission.teacherScore
      teacherComments.value = fileUploadSubmission.teacherComments || ''
    }
  }
})

// 方法
const beforeUpload = (file: File) => {
  // 检查文件类型
  const allowedTypes = props.task.fileRequirements.allowedTypes
  const fileType = '.' + file.name.split('.').pop()?.toLowerCase()

  if (!allowedTypes.includes(fileType)) {
    message.error(`不支持的文件类型，请上传 ${allowedTypesText.value} 格式的文件`)
    return false
  }

  // 检查文件大小
  if (file.size > props.task.fileRequirements.maxSize) {
    message.error(`文件大小超过限制，最大允许 ${formatFileSize(props.task.fileRequirements.maxSize)}`)
    return false
  }

  return true
}

const handleFileChange = (info: any) => {
  if (info.file.status === 'uploading') {
    uploading.value = true
  } else if (info.file.status === 'done') {
    uploading.value = false

    // 模拟文件上传成功
    const uploadedFile = {
      id: `file_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name: info.file.name,
      url: URL.createObjectURL(info.file.originFileObj), // 临时URL
      size: info.file.size,
      uploadedAt: new Date().toISOString()
    }

    uploadedFiles.value.push(uploadedFile)
    message.success(`${info.file.name} 上传成功`)

    // 清空文件列表
    fileList.value = []
  } else if (info.file.status === 'error') {
    uploading.value = false
    message.error(`${info.file.name} 上传失败`)
  }
}

const removeFile = (fileId: string) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个文件吗？此操作无法撤销。',
    onOk: () => {
      uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId)
      message.success('文件已删除')
    }
  })
}

const clearAllFiles = () => {
  Modal.confirm({
    title: '确认清空',
    content: '确定要清空所有上传的文件吗？此操作无法撤销。',
    onOk: () => {
      uploadedFiles.value = []
      fileList.value = []
      message.success('已清空所有文件')
    }
  })
}

const previewFile = (file: any) => {
  // 这里可以实现文件预览功能
  window.open(file.url, '_blank')
}

const submitTask = async () => {
  if (!canSubmit.value) {
    message.error('请先上传至少一个文件')
    return
  }

  submitting.value = true

  try {
    const submission: Partial<FileUploadSubmission> = {
      taskId: props.task.id,
      status: 'completed',
      files: uploadedFiles.value,
      submittedAt: new Date().toISOString(),
      maxScore: props.task.points
    }

    if (props.onSubmit) {
      await props.onSubmit(submission)
    }

    message.success('作业提交成功！')
  } catch (error) {
    console.error('提交失败:', error)
    message.error('提交失败，请重试')
  } finally {
    submitting.value = false
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
    message.success('评分提交成功')

    // 更新本地数据
    if (props.submission) {
      (props.submission as FileUploadSubmission).teacherScore = teacherScore.value
      (props.submission as FileUploadSubmission).teacherComments = teacherComments.value
    }
  } catch (error) {
    console.error('评分提交失败:', error)
    message.error('评分提交失败，请重试')
  } finally {
    grading.value = false
  }
}

const downloadFile = (file: any) => {
  const link = document.createElement('a')
  link.href = file.url
  link.download = file.name
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

const downloadAllFiles = () => {
  uploadedFiles.value.forEach(file => {
    downloadFile(file)
  })
}

const getSubmittedFiles = () => {
  if (props.submission) {
    const fileUploadSubmission = props.submission as FileUploadSubmission
    return fileUploadSubmission.files
  }
  return []
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.file-upload-task {
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

.task-instructions {
  margin-bottom: 32px;
}

.task-instructions h3,
.task-instructions h4 {
  margin: 0 0 12px 0;
  color: #f3f4f6;
}

.task-instructions p {
  margin: 0 0 16px 0;
  line-height: 1.6;
  color: #4b5563;
}

.requirements-list {
  background: white;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.requirement-item {
  display: flex;
  margin-bottom: 8px;
}

.requirement-item:last-child {
  margin-bottom: 0;
}

.requirement-item .label {
  font-weight: 500;
  color: #374151;
  min-width: 80px;
}

.requirement-item .value {
  color: #6b7280;
}

.grading-criteria {
  margin-top: 16px;
}

.grading-criteria ul {
  margin: 0;
  padding-left: 20px;
}

.grading-criteria li {
  margin-bottom: 4px;
  color: #4b5563;
}

.file-upload-section {
  margin-bottom: 24px;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.upload-header h3 {
  margin: 0;
  color: #f3f4f6;
}

.upload-info {
  font-size: 14px;
  color: #6b7280;
}

.uploaded-files {
  margin-bottom: 16px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 8px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.file-icon {
  color: #6b7280;
  font-size: 20px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #f3f4f6;
  margin-bottom: 2px;
}

.file-meta {
  font-size: 12px;
  color: #6b7280;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.upload-area {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  overflow: hidden;
}

.upload-content {
  padding: 40px;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  color: #9ca3af;
  margin-bottom: 16px;
}

.upload-text p {
  margin: 8px 0;
  color: #6b7280;
}

.upload-hint {
  color: #9ca3af !important;
  font-size: 12px !important;
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
  margin-bottom: 24px;
}

.submission-info p {
  margin: 4px 0;
}

.submitted-files {
  text-align: left;
}

.submitted-files h4 {
  margin: 0 0 12px 0;
  color: #f3f4f6;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.submitted-file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.submitted-file-item .file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.submitted-file-item .file-info span {
  color: #4b5563;
}

.file-size {
  color: #6b7280;
  font-size: 12px;
}

@media (max-width: 768px) {
  .file-upload-task {
    max-width: 100%;
  }

  .task-content {
    padding: 16px;
  }

  .upload-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .upload-area .ant-upload-drag {
    padding: 16px !important;
  }

  .upload-area .ant-upload-drag p.ant-upload-text {
    font-size: 14px;
    margin: 8px 0;
  }

  .upload-area .ant-upload-drag p.ant-upload-hint {
    font-size: 12px;
    margin: 4px 0 0 0;
  }

  .file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .file-item .file-info {
    width: 100%;
  }

  .file-item .file-details {
    flex: 1;
  }

  .file-actions {
    align-self: flex-end;
    width: 100%;
    display: flex;
    justify-content: flex-end;
  }

  .requirements-list {
    gap: 12px;
  }

  .requirement-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .requirement-item .label {
    font-size: 12px;
    color: #6b7280;
  }

  .requirement-item .value {
    font-size: 14px;
    font-weight: 500;
  }

  .submitted-file-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .submitted-file-item .file-info {
    width: 100%;
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

  .grading-form .ant-form-item {
    margin-bottom: 16px;
  }

  .grading-form .ant-input-number {
    width: 100%;
  }
}
</style>
