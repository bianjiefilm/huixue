<template>
  <div class="student-grades-page">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 返回按钮 -->
      <div class="back-link">
        <router-link :to="`/classroom/${classroomId}/student-status`">
          <a-button type="link">
            <template #icon><arrow-left-outlined /></template>
            返回学情分析
          </a-button>
        </router-link>
      </div>

      <!-- 页面标题 -->
      <div class="page-header">
        <h1>个人成绩单</h1>
      </div>

      <!-- 学生基本信息卡片 -->
      <a-card class="student-info-card" v-if="studentGrades">
        <div class="student-info-header">
          <div class="student-avatar">
            <a-avatar 
              :size="80" 
              :src="studentGrades.avatar_url" 
              :alt="studentGrades.student_name"
              class="avatar"
            >{{ studentGrades.student_name.charAt(0) }}</a-avatar>
          </div>
          <div class="student-basic-info">
            <h2 class="student-name">{{ studentGrades.student_name }}</h2>
            <div class="student-details">
              <p><user-outlined /> 学号：{{ studentGrades.student_number }}</p>
              <p v-if="studentGrades.class_name"><team-outlined /> 班级：{{ studentGrades.class_name }}</p>
            </div>
          </div>
        </div>
      </a-card>

      <!-- 学习数据统计 -->
      <a-card class="stats-card" v-if="studentGrades">
        <a-row :gutter="16">
          <a-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon score-icon">
                <crown-outlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ studentGrades.statistics.average_score.toFixed(1) }}</div>
                <div class="stat-label">
                  课程平均分
                  <a-tooltip title="必修课程总分/必修课程总数，包括实践类和实训类">
                    <question-circle-outlined class="help-icon" />
                  </a-tooltip>
                </div>
                <div class="stat-extra">排名：第{{ studentGrades.statistics.ranking }}名</div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon time-icon">
                <clock-circle-outlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatStudyTime(studentGrades.statistics.total_study_hours * 60) }}</div>
                <div class="stat-label">
                  总学习时长
                  <a-tooltip title="该学生各课程的学习时长总和">
                    <question-circle-outlined class="help-icon" />
                  </a-tooltip>
                </div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon course-icon">
                <book-outlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ studentGrades.statistics.completed_courses }}/{{ studentGrades.statistics.total_courses }}</div>
                <div class="stat-label">
                  完成课程数
                  <a-tooltip title="已完成的课程数/总课程数">
                    <question-circle-outlined class="help-icon" />
                  </a-tooltip>
                </div>
                <div class="stat-extra">完成率：{{ getCompletionRate() }}%</div>
              </div>
            </div>
          </a-col>
          <a-col :xs="24" :sm="12" :md="6">
            <div class="stat-item">
              <div class="stat-icon work-icon">
                <trophy-outlined />
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ studentGrades.statistics.excellent_assignments }}</div>
                <div class="stat-label">
                  优秀作业数
                  <a-tooltip title="该学生的实训作业被评为优秀作业的数量">
                    <question-circle-outlined class="help-icon" />
                  </a-tooltip>
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </a-card>

      <!-- 课程成绩列表 -->
      <a-card class="courses-card" v-if="studentGrades">
        <a-tabs v-model:activeKey="activeTabKey">
          <a-tab-pane key="practice" tab="实践课程">
            <div class="course-list">
              <div class="course-list-header">
                <div class="course-name">课程名称</div>
                <div class="course-progress">关卡完成进度</div>
                <div class="course-time">学习时长</div>
                <div class="course-complete-time">完成时间</div>
                <div class="course-score">课程得分</div>
              </div>

              <div v-if="practiceCourses.length === 0" class="empty-courses">
                <a-empty description="暂无实践课程数据" />
              </div>

              <div v-else class="course-list-body">
                <div 
                  v-for="course in practiceCourses" 
                  :key="course.course_id" 
                  class="course-item"
                  :class="{ 'course-required': course.is_required }"
                >
                  <div class="course-name">
                    <span v-if="course.is_required" class="required-tag">必修</span>
                    {{ course.course_name }}
                  </div>
                  <div class="course-progress">
                    <a-progress 
                      :percent="course.level_progress || 0" 
                      :status="(course.level_progress || 0) === 100 ? 'success' : 'active'"
                      size="small"
                    />
                  </div>
                  <div class="course-time">{{ formatStudyTime(course.study_time_minutes) }}</div>
                  <div class="course-complete-time">{{ formatDateTime(course.complete_time) }}</div>
                  <div class="course-score">
                    <span :class="getScoreClass(course.score)">{{ course.score }}</span>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>

          <a-tab-pane key="training" tab="实训课程">
            <div class="course-list">
              <div class="course-list-header">
                <div class="course-name">课程名称</div>
                <div class="course-submission">提交作业数</div>
                <div class="course-time">学习时长</div>
                <div class="course-complete-time">完成时间</div>
                <div class="course-score">课程得分</div>
              </div>

              <div v-if="trainingCourses.length === 0" class="empty-courses">
                <a-empty description="暂无实训课程数据" />
              </div>

              <div v-else class="course-list-body">
                <div 
                  v-for="course in trainingCourses" 
                  :key="course.course_id" 
                  class="course-item"
                  :class="{ 'course-required': course.is_required }"
                >
                  <div class="course-name">
                    <span v-if="course.is_required" class="required-tag">必修</span>
                    {{ course.course_name }}
                    <span v-if="course.is_excellent" class="excellent-tag">优秀</span>
                  </div>
                  <div class="course-submission">{{ course.submitted_work_count || 0 }}</div>
                  <div class="course-time">{{ formatStudyTime(course.study_time_minutes) }}</div>
                  <div class="course-complete-time">{{ formatDateTime(course.complete_time) }}</div>
                  <div class="course-score">
                    <span :class="getScoreClass(course.score)">{{ course.score }}</span>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>

      <a-result v-if="!studentGrades && !loading" status="warning" title="未找到成绩单" sub-title="无法获取该学生的成绩单信息">
        <template #extra>
          <router-link :to="`/classroom/${classroomId}/student-status`">
            <a-button type="primary">返回学情分析</a-button>
          </router-link>
        </template>
      </a-result>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  ArrowLeftOutlined, 
  UserOutlined, 
  TeamOutlined, 
  BookOutlined,
  ClockCircleOutlined,
  CrownOutlined,
  TrophyOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import { 
  getStudentGrades,
  getStudentTranscript,
  type StudentTranscript
} from '../../api/grades';
import dayjs from 'dayjs';

// 路由相关
const route = useRoute();
const userStore = useUserStore();
const classroomId = computed(() => route.params.id as string);
const studentId = computed(() => {
  const routeStudentId = route.params.studentId as string;
  return routeStudentId ? parseInt(routeStudentId) : (userStore.userInfo.id || 0);
});

// 状态管理
const loading = ref(false);
const studentGrades = ref<StudentTranscript | undefined>(undefined);
const activeTabKey = ref('practice');

// 过滤课程列表
const practiceCourses = computed(() => {
  if (!studentGrades.value) return [];
  return studentGrades.value.courses.filter(course => course.course_type === 'PRACTICE');
});

const trainingCourses = computed(() => {
  if (!studentGrades.value) return [];
  return studentGrades.value.courses.filter(course => course.course_type === 'TRAINING');
});

// 计算完成率
const getCompletionRate = () => {
  if (!studentGrades.value) return 0;
  const { completed_courses, total_courses } = studentGrades.value.statistics;
  return Math.round((completed_courses / total_courses) * 100);
};

// 获取分数样式
const getScoreClass = (score: number) => {
  if (score >= 90) return 'score-excellent';
  if (score >= 80) return 'score-good';
  if (score >= 60) return 'score-pass';
  return 'score-fail';
};

// 格式化学习时间
const formatStudyTime = (minutes: number) => {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
};

// 格式化日期时间
const formatDateTime = (dateTime?: string | null) => {
  if (!dateTime) return '未完成';
  return dayjs(dateTime).format('YYYY-MM-DD HH:mm');
};

// 加载学生成绩单数据 (使用新的 P3 API)
const loadStudentGrades = async () => {
  loading.value = true;
  try {
    // 先尝试使用新的 P3 API
    const res = await getStudentGrades({
      classroom_id: parseInt(classroomId.value),
      student_id: studentId.value
    });
    
    if (res.code === '0000') {
      // 转换新的 API 响应格式为旧格式（兼容现有 UI）
      const data = res.data;
      studentGrades.value = {
        student_id: studentId.value,
        student_name: data.student_name || '学生',
        student_number: data.student_number || '',
        avatar_url: data.avatar_url || null,
        statistics: {
          average_score: data.class_average || 0,
          ranking: data.student_rank || 0,
          total_study_hours: 0,
          completed_courses: data.courses?.filter((c: any) => c.status === 'graded').length || 0,
          total_courses: data.courses?.length || 0,
          excellent_assignments: data.courses?.filter((c: any) => c.is_excellent).length || 0
        },
        courses: (data.courses || []).map((c: any) => ({
          course_id: c.course_id || 0,
          course_name: c.course_name || '',
          course_type: c.course_type || 'PRACTICE',
          is_required: c.is_required || false,
          score: c.overall_score || 0,
          status: c.status || 'not_started',
          level_progress: 0,
          study_time_minutes: 0,
          complete_time: c.graded_at || null,
          submitted_work_count: 0,
          is_excellent: c.is_excellent || false
        }))
      } as StudentTranscript;
    } else {
      // 如果新 API 失败，尝试使用旧 API
      const fallbackRes = await getStudentTranscript({
        classroom_id: parseInt(classroomId.value),
        student_id: studentId.value
      });
      
      if (fallbackRes.code === '0000') {
        studentGrades.value = fallbackRes.data;
      } else {
        message.error(fallbackRes.message || '获取学生成绩单失败');
      }
    }
  } catch (error) {
    console.error('获取学生成绩单失败:', error);
    message.error('获取学生成绩单失败');
  } finally {
    loading.value = false;
  }
};

// 生命周期钩子
onMounted(() => {
  loadStudentGrades();
});
</script>

<style scoped>
.student-grades-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #1f1f1f;
}

.student-info-card,
.stats-card,
.courses-card {
  margin-bottom: 24px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.student-info-header {
  display: flex;
  align-items: center;
}

.student-avatar {
  margin-right: 24px;
}

.avatar {
  background-color: #1890ff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.student-basic-info .student-name {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.student-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.student-details p {
  margin: 0;
  color: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
}

.student-details :deep(svg) {
  margin-right: 8px;
  font-size: 16px;
  color: #1890ff;
}

/* 统计卡片样式 */
.stats-card :deep(.ant-card-body) {
  padding: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  height: 100%;
  transition: all 0.3s ease;
}

.stat-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
  transform: translateY(-2px);
}

.stat-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  margin-right: 16px;
  font-size: 24px;
  color: #fff;
}

.score-icon {
  background-color: #1890ff;
}

.time-icon {
  background-color: #13c2c2;
}

.course-icon {
  background-color: #52c41a;
}

.work-icon {
  background-color: #722ed1;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #1f1f1f;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  margin-top: 4px;
  display: flex;
  align-items: center;
}

.help-icon {
  font-size: 14px;
  margin-left: 4px;
  color: rgba(0, 0, 0, 0.45);
  cursor: pointer;
}

.stat-extra {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

/* 课程列表样式 */
.course-list {
  margin-top: 16px;
}

.course-list-header {
  display: flex;
  background-color: #f5f5f5;
  padding: 12px 16px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  border-radius: 4px 4px 0 0;
}

.course-list-body {
  border: 1px solid #f0f0f0;
  border-radius: 0 0 4px 4px;
}

.course-item {
  display: flex;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.course-item:last-child {
  border-bottom: none;
}

.course-item:hover {
  background-color: #f5f5f5;
}

.course-required {
  background-color: #fafafa;
}

.course-name {
  flex: 2;
  display: flex;
  align-items: center;
}

.course-progress,
.course-submission {
  flex: 1.5;
  padding: 0 8px;
}

.course-time {
  flex: 1;
  padding: 0 8px;
}

.course-complete-time {
  flex: 1.5;
  padding: 0 8px;
}

.course-score {
  flex: 0.5;
  text-align: center;
  font-weight: 600;
}

.required-tag {
  display: inline-block;
  padding: 0 6px;
  font-size: 12px;
  line-height: 20px;
  background: #1890ff;
  color: #fff;
  border-radius: 2px;
  margin-right: 8px;
}

.excellent-tag {
  display: inline-block;
  padding: 0 6px;
  font-size: 12px;
  line-height: 20px;
  background: #52c41a;
  color: #fff;
  border-radius: 2px;
  margin-left: 8px;
}

.score-excellent {
  color: #52c41a;
}

.score-good {
  color: #1890ff;
}

.score-pass {
  color: #faad14;
}

.score-fail {
  color: #ff4d4f;
}

.empty-courses {
  padding: 32px 0;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 0 0 4px 4px;
}

@media (max-width: 768px) {
  .student-info-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .student-avatar {
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .student-details {
    justify-content: center;
  }
  
  .course-list-header,
  .course-item {
    font-size: 12px;
  }
  
  .course-progress,
  .course-submission {
    flex: 1;
  }
}
</style> 