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
          <a-tab-pane key="existing" tab="从已有教学资源选择">
            <a-alert
              v-if="loadResourceError"
              type="error"
              :message="loadResourceError"
              show-icon
              style="margin-bottom: 16px"
            />
            <a-input-search
              v-model:value="resourceKeyword"
              placeholder="按标题搜索教学资源"
              style="margin-bottom: 16px; max-width: 320px"
              @search="handleSearchResources"
            />
            <a-table
              :columns="resourceColumns"
              :data-source="resourceList"
              :loading="loadingResources"
              :row-selection="{ selectedRowKeys: selectedDocumentIds, onChange: onSelectResources }"
              row-key="document_id"
              :pagination="{ pageSize: 5 }"
            />
          </a-tab-pane>
          <a-tab-pane key="upload" tab="上传新资料" disabled>
            <a-empty description="上传新资料模式将在后续版本开放，请先使用「从已有教学资源选择」" />
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
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  createGenerationJob,
  listTeachingResources,
  STUDENT_LEVEL_OPTIONS,
  type StudentLevel,
  type TeachingResourceItem
} from '@/api/teacher-ai'

const router = useRouter()

// 资料选择
const resourceMode = ref<'existing' | 'upload' | 'combine'>('existing')
const resourceKeyword = ref('')
const resourceList = ref<TeachingResourceItem[]>([])
const selectedDocumentIds = ref<string[]>([])
const loadingResources = ref(false)
const loadResourceError = ref('')

const resourceColumns = [
  { title: '标题', dataIndex: 'title' },
  { title: '类型', dataIndex: 'file_type', width: 100 },
  { title: '页数', dataIndex: 'pages', width: 100 },
  { title: '上传时间', dataIndex: 'uploaded_at', width: 180 }
]

const onSelectResources = (keys: string[]) => {
  selectedDocumentIds.value = keys
}

const handleSearchResources = async () => {
  loadingResources.value = true
  loadResourceError.value = ''
  try {
    const result: any = await listTeachingResources(resourceKeyword.value)
    resourceList.value = result?.data?.items ?? result?.items ?? []
  } catch (error) {
    // 后端接口尚未联调，第一版允许失败但不阻断表单填写
    loadResourceError.value = '教学资源列表暂未接入（后端接口开发中），资料选择功能待联调后可用'
    console.error(error)
  } finally {
    loadingResources.value = false
  }
}

onMounted(() => {
  handleSearchResources()
})

// 教学目标
const objective = ref('')

// 学生水平
const studentLevel = ref<StudentLevel>('learned_but_cannot_apply')

// 提交
const submitting = ref(false)

const canSubmit = computed(() => {
  return selectedDocumentIds.value.length > 0 && objective.value.trim().length > 0
})

const handleStartGenerate = async () => {
  if (!canSubmit.value) {
    message.warning('请先选择资料并填写教学目标')
    return
  }

  submitting.value = true
  try {
    const result: any = await createGenerationJob({
      source_document_ids: selectedDocumentIds.value,
      objective: objective.value.trim(),
      student_level: studentLevel.value
    })

    const jobId = result?.data?.job_id ?? result?.job_id
    message.success('生成任务已创建，进入知识点确认')
    if (jobId) {
      router.push(`/teacher/ai-practice-generator/${jobId}/knowledge`)
    }
  } catch (error) {
    // 后端接口尚未实现，第一版先给出明确提示，不假装成功
    message.error('创建生成任务失败（后端接口开发中，暂无法联调）')
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
