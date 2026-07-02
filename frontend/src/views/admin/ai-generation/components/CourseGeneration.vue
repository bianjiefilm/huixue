<template>
  <div class="course-generation">
    <a-steps :current="currentStep" class="mb-6">
      <a-step title="上传文件" description="选择教学文件并指定类型" />
      <a-step title="设置参数" description="配置课程生成参数" />
      <a-step title="生成中" description="AI正在生成课程内容" />
      <a-step title="完成" description="查看生成结果" />
    </a-steps>

    <!-- 步骤1: 上传文件 -->
    <div v-show="currentStep === 0" class="step-content">
      <a-form :model="formData" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="课程标题" :rules="[{ required: true, message: '请输入课程标题' }]">
          <a-input
            v-model:value="formData.courseTitle"
            placeholder="请输入课程标题，如：Python程序设计基础"
            :maxlength="100"
            show-count
          />
        </a-form-item>

        <a-form-item label="教学文件" :rules="[{ required: true, message: '请上传至少一个文件' }]">
          <a-upload-dragger
            v-model:fileList="fileList"
            :multiple="true"
            :before-upload="beforeUpload"
            @remove="handleRemove"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持多文件上传，支持 PDF、DOCX 格式，单个文件最大 10MB
            </p>
          </a-upload-dragger>

          <div v-if="fileList.length > 0" class="file-type-config">
            <h4>文件类型配置</h4>
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
                    <a-select-option value="teaching_content">教学内容</a-select-option>
                    <a-select-option value="teaching_plan">教学方案</a-select-option>
                    <a-select-option value="ideological_elements">思政元素</a-select-option>
                  </a-select>
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-button type="link" danger size="small" @click="removeFile(record)">
                    移除
                  </a-button>
                </template>
              </template>
            </a-table>
            <a-alert
              class="mt-2"
              message="文件类型说明"
              description="教学内容：生成完整关卡（提纲+内容+评测）| 教学方案：生成课程规划试题 | 思政元素：生成价值观教育试题"
              type="info"
              show-icon
            />
          </div>
        </a-form-item>

        <a-form-item :wrapper-col="{ offset: 4, span: 20 }">
          <a-button type="primary" @click="nextStep" :disabled="!canProceed">
            下一步
          </a-button>
        </a-form-item>
      </a-form>
    </div>

    <!-- 步骤2: 设置参数 -->
    <div v-show="currentStep === 1" class="step-content">
      <a-form :model="formData" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="生成选项">
          <a-checkbox-group v-model:value="formData.generateOptions">
            <a-checkbox value="outline">生成关卡提纲</a-checkbox>
            <a-checkbox value="content">生成关卡内容</a-checkbox>
            <a-checkbox value="evaluation">生成评测资源</a-checkbox>
            <a-checkbox value="questions">生成考核试题</a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <a-form-item label="难度设置">
          <a-radio-group v-model:value="formData.difficulty">
            <a-radio value="初级">初级</a-radio>
            <a-radio value="中级">中级</a-radio>
            <a-radio value="高级">高级</a-radio>
            <a-radio value="混合">混合（根据内容自动判断）</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="关卡类型偏好">
          <a-checkbox-group v-model:value="formData.levelTypes">
            <a-checkbox value="实践题">实践题</a-checkbox>
            <a-checkbox value="选择题">选择题</a-checkbox>
            <a-checkbox value="判断题">判断题</a-checkbox>
          </a-checkbox-group>
        </a-form-item>

        <a-form-item label="高级选项">
          <a-switch v-model:checked="formData.autoSave" /> 自动保存到数据库
          <a-tooltip title="生成完成后自动保存到课程库，可直接在课程管理中查看和使用">
            <QuestionCircleOutlined class="ml-2" />
          </a-tooltip>
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
        <h3>AI 正在生成课程内容...</h3>
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
            <a-descriptions-item label="开始时间">{{ taskStartTime }}</a-descriptions-item>
            <a-descriptions-item label="预计耗时">1-3 分钟</a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </div>

    <!-- 步骤4: 完成 -->
    <div v-show="currentStep === 3" class="step-content">
      <a-result
        :status="generationResult.success ? 'success' : 'error'"
        :title="generationResult.success ? '课程生成成功！' : '生成失败'"
        :sub-title="generationResult.message"
      >
        <template #extra>
          <a-space>
            <a-button type="primary" @click="viewResult">查看结果</a-button>
            <a-button v-if="generationResult.practiceId" @click="goToCourse">
              进入课程
            </a-button>
            <a-button @click="resetForm">继续生成</a-button>
          </a-space>
        </template>

        <div v-if="generationResult.success && generationResult.details" class="result-summary">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="课程ID">
              {{ generationResult.details.practice?.id }}
            </a-descriptions-item>
            <a-descriptions-item label="课程标题">
              {{ generationResult.details.practice?.title }}
            </a-descriptions-item>
            <a-descriptions-item label="关卡数量">
              {{ generationResult.details.tasks?.length || 0 }}
            </a-descriptions-item>
            <a-descriptions-item label="试题数量">
              {{ generationResult.details.test_paper?.question_count || 0 }}
            </a-descriptions-item>
          </a-descriptions>

          <div class="generated-files">
            <h4>处理的文件</h4>
            <a-list
              :data-source="generationResult.processedFiles || []"
              size="small"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-space>
                    <FileTextOutlined />
                    {{ item.original_filename }}
                    <a-tag :color="item.processing_status === 'SUCCESS' ? 'success' : 'error'">
                      {{ item.processing_status }}
                    </a-tag>
                    <span v-if="item.levels">生成 {{ item.levels.length }} 个关卡</span>
                    <span v-if="item.exam_questions">生成 {{ item.exam_questions.length }} 道试题</span>
                  </a-space>
                </a-list-item>
              </template>
            </a-list>
          </div>
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
  InboxOutlined,
  QuestionCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import {
  createCoursePackageTask,
  getCoursePackageTaskStatus,
  type CourseManifest,
  type FileManifestItem,
  type TaskStatus
} from '@/api/ai-generation'

const router = useRouter()
const currentStep = ref(0)
const generating = ref(false)
const generationProgress = ref(0)
const generationStatus = ref<'active' | 'exception' | 'success'>('active')
const progressMessage = ref('正在初始化...')
const currentTaskId = ref('')
const taskStartTime = ref('')

// 任务列表（供父组件使用）
const taskList = ref<any[]>([])

// 表单数据
const formData = reactive({
  courseTitle: '',
  generateOptions: ['outline', 'content', 'evaluation', 'questions'],
  difficulty: '混合',
  levelTypes: ['实践题', '选择题', '判断题'],
  autoSave: true
})

// 文件列表
const fileList = ref<any[]>([])

// 生成结果
const generationResult = reactive({
  success: false,
  message: '',
  practiceId: null as number | null,
  details: null as any,
  processedFiles: [] as any[]
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
const canProceed = computed(() => {
  return formData.courseTitle && fileList.value.length > 0 &&
    fileList.value.every(file => file.fileType)
})

// 文件上传前的处理
const beforeUpload = (file: File) => {
  const isValidType = file.type === 'application/pdf' ||
    file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
  if (!isValidType) {
    message.error('只能上传 PDF 或 DOCX 格式的文件！')
    return false
  }

  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('文件大小不能超过 10MB！')
    return false
  }

  // 默认设置文件类型
  const fileWithType = {
    ...file,
    uid: file.uid || Date.now().toString(),
    name: file.name,
    size: file.size,
    originFileObj: file,
    fileType: 'teaching_content' // 默认为教学内容
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
  if (currentStep.value === 0 && !canProceed.value) {
    message.warning('请填写课程标题并为每个文件选择类型')
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
  generating.value = true
  generationProgress.value = 0
  progressMessage.value = '正在上传文件...'
  currentStep.value = 2

  try {
    // 构建清单
    const manifest: CourseManifest = {
      course_title: formData.courseTitle,
      files: fileList.value.map((file, index) => ({
        form_field_name: `file_${index + 1}`,
        original_filename: file.name,
        file_type: file.fileType as FileManifestItem['file_type']
      }))
    }

    // 创建任务
    const files = fileList.value.map(f => f.originFileObj || f)
    const response = await createCoursePackageTask(files, manifest)
    currentTaskId.value = response.task_id
    taskStartTime.value = new Date().toLocaleString()
    progressMessage.value = '任务已创建，正在处理中...'

    // 添加到任务列表
    const newTask = {
      task_id: response.task_id,
      type: 'course',
      title: formData.courseTitle,
      status: 'PROCESSING',
      progress: 0,
      create_time: taskStartTime.value,
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
    const status: TaskStatus = await getCoursePackageTaskStatus(taskId)
    
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
      generationResult.message = status.result?.database_result?.message || '课程生成成功'
      generationResult.practiceId = status.result?.database_result?.practice_id || null
      generationResult.details = status.result?.database_result?.details || null
      generationResult.processedFiles = status.result?.course_package?.processed_files || []
      
      // 更新任务完成时间
      if (taskIndex > -1) {
        taskList.value[taskIndex].complete_time = new Date().toLocaleString()
      }
      
      message.success('课程生成成功！')
      
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
        progressMessage.value = '正在解析文件...'
      } else if (status.progress < 40) {
        progressMessage.value = '正在生成课程元数据...'
      } else if (status.progress < 60) {
        progressMessage.value = '正在生成关卡内容...'
      } else if (status.progress < 80) {
        progressMessage.value = '正在生成评测资源...'
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
  // 父组件会处理结果展示
  const latestTask = taskList.value.find(t => t.task_id === currentTaskId.value)
  if (latestTask && latestTask.result) {
    // 触发父组件的查看结果方法
    console.log('View result:', latestTask)
  }
}

// 进入课程
const goToCourse = () => {
  if (generationResult.practiceId) {
    router.push(`/admin/course/detail/${generationResult.practiceId}`)
  }
}

// 重置表单
const resetForm = () => {
  currentStep.value = 0
  formData.courseTitle = ''
  formData.generateOptions = ['outline', 'content', 'evaluation', 'questions']
  formData.difficulty = '混合'
  formData.levelTypes = ['实践题', '选择题', '判断题']
  formData.autoSave = true
  fileList.value = []
  generationResult.success = false
  generationResult.message = ''
  generationResult.practiceId = null
  generationResult.details = null
  generationResult.processedFiles = []
  currentTaskId.value = ''
  taskStartTime.value = ''
  generationProgress.value = 0
  progressMessage.value = '正在初始化...'
}

// 暴露方法给父组件
defineExpose({
  getTaskList: () => taskList.value
})
</script>

<style lang="less" scoped>
.course-generation {
  .mb-6 {
    margin-bottom: 24px;
  }
  
  .step-content {
    min-height: 400px;
    
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
    }
    
    .result-summary {
      margin-top: 24px;
      
      .generated-files {
        margin-top: 24px;
        
        h4 {
          margin-bottom: 12px;
          font-weight: 500;
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