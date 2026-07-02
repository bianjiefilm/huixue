<template>
  <div class="my-exams-container">
    <!-- 顶部操作区 -->
    <div class="operation-bar">
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索考试名称"
        style="width: 300px"
        @search="handleSearch"
        allow-clear
      />
      <div class="filter-section">
        <a-select
          v-model:value="filterStatus"
          placeholder="考试状态"
          style="width: 120px; margin-left: 8px"
          @change="handleFilterChange"
          allow-clear
        >
          <a-select-option value="unpublished">未发布</a-select-option>
          <a-select-option value="upcoming">未开始</a-select-option>
          <a-select-option value="ongoing">进行中</a-select-option>
          <a-select-option value="finished">已结束</a-select-option>
        </a-select>
        <a-select
          v-model:value="filterClassroom"
          placeholder="课堂"
          style="width: 200px; margin-left: 8px"
          @change="handleFilterChange"
          allow-clear
        >
          <a-select-option v-for="classroom in classroomList" :key="classroom.id" :value="classroom.id">
            {{ classroom.name }}
          </a-select-option>
        </a-select>
      </div>
    </div>

    <!-- 考试列表 -->
    <div class="exam-list">
      <a-spin :spinning="loading">
        <a-empty v-if="examList.length === 0" description="暂无考试" />
        <a-table
          v-else
          :columns="columns"
          :data-source="examList"
          :pagination="false"
          :rowKey="record => record.id"
        >
          <!-- 考试名称 -->
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'title'">
              <a @click="viewExamDetail(record)">{{ record.title }}</a>
            </template>
            
            <!-- 考试状态 -->
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            
            <!-- 参与人数 -->
            <template v-if="column.dataIndex === 'participantCount'">
              {{ record.participantCount }}/{{ record.totalCount }}
            </template>
            
            <!-- 时间信息 -->
            <template v-if="column.dataIndex === 'examTime'">
              <div>{{ formatDateTime(record.startTime) }}</div>
              <div>至</div>
              <div>{{ formatDateTime(record.endTime) }}</div>
            </template>
            
            <!-- 操作 -->
            <template v-if="column.dataIndex === 'action'">
              <div class="action-buttons">
                <a-tooltip title="查看">
                  <a-button type="link" size="small" @click="viewExamDetail(record)">
                    <template #icon><EyeOutlined /></template>
                  </a-button>
                </a-tooltip>
                
                <a-tooltip title="发布" v-if="record.status === 'unpublished'">
                  <a-button type="link" size="small" @click="publishExam(record)">
                    <template #icon><SendOutlined /></template>
                  </a-button>
                </a-tooltip>
                
                <a-tooltip title="编辑" v-if="record.status === 'unpublished'">
                  <a-button type="link" size="small" @click="editExam(record)">
                    <template #icon><EditOutlined /></template>
                  </a-button>
                </a-tooltip>
                
                <a-tooltip title="批阅" v-if="record.status === 'finished'">
                  <a-button type="link" size="small" @click="markExam(record)">
                    <template #icon><CheckSquareOutlined /></template>
                  </a-button>
                </a-tooltip>
                
                <a-tooltip title="查看成绩" v-if="record.status === 'finished'">
                  <a-button type="link" size="small" @click="viewResults(record)">
                    <template #icon><BarChartOutlined /></template>
                  </a-button>
                </a-tooltip>
                
                <a-tooltip title="删除">
                  <a-button type="link" size="small" danger @click="showDeleteConfirm(record)">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-tooltip>
              </div>
            </template>
          </template>
        </a-table>
      </a-spin>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <a-pagination
        v-model:current="currentPage"
        :total="totalExams"
        :pageSize="pageSize"
        show-quick-jumper
        @change="handlePageChange"
      />
    </div>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteConfirmVisible"
      title="删除确认"
      okText="确定"
      okType="danger"
      cancelText="取消"
      @ok="confirmDelete"
    >
      <p>数据删除后不可恢复，是否确定删除该考试？</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  EyeOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SendOutlined,
  CheckSquareOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import { useUserStore } from '@/stores/user';
import { useClassroomStore } from '@/stores/classroom';
import { 
  getExamList,
  publishExam as publishExamApi,
  deleteExam as deleteExamApi,
  type ExamItem
} from '@/api/exam';

const router = useRouter();
const userStore = useUserStore();
const classroomStore = useClassroomStore();

// 表格列定义
const columns = [
  {
    title: '考试名称',
    dataIndex: 'title',
    key: 'title',
    ellipsis: true,
    width: 250
  },
  {
    title: '所属课堂',
    dataIndex: 'classroomName',
    key: 'classroomName',
    ellipsis: true,
    width: 200
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '参与人数',
    dataIndex: 'participantCount',
    key: 'participantCount',
    width: 100
  },
  {
    title: '考试时间',
    dataIndex: 'examTime',
    key: 'examTime',
    width: 200
  },
  {
    title: '操作',
    dataIndex: 'action',
    key: 'action',
    fixed: 'right',
    width: 150
  }
];

// 搜索和筛选
const searchKeyword = ref('');
const filterStatus = ref<string | undefined>(undefined);
const filterClassroom = ref<string | undefined>(undefined);

// 分页相关
const currentPage = ref(1);
const pageSize = ref(10);
const totalExams = ref(0);

// 加载状态
const loading = ref(false);

// 考试列表
const examList = ref<any[]>([]);

// 课堂列表
const classroomList = ref<any[]>([]);

// 删除确认弹窗
const deleteConfirmVisible = ref(false);
const currentExam = ref<any>(null);

// 初始化加载数据
onMounted(() => {
  loadExamList();
  loadClassroomList();
});

// 加载考试列表
const loadExamList = async () => {
  if (!userStore.userInfo?.id) return;
  
  loading.value = true;
  try {
    const res = await getExamList({
      teacher_id: userStore.userInfo.id,
      keyword: searchKeyword.value ? encodeURIComponent(searchKeyword.value) : undefined,
      status: filterStatus.value,
      classroom_id: filterClassroom.value,
      page: currentPage.value,
      page_size: pageSize.value
    });
    
    if (res.code === '0000') {
      examList.value = res.data.list;
      totalExams.value = res.data.meta.total;
    } else {
      message.error(res.message || '获取考试列表失败');
    }
  } catch (error) {
    console.error('获取考试列表失败:', error);
    message.error('获取考试列表失败');
  } finally {
    loading.value = false;
  }
};

// 加载课堂列表
const loadClassroomList = async () => {
  // 从课堂store获取教师的课堂列表
  if (classroomStore.classrooms.length > 0) {
    classroomList.value = classroomStore.classrooms;
  } else {
    // 如果store中没有数据，触发加载
    await classroomStore.fetchClassrooms();
    classroomList.value = classroomStore.classrooms;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadExamList();
};

// 处理筛选条件变化
const handleFilterChange = () => {
  currentPage.value = 1;
  loadExamList();
};

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadExamList();
};

// 查看考试详情
const viewExamDetail = (exam: any) => {
  router.push(`/classroom/${exam.classroomId}/course/default/exam/${exam.id}/detail`);
};

// 发布考试
const publishExam = async (exam: ExamItem) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await publishExamApi(exam.id, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success(`考试"${exam.title}"已发布`);
      loadExamList();
    } else {
      message.error(res.message || '发布考试失败');
    }
  } catch (error) {
    console.error('发布考试失败:', error);
    message.error('发布考试失败');
  }
};

// 编辑考试
const editExam = (exam: any) => {
  router.push(`/classroom/${exam.classroomId}/course/default/exam/${exam.id}/edit`);
};

// 批阅考试
const markExam = (exam: any) => {
  router.push(`/classroom/${exam.classroomId}/course/default/exam/${exam.id}/marking`);
};

// 查看成绩
const viewResults = (exam: any) => {
  router.push(`/classroom/${exam.classroomId}/course/default/exam/${exam.id}/results`);
};

// 显示删除确认弹窗
const showDeleteConfirm = (exam: any) => {
  currentExam.value = exam;
  deleteConfirmVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!currentExam.value || !userStore.userInfo?.id) return;
  
  try {
    const res = await deleteExamApi(currentExam.value.id, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success(`已删除考试"${currentExam.value.title}"`);
      deleteConfirmVisible.value = false;
      loadExamList();
    } else {
      message.error(res.message || '删除考试失败');
    }
  } catch (error) {
    console.error('删除考试失败:', error);
    message.error('删除考试失败');
  }
};

// 格式化日期时间
const formatDateTime = (date: Date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'unpublished': '未发布',
    'upcoming': '未开始',
    'ongoing': '进行中',
    'finished': '已结束'
  };
  return statusMap[status] || status;
};

// 获取状态对应的颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'unpublished': 'default',
    'upcoming': 'blue',
    'ongoing': 'green',
    'finished': 'orange'
  };
  return colorMap[status] || 'default';
};
</script>

<style scoped>
.my-exams-container {
  padding: 0 8px;
}

.operation-bar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.filter-section {
  display: flex;
  margin-left: auto;
  flex-wrap: wrap;
}

.exam-list {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  justify-content: space-between;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .operation-bar {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-section {
    margin-left: 0;
    margin-top: 16px;
    width: 100%;
  }
}
</style> 