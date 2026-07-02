<template>
  <div class="exam-marking-page">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 返回按钮 -->
      <div class="back-link">
        <router-link :to="`/classroom/${classroomId}/course/${courseId}/exam`">
          <a-button type="link">
            <template #icon><arrow-left-outlined /></template>
            返回考试列表
          </a-button>
        </router-link>
      </div>

      <!-- 页面标题 -->
      <div class="page-header">
        <h1>{{ exam?.exam_name || '考试' }}阅卷</h1>
        <div class="header-info">
          <span>总人数: {{ studentPapers.length }}</span>
          <a-divider type="vertical" />
          <span>已批阅: {{ markedCount }}</span>
          <a-divider type="vertical" />
          <span>未批阅: {{ unmarkedCount }}</span>
        </div>
      </div>

      <!-- 搜索和筛选 -->
      <div class="filter-section">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索学生姓名"
          style="width: 250px"
          @search="handleSearch"
        />
        
        <a-radio-group v-model:value="filterType" button-style="solid" @change="handleFilterChange">
          <a-radio-button value="all">全部</a-radio-button>
          <a-radio-button value="unmarked">未批阅</a-radio-button>
          <a-radio-button value="marked">已批阅</a-radio-button>
        </a-radio-group>
      </div>

      <!-- 学生列表 -->
      <div class="student-list-container">
        <a-empty v-if="filteredStudents.length === 0" description="暂无学生数据" />
        
        <a-table
          v-else
          :columns="columns"
          :data-source="filteredStudents"
          :pagination="{ 
            pageSize: 10,
            showSizeChanger: true,
            pageSizeOptions: ['10', '20', '50'],
            showTotal: (total) => `共 ${total} 条记录`
          }"
          :row-key="record => record.id"
          :loading="loading"
        >
          <!-- 学生姓名列 -->
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <a>{{ record.student_name }}</a>
            </template>
            
            <!-- 试卷状态列 -->
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.grading_status)">
                {{ getStatusText(record.grading_status) }}
              </a-tag>
            </template>
            
            <!-- 分数列 -->
            <template v-else-if="column.key === 'score'">
              <span v-if="record.grading_status === 'fully_graded'">
                {{ record.obtained_score || 0 }}/{{ record.total_score }}
              </span>
              <span v-else-if="record.grading_status === 'partially_graded'">
                {{ record.obtained_score || 0 }}+/{{ record.total_score }}
              </span>
              <span v-else>-/{{ record.total_score }}</span>
            </template>
            
            <!-- 操作列 -->
            <template v-else-if="column.key === 'action'">
              <a-button 
                type="primary"
                size="small"
                @click="markPaper(record)"
              >
                {{ record.grading_status === 'not_graded' ? '阅卷' : '继续阅卷' }}
              </a-button>
            </template>
          </template>
        </a-table>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  ArrowLeftOutlined, 
  SearchOutlined
} from '@ant-design/icons-vue';
import { 
  getExamDetail,
  getExamPapers,
  type ExamInfo,
  type StudentPaper
} from '@/api/exam';
import { useUserStore } from '@/stores/user';

// 路由相关
const route = useRoute();
const router = useRouter();
const classroomId = computed(() => route.params.classroomId as string);
const courseId = computed(() => route.params.courseId as string);
const examId = computed(() => route.params.examId as string);

// 状态管理
const loading = ref(false);
const exam = ref<ExamInfo | null>(null);
const userStore = useUserStore();
const studentPapers = ref<StudentPaper[]>([]);
const searchText = ref('');
const filterType = ref('all'); // 'all', 'unmarked', 'marked'

// 过滤与计算属性
const filteredStudents = computed(() => {
  let result = studentPapers.value;
  
  // 按姓名搜索
  if (searchText.value) {
    result = result.filter(
      student => student.student_name.toLowerCase().includes(searchText.value.toLowerCase())
    );
  }
  
  // 按批阅状态过滤
  if (filterType.value === 'unmarked') {
    result = result.filter(student => student.grading_status === 'not_graded');
  } else if (filterType.value === 'marked') {
    result = result.filter(
      student => student.grading_status === 'fully_graded' || student.grading_status === 'partially_graded'
    );
  }
  
  return result;
});

// 统计数据
const markedCount = computed(() => 
  studentPapers.value.filter(
    student => student.grading_status === 'fully_graded' || student.grading_status === 'partially_graded'
  ).length
);

const unmarkedCount = computed(() => 
  studentPapers.value.filter(student => student.grading_status === 'not_graded').length
);

// 表格列定义
const columns = [
  {
    title: '学生姓名',
    dataIndex: 'student_name',
    key: 'name',
    sorter: (a: StudentPaper, b: StudentPaper) => a.student_name.localeCompare(b.student_name)
  },
  {
    title: '提交时间',
    dataIndex: 'submission_time',
    key: 'submitTime',
    sorter: (a: StudentPaper, b: StudentPaper) => {
      if (!a.submission_time) return -1;
      if (!b.submission_time) return 1;
      return new Date(a.submission_time).getTime() - new Date(b.submission_time).getTime();
    }
  },
  {
    title: '批阅状态',
    key: 'status',
    sorter: (a: StudentPaper, b: StudentPaper) => {
      const statusOrder = { fully_graded: 2, partially_graded: 1, not_graded: 0, auto_graded: 3 };
      return (statusOrder[a.grading_status] || 0) - (statusOrder[b.grading_status] || 0);
    }
  },
  {
    title: '得分',
    key: 'score',
    sorter: (a: StudentPaper, b: StudentPaper) => (a.obtained_score || 0) - (b.obtained_score || 0)
  },
  {
    title: '操作',
    key: 'action'
  }
];

// 辅助函数
function getStatusColor(status: string): string {
  switch (status) {
    case 'fully_graded':
      return 'green';
    case 'partially_graded':
      return 'orange';
    case 'not_graded':
      return 'red';
    case 'auto_graded':
      return 'blue';
    default:
      return 'default';
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'fully_graded':
      return '已批阅';
    case 'partially_graded':
      return '部分批阅';
    case 'not_graded':
      return '未批阅';
    case 'auto_graded':
      return '自动批阅';
    default:
      return '未知状态';
  }
}

// 事件处理
function handleSearch() {
  // 搜索逻辑已在计算属性中处理
  console.log('搜索:', searchText.value);
}

function handleFilterChange() {
  // 过滤逻辑已在计算属性中处理
  console.log('过滤类型变更:', filterType.value);
}

function markPaper(paper: StudentPaper) {
  // 跳转到试卷阅卷页面
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/marking/${paper.student_id}`);
}

// 数据加载
async function fetchData() {
  loading.value = true;
  try {
    // 获取考试信息
    const examRes = await getExamDetail({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (examRes.code === '0000') {
      exam.value = examRes.data;
    } else {
      message.error(examRes.message || '获取考试信息失败');
      return;
    }
    
    // 获取学生试卷列表
    const papersRes = await getExamPapers({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      page: 1,
      page_size: 100 // 获取所有学生
    });
    
    if (papersRes.code === '0000') {
      studentPapers.value = papersRes.data.list;
    } else {
      message.error(papersRes.message || '获取学生试卷列表失败');
    }
  } catch (error) {
    console.error('获取数据失败:', error);
    message.error('获取数据失败');
  } finally {
    loading.value = false;
  }
}

// 生命周期钩子
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.exam-marking-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.header-info {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.filter-section {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
}

.student-list-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}
</style> 