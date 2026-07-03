<template>
  <div class="teacher-ai-generator-form">
    <a-page-header
      title="AI 生成实践闯关任务"
      sub-title="选择教学资料，AI 自动拆解知识点并生成实践关卡"
      @back="() => $router.back()"
    />

    <div class="form-content">
      <a-card title="① 资料选择" class="section-card">
        <a-tabs v-model:activeKey="resourceMode">
          <a-tab-pane key="upload" tab="上传新资料">
            <a-upload-dragger
              :file-list="fileList"
              :before-upload="handleBeforeUpload"
              :max-count="1"
              accept=".pdf,.docx,.pptx"
              @remove="handleRemoveFile"
            >
              <p class="ant-upload-drag-icon">
                <inbox-outlined />
              </p>
              <p class="ant-upload-text">点击或拖拽文件到此处上传</p>
              <p class="ant-upload-hint">支持 PDF / DOCX / PPTX，暂不支持视频与扫描版 PDF</p>
            </a-upload-dragger>
          </a-tab-pane>
          <a-tab-pane key="existing" tab="从已有教学资源选择" disabled>
            <a-empty description="后端资料库选择接口暂未实现，请先使用「上传新资料」" />
          </a-tab-pane>
          <a-tab-pane key="combine" tab="多文件组合生成" disabled>
            <a-empty description="多文件组合生成将在后续版本开放" />
          </a-tab-pane>
        </a-tabs>
      </a-card>

      <a-card title="② 教学目标" class="section-card">
        <a-form layout="vertical">
          <a-form-item
            help="教学目标会约束 AI：不生成偏离目标的知识点、不生成过多背景性任务、不生成不适合本节课的综合项目"
          >
            <a-textarea
              v-model:value="objective"
              :rows="4"
              placeholder="例如：让学生掌握数据导入、字段清洗、缺失值处理和基础可视化。"
            />
          </a-form-item>
        </a-form>
      </a-card>

      <a-card title="③ 学生水平" class="section-card">
        <a-radio-group v-model:value="studentLevel" class="student-level-group">
          <a-radio
            v-for="opt in STUDENT_LEVEL_OPTIONS"
            :key="opt.value"
            :value="opt.value"
            class="student-level-option"
          >
            <div class="option-label">{{ opt.label }}</div>
            <div class="option-desc">{{ opt.desc }}</div>
          </a-radio>
        </a-radio-group>
      </a-card>

      <div class="form-actions">
        <a-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="handleStartGenerate"
        >
          开始生成
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { InboxOutlined } from '@ant-design/icons-vue'
import { useRouter } from 'vue-router'
import {
  createGenerationJob,
  STUDENT_LEVEL_OPTIONS,
  type StudentLevel
} from '@/api/teacher-ai'

const router = useRouter()

// 资料选择：真实文件上传（后端目前只支持直接上传，没有资源库选择接口）
const resourceMode = ref<'existing' | 'upload' | 'combine'>('upload')
const fileList = ref<any[]>([])
const selectedFile = ref<File | null>(null)

const handleBeforeUpload = (file: File) => {
  selectedFile.value = file
  fileList.value = [file]
  return false // 阻止 antd 自动上传，由「开始生成」按钮统一提交
}

const handleRemoveFile = () => {
  selectedFile.value = null
  fileList.value = []
}

// 教学目标
const objective = ref('')

// 学生水平
const studentLevel = ref<StudentLevel>('learned_but_cannot_apply')

// 提交
const submitting = ref(false)

const canSubmit = computed(() => {
  return selectedFile.value !== null && objective.value.trim().length > 0
})

const handleStartGenerate = async () => {
  if (!canSubmit.value || !selectedFile.value) {
    message.warning('请先上传资料并填写教学目标')
    return
  }

  submitting.value = true
  try {
    const result = await createGenerationJob({
      file: selectedFile.value,
      objective: objective.value.trim(),
      studentLevel: studentLevel.value
    })

    const jobId = (result as any)?.job?.id
    message.success(`生成任务已创建，AI 拆解出 ${(result as any)?.knowledge_points?.length ?? 0} 个知识点`)
    if (jobId) {
      router.push(`/teacher/ai-practice-generator/${jobId}/knowledge`)
    }
  } catch (error) {
    message.error('创建生成任务失败，请检查后端服务是否已启动')
    console.error(error)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="less">
.teacher-ai-generator-form {
  background-color: #f0f2f5;
  min-height: 100vh;

  .form-content {
    padding: 24px;
    max-width: 900px;
    margin: 0 auto;
  }

  .section-card {
    margin-bottom: 24px;
  }

  .student-level-group {
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  .student-level-option {
    display: flex;
    align-items: flex-start;
    padding: 12px 16px;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    width: 100%;

    .option-label {
      font-weight: 600;
    }

    .option-desc {
      color: #666;
      font-size: 12px;
      margin-top: 4px;
    }
  }

  .form-actions {
    text-align: center;
    margin-top: 32px;
  }
}
</style>
