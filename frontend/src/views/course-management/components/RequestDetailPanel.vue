<template>
  <div class="request-detail-panel">
    <a-descriptions title="申请基本信息" :column="1" bordered>
      <a-descriptions-item label="申请ID">{{ request.id }}</a-descriptions-item>
      <a-descriptions-item label="课程名称">
        <a @click="viewCourseDetail" class="course-link">
          {{ request.course.title }}
        </a>
        <a-tag :color="getCourseTypeColor(request.course_type)" size="small" style="margin-left: 8px;">
          {{ request.course_type_text }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="申请人">
        <a-avatar size="small" style="margin-right: 8px;">
          {{ request.applicant.full_name?.charAt(0) || request.applicant.username?.charAt(0) }}
        </a-avatar>
        {{ request.applicant.full_name || request.applicant.username }}
      </a-descriptions-item>
      <a-descriptions-item label="申请类型">
        <a-tag :color="getRequestTypeColor(request.request_type)">
          {{ request.request_type_text }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="申请状态">
        <a-tag :color="getStatusColor(request.status)">
          {{ request.status_text }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="申请时间">
        {{ formatDateTime(request.applied_at) }}
      </a-descriptions-item>
      <a-descriptions-item label="申请理由" v-if="request.application_reason">
        <div class="reason-content">{{ request.application_reason }}</div>
      </a-descriptions-item>
    </a-descriptions>

    <!-- 审批信息 -->
    <a-descriptions 
      title="审批信息" 
      :column="1" 
      bordered 
      style="margin-top: 16px;"
      v-if="isReviewed"
    >
      <a-descriptions-item label="审批人">
        <a-avatar size="small" style="margin-right: 8px;" v-if="request.reviewer">
          {{ request.reviewer.full_name?.charAt(0) || request.reviewer.username?.charAt(0) }}
        </a-avatar>
        {{ request.reviewer?.full_name || request.reviewer?.username || '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="审批时间">
        {{ request.reviewed_at ? formatDateTime(request.reviewed_at) : '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="审批意见" v-if="request.review_comments">
        <div class="review-comments">{{ request.review_comments }}</div>
      </a-descriptions-item>
    </a-descriptions>

    <!-- 撤销信息 -->
    <a-descriptions 
      title="撤销信息" 
      :column="1" 
      bordered 
      style="margin-top: 16px;"
      v-if="isCancelled"
    >
      <a-descriptions-item label="撤销时间">
        {{ request.cancelled_at ? formatDateTime(request.cancelled_at) : '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="撤销原因" v-if="request.cancelled_reason">
        <div class="cancel-reason">{{ request.cancelled_reason }}</div>
      </a-descriptions-item>
    </a-descriptions>

    <!-- 申请历史时间线 -->
    <div class="timeline-section" style="margin-top: 24px;">
      <h4>申请流程</h4>
      <a-timeline mode="left">
        <a-timeline-item color="green">
          <template #dot>
            <ClockCircleOutlined style="font-size: 16px;" />
          </template>
          <div class="timeline-content">
            <div class="timeline-title">提交申请</div>
            <div class="timeline-time">{{ formatDateTime(request.applied_at) }}</div>
            <div class="timeline-desc">{{ request.applicant.full_name || request.applicant.username }} 提交了{{ request.request_type_text }}</div>
          </div>
        </a-timeline-item>

        <a-timeline-item 
          v-if="isReviewed"
          :color="request.status === 'APPROVED' ? 'green' : 'red'"
        >
          <template #dot>
            <CheckCircleOutlined v-if="request.status === 'APPROVED'" style="font-size: 16px;" />
            <CloseCircleOutlined v-else style="font-size: 16px;" />
          </template>
          <div class="timeline-content">
            <div class="timeline-title">
              {{ request.status === 'APPROVED' ? '申请通过' : '申请驳回' }}
            </div>
            <div class="timeline-time">{{ formatDateTime(request.reviewed_at!) }}</div>
            <div class="timeline-desc">
              {{ request.reviewer?.full_name || request.reviewer?.username }} 
              {{ request.status === 'APPROVED' ? '同意了' : '驳回了' }}此申请
            </div>
            <div class="timeline-comments" v-if="request.review_comments">
              审批意见：{{ request.review_comments }}
            </div>
          </div>
        </a-timeline-item>

        <a-timeline-item 
          v-if="isCancelled"
          color="gray"
        >
          <template #dot>
            <StopOutlined style="font-size: 16px;" />
          </template>
          <div class="timeline-content">
            <div class="timeline-title">申请撤销</div>
            <div class="timeline-time">{{ formatDateTime(request.cancelled_at!) }}</div>
            <div class="timeline-desc">申请人撤销了此申请</div>
            <div class="timeline-comments" v-if="request.cancelled_reason">
              撤销原因：{{ request.cancelled_reason }}
            </div>
          </div>
        </a-timeline-item>

        <a-timeline-item 
          v-if="isPending"
          color="blue"
        >
          <template #dot>
            <LoadingOutlined style="font-size: 16px;" />
          </template>
          <div class="timeline-content">
            <div class="timeline-title">等待审批</div>
            <div class="timeline-desc">申请正在等待管理员审批...</div>
          </div>
        </a-timeline-item>
      </a-timeline>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons" style="margin-top: 24px;" v-if="isPending">
      <a-space>
        <a-button 
          type="primary" 
          @click="handleAction('approve')"
          :disabled="!request.can_approve"
        >
          <CheckCircleOutlined />
          同意申请
        </a-button>
        
        <a-button 
          danger 
          @click="handleAction('reject')"
          :disabled="!request.can_reject"
        >
          <CloseCircleOutlined />
          驳回申请
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  StopOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import type { CourseRequestDetail } from '@/api/course-management'

interface Props {
  request: CourseRequestDetail
}

interface Emits {
  (e: 'action', action: string, request: CourseRequestDetail): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 计算属性
const isPending = computed(() => props.request.status === 'PENDING')
const isReviewed = computed(() => 
  props.request.status === 'APPROVED' || props.request.status === 'REJECTED'
)
const isCancelled = computed(() => props.request.status === 'CANCELLED')

// 方法
const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const getCourseTypeColor = (type: string) => {
  return type === 'PRACTICE' ? 'blue' : 'green'
}

const getRequestTypeColor = (type: string) => {
  return type === 'PUBLISH' ? 'green' : 'orange'
}

const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'PENDING': 'orange',
    'APPROVED': 'green',
    'REJECTED': 'red',
    'CANCELLED': 'gray'
  }
  return colorMap[status] || 'default'
}

const viewCourseDetail = () => {
  const routePath = props.request.course_type === 'PRACTICE' 
    ? `/course-management/practice/${props.request.course_id}`
    : `/course-management/training/${props.request.course_id}`
  
  window.open(routePath, '_blank')
}

const handleAction = (action: string) => {
  emit('action', action, props.request)
}
</script>

<style scoped>
.request-detail-panel {
  max-height: 70vh;
  overflow-y: auto;
}

.course-link {
  color: #1890ff;
  text-decoration: none;
}

.course-link:hover {
  color: #40a9ff;
}

.reason-content,
.review-comments,
.cancel-reason {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  border-left: 3px solid #1890ff;
  margin: 8px 0;
  font-size: 14px;
  line-height: 1.6;
}

.review-comments {
  border-left-color: #52c41a;
}

.cancel-reason {
  border-left-color: #faad14;
}

.timeline-section h4 {
  margin-bottom: 16px;
  color: #333;
  font-weight: 600;
}

.timeline-content {
  padding-left: 8px;
}

.timeline-title {
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-bottom: 4px;
}

.timeline-time {
  color: #999;
  font-size: 12px;
  margin-bottom: 8px;
}

.timeline-desc {
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.timeline-comments {
  background: #f5f5f5;
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 8px;
  font-size: 13px;
  color: #666;
  border-left: 3px solid #1890ff;
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

:deep(.ant-timeline-item-content) {
  margin-left: 8px;
}
</style> 