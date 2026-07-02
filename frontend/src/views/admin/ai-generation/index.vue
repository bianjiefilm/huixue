<template>
  <div class="ai-generation-container">
    <div class="page-header">
      <h1>
        <RobotOutlined /> 内容智能生成
      </h1>
      <p class="subtitle">使用AI技术快速生成高质量的教学内容，包括课程关卡、实训资源、考核试题等</p>
    </div>

    <a-tabs v-model:activeKey="activeTab" type="card" @change="handleTabChange">
      <a-tab-pane key="course" tab="课程资源生成">
        <CourseGeneration ref="courseGenerationRef" />
      </a-tab-pane>
      <a-tab-pane key="training" tab="实训资源生成">
        <TrainingGeneration ref="trainingGenerationRef" />
      </a-tab-pane>
    </a-tabs>

    <div class="task-history">
      <h2>
        <HistoryOutlined /> 近期生成任务
        <a-button type="link" size="small" @click="refreshTaskHistory">
          <ReloadOutlined /> 刷新
        </a-button>
      </h2>
      <a-table
        :columns="taskColumns"
        :data-source="taskHistory"
        :loading="taskHistoryLoading"
        :pagination="{
          pageSize: 20,
          showSizeChanger: false,
          showTotal: (total) => `共 ${total} 条记录`
        }"
        row-key="task_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="record.type === 'course' ? 'blue' : 'green'">
              {{ record.type === 'course' ? '课程' : '实训' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge v-if="record.status === 'SUCCESS'" status="success" text="成功" />
            <a-badge v-else-if="record.status === 'ERROR'" status="error" text="失败" />
            <a-badge v-else-if="record.status === 'PROCESSING'" status="processing" text="处理中" />
            <a-badge v-else status="default" text="等待中" />
          </template>
          <template v-else-if="column.key === 'progress'">
            <a-progress
              :percent="record.progress"
              :status="record.status === 'ERROR' ? 'exception' : 'active'"
              :stroke-color="{
                '0%': '#108ee9',
                '100%': '#87d068'
              }"
            />
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button
                v-if="record.status === 'SUCCESS' && record.result?.database_result?.success"
                type="link"
                size="small"
                @click="viewGeneratedContent(record)"
              >
                查看结果
              </a-button>
              <a-button
                v-if="record.status === 'SUCCESS' && record.result?.database_result?.practice_id"
                type="link"
                size="small"
                @click="goToCourseDetail(record.result.database_result.practice_id)"
              >
                进入课程
              </a-button>
              <a-button
                v-if="record.status === 'SUCCESS' && record.result?.database_result?.training_id"
                type="link"
                size="small"
                @click="goToTrainingDetail(record.result.database_result.training_id)"
              >
                进入实训
              </a-button>
              <a-button
                v-if="record.status === 'ERROR'"
                type="link"
                size="small"
                danger
                @click="viewError(record)"
              >
                查看错误
              </a-button>
              <a-button
                v-if="record.status === 'PROCESSING'"
                type="link"
                size="small"
                @click="cancelTask(record)"
                danger
              >
                取消
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 结果查看弹窗 -->
    <a-modal
      v-model:open="resultModalVisible"
      title="生成结果详情"
      width="80%"
      :footer="null"
    >
      <div v-if="selectedResult" class="result-detail">
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="任务ID">{{ selectedResult.task_id }}</a-descriptions-item>
          <a-descriptions-item label="生成类型">
            {{ selectedResult.type === 'course' ? '课程资源' : '实训资源' }}
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">{{ selectedResult.create_time }}</a-descriptions-item>
          <a-descriptions-item label="完成时间">{{ selectedResult.complete_time }}</a-descriptions-item>
          <a-descriptions-item label="数据库保存">
            <a-tag :color="selectedResult.result?.database_result?.success ? 'success' : 'error'">
              {{ selectedResult.result?.database_result?.success ? '成功' : '失败' }}
            </a-tag>
            <span v-if="selectedResult.result?.database_result?.message" class="ml-2">
              {{ selectedResult.result.database_result.message }}
            </span>
          </a-descriptions-item>
        </a-descriptions>
        
        <div v-if="selectedResult.type === 'course' && selectedResult.result?.course_package" class="mt-4">
          <h3>课程元数据</h3>
          <pre>{{ JSON.stringify(selectedResult.result.course_package.metadata, null, 2) }}</pre>
          
          <h3 class="mt-4">生成的文件</h3>
          <a-list
            :data-source="selectedResult.result.course_package.processed_files"
            :bordered="true"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta
                  :title="item.original_filename"
                  :description="`类型: ${item.file_type} | 状态: ${item.processing_status}`"
                />
                <template #actions>
                  <a-button type="link" size="small" @click="viewFileDetail(item)">
                    查看详情
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </div>
        
        <div v-if="selectedResult.type === 'training' && selectedResult.result?.training_package" class="mt-4">
          <h3>实训元数据</h3>
          <pre>{{ JSON.stringify(selectedResult.result.training_package.metadata, null, 2) }}</pre>
          
          <h3 class="mt-4">实训手册</h3>
          <div class="handbook-preview" v-html="renderMarkdown(selectedResult.result.training_package.handbook_markdown)"></div>
        </div>
      </div>
    </a-modal>

    <!-- 错误详情弹窗 -->
    <a-modal
      v-model:open="errorModalVisible"
      title="错误详情"
      width="600px"
      :footer="null"
    >
      <a-alert
        v-if="selectedError"
        type="error"
        :message="selectedError.error_message || '任务执行失败'"
        show-icon
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  RobotOutlined,
  HistoryOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import { marked } from 'marked'
import CourseGeneration from './components/CourseGeneration.vue'
import TrainingGeneration from './components/TrainingGeneration.vue'
import type { TaskStatus } from '@/api/ai-generation'

const router = useRouter()
const activeTab = ref('course')
const courseGenerationRef = ref()
const trainingGenerationRef = ref()

// 任务历史相关
const taskHistory = ref<any[]>([])
const taskHistoryLoading = ref(false)
const pollingInterval = ref<number | null>(null)

// 弹窗相关
const resultModalVisible = ref(false)
const selectedResult = ref<any>(null)
const errorModalVisible = ref(false)
const selectedError = ref<any>(null)

// 表格列配置
const taskColumns = [
  {
    title: '任务ID',
    dataIndex: 'task_id',
    key: 'task_id',
    width: 180,
    ellipsis: true
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type',
    width: 80
  },
  {
    title: '标题',
    dataIndex: 'title',
    key: 'title',
    ellipsis: true
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '进度',
    dataIndex: 'progress',
    key: 'progress',
    width: 150
  },
  {
    title: '创建时间',
    dataIndex: 'create_time',
    key: 'create_time',
    width: 180
  },
  {
    title: '操作',
    key: 'action',
    width: 200
  }
]

// 处理标签页切换
const handleTabChange = (key: string) => {
  activeTab.value = key
  refreshTaskHistory()
}

// 刷新任务历史
const refreshTaskHistory = async () => {
  taskHistoryLoading.value = true
  try {
    // 从子组件获取任务列表
    const courseTasks = courseGenerationRef.value?.getTaskList() || []
    const trainingTasks = trainingGenerationRef.value?.getTaskList() || []
    
    // 合并并按时间排序
    taskHistory.value = [...courseTasks, ...trainingTasks]
      .sort((a, b) => new Date(b.create_time).getTime() - new Date(a.create_time).getTime())
      .slice(0, 20) // 只显示最近20条
  } catch (error) {
    console.error('Failed to refresh task history:', error)
  } finally {
    taskHistoryLoading.value = false
  }
}

// 查看生成的内容
const viewGeneratedContent = (record: any) => {
  selectedResult.value = record
  resultModalVisible.value = true
}

// 查看错误详情
const viewError = (record: any) => {
  selectedError.value = record
  errorModalVisible.value = true
}

// 取消任务
const cancelTask = async (record: any) => {
  message.warning('任务取消功能暂未实现')
}

// 进入课程详情
const goToCourseDetail = (practiceId: number) => {
  router.push(`/admin/course/detail/${practiceId}`)
}

// 进入实训详情
const goToTrainingDetail = (trainingId: number) => {
  router.push(`/project/${trainingId}`)
}

// 查看文件详情
const viewFileDetail = (file: any) => {
  console.log('View file detail:', file)
  // 可以展开显示更多文件内容
}

// 渲染Markdown
const renderMarkdown = (markdown: string) => {
  return marked(markdown || '')
}

// 定期刷新进行中的任务
const startPolling = () => {
  pollingInterval.value = window.setInterval(() => {
    const hasProcessingTasks = taskHistory.value.some(task => task.status === 'PROCESSING')
    if (hasProcessingTasks) {
      refreshTaskHistory()
    }
  }, 2000)
}

const stopPolling = () => {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

onMounted(() => {
  refreshTaskHistory()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style lang="less" scoped>
.ai-generation-container {
  .page-header {
    margin-bottom: 24px;
    
    h1 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 8px;
      color: #000000;
      
      .anticon {
        margin-right: 8px;
        color: #1890ff;
      }
    }
    
    .subtitle {
      color: #666666;
      font-size: 14px;
      margin: 0;
    }
  }
  
  .task-history {
    margin-top: 24px;
    
    h2 {
      font-size: 18px;
      font-weight: 500;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      
      .anticon {
        margin-right: 8px;
      }
    }
  }
  
  .result-detail {
    max-height: 70vh;
    overflow-y: auto;
    
    pre {
      background: #f5f5f5;
      padding: 12px;
      border-radius: 4px;
      overflow-x: auto;
    }
    
    .handbook-preview {
      background: #f5f5f5;
      padding: 16px;
      border-radius: 4px;
      max-height: 400px;
      overflow-y: auto;
      
      :deep(h1), :deep(h2), :deep(h3) {
        margin-top: 16px;
        margin-bottom: 8px;
      }
      
      :deep(ul), :deep(ol) {
        padding-left: 24px;
      }
      
      :deep(code) {
        background: #e8e8e8;
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
  
  .mt-4 {
    margin-top: 16px;
  }
  
  .ml-2 {
    margin-left: 8px;
  }
}
</style>