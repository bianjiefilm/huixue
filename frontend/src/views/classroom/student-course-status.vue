<template>
  <div class="student-course-status-page">
    <a-spin :spinning="classroomStore.loading.detail" tip="加载中...">
      <div v-if="currentClassroom" class="content-container">
        <!-- 返回按钮 -->
        <div class="back-link">
          <router-link to="/classroom">
            <a-button type="link">
              <template #icon><arrow-left-outlined /></template>
              返回课堂列表
            </a-button>
          </router-link>
        </div>

        <!-- 课堂标题和状态 -->
        <div class="classroom-header">
          <div class="status-badge" :class="getStatusClass(currentClassroom.status)">
            {{ getStatusText(currentClassroom.status) }}
          </div>
          <h1 class="classroom-title">{{ currentClassroom.name }}</h1>
          <div class="student-info">
            <a-tag color="blue">
              <user-outlined />
              {{ userInfo.username || '学生' }}
            </a-tag>
            <a-tag color="green">
              <calendar-outlined />
              {{ currentClassroom.semester }}
            </a-tag>
            <a-button 
              type="primary" 
              @click="viewStudentGrades"
              class="grades-button"
            >
              查看成绩单
            </a-button>
          </div>
        </div>

        <!-- 课堂基本信息卡片 -->
        <a-card class="info-card">
          <div class="classroom-info">
            <div class="info-item">
              <book-outlined />
              <span>教师：{{ currentClassroom.teacherName }}</span>
            </div>
            <div class="info-item">
              <calendar-outlined />
              <span>起止时间：{{ formatDate(currentClassroom.startDate) }} 至 {{ formatDate(currentClassroom.endDate) }}</span>
            </div>
            <div class="info-item">
              <trophy-outlined />
              <span>学分：{{ currentClassroom.credits }}</span>
            </div>
            <div class="info-item">
              <team-outlined />
              <span>学生数量：{{ currentClassroom.studentCount }}</span>
            </div>
          </div>
        </a-card>

        <!-- 课程状态切换标签 -->
        <a-card class="courses-card">
          <a-tabs v-model:activeKey="activeTabKey" @change="handleTabChange">
            <a-tab-pane :key="'all'" :tab="`全部课程 ${totalCourses}`">
              <a-list 
                :data-source="filteredCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无课程" />
                </template>
              </a-list>
            </a-tab-pane>
            
            <!-- 未开始课程 - 只在课堂未结束时显示 -->
            <a-tab-pane v-if="currentClassroom.status !== 'past'" :key="'not_started'" :tab="`未开始 ${notStartedCount}`">
              <a-list 
                :data-source="notStartedCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无未开始的课程" />
                </template>
              </a-list>
            </a-tab-pane>
            
            <!-- 学习中课程 - 只在课堂未结束时显示 -->
            <a-tab-pane v-if="currentClassroom.status !== 'past'" :key="'learning'" :tab="`学习中 ${learningCount}`">
              <a-list 
                :data-source="learningCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无学习中的课程" />
                </template>
              </a-list>
            </a-tab-pane>
            
            <!-- 待补交课程 - 只在课堂未结束时显示 -->
            <a-tab-pane v-if="currentClassroom.status !== 'past'" :key="'makeup'" :tab="`待补交 ${makeupCount}`">
              <a-list 
                :data-source="makeupCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无待补交的课程" />
                </template>
              </a-list>
            </a-tab-pane>
            
            <!-- 已完成课程 -->
            <a-tab-pane :key="'completed'" :tab="`已完成 ${completedCount}`">
              <a-list 
                :data-source="completedCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无已完成的课程" />
                </template>
              </a-list>
            </a-tab-pane>
            
            <!-- 未完成课程 - 只在历史课堂中显示 -->
            <a-tab-pane v-if="currentClassroom.status === 'past'" :key="'incomplete'" :tab="`未完成 ${incompleteCount}`">
              <a-list 
                :data-source="incompleteCourses" 
                :loading="loading" 
                item-layout="horizontal"
              >
                <template #renderItem="{ item }">
                  <a-list-item>
                    <CourseItemComponent :course="item" :classroom="currentClassroom" :student-view="true" />
                  </a-list-item>
                </template>
                <template #empty>
                  <a-empty description="暂无未完成的课程" />
                </template>
              </a-list>
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </div>
      <a-result v-else status="404" title="找不到课堂" sub-title="您访问的课堂不存在或已被删除">
        <template #extra>
          <router-link to="/classroom">
            <a-button type="primary">返回课堂列表</a-button>
          </router-link>
        </template>
      </a-result>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  ArrowLeftOutlined, BookOutlined, CalendarOutlined, TrophyOutlined, 
  TeamOutlined, UserOutlined, ScheduleOutlined, CheckCircleOutlined,
  ClockCircleOutlined, ExclamationCircleOutlined
} from '@ant-design/icons-vue';
import { useClassroomStore } from '../../stores/classroom';
import { useUserStore } from '../../stores/user';
import dayjs from 'dayjs';
import type { ClassroomDetail, CourseItem as CourseItemType, CourseStatus } from '@/types/classroom';
import { getStudentCourses, getStudentCoursesSummary } from '../../api/classrooms';
import CourseItemComponent from '../../components/classroom/CourseItem.vue';

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();
const userStore = useUserStore();

// 获取课堂ID
const classroomId = computed(() => route.params.id as string);

// 当前课堂
const currentClassroom = computed(() => classroomStore.currentClassroom);

// 用户信息
const userInfo = computed(() => userStore.userInfo);

// 课程数据
const coursesList = ref<CourseItemType[]>([]);
const loading = ref(false);
const activeTabKey = ref('all');

// 状态统计数据
const statusSummary = ref({
  total: 0,
  not_started: 0,
  learning: 0,
  pending_makeup: 0,
  completed: 0
});

// 获取当前学生ID
const currentStudentId = computed(() => userStore.userId);

const requireCurrentStudentId = () => {
  const studentId = currentStudentId.value;
  if (!studentId) {
    message.warning('请先登录后再查看课程状态');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return studentId;
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'ongoing': return '正在上课';
    case 'upcoming': return '未开始';
    case 'past': return '历史课堂';
    default: return '未知状态';
  }
};

// 获取状态类名
const getStatusClass = (status: string) => {
  switch (status) {
    case 'ongoing': return 'status-ongoing';
    case 'upcoming': return 'status-upcoming';
    case 'past': return 'status-past';
    default: return '';
  }
};

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 基于API统计数据的计数
const totalCourses = computed(() => statusSummary.value.total);
const notStartedCount = computed(() => statusSummary.value.not_started);
const learningCount = computed(() => statusSummary.value.learning);
const makeupCount = computed(() => statusSummary.value.pending_makeup);
const completedCount = computed(() => statusSummary.value.completed);

// 历史课堂的未完成课程数（总数减去已完成）
const incompleteCount = computed(() => {
  if (currentClassroom.value?.status !== 'past') return 0;
  return statusSummary.value.total - statusSummary.value.completed;
});

// 过滤后的课程列表（用于显示）
const filteredCourses = computed(() => {
  return coursesList.value; // 学生端API已过滤了未发布课程
});

const notStartedCourses = computed(() => {
  return coursesList.value.filter(course => course.studentStatus === 'not_started');
});

const learningCourses = computed(() => {
  return coursesList.value.filter(course => course.studentStatus === 'learning');
});

const makeupCourses = computed(() => {
  return coursesList.value.filter(course => course.studentStatus === 'pending_makeup');
});

const completedCourses = computed(() => {
  return coursesList.value.filter(course => 
    course.studentStatus === 'completed_ontime' || course.studentStatus === 'completed_late'
  );
});

const incompleteCourses = computed(() => {
  if (currentClassroom.value?.status !== 'past') return [];
  return coursesList.value.filter(course => 
    course.studentStatus !== 'completed_ontime' && course.studentStatus !== 'completed_late'
  );
});

// 处理标签切换
const handleTabChange = (key: string) => {
  console.log('切换到标签:', key);
  // 重新获取过滤后的数据
  fetchClassroomDetail();
};

// 获取课堂详情和课程列表
const fetchClassroomDetail = async () => {
  loading.value = true;
  try {
    await classroomStore.fetchClassroomDetail(classroomId.value);
    
    // 获取学生课程列表
    const coursesResponse = await getStudentCourses({
      classroomId: parseInt(classroomId.value),
      studentId: requireCurrentStudentId(),
      status: activeTabKey.value === 'all' ? undefined : activeTabKey.value
    });
    
    // 处理课程列表数据
    if (coursesResponse.code === '0000') {
      const coursesData = coursesResponse.data.list || [];
      coursesList.value = coursesData.map((course: any) => ({
        id: course.id.toString(),
        name: course.title || '未命名课程',
        type: course.course_type || 'practice',
        status: 'published', // 学生端只显示已发布课程
        studentStatus: mapBackendStudentStatusToFrontend(course.student_status),
        studentScore: course.student_score || 0,
        completedTaskCount: course.completed_task_count || 0,
        totalTimeSpent: course.total_time_spent_seconds || 0,
        firstAccessAt: course.first_access_at,
        lastSubmissionAt: course.last_submission_at,
        coverUrl: course.cover_url,
        difficulty: course.difficulty,
        deadlineAt: course.deadline_at,
        makeupDeadlineAt: course.makeup_deadline_at,
        isMandatory: course.is_mandatory
      }));
      
      // 计算状态统计（临时方案）
      calculateStatusSummary(coursesList.value);
    }
  } catch (error) {
    console.error('获取课堂详情失败:', error);
    message.error('获取课堂详情失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 后端学生状态映射到前端状态
const mapBackendStudentStatusToFrontend = (backendStatus: string) => {
  const statusMap: Record<string, string> = {
    'NOT_STARTED': 'not_started',
    'LEARNING': 'learning',
    'PENDING_MAKEUP': 'pending_makeup',
    'COMPLETED_ON_TIME': 'completed_ontime',
    'COMPLETED_LATE': 'completed_late'
  };
  return statusMap[backendStatus] || 'not_started';
};

// 计算状态统计（临时方案，等后端提供统计API）
const calculateStatusSummary = (courses: any[]) => {
  statusSummary.value = {
    total: courses.length,
    not_started: courses.filter(c => c.studentStatus === 'not_started').length,
    learning: courses.filter(c => c.studentStatus === 'learning').length,
    pending_makeup: courses.filter(c => c.studentStatus === 'pending_makeup').length,
    completed: courses.filter(c => c.studentStatus === 'completed_ontime' || c.studentStatus === 'completed_late').length
  };
};

// 组件挂载时获取课堂详情
onMounted(() => {
  fetchClassroomDetail();
});

// 查看学生成绩单
const viewStudentGrades = () => {
  // 跳转到学生成绩单页面
  router.push(`/classroom/${classroomId.value}/student-grades`);
};
</script>

<style scoped>
.student-course-status-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.content-container {
  background: #fff;
  border-radius: 2px;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.classroom-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #fff;
  margin-right: 16px;
}

.status-ongoing {
  background-color: #1890ff;
}

.status-upcoming {
  background-color: #52c41a;
}

.status-past {
  background-color: #d9d9d9;
}

.classroom-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.student-info {
  margin-left: auto;
}

.info-card,
.courses-card {
  margin-bottom: 24px;
}

.classroom-info {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  color: rgba(0, 0, 0, 0.65);
}

.info-item :deep(svg) {
  margin-right: 8px;
  font-size: 16px;
  color: #1890ff;
}

.grades-button {
  margin-left: 16px;
}
</style> 
