<template>
  <div class="course-approval-page">
    <div class="page-header">
      <h2>课程审批管理</h2>
    </div>

    <!-- 标签页 -->
    <a-tabs v-model:activeKey="activeTab" @change="onTabChange">
      <a-tab-pane key="pending" tab="待审批">
        <template #tab>
          <span>
            <ClockCircleOutlined />
            待审批
            <a-badge :count="pendingCount" :offset="[10, 0]" />
          </span>
        </template>
      </a-tab-pane>
      
      <a-tab-pane key="reviewed" tab="已审批">
        <template #tab>
          <span>
            <CheckCircleOutlined />
            已审批
          </span>
        </template>
      </a-tab-pane>
    </a-tabs>

    <!-- 搜索筛选区域 -->
    <div class="filter-section">
      <a-form layout="inline" :model="queryParams">
        <a-form-item label="课程名称">
          <a-input
            v-model:value="queryParams.course_name"
            placeholder="请输入课程名称"
            style="width: 200px"
            allow-clear
          />
        </a-form-item>
        
        <a-form-item label="申请人">
          <a-input
            v-model:value="queryParams.applicant_name"
            placeholder="请输入申请人姓名"
            style="width: 200px"
            allow-clear
          />
        </a-form-item>
        
        <a-form-item label="课程类型">
          <a-select
            v-model:value="queryParams.course_type"
            placeholder="请选择课程类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="PRACTICE">实践课程</a-select-option>
            <a-select-option value="TRAINING">实训课程</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="申请类型">
          <a-select
            v-model:value="queryParams.request_type"
            placeholder="请选择申请类型"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="PUBLISH">申请发布</a-select-option>
            <a-select-option value="UNPUBLISH">申请下架</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="申请时间" v-if="activeTab === 'reviewed'">
          <a-range-picker
            v-model:value="dateRange"
            format="YYYY-MM-DD"
            style="width: 240px"
          />
        </a-form-item>
        
        <a-form-item label="审批状态" v-if="activeTab === 'reviewed'">
          <a-select
            v-model:value="queryParams.status"
            placeholder="请选择审批状态"
            style="width: 120px"
            allow-clear
          >
            <a-select-option value="APPROVED">已同意</a-select-option>
            <a-select-option value="REJECTED">已驳回</a-select-option>
            <a-select-option value="CANCELLED">已撤销</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="searchRequests" :loading="loading">
              <SearchOutlined />
              搜索
            </a-button>
            <a-button @click="resetSearch">
              <ReloadOutlined />
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </div>

    <!-- 申请列表 -->
    <div class="table-section">
      <a-table
        :columns="tableColumns"
        :data-source="requestList.items"
        :loading="loading"
        :pagination="false"
        row-key="id"
        size="middle"
      >
        <!-- 课程名称 -->
        <template #course="{ record }">
          <a @click="viewCourseDetail(record)" class="course-link">
            {{ record.course.title }}
          </a>
          <a-tag :color="getCourseTypeColor(record.course_type)" size="small" style="margin-left: 8px;">
            {{ record.course_type_text }}
          </a-tag>
        </template>

        <!-- 申请人 -->
        <template #applicant="{ record }">
          <a-avatar size="small" style="margin-right: 8px;">
            {{ record.applicant.full_name?.charAt(0) || record.applicant.username?.charAt(0) }}
          </a-avatar>
          {{ record.applicant.full_name || record.applicant.username }}
        </template>

        <!-- 申请类型 -->
        <template #requestType="{ record }">
          <a-tag :color="getRequestTypeColor(record.request_type)">
            {{ record.request_type_text }}
          </a-tag>
        </template>

        <!-- 申请时间 -->
        <template #appliedAt="{ record }">
          {{ formatDateTime(record.applied_at) }}
        </template>

        <!-- 审批时间 -->
        <template #reviewedAt="{ record }">
          {{ record.reviewed_at ? formatDateTime(record.reviewed_at) : '-' }}
        </template>

        <!-- 状态 -->
        <template #status="{ record }">
          <a-tag :color="getStatusColor(record.status)">
            {{ record.status_text }}
          </a-tag>
        </template>

        <!-- 操作 -->
        <template #action="{ record }">
          <a-space>
            <a-button
              type="link"
              size="small"
              @click="viewRequestDetail(record)"
            >
              查看详情
            </a-button>
            
            <a-button
              v-if="record.can_approve"
              type="link"
              size="small"
              style="color: #52c41a"
              @click="showApprovalModal(record, 'approve')"
            >
              同意
            </a-button>
            
            <a-button
              v-if="record.can_reject"
              type="link"
              size="small"
              danger
              @click="showApprovalModal(record, 'reject')"
            >
              驳回
            </a-button>
            
            <a-button
              v-if="record.status === 'APPROVED' || record.status === 'REJECTED'"
              type="link"
              size="small"
              @click="viewApprovalComments(record)"
            >
              查看审批意见
            </a-button>
          </a-space>
        </template>
      </a-table>

      <!-- 分页 -->
      <div class="pagination-container" v-if="requestList.total > 0">
        <a-pagination
          v-model:current="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="requestList.total"
          :show-size-changer="true"
          :show-quick-jumper="true"
          :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
          @change="loadRequestList"
          @show-size-change="loadRequestList"
        />
      </div>
    </div>

    <!-- 申请详情抽屉 -->
    <a-drawer
      v-model:open="detailDrawerVisible"
      title="申请详情"
      width="800"
      :body-style="{ padding: '24px' }"
    >
      <request-detail-panel
        v-if="selectedRequest"
        :request="selectedRequest"
        @action="onRequestAction"
      />
    </a-drawer>

    <!-- 审批模态框 -->
    <a-modal
      v-model:open="approvalModalVisible"
      :title="approvalAction === 'approve' ? '同意申请' : '驳回申请'"
      @ok="confirmApproval"
      @cancel="approvalModalVisible = false"
    >
      <div class="approval-content">
        <p>
          <strong>课程名称：</strong>{{ actionRequest?.course.title }}
        </p>
        <p>
          <strong>申请人：</strong>{{ actionRequest?.applicant.full_name || actionRequest?.applicant.username }}
        </p>
        <p>
          <strong>申请类型：</strong>{{ actionRequest?.request_type_text }}
        </p>
        <p v-if="actionRequest?.application_reason">
          <strong>申请理由：</strong>{{ actionRequest.application_reason }}
        </p>
        
        <a-form-item 
          :label="approvalAction === 'approve' ? '同意理由（可选）' : '驳回理由（可选）'"
          style="margin-top: 16px;"
        >
          <a-textarea
            v-model:value="approvalComments"
            :placeholder="approvalAction === 'approve' ? '请输入同意理由...' : '请输入驳回理由...'"
            :rows="4"
            :max-length="500"
            show-count
          />
        </a-form-item>
      </div>
    </a-modal>

    <!-- 审批意见查看模态框 -->
    <a-modal
      v-model:open="commentsModalVisible"
      title="审批意见"
      :footer="null"
    >
      <div class="comments-content" v-if="selectedRequest">
        <a-descriptions :column="1" bordered>
          <a-descriptions-item label="审批人">
            {{ selectedRequest.reviewer?.full_name || selectedRequest.reviewer?.username || '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="审批时间">
            {{ selectedRequest.reviewed_at ? formatDateTime(selectedRequest.reviewed_at) : '-' }}
          </a-descriptions-item>
          <a-descriptions-item label="审批状态">
            <a-tag :color="getStatusColor(selectedRequest.status)">
              {{ selectedRequest.status_text }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="审批意见">
            {{ selectedRequest.review_comments || '无' }}
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import type { Dayjs } from 'dayjs'
import {
  ClockCircleOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue'
import {
  CourseManagementAPI,
  type CourseRequestItem,
  type CourseRequestDetail,
  type CourseRequestQuery,
  type CourseRequestApprovalRequest,
  RequestStatusEnum,
  CourseTypeEnum,
  RequestTypeEnum
} from '@/api/course-management'
import RequestDetailPanel from './components/RequestDetailPanel.vue'

// 响应式数据
const loading = ref(false)
const activeTab = ref('pending')
const pendingCount = ref(0)
const dateRange = ref<[Dayjs, Dayjs] | null>(null)

const requestList = reactive({
  items: [] as CourseRequestItem[],
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0
})

const queryParams = reactive<CourseRequestQuery>({
  status: undefined,
  course_type: undefined,
  request_type: undefined,
  course_name: '',
  applicant_name: '',
  start_date: undefined,
  end_date: undefined,
  page: 1,
  page_size: 20,
  sort_field: 'applied_at',
  sort_order: 'desc'
})

// 详情抽屉
const detailDrawerVisible = ref(false)
const selectedRequest = ref<CourseRequestDetail | null>(null)

// 审批模态框
const approvalModalVisible = ref(false)
const approvalAction = ref<'approve' | 'reject'>('approve')
const actionRequest = ref<CourseRequestItem | null>(null)
const approvalComments = ref('')

// 审批意见查看模态框
const commentsModalVisible = ref(false)

// 表格列配置
const tableColumns = computed(() => {
  const baseColumns = [
    {
      title: '课程名称',
      dataIndex: 'course',
      key: 'course',
      slots: { customRender: 'course' },
      sorter: true
    },
    {
      title: '申请人',
      dataIndex: 'applicant',
      key: 'applicant',
      slots: { customRender: 'applicant' },
      sorter: true
    },
    {
      title: '申请类型',
      dataIndex: 'request_type',
      key: 'request_type',
      slots: { customRender: 'requestType' },
      sorter: true
    },
    {
      title: '申请时间',
      dataIndex: 'applied_at',
      key: 'applied_at',
      slots: { customRender: 'appliedAt' },
      sorter: true
    }
  ]

  if (activeTab.value === 'reviewed') {
    baseColumns.push(
      {
        title: '审批时间',
        dataIndex: 'reviewed_at',
        key: 'reviewed_at',
        slots: { customRender: 'reviewedAt' },
        sorter: true
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        slots: { customRender: 'status' },
        sorter: true
      }
    )
  }

  baseColumns.push({
    title: '操作',
    key: 'action',
    slots: { customRender: 'action' },
    width: 200
  })

  return baseColumns
})

// 监听器
watch(activeTab, (newTab) => {
  if (newTab === 'pending') {
    queryParams.status = RequestStatusEnum.PENDING
  } else {
    queryParams.status = undefined
  }
  queryParams.page = 1
  loadRequestList()
})

watch(dateRange, (newRange) => {
  if (newRange) {
    queryParams.start_date = newRange[0].format('YYYY-MM-DD')
    queryParams.end_date = newRange[1].format('YYYY-MM-DD')
  } else {
    queryParams.start_date = undefined
    queryParams.end_date = undefined
  }
})

// 生命周期
onMounted(() => {
  queryParams.status = RequestStatusEnum.PENDING
  loadRequestList()
  loadPendingCount()
})

// 方法
const loadRequestList = async () => {
  loading.value = true
  try {
    const response = await CourseManagementAPI.getCourseRequests(queryParams)
    Object.assign(requestList, response)
  } catch (error) {
    console.error('加载申请列表失败:', error)
    message.error('加载申请列表失败')
  } finally {
    loading.value = false
  }
}

const loadPendingCount = async () => {
  try {
    const response = await CourseManagementAPI.getCourseRequests({
      status: RequestStatusEnum.PENDING,
      page: 1,
      page_size: 1
    })
    pendingCount.value = response.total
  } catch (error) {
    console.error('加载待审批数量失败:', error)
  }
}

const onTabChange = (key: string) => {
  activeTab.value = key
}

const searchRequests = () => {
  queryParams.page = 1
  loadRequestList()
}

const resetSearch = () => {
  Object.assign(queryParams, {
    course_name: '',
    applicant_name: '',
    course_type: undefined,
    request_type: undefined,
    start_date: undefined,
    end_date: undefined,
    page: 1,
    page_size: 20,
    sort_field: 'applied_at',
    sort_order: 'desc'
  })
  
  if (activeTab.value === 'pending') {
    queryParams.status = RequestStatusEnum.PENDING
  }
  
  dateRange.value = null
  loadRequestList()
}

const viewRequestDetail = async (request: CourseRequestItem) => {
  try {
    const detail = await CourseManagementAPI.getCourseRequestDetail(request.id)
    selectedRequest.value = detail
    detailDrawerVisible.value = true
  } catch (error) {
    console.error('加载申请详情失败:', error)
    message.error('加载申请详情失败')
  }
}

const viewCourseDetail = (request: CourseRequestItem) => {
  // 可以跳转到课程详情页面
  const routePath = request.course_type === 'PRACTICE' 
    ? `/course-management/practice/${request.course_id}`
    : `/course-management/training/${request.course_id}`
  
  window.open(routePath, '_blank')
}

const showApprovalModal = (request: CourseRequestItem, action: 'approve' | 'reject') => {
  actionRequest.value = request
  approvalAction.value = action
  approvalComments.value = ''
  approvalModalVisible.value = true
}

const confirmApproval = async () => {
  if (!actionRequest.value) return
  
  try {
    const requestData: CourseRequestApprovalRequest = {
      action: approvalAction.value,
      review_comments: approvalComments.value || undefined
    }
    
    const response = await CourseManagementAPI.approveCourseRequest(
      actionRequest.value.id,
      requestData
    )
    
    if (response.success) {
      message.success(response.message)
      approvalModalVisible.value = false
      loadRequestList()
      loadPendingCount()
    } else {
      message.error(response.message)
    }
  } catch (error) {
    console.error('审批失败:', error)
    message.error('审批失败')
  }
}

const viewApprovalComments = (request: CourseRequestItem) => {
  selectedRequest.value = request as any
  commentsModalVisible.value = true
}

const onRequestAction = (action: string, request: any) => {
  if (action === 'approve') {
    showApprovalModal(request, 'approve')
  } else if (action === 'reject') {
    showApprovalModal(request, 'reject')
  }
  detailDrawerVisible.value = false
}

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
</script>

<style scoped>
.course-approval-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  color: #333;
}

.filter-section {
  background: white;
  padding: 24px;
  border-radius: 6px;
  margin-bottom: 16px;
}

.table-section {
  background: white;
  padding: 24px;
  border-radius: 6px;
}

.course-link {
  color: #1890ff;
  text-decoration: none;
}

.course-link:hover {
  color: #40a9ff;
}

.pagination-container {
  margin-top: 24px;
  text-align: center;
}

.approval-content {
  margin-bottom: 16px;
}

.approval-content p {
  margin-bottom: 8px;
  color: #333;
}

.comments-content {
  padding: 16px 0;
}

:deep(.ant-tabs-tab) {
  font-size: 16px;
  font-weight: 500;
}

:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
  font-weight: 600;
}

:deep(.ant-badge) {
  margin-left: 8px;
}
</style> 