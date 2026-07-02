<template>
  <div class="course-detail-panel">
    <a-descriptions title="课程基本信息" :column="1" bordered>
      <a-descriptions-item label="课程ID">{{ course.id }}</a-descriptions-item>
      <a-descriptions-item label="课程名称">{{ course.title }}</a-descriptions-item>
      <a-descriptions-item label="课程描述" v-if="course.description">
        {{ course.description }}
      </a-descriptions-item>
      <a-descriptions-item label="课程简介" v-if="isPractice && course.intro">
        {{ course.intro }}
      </a-descriptions-item>
      <a-descriptions-item label="课程总结" v-if="isPractice && course.summary">
        {{ course.summary }}
      </a-descriptions-item>
      <a-descriptions-item label="课程手册" v-if="isTraining && course.handbook_content">
        <div class="handbook-content" v-html="course.handbook_content"></div>
      </a-descriptions-item>
    </a-descriptions>

    <a-descriptions title="课程分类" :column="2" bordered style="margin-top: 16px;">
      <a-descriptions-item label="方向" v-if="isPractice">
        {{ getCategoryName(course.direction) }}
      </a-descriptions-item>
      <a-descriptions-item label="行业" v-if="isTraining">
        {{ getCategoryName(course.industry) }}
      </a-descriptions-item>
      <a-descriptions-item label="分类" v-if="isPractice">
        {{ getCategoryName(course.category) }}
      </a-descriptions-item>
      <a-descriptions-item label="难度">
        <a-tag :color="getDifficultyColor(course.difficulty)">
          {{ getDifficultyText(course.difficulty) }}
        </a-tag>
      </a-descriptions-item>
    </a-descriptions>

    <a-descriptions title="课程统计" :column="2" bordered style="margin-top: 16px;">
      <a-descriptions-item label="任务数量" v-if="isPractice">
        {{ course.task_count || 0 }} 个
      </a-descriptions-item>
      <a-descriptions-item label="课程学时" v-if="isTraining">
        {{ course.course_hours || 0 }} 学时
      </a-descriptions-item>
      <a-descriptions-item label="金币奖励" v-if="isPractice">
        {{ course.coin || 0 }} 金币
      </a-descriptions-item>
      <a-descriptions-item label="实训类型" v-if="isTraining">
        {{ getTrainingTypeText(course.training_type) }}
      </a-descriptions-item>
    </a-descriptions>

    <a-descriptions title="创建信息" :column="2" bordered style="margin-top: 16px;">
      <a-descriptions-item label="创建者">
        <a-avatar size="small" style="margin-right: 8px;">
          {{ course.creator?.full_name?.charAt(0) || course.creator?.username?.charAt(0) || 'S' }}
        </a-avatar>
        {{ course.creator?.full_name || course.creator?.username || '系统导入' }}
      </a-descriptions-item>
      <a-descriptions-item label="创建时间">
        {{ formatDateTime(course.created_at) }}
      </a-descriptions-item>
      <a-descriptions-item label="更新时间">
        {{ formatDateTime(course.updated_at) }}
      </a-descriptions-item>
      <a-descriptions-item label="发布状态">
        <a-tag :color="getStatusColor()">
          {{ getStatusText() }}
        </a-tag>
      </a-descriptions-item>
    </a-descriptions>

    <!-- 技术配置信息 -->
    <a-descriptions 
      title="技术配置" 
      :column="2" 
      bordered 
      style="margin-top: 16px;"
      v-if="hasEnvironmentInfo"
    >
      <a-descriptions-item label="环境ID" v-if="course.environment_id">
        {{ course.environment_id }}
      </a-descriptions-item>
      <a-descriptions-item label="存储限制" v-if="course.storage_limit">
        {{ course.storage_limit }}
      </a-descriptions-item>
      <a-descriptions-item label="内存限制" v-if="course.memory_limit">
        {{ course.memory_limit }}
      </a-descriptions-item>
      <a-descriptions-item label="CPU限制" v-if="course.cpu_limit">
        {{ course.cpu_limit }}
      </a-descriptions-item>
    </a-descriptions>

    <!-- 实训特殊配置 -->
    <a-descriptions 
      title="实训要求" 
      :column="2" 
      bordered 
      style="margin-top: 16px;"
      v-if="isTraining"
    >
      <a-descriptions-item label="设计文件要求">
        <a-tag :color="course.require_design_files ? 'green' : 'gray'">
          {{ course.require_design_files ? '需要' : '不需要' }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="实验报告要求">
        <a-tag :color="course.require_experiment_report ? 'green' : 'gray'">
          {{ course.require_experiment_report ? '需要' : '不需要' }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="作业节点" v-if="course.assignment_nodes">
        {{ course.assignment_nodes }}
      </a-descriptions-item>
    </a-descriptions>

    <!-- 课程封面 -->
    <div class="cover-section" style="margin-top: 16px;" v-if="course.cover_url">
      <h4>课程封面</h4>
      <img :src="course.cover_url" :alt="course.title" class="course-cover-image" />
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons" style="margin-top: 24px;">
      <a-space>
        <a-button 
          type="primary" 
          danger 
          v-if="course.can_unpublish"
          @click="handleAction('unpublish')"
        >
          <CloudDownloadOutlined />
          下架课程
        </a-button>
        
        <a-button 
          type="primary" 
          v-if="course.can_publish"
          @click="handleAction('publish')"
        >
          <CloudUploadOutlined />
          发布课程
        </a-button>
        
        <a-button @click="handleViewFullDetail">
          <EyeOutlined />
          查看完整详情
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { CloudDownloadOutlined, CloudUploadOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { CourseManagementAPI } from '@/api/course-management'
import type { PracticeCourseDetail, TrainingCourseDetail } from '@/api/course-management'

interface Props {
  course: PracticeCourseDetail | TrainingCourseDetail
  courseType: 'practice' | 'training'
}

interface Emits {
  (e: 'action', action: string, course: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性
const isPractice = computed(() => props.courseType === 'practice')
const isTraining = computed(() => props.courseType === 'training')

const hasEnvironmentInfo = computed(() => {
  return props.course.environment_id || 
         props.course.storage_limit || 
         props.course.memory_limit || 
         props.course.cpu_limit
})

// 方法
const getCategoryName = (key?: string) => {
  if (!key) return '-'
  
  // 这里可以根据实际的分类映射返回中文名称
  const categoryMap: Record<string, string> = {
    // 实践课程方向
    'artificial_intelligence': '人工智能',
    'data_science': '数据科学',
    'web_development': 'Web开发',
    'mobile_development': '移动开发',
    'database': '数据库',
    'software_engineering': '软件工程',
    'cybersecurity': '网络安全',
    'cloud_computing': '云计算',
    'algorithms': '算法与数据结构',
    
    // 实训课程行业
    'finance': '金融行业',
    'healthcare': '医疗健康',
    'education': '教育行业',
    'retail': '零售电商',
    'manufacturing': '制造业',
    'transportation': '交通运输',
    'energy': '能源行业',
    'media': '媒体娱乐'
  }
  
  return categoryMap[key] || key
}

const getDifficultyText = (difficulty?: string) => {
  return CourseManagementAPI.getDifficultyText(difficulty)
}

const getDifficultyColor = (difficulty?: string) => {
  const colorMap: Record<string, string> = {
    'BEGINNER': 'green',
    'INTERMEDIATE': 'orange',
    'ADVANCED': 'red'
  }
  return difficulty ? colorMap[difficulty] || 'default' : 'default'
}

const getTrainingTypeText = (type?: string) => {
  const typeMap: Record<string, string> = {
    'INDIVIDUAL': '个人实训',
    'TEAM': '团队实训',
    'PROJECT': '项目实训'
  }
  return type ? typeMap[type] || type : '-'
}

const getStatusText = () => {
  if (isPractice.value) {
    const course = props.course as PracticeCourseDetail
    if (course.visibility === 'PUBLIC' && course.publish_status === 'PUBLISHED') {
      return '已发布'
    } else if (course.visibility === 'PRIVATE') {
      return '个人发布'
    } else if (course.publish_status === 'EDITING') {
      return '未发布'
    }
  } else {
    const course = props.course as TrainingCourseDetail
    if (course.visibility === 'PUBLIC' && course.publish_status === 'PUBLISHED') {
      return '已发布'
    } else if (course.visibility === 'PRIVATE') {
      return '个人发布'
    } else if (course.publish_status === 'EDITING') {
      return '未发布'
    }
  }
  return '未知状态'
}

const getStatusColor = () => {
  if (isPractice.value) {
    const course = props.course as PracticeCourseDetail
    if (course.visibility === 'PUBLIC' && course.publish_status === 'PUBLISHED') {
      return 'green'
    } else if (course.visibility === 'PRIVATE') {
      return 'orange'
    } else if (course.publish_status === 'EDITING') {
      return 'gray'
    }
  } else {
    const course = props.course as TrainingCourseDetail
    if (course.visibility === 'PUBLIC' && course.publish_status === 'PUBLISHED') {
      return 'green'
    } else if (course.visibility === 'PRIVATE') {
      return 'orange'
    } else if (course.publish_status === 'EDITING') {
      return 'gray'
    }
  }
  return 'default'
}

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const handleAction = (action: string) => {
  emit('action', action, props.course)
}

const handleViewFullDetail = () => {
  // 可以跳转到完整的课程详情页面
  const routePath = isPractice.value 
    ? `/course-management/practice/${props.course.id}`
    : `/course-management/training/${props.course.id}`
  
  window.open(routePath, '_blank')
}
</script>

<style scoped>
.course-detail-panel {
  max-height: 70vh;
  overflow-y: auto;
}

.handbook-content {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
}

.course-cover-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.cover-section h4 {
  margin-bottom: 12px;
  color: #333;
}

.action-buttons {
  border-top: 1px solid #e8e8e8;
  padding-top: 16px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  color: #333;
  width: 120px;
}

:deep(.ant-descriptions-item-content) {
  color: #666;
}

:deep(.ant-descriptions-title) {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}
</style> 