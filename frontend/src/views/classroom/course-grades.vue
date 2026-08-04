<template>
  <PageShell max-width="wide" class="course-grades-page">
    <PageHeaderBar
      :title="course?.name || '课程成绩'"
      :subtitle="gradesSubtitle"
      show-back
      :back-to="`/classroom/${classroomId}/status`"
    >
      <template #actions>
        <a-tag v-if="course?.type" :color="course.type === 'practice' ? 'blue' : 'green'">
          {{ course.type === 'practice' ? '实践课程' : '实训课程' }}
        </a-tag>
      </template>
    </PageHeaderBar>

      <a-card class="stats-card">
        <a-row :gutter="16">
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ studentCount }}</div>
              <div class="stat-label">总学生数</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ completedCount }}</div>
              <div class="stat-label">已完成学生</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ inProgressCount }}</div>
              <div class="stat-label">进行中学生</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ notStartedCount }}</div>
              <div class="stat-label">未开始学生</div>
            </div>
          </a-col>
        </a-row>
        <a-row :gutter="16" v-if="!isPractice" class="comment-stats">
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ commentedCount }}</div>
              <div class="stat-label">已点评作业</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ notCommentedCount }}</div>
              <div class="stat-label">未点评作业</div>
            </div>
          </a-col>
          <a-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ excellentCount }}</div>
              <div class="stat-label">优秀作业</div>
            </div>
          </a-col>
        </a-row>
      </a-card>

      <a-card class="grades-card">
        <div class="grades-header">
          <div class="grades-filter">
            <!-- 作业状态筛选（复选框组） -->
            <div class="filter-group" v-if="isPractice !== false">
              <span class="filter-label">作业状态：</span>
              <a-checkbox-group v-model:value="selectedStatuses" @change="onStatusChange">
                <a-checkbox value="all">全选</a-checkbox>
                <a-checkbox value="not_started">未开始</a-checkbox>
                <a-checkbox value="in_progress">未通关</a-checkbox>
                <a-checkbox value="completed">按时通关</a-checkbox>
                <a-checkbox value="late_completed">补交通关</a-checkbox>
              </a-checkbox-group>
            </div>
            <div class="filter-group" v-else>
              <span class="filter-label">作业状态：</span>
              <a-checkbox-group v-model:value="selectedStatuses" @change="onStatusChange">
                <a-checkbox value="all">全选</a-checkbox>
                <a-checkbox value="not_started">未开始</a-checkbox>
                <a-checkbox value="not_submitted">未提交</a-checkbox>
                <a-checkbox value="submitted">已提交</a-checkbox>
                <a-checkbox value="late_submitted">已补交</a-checkbox>
              </a-checkbox-group>
            </div>

            <!-- 点评状态筛选（复选框组 - 仅实训课程） -->
            <div class="filter-group" v-if="!isPractice">
              <span class="filter-label">点评状态：</span>
              <a-checkbox-group v-model:value="selectedCommentStatuses" @change="onCommentStatusChange">
                <a-checkbox value="all">全选</a-checkbox>
                <a-checkbox value="commented">已点评</a-checkbox>
                <a-checkbox value="not_commented">未点评</a-checkbox>
              </a-checkbox-group>
            </div>

            <a-input-search
              v-model:value="searchText"
              placeholder="搜索学生姓名或学号"
              style="width: 250px"
              @search="onSearch"
            />
          </div>
          <div class="grades-export">
            <a-button type="primary">
              <template #icon><download-outlined /></template>
              导出成绩
            </a-button>
          </div>
        </div>

        <!-- 实践课程成绩表格 -->
        <a-table 
          v-if="isPractice"
          :columns="practiceColumns" 
          :data-source="filteredStudents" 
          :loading="loading"
          :pagination="{ 
            current: currentPage,
            pageSize: 10, 
            total: totalCount,
            showTotal: (total: number) => `共 ${total} 条记录`,
            onChange: (page: number) => {
              currentPage.value = page;
              fetchStudentGrades();
            }
          }"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            <template v-if="column.key === 'completedTasks'">
              <span>{{ record.completedTasks }}/{{ record.totalTasks }}</span>
            </template>
            <template v-if="column.key === 'penalty'">
              <a-input-number 
                v-if="record.status === 'late_completed'"
                v-model:value="record.penalty" 
                :min="0" 
                :max="100" 
                :disabled="!record.canEditPenalty"
                @change="updatePenalty(record)"
              />
              <span v-else>-</span>
            </template>
            <template v-if="column.key === 'finalScore'">
              <span :class="{'score-highlight': record.finalScore >= 90}">
                {{ record.finalScore }}
              </span>
            </template>
            <template v-if="column.key === 'action'">
              <a-button type="link" @click="viewStudentDetail(record)">查看详情</a-button>
            </template>
          </template>
        </a-table>

        <!-- 实训课程成绩表格 -->
        <a-table 
          v-else
          :columns="trainingColumns" 
          :data-source="filteredStudents" 
          :loading="loading"
          :pagination="{ 
            current: currentPage,
            pageSize: 10, 
            total: totalCount,
            showTotal: (total: number) => `共 ${total} 条记录`,
            onChange: (page: number) => {
              currentPage.value = page;
              fetchStudentGrades();
            }
          }"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div style="display: flex; align-items: center; gap: 8px;">
                <a-avatar :size="28" :src="record.avatar">
                  <template #icon><UserOutlined /></template>
                </a-avatar>
                <span>{{ record.name }}</span>
              </div>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            <template v-if="column.key === 'commentStatus'">
              <a-tag :color="record.commentStatus === 'commented' ? 'green' : 'orange'">
                {{ record.commentStatus === 'commented' ? '已点评' : '未点评' }}
              </a-tag>
            </template>
            <template v-if="column.key === 'score'">
              <template v-if="record.status === 'submitted' || record.status === 'late_submitted'">
                <span v-if="record.commentStatus === 'commented'">{{ record.score }}</span>
                <a-input-number 
                  v-else
                  v-model:value="record.score" 
                  :min="0" 
                  :max="100" 
                  @change="updateScore(record)"
                />
              </template>
              <span v-else>-</span>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <!-- 查看作业按钮：已提交/已补交可点击，未提交/未开始置灰 -->
                <a-button
                  type="link"
                  :disabled="record.status !== 'submitted' && record.status !== 'late_submitted'"
                  @click="viewHomework(record)"
                >
                  查看作业
                </a-button>
                <template v-if="record.status === 'submitted' || record.status === 'late_submitted'">
                  <a-button type="link" @click="openCommentModal(record)">
                    {{ record.commentStatus === 'commented' ? '修改点评' : '点评' }}
                  </a-button>
                  <template v-if="record.commentStatus === 'commented'">
                    <a-button
                      v-if="!record.isExcellent"
                      type="link"
                      @click="markAsExcellent(record)"
                    >
                      设为优秀
                    </a-button>
                    <a-button
                      v-else
                      type="link"
                      danger
                      @click="removeExcellent(record)"
                    >
                      取消优秀
                    </a-button>
                  </template>
                </template>
                <a-button type="link" @click="viewStudentDetail(record)">查看详情</a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

    <!-- 点评模态框 -->
    <a-modal
      v-model:open="commentModalVisible"
      :title="`为 ${currentStudent?.name || ''} 评分点评`"
      @ok="submitComment"
      :confirm-loading="submittingComment"
      width="600px"
    >
      <a-form layout="vertical">
        <a-form-item label="分数">
          <a-input-number 
            v-model:value="commentForm.score" 
            :min="0" 
            :max="100" 
            style="width: 100%" 
          />
        </a-form-item>
        <a-form-item label="点评意见">
          <a-textarea 
            v-model:value="commentForm.comment" 
            :rows="4" 
            placeholder="请输入点评意见" 
          />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="commentForm.isExcellent">
            设为优秀作业（可供其他学生参考学习）
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import {
  ArrowLeftOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  DownloadOutlined,
  UserOutlined
} from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import { useClassroomStore } from '../../stores/classroom';
import { useUserStore } from '../../stores/user';
import { getClassroomCoursesWithStats } from '@/api/classrooms';
import type { ClassroomDetail, CourseItem } from '@/types/classroom';
import type { TableColumnsType } from 'ant-design-vue';
import { getToken } from '@/utils/auth';

// 模拟学生成绩数据接口
interface PracticeStudentGrade {
  id: string;
  name: string;
  studentId: string;
  status: 'not_started' | 'in_progress' | 'completed' | 'late_completed';
  completedTasks: number;
  totalTasks: number;
  submittedAt: string | null;
  totalTime: number; // 分钟
  taskScore: number;
  penalty: number;
  finalScore: number;
  canEditPenalty: boolean;
}

// 修改实训课程相关的数据接口
interface TrainingStudentGrade {
  id: string;
  name: string;
  studentId: string;
  status: 'not_started' | 'not_submitted' | 'submitted' | 'late_submitted';
  startedAt: string | null;
  submittedAt: string | null;
  score: number | null;
  commentStatus: 'not_commented' | 'commented';
  comment: string;
  isExcellent: boolean;
}

type StudentGrade = PracticeStudentGrade | TrainingStudentGrade;

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();

// 加载状态
const loading = ref(false);
// 当前课堂ID和课堂课程ID
const classroomId = computed(() => route.params.classroomId as string);

const gradesSubtitle = computed(() => {
  const parts: string[] = [];
  if (course.value?.startDate) parts.push(`发布：${formatDate(course.value.startDate)}`);
  if (course.value?.endDate) parts.push(`截止：${formatDate(course.value.endDate)}`);
  return parts.join(' · ');
});
const classroomCourseId = computed(() =>
  (route.params.classroomCourseId || route.params.courseId) as string
);
// 当前课堂和课程
const currentClassroom = computed(() => classroomStore.currentClassroom);
const course = ref<CourseItem | null>(null);
// 搜索和筛选
const searchText = ref('');
const searchKeyword = ref('');
const currentStatus = ref('all');
const commentStatusFilter = ref('all');
// 复选框筛选状态
const selectedStatuses = ref<string[]>([]);
const selectedCommentStatuses = ref<string[]>([]);
// 分页
const currentPage = ref(1);
const pageSize = ref(10);
const totalCount = ref(0);
// 学生成绩列表
const students = ref<StudentGrade[]>([]);

// 判断是否是实践课程
const isPractice = computed(() => course.value?.type === 'practice');

const normalizeCourseType = (value?: string) => {
  if (!value) return 'practice';
  const type = value.toLowerCase();
  return type === 'course' || type === 'practice_course' ? 'practice' : type;
};

const normalizeCourseForGrades = (raw: any): CourseItem => {
  const courseName = raw.name_override || raw.course_name || raw.course?.title || raw.practice?.title || raw.title || raw.name || '课程成绩';
  return {
    ...raw,
    id: String(raw.classroom_course_id || raw.classroomCourseId || raw.id),
    classroom_course_id: raw.classroom_course_id || raw.classroomCourseId || raw.id,
    course_id: raw.course_id || raw.course?.id,
    practice_id: raw.practice_id || raw.practice?.id,
    name: courseName,
    title: courseName,
    type: normalizeCourseType(raw.source_type || raw.type || raw.course?.course_type || raw.training_type) as any
  };
};

const matchesClassroomCourseId = (candidate: any, idStr: string, idNum: number) => {
  return [candidate.classroom_course_id, candidate.classroomCourseId, candidate.id]
    .some(value => String(value) === idStr || value === idNum);
};

const extractEnhancedCourses = (response: any) => {
  const data = response?.data ?? response;
  if (Array.isArray(data)) return data;
  return data?.list || data?.courses || [];
};

const extractGradeRows = (payload: any) => {
  const data = payload?.data ?? payload;
  return data?.grades || data?.list || data?.data?.grades || data?.data?.list || [];
};

const extractGradeTotal = (payload: any, fallback: number) => {
  const data = payload?.data ?? payload;
  return data?.total || data?.meta?.total || data?.data?.total || data?.data?.meta?.total || fallback;
};

// 实践课程表格列
const practiceColumns = computed<TableColumnsType>(() => [
  {
    title: '学生姓名',
    dataIndex: 'name',
    key: 'name',
    width: '12%',
  },
  {
    title: '学号',
    dataIndex: 'studentId',
    key: 'studentId',
    width: '12%',
  },
  {
    title: '作业状态',
    dataIndex: 'status',
    key: 'status',
    width: '10%',
  },
  {
    title: '提交时间',
    dataIndex: 'submittedAt',
    key: 'submittedAt',
    width: '15%',
    customRender: ({ text }) => text ? formatDateTime(text) : '-',
  },
  {
    title: '作业总耗时',
    dataIndex: 'totalTime',
    key: 'totalTime',
    width: '10%',
    customRender: ({ text }) => text ? formatTime(text) : '-',
  },
  {
    title: '完成关卡',
    dataIndex: 'completedTasks',
    key: 'completedTasks',
    width: '10%',
  },
  {
    title: '关卡得分',
    dataIndex: 'taskScore',
    key: 'taskScore',
    width: '8%',
  },
  {
    title: '奖惩情况',
    dataIndex: 'penalty',
    key: 'penalty',
    width: '10%',
  },
  {
    title: '当前成绩',
    dataIndex: 'finalScore',
    key: 'finalScore',
    width: '8%',
  },
  {
    title: '操作',
    key: 'action',
    width: '10%',
  }
]);

// 更新实训课程表格列
const trainingColumns = computed<TableColumnsType>(() => [
  {
    title: '序号',
    key: 'index',
    width: '5%',
    customRender: ({ index }) => index + 1 + (currentPage.value - 1) * 10,
  },
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    width: '10%',
  },
  {
    title: '学号',
    dataIndex: 'studentId',
    key: 'studentId',
    width: '12%',
  },
  {
    title: '作业状态',
    dataIndex: 'status',
    key: 'status',
    width: '10%',
  },
  {
    title: '提交时间',
    dataIndex: 'submittedAt',
    key: 'submittedAt',
    width: '15%',
    customRender: ({ text }) => text ? formatDateTime(text) : '-',
  },
  {
    title: '点评状态',
    dataIndex: 'commentStatus',
    key: 'commentStatus',
    width: '10%',
    customRender: ({ text }) => {
      return text === 'commented' ? '已点评' : '未点评';
    },
  },
  {
    title: '当前成绩',
    dataIndex: 'score',
    key: 'score',
    width: '10%',
    customRender: ({ text }) => text !== null ? text : '-',
  },
  {
    title: '操作',
    key: 'action',
    width: '18%',
  }
]);

// 筛选后的学生列表
const filteredStudents = computed(() => {
  let result = students.value;

  // 按状态筛选
  if (currentStatus.value !== 'all') {
    result = result.filter(student => student.status === currentStatus.value);
  }

  // 按点评状态筛选（只适用于实训课程）
  if (!isPractice.value && commentStatusFilter.value !== 'all') {
    result = result.filter(student => {
      // 类型断言确保TypeScript知道我们正在处理TrainingStudentGrade类型
      const trainingStudent = student as TrainingStudentGrade;
      return trainingStudent.commentStatus === commentStatusFilter.value;
    });
  }

  // 按搜索文本筛选
  if (searchText.value) {
    const lowerSearchText = searchText.value.toLowerCase();
    result = result.filter(student =>
      student.name.toLowerCase().includes(lowerSearchText) ||
      student.studentId.toLowerCase().includes(lowerSearchText)
    );
  }

  return result;
});

// 学生统计数据
const studentCount = computed(() => students.value.length);
const completedCount = computed(() => {
  if (isPractice.value) {
    return students.value.filter(s => 
      s.status === 'completed' || s.status === 'late_completed'
    ).length;
  } else {
    return students.value.filter(s => 
      s.status === 'submitted' || s.status === 'late_submitted'
    ).length;
  }
});
const inProgressCount = computed(() => {
  if (isPractice.value) {
    return students.value.filter(s => s.status === 'in_progress').length;
  } else {
    return students.value.filter(s => s.status === 'not_submitted').length;
  }
});
const notStartedCount = computed(() => {
  return students.value.filter(s => s.status === 'not_started').length;
});

// 评论状态统计
const commentedCount = computed(() => {
  if (!isPractice.value) {
    return students.value.filter(s => {
      const trainingStudent = s as TrainingStudentGrade;
      return trainingStudent.commentStatus === 'commented';
    }).length;
  }
  return 0;
});

const notCommentedCount = computed(() => {
  if (!isPractice.value) {
    return students.value.filter(s => {
      const trainingStudent = s as TrainingStudentGrade;
      return (trainingStudent.status === 'submitted' || trainingStudent.status === 'late_submitted') 
        && trainingStudent.commentStatus === 'not_commented';
    }).length;
  }
  return 0;
});

const excellentCount = computed(() => {
  if (!isPractice.value) {
    return students.value.filter(s => {
      const trainingStudent = s as TrainingStudentGrade;
      return trainingStudent.isExcellent;
    }).length;
  }
  return 0;
});

// 获取状态文本
const getStatusText = (status: string) => {
  if (isPractice.value) {
    switch (status) {
      case 'not_started': return '未开始';
      case 'in_progress': return '未通关';
      case 'completed': return '按时通关';
      case 'late_completed': return '补交通关';
      default: return '未知状态';
    }
  } else {
    switch (status) {
      case 'not_started': return '未开始';
      case 'not_submitted': return '未提交';
      case 'submitted': return '已提交';
      case 'late_submitted': return '已补交';
      default: return '未知状态';
    }
  }
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'not_started': return 'default';  // 灰色
    case 'in_progress': return 'blue';     // 蓝色（实践课程进行中）
    case 'not_submitted': return 'red';    // 红色（实训课程未提交）
    case 'completed':
    case 'submitted':
      return 'green';  // 绿色
    case 'late_completed':
    case 'late_submitted':
      return 'gold';   // 黄色（已补交）
    default: return 'default';
  }
};

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss');
};

// 格式化时间（分钟转为小时和分钟）
const formatTime = (minutes: number) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
};

// 返回上一页
const goBack = () => {
  router.push(`/classroom/${classroomId.value}/status`);
};

// 搜索
const onSearch = () => {
  searchKeyword.value = searchText.value;
};

// 作业状态复选框变化
const onStatusChange = (checkedValues: string[]) => {
  if (checkedValues.includes('all')) {
    // 如果选中了"全选"，则只保留"all"并清除其他选择
    if (isPractice.value) {
      selectedStatuses.value = ['all', 'not_started', 'in_progress', 'completed', 'late_completed'];
    } else {
      selectedStatuses.value = ['all', 'not_started', 'not_submitted', 'submitted', 'late_submitted'];
    }
  }
  // 更新筛选状态
  updateStatusFilter();
};

// 点评状态复选框变化
const onCommentStatusChange = (checkedValues: string[]) => {
  if (checkedValues.includes('all')) {
    selectedCommentStatuses.value = ['all', 'commented', 'not_commented'];
  }
  // 更新筛选状态
  updateCommentStatusFilter();
};

// 更新作业状态筛选
const updateStatusFilter = () => {
  if (selectedStatuses.value.includes('all') && selectedStatuses.value.length > 1) {
    // 如果有"全选"和其他选项，只保留"全选"
    if (isPractice.value) {
      selectedStatuses.value = ['all'];
    } else {
      selectedStatuses.value = ['all'];
    }
  }

  if (selectedStatuses.value.includes('all')) {
    currentStatus.value = 'all';
  } else if (selectedStatuses.value.length === 1) {
    currentStatus.value = selectedStatuses.value[0];
  } else if (selectedStatuses.value.length > 1) {
    // 多个选项（不包括全选），转为第一个选中的非all选项
    currentStatus.value = selectedStatuses.value.find(s => s !== 'all') || 'all';
  } else {
    currentStatus.value = 'all';
  }
};

// 更新点评状态筛选
const updateCommentStatusFilter = () => {
  if (selectedCommentStatuses.value.includes('all') && selectedCommentStatuses.value.length > 1) {
    selectedCommentStatuses.value = ['all'];
  }

  if (selectedCommentStatuses.value.includes('all')) {
    commentStatusFilter.value = 'all';
  } else if (selectedCommentStatuses.value.length === 1) {
    commentStatusFilter.value = selectedCommentStatuses.value[0];
  } else if (selectedCommentStatuses.value.length > 1) {
    commentStatusFilter.value = selectedCommentStatuses.value.find(s => s !== 'all') || 'all';
  } else {
    commentStatusFilter.value = 'all';
  }
};

// 查看学生详情
const viewStudentDetail = (student: StudentGrade) => {
  message.info(`查看学生 "${student.name}" 的详情功能尚未实现`);
};

// 查看作业（实训课程）
const viewHomework = (student: TrainingStudentGrade) => {
  // 使用新的作业详情页 (支持BI快照查看)
  router.push({
    name: 'SubmissionDetail',
    params: { progressId: student.id }
  });
};

// 评分和点评相关状态
const commentModalVisible = ref(false);
const submittingComment = ref(false);
const currentStudent = ref<TrainingStudentGrade | null>(null);
const commentForm = reactive({
  score: 0,
  comment: '',
  isExcellent: false
});

// 打开点评模态框
const openCommentModal = (student: TrainingStudentGrade) => {
  currentStudent.value = student;
  commentForm.score = student.score ?? 0;
  commentForm.comment = student.comment;
  commentForm.isExcellent = student.isExcellent;
  commentModalVisible.value = true;
};

// 提交点评
const submitComment = async () => {
  if (!currentStudent.value) return;
  
  submittingComment.value = true;
  
  try {
    const userStore = useUserStore();
    const teacherId = userStore.userInfo?.id || userStore.userId;
    
    if (!teacherId) {
      message.error('无法获取教师ID');
      return;
    }
    
    const response = await fetch(`/api/v1/grades/classroom-courses/${classroomCourseId.value}/students/${currentStudent.value.numericStudentId}/grade?teacher_id=${teacherId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        score: commentForm.score,
        feedback: commentForm.comment,
        is_excellent: commentForm.isExcellent
      })
    });
    
    const result = await response.json();
    
    if (result.code === '0000') {
      if (currentStudent.value) {
        currentStudent.value.score = commentForm.score;
        currentStudent.value.comment = commentForm.comment;
        currentStudent.value.isExcellent = commentForm.isExcellent;
        currentStudent.value.commentStatus = 'commented';
      }
      
      message.success('点评提交成功');
      commentModalVisible.value = false;
      
      // 刷新成绩列表
      await fetchStudentGrades();
    } else {
      message.error(result.message || '点评提交失败');
    }
  } catch (error) {
    console.error('提交点评失败:', error);
    message.error('提交点评失败');
  } finally {
    submittingComment.value = false;
  }
};

// 标记为优秀作业
const markAsExcellent = (student: TrainingStudentGrade) => {
  student.isExcellent = true;
  message.success(`已将 ${student.name} 的作业设为优秀作业`);
};

// 移除优秀作业标记
const removeExcellent = (student: TrainingStudentGrade) => {
  student.isExcellent = false;
  message.success(`已取消 ${student.name} 作业的优秀标记`);
};

// 更新成绩（实训课程）
const updateScore = (student: TrainingStudentGrade) => {
  if (student.score !== null) {
    student.commentStatus = 'commented';
  }
  message.success('已更新学生成绩');
};

// 更新补交扣分（实践课程）
const updatePenalty = (student: PracticeStudentGrade) => {
  // 更新最终成绩
  student.finalScore = Math.max(0, student.taskScore - student.penalty);
  message.success('已更新学生扣分情况');
};

// 获取课程详情和学生成绩
const fetchCourseDetail = async () => {
  loading.value = true;
  try {
    // 路由切换课堂时不能复用上一课堂缓存,否则 cc_id 会在错误课堂中查找.
    if (!currentClassroom.value || String((currentClassroom.value as any).id) !== classroomId.value) {
      await classroomStore.fetchClassroomDetail(classroomId.value);
    }
    
    const classroom = currentClassroom.value || classroomStore.currentClassroom;
    if (!classroom) {
      message.error('未找到课堂');
      router.push(`/classroom/${classroomId.value}/status`);
      return;
    }
    
    // route 参数统一为 classroom_course_id(cc_id),不混用 master course_id / practice_id
    const courseIdStr = String(classroomCourseId.value);
    const courseIdNum = Number(classroomCourseId.value);
    
    let foundCourse: any = null;

    const courseResponse = await getClassroomCoursesWithStats({
      classroomId: Number(classroomId.value),
      page: 1,
      pageSize: 100
    });
    const enhancedCourses = courseResponse.code === '0000' ? extractEnhancedCourses(courseResponse) : [];
    foundCourse = enhancedCourses.find((c: any) => matchesClassroomCourseId(c, courseIdStr, courseIdNum));
    
    // 再从course_list（实训）中查找旧缓存
    if (!foundCourse) {
      foundCourse = classroom.course_list?.find((c: any) => 
        matchesClassroomCourseId(c, courseIdStr, courseIdNum)
      );
    }
    
    // 如果没找到，从practice_list中查找
    if (!foundCourse) {
      foundCourse = classroom.practice_list?.find((c: any) => 
        matchesClassroomCourseId(c, courseIdStr, courseIdNum)
      );
      if (foundCourse) {
        // 统一字段名称
        foundCourse = {
          ...foundCourse,
          name: foundCourse.title || foundCourse.name,
          type: 'practice'
        };
      }
    }
    
    // 还可以尝试从courses字段查找（兼容旧数据结构）
    if (!foundCourse && classroom.courses) {
      foundCourse = classroom.courses.find((c: any) => 
        matchesClassroomCourseId(c, courseIdStr, courseIdNum)
      );
    }

    if (foundCourse) {
      // R2: 统一 lowercase, 兼容 backend 大写 PRACTICE/TRAINING enum 值
      course.value = normalizeCourseForGrades(foundCourse);
      await fetchStudentGrades();
    } else {
      // 如果从classroom列表中找不到课程，使用URL参数创建虚拟课程对象
      // 这样可以支持实训（training）类型的课程
      console.warn('未找到课堂课程, classroomCourseId:', classroomCourseId.value, '使用URL参数作为备用');
      const courseName = route.query.courseName as string;
      const courseTypeParam = route.query.courseType as string;
      
      if (courseName) {
        course.value = {
          id: classroomCourseId.value,
          classroom_course_id: classroomCourseId.value,
          course_id: route.query.courseId as string,
          practice_id: route.query.practiceId as string,
          name: courseName,
          title: courseName,
          // R2: lowercase 化 — status 页 navigate 时传 PRACTICE 大写, 老逻辑
          // === 'practice' 不匹配 → 走 training 分支 → "当前成绩" 列空 等 UI 错乱
          type: normalizeCourseType(courseTypeParam) as any
        };
        // isPractice 会自动根据 course.value.type 计算
        await fetchStudentGrades();
      } else {
        course.value = {
          id: classroomCourseId.value,
          classroom_course_id: classroomCourseId.value,
          course_id: route.query.courseId as string,
          practice_id: route.query.practiceId as string,
          name: '课程成绩',
          title: '课程成绩',
          type: 'practice'
        };
        await fetchStudentGrades();
      }
    }
  } catch (error) {
    console.error('获取课程详情失败:', error);
    message.error('获取课程详情失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 获取学生成绩列表
const fetchStudentGrades = async () => {
  loading.value = true;
  try {
    const userStore = useUserStore();
    const teacherId = userStore.userInfo?.id || userStore.userId;
    
    if (!teacherId) {
      message.error('无法获取教师ID');
      return;
    }
    
    // 教师成绩页直接读取同源 API, 避免不同历史 endpoint/axios wrapper
    // 返回形态不一致导致 grades/list 被误判为空。
    const params = new URLSearchParams({
      teacher_id: String(teacherId),
      page: String(currentPage.value),
      page_size: String(pageSize.value)
    });
    if (currentStatus.value !== 'all') params.set('status', currentStatus.value);
    if (searchKeyword.value) params.set('keyword', searchKeyword.value);

    const fetchResponse = await fetch(
      `/api/v1/classrooms/${classroomId.value}/courses/${classroomCourseId.value}/grades?${params.toString()}`,
      {
        headers: {
          'Authorization': `Bearer ${getToken() || ''}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const response = await fetchResponse.json();
    
    if (response.code === '0000' && response.data) {
      const gradeList = extractGradeRows(response);
      
    if (course.value?.type === 'practice') {
      // 实践课程成绩
        students.value = gradeList.map((grade: any) => ({
          id: grade.id.toString(),
          name: grade.name,
          studentId: grade.studentId,
          status: grade.status === 'COMPLETED_ON_TIME' ? 'completed' : 
                  grade.status === 'COMPLETED_LATE' ? 'late_completed' :
                  grade.status === 'LEARNING' ? 'in_progress' : 'not_started',
          completedTasks: grade.completedTasks || 0,
          totalTasks: grade.totalTasks || 0,
          submittedAt: grade.submittedAt,
          totalTime: grade.totalTime || 0,
          taskScore: grade.taskScore || 0,
          penalty: grade.penalty || 0,
          finalScore: grade.finalScore || 0,
          canEditPenalty: grade.canEditPenalty || false
        }));
      } else {
        // 实训课程成绩
        students.value = gradeList.map((grade: any) => ({
          id: grade.id.toString(),
          name: grade.name,
          studentId: grade.studentId,
          numericStudentId: grade.numericStudentId,  // 数字ID用于API调用
          status: grade.submissionStatus === 'SUBMITTED' ? 'submitted' :
                  grade.submissionStatus === 'LATE_SUBMISSION' ? 'late_submitted' :
                  grade.submissionStatus === 'IN_PROGRESS' ? 'not_submitted' : 'not_started',
          startedAt: grade.firstAccessAt || grade.first_access_at,
          submittedAt: grade.submittedAt || grade.last_submission_at,
          score: grade.finalScore || grade.overall_score || grade.final_calculated_score || null,
          commentStatus: grade.commentStatus === 'commented' ? 'commented' : 'not_commented',
          comment: grade.teacherFeedback || grade.teacher_feedback || '',
          isExcellent: grade.isExcellentWork || grade.is_excellent_work || false
        }));
      }
      
      // 更新统计数据
      totalCount.value = extractGradeTotal(response, gradeList.length);
    } else {
      message.error(response.message || '获取成绩列表失败');
    }
  } catch (error: any) {
    console.error('获取学生成绩失败:', error);
    message.error('获取学生成绩失败，请稍后重试');
  } finally {
    loading.value = false;
    }
};

// 组件挂载时获取课程详情和学生成绩
onMounted(() => {
  fetchCourseDetail();
});

// 监听筛选条件变化，自动刷新数据
watch([currentStatus, searchKeyword, currentPage], () => {
  if (course.value) {
    fetchStudentGrades();
  }
});
</script>

<style scoped>
.course-grades-page {
  /* PageShell handles outer padding */
}



.classroom-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.classroom-title-container {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.classroom-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  margin-right: 12px;
}

.classroom-meta {
  display: flex;
  color: rgba(0, 0, 0, 0.45);
  gap: 16px;
  font-size: 14px;
}

.stats-card {
  margin-bottom: var(--hx-space-4);
}

.comment-stats {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e8e8e8;
}

.stat-item {
  text-align: center;
  padding: 16px 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1890ff;
}

.stat-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.grades-card {
  margin-top: var(--hx-space-4);
  margin-bottom: var(--hx-space-4);
}

.grades-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--hx-space-4);
  flex-wrap: wrap;
  gap: var(--hx-space-4);
}

.grades-filter {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
}

.filter-label {
  color: rgba(0, 0, 0, 0.65);
  margin-right: 8px;
  white-space: nowrap;
}

.grades-export {
  flex-shrink: 0;
}

.score-highlight {
  color: #52c41a;
  font-weight: bold;
}
</style> 
