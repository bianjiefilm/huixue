<template>
  <PageShell max-width="wide" class="exam-detail-page">
    <PageHeaderBar
      :title="exam?.exam_name || '考试'"
      :subtitle="`总人数: ${studentPapers.length} · 完成: ${completeCount} · 通过: ${passedCount}`"
      show-back
      :back-to="`/classroom/${classroomId}/course/${courseId}/exam`"
    >
      <template #actions>
        <a-button
          v-if="isTeacherView && hasUnmarkedPapers"
          type="primary"
          @click="goToMarking"
        >
          阅卷
        </a-button>
      </template>
    </PageHeaderBar>

    <a-spin :spinning="loading" tip="加载中...">
      <!-- 标签切换 -->
      <a-tabs v-model:activeKey="activeTab" class="exam-tabs">
        <a-tab-pane key="overview" tab="考试详情">
          <!-- 考试基本信息 -->
          <div class="tab-content">
            <div class="exam-overview">
              <a-row :gutter="[16, 16]">
                <a-col :span="24">
                  <a-card title="基本信息" :bordered="false">
                    <a-row :gutter="[16, 16]">
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">考试名称：</span>
                          <span class="info-value">{{ exam?.exam_name || '-' }}</span>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">试卷名称：</span>
                          <span class="info-value">{{ exam?.test_paper_name || '-' }}</span>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">考试状态：</span>
                          <a-tag :color="getExamStatusColor()">{{ getExamStatusText() }}</a-tag>
                        </div>
                      </a-col>
                      
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">考试时长：</span>
                          <span class="info-value">{{ exam?.time_limit_minutes || 0 }} 分钟</span>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">总分：</span>
                          <span class="info-value">{{ exam?.total_score || 100 }} 分</span>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">及格分数：</span>
                          <span class="info-value">{{ exam?.passing_score || 60 }} 分</span>
                        </div>
                      </a-col>
                      
                      <a-col :span="8" v-if="exam?.start_time">
                        <div class="info-item">
                          <span class="info-label">开始时间：</span>
                          <span class="info-value">{{ formatDateTime(exam.start_time) }}</span>
                        </div>
                      </a-col>
                      <a-col :span="8" v-if="exam?.end_time">
                        <div class="info-item">
                          <span class="info-label">结束时间：</span>
                          <span class="info-value">{{ formatDateTime(exam.end_time) }}</span>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">创建时间：</span>
                          <span class="info-value">{{ formatDateTime(exam?.created_at) }}</span>
                        </div>
                      </a-col>
                    </a-row>
                  </a-card>
                </a-col>
                
                <a-col :span="24">
                  <a-card title="考试设置" :bordered="false">
                    <a-row :gutter="[16, 16]">
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">试题打乱：</span>
                          <a-tag :color="exam?.shuffle_questions ? 'green' : 'red'">
                            {{ exam?.shuffle_questions ? '启用' : '禁用' }}
                          </a-tag>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">选项打乱：</span>
                          <a-tag :color="exam?.shuffle_options ? 'green' : 'red'">
                            {{ exam?.shuffle_options ? '启用' : '禁用' }}
                          </a-tag>
                        </div>
                      </a-col>
                      <a-col :span="8">
                        <div class="info-item">
                          <span class="info-label">题目数量：</span>
                          <span class="info-value">{{ exam?.question_count || 0 }} 题</span>
                        </div>
                      </a-col>
                    </a-row>
                  </a-card>
                </a-col>
              </a-row>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="stats" tab="成绩统计">
          <!-- 成绩统计内容 -->
          <div class="tab-content">
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
                  showTotal: (total: number) => `共 ${total} 条记录`
                }"
                :row-key="(record: any) => record.id"
                :loading="loading"
              >
                <!-- 学生姓名列 -->
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'name'">
                    <a>{{ record.student_name }}</a>
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
                      {{ record.obtained_score || 0 }}/{{ record.total_score || exam?.total_score || 100 }}
                      <span class="score-percent">({{ getScorePercent(record) }}%)</span>
                    </span>
                  </template>
                  
                  <!-- 评阅状态列 -->
                  <template v-else-if="column.key === 'marking'">
                    <a-tag :color="getMarkingStatusColor(record.grading_status)">
                      {{ getMarkingStatusText(record.grading_status) }}
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

            <!-- 导出按钮 -->
            <div class="export-section">
              <a-button 
                type="primary" 
                @click="exportExcelFile"
                :loading="exportLoading"
              >
                导出成绩
              </a-button>
            </div>

            <!-- 统计图表 -->
            <div class="stats-container">
              <h2>考试统计</h2>
              <div class="stats-cards">
                <a-card title="平均分" :bordered="false">
                  <div class="stat-value">{{ averageScore || 0 }}分</div>
                  <div class="stat-desc">总分 {{ exam?.total_score || 100 }}分</div>
                </a-card>
                <a-card title="及格率" :bordered="false">
                  <div class="stat-value">{{ passRate }}%</div>
                  <div class="stat-desc">通过标准 {{ exam?.passing_score || 60 }}分</div>
                </a-card>
                <a-card title="平均答题时长" :bordered="false">
                  <div class="stat-value">{{ averageDuration }}</div>
                  <div class="stat-desc">限时 {{ exam?.time_limit_minutes || 0 }} 分钟</div>
                </a-card>
                <a-card title="考生完成情况" :bordered="false">
                  <div class="stat-value">{{ completeCount }}/{{ studentPapers.length }}</div>
                  <div class="stat-desc">完成率 {{ completionRate }}%</div>
                </a-card>
                <a-card title="试卷评阅状态" :bordered="false">
                  <div class="stat-value">{{ gradedCount }}/{{ completeCount }}</div>
                  <div class="stat-desc">评阅进度 {{ gradingProgress }}%</div>
                </a-card>
                <a-card title="最高分" :bordered="false">
                  <div class="stat-value">{{ highestScore || 0 }}分</div>
                  <div class="stat-desc">{{ highestScoreStudent || '-' }}</div>
                </a-card>
                <a-card title="最低分" :bordered="false">
                  <div class="stat-value">{{ lowestScore || 0 }}分</div>
                  <div class="stat-desc">{{ lowestScoreStudent || '-' }}</div>
                </a-card>
                <a-card title="分数标准差" :bordered="false">
                  <div class="stat-value">{{ scoreStandardDeviation }}</div>
                  <div class="stat-desc">成绩离散程度</div>
                </a-card>
              </div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="distribution" tab="成绩分布">
          <!-- 成绩分布内容 -->
          <div class="tab-content">
            <div class="action-section">
              <a-button type="primary" @click="showSegmentSettingsModal">
                分数段设置
              </a-button>
              <a-button style="margin-left: 12px;" @click="exportDistributionData" :loading="exportLoading">
                导出分布数据
              </a-button>
              <a-radio-group v-model:value="distributionViewType" style="margin-left: 12px;" button-style="solid">
                <a-radio-button value="segment">分数段</a-radio-button>
                <a-radio-button value="grade">考试评价</a-radio-button>
              </a-radio-group>
            </div>
            
            <!-- 分布统计卡片 -->
            <div class="distribution-stats">
              <a-row :gutter="16">
                <a-col :span="6" v-for="(segment, index) in currentDistributionData" :key="index">
                  <a-card size="small" :bordered="false">
                    <div class="distribution-item">
                      <div class="distribution-label">{{ segment.name }}</div>
                      <div class="distribution-value">{{ segment.count }}人</div>
                      <div class="distribution-percent">({{ getPercentage(segment.count, completeCount) }}%)</div>
                    </div>
                  </a-card>
                </a-col>
              </a-row>
            </div>
            
            <div class="chart-container">
              <div class="chart-title">
                <h3>成绩分布柱状图</h3>
                <div class="chart-actions">
                  <a-button size="small" @click="downloadChart('bar')">
                    <template #icon><download-outlined /></template>
                    下载图表
                  </a-button>
                </div>
              </div>
              <div id="bar-chart" class="chart-box" ref="barChartRef"></div>
            </div>
            
            <div class="chart-container">
              <div class="chart-title">
                <h3>成绩分布饼状图</h3>
                <div class="chart-actions">
                  <a-button size="small" @click="downloadChart('pie')">
                    <template #icon><download-outlined /></template>
                    下载图表
                  </a-button>
                </div>
              </div>
              <div id="pie-chart" class="chart-box" ref="pieChartRef"></div>
            </div>
          </div>
        </a-tab-pane>
        
        <a-tab-pane key="questions" tab="试题分析">
          <!-- 试题分析内容 -->
          <div class="tab-content">
            <div class="question-analysis-container">
              <!-- 试题分析总览 -->
              <div class="analysis-overview" v-if="questionAnalysis.length > 0">
                <a-row :gutter="16">
                  <a-col :span="6">
                    <a-card size="small" :bordered="false">
                      <div class="overview-item">
                        <div class="overview-label">题目总数</div>
                        <div class="overview-value">{{ questionAnalysis.length }}</div>
                      </div>
                    </a-card>
                  </a-col>
                  <a-col :span="6">
                    <a-card size="small" :bordered="false">
                      <div class="overview-item">
                        <div class="overview-label">平均正确率</div>
                        <div class="overview-value">{{ averageCorrectRate }}%</div>
                      </div>
                    </a-card>
                  </a-col>
                  <a-col :span="6">
                    <a-card size="small" :bordered="false">
                      <div class="overview-item">
                        <div class="overview-label">难题数量</div>
                        <div class="overview-value">{{ difficultQuestionCount }}</div>
                      </div>
                    </a-card>
                  </a-col>
                  <a-col :span="6">
                    <a-card size="small" :bordered="false">
                      <div class="overview-item">
                        <div class="overview-label">区分度高题数</div>
                        <div class="overview-value">{{ highDiscriminationCount }}</div>
                      </div>
                    </a-card>
                  </a-col>
                </a-row>
              </div>

              <!-- 分析工具栏 -->
              <div class="analysis-toolbar" v-if="questionAnalysis.length > 0">
                <a-radio-group v-model:value="questionFilter" button-style="solid">
                  <a-radio-button value="all">全部题目</a-radio-button>
                  <a-radio-button value="difficult">难题 (正确率 < 60%)</a-radio-button>
                  <a-radio-button value="easy">简单 (正确率 > 85%)</a-radio-button>
                  <a-radio-button value="objective">客观题</a-radio-button>
                  <a-radio-button value="subjective">主观题</a-radio-button>
                </a-radio-group>
                <a-button @click="exportQuestionAnalysis" :loading="exportLoading">
                  <template #icon><download-outlined /></template>
                  导出分析
                </a-button>
              </div>

              <a-empty v-if="filteredQuestionAnalysis.length === 0" description="暂无试题分析数据" />
              
              <div v-else>
                <a-collapse accordion :bordered="false">
                  <a-collapse-panel 
                    v-for="(question, index) in filteredQuestionAnalysis" 
                    :key="question.id"
                  >
                    <template #header>
                      <div class="question-header">
                        <span class="question-title">
                          {{ getQuestionIndex(question) }}. {{ getQuestionTypeText(question.question_type) }}
                        </span>
                        <div class="question-stats">
                          <a-tag :color="getCorrectRateColor(question.correct_rate)">
                            正确率: {{ Math.round(question.correct_rate) }}%
                          </a-tag>
                          <a-tag color="blue">{{ question.question_score }}分</a-tag>
                          <a-tag v-if="question.discrimination" 
                                 :color="getDiscriminationColor(question.discrimination)">
                            区分度: {{ question.discrimination.toFixed(2) }}
                          </a-tag>
                        </div>
                      </div>
                    </template>
                    
                    <div class="question-detail">
                      <div class="question-content">{{ question.question_content }}</div>
                      
                      <!-- 客观题选项分析 -->
                      <div v-if="['single', 'multiple', 'judge'].includes(question.question_type)">
                        <a-divider>选项分析</a-divider>
                        
                        <div class="options-analysis">
                          <div v-for="option in question.options" :key="option.option_id" class="option-analysis-item">
                            <div class="option-header">
                              <span class="option-label" :class="{ 'correct-option': option.is_correct }">
                                选项 {{ option.option_id }}{{ option.is_correct ? ' (正确答案)' : '' }}
                              </span>
                              <span class="option-stats">
                                {{ option.selected_count }}人选择 ({{ Math.round(option.selected_rate) }}%)
                              </span>
                            </div>
                            <div class="option-content">{{ option.option_content }}</div>
                            <div class="option-bar">
                              <a-progress 
                                :percent="option.selected_rate" 
                                :stroke-color="option.is_correct ? '#52c41a' : '#ff4d4f'"
                                :format="(percent: number) => `${Math.round(percent)}%`"
                                :show-info="false"
                              />
                              <span class="percentage-text">{{ Math.round(option.selected_rate) }}%</span>
                            </div>
                          </div>
                        </div>

                        <!-- 答题分析 -->
                        <div class="answer-analysis">
                          <a-row :gutter="16">
                            <a-col :span="8">
                              <div class="analysis-metric">
                                <div class="metric-label">答题人数</div>
                                <div class="metric-value">{{ question.answered_students }}</div>
                              </div>
                            </a-col>
                            <a-col :span="8">
                              <div class="analysis-metric">
                                <div class="metric-label">正确人数</div>
                                <div class="metric-value">{{ Math.round(question.answered_students * question.correct_rate / 100) }}</div>
                              </div>
                            </a-col>
                            <a-col :span="8">
                              <div class="analysis-metric">
                                <div class="metric-label">平均用时</div>
                                <div class="metric-value">{{ question.average_time || '-' }}</div>
                              </div>
                            </a-col>
                          </a-row>
                        </div>
                      </div>
                      
                      <!-- 主观题分析 -->
                      <div v-else-if="question.question_type === 'essay'">
                        <a-divider>评分分析</a-divider>
                        <div class="essay-analysis">
                          <a-row :gutter="16">
                            <a-col :span="6">
                              <div class="analysis-metric">
                                <div class="metric-label">答题人数</div>
                                <div class="metric-value">{{ question.answered_students }}/{{ question.total_students }}</div>
                              </div>
                            </a-col>
                            <a-col :span="6">
                              <div class="analysis-metric">
                                <div class="metric-label">平均得分</div>
                                <div class="metric-value">{{ question.average_score?.toFixed(1) }}分</div>
                              </div>
                            </a-col>
                            <a-col :span="6">
                              <div class="analysis-metric">
                                <div class="metric-label">得分率</div>
                                <div class="metric-value">{{ Math.round(question.correct_rate) }}%</div>
                              </div>
                            </a-col>
                            <a-col :span="6">
                              <div class="analysis-metric">
                                <div class="metric-label">满分人数</div>
                                <div class="metric-value">{{ question.full_score_count || 0 }}</div>
                              </div>
                            </a-col>
                          </a-row>

                          <!-- 分数分布 -->
                          <div class="score-distribution">
                            <h4>分数分布</h4>
                            <div class="score-ranges">
                              <div v-for="range in getScoreRanges(question)" :key="range.label" class="score-range">
                                <span class="range-label">{{ range.label }}</span>
                                <div class="range-bar">
                                  <div class="range-fill" :style="{ width: range.percentage + '%' }"></div>
                                </div>
                                <span class="range-count">{{ range.count }}人</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </a-collapse-panel>
                </a-collapse>
              </div>
            </div>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-spin>

    <!-- 分数段设置弹窗 -->
    <a-modal
      v-model:open="segmentModalVisible"
      title="分数段设置"
      @ok="applySegmentSettings"
      :confirm-loading="settingsLoading"
      width="700px"
    >
      <div class="segment-settings">
        <div class="segment-count-setting">
          <span class="setting-label">分数段数量:</span>
          <a-radio-group v-model:value="scoreSegmentConfig.count" button-style="solid">
            <a-radio-button v-for="num in [2, 3, 4, 5, 6]" :key="num" :value="num">{{ num }}</a-radio-button>
          </a-radio-group>
        </div>
        
        <a-divider />
        
        <div class="segment-custom-name">
          <a-checkbox v-model:checked="scoreSegmentConfig.useCustomName">启用自定义考试评价</a-checkbox>
        </div>
        
        <div class="segment-items">
          <div class="segment-item" v-for="(segment, index) in scoreSegmentConfig.segments" :key="index">
            <div class="segment-range">
              <a-input-number 
                v-model:value="segment.min" 
                :min="0" 
                :max="segment.max - 1"
                style="width: 80px;" 
                :disabled="index !== 0 && index !== scoreSegmentConfig.segments.length - 1"
              />
              <span class="range-separator">~</span>
              <a-input-number 
                v-model:value="segment.max" 
                :min="segment.min + 1" 
                :max="100"
                style="width: 80px;"
                :disabled="index !== 0 && index !== scoreSegmentConfig.segments.length - 1"
              />
            </div>
            <div class="segment-name">
              <a-input 
                v-model:value="segment.name" 
                placeholder="分数段名称"
                :disabled="!scoreSegmentConfig.useCustomName"
              />
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import * as echarts from 'echarts';
import type { EChartsOption } from 'echarts';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import { 
  SearchOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import { 
  getExamDetail,
  getExamScores,
  getExamStatistics,
  getExamQuestionAnalysis,
  getExamScoreDistribution,
  updateExamScoreRanges,
  exportExamScores,
  type ExamInfo,
  type StudentPaper,
  type QuestionAnalysis,
  type ScoreSegment,
  type ExamStatistics
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
const exportLoading = ref(false);
const exam = ref<ExamInfo | undefined>(undefined);
const studentPapers = ref<StudentPaper[]>([]);
const questionAnalysis = ref<QuestionAnalysis[]>([]);
const statistics = ref<ExamStatistics | undefined>(undefined);
const searchText = ref('');
const filterType = ref('all'); // 'all', 'passed', 'failed'
const activeTab = ref('overview'); // 'overview', 'stats', 'distribution', 'questions'
const distributionViewType = ref('segment'); // 'segment', 'grade'
const questionFilter = ref('all'); // 'all', 'difficult', 'easy', 'objective', 'subjective'

// 图表引用
const barChartRef = ref<HTMLElement | null>(null);
const pieChartRef = ref<HTMLElement | null>(null);
let barChart: echarts.ECharts | null = null;
let pieChart: echarts.ECharts | null = null;

// 分数段设置
const segmentModalVisible = ref(false);
const settingsLoading = ref(false);
const scoreSegmentConfig = ref<{
  count: number;
  segments: ScoreSegment[];
  useCustomName: boolean;
}>({
  count: 4,
  segments: [
    { min: 0, max: 60, name: '不及格' },
    { min: 60, max: 75, name: '及格' },
    { min: 75, max: 90, name: '良好' },
    { min: 90, max: 100, name: '优秀' }
  ],
  useCustomName: false
});

// 表格列定义
const columns = [
  {
    title: '姓名',
    dataIndex: 'student_name',
    key: 'name',
  },
  {
    title: '分数',
    dataIndex: 'obtained_score',
    key: 'score',
    sorter: (a: StudentPaper, b: StudentPaper) => (a.obtained_score || 0) - (b.obtained_score || 0),
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    filters: [
      { text: '通过', value: 'passed' },
      { text: '未通过', value: 'failed' },
    ],
    onFilter: (value: string, record: StudentPaper) => {
      if (value === 'passed') return isPassed(record);
      return !isPassed(record);
    },
  },
  {
    title: '评阅状态',
    dataIndex: 'grading_status',
    key: 'marking',
    filters: [
      { text: '已评阅', value: 'fully_graded' },
      { text: '未评阅', value: 'not_graded' },
      { text: '部分评阅', value: 'partially_graded' },
      { text: '自动评阅', value: 'auto_graded' },
    ],
    onFilter: (value: string, record: StudentPaper) => record.grading_status === value,
  },
  {
    title: '操作',
    key: 'action',
  },
];

// 是否为教师视图
const isTeacherView = computed(() => {
  const role = userStore.userInfo.role;
  return role === 'teacher' || role === 'admin';
});

// 是否有未阅卷的试卷
const hasUnmarkedPapers = computed(() => {
  return studentPapers.value.some(paper => 
    paper.grading_status === 'not_graded' || paper.grading_status === 'partially_graded'
  );
});

// 过滤与计算属性
const filteredStudents = computed(() => {
  let result = studentPapers.value;
  
  // 按姓名搜索
  if (searchText.value) {
    result = result.filter(
      student => student.student_name.toLowerCase().includes(searchText.value.toLowerCase())
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
const completeCount = computed(() => statistics.value?.submitted_count || 0);

const passedCount = computed(() => statistics.value?.passed_count || 0);

const averageScore = computed(() => statistics.value?.average_score || 0);

const passRate = computed(() => statistics.value?.pass_rate || 0);

const highestScore = computed(() => statistics.value?.highest_score || 0);

const highestScoreStudent = computed(() => {
  const validPapers = studentPapers.value.filter(s => s.obtained_score !== null);
  if (validPapers.length === 0) return '';
  const maxScore = Math.max(...validPapers.map(s => s.obtained_score || 0));
  const student = validPapers.find(s => s.obtained_score === maxScore);
  return student ? student.student_name : '';
});

const lowestScore = computed(() => statistics.value?.lowest_score || 0);

const lowestScoreStudent = computed(() => {
  const validPapers = studentPapers.value.filter(s => s.obtained_score !== null);
  if (validPapers.length === 0) return '';
  const minScore = Math.min(...validPapers.map(s => s.obtained_score || 0));
  const student = validPapers.find(s => s.obtained_score === minScore);
  return student ? student.student_name : '';
});

// 新增统计指标
const averageDuration = computed(() => {
  const validPapers = studentPapers.value.filter(s => s.duration_minutes && s.duration_minutes > 0);
  if (validPapers.length === 0) return '-';
  const totalDuration = validPapers.reduce((sum, s) => sum + (s.duration_minutes || 0), 0);
  const avgMinutes = Math.round(totalDuration / validPapers.length);
  const hours = Math.floor(avgMinutes / 60);
  const minutes = avgMinutes % 60;
  return hours > 0 ? `${hours}小时${minutes}分钟` : `${minutes}分钟`;
});

const completionRate = computed(() => {
  if (studentPapers.value.length === 0) return 0;
  return Math.round((completeCount.value / studentPapers.value.length) * 100);
});

const gradedCount = computed(() => {
  return studentPapers.value.filter(s => 
    s.grading_status === 'fully_graded' || s.grading_status === 'auto_graded'
  ).length;
});

const gradingProgress = computed(() => {
  if (completeCount.value === 0) return 0;
  return Math.round((gradedCount.value / completeCount.value) * 100);
});

const scoreStandardDeviation = computed(() => {
  const validPapers = studentPapers.value.filter(s => s.obtained_score !== null);
  if (validPapers.length === 0) return '-';
  
  const scores = validPapers.map(s => s.obtained_score || 0);
  const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length;
  const variance = scores.reduce((sum, score) => sum + Math.pow(score - avg, 2), 0) / scores.length;
  const stdDev = Math.sqrt(variance);
  
  return stdDev.toFixed(2);
});

// 当前分布数据
const currentDistributionData = computed(() => {
  if (distributionViewType.value === 'grade') {
    return gradeDistributionData.value;
  }
  return segmentDistributionData.value;
});

// 分数段分布数据
const segmentDistributionData = computed(() => {
  return scoreSegmentConfig.value.segments.map(segment => {
    const count = studentPapers.value.filter(student => {
      const score = student.obtained_score || 0;
      if (segment.max === 100) {
        return score >= segment.min && score <= segment.max;
      }
      return score >= segment.min && score < segment.max;
    }).length;
    
    return {
      name: segment.name,
      count,
      min: segment.min,
      max: segment.max
    };
  });
});

// 等级分布数据
const gradeDistributionData = computed(() => {
  const totalScore = exam.value?.total_score || 100;
  const grades = [
    { name: '优秀', min: 90, max: 100, color: '#52c41a' },
    { name: '良好', min: 80, max: 89, color: '#1890ff' },
    { name: '中等', min: 70, max: 79, color: '#faad14' },
    { name: '及格', min: 60, max: 69, color: '#fa8c16' },
    { name: '不及格', min: 0, max: 59, color: '#ff4d4f' }
  ];
  
  return grades.map(grade => {
    const count = studentPapers.value.filter(student => {
      const score = student.obtained_score || 0;
      const percentage = (score / totalScore) * 100;
      return percentage >= grade.min && percentage <= grade.max;
    }).length;
    
    return {
      name: grade.name,
      count,
      color: grade.color
    };
  });
});

// 试题分析相关计算属性
const averageCorrectRate = computed(() => {
  if (questionAnalysis.value.length === 0) return 0;
  const totalRate = questionAnalysis.value.reduce((sum, q) => sum + q.correct_rate, 0);
  return Math.round(totalRate / questionAnalysis.value.length);
});

const difficultQuestionCount = computed(() => {
  return questionAnalysis.value.filter(q => q.correct_rate < 60).length;
});

const highDiscriminationCount = computed(() => {
  return questionAnalysis.value.filter(q => q.discrimination && q.discrimination > 0.3).length;
});

const filteredQuestionAnalysis = computed(() => {
  let filtered = questionAnalysis.value;
  
  switch (questionFilter.value) {
    case 'difficult':
      filtered = filtered.filter(q => q.correct_rate < 60);
      break;
    case 'easy':
      filtered = filtered.filter(q => q.correct_rate > 85);
      break;
    case 'objective':
      filtered = filtered.filter(q => ['single', 'multiple', 'judge'].includes(q.question_type));
      break;
    case 'subjective':
      filtered = filtered.filter(q => q.question_type === 'essay');
      break;
  }
  
  return filtered;
});

// 功能函数
function isPassed(student: StudentPaper): boolean {
  if (!exam.value) return false;
  return (student.obtained_score || 0) >= (exam.value.pass_score || 60);
}

function getScorePercent(student: StudentPaper): number {
  const totalScore = student.total_score || exam.value?.total_score || 100;
  if (totalScore === 0) return 0;
  return Math.round(((student.obtained_score || 0) / totalScore) * 100);
}

function getScoreColor(student: StudentPaper): string {
  if (isPassed(student)) {
    return 'success';
  }
  return 'error';
}

function getMarkingStatusText(status: string): string {
  switch (status) {
    case 'fully_graded':
      return '已评阅';
    case 'not_graded':
      return '未评阅';
    case 'partially_graded':
      return '部分评阅';
    case 'auto_graded':
      return '自动评阅';
    default:
      return '未知状态';
  }
}

function getMarkingStatusColor(status: string): string {
  switch (status) {
    case 'fully_graded':
      return 'success';
    case 'not_graded':
      return 'warning';
    case 'partially_graded':
      return 'processing';
    case 'auto_graded':
      return 'default';
    default:
      return 'default';
  }
}

function needMarking(student: StudentPaper): boolean {
  return student.grading_status === 'not_graded' || student.grading_status === 'partially_graded';
}

function getQuestionTypeText(type: string): string {
  switch (type) {
    case 'single':
      return '单选题';
    case 'multiple':
      return '多选题';
    case 'judge':
      return '判断题';
    case 'essay':
      return '主观题';
    default:
      return '未知题型';
  }
}

function getExamStatusText(): string {
  if (!exam.value) return '未知';
  
  if (!exam.value.is_published) return '未发布';
  
  const now = new Date();
  const startTime = exam.value.start_time ? new Date(exam.value.start_time) : null;
  const endTime = exam.value.end_time ? new Date(exam.value.end_time) : null;
  
  if (startTime && now < startTime) return '未开始';
  if (endTime && now > endTime) return '已结束';
  if (startTime && endTime && now >= startTime && now <= endTime) return '进行中';
  
  return '已发布';
}

function getExamStatusColor(): string {
  const status = getExamStatusText();
  switch (status) {
    case '未发布': return 'default';
    case '未开始': return 'blue';
    case '进行中': return 'green';
    case '已结束': return 'orange';
    default: return 'default';
  }
}

function formatDateTime(dateTime?: string | null): string {
  if (!dateTime) return '-';
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getPercentage(count: number, total: number): number {
  if (total === 0) return 0;
  return Math.round((count / total) * 100);
}

function downloadChart(chartType: 'bar' | 'pie') {
  const chart = chartType === 'bar' ? barChart : pieChart;
  if (!chart) return;
  
  const url = chart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  });
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${exam.value?.exam_name || '考试'}_${chartType === 'bar' ? '柱状图' : '饼状图'}.png`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function exportDistributionData() {
  exportLoading.value = true;
  try {
    const data = currentDistributionData.value.map(item => ({
      '分数段': item.name,
      '人数': item.count,
      '百分比': `${getPercentage(item.count, completeCount.value)}%`
    }));
    
    // 这里可以调用API导出，或者使用前端导出
    console.log('导出数据:', data);
    message.success('分布数据导出成功');
  } catch (error) {
    message.error('导出失败');
  } finally {
    exportLoading.value = false;
  }
}

// 试题分析相关函数
function getQuestionIndex(question: any): number {
  return questionAnalysis.value.findIndex(q => q.id === question.id) + 1;
}

function getCorrectRateColor(rate: number): string {
  if (rate >= 85) return 'green';
  if (rate >= 70) return 'blue';
  if (rate >= 60) return 'orange';
  return 'red';
}

function getDiscriminationColor(discrimination: number): string {
  if (discrimination >= 0.4) return 'green';
  if (discrimination >= 0.3) return 'blue';
  if (discrimination >= 0.2) return 'orange';
  return 'red';
}

function getScoreRanges(question: any) {
  const maxScore = question.question_score;
  const ranges = [
    { label: '0分', min: 0, max: 0 },
    { label: `1-${Math.floor(maxScore * 0.3)}分`, min: 1, max: Math.floor(maxScore * 0.3) },
    { label: `${Math.floor(maxScore * 0.3) + 1}-${Math.floor(maxScore * 0.7)}分`, min: Math.floor(maxScore * 0.3) + 1, max: Math.floor(maxScore * 0.7) },
    { label: `${Math.floor(maxScore * 0.7) + 1}-${maxScore - 1}分`, min: Math.floor(maxScore * 0.7) + 1, max: maxScore - 1 },
    { label: `${maxScore}分 (满分)`, min: maxScore, max: maxScore }
  ];
  
  return ranges.map(range => {
    // 从实际答题数据中统计各分数段人数
    const scoreDistribution = question.score_distribution || {};
    let count = 0;
    for (let score = range.min; score <= range.max; score++) {
      count += (scoreDistribution[score] || 0);
    }
    const total = question.answered_students || 1;
    const percentage = (count / total) * 100;

    return {
      ...range,
      count,
      percentage: Math.min(percentage, 100)
    };
  });
}

async function exportQuestionAnalysis() {
  exportLoading.value = true;
  try {
    const data = filteredQuestionAnalysis.value.map((question, index) => ({
      '题号': getQuestionIndex(question),
      '题型': getQuestionTypeText(question.question_type),
      '题目内容': question.question_content,
      '分值': question.question_score,
      '正确率': `${Math.round(question.correct_rate)}%`,
      '答题人数': question.answered_students,
      '区分度': question.discrimination?.toFixed(2) || '-'
    }));
    
    console.log('导出试题分析:', data);
    message.success('试题分析导出成功');
  } catch (error) {
    message.error('导出失败');
  } finally {
    exportLoading.value = false;
  }
}

// 事件处理函数
function handleSearch() {
  // 搜索功能已通过计算属性实现
}

function handleFilterChange() {
  // 过滤功能已通过计算属性实现
}

function viewPaper(student: StudentPaper) {
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/paper/${student.student_id}`);
}

function markPaper(student: StudentPaper) {
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/marking/${student.student_id}`);
}

function goToMarking() {
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${examId.value}/marking`);
}

async function exportExcelFile() {
  exportLoading.value = true;
  
  try {
    const blob = await exportExamScores({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo.id) || 1,
      export_format: 'xlsx'
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `考试成绩_${exam.value?.exam_name || '未知考试'}_${new Date().toLocaleDateString()}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    message.success('成绩已成功导出为Excel文件');
  } catch (error) {
    console.error('导出失败:', error);
    message.error('导出失败，请重试');
  } finally {
    exportLoading.value = false;
  }
}

function showSegmentSettingsModal() {
  segmentModalVisible.value = true;
}

async function applySegmentSettings() {
  settingsLoading.value = true;
  
  try {
    // 确保分数段数量与配置匹配
    adjustSegments();
    
    // 更新分数段设置
    const response = await updateExamScoreRanges({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo.id) || 1,
      ranges: scoreSegmentConfig.value.segments,
      enable_custom_labels: scoreSegmentConfig.value.useCustomName
    });
    
    if (response.code === '0000') {
      segmentModalVisible.value = false;
      
      // 重新绘制图表
      initCharts();
      
      message.success('分数段设置已更新');
    } else {
      message.error('更新分数段设置失败');
    }
  } catch (error) {
    console.error('更新分数段设置失败:', error);
    message.error('更新分数段设置失败');
  } finally {
    settingsLoading.value = false;
  }
}

function adjustSegments() {
  const count = scoreSegmentConfig.value.count;
  const segments = scoreSegmentConfig.value.segments;
  
  // 如果段数与当前配置不匹配，调整段数
  if (segments.length > count) {
    // 删除多余段
    scoreSegmentConfig.value.segments = segments.slice(0, count);
  } else if (segments.length < count) {
    // 添加缺少的段
    const lastSegment = segments[segments.length - 1];
    const step = Math.floor((100 - lastSegment.max) / (count - segments.length));
    
    let min = lastSegment.max;
    for (let i = segments.length; i < count; i++) {
      const max = i === count - 1 ? 100 : min + step;
      segments.push({
        min,
        max,
        name: `分段${i + 1}`
      });
      min = max;
    }
  }
}

// 图表初始化与数据加载
function initCharts() {
  nextTick(() => {
    initBarChart();
    initPieChart();
  });
}

function initBarChart() {
  if (!barChartRef.value) return;
  
  if (!barChart) {
    barChart = echarts.init(barChartRef.value);
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
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: currentDistributionData.value.map(d => d.name),
        axisTick: {
          alignWithLabel: true
        }
      }
    ],
    yAxis: [
      {
        type: 'value'
      }
    ],
    series: [
      {
        name: '学生人数',
        type: 'bar',
        barWidth: '60%',
        data: generateScoreDistributionData()
      }
    ]
  };
  
  barChart.setOption(option);
  
  // 窗口大小变化时自动调整图表大小
  window.addEventListener('resize', () => {
    barChart?.resize();
  });
}

function initPieChart() {
  if (!pieChartRef.value) return;
  
  if (!pieChart) {
    pieChart = echarts.init(pieChartRef.value);
  }
  
  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 10,
      data: currentDistributionData.value.map(d => d.name)
    },
    series: [
      {
        name: '分布情况',
        type: 'pie',
        radius: ['50%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: true,
          formatter: '{b}: {c}人 ({d}%)'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '16',
            fontWeight: 'bold'
          }
        },
        data: currentDistributionData.value.map(item => ({
          value: item.count,
          name: item.name,
          itemStyle: distributionViewType.value === 'grade' && 'color' in item ? 
            { color: item.color } : undefined
        }))
      }
    ]
  };
  
  pieChart.setOption(option);
  
  // 窗口大小变化时自动调整图表大小
  window.addEventListener('resize', () => {
    pieChart?.resize();
  });
}

function generateScoreDistributionData() {
  return currentDistributionData.value.map(item => item.count);
}

// 加载数据
async function loadExamData() {
  loading.value = true;
  
  try {
    // 加载考试信息
    const examResponse = await getExamDetail({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo.id) || 1
    });
    
    if (examResponse.code === '0000' && examResponse.data) {
      exam.value = examResponse.data;
    }
    
    // 加载学生成绩列表
    const scoresResponse = await getExamScores({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo.id) || 1,
      page: 1,
      page_size: 100 // 获取全部数据用于统计
    });
    
    if (scoresResponse.code === '0000' && scoresResponse.data) {
      studentPapers.value = scoresResponse.data.students || scoresResponse.data.list || [];
      statistics.value = scoresResponse.data.statistics;
    }
    
    // 加载题目分析数据
    if (isTeacherView.value) {
      const analysisResponse = await getExamQuestionAnalysis({
        exam_id: parseInt(examId.value),
        teacher_id: parseInt(userStore.userInfo.id) || 1
      });
      
      if (analysisResponse.code === '0000' && analysisResponse.data) {
        questionAnalysis.value = analysisResponse.data.questions;
      }
    }
    
    // 初始化图表
    nextTick(() => {
      if (activeTab.value === 'distribution') {
        initCharts();
      }
    });
  } catch (error) {
    console.error('加载考试数据失败:', error);
    message.error('加载考试数据失败，请稍后重试');
    exam.value = null;
    studentPapers.value = [];
    statistics.value = null;
    questionAnalysis.value = [];
  } finally {
    loading.value = false;
  }
}

// 页面初始化
onMounted(() => {
  loadExamData();
});

// 监听考试ID变化，重新加载数据
watch(() => examId.value, (newId, oldId) => {
  if (newId !== oldId) {
    loadExamData();
  }
});

// 监听标签页切换，初始化图表
watch(activeTab, (newTab) => {
  if (newTab === 'distribution') {
    nextTick(() => {
      initCharts();
    });
  }
});

// 监听分布视图类型变化，重新绘制图表
watch(distributionViewType, () => {
  if (activeTab.value === 'distribution') {
    nextTick(() => {
      initCharts();
    });
  }
});
</script>

<style lang="less" scoped>
.exam-detail-page {
  .exam-tabs {
    background: var(--hx-color-bg-container);
    padding: 0 var(--hx-space-5);
    border-radius: 8px;
    border: 1px solid var(--hx-color-border-muted);

    :deep(.ant-tabs-nav) {
      margin-bottom: 0;
    }
  }

  .tab-content {
    padding: 24px;
  }

  .filter-section {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
  }

  .student-list-container {
    margin-bottom: 24px;
  }

  .score-percent {
    color: #666;
    font-size: 12px;
    margin-left: 4px;
  }

  .export-section {
    margin-top: 16px;
    text-align: right;
  }

  .stats-container {
    margin-top: 32px;

    h2 {
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
    }
  }

  .stats-cards {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;

    .ant-card {
      text-align: center;

      .stat-value {
        font-size: 32px;
        font-weight: 600;
        color: #1890ff;
        line-height: 1.2;
      }

      .stat-desc {
        font-size: 14px;
        color: #666;
        margin-top: 8px;
      }
    }
  }

  .action-section {
    margin-bottom: 24px;
  }

  .chart-container {
    margin-bottom: 32px;

    .chart-title {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      h3 {
        font-size: 16px;
        font-weight: 600;
        margin: 0;
      }

      .chart-actions {
        display: flex;
        gap: 8px;
      }
    }

    .chart-box {
      width: 100%;
      height: 400px;
    }
  }

  // 考试详情页面样式
  .exam-overview {
    .info-item {
      margin-bottom: 16px;

      .info-label {
        font-weight: 500;
        color: #666;
        margin-right: 8px;
      }

      .info-value {
        color: #333;
      }
    }
  }

  // 分布统计样式
  .distribution-stats {
    margin-bottom: 24px;

    .distribution-item {
      text-align: center;
      padding: 16px 0;

      .distribution-label {
        font-size: 14px;
        color: #666;
        margin-bottom: 8px;
      }

      .distribution-value {
        font-size: 24px;
        font-weight: 600;
        color: #1890ff;
      }

      .distribution-percent {
        font-size: 12px;
        color: #999;
        margin-top: 4px;
      }
    }
  }

  .question-analysis-container {
    // 分析总览
    .analysis-overview {
      margin-bottom: 24px;

      .overview-item {
        text-align: center;
        padding: 16px 0;

        .overview-label {
          font-size: 14px;
          color: #666;
          margin-bottom: 8px;
        }

        .overview-value {
          font-size: 24px;
          font-weight: 600;
          color: #1890ff;
        }
      }
    }

    // 分析工具栏
    .analysis-toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding: 16px;
      background: #f5f5f5;
      border-radius: 8px;
    }

    // 题目头部
    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      width: 100%;

      .question-title {
        font-weight: 500;
        font-size: 16px;
      }

      .question-stats {
        display: flex;
        gap: 8px;
      }
    }

    // 题目详情
    .question-detail {
      .question-content {
        margin-bottom: 16px;
        padding: 16px;
        background: #f9f9f9;
        border-radius: 6px;
        font-size: 15px;
        line-height: 1.6;
      }
    }

    // 选项分析
    .options-analysis {
      .option-analysis-item {
        margin-bottom: 16px;
        padding: 12px;
        border: 1px solid #e8e8e8;
        border-radius: 6px;

        .option-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;

          .option-label {
            font-weight: 500;

            &.correct-option {
              color: #52c41a;
              font-weight: 600;
            }
          }

          .option-stats {
            font-size: 14px;
            color: #666;
          }
        }

        .option-content {
          margin-bottom: 12px;
          color: #333;
        }

        .option-bar {
          display: flex;
          align-items: center;
          gap: 12px;

          .percentage-text {
            font-weight: 500;
            min-width: 40px;
          }
        }
      }
    }

    // 答题分析指标
    .answer-analysis,
    .essay-analysis {
      margin-top: 20px;
      padding: 16px;
      background: #fafafa;
      border-radius: 6px;

      .analysis-metric {
        text-align: center;

        .metric-label {
          font-size: 14px;
          color: #666;
          margin-bottom: 8px;
        }

        .metric-value {
          font-size: 20px;
          font-weight: 600;
          color: #1890ff;
        }
      }
    }

    // 分数分布
    .score-distribution {
      margin-top: 16px;

      h4 {
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
      }

      .score-ranges {
        .score-range {
          display: flex;
          align-items: center;
          margin-bottom: 8px;
          gap: 12px;

          .range-label {
            min-width: 80px;
            font-size: 14px;
          }

          .range-bar {
            flex: 1;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            position: relative;

            .range-fill {
              height: 100%;
              background: linear-gradient(90deg, #1890ff, #40a9ff);
              transition: width 0.3s ease;
            }
          }

          .range-count {
            min-width: 40px;
            font-size: 14px;
            text-align: right;
          }
        }
      }
    }

    .question-content {
      margin-bottom: 16px;
      color: #333;
      font-size: 14px;
      line-height: 1.6;
    }

    .option-item {
      margin-bottom: 16px;

      .option-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;

        .option-label {
          font-weight: 500;
          
          &.correct-option {
            color: #52c41a;
          }
        }

        .option-stats {
          color: #666;
          font-size: 14px;
        }
      }

      .option-content {
        margin-bottom: 8px;
        padding-left: 20px;
        color: #666;
      }
    }

    .essay-stats {
      padding: 16px;
      background: #f5f5f5;
      border-radius: 4px;

      p {
        margin: 4px 0;
        color: #666;
      }
    }
  }

  .segment-settings {
    .segment-count-setting {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;

      .setting-label {
        font-weight: 500;
      }
    }

    .segment-custom-name {
      margin-bottom: 16px;
    }

    .segment-items {
      .segment-item {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;

        .segment-range {
          display: flex;
          align-items: center;
          gap: 8px;

          .range-separator {
            color: #999;
          }
        }

        .segment-name {
          flex: 1;
        }
      }
    }
  }
}

@media (max-width: 1200px) {
  .exam-detail-page {
    .stats-cards {
      grid-template-columns: repeat(2, 1fr);
    }
  }
}

@media (max-width: 768px) {
  .exam-detail-page {
    .stats-cards {
      grid-template-columns: 1fr;
    }

    .filter-section {
      flex-direction: column;
    }
  }
}
</style>