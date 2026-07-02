<template>
  <div class="batch-course-generator">
    <!-- 页面标题 -->
    <a-page-header
      title="智能课程补充系统"
      sub-title="自动检测并补充课程项目中缺失的实践、关卡和试题"
      @back="() => $router.back()"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshFileList">
            <ReloadOutlined /> 刷新列表
          </a-button>
          <a-button 
            type="primary" 
            @click="handleBatchGenerate"
            :disabled="selectedProjects.length === 0"
            :loading="batchGenerating"
          >
            <RobotOutlined /> 批量补充课程 ({{ selectedProjects.length }})
          </a-button>
          <a-button 
            type="primary"
            danger
            @click="handleCompleteAllProjects"
            :loading="completingAll"
          >
            <RobotOutlined /> 一键完成所有课程
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主体内容 -->
    <div class="generator-content">
      <a-row :gutter="24">
        <!-- 左侧：项目列表 -->
        <a-col :span="14">
          <a-card title="课程项目">
            <!-- 统计信息 -->
            <template #extra>
              <a-statistic
                :value="projectList.length"
                suffix="个项目"
                :value-style="{ fontSize: '16px' }"
              />
            </template>

            <!-- 批量操作 -->
            <div class="batch-actions">
              <a-space>
                <a-checkbox
                  v-model:checked="selectAll"
                  :indeterminate="indeterminate"
                  @change="handleSelectAll"
                >
                  全选
                </a-checkbox>
                <a-divider type="vertical" />
                <span>已选择 {{ selectedProjects.length }} 个项目</span>
              </a-space>
            </div>

            <!-- 项目列表 -->
            <a-table
              :columns="projectColumns"
              :data-source="projectList"
              :row-selection="rowSelection"
              :pagination="{ pageSize: 10 }"
              :loading="loadingProjects"
              row-key="project_name"
              size="middle"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'project_name'">
                  <a-space>
                    <FolderOutlined style="color: #1890ff" />
                    <span>{{ record.project_name }}</span>
                  </a-space>
                </template>
                <template v-if="column.key === 'files'">
                  <span>{{ record.file_count }} 个文件</span>
                </template>
                <template v-if="column.key === 'largest_file'">
                  <a-tooltip :title="record.largest_file || '-'">
                    <span>{{ record.largest_file ? record.largest_file.split('/').pop() : '-' }}</span>
                    <span style="color: #999; margin-left: 4px">({{ Number(record.largest_file_size_mb ?? 0).toFixed(1) }} MB)</span>
                  </a-tooltip>
                </template>
                <template v-if="column.key === 'status'">
                  <a-tag v-if="record.status === '待处理'" color="default">
                    <ClockCircleOutlined /> 待处理
                  </a-tag>
                  <a-tag v-else-if="record.status === '部分完成'" color="orange">
                    <ExclamationCircleOutlined /> 部分完成
                  </a-tag>
                  <a-tag v-else-if="record.status === '已完成'" color="success">
                    <CheckCircleOutlined /> 已完成
                  </a-tag>
                </template>
                <template v-if="column.key === 'missing'">
                  <a-space v-if="Array.isArray(record.missing_components) && record.missing_components.length > 0">
                    <a-tag v-for="comp in record.missing_components" :key="comp" color="red" size="small">
                      缺 {{ comp }}
                    </a-tag>
                  </a-space>
                  <span v-else style="color: #52c41a">-</span>
                </template>
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a-button
                      v-if="record.status !== '已完成'"
                      size="small"
                      type="link"
                      @click="handleSupplementProject(record)"
                      :disabled="!!tasks[record.project_name]"
                    >
                      补充
                    </a-button>
                    <a-button
                      v-if="record.practice_id"
                      size="small"
                      type="link"
                      @click="viewPractice(record.practice_id)"
                    >
                      查看
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>

        <!-- 右侧：任务监控 -->
        <a-col :span="10">
          <a-card title="任务监控">
            <!-- 总体进度 -->
            <div class="overall-progress">
              <h4>总体进度</h4>
              <a-progress
                :percent="overallProgress"
                :status="overallStatus"
                :stroke-color="{
                  '0%': '#108ee9',
                  '100%': '#87d068'
                }"
              />
              <a-row :gutter="16" style="margin-top: 16px">
                <a-col :span="6">
                  <a-statistic
                    title="待处理"
                    :value="taskStats.pending"
                    :value-style="{ fontSize: '20px' }"
                  />
                </a-col>
                <a-col :span="6">
                  <a-statistic
                    title="处理中"
                    :value="taskStats.processing"
                    :value-style="{ fontSize: '20px', color: '#1890ff' }"
                  />
                </a-col>
                <a-col :span="6">
                  <a-statistic
                    title="已完成"
                    :value="taskStats.success"
                    :value-style="{ fontSize: '20px', color: '#52c41a' }"
                  />
                </a-col>
                <a-col :span="6">
                  <a-statistic
                    title="失败"
                    :value="taskStats.error"
                    :value-style="{ fontSize: '20px', color: '#f5222d' }"
                  />
                </a-col>
              </a-row>
            </div>

            <a-divider />

            <!-- 任务详情列表 -->
            <div class="task-list">
              <h4>任务详情</h4>
              <a-empty v-if="Object.keys(tasks).length === 0" description="暂无任务" />
              
              <a-timeline v-else>
                <a-timeline-item
                  v-for="(task, projectName) in tasks"
                  :key="task.task_id"
                  :color="getTimelineColor(task.status)"
                >
                  <template #dot>
                    <LoadingOutlined v-if="task.status === 'processing'" spin />
                    <CheckCircleOutlined v-else-if="task.status === 'success'" />
                    <CloseCircleOutlined v-else-if="task.status === 'error'" />
                    <ClockCircleOutlined v-else />
                  </template>
                  
                  <div class="task-item">
                    <div class="task-header">
                      <span class="task-filename">{{ projectName }}</span>
                      <a-tag :color="getStatusColor(task.status)" size="small">
                        {{ getStatusText(task.status) }}
                      </a-tag>
                    </div>
                    
                    <div class="task-progress" v-if="task.status === 'processing'">
                      <a-progress
                        :percent="task.progress || 0"
                        size="small"
                        :show-info="false"
                      />
                      <span class="progress-text">{{ task.message }}</span>
                    </div>
                    
                    <div class="task-result" v-if="task.status === 'success' && task.result">
                      <a-space>
                        <span v-if="task.result.stages_count > 0">✅ 补充 {{ task.result.stages_count }} 个关卡</span>
                        <span v-if="task.result.questions_count > 0">✅ 补充 {{ task.result.questions_count }} 道试题</span>
                        <span v-if="task.result.stages_count === 0 && task.result.questions_count === 0">✅ 项目已完整</span>
                        <a-button
                          v-if="task.result.practice_id"
                          type="link"
                          size="small"
                          @click="viewPractice(task.result.practice_id)"
                        >
                          查看课程
                        </a-button>
                      </a-space>
                    </div>
                    
                    <div class="task-error" v-if="task.status === 'error'">
                      <a-alert
                        :message="task.error || '处理失败'"
                        type="error"
                        show-icon
                        :style="{ marginTop: '8px' }"
                      />
                    </div>
                  </div>
                </a-timeline-item>
              </a-timeline>
            </div>
          </a-card>

          <!-- 配置面板 -->
          <a-card title="生成配置" style="margin-top: 16px">
            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <a-form-item label="课程分类">
                <a-select
                  v-model:value="config.categoryId"
                  placeholder="选择课程分类"
                >
                  <a-select-option :value="1">计算机基础</a-select-option>
                  <a-select-option :value="2">数据分析</a-select-option>
                  <a-select-option :value="3">人工智能</a-select-option>
                  <a-select-option :value="4">软件开发</a-select-option>
                </a-select>
              </a-form-item>
              
              <a-form-item label="并发数">
                <a-input-number
                  v-model:value="config.concurrency"
                  :min="1"
                  :max="5"
                />
                <div class="hint">同时处理的文件数量</div>
              </a-form-item>
              
              <a-form-item label="自动轮询">
                <a-switch v-model:checked="config.autoRefresh" />
                <span style="margin-left: 8px">每5秒自动更新任务状态</span>
              </a-form-item>
            </a-form>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  ReloadOutlined,
  RobotOutlined,
  FileTextOutlined,
  FilePptOutlined,
  FileWordOutlined,
  FolderOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import {
  getCourseProjects,
  supplementCourseProject,
  getTaskStatus as getTaskStatusApi,
  type CourseProject,
  type CourseGenerationTask
} from '@/api/ai-generation'

const router = useRouter()

// 项目列表
const projectList = ref<CourseProject[]>([])
const loadingProjects = ref(false)
const selectedProjects = ref<string[]>([])
const selectAll = ref(false)
const indeterminate = ref(false)

// 任务管理
const tasks = ref<Record<string, CourseGenerationTask>>({})
const batchGenerating = ref(false)
const completingAll = ref(false)
let pollTimer: number | null = null

// 配置
const config = reactive({
  categoryId: 1,
  concurrency: 3,
  autoRefresh: true
})

// 表格列配置
const projectColumns = [
  {
    title: '项目名称',
    dataIndex: 'project_name',
    key: 'project_name',
    width: '25%'
  },
  {
    title: '文件数',
    key: 'files',
    width: '10%'
  },
  {
    title: '主文件',
    key: 'largest_file',
    width: '20%'
  },
  {
    title: '状态',
    key: 'status',
    width: '15%'
  },
  {
    title: '缺失组件',
    key: 'missing',
    width: '20%'
  },
  {
    title: '操作',
    key: 'action',
    width: '10%'
  }
]

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedProjects.value,
  onChange: (selectedRowKeys: string[]) => {
    selectedProjects.value = selectedRowKeys
    updateSelectAllState()
  }
}))

// 计算属性
const overallProgress = computed(() => {
  const total = Object.keys(tasks.value).length
  if (total === 0) return 0
  
  const completed = Object.values(tasks.value).filter(t => 
    t.status === 'success' || t.status === 'error'
  ).length
  
  return Math.round((completed / total) * 100)
})

// 项目统计
const projectStats = computed(() => {
  const total = projectList.value.length
  const completed = projectList.value.filter(p => p.status === '已完成').length
  const partial = projectList.value.filter(p => p.status === '部分完成').length
  const pending = projectList.value.filter(p => p.status === '待处理').length
  
  return {
    total,
    completed,
    partial,
    pending,
    completionRate: total > 0 ? Math.round((completed / total) * 100) : 0
  }
})

const overallStatus = computed(() => {
  const hasError = Object.values(tasks.value).some(t => t.status === 'error')
  const allDone = Object.values(tasks.value).every(t => 
    t.status === 'success' || t.status === 'error'
  )
  
  if (hasError && allDone) return 'exception'
  if (allDone) return 'success'
  return 'active'
})

const taskStats = computed(() => {
  const stats = {
    pending: 0,
    processing: 0,
    success: 0,
    error: 0
  }
  
  Object.values(tasks.value).forEach(task => {
    stats[task.status]++
  })
  
  return stats
})

// 方法
const refreshFileList = async () => {
  loadingProjects.value = true
  try {
    const result = await getCourseProjects()
    console.log('Project list result:', result)  // 调试信息
    
    // 直接使用result，因为request已经返回了data部分
    if (result && result.projects) {
      projectList.value = result.projects
      const stats = projectStats.value
      message.success(`加载了 ${stats.total} 个项目：${stats.completed} 个已完成，${stats.partial} 个部分完成，${stats.pending} 个待处理`)
      console.log('Projects loaded:', projectList.value)  // 调试信息
    } else {
      message.error('加载项目列表失败')
      console.error('Invalid result format:', result)
    }
  } catch (error) {
    message.error('获取项目列表失败')
    console.error('Error fetching projects:', error)
  } finally {
    loadingProjects.value = false
  }
}

const handleSelectAll = (e: any) => {
  if (e.target.checked) {
    selectedProjects.value = projectList.value.map(p => p.project_name)
  } else {
    selectedProjects.value = []
  }
  updateSelectAllState()
}

const updateSelectAllState = () => {
  const total = projectList.value.length
  const selected = selectedProjects.value.length
  
  selectAll.value = selected === total && total > 0
  indeterminate.value = selected > 0 && selected < total
}

const handleSupplementProject = async (project: CourseProject) => {
  try {
    const result = await supplementCourseProject(project.project_name, config.categoryId)
    
    if (result && result.task_id) {
      // 添加任务到监控列表
      tasks.value[project.project_name] = {
        task_id: result.task_id,
        file_name: project.project_name,
        status: 'pending',
        progress: 0,
        message: '任务已创建'
      }
      
      const missingText = Array.isArray(project.missing_components) && project.missing_components.length > 0 
        ? `，补充: ${project.missing_components.join('、')}`
        : ''
      message.success(`开始补充项目: ${project.project_name}${missingText}`)
      
      // 开始轮询任务状态
      if (!pollTimer && config.autoRefresh) {
        startPolling()
      }
    } else {
      message.error('创建任务失败')
    }
  } catch (error) {
    message.error('补充任务创建失败')
    console.error(error)
  }
}

const handleBatchGenerate = async () => {
  if (selectedProjects.value.length === 0) {
    message.warning('请选择要处理的项目')
    return
  }
  
  batchGenerating.value = true
  const { concurrency } = config
  
  try {
    // 分批处理，控制并发数
    for (let i = 0; i < selectedProjects.value.length; i += concurrency) {
      const batch = selectedProjects.value.slice(i, i + concurrency)
      
      // 并发创建任务
      const promises = batch.map(projectName => {
        const project = projectList.value.find(p => p.project_name === projectName)
        if (project && project.status !== '已完成') {
          return handleSupplementProject(project)
        }
      })
      
      await Promise.all(promises)
      
      // 批次间延追
      if (i + concurrency < selectedProjects.value.length) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    const needSupplement = selectedProjects.value.filter(name => {
      const project = projectList.value.find(p => p.project_name === name)
      return project && project.status !== '已完成'
    }).length
    
    message.success(`已创建 ${needSupplement} 个补充任务`)
    selectedProjects.value = []
    updateSelectAllState()
  } finally {
    batchGenerating.value = false
  }
}

const pollTaskStatus = async () => {
  const pendingTasks = Object.entries(tasks.value)
    .filter(([_, task]) => task.status === 'pending' || task.status === 'processing')
  
  for (const [projectName, task] of pendingTasks) {
    try {
      const result = await getTaskStatusApi(task.task_id)
      
      if (result) {
        tasks.value[projectName] = {
          ...tasks.value[projectName],
          ...result
        }
        
        // 如果任务完成，刷新项目列表以更新状态
        if (result.status === 'success') {
          await refreshFileList()
        }
      }
    } catch (error) {
      console.error(`轮询任务 ${task.task_id} 状态失败:`, error)
    }
  }
  
  // 如果所有任务都完成了，停止轮询
  const allDone = Object.values(tasks.value).every(t => 
    t.status === 'success' || t.status === 'error'
  )
  
  if (allDone && pollTimer) {
    stopPolling()
    message.success('所有补充任务已完成')
  }
}

const startPolling = () => {
  if (pollTimer) return
  
  pollTimer = window.setInterval(() => {
    if (config.autoRefresh) {
      pollTaskStatus()
    }
  }, 5000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const getProjectTaskStatus = (projectName: string) => {
  return tasks.value[projectName]?.status
}

const getTimelineColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'gray',
    processing: 'blue',
    success: 'green',
    error: 'red'
  }
  return map[status] || 'gray'
}

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    pending: 'default',
    processing: 'processing',
    success: 'success',
    error: 'error'
  }
  return map[status] || 'default'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    success: '已完成',
    error: '失败'
  }
  return map[status] || status
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN')
}

const viewPractice = (practiceId: number) => {
  router.push(`/course/practice/${practiceId}/edit`)
}

const viewGeneratedCourse = (project: CourseProject) => {
  if (project.practice_id) {
    viewPractice(project.practice_id)
  }
}

// 一键完成所有课程
const handleCompleteAllProjects = async () => {
  completingAll.value = true
  try {
    const needSupplement = projectList.value.filter(p => p.status !== '已完成')
    
    if (needSupplement.length === 0) {
      message.info('所有项目已完成，无需补充')
      return
    }
    
    Modal.confirm({
      title: '确认操作',
      content: `将为 ${needSupplement.length} 个未完成的项目补充缺失的组件，是否继续？`,
      async onOk() {
        const { concurrency } = config
        
        // 分批处理
        for (let i = 0; i < needSupplement.length; i += concurrency) {
          const batch = needSupplement.slice(i, i + concurrency)
          
          const promises = batch.map(project => handleSupplementProject(project))
          await Promise.all(promises)
          
          if (i + concurrency < needSupplement.length) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
        
        message.success(`已为 ${needSupplement.length} 个项目创建补充任务`)
      },
      onCancel() {
        // 用户取消
      }
    })
    
    return
  } catch (error) {
    message.error('一键完成失败')
    console.error(error)
  } finally {
    completingAll.value = false
  }
}

// 生命周期
onMounted(() => {
  refreshFileList()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="less">
.batch-course-generator {
  background-color: #f0f2f5;
  min-height: 100vh;
  
  .generator-content {
    padding: 24px;
  }
  
  .batch-actions {
    margin-bottom: 16px;
    padding: 12px;
    background: #fafafa;
    border-radius: 4px;
  }
  
  .overall-progress {
    h4 {
      margin-bottom: 12px;
      color: #333;
    }
  }
  
  .task-list {
    max-height: 400px;
    overflow-y: auto;
    
    h4 {
      margin-bottom: 12px;
      color: #333;
    }
    
    .task-item {
      .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        
        .task-filename {
          font-weight: 500;
          color: #333;
        }
      }
      
      .task-progress {
        margin: 8px 0;
        
        .progress-text {
          display: block;
          margin-top: 4px;
          font-size: 12px;
          color: #666;
        }
      }
      
      .task-result {
        margin-top: 8px;
        padding: 8px;
        background: #f6ffed;
        border-radius: 4px;
        font-size: 13px;
      }
      
      .task-error {
        margin-top: 8px;
      }
    }
  }
  
  .hint {
    margin-top: 4px;
    font-size: 12px;
    color: #999;
  }
  
  :deep(.ant-timeline) {
    margin-top: 16px;
  }
  
  :deep(.ant-statistic-content) {
    font-size: 16px;
  }
}
</style>