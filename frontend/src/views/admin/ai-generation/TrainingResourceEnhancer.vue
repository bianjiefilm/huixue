<template>
  <div class="training-resource-enhancer">
    <!-- 页面标题 -->
    <a-page-header
      title="实训资源智能增强"
      sub-title="自动检测并补充实训项目中缺失的任务、数据集和实验笔记"
      @back="() => $router.back()"
    >
      <template #extra>
        <a-space>
          <a-button @click="refreshProjectList">
            <ReloadOutlined /> 刷新列表
          </a-button>
          <a-button 
            type="primary" 
            @click="handleBatchEnhance"
            :disabled="selectedProjects.length === 0"
            :loading="batchEnhancing"
          >
            <ExperimentOutlined /> 批量增强项目 ({{ selectedProjects.length }})
          </a-button>
          <a-button 
            type="primary"
            danger
            @click="handleEnhanceAllProjects"
            :loading="enhancingAll"
          >
            <ThunderboltOutlined /> 一键增强所有项目
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主体内容 -->
    <div class="enhancer-content">
      <a-row :gutter="24">
        <!-- 左侧：项目列表 -->
        <a-col :span="14">
          <a-card title="实训项目">
            <!-- 统计信息 -->
            <template #extra>
              <a-space>
                <a-statistic
                  :value="projectList.length"
                  suffix="个项目"
                  :value-style="{ fontSize: '16px' }"
                />
                <a-divider type="vertical" />
                <a-tag color="success">完成 {{ projectStats.completed }}</a-tag>
                <a-tag color="orange">部分 {{ projectStats.partial }}</a-tag>
                <a-tag color="default">待处理 {{ projectStats.pending }}</a-tag>
              </a-space>
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
                <a-divider type="vertical" />
                <a-radio-group v-model:value="filterStatus" button-style="solid" size="small">
                  <a-radio-button value="all">全部</a-radio-button>
                  <a-radio-button value="待处理">待处理</a-radio-button>
                  <a-radio-button value="部分完成">部分完成</a-radio-button>
                  <a-radio-button value="已完成">已完成</a-radio-button>
                </a-radio-group>
              </a-space>
            </div>

            <!-- 项目列表 -->
            <a-table
              :columns="projectColumns"
              :data-source="filteredProjects"
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
                  <a-tooltip :title="record.largest_file">
                    <span>{{ record.largest_file.split('/').pop() }}</span>
                    <span style="color: #999; margin-left: 4px">({{ record.largest_file_size_mb.toFixed(1) }} MB)</span>
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
                <template v-if="column.key === 'components'">
                  <a-space>
                    <a-tag :color="record.has_training ? 'green' : 'red'" size="small">
                      {{ record.has_training ? '✓' : '✗' }} 任务
                    </a-tag>
                    <a-tag :color="record.has_datasets ? 'green' : 'red'" size="small">
                      {{ record.has_datasets ? '✓' : '✗' }} 数据
                    </a-tag>
                    <a-tag :color="record.has_notebooks ? 'green' : 'red'" size="small">
                      {{ record.has_notebooks ? '✓' : '✗' }} 笔记
                    </a-tag>
                  </a-space>
                </template>
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a-button
                      v-if="record.status !== '已完成'"
                      size="small"
                      type="link"
                      @click="handleEnhanceProject(record)"
                      :disabled="!!tasks[record.project_name]"
                    >
                      增强
                    </a-button>
                    <a-button
                      v-if="record.training_id"
                      size="small"
                      type="link"
                      @click="viewTraining(record.training_id)"
                    >
                      查看
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>

        <!-- 右侧：任务监控和配置 -->
        <a-col :span="10">
          <!-- 项目完成度统计 -->
          <a-card title="项目完成度" style="margin-bottom: 16px">
            <a-progress
              :percent="projectStats.completionRate"
              :stroke-color="{
                '0%': '#108ee9',
                '100%': '#87d068'
              }"
            />
            <a-row :gutter="16" style="margin-top: 16px">
              <a-col :span="8">
                <a-statistic
                  title="已完成"
                  :value="projectStats.completed"
                  :value-style="{ fontSize: '20px', color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="部分完成"
                  :value="projectStats.partial"
                  :value-style="{ fontSize: '20px', color: '#faad14' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="待处理"
                  :value="projectStats.pending"
                  :value-style="{ fontSize: '20px', color: '#999' }"
                />
              </a-col>
            </a-row>
          </a-card>

          <!-- 任务监控 -->
          <a-card title="任务监控">
            <!-- 总体进度 -->
            <div class="overall-progress">
              <h4>处理进度</h4>
              <a-progress
                :percent="overallProgress"
                :status="overallStatus"
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
                        <span v-if="task.result.training_generated">✅ 生成实训任务</span>
                        <span v-if="task.result.datasets_generated">✅ 生成数据集</span>
                        <span v-if="task.result.notebooks_generated">✅ 生成实验笔记</span>
                        <span v-if="task.result.total_generated === 0">✅ 项目已完整</span>
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
          <a-card title="增强配置" style="margin-top: 16px">
            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <a-form-item label="并发数">
                <a-input-number
                  v-model:value="config.concurrency"
                  :min="1"
                  :max="5"
                />
                <div class="hint">同时处理的项目数量</div>
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
  ExperimentOutlined,
  ThunderboltOutlined,
  FolderOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import {
  getTrainingProjects,
  supplementTrainingProject,
  getTaskStatus,
  type TrainingProject,
  type CourseGenerationTask
} from '@/api/ai-generation'

const router = useRouter()

// 项目列表
const projectList = ref<TrainingProject[]>([])
const loadingProjects = ref(false)
const selectedProjects = ref<string[]>([])
const selectAll = ref(false)
const indeterminate = ref(false)
const filterStatus = ref('all')

// 任务管理
const tasks = ref<Record<string, CourseGenerationTask>>({})
const batchEnhancing = ref(false)
const enhancingAll = ref(false)
let pollTimer: number | null = null

// 配置
const config = reactive({
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
    width: '12%'
  },
  {
    title: '组件状态',
    key: 'components',
    width: '23%'
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

// 过滤后的项目列表
const filteredProjects = computed(() => {
  if (filterStatus.value === 'all') {
    return projectList.value
  }
  return projectList.value.filter(p => p.status === filterStatus.value)
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

// 计算属性
const overallProgress = computed(() => {
  const total = Object.keys(tasks.value).length
  if (total === 0) return 0
  
  const completed = Object.values(tasks.value).filter(t => 
    t.status === 'success' || t.status === 'error'
  ).length
  
  return Math.round((completed / total) * 100)
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
const refreshProjectList = async () => {
  loadingProjects.value = true
  try {
    const result = await getTrainingProjects()
    console.log('Training projects result:', result)
    
    if (result && result.projects) {
      projectList.value = result.projects
      const stats = projectStats.value
      message.success(`加载了 ${stats.total} 个实训项目：${stats.completed} 个已完成，${stats.partial} 个部分完成，${stats.pending} 个待处理`)
      console.log('Projects loaded:', projectList.value)
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
    selectedProjects.value = filteredProjects.value.map(p => p.project_name)
  } else {
    selectedProjects.value = []
  }
  updateSelectAllState()
}

const updateSelectAllState = () => {
  const total = filteredProjects.value.length
  const selected = selectedProjects.value.length
  
  selectAll.value = selected === total && total > 0
  indeterminate.value = selected > 0 && selected < total
}

const handleEnhanceProject = async (project: TrainingProject) => {
  try {
    const result = await supplementTrainingProject(project.project_name)
    
    if (result && result.task_id) {
      // 添加任务到监控列表
      tasks.value[project.project_name] = {
        task_id: result.task_id,
        file_name: project.project_name,
        status: 'pending',
        progress: 0,
        message: '任务已创建'
      }
      
      const missingText = project.missing_components.length > 0 
        ? `，增强: ${project.missing_components.join('、')}`
        : ''
      message.success(`开始增强项目: ${project.project_name}${missingText}`)
      
      // 开始轮询任务状态
      if (!pollTimer && config.autoRefresh) {
        startPolling()
      }
    } else {
      message.error('创建任务失败')
    }
  } catch (error) {
    message.error('增强任务创建失败')
    console.error(error)
  }
}

const handleBatchEnhance = async () => {
  if (selectedProjects.value.length === 0) {
    message.warning('请选择要处理的项目')
    return
  }
  
  batchEnhancing.value = true
  const { concurrency } = config
  
  try {
    // 分批处理，控制并发数
    for (let i = 0; i < selectedProjects.value.length; i += concurrency) {
      const batch = selectedProjects.value.slice(i, i + concurrency)
      
      // 并发创建任务
      const promises = batch.map(projectName => {
        const project = projectList.value.find(p => p.project_name === projectName)
        if (project && project.status !== '已完成') {
          return handleEnhanceProject(project)
        }
      })
      
      await Promise.all(promises)
      
      // 批次间延迟
      if (i + concurrency < selectedProjects.value.length) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    const needEnhance = selectedProjects.value.filter(name => {
      const project = projectList.value.find(p => p.project_name === name)
      return project && project.status !== '已完成'
    }).length
    
    message.success(`已创建 ${needEnhance} 个增强任务`)
    selectedProjects.value = []
    updateSelectAllState()
  } finally {
    batchEnhancing.value = false
  }
}

const handleEnhanceAllProjects = async () => {
  enhancingAll.value = true
  try {
    const needEnhance = projectList.value.filter(p => p.status !== '已完成')
    
    if (needEnhance.length === 0) {
      message.info('所有项目已完成，无需增强')
      return
    }
    
    Modal.confirm({
      title: '确认操作',
      content: `将为 ${needEnhance.length} 个未完成的项目增强缺失的组件，是否继续？`,
      async onOk() {
        const { concurrency } = config
        
        // 分批处理
        for (let i = 0; i < needEnhance.length; i += concurrency) {
          const batch = needEnhance.slice(i, i + concurrency)
          
          const promises = batch.map(project => handleEnhanceProject(project))
          await Promise.all(promises)
          
          if (i + concurrency < needEnhance.length) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
        
        message.success(`已为 ${needEnhance.length} 个项目创建增强任务`)
      },
      onCancel() {
        // 用户取消
      }
    })
    
    return
  } catch (error) {
    message.error('一键增强失败')
    console.error(error)
  } finally {
    enhancingAll.value = false
  }
}

const pollTaskStatus = async () => {
  const pendingTasks = Object.entries(tasks.value)
    .filter(([_, task]) => task.status === 'pending' || task.status === 'processing')
  
  for (const [projectName, task] of pendingTasks) {
    try {
      const result = await getTaskStatus(task.task_id)
      
      if (result) {
        tasks.value[projectName] = {
          ...tasks.value[projectName],
          ...result
        }
        
        // 如果任务完成，刷新项目列表以更新状态
        if (result.status === 'success') {
          await refreshProjectList()
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
    message.success('所有增强任务已完成')
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

const getTaskStatus = (projectName: string) => {
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

const viewTraining = (trainingId: number) => {
  router.push(`/training/${trainingId}/edit`)
}

// 生命周期
onMounted(() => {
  refreshProjectList()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped lang="less">
.training-resource-enhancer {
  background-color: #f0f2f5;
  min-height: 100vh;
  
  .enhancer-content {
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