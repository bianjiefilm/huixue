<template>
  <div class="learning-overview-tab">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 课堂基本信息 -->
      <div class="info-section">
        <a-card title="课堂基本信息" :bordered="false" class="info-card">
          <div class="info-grid">
            <div class="info-item">
              <span class="label">起止时间:</span>
              <span class="value">
                {{ overview?.classroom_info?.start_date }} 至 {{ overview?.classroom_info?.end_date }}
              </span>
            </div>
            <div class="info-item">
              <span class="label">实践课程总数:</span>
              <span class="value">{{ overview?.classroom_info?.practice_courses_total || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="label">已发布实践数:</span>
              <span class="value">{{ overview?.classroom_info?.practice_courses_published || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="label">实训项目总数:</span>
              <span class="value">{{ overview?.classroom_info?.training_courses_total || 0 }}</span>
            </div>
            <div class="info-item">
              <span class="label">已发布实训数:</span>
              <span class="value">{{ overview?.classroom_info?.training_courses_published || 0 }}</span>
            </div>
          </div>
        </a-card>
      </div>

      <!-- 图表区域 -->
      <div class="charts-section">
        <a-row :gutter="16">
          <!-- 课程完成情况饼图 -->
          <a-col :span="8">
            <a-card title="课程完成情况" :bordered="false">
              <div ref="completionChartRef" class="chart-container"></div>
            </a-card>
          </a-col>

          <!-- 学生在线情况统计 -->
          <a-col :span="8">
            <a-card title="学生在线情况" :bordered="false">
              <div ref="onlineChartRef" class="chart-container"></div>
            </a-card>
          </a-col>

          <!-- 学生平均成绩统计图 -->
          <a-col :span="8">
            <a-card title="学生平均成绩" :bordered="false">
              <div ref="scoreChartRef" class="chart-container"></div>
            </a-card>
          </a-col>
        </a-row>
      </div>

      <!-- 统计表格区域 -->
      <div class="tables-section">
        <a-row :gutter="16">
          <!-- 平均成绩排名 -->
          <a-col :span="12">
            <a-card title="平均成绩排名" :bordered="false">
              <a-table
                :columns="rankingColumns"
                :data-source="overview?.statistics?.top_students || []"
                :pagination="false"
                size="small"
              >
                <template #bodyCell="{ column, record, index }">
                  <template v-if="column.key === 'ranking'">
                    <a-tag :color="getRankingColor(index + 1)">
                      第{{ index + 1 }}名
                    </a-tag>
                  </template>
                  <template v-else-if="column.key === 'score'">
                    {{ record.average_score?.toFixed(1) || 0 }}分
                  </template>
                </template>
              </a-table>
            </a-card>
          </a-col>

          <!-- 学习时长统计 -->
          <a-col :span="12">
            <a-card title="学习时长统计" :bordered="false">
              <div ref="studyTimeChartRef" class="chart-container"></div>
            </a-card>
          </a-col>
        </a-row>
      </div>

      <!-- 课程平均成绩统计图 -->
      <div class="course-stats-section">
        <a-card title="课程平均成绩统计" :bordered="false">
          <div class="chart-controls">
            <a-radio-group v-model:value="chartType" button-style="solid">
              <a-radio-button value="chapter">按章节统计</a-radio-button>
              <a-radio-button value="course">按课程统计</a-radio-button>
            </a-radio-group>
          </div>
          <div ref="courseStatsChartRef" class="large-chart-container"></div>
        </a-card>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue';
import { message } from 'ant-design-vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import { getLearningOverview } from '../../api/analytics';
import type { LearningOverview } from '../../api/analytics';

// Props
interface Props {
  classroomId: number;
  teacherId: number;
  keyword?: string;
}

const props = defineProps<Props>();

// 状态管理
const loading = ref(false);
const overview = ref<LearningOverview | null>(null);
const chartType = ref<'chapter' | 'course'>('chapter');

// 图表引用
const completionChartRef = ref<HTMLElement>();
const onlineChartRef = ref<HTMLElement>();
const scoreChartRef = ref<HTMLElement>();
const studyTimeChartRef = ref<HTMLElement>();
const courseStatsChartRef = ref<HTMLElement>();

let completionChart: echarts.ECharts | null = null;
let onlineChart: echarts.ECharts | null = null;
let scoreChart: echarts.ECharts | null = null;
let studyTimeChart: echarts.ECharts | null = null;
let courseStatsChart: echarts.ECharts | null = null;

// 表格列定义
const rankingColumns = [
  {
    title: '排名',
    key: 'ranking',
    width: 80,
  },
  {
    title: '姓名',
    dataIndex: 'student_name',
    key: 'name',
  },
  {
    title: '平均成绩',
    key: 'score',
    width: 100,
  },
];

// 加载数据
async function loadOverviewData() {
  loading.value = true;
  try {
    const response = await getLearningOverview({
      classroom_id: props.classroomId,
      teacher_id: props.teacherId
    });

    if (response.code === '0000') {
      overview.value = response.data;
      
      // 初始化图表
      nextTick(() => {
        initCharts();
      });
    } else {
      message.error(response.message || '获取学情总览失败');
    }
  } catch (error) {
    console.error('获取学情总览失败:', error);
    message.error('获取学情总览失败');
  } finally {
    loading.value = false;
  }
}

// 初始化所有图表
function initCharts() {
  initCompletionChart();
  initOnlineChart();
  initScoreChart();
  initStudyTimeChart();
  initCourseStatsChart();
}

// 课程完成情况饼图
function initCompletionChart() {
  if (!completionChartRef.value || !overview.value) return;
  
  if (completionChart) {
    completionChart.dispose();
  }
  
  completionChart = echarts.init(completionChartRef.value);
  
  // 兼容两种API返回格式：course_completion_stats 或 course_completion
  const completion = overview.value.course_completion_stats || overview.value.course_completion || {
    completed: 0, learning: 0, makeup: 0, unpublished: 0
  };
  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '课程状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: completion.completed || 0, name: '已完成' },
          { value: completion.learning || 0, name: '学习中' },
          { value: completion.makeup || 0, name: '补交中' },
          { value: completion.unpublished || completion.not_published || 0, name: '未发布' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };
  
  completionChart.setOption(option);
}

// 学生在线情况环图
function initOnlineChart() {
  if (!onlineChartRef.value || !overview.value) return;
  
  if (onlineChart) {
    onlineChart.dispose();
  }
  
  onlineChart = echarts.init(onlineChartRef.value);
  
  // 兼容两种API返回格式：student_online_stats 或 online_status
  const onlineStatus = overview.value.student_online_stats || overview.value.online_status || {
    online_count: 0, offline_count: 0
  };
  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      bottom: '5%',
      left: 'center'
    },
    series: [
      {
        name: '在线状态',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        data: [
          { value: onlineStatus.online_count || 0, name: '在线' },
          { value: onlineStatus.offline_count || 0, name: '离线' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        itemStyle: {
          color: function(params: any) {
            const colors = ['#52c41a', '#d9d9d9'];
            return colors[params.dataIndex];
          }
        }
      }
    ]
  };
  
  onlineChart.setOption(option);
}

// 学生平均成绩柱状图
function initScoreChart() {
  if (!scoreChartRef.value || !overview.value) return;
  
  if (scoreChart) {
    scoreChart.dispose();
  }
  
  scoreChart = echarts.init(scoreChartRef.value);
  
  // 兼容两种API格式：top_students_ranking 或 statistics.top_students
  const topStudentsData = overview.value.top_students_ranking || 
    (overview.value.statistics && overview.value.statistics.top_students) || [];
  const topStudents = topStudentsData.slice(0, 10);
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: topStudents.map(s => s.student_name),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '分数'
    },
    series: [
      {
        name: '平均成绩',
        type: 'bar',
        data: topStudents.map(s => s.average_score),
        itemStyle: {
          color: '#1890ff'
        }
      }
    ]
  };
  
  scoreChart.setOption(option);
}

// 学习时长统计图
function initStudyTimeChart() {
  if (!studyTimeChartRef.value || !overview.value) return;
  
  if (studyTimeChart) {
    studyTimeChart.dispose();
  }
  
  studyTimeChart = echarts.init(studyTimeChartRef.value);
  
  // 兼容两种API格式：study_duration_stats 或 statistics.study_time_stats
  const studyTimeData = overview.value.study_duration_stats || 
    (overview.value.statistics && overview.value.statistics.study_time_stats) || [];
  const studyTimeStats = studyTimeData.slice(0, 10);
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: studyTimeStats.map(s => s.student_number),
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '小时'
    },
    series: [
      {
        name: '学习时长',
        type: 'bar',
        data: studyTimeStats.map(s => s.total_study_hours),
        itemStyle: {
          color: '#52c41a'
        }
      }
    ]
  };
  
  studyTimeChart.setOption(option);
}

// 课程平均成绩统计图
function initCourseStatsChart() {
  if (!courseStatsChartRef.value || !overview.value) return;
  
  if (courseStatsChart) {
    courseStatsChart.dispose();
  }
  
  courseStatsChart = echarts.init(courseStatsChartRef.value);
  
  // 兼容两种API格式：course_average_scores 或 statistics.course_avg_scores
  const rawCourseStats = overview.value.course_average_scores || 
    (overview.value.statistics && overview.value.statistics.course_avg_scores) || [];
  // 确保courseStats是数组
  const courseStats = Array.isArray(rawCourseStats) ? rawCourseStats : [];
  let data: any[] = [];
  let xAxisData: string[] = [];
  
  if (chartType.value === 'chapter') {
    // 按章节统计
    const chapterMap = new Map<string, { scores: number[], courseCount: number }>();
    
    courseStats.forEach((course: any) => {
      const chapter = course.chapter || '未分类';
      if (!chapterMap.has(chapter)) {
        chapterMap.set(chapter, { scores: [], courseCount: 0 });
      }
      chapterMap.get(chapter)!.scores.push(course.average_score);
      chapterMap.get(chapter)!.courseCount++;
    });
    
    chapterMap.forEach((value, chapter) => {
      const avgScore = value.scores.reduce((sum, score) => sum + score, 0) / value.scores.length;
      xAxisData.push(chapter);
      data.push(avgScore);
    });
  } else {
    // 按课程统计
    xAxisData = courseStats.map(course => course.course_name);
    data = courseStats.map(course => course.average_score);
  }
  
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      name: '平均分'
    },
    series: [
      {
        name: '平均成绩',
        type: 'line',
        data: data,
        smooth: true,
        itemStyle: {
          color: '#722ed1'
        },
        areaStyle: {
          color: 'rgba(114, 46, 209, 0.1)'
        }
      }
    ]
  };
  
  courseStatsChart.setOption(option);
}

// 获取排名颜色
function getRankingColor(rank: number): string {
  if (rank === 1) return 'gold';
  if (rank === 2) return 'orange';
  if (rank === 3) return 'green';
  return 'blue';
}

// 监听图表类型变化
watch(chartType, () => {
  initCourseStatsChart();
});

// 组件挂载时加载数据
onMounted(() => {
  loadOverviewData();
});

// 监听props变化
watch(() => [props.classroomId, props.teacherId], () => {
  loadOverviewData();
});

// 监听窗口大小变化
window.addEventListener('resize', () => {
  completionChart?.resize();
  onlineChart?.resize();
  scoreChart?.resize();
  studyTimeChart?.resize();
  courseStatsChart?.resize();
});
</script>

<style lang="less" scoped>
.learning-overview-tab {
  .info-section {
    margin-bottom: 16px;
    
    .info-card {
      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        
        .info-item {
          .label {
            color: #666;
            margin-right: 8px;
          }
          
          .value {
            font-weight: 500;
            color: #333;
          }
        }
      }
    }
  }
  
  .charts-section {
    margin-bottom: 16px;
    
    .chart-container {
      height: 300px;
      width: 100%;
    }
  }
  
  .tables-section {
    margin-bottom: 16px;
    
    .chart-container {
      height: 300px;
      width: 100%;
    }
  }
  
  .course-stats-section {
    .chart-controls {
      margin-bottom: 16px;
      text-align: center;
    }
    
    .large-chart-container {
      height: 400px;
      width: 100%;
    }
  }
}
</style>
