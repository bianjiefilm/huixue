<template>
  <div class="training-generation">
    <a-steps :current="currentStep" class="mb-6">
      <a-step title="配置实训" description="设置实训基本信息" />
      <a-step title="上传资源" description="上传实训相关文件" />
      <a-step title="生成中" description="AI正在生成实训内容" />
      <a-step title="完成" description="查看生成结果" />
    </a-steps>

    <!-- 步骤1: 配置实训 -->
    <div v-show="currentStep === 0" class="step-content">
      <a-form :model="formData" :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="实训标题" :rules="[{ required: true, message: '请输入实训标题' }]">
          <a-input
            v-model:value="formData.trainingTitle"
            placeholder="请输入实训标题，如：某零售企业经营分析"
            :maxlength="100"
            show-count
          />
        </a-form-item>

        <a-form-item label="实训类型" :rules="[{ required: true, message: '请选择实训类型' }]">
          <a-radio-group v-model:value="formData.trainingType">
            <a-radio value="拖拽式">
              <span>拖拽式</span>
              <a-tooltip title="使用BI设计器进行数据分析，适合可视化分析场景">
                <QuestionCircleOutlined class="ml-2" />
              </a-tooltip>
            </a-radio>
            <a-radio value="编码式">
              <span>编码式</span>
              <a-tooltip title="使用Jupyter Notebook编写Python代码，适合机器学习场景">
                <QuestionCircleOutlined class="ml-2" />
              </a-tooltip>
            </a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="分析目标" :rules="[{ required: true, message: '请至少添加一个分析目标' }]">
          <a-space direction="vertical" style="width: 100%">
            <div v-for="(goal, index) in formData.analysisGoals" :key="index" class="goal-item">
              <a-input
                v-model:value="formData.analysisGoals[index]"
                placeholder="如：构建销售总览仪表盘"
                style="width: calc(100% - 40px)"
              />
              <a-button
                type="link"
                danger
                @click="removeGoal(index)"
                :disabled="formData.analysisGoals.length === 1"
              >
                <DeleteOutlined />
              </a-button>
            </div>
            <a-button type="dashed" @click="addGoal" style="width: 100%">
              <PlusOutlined /> 添加分析目标
            </a-button>
          </a-space>
        </a-form-item>

        <a-form-item label="行业领域">
          <a-select v-model:value="formData.industry" placeholder="请选择行业领域">
            <a-select-option value="零售">零售</a-select-option>
            <a-select-option value="电商">电商</a-select-option>
            <a-select-option value="金融">金融</a-select-option>
            <a-select-option value="制造">制造</a-select-option>
            <a-select-option value="教育">教育</a-select-option>
            <a-select-option value="医疗">医疗</a-select-option>
            <a-select-option value="物流">物流</a-select-option>
            <a-select-option value="其他">其他</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="难度等级">
          <a-radio-group v-model:value="formData.difficulty">
            <a-radio value="初级">初级（适合初学者）</a-radio>
            <a-radio value="中级">中级（需要一定基础）</a-radio>
            <a-radio value="高级">高级（需要扎实功底）</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="预计时长">
          <a-input-number
            v-model:value="formData.durationHours"
            :min="1"
            :max="40"
            style="width: 200px"
          />
          <span class="ml-2">小时</span>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 16 }">
          <a-button type="primary" @click="nextStep" :disabled="!canProceedStep1">
            下一步
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 步骤2: 上传资源 -->
    <div v-show="currentStep === 1" class="step-content">
      <a-alert
        message="文件上传说明"
        :description="fileUploadTips"
        type="info"
        show-icon
        class="mb-4"
      />

      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="实训文件" :rules="[{ required: true, message: '请上传至少一个文件' }]">
          <a-upload-dragger
            v-model:fileList="fileList"
            :multiple="true"
            :before-upload="beforeUpload"
            @remove="handleRemove"
          >
            <p class="ant-upload-drag-icon">
              <CloudUploadOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持 SQL、CSV、Excel、BI模板(.tpo)、AI模板(.tapp)、Jupyter(.ipynb) 等格式
            </p>
          </a-upload-dragger>

          <div v-if="fileList.length > 0" class="file-type-config">
            <h4>文件类型标注</h4>
            <a-table
              :columns="fileColumns"
              :data-source="fileList"
              :pagination="false"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'type'">
                  <a-select
                    v-model:value="record.fileType"
                    style="width: 200px"
                    placeholder="请选择文件类型"
                  >
                    <a-select-option value="sql_schema">SQL结构定义</a-select-option>
                    <a-select-option value="sql_data">SQL数据插入</a-select-option>
                    <a-select-option value="bi_template">BI模板文件</a-select-option>
                    <a-select-option value="ai_template">AI模板文件</a-select-option>
                    <a-select-option value="jupyter_notebook">Jupyter笔记本</a-select-option>
                    <a-select-option value="supporting_asset">辅助素材</a-select-option>
                  </a-select>
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-button type="link" danger size="small" @click="removeFile(record)">
                    移除
                  </a-button>
                </template>
              </template>
            </a-table>
          </div>
        </a-form-item>

        <a-form-item label="生成选项" :wrapper-col="{ span: 20 }">
          <a-checkbox v-model:checked="formData.generateHandbook">
            生成实训操作手册
            <a-tooltip title="AI将根据数据结构和分析目标自动生成详细的操作指导手册">
              <QuestionCircleOutlined class="ml-2" />
            </a-tooltip>
          </a-checkbox>
        </a-form-item>

        <a-form-item label="作业配置" :wrapper-col="{ span: 20 }">
          <a-checkbox v-model:checked="formData.requireReport">
            要求提交实验报告
          </a-checkbox>
          <div v-if="formData.trainingType === '拖拽式'" class="mt-2">
            <a-checkbox v-model:checked="formData.requireDesignFile">
              要求提交BI设计文件
            </a-checkbox>
          </div>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 20 }">
          <a-space>
            <a-button @click="prevStep">上一步</a-button>
            <a-button type="primary" @click="startGeneration" :loading="generating">
              开始生成
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <!-- 步骤3: 生成中 -->
    <div v-show="currentStep === 2" class="step-content">
      <div class="generation-progress">
        <a-spin size="large" />
        <h3>AI 正在生成实训内容...</h3>
        <a-progress
          :percent="generationProgress"
          :status="generationStatus"
          :stroke-color="{
            '0%': '#108ee9',
            '100%': '#87d068'
          }"
        />
        <p class="progress-message">{{ progressMessage }}</p>

        <div v-if="currentTaskId" class="task-info">
          <a-descriptions :column="1" bordered size="small">
            <a-descriptions-item label="任务ID">{{ currentTaskId }}</a-descriptions-item>
            <a-descriptions-item label="实训类型">{{ formData.trainingType }}</a-descriptions-item>
            <a-descriptions-item label="文件数量">{{ fileList.length }}</a-descriptions-item>
            <a-descriptions-item label="预计耗时">2-5 分钟</a-descriptions-item>
          </a-descriptions>
        </div>

        <div class="generation-steps">
          <a-timeline>
            <a-timeline-item :color="generationProgress >= 20 ? 'green' : 'gray'">
              解析数据结构
            </a-timeline-item>
            <a-timeline-item :color="generationProgress >= 40 ? 'green' : 'gray'">
              生成实训元数据
            </a-timeline-item>
            <a-timeline-item :color="generationProgress >= 60 ? 'green' : 'gray'">
              生成操作手册
            </a-timeline-item>
            <a-timeline-item :color="generationProgress >= 80 ? 'green' : 'gray'">
              配置作业节点
            </a-timeline-item>
            <a-timeline-item :color="generationProgress >= 100 ? 'green' : 'gray'">
              保存到数据库
            </a-timeline-item>
          </a-timeline>
        </div>
      </div>
    </div>

    <!-- 步骤4: 完成 -->
    <div v-show="currentStep === 3" class="step-content">
      <a-result
        :status="generationResult.success ? 'success' : 'error'"
        :title="generationResult.success ? '实训生成成功！' : '生成失败'"
        :sub-title="generationResult.message"
      >
        <template #extra>
          <a-space>
            <a-button type="primary" @click="viewResult">查看结果</a-button>
            <a-button v-if="generationResult.trainingId" @click="goToTraining">
              进入实训
            </a-button>
            <a-button @click="resetForm">继续生成</a-button>
          </a-space>
        </template>

        <div v-if="generationResult.success && generationResult.details" class="result-summary">
          <a-card title="生成结果摘要" class="mb-4">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="实训ID">
                {{ generationResult.details.training?.id }}
              </a-descriptions-item>
              <a-descriptions-item label="实训标题">
                {{ generationResult.details.training?.title }}
              </a-descriptions-item>
              <a-descriptions-item label="实训类型">
                <a-tag :color="generationResult.details.training?.type === 'DRAG_DROP' ? 'blue' : 'green'">
                  {{ generationResult.details.training?.type === 'DRAG_DROP' ? '拖拽式' : '编码式' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="难度等级">
                {{ generationResult.details.training?.difficulty }}
              </a-descriptions-item>
              <a-descriptions-item label="数据集数量">
                {{ generationResult.datasetCount || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="Jupyter文件">
                {{ generationResult.jupyterCount || 0 }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>

          <a-card v-if="generationResult.metadata" title="实训配置信息" class="mb-4">
            <pre>{{ JSON.stringify(generationResult.metadata, null, 2) }}</pre>
          </a-card>

          <a-card v-if="generationResult.handbook" title="实训手册预览">
            <div class="handbook-preview" v-html="renderMarkdown(generationResult.handbook)"></div>
          </a-card>
        </div>
      </a-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  CloudUploadOutlined,
  QuestionCircleOutlined,
  DeleteOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import { marked } from 'marked'
import {
  createTrainingPackageTask,
  getTrainingPackageTaskStatus,
  type TrainingManifest,
  type TrainingFileManifestItem,
  type TaskStatus
} from '@/api/ai-generation'

const router = useRouter()
const currentStep = ref(0)
const generating = ref(false)
const generationProgress = ref(0)
const generationStatus = ref<'active' | 'exception' | 'success'>('active')
const progressMessage = ref('正在初始化...')
const currentTaskId = ref('')

// 任务列表（供父组件使用）
const taskList = ref<any[]>([])

// 表单数据
const formData = reactive({
  trainingTitle: '',
  trainingType: '拖拽式' as '拖拽式' | '编码式',
  analysisGoals: [''],
  industry: '零售',
  difficulty: '中级',
  durationHours: 8,
  generateHandbook: true,
  requireReport: true,
  requireDesignFile: true
})

// 文件列表
const fileList = ref<any[]>([])

// 生成结果
const generationResult = reactive({
  success: false,
  message: '',
  trainingId: null as number | null,
  details: null as any,
  metadata: null as any,
  handbook: '',
  datasetCount: 0,
  jupyterCount: 0
})

// 文件上传提示
const fileUploadTips = computed(() => {
  if (formData.trainingType === '拖拽式') {
    return '拖拽式实训：请上传SQL文件（数据库结构和数据）、BI模板文件（可选）等'
  } else {
    return '编码式实训：请上传数据文件（CSV/Excel）、Jupyter Notebook文件（可选）等'
  }
})

// 文件表格列
const fileColumns = [
  {
    title: '文件名',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '大小',
    dataIndex: 'size',
    key: 'size',
    width: 100,
    customRender: ({ text }: { text: number }) => {
      return `${(text / 1024 / 1024).toFixed(2)} MB`
    }
  },
  {
    title: '文件类型',
    key: 'type',
    width: 220
  },
  {
    title: '操作',
    key: 'action',
    width: 80
  }
]

// 计算是否可以继续下一步
const canProceedStep1 = computed(() => {
  return formData.trainingTitle &&
    formData.analysisGoals.length > 0 &&
    formData.analysisGoals.every(goal => goal.trim())
})

// 添加分析目标
const addGoal = () => {
  formData.analysisGoals.push('')
}

// 移除分析目标
const removeGoal = (index: number) => {
  if (formData.analysisGoals.length > 1) {
    formData.analysisGoals.splice(index, 1)
  }
}

// 文件上传前的处理
const beforeUpload = (file: File) => {
  const fileExt = file.name.split('.').pop()?.toLowerCase()
  const validExts = ['sql', 'csv', 'xlsx', 'xls', 'tpo', 'tapp', 'ipynb', 'json', 'txt']
  
  if (!fileExt || !validExts.includes(fileExt)) {
    message.error(`不支持的文件格式: ${fileExt}`)
    return false
  }

  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB！')
    return false
  }

  // 根据文件扩展名智能设置文件类型
  let defaultFileType = 'supporting_asset'
  if (fileExt === 'sql') {
    defaultFileType = file.name.toLowerCase().includes('create') ? 'sql_schema' : 'sql_data'
  } else if (fileExt === 'tpo') {
    defaultFileType = 'bi_template'
  } else if (fileExt === 'tapp') {
    defaultFileType = 'ai_template'
  } else if (fileExt === 'ipynb') {
    defaultFileType = 'jupyter_notebook'
  }

  const fileWithType = {
    ...file,
    uid: file.uid || Date.now().toString(),
    name: file.name,
    size: file.size,
    originFileObj: file,
    fileType: defaultFileType
  }
  fileList.value.push(fileWithType)
  return false // 阻止自动上传
}

// 移除文件
const handleRemove = (file: any) => {
  const index = fileList.value.indexOf(file)
  if (index > -1) {
    fileList.value.splice(index, 1)
  }
}

// 移除文件（表格中）
const removeFile = (file: any) => {
  handleRemove(file)
}

// 下一步
const nextStep = () => {
  if (currentStep.value === 0 && !canProceedStep1.value) {
    message.warning('请填写完整的实训信息')
    return
  }
  currentStep.value++
}

// 上一步
const prevStep = () => {
  currentStep.value--
}

// 开始生成
const startGeneration = async () => {
  if (fileList.value.length === 0) {
    message.warning('请上传至少一个文件')
    return
  }

  if (!fileList.value.every(file => file.fileType)) {
    message.warning('请为每个文件选择类型')
    return
  }

  generating.value = true
  generationProgress.value = 0
  progressMessage.value = '正在上传文件...'
  currentStep.value = 2

  try {
    // 构建清单
    const manifest: TrainingManifest = {
      training_title: formData.trainingTitle,
      analysis_goals: formData.analysisGoals.filter(goal => goal.trim()),
      training_type: formData.trainingType,
      files: fileList.value.map((file, index) => ({
        form_field_name: `file_${index + 1}`,
        original_filename: file.name,
        file_type: file.fileType as TrainingFileManifestItem['file_type']
      }))
    }

    // 创建任务
    const files = fileList.value.map(f => f.originFileObj || f)
    const response = await createTrainingPackageTask(files, manifest)
    currentTaskId.value = response.task_id
    progressMessage.value = '任务已创建，正在处理中...'

    // 添加到任务列表
    const newTask = {
      task_id: response.task_id,
      type: 'training',
      title: formData.trainingTitle,
      status: 'PROCESSING',
      progress: 0,
      create_time: new Date().toLocaleString(),
      complete_time: null,
      result: null,
      error_message: null
    }
    taskList.value.unshift(newTask)

    // 轮询任务状态
    pollTaskStatus(response.task_id)

  } catch (error: any) {
    generating.value = false
    generationStatus.value = 'exception'
    message.error(error.message || '创建任务失败')
    currentStep.value = 3
    generationResult.success = false
    generationResult.message = error.message || '创建任务失败'
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string) => {
  try {
    const status: TaskStatus = await getTrainingPackageTaskStatus(taskId)
    
    // 更新任务列表中的状态
    const taskIndex = taskList.value.findIndex(t => t.task_id === taskId)
    if (taskIndex > -1) {
      taskList.value[taskIndex] = {
        ...taskList.value[taskIndex],
        status: status.status,
        progress: status.progress,
        result: status.result,
        error_message: status.error_message
      }
    }

    generationProgress.value = status.progress
    
    if (status.status === 'SUCCESS') {
      generating.value = false
      generationStatus.value = 'success'
      progressMessage.value = '生成完成！'
      currentStep.value = 3
      
      // 处理成功结果
      generationResult.success = true
      generationResult.message = status.result?.database_result?.message || '实训生成成功'
      generationResult.trainingId = status.result?.database_result?.training_id || null
      generationResult.details = status.result?.database_result?.details || null
      generationResult.metadata = status.result?.training_package?.metadata || null
      generationResult.handbook = status.result?.training_package?.handbook_markdown || ''
      generationResult.datasetCount = status.result?.database_result?.dataset_ids?.length || 0
      generationResult.jupyterCount = status.result?.database_result?.jupyter_file_ids?.length || 0
      
      // 更新任务完成时间
      if (taskIndex > -1) {
        taskList.value[taskIndex].complete_time = new Date().toLocaleString()
      }
      
      message.success('实训生成成功！')
      
    } else if (status.status === 'ERROR') {
      generating.value = false
      generationStatus.value = 'exception'
      progressMessage.value = '生成失败'
      currentStep.value = 3
      
      generationResult.success = false
      generationResult.message = status.error_message || '生成过程中出现错误'
      
      message.error(status.error_message || '生成失败')
      
    } else if (status.status === 'PROCESSING') {
      // 更新进度消息
      if (status.progress < 20) {
        progressMessage.value = '正在解析数据结构...'
      } else if (status.progress < 40) {
        progressMessage.value = '正在生成实训元数据...'
      } else if (status.progress < 60) {
        progressMessage.value = '正在生成操作手册...'
      } else if (status.progress < 80) {
        progressMessage.value = '正在配置作业节点...'
      } else if (status.progress < 100) {
        progressMessage.value = '正在保存到数据库...'
      }
      
      // 继续轮询
      setTimeout(() => pollTaskStatus(taskId), 2000)
    }
  } catch (error: any) {
    generating.value = false
    generationStatus.value = 'exception'
    message.error('查询任务状态失败')
    currentStep.value = 3
    generationResult.success = false
    generationResult.message = error.message || '查询任务状态失败'
  }
}

// 查看结果
const viewResult = () => {
  const latestTask = taskList.value.find(t => t.task_id === currentTaskId.value)
  if (latestTask && latestTask.result) {
    console.log('View result:', latestTask)
  }
}

// 进入实训
const goToTraining = () => {
  if (generationResult.trainingId) {
    router.push(`/project/${generationResult.trainingId}`)
  }
}

// 重置表单
const resetForm = () => {
  currentStep.value = 0
  formData.trainingTitle = ''
  formData.trainingType = '拖拽式'
  formData.analysisGoals = ['']
  formData.industry = '零售'
  formData.difficulty = '中级'
  formData.durationHours = 8
  formData.generateHandbook = true
  formData.requireReport = true
  formData.requireDesignFile = true
  fileList.value = []
  generationResult.success = false
  generationResult.message = ''
  generationResult.trainingId = null
  generationResult.details = null
  generationResult.metadata = null
  generationResult.handbook = ''
  generationResult.datasetCount = 0
  generationResult.jupyterCount = 0
  currentTaskId.value = ''
  generationProgress.value = 0
  progressMessage.value = '正在初始化...'
}

// 渲染Markdown
const renderMarkdown = (markdown: string) => {
  return marked(markdown || '')
}

// 暴露方法给父组件
defineExpose({
  getTaskList: () => taskList.value
})
</script>

<style lang="less" scoped>
.training-generation {
  .mb-6 {
    margin-bottom: 24px;
  }
  
  .mb-4 {
    margin-bottom: 16px;
  }
  
  .step-content {
    min-height: 400px;
    
    .goal-item {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    
    .file-type-config {
      margin-top: 16px;
      
      h4 {
        margin-bottom: 12px;
        font-weight: 500;
      }
    }
    
    .generation-progress {
      text-align: center;
      padding: 48px;
      
      h3 {
        margin: 24px 0 16px;
        font-size: 18px;
      }
      
      .progress-message {
        margin-top: 16px;
        color: #666666;
      }
      
      .task-info {
        margin-top: 32px;
        max-width: 500px;
        margin-left: auto;
        margin-right: auto;
      }
      
      .generation-steps {
        margin-top: 32px;
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
        text-align: left;
      }
    }
    
    .result-summary {
      margin-top: 24px;
      
      .handbook-preview {
        max-height: 500px;
        overflow-y: auto;
        
        :deep(h1), :deep(h2), :deep(h3) {
          margin-top: 16px;
          margin-bottom: 8px;
        }
        
        :deep(ul), :deep(ol) {
          padding-left: 24px;
        }
        
        :deep(code) {
          background: #f5f5f5;
          padding: 2px 4px;
          border-radius: 2px;
        }
        
        :deep(pre) {
          background: #2b2b2b;
          color: #fff;
          padding: 12px;
          border-radius: 4px;
          overflow-x: auto;
        }
      }
    }
  }
  
  .mt-2 {
    margin-top: 8px;
  }
  
  .ml-2 {
    margin-left: 8px;
  }
}
</style>