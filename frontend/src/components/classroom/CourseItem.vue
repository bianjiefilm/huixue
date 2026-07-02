<template>
  <div class="course-item" :class="{ 'is-student-view': studentView }">
    <div class="course-type-tag" :class="course.type">
      {{ course.type === 'practice' ? '实践' : '实训' }}
    </div>
    <div class="course-main">
      <div class="course-header">
        <h3 class="course-title" @click="handleCourseClick">
          {{ course.name }}
        </h3>
        <div class="course-status" :class="getStatusClass(studentStatus || course.status)">
          {{ getStatusText(studentStatus || course.status) }}
        </div>
      </div>
      
      <div class="course-info">
        <div class="course-detail">
          <div v-if="course.chapter" class="chapter-info">
            <book-outlined />
            <span>{{ course.chapter }}</span>
          </div>
          
          <div class="time-info">
            <clock-circle-outlined />
            <span v-if="course.status === 'unpublished'">
              创建时间：{{ formatDate(course.createTime) }}
            </span>
            <span v-else>
              {{ formatDate(course.startDate) }} 至 {{ formatDate(course.endDate) }}
            </span>
          </div>
          
          <div v-if="(course.status === 'learning' || course.status === 'makeup') && course.remainingTime" class="time-remaining">
            <hourglass-outlined />
            <span>剩余时间：{{ course.remainingTime }}</span>
          </div>
          
          <div v-if="course.type === 'training' && course.industry" class="industry-info">
            <shop-outlined />
            <span>{{ course.industry }}</span>
          </div>
          
          <div v-if="course.type === 'training' && course.trainingType" class="training-type">
            <experiment-outlined />
            <span>{{ course.trainingType }}</span>
          </div>
        </div>
        
        <div v-if="course.type === 'training' && (course.intro || course.introduction)" class="training-intro">
          {{ course.intro || course.introduction }}
        </div>
        
        <!-- 学生端特有信息 -->
        <div v-if="studentView" class="student-progress">
          <a-progress 
            :percent="getProgressPercent()" 
            :status="getProgressStatus()"
            size="small"
            :format="(percent: number) => `完成度: ${percent}%`"
          />
          <div class="completion-time" v-if="studentStatus === 'completed_ontime' || studentStatus === 'completed_late'">
            <check-circle-outlined :style="{ color: studentStatus === 'completed_ontime' ? '#52c41a' : '#faad14' }" />
            <span>{{ studentStatus === 'completed_ontime' ? '按时完成' : '补交完成' }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <div class="course-actions">
      <a-button 
        type="primary" 
        size="small"
        :disabled="classroom.status === 'past' && studentStatus !== 'completed_ontime' && studentStatus !== 'completed_late'"
        @click="handleCourseClick"
      >
        {{ getActionButtonText() }}
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { 
  BookOutlined, ClockCircleOutlined, ShopOutlined, 
  ExperimentOutlined, CheckCircleOutlined, HourglassOutlined 
} from '@ant-design/icons-vue';
import type { CourseItem, ClassroomDetail, CourseStatus } from '@/types/classroom';
import { useUserStore } from '../../stores/user';
import dayjs from 'dayjs';

// 定义组件属性
const props = defineProps({
  course: {
    type: Object as () => CourseItem,
    required: true
  },
  classroom: {
    type: Object as () => ClassroomDetail,
    required: true
  },
  studentView: {
    type: Boolean,
    default: false
  }
});

const router = useRouter();
const userStore = useUserStore();

// 学生课程状态
const studentStatus = computed(() => {
  if (!props.studentView) return null;
  return getStudentCourseStatus(props.course.id, userStore.userInfo.id || '');
});

// 获取课程状态文本
const getStatusText = (status: string) => {
  // 教师端状态
  if (!props.studentView) {
    switch (status) {
      case 'unpublished': return '未发布';
      case 'learning': return '学习中';
      case 'makeup': return '补交中';
      case 'completed': return '已完成';
      case 'ended': return '已结束';
      default: return '未知状态';
    }
  }
  
  // 学生端状态
  switch (status) {
    case 'not_started': return '未开始';
    case 'learning': return '学习中';
    case 'makeup': return '待补交';
    case 'completed_ontime': return '已完成';
    case 'completed_late': return '已完成';
    case 'ended': return '已结束';
    default: return '未知状态';
  }
};

// 获取状态类名
const getStatusClass = (status: string) => {
  // 教师端状态类名
  if (!props.studentView) {
    switch (status) {
      case 'unpublished': return 'status-unpublished';
      case 'learning': return 'status-learning';
      case 'makeup': return 'status-makeup';
      case 'completed': return 'status-completed';
      case 'ended': return 'status-ended';
      default: return '';
    }
  }
  
  // 学生端状态类名
  switch (status) {
    case 'not_started': return 'status-not-started';
    case 'learning': return 'status-learning';
    case 'makeup': return 'status-makeup';
    case 'completed_ontime': return 'status-completed-ontime';
    case 'completed_late': return 'status-completed-late';
    case 'ended': return 'status-ended';
    default: return '';
  }
};

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 获取操作按钮文本
const getActionButtonText = () => {
  if (props.classroom.status === 'past') {
    return '查看详情';
  }
  
  if (props.studentView) {
    const status = studentStatus.value;
    if (status === 'not_started') return '开始学习';
    if (status === 'learning') return '继续学习';
    if (status === 'makeup') return '补交作业';
    if (status === 'completed_ontime' || status === 'completed_late') return '查看详情';
    return '查看详情';
  }
  
  return '查看详情';
};

// 处理课程点击
const handleCourseClick = () => {
  // 根据课程类型和学生状态跳转到不同页面
  const courseType = props.course.type;
  const courseId = props.course.id;
  
  if (courseType === 'practice') {
    router.push(`/course/practice/${courseId}`);
  } else {
    router.push(`/course/training/${courseId}`);
  }
};

// 计算学生进度百分比
const getProgressPercent = () => {
  if (!props.studentView) return 0;
  
  const progress = getStudentCourseProgress(props.course.id, userStore.userInfo.id || '');
  return progress;
};

// 获取进度状态
const getProgressStatus = () => {
  if (!props.studentView) return 'normal';
  
  const status = studentStatus.value;
  if (status === 'completed_ontime') return 'success';
  if (status === 'completed_late') return 'success';
  if (status === 'makeup') return 'warning';
  if (props.classroom.status === 'past') return 'exception';
  return 'active';
};
</script>

<style scoped>
.course-item {
  display: flex;
  width: 100%;
  padding: 16px;
  border-radius: 4px;
  background-color: #f9f9f9;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.course-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.course-type-tag {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  font-weight: bold;
  margin-right: 16px;
}

.course-type-tag.practice {
  background-color: #1890ff;
}

.course-type-tag.training {
  background-color: #722ed1;
}

.course-main {
  flex: 1;
}

.course-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.course-title {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  margin-right: 12px;
  cursor: pointer;
  transition: color 0.3s;
}

.course-title:hover {
  color: #1890ff;
}

.course-status {
  padding: 2px 8px;
  border-radius: 2px;
  font-size: 12px;
  color: #fff;
}

.status-unpublished,
.status-not-started {
  background-color: #d9d9d9;
}

.status-learning {
  background-color: #1890ff;
}

.status-makeup {
  background-color: #faad14;
}

.status-completed,
.status-completed-ontime {
  background-color: #52c41a;
}

.status-completed-late {
  background-color: #13c2c2;
}

.status-ended {
  background-color: #8c8c8c;
}

.course-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

.chapter-info,
.time-info,
.time-remaining,
.industry-info,
.training-type {
  display: flex;
  align-items: center;
}

.time-remaining {
  color: #faad14;
}

.course-detail :deep(svg) {
  margin-right: 8px;
  font-size: 14px;
}

.training-intro {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
  line-height: 1.5;
}

.student-progress {
  margin-top: 12px;
}

.completion-time {
  margin-top: 8px;
  display: flex;
  align-items: center;
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

.completion-time :deep(svg) {
  margin-right: 8px;
  font-size: 14px;
}

.course-actions {
  margin-left: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
</style> 