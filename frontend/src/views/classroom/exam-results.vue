<template>
  <div class="exam-results-page">
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
        <h1>{{ exam?.exam_name || '考试' }}结果</h1>
        <div class="header-info">
          <span>总人数: {{ examStats?.total_students || 0 }}</span>
          <a-divider type="vertical" />
          <span>完成人数: {{ completeCount }}</span>
          <a-divider type="vertical" />
          <span>通过人数: {{ passedCount }}</span>
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
          <a-radio-button value="passed">通过</a-radio-button>
          <a-radio-button value="failed">未通过</a-radio-button>
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
              <a>{{ record.studentName }}</a>
            </template>
            
            <!-- 状态列 -->
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getScoreColor(record)">
                {{ isPassed(record) ? '通过' : '未通过' }}
              </a-tag>
            </template>
            
            <!-- 分数列 -->
            <template v-else-if="column.key === 'score'">
              <span>
                {{ record.obtainedScore }}/{{ record.totalScore }}
                <span class="score-percent">({{ getScorePercent(record) }}%)</span>
              </span>
            </template>
            
            <!-- 评阅状态列 -->
            <template v-else-if="column.key === 'marking'">
              <a-tag :color="getMarkingStatusColor(record.markingStatus)">
                {{ getMarkingStatusText(record.markingStatus) }}
              </a-tag>
            </template>
            
            <!-- 操作列 -->
            <template v-else-if="column.key === 'action'">
              <a-button 
                type="primary"
                size="small"
                @click="viewPaper(record)"
              >
                查看试卷
              </a-button>
              <a-button 
                v-if="isTeacherView && needMarking(record)"
                type="primary"
                size="small"
                style="margin-left: 8px;"
                @click="markPaper(record)"
              >
                阅卷
              </a-button>
            </template>
          </template>
        </a-table>
      </div>

      <!-- 统计图表 -->
      <div class="stats-container">
        <h2>成绩统计</h2>
        <div class="stats-cards">
          <a-card title="平均分" :bordered="false">
            <div class="stat-value">{{ averageScore || 0 }}分</div>
            <div class="stat-desc">总分 {{ exam?.paperTotalScore || 100 }}分</div>
          </a-card>
          <a-card title="通过率" :bordered="false">
            <div class="stat-value">{{ passRate }}%</div>
            <div class="stat-desc">通过标准 {{ exam?.passingScore || 60 }}分</div>
          </a-card>
          <a-card title="最高分" :bordered="false">
            <div class="stat-value">{{ highestScore || 0 }}分</div>
            <div class="stat-desc">{{ highestScoreStudent || '' }}</div>
          </a-card>
          <a-card title="最低分" :bordered="false">
            <div class="stat-value">{{ lowestScore || 0 }}分</div>
            <div class="stat-desc">{{ lowestScoreStudent || '' }}</div>
          </a-card>
        </div>
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
import { useUserStore } from '../../stores/user';
import { 
  getExamDetail,
  getExamPapers,
  type ExamInfo,
  type StudentPaper
} from '../../api/exam';

// 路由相关
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const classroomId = computed(() => route.params.classroomId as string);
const courseId = computed(() => route.params.courseId as string);
const examId = computed(() => route.params.examId as string);

// 状态管理
const loading = ref(false);
const exam = ref<ExamItem | undefined>(undefined);
const studentPapers = ref<StudentPaper[]>([]);
const searchText = ref('');
const filterType = ref('all'); // 'all', 'passed', 'failed'

// 是否为教师视图
const isTeacherView = computed(() => {
  const role = userStore.userInfo.role;
  return role === 'teacher' || role === 'admin';
});

// 过滤与计算属性
const filteredStudents = computed(() => {
  let result = studentPapers.value;
  
  // 按姓名搜索
  if (searchText.value) {
    result = result.filter(
      student => student.studentName.toLowerCase().includes(searchText.value.toLowerCase())
    );
  }
  
  // 按通过状态过滤
  if (filterType.value === 'passed') {
    result = result.filter(student => isPassed(student));
  } else if (filterType.value === 'failed') {
    result = result.filter(student => !isPassed(student));
  }
  
  return result;
});

// 统计数据
const completeCount = computed(() => studentPapers.value.length);

const passedCount = computed(() => 
  studentPapers.value.filter(student => isPassed(student)).length
);

// 使用统计数据中的最高分和最低分学生信息
const highestScoreStudent = computed(() => {
  if (!examStats.value || studentPapers.value.length === 0) return '';
  const student = studentPapers.value.find(s => 
    (s.obtained_score || 0) === examStats.value.highest_score
  );
  return student ? student.student_name : '';
});

const lowestScoreStudent = computed(() => {
  if (!examStats.value || studentPapers.value.length === 0) return '';
  const student = studentPapers.value.find(s => 
    (s.obtained_score || 0) === examStats.value.lowest_score
  );
  return student ? student.student_name : '';
});

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
    title: '状态',
    key: 'status',
    sorter: (a: StudentPaper, b: StudentPaper) => {
      const passingScore = exam.value?.passing_score || 60;
      return (isStudentPassed(a, passingScore) ? 1 : 0) - (isStudentPassed(b, passingScore) ? 1 : 0);
    }
  },
  {
    title: '得分',
    key: 'score',
    sorter: (a: StudentPaper, b: StudentPaper) => (a.obtained_score || 0) - (b.obtained_score || 0)
  },
  {
    title: '评阅状态',
    key: 'marking',
    sorter: (a: StudentPaper, b: StudentPaper) => {
      const statusOrder: Record<string, number> = { 
        'fully_graded': 3,
        'partially_graded': 2,
        'auto_graded': 1,
        'not_graded': 0
      };
      return (statusOrder[a.grading_status] || 0) - (statusOrder[b.grading_status] || 0);
    }
  },
  {
    title: '操作',
    key: 'action'
  }
];

// 辅助函数
function getScoreColor(student: StudentPaper): string {
  const passingScore = exam.value?.passing_score || 60;
  return isStudentPassed(student, passingScore) ? 'green' : 'red';
}

function getScorePercent(student: StudentPaper): number {
  return Math.round(((student.obtained_score || 0) / student.total_score) * 100);
}

function needMarking(student: StudentPaper): boolean {
  return student.grading_status === 'not_graded' || student.grading_status === 'partially_graded';
}

// 事件处理
function handleSearch() {
  currentPage.value = 1;
  loadStudentPapers();
}

function handleFilterChange() {
  currentPage.value = 1;
  loadStudentPapers();
}

function viewPaper(paper: StudentPaper) {
  // 跳转到试卷查看页面
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/paper/${paper.student_id}`);
}

function markPaper(paper: StudentPaper) {
  // 跳转到试卷阅卷页面
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/marking/${paper.student_id}`);
}

// 加载考试信息
async function loadExamInfo() {
  try {
    const res = await getExamDetail({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (res.code === '0000') {
      exam.value = res.data;
    } else {
      message.error(res.message || '获取考试信息失败');
    }
  } catch (error) {
    console.error('获取考试信息失败:', error);
    message.error('获取考试信息失败');
  }
}

// 加载学生试卷列表
async function loadStudentPapers() {
  loading.value = true;
  try {
    // 构建查询参数
    const params: any = {
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      page: currentPage.value,
      page_size: pageSize.value
    };
    
    // 添加搜索关键词
    if (searchText.value) {
      params.keyword = searchText.value;
    }
    
    // 添加状态筛选
    if (filterType.value !== 'all') {
      // 这里可能需要根据后端接口调整
      params.status = filterType.value;
    }
    
    const res = await getExamPapers(params);
    
    if (res.code === '0000') {
      studentPapers.value = res.data.list;
      totalRecords.value = res.data.meta.total;
    } else {
      message.error(res.message || '获取学生试卷列表失败');
    }
  } catch (error) {
    console.error('获取学生试卷列表失败:', error);
    message.error('获取学生试卷列表失败');
  } finally {
    loading.value = false;
  }
}

// 加载考试统计信息
async function loadExamStatistics() {
  try {
    const res = await getExamStatistics({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (res.code === '0000') {
      examStats.value = res.data;
    } else {
      console.error('获取考试统计信息失败:', res.message);
    }
  } catch (error) {
    console.error('获取考试统计信息失败:', error);
  }
}

// 数据加载
async function fetchData() {
  await Promise.all([
    loadExamInfo(),
    loadStudentPapers(),
    loadExamStatistics()
  ]);
}

// 生命周期钩子
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.exam-results-page {
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
  margin-bottom: 24px;
}

.score-percent {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-left: 4px;
}

.stats-container {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.stats-container h2 {
  margin-top: 0;
  margin-bottom: 16px;
}

.stats-cards {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.stats-cards .ant-card {
  width: calc(25% - 12px);
  min-width: 200px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #1890ff;
  margin-bottom: 8px;
}

.stat-desc {
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

@media (max-width: 768px) {
  .stats-cards .ant-card {
    width: calc(50% - 8px);
  }
}

@media (max-width: 576px) {
  .stats-cards .ant-card {
    width: 100%;
  }
  
  .filter-section {
    flex-direction: column;
    gap: 16px;
  }
}
</style> 