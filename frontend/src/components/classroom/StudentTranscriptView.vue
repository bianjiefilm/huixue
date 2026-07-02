<template>
  <div class="student-transcript-view">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 学生基本信息 -->
      <div class="student-info-section" v-if="transcript">
        <div class="info-header">
          <a-avatar :size="80" :src="transcript.student_info?.avatar_url">
            {{ transcript.student_info?.student_name?.charAt(0) }}
          </a-avatar>
          <div class="info-content">
            <h2>{{ transcript.student_info?.student_name }}</h2>
            <p>学号: {{ transcript.student_info?.student_number }}</p>
            <p v-if="transcript.student_info?.class_name">班级: {{ transcript.student_info?.class_name }}</p>
            <p v-if="transcript.student_info?.grade">年级: {{ transcript.student_info?.grade }}</p>
          </div>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="statistics-section" v-if="transcript && transcript.overall_stats">
        <a-row :gutter="16">
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="课程平均分"
                :value="transcript.overall_stats.course_average_score || 0"
                :precision="1"
                suffix="分"
                :value-style="{ color: getScoreColor(transcript.overall_stats.course_average_score) }"
              />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="成绩排名"
                :value="transcript.overall_stats.score_ranking || 0"
                suffix="名"
                :value-style="{ color: getRankingColor(transcript.overall_stats.score_ranking || 0) }"
              />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="总学习时长"
                :value="transcript.overall_stats.total_study_hours || 0"
                :precision="1"
                suffix="小时"
              />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="完成课程数"
                :value="transcript.overall_stats.completed_courses || '0/0'"
              />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="完成率"
                :value="calculateCompletionRate(transcript.overall_stats.completed_courses)"
                suffix="%"
              />
            </a-card>
          </a-col>
          <a-col :span="4">
            <a-card size="small">
              <a-statistic
                title="优秀作业数"
                :value="transcript.overall_stats.excellent_assignments || 0"
                suffix="个"
                :value-style="{ color: '#52c41a' }"
              />
            </a-card>
          </a-col>
        </a-row>
      </div>

      <!-- 课程列表 -->
      <div class="courses-section" v-if="transcript">
        <h3>课程详情</h3>
        
        <!-- 筛选器 -->
        <div class="filters">
          <a-space>
            <a-select 
              v-model:value="courseTypeFilter" 
              style="width: 120px"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="PRACTICE">实践课程</a-select-option>
              <a-select-option value="TRAINING">实训课程</a-select-option>
            </a-select>
            
            <a-select 
              v-model:value="requiredFilter" 
              style="width: 120px"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="required">必修</a-select-option>
              <a-select-option value="optional">拓展</a-select-option>
            </a-select>
            
            <a-select 
              v-model:value="statusFilter" 
              style="width: 120px"
              @change="handleFilterChange"
            >
              <a-select-option value="all">全部状态</a-select-option>
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="learning">学习中</a-select-option>
              <a-select-option value="not_started">未开始</a-select-option>
            </a-select>
          </a-space>
        </div>

        <!-- 课程表格 -->
        <a-table
          :columns="courseColumns"
          :data-source="filteredCourses"
          :pagination="false"
          size="small"
          :scroll="{ x: 1200 }"
        >
          <template #bodyCell="{ column, record }">
            <!-- 课程类型 -->
            <template v-if="column.key === 'course_type'">
              <a-tag :color="record.course_type === 'PRACTICE' ? 'blue' : 'green'">
                {{ record.course_type === 'PRACTICE' ? '实践课程' : '实训课程' }}
              </a-tag>
            </template>
            
            <!-- 是否必修 -->
            <template v-else-if="column.key === 'is_required'">
              <a-tag :color="record.is_required ? 'orange' : 'purple'">
                {{ record.is_required ? '必修' : '拓展' }}
              </a-tag>
            </template>
            
            <!-- 课程状态 -->
            <template v-else-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            
            <!-- 关卡进度 -->
            <template v-else-if="column.key === 'level_progress'">
              <span v-if="record.course_type === 'PRACTICE'">
                {{ record.level_progress || 0 }}%
              </span>
              <span v-else>-</span>
            </template>
            
            <!-- 学习时长 -->
            <template v-else-if="column.key === 'study_time'">
              {{ formatMinutesToHours(record.study_time_minutes) }}
            </template>
            
            <!-- 完成时间 -->
            <template v-else-if="column.key === 'complete_time'">
              {{ record.complete_time ? formatDateTime(record.complete_time) : '-' }}
            </template>
            
            <!-- 课程得分 -->
            <template v-else-if="column.key === 'course_score'">
              <a-tag :color="getScoreColor(record.course_score)">
                {{ record.course_score?.toFixed(1) || 0 }}分
              </a-tag>
            </template>
            
            <!-- 提交作业数量 -->
            <template v-else-if="column.key === 'submitted_work'">
              <span v-if="record.course_type === 'TRAINING'">
                {{ record.submitted_work_count || 0 }}
              </span>
              <span v-else>-</span>
            </template>
            
            <!-- 是否优秀 -->
            <template v-else-if="column.key === 'is_excellent'">
              <a-tag v-if="record.is_excellent" color="gold">
                优秀作业
              </a-tag>
              <span v-else>-</span>
            </template>
          </template>
        </a-table>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { getStudentTranscript } from '../../api/analytics';
import type { StudentTranscript } from '../../api/analytics';

// Props
interface Props {
  classroomId: number;
  studentId: number;
  teacherId: number;
}

const props = defineProps<Props>();

// 状态管理
const loading = ref(false);
const transcript = ref<StudentTranscript | null>(null);

// 筛选器
const courseTypeFilter = ref('all');
const requiredFilter = ref('all');
const statusFilter = ref('all');

// 表格列定义
const courseColumns = [
  {
    title: '课程名称',
    dataIndex: 'course_name',
    key: 'name',
    width: 200,
    fixed: 'left' as const,
  },
  {
    title: '课程类型',
    key: 'course_type',
    width: 100,
  },
  {
    title: '课程属性',
    key: 'is_required',
    width: 100,
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
  },
  {
    title: '关卡完成进度',
    key: 'level_progress',
    width: 120,
  },
  {
    title: '学习时长',
    key: 'study_time',
    width: 100,
  },
  {
    title: '完成时间',
    key: 'complete_time',
    width: 150,
  },
  {
    title: '课程得分',
    key: 'course_score',
    width: 100,
  },
  {
    title: '提交作业数',
    key: 'submitted_work',
    width: 100,
  },
  {
    title: '优秀作业',
    key: 'is_excellent',
    width: 100,
  },
];

// 计算属性
const filteredCourses = computed(() => {
  if (!transcript.value) return [];
  
  return transcript.value.courses.filter(course => {
    // 课程类型筛选
    if (courseTypeFilter.value !== 'all' && course.course_type !== courseTypeFilter.value) {
      return false;
    }
    
    // 必修/拓展筛选
    if (requiredFilter.value !== 'all') {
      if (requiredFilter.value === 'required' && !course.is_required) return false;
      if (requiredFilter.value === 'optional' && course.is_required) return false;
    }
    
    // 状态筛选
    if (statusFilter.value !== 'all' && course.status !== statusFilter.value) {
      return false;
    }
    
    return true;
  });
});

// 加载学生成绩单数据
async function loadTranscriptData() {
  loading.value = true;
  try {
    const response = await getStudentTranscript({
      classroom_id: props.classroomId,
      student_id: props.studentId,
      teacher_id: props.teacherId
    });

    if (response.code === '0000') {
      transcript.value = response.data;
    } else {
      message.error(response.message || '获取学生成绩单失败');
    }
  } catch (error) {
    console.error('获取学生成绩单失败:', error);
    message.error('获取学生成绩单失败');
  } finally {
    loading.value = false;
  }
}

// 筛选器变化处理
function handleFilterChange() {
  // 筛选逻辑已通过计算属性实现
}

// 辅助函数
function getScoreColor(score?: number): string {
  if (!score) return '#d9d9d9';
  if (score >= 90) return '#52c41a';
  if (score >= 80) return '#1890ff';
  if (score >= 70) return '#fa8c16';
  if (score >= 60) return '#faad14';
  return '#f5222d';
}

function getRankingColor(ranking: number): string {
  if (ranking <= 3) return '#52c41a';
  if (ranking <= 10) return '#1890ff';
  return '#666';
}

function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    'completed': 'green',
    'learning': 'blue',
    'not_started': 'default',
    'makeup': 'orange'
  };
  return colorMap[status] || 'default';
}

function getStatusText(status: string): string {
  const textMap: Record<string, string> = {
    'completed': '已完成',
    'learning': '学习中',
    'not_started': '未开始',
    'makeup': '补交中'
  };
  return textMap[status] || status;
}

function formatMinutesToHours(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}分钟`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 
    ? `${hours}小时${remainingMinutes}分钟` 
    : `${hours}小时`;
}

function formatDateTime(dateTime: string): string {
  return new Date(dateTime).toLocaleString('zh-CN');
}

function calculateCompletionRate(completedCoursesStr: string): number {
  if (!completedCoursesStr) return 0;
  const parts = completedCoursesStr.split('/');
  if (parts.length !== 2) return 0;
  const completed = parseInt(parts[0]) || 0;
  const total = parseInt(parts[1]) || 0;
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
}

// 组件挂载时加载数据
onMounted(() => {
  loadTranscriptData();
});

// 监听props变化
watch(() => [props.classroomId, props.studentId, props.teacherId], () => {
  loadTranscriptData();
});
</script>

<style lang="less" scoped>
.student-transcript-view {
  .student-info-section {
    margin-bottom: 24px;
    
    .info-header {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 16px;
      background: #f5f5f5;
      border-radius: 8px;
      
      .info-content {
        h2 {
          margin: 0 0 8px 0;
          color: #333;
        }
        
        p {
          margin: 4px 0;
          color: #666;
          font-size: 14px;
        }
      }
    }
  }
  
  .statistics-section {
    margin-bottom: 24px;
  }
  
  .courses-section {
    h3 {
      margin-bottom: 16px;
      color: #333;
    }
    
    .filters {
      margin-bottom: 16px;
    }
    
    :deep(.ant-table-wrapper) {
      .ant-table-thead > tr > th {
        background: #fafafa;
        font-weight: 600;
      }
      
      .ant-table-tbody > tr:hover > td {
        background: #f5f5f5;
      }
    }
  }
}
</style>