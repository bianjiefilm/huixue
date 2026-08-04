<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar title="实训课程审批" />

    <div class="approval-container">
      <a-card :bordered="false">
        <a-tabs v-model:activeKey="activeTabKey">
          <!-- 待审批标签页 -->
          <a-tab-pane key="pending" tab="待审批">
            <div class="filter-bar">
              <Stack direction="horizontal" :gap="3" align="center">
                <a-input v-model:value="filters.pending.keyword" placeholder="课程名称" style="width: 160px" />
                <a-input v-model:value="filters.pending.applicant" placeholder="申请人" style="width: 140px" />
                <a-select v-model:value="filters.pending.type" style="width: 120px" allowClear placeholder="申请类型">
                  <a-select-option value="publish">发布申请</a-select-option>
                  <a-select-option value="unpublish">撤销发布</a-select-option>
                </a-select>
                <a-range-picker v-model:value="filters.pending.appliedTimeRange" />
                <a-button type="primary" @click="applyPendingFilters">查询</a-button>
                <a-button @click="resetPendingFilters">重置</a-button>
              </Stack>
            </div>
            
            <a-table
              :loading="loading.trainingApprovals"
              :dataSource="pendingTrainingApprovals"
              :columns="pendingColumns"
              :pagination="{ pageSize: 10, showTotal: (total: number) => `共 ${total} 条` }"
              :rowKey="(record: CourseApproval) => record.id"
            >
              <template #emptyText>
                <EmptyStateBlock description="暂无待审批申请" />
              </template>
              <!-- 自定义列 -->
              <template #bodyCell="{ column, record }">
                <!-- 申请类型列 -->
                <template v-if="column.dataIndex === 'type'">
                  <a-tag :color="record.type === 'publish' ? 'blue' : 'orange'">
                    {{ record.type === 'publish' ? '发布申请' : '撤销发布' }}
                  </a-tag>
                </template>
                
                <!-- 操作列 -->
                <template v-else-if="column.dataIndex === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="viewCourseDetail(record)">查看课程</a-button>
                    <a-button type="primary" size="small" @click="showApproveConfirm(record)">同意</a-button>
                    <a-button danger size="small" @click="showRejectConfirm(record)">驳回</a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-tab-pane>
          
          <!-- 已审批标签页 -->
          <a-tab-pane key="approved" tab="已审批">
            <div class="filter-bar">
              <Stack direction="horizontal" :gap="3" align="center">
                <a-input v-model:value="filters.approved.keyword" placeholder="课程名称" style="width: 160px" />
                <a-input v-model:value="filters.approved.applicant" placeholder="申请人" style="width: 140px" />
                <a-select v-model:value="filters.approved.type" style="width: 120px" allowClear placeholder="申请类型">
                  <a-select-option value="publish">发布申请</a-select-option>
                  <a-select-option value="unpublish">撤销发布</a-select-option>
                </a-select>
                <a-range-picker v-model:value="filters.approved.appliedTimeRange" />
                <a-select v-model:value="filters.approved.status" style="width: 120px" allowClear placeholder="审批状态">
                  <a-select-option value="approved">已同意</a-select-option>
                  <a-select-option value="rejected">已驳回</a-select-option>
                  <a-select-option value="cancelled">用户撤销</a-select-option>
                </a-select>
                <a-button type="primary" @click="applyApprovedFilters">查询</a-button>
                <a-button @click="resetApprovedFilters">重置</a-button>
              </Stack>
            </div>
            
            <a-table
              :loading="loading.trainingApprovals"
              :dataSource="approvedTrainingApprovals"
              :columns="approvedColumns"
              :pagination="{ pageSize: 10, showTotal: (total: number) => `共 ${total} 条` }"
              :rowKey="(record: CourseApproval) => record.id"
            >
              <template #emptyText>
                <EmptyStateBlock description="暂无已审批记录" />
              </template>
              <!-- 自定义列 -->
              <template #bodyCell="{ column, record }">
                <!-- 课程名称列 -->
                <template v-if="column.dataIndex === 'courseTitle'">
                  <template v-if="record.status !== 'cancelled'">
                    <a @click="viewCourseDetail(record)">{{ record.courseTitle }}</a>
                  </template>
                  <template v-else>
                    <span>{{ record.courseTitle }}</span>
                  </template>
                </template>
                
                <!-- 申请类型列 -->
                <template v-else-if="column.dataIndex === 'type'">
                  <a-tag :color="record.type === 'publish' ? 'blue' : 'orange'">
                    {{ record.type === 'publish' ? '发布申请' : '撤销发布' }}
                  </a-tag>
                </template>
                
                <!-- 状态列 -->
                <template v-else-if="column.dataIndex === 'status'">
                  <a-tag :color="getStatusColor(record.status)">
                    {{ getStatusText(record.status) }}
                  </a-tag>
                </template>
                
                <!-- 操作列 -->
                <template v-else-if="column.dataIndex === 'action'">
                  <a-button 
                    v-if="record.status !== 'cancelled'" 
                    type="link" 
                    size="small" 
                    @click="showFeedbackModal(record)"
                  >
                    查看审批意见
                  </a-button>
                </template>
              </template>
            </a-table>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
    
    <!-- 审批确认弹窗 -->
    <a-modal
      v-model:open="approvalModal.visible"
      :title="approvalModal.isApprove ? '审批同意' : '审批驳回'"
      @ok="handleApprovalConfirm"
      :confirmLoading="approvalModal.loading"
    >
      <a-form :model="approvalModal.form" layout="vertical">
        <a-form-item label="课程名称">
          <span>{{ approvalModal.record?.courseTitle }}</span>
        </a-form-item>
        <a-form-item label="申请人">
          <span>{{ approvalModal.record?.applicant }}</span>
        </a-form-item>
        <a-form-item label="申请类型">
          <span>{{ approvalModal.record?.type === 'publish' ? '发布申请' : '撤销发布' }}</span>
        </a-form-item>
        <a-form-item label="申请理由">
          <span>{{ approvalModal.record?.reason || '无' }}</span>
        </a-form-item>
        <a-form-item label="审批意见">
          <a-textarea 
            v-model:value="approvalModal.form.feedback" 
            :rows="4" 
            placeholder="请输入审批意见"
          />
        </a-form-item>
      </a-form>
    </a-modal>
    
    <!-- 审批意见查看弹窗 -->
    <a-modal
      v-model:open="feedbackModal.visible"
      title="审批意见"
      :footer="null"
    >
      <a-descriptions bordered>
        <a-descriptions-item label="课程名称" :span="3">
          {{ feedbackModal.record?.courseTitle }}
        </a-descriptions-item>
        <a-descriptions-item label="申请人" :span="3">
          {{ feedbackModal.record?.applicant }}
        </a-descriptions-item>
        <a-descriptions-item label="申请类型" :span="3">
          {{ feedbackModal.record?.type === 'publish' ? '发布申请' : '撤销发布' }}
        </a-descriptions-item>
        <a-descriptions-item label="申请理由" :span="3">
          {{ feedbackModal.record?.reason || '无' }}
        </a-descriptions-item>
        <a-descriptions-item label="申请时间" :span="3">
          {{ formatDateTime(feedbackModal.record?.appliedAt) }}
        </a-descriptions-item>
        <a-descriptions-item label="审批结果" :span="3">
          <a-tag :color="getStatusColor(feedbackModal.record?.status)">
            {{ getStatusText(feedbackModal.record?.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="审批时间" :span="3">
          {{ formatDateTime(feedbackModal.record?.approvedAt) }}
        </a-descriptions-item>
        <a-descriptions-item label="审批意见" :span="3">
          {{ feedbackModal.record?.feedback || '无' }}
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { useAdminCourseStore } from '@/stores/admin-course';
import { ApprovalStatus, type CourseApproval } from '@/types/admin';
import dayjs from 'dayjs';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

const router = useRouter();
const adminCourseStore = useAdminCourseStore();

// 当前选中的标签页
const activeTabKey = ref<string>('pending');

// 加载状态
const loading = computed(() => adminCourseStore.loading);

// 审批列表数据
const pendingTrainingApprovals = computed(() => adminCourseStore.pendingTrainingApprovals);
const approvedTrainingApprovals = computed(() => adminCourseStore.approvedTrainingApprovals);

// 筛选条件
const filters = reactive({
  pending: {
    keyword: '',
    applicant: '',
    type: '',
    appliedTimeRange: []
  },
  approved: {
    keyword: '',
    applicant: '',
    type: '',
    appliedTimeRange: [],
    status: ''
  }
});

// 审批确认弹窗状态
const approvalModal = reactive({
  visible: false,
  isApprove: true,
  loading: false,
  record: null as CourseApproval | null,
  form: {
    feedback: ''
  }
});

// 审批意见查看弹窗状态
const feedbackModal = reactive({
  visible: false,
  record: null as CourseApproval | null
});

// 待审批表格列定义
const pendingColumns = [
  {
    title: '待审实训课程',
    dataIndex: 'courseTitle',
    key: 'courseTitle',
    ellipsis: true,
    sorter: (a: CourseApproval, b: CourseApproval) => a.courseTitle.localeCompare(b.courseTitle)
  },
  {
    title: '申请人',
    dataIndex: 'applicant',
    key: 'applicant',
    width: 120,
    sorter: (a: CourseApproval, b: CourseApproval) => a.applicant.localeCompare(b.applicant)
  },
  {
    title: '申请类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    filters: [
      { text: '发布申请', value: 'publish' },
      { text: '撤销发布', value: 'unpublish' }
    ],
    onFilter: (value: string, record: CourseApproval) => record.type === value
  },
  {
    title: '申请时间',
    dataIndex: 'appliedAt',
    key: 'appliedAt',
    width: 170,
    sorter: (a: CourseApproval, b: CourseApproval) => 
      new Date(a.appliedAt).getTime() - new Date(b.appliedAt).getTime(),
    defaultSortOrder: 'descend',
    render: (time: string) => formatDateTime(time)
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
    width: 220,
    fixed: 'right'
  }
];

// 已审批表格列定义
const approvedColumns = [
  {
    title: '已审实训课程',
    dataIndex: 'courseTitle',
    key: 'courseTitle',
    ellipsis: true,
    sorter: (a: CourseApproval, b: CourseApproval) => a.courseTitle.localeCompare(b.courseTitle)
  },
  {
    title: '申请人',
    dataIndex: 'applicant',
    key: 'applicant',
    width: 120,
    sorter: (a: CourseApproval, b: CourseApproval) => a.applicant.localeCompare(b.applicant)
  },
  {
    title: '申请类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    filters: [
      { text: '发布申请', value: 'publish' },
      { text: '撤销发布', value: 'unpublish' }
    ],
    onFilter: (value: string, record: CourseApproval) => record.type === value
  },
  {
    title: '申请时间',
    dataIndex: 'appliedAt',
    key: 'appliedAt',
    width: 170,
    sorter: (a: CourseApproval, b: CourseApproval) => 
      new Date(a.appliedAt).getTime() - new Date(b.appliedAt).getTime(),
    render: (time: string) => formatDateTime(time)
  },
  {
    title: '审批时间',
    dataIndex: 'approvedAt',
    key: 'approvedAt',
    width: 170,
    sorter: (a: CourseApproval, b: CourseApproval) => 
      new Date(a.approvedAt || '').getTime() - new Date(b.approvedAt || '').getTime(),
    render: (time: string) => formatDateTime(time)
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100,
    filters: [
      { text: '已同意', value: ApprovalStatus.APPROVED },
      { text: '已驳回', value: ApprovalStatus.REJECTED },
      { text: '用户撤销', value: ApprovalStatus.CANCELLED }
    ],
    onFilter: (value: string, record: CourseApproval) => record.status === value
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
    width: 140,
    fixed: 'right'
  }
];

// 页面加载时获取数据
onMounted(async () => {
  await adminCourseStore.fetchTrainingApprovals();
});

// 获取状态对应的颜色
const getStatusColor = (status?: string) => {
  if (!status) return '';
  switch (status) {
    case ApprovalStatus.APPROVED: return 'green';
    case ApprovalStatus.REJECTED: return 'red';
    case ApprovalStatus.CANCELLED: return 'gray';
    default: return 'blue';
  }
};

// 获取状态对应的文本
const getStatusText = (status?: string) => {
  if (!status) return '';
  switch (status) {
    case ApprovalStatus.APPROVED: return '已同意';
    case ApprovalStatus.REJECTED: return '已驳回';
    case ApprovalStatus.CANCELLED: return '用户撤销';
    case ApprovalStatus.PENDING: return '待审批';
    default: return '未知';
  }
};

// 格式化日期时间
const formatDateTime = (dateTimeString?: string) => {
  if (!dateTimeString) return '';
  const date = new Date(dateTimeString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};

// 应用待审批筛选条件
const applyPendingFilters = () => {
  adminCourseStore.setFilter('trainingApproval', 'keyword', filters.pending.keyword);
  adminCourseStore.setFilter('trainingApproval', 'applicant', filters.pending.applicant);
  adminCourseStore.setFilter('trainingApproval', 'type', filters.pending.type);
  adminCourseStore.setFilter('trainingApproval', 'appliedTimeRange', filters.pending.appliedTimeRange);
};

// 应用已审批筛选条件
const applyApprovedFilters = () => {
  adminCourseStore.setFilter('trainingApproval', 'keyword', filters.approved.keyword);
  adminCourseStore.setFilter('trainingApproval', 'applicant', filters.approved.applicant);
  adminCourseStore.setFilter('trainingApproval', 'type', filters.approved.type);
  adminCourseStore.setFilter('trainingApproval', 'appliedTimeRange', filters.approved.appliedTimeRange);
  adminCourseStore.setFilter('trainingApproval', 'status', filters.approved.status);
};

// 重置待审批筛选条件
const resetPendingFilters = () => {
  filters.pending = {
    keyword: '',
    applicant: '',
    type: '',
    appliedTimeRange: []
  };
  adminCourseStore.resetFilters('trainingApproval');
};

// 重置已审批筛选条件
const resetApprovedFilters = () => {
  filters.approved = {
    keyword: '',
    applicant: '',
    type: '',
    appliedTimeRange: [],
    status: ''
  };
  adminCourseStore.resetFilters('trainingApproval');
};

// 查看课程详情
const viewCourseDetail = (record: CourseApproval) => {
  router.push(`/admin/course/detail/${record.courseId}`);
};

// 显示同意确认弹窗
const showApproveConfirm = (record: CourseApproval) => {
  approvalModal.isApprove = true;
  approvalModal.record = record;
  approvalModal.form.feedback = '';
  approvalModal.visible = true;
};

// 显示驳回确认弹窗
const showRejectConfirm = (record: CourseApproval) => {
  approvalModal.isApprove = false;
  approvalModal.record = record;
  approvalModal.form.feedback = '';
  approvalModal.visible = true;
};

// 处理审批确认
const handleApprovalConfirm = async () => {
  if (!approvalModal.record) return;
  
  approvalModal.loading = true;
  try {
    const success = approvalModal.isApprove
      ? await adminCourseStore.approveCourseApplication(approvalModal.record.id, approvalModal.form.feedback)
      : await adminCourseStore.rejectCourseApplication(approvalModal.record.id, approvalModal.form.feedback);
    
    if (success) {
      message.success(`已${approvalModal.isApprove ? '同意' : '驳回'}申请`);
      approvalModal.visible = false;
    } else {
      message.error(`${approvalModal.isApprove ? '同意' : '驳回'}申请失败`);
    }
  } catch (error) {
    message.error(`操作失败: ${error}`);
  } finally {
    approvalModal.loading = false;
  }
};

// 显示审批意见弹窗
const showFeedbackModal = (record: CourseApproval) => {
  feedbackModal.record = record;
  feedbackModal.visible = true;
};
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.approval-container {
  flex: 1;
  margin-top: 0;
}

.filter-bar {
  margin-bottom: var(--hx-space-4);
  background-color: var(--hx-color-bg-hover);
  padding: var(--hx-space-4);
  border-radius: var(--hx-radius-sm);
}
</style> 