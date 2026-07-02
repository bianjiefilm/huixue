<template>
  <div class="exam-statistics-page">
    <!-- 顶部信息栏 -->
    <div class="page-header">
      <div class="header-left">
        <a-button type="text" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回
        </a-button>
        <h1>{{ examInfo?.title || '考试详情' }}</h1>
        <a-tag :color="getStatusColor(examInfo?.status)">
          {{ getStatusText(examInfo?.status) }}
        </a-tag>
      </div>
      <div class="header-stats">
        <a-statistic title="及格分/总分" :value="`${examInfo?.pass_mark || 60}/${totalScore}`" />
        <a-divider type="vertical" />
        <a-statistic title="最高分" :value="stats.maxScore" />
        <a-divider type="vertical" />
        <a-statistic title="最低分" :value="stats.minScore" />
        <a-divider type="vertical" />
        <a-statistic title="平均分" :value="stats.avgScore" :precision="1" />
      </div>
    </div>

    <!-- Tab导航 -->
    <a-tabs v-model:activeKey="activeTab" class="main-tabs">
      <!-- 成绩统计Tab -->
      <a-tab-pane key="grades" tab="成绩统计">
        <div class="tab-content">
          <div class="toolbar">
            <a-button type="primary" @click="exportGrades">
              <template #icon><download-outlined /></template>
              导出成绩
            </a-button>
          </div>

          <a-table
            :columns="gradeColumns"
            :data-source="studentGrades"
            :loading="loading"
            :pagination="{ pageSize: 20 }"
            row-key="student_id"
            @change="handleTableChange"
          >
            <template #bodyCell="{ column, record, index }">
              <template v-if="column.key === 'rank'">
                <span class="rank" :class="getRankClass(index + 1)">{{ index + 1 }}</span>
              </template>
              <template v-else-if="column.key === 'student'">
                <div class="student-info">
                  <span class="name">{{ record.student_name }}</span>
                  <span class="id">{{ record.student_number }}</span>
                </div>
              </template>
              <template v-else-if="column.key === 'submit_time'">
                {{ formatDateTime(record.submit_time) }}
              </template>
              <template v-else-if="column.key === 'duration'">
                {{ formatDuration(record.duration_seconds) }}
              </template>
              <template v-else-if="column.key === 'objective_score'">
                {{ record.objective_score || 0 }}分
              </template>
              <template v-else-if="column.key === 'subjective_score'">
                {{ record.subjective_score || 0 }}分
              </template>
              <template v-else-if="column.key === 'total_score'">
                <span class="score" :class="record.score >= (examInfo?.pass_mark || 60) ? 'pass' : 'fail'">
                  {{ record.score || 0 }}分
                </span>
              </template>
              <template v-else-if="column.key === 'action'">
                <a-button type="link" size="small" @click="viewPaper(record)">
                  查看试卷
                </a-button>
              </template>
            </template>
          </a-table>
        </div>
      </a-tab-pane>

      <!-- 成绩分布Tab -->
      <a-tab-pane key="distribution" tab="成绩分布">
        <div class="tab-content">
          <div class="toolbar">
            <a-button @click="showSegmentSettings = true">
              <template #icon><setting-outlined /></template>
              分数段设置
            </a-button>
          </div>

          <div class="charts-container">
            <div class="chart-wrapper">
              <h3>成绩分布柱状图</h3>
              <div ref="barChartRef" class="chart"></div>
            </div>
            <div class="chart-wrapper">
              <h3>成绩占比饼状图</h3>
              <div ref="pieChartRef" class="chart"></div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- 试题分析Tab -->
      <a-tab-pane key="analysis" tab="试题分析">
        <div class="tab-content">
          <div class="question-analysis-list">
            <div
              v-for="(question, index) in questionAnalysis"
              :key="question.id"
              class="question-item"
            >
              <div class="question-header" @click="toggleQuestion(index)">
                <div class="question-info">
                  <span class="question-num">第{{ question.question_number || index + 1 }}题</span>
                  <a-tag>{{ question.question_type_cn || getQuestionTypeText(question.question_type) }}</a-tag>
                  <span class="question-preview">{{ (question.question_content || question.content)?.substring(0, 50) }}...</span>
                </div>
                <div class="question-stats">
                  <span class="stat correct">
                    <check-circle-outlined /> 正确率: {{ (question.correct_rate || 0).toFixed(1) }}%
                  </span>
                  <span class="stat rate">
                    平均分: {{ (question.average_score || 0).toFixed(1) }}/{{ question.score || 0 }}
                  </span>
                  <span class="stat difficulty" :class="getDifficultyClassByLevel(question.difficulty_level)">
                    难度: {{ getDifficultyTextByLevel(question.difficulty_level) }}
                  </span>
                  <right-outlined :class="{ 'expanded': expandedQuestions.includes(index) }" />
                </div>
              </div>

              <div v-if="expandedQuestions.includes(index)" class="question-detail">
                <div v-if="['SINGLE_CHOICE', 'MULTIPLE_CHOICE'].includes(question.question_type)" class="option-distribution">
                  <div
                    v-for="(option, optIdx) in (question.option_statistics || [])"
                    :key="optIdx"
                    class="option-bar"
                    :class="{ correct: option.is_correct }"
                  >
                    <span class="option-label">{{ option.option_label || String.fromCharCode(65 + optIdx) }}</span>
                    <div class="bar-wrapper">
                      <div class="bar" :style="{ width: `${option.percentage || 0}%` }"></div>
                    </div>
                    <span class="option-count">{{ option.count || 0 }}人 ({{ (option.percentage || 0).toFixed(1) }}%)</span>
                    <check-outlined v-if="option.is_correct" class="correct-icon" />
                  </div>
                  <div v-if="!question.option_statistics?.length" class="no-data">暂无选项统计数据</div>
                </div>
                <div v-else class="subjective-stats">
                  <p>平均得分: {{ (question.average_score || 0).toFixed(1) }} / {{ question.score || 0 }}分</p>
                  <p>正确率: {{ (question.correct_rate || 0).toFixed(1) }}%</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 分数段设置弹窗 -->
    <a-modal
      v-model:open="showSegmentSettings"
      title="分数段设置"
      width="600px"
      @ok="saveSegmentSettings"
    >
      <a-form layout="vertical">
        <a-form-item label="开启自定义评价">
          <a-switch v-model:checked="segmentConfig.enableCustomLabel" />
        </a-form-item>

        <a-form-item label="分段数量">
          <a-select v-model:value="segmentConfig.count" @change="updateSegments">
            <a-select-option :value="2">2段</a-select-option>
            <a-select-option :value="3">3段</a-select-option>
            <a-select-option :value="4">4段</a-select-option>
            <a-select-option :value="5">5段</a-select-option>
            <a-select-option :value="6">6段</a-select-option>
          </a-select>
        </a-form-item>

        <div class="segment-list">
          <div v-for="(seg, idx) in segmentConfig.segments" :key="idx" class="segment-row">
            <a-input-number
              v-model:value="seg.min"
              :min="0"
              :max="totalScore"
              :disabled="idx === 0"
            />
            <span>-</span>
            <a-input-number
              v-model:value="seg.max"
              :min="0"
              :max="totalScore"
            />
            <a-input
              v-if="segmentConfig.enableCustomLabel"
              v-model:value="seg.label"
              placeholder="评价名称"
              style="width: 120px"
            />
          </div>
        </div>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RightOutlined,
  CheckOutlined
} from '@ant-design/icons-vue';
import * as echarts from 'echarts';
import request from '@/utils/request';

const route = useRoute();
const router = useRouter();

const classroomId = computed(() => route.params.classroomId as string);
const examId = computed(() => route.params.examId as string);

const loading = ref(false);
const activeTab = ref('grades');
const examInfo = ref<any>(null);
const studentGrades = ref<any[]>([]);
const questionAnalysis = ref<any[]>([]);
const expandedQuestions = ref<number[]>([]);
const showSegmentSettings = ref(false);

const barChartRef = ref<HTMLElement | null>(null);
const pieChartRef = ref<HTMLElement | null>(null);
let barChart: echarts.ECharts | null = null;
let pieChart: echarts.ECharts | null = null;

// 分数段配置
const segmentConfig = ref({
  enableCustomLabel: false,
  count: 4,
  segments: [
    { min: 0, max: 59, label: '不及格' },
    { min: 60, max: 74, label: '及格' },
    { min: 75, max: 89, label: '良好' },
    { min: 90, max: 100, label: '优秀' }
  ]
});

// 统计数据（从API statistics字段获取）
const statsData = ref<any>({});
const stats = computed(() => {
  if (statsData.value && Object.keys(statsData.value).length > 0) {
    return {
      maxScore: statsData.value.highest_score || 0,
      minScore: statsData.value.lowest_score || 0,
      avgScore: statsData.value.average_score || 0
    };
  }
  // 备用：从学生数据计算
  if (!studentGrades.value.length) {
    return { maxScore: 0, minScore: 0, avgScore: 0 };
  }
  const scores = studentGrades.value.map(s => s.score || 0);
  return {
    maxScore: Math.max(...scores),
    minScore: Math.min(...scores),
    avgScore: scores.reduce((a, b) => a + b, 0) / scores.length
  };
});

const totalScore = computed(() => {
  return examInfo.value?.total_score || 100;
});

// 表格列配置
const gradeColumns = [
  { title: '排名', key: 'rank', width: 80 },
  { title: '姓名/学号', key: 'student', width: 150 },
  { title: '提交时间', key: 'submit_time', width: 160, sorter: true },
  { title: '答题用时', key: 'duration', width: 100 },
  { title: '客观题得分', key: 'objective_score', width: 100, sorter: true },
  { title: '主观题得分', key: 'subjective_score', width: 100, sorter: true },
  { title: '总成绩', key: 'total_score', width: 100, sorter: true, defaultSortOrder: 'descend' },
  { title: '操作', key: 'action', width: 100 }
];

// 辅助函数
function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    'ONGOING': 'green',
    'SCHEDULED': 'blue',
    'COMPLETED': 'default',
    'UNPUBLISHED': 'orange'
  };
  return colors[status] || 'default';
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    'ONGOING': '进行中',
    'SCHEDULED': '已安排',
    'COMPLETED': '已结束',
    'UNPUBLISHED': '未发布'
  };
  return texts[status] || status;
}

function formatDateTime(time: string) {
  if (!time) return '-';
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function formatDuration(seconds: number) {
  if (!seconds) return '-';
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}分${secs}秒`;
}

function getRankClass(rank: number) {
  if (rank === 1) return 'gold';
  if (rank === 2) return 'silver';
  if (rank === 3) return 'bronze';
  return '';
}

function getQuestionTypeText(type: string) {
  const types: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题',
    'FILL_BLANK': '填空题'
  };
  return types[type] || type;
}

function getDifficultyClass(rate: number) {
  if (rate >= 0.8) return 'easy';
  if (rate >= 0.5) return 'medium';
  return 'hard';
}

function getDifficultyText(rate: number) {
  if (rate >= 0.8) return '简单';
  if (rate >= 0.5) return '中等';
  return '困难';
}

function getDifficultyClassByLevel(level: string) {
  const classes: Record<string, string> = {
    'easy': 'easy',
    'medium': 'medium',
    'hard': 'hard'
  };
  return classes[level] || 'medium';
}

function getDifficultyTextByLevel(level: string) {
  const texts: Record<string, string> = {
    'easy': '简单',
    'medium': '中等',
    'hard': '困难'
  };
  return texts[level] || '中等';
}

function toggleQuestion(index: number) {
  const idx = expandedQuestions.value.indexOf(index);
  if (idx === -1) {
    expandedQuestions.value.push(index);
  } else {
    expandedQuestions.value.splice(idx, 1);
  }
}

function goBack() {
  router.push(`/classroom/${classroomId.value}`);
}

function viewPaper(record: any) {
  router.push(`/classroom/${classroomId.value}/exam/${examId.value}/paper/${record.student_id}`);
}

function handleTableChange(pagination: any, filters: any, sorter: any) {
  // 排序处理
  if (sorter.field && sorter.order) {
    studentGrades.value.sort((a, b) => {
      const aVal = a[sorter.field] || 0;
      const bVal = b[sorter.field] || 0;
      return sorter.order === 'ascend' ? aVal - bVal : bVal - aVal;
    });
  }
}

async function exportGrades() {
  try {
    const teacherId = getCurrentUserId();
    const res = await request.get(
      `/api/v1/exams/${examId.value}/scores/export`,
      { params: { teacher_id: teacherId }, responseType: 'blob' }
    );
    const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${examInfo.value?.title || '考试'}_成绩单.xlsx`;
    link.click();
    window.URL.revokeObjectURL(url);
    message.success('导出成功');
  } catch (error: any) {
    console.error('导出失败:', error);
    message.error('导出失败');
  }
}

function updateSegments() {
  const count = segmentConfig.value.count;
  const step = Math.floor(totalScore.value / count);
  const segments = [];
  for (let i = 0; i < count; i++) {
    const min = i * step;
    const max = i === count - 1 ? totalScore.value : (i + 1) * step - 1;
    segments.push({ min, max, label: '' });
  }
  segmentConfig.value.segments = segments;
}

function saveSegmentSettings() {
  showSegmentSettings.value = false;
  renderCharts();
  message.success('设置已保存');
}

function renderCharts() {
  if (!barChartRef.value || !pieChartRef.value) return;

  // 计算分布数据
  const distribution = segmentConfig.value.segments.map(seg => ({
    ...seg,
    count: studentGrades.value.filter(
      s => (s.score || 0) >= seg.min && (s.score || 0) <= seg.max
    ).length
  }));

  // 柱状图
  if (!barChart) {
    barChart = echarts.init(barChartRef.value);
  }
  barChart.setOption({
    xAxis: {
      type: 'category',
      data: distribution.map(d =>
        segmentConfig.value.enableCustomLabel && d.label
          ? d.label
          : `${d.min}-${d.max}分`
      )
    },
    yAxis: { type: 'value', name: '人数' },
    series: [{
      data: distribution.map(d => d.count),
      type: 'bar',
      itemStyle: { color: '#1890ff' }
    }],
    tooltip: { trigger: 'axis' }
  });

  // 饼图
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value);
  }
  pieChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: distribution.map(d => ({
        name: segmentConfig.value.enableCustomLabel && d.label
          ? d.label
          : `${d.min}-${d.max}分`,
        value: d.count
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  });
}

// 获取当前用户ID
function getCurrentUserId(): number {
  try {
    const storedUser = localStorage.getItem('userInfo');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      return parsed.id ? parseInt(parsed.id) : 1;
    }
  } catch (e) {
    console.error('解析用户信息失败:', e);
  }
  return 1;
}

// 数据加载
async function fetchData() {
  loading.value = true;
  try {
    const teacherId = getCurrentUserId();

    // 获取考试信息
    const examRes = await request.get(`/api/v1/classroom-exams/${examId.value}`, {
      params: { student_id: teacherId }
    });
    examInfo.value = examRes.data;

    // 获取学生成绩列表
    const gradesRes = await request.get(
      `/api/v1/exams/${examId.value}/scores`,
      { params: { teacher_id: teacherId } }
    );

    // 提取exam_info和统计数据
    if (gradesRes.data?.exam_info) {
      examInfo.value = { ...examInfo.value, ...gradesRes.data.exam_info };
    }
    if (gradesRes.data?.statistics) {
      statsData.value = gradesRes.data.statistics;
    }

    studentGrades.value = gradesRes.data?.students || [];

    // 按分数降序排序
    studentGrades.value.sort((a, b) => (b.score || 0) - (a.score || 0));

    // 获取试题分析（延迟加载）
    fetchQuestionAnalysis();

  } catch (error: any) {
    console.error('获取数据失败:', error);
    message.error(error.response?.data?.detail || '获取数据失败');
  } finally {
    loading.value = false;
  }
}

async function fetchQuestionAnalysis() {
  try {
    const teacherId = getCurrentUserId();
    const res = await request.get(
      `/api/v1/exams/${examId.value}/questions/stats`,
      { params: { teacher_id: teacherId } }
    );
    questionAnalysis.value = res.data?.questions || res.data || [];
  } catch (error) {
    console.error('获取试题分析失败:', error);
  }
}

// 监听Tab切换渲染图表
watch(activeTab, (newVal) => {
  if (newVal === 'distribution') {
    nextTick(() => {
      renderCharts();
    });
  }
});

onMounted(() => {
  fetchData();
});
</script>

<style scoped lang="less">
.exam-statistics-page {
  min-height: 100vh;
  background: #f0f2f5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;

  .header-left {
    display: flex;
    align-items: center;
    gap: 12px;

    h1 {
      margin: 0;
      font-size: 20px;
    }
  }

  .header-stats {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.main-tabs {
  margin: 24px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.tab-content {
  .toolbar {
    margin-bottom: 16px;
    display: flex;
    justify-content: flex-end;
  }
}

.student-info {
  .name {
    font-weight: 500;
    display: block;
  }
  .id {
    font-size: 12px;
    color: #999;
  }
}

.rank {
  display: inline-block;
  width: 24px;
  height: 24px;
  line-height: 24px;
  text-align: center;
  border-radius: 50%;
  font-weight: bold;

  &.gold {
    background: #ffd700;
    color: #fff;
  }
  &.silver {
    background: #c0c0c0;
    color: #fff;
  }
  &.bronze {
    background: #cd7f32;
    color: #fff;
  }
}

.score {
  font-weight: 600;
  &.pass { color: #52c41a; }
  &.fail { color: #ff4d4f; }
}

// 图表区域
.charts-container {
  display: flex;
  gap: 24px;

  .chart-wrapper {
    flex: 1;
    background: #fafafa;
    border-radius: 8px;
    padding: 16px;

    h3 {
      margin: 0 0 16px 0;
      font-size: 16px;
    }

    .chart {
      height: 400px;
    }
  }
}

// 试题分析列表
.question-analysis-list {
  .question-item {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    margin-bottom: 12px;
    overflow: hidden;

    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: #fafafa;
      cursor: pointer;
      transition: background 0.2s;

      &:hover {
        background: #f0f0f0;
      }

      .question-info {
        display: flex;
        align-items: center;
        gap: 12px;

        .question-num {
          font-weight: 600;
        }

        .question-preview {
          color: #666;
        }
      }

      .question-stats {
        display: flex;
        align-items: center;
        gap: 16px;

        .stat {
          display: flex;
          align-items: center;
          gap: 4px;

          &.correct { color: #52c41a; }
          &.incorrect { color: #ff4d4f; }

          &.difficulty {
            padding: 2px 8px;
            border-radius: 4px;

            &.easy { background: #f6ffed; color: #52c41a; }
            &.medium { background: #fffbe6; color: #faad14; }
            &.hard { background: #fff2f0; color: #ff4d4f; }
          }
        }

        .anticon-right {
          transition: transform 0.2s;
          &.expanded {
            transform: rotate(90deg);
          }
        }
      }
    }

    .question-detail {
      padding: 16px;
      border-top: 1px solid #e8e8e8;

      .option-distribution {
        .option-bar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;

          .option-label {
            width: 24px;
            height: 24px;
            line-height: 24px;
            text-align: center;
            border-radius: 50%;
            background: #f0f0f0;
            font-weight: 500;
          }

          .bar-wrapper {
            flex: 1;
            height: 20px;
            background: #f0f0f0;
            border-radius: 4px;
            overflow: hidden;

            .bar {
              height: 100%;
              background: #1890ff;
              transition: width 0.3s;
            }
          }

          .option-count {
            width: 100px;
            text-align: right;
          }

          .correct-icon {
            color: #52c41a;
          }

          &.correct {
            .option-label {
              background: #52c41a;
              color: #fff;
            }
            .bar {
              background: #52c41a;
            }
          }
        }
      }

      .subjective-stats {
        p {
          margin: 8px 0;
        }
      }
    }
  }
}

// 分数段设置
.segment-list {
  .segment-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }
}
</style>
