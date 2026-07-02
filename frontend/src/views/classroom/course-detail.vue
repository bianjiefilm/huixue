<template>
  <div class="course-detail-page">
    <a-spin :spinning="loading" tip="加载中...">
      <div v-if="courseDetail" class="content-container">
        <!-- 返回按钮 -->
        <div class="back-link">
          <router-link :to="`/classroom/${classroomId}`">
            <a-button type="link">
              <template #icon><arrow-left-outlined /></template>
              返回课堂
            </a-button>
          </router-link>
        </div>

        <!-- 课程标题和状态区域 -->
        <div class="course-header">
          <div class="status-badge" :class="getCourseStatusClass(courseDetail.status)">
            {{ getCourseStatusText(courseDetail.status) }}
          </div>
          <h1 class="course-title">{{ courseDetail.name }}</h1>
          <div class="course-coins">
            <gift-outlined />
            <span>{{ courseDetail.coins }} 金币</span>
          </div>
        </div>

        <!-- 教师状态管理区域 -->
        <a-card v-if="isTeacher && courseDetail.statusSuggestions && courseDetail.statusSuggestions.length > 0" class="status-management-card">
          <template #title>
            <div class="card-title">
              <exclamation-circle-outlined />
              <span>状态管理建议</span>
            </div>
          </template>
          <div class="status-suggestions">
            <a-alert
              v-for="(suggestion, index) in courseDetail.statusSuggestions"
              :key="index"
              :message="suggestion"
              type="info"
              show-icon
              style="margin-bottom: 8px"
            />
          </div>
          <div class="status-actions">
            <a-space>
              <PermissionGuard :permission="PermissionCode.CLASSROOM_MANAGE" :context="{ classroomId }">
                <a-button
                  v-if="courseDetail.canPublish"
                  type="primary"
                  @click="publishCourse"
                >
                  发布课程
                </a-button>
                <a-button
                  v-if="courseDetail.canUnpublish"
                  danger
                  @click="unpublishCourse"
                >
                  取消发布
                </a-button>
              </PermissionGuard>
              <a-button @click="refreshStatus">
                刷新状态
              </a-button>
            </a-space>
          </div>
        </a-card>

        <!-- 课程基本信息卡片 -->
        <a-card class="info-card">
          <a-row :gutter="16">
            <a-col :xs="24" :md="16">
              <div class="basic-info">
                <template v-if="!courseDetail.isStudentView">
                  <div class="info-item">
                    <team-outlined />
                    <span>学习人数：</span>
                    <div class="student-stats">
                      <span class="student-learning">学习中：{{ courseDetail.learningCount }}</span>
                      <span class="student-completed">已完成：<span class="completed-count">{{ courseDetail.completedCount }}</span></span>
                      <span class="student-not-started">未开始：{{ courseDetail.notStartedCount }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <star-outlined />
                    <span>难度系数：</span>
                    <a-rate :value="getDifficultyNumber(courseDetail.difficulty)" :count="5" disabled />
                  </div>
                  <div class="info-item">
                    <calendar-outlined />
                    <span>起止时间：</span>
                    <span>{{ formatDate(courseDetail.startDate) }} 至 {{ formatDate(courseDetail.endDate) }}</span>
                  </div>
                  <div class="info-item" v-if="courseDetail.endDate && courseDetail.status !== 'completed'">
                    <clock-circle-outlined />
                    <span>剩余时间：</span>
                    <span class="remaining-time">{{ courseDetail.formattedRemainingTime || calculateRemainingTime(courseDetail.endDate) }}</span>
                  </div>
                </template>
                <template v-else>
                  <div class="info-item">
                    <tags-outlined />
                    <span>当前状态：</span>
                    <a-tag :color="getCourseStatusClass(courseDetail.status) === 'status-ongoing' ? 'blue' : (getCourseStatusClass(courseDetail.status) === 'status-completed' ? 'green' : 'orange')">
                      {{ getCourseStatusText(courseDetail.status) }}
                    </a-tag>
                  </div>
                  <div class="info-item">
                    <team-outlined />
                    <span>个人进度：</span>
                    <div class="student-stats">
                      <span class="student-completed">已完成 {{ courseDetail.studentProgress?.completedTaskCount || 0 }}</span>
                      <span class="student-not-started">未开始 {{ (courseDetail.studentProgress?.totalTaskCount || 0) - (courseDetail.studentProgress?.completedTaskCount || 0) }}</span>
                    </div>
                  </div>
                  <div class="info-item">
                    <star-outlined />
                    <span>难易程度：</span>
                    <span>{{ getDifficultyText(courseDetail.difficulty) }}</span>
                  </div>
                  <div class="info-item">
                    <calendar-outlined />
                    <span>起止时间：</span>
                    <span>{{ formatDate(courseDetail.startDate) }} 至 {{ formatDate(courseDetail.endDate) }}</span>
                  </div>
                  <div class="info-item" v-if="courseDetail.endDate">
                    <clock-circle-outlined />
                    <span>剩余时间：</span>
                    <span class="remaining-time">{{ courseDetail.formattedRemainingTime || calculateRemainingTime(courseDetail.endDate) }}</span>
                  </div>
                </template>
              </div>
            </a-col>
            <a-col :xs="24" :md="8">
              <div class="classroom-info-sidebar">
                <div class="info-section">
                  <div class="info-title">所属课堂</div>
                  <router-link :to="`/classroom/${safeClassroom.id}`" class="classroom-link">
                    <a-tag color="blue" style="font-size: 14px; padding: 4px 8px;">
                      <read-outlined style="margin-right: 4px;" />
                      {{ safeClassroom.name }}
                    </a-tag>
                  </router-link>
                </div>

                <!-- 学习统计与技能标签侧边栏 (学生端) -->
                <template v-if="courseDetail.isStudentView">
                  <a-divider style="margin: 12px 0;" />
                  <div class="info-section student-sidebar-stats">
                    <div class="sidebar-header">
                      <div class="info-title">学习统计</div>
                      <span class="sidebar-extra">已学习 {{ courseDetail.studentProgress?.completedTaskCount || 0 }} 关 / 共 {{ courseDetail.studentProgress?.totalTaskCount || 0 }} 关</span>
                    </div>
                    <div class="sidebar-content">
                      <a-progress 
                        :percent="courseDetail.studentProgress?.completionRate || 0" 
                        strokeColor="#1890ff"
                        :status="courseDetail.studentProgress?.completionRate === 100 ? 'success' : 'active'"
                      />
                    </div>
                  </div>
                  
                  <a-divider style="margin: 12px 0;" />
                  <div class="info-section student-sidebar-skills">
                    <div class="sidebar-header">
                      <div class="info-title">技能标签</div>
                      <span class="sidebar-extra" v-if="courseDetail.skills">已获得 {{ courseDetail.skills.filter(s => s.isLighted).length }} 个 / 共 {{ courseDetail.skills.length }} 个</span>
                    </div>
                    <div class="sidebar-content">
                      <a-empty v-if="!courseDetail.skills || courseDetail.skills.length === 0" description="暂无标签" :image-style="{ height: '40px' }" style="margin: 0" />
                      <a-space v-else wrap :size="[8, 8]">
                        <a-tag
                          v-for="skill in courseDetail.skills"
                          :key="skill.id"
                          :color="skill.isLighted ? 'orange' : 'default'"
                          :style="{ 
                            margin: 0, 
                            color: skill.isLighted ? '#fff' : '#8c8c8c',
                            background: skill.isLighted ? '#fa8c16' : '#f5f5f5',
                            borderColor: skill.isLighted ? '#fa8c16' : '#d9d9d9'
                          }"
                        >
                          {{ skill.name }}
                        </a-tag>
                      </a-space>
                    </div>
                  </div>
                </template>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 学生学习进度卡片 (仅学生视图) -->
        <a-card v-if="courseDetail.isStudentView && courseDetail.studentProgress" class="progress-card">
          <template #title>
            <div class="card-title">
              <line-chart-outlined />
              <span>学习统计</span>
            </div>
          </template>
          <a-row :gutter="24">
            <a-col :xs="24" :sm="12" :md="6">
              <a-statistic 
                title="已完成关卡" 
                :value="`${courseDetail.studentProgress.completedTaskCount}/${courseDetail.studentProgress.totalTaskCount}`" 
                :valueStyle="{ color: '#1890ff' }"
              >
                <template #prefix>
                  <check-circle-outlined />
                </template>
              </a-statistic>
            </a-col>
            <a-col :xs="24" :sm="12" :md="6">
              <a-statistic 
                title="学习进度" 
                :value="`${courseDetail.studentProgress.completionRate}%`" 
                :valueStyle="{ color: '#52c41a' }"
              >
                <template #prefix>
                  <line-chart-outlined />
                </template>
              </a-statistic>
            </a-col>
            <a-col :xs="24" :sm="12" :md="6">
              <a-statistic 
                title="已获得金币" 
                :value="courseDetail.studentProgress.earnedCoins" 
                :valueStyle="{ color: '#faad14' }"
              >
                <template #prefix>
                  <trophy-outlined />
                </template>
              </a-statistic>
            </a-col>
            <a-col :xs="24" :md="6">
              <div class="progress-bar-container">
                <div class="progress-label">总体进度</div>
                <a-progress 
                  :percent="courseDetail.studentProgress.completionRate" 
                  :status="courseDetail.studentProgress.completionRate === 100 ? 'success' : 'active'"
                />
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 实训作业卡片 (仅实训课程且学生视图) -->
        <a-card v-if="courseDetail.isStudentView && courseDetail.trainingType" class="homework-card" title="作业提交">
          <template #extra>
            <file-text-outlined />
          </template>
          <div class="homework-content">
            <div v-if="courseDetail.homeworks && courseDetail.homeworks.length > 0" class="homework-list">
              <div v-for="homework in courseDetail.homeworks" :key="homework.id" class="homework-item">
                <div class="homework-info">
                  <div class="homework-title">{{ homework.title }}</div>
                  <div class="homework-desc">{{ homework.description }}</div>
                  <div class="homework-meta">
                    <a-tag :color="getHomeworkStatusColor(homework.status)">
                      {{ getHomeworkStatusText(homework.status) }}
                    </a-tag>
                    <span v-if="homework.submittedAt" class="submit-time">
                      提交时间: {{ formatDate(homework.submittedAt) }}
                    </span>
                    <span v-if="homework.deadline" class="deadline">
                      截止时间: {{ formatDate(homework.deadline) }}
                    </span>
                  </div>
                </div>
                <div class="homework-actions">
                  <a-button
                    v-if="homework.status === 'not_submitted'"
                    type="primary"
                    size="small"
                    @click="openHomeworkSubmitModal(homework)"
                  >
                    提交作业
                  </a-button>
                  <a-button
                    v-else-if="homework.status === 'submitted' || homework.status === 'late_submitted'"
                    type="default"
                    size="small"
                    @click="viewHomeworkSubmission(homework)"
                  >
                    查看提交
                  </a-button>
                </div>
              </div>
            </div>
            <a-empty v-else description="暂无作业要求" />
          </div>
        </a-card>

        <!-- 全部任务卡片 -->
        <a-card class="tasks-card" title="全部任务">
          <template #extra>
            <safety-outlined />
          </template>
          <a-empty v-if="!courseDetail.tasks || courseDetail.tasks.length === 0" description="暂无任务" />
          <div v-else class="tasks-container">
            <a-collapse v-model:activeKey="activeTaskKeys">
              <a-collapse-panel
                v-for="(task, index) in courseDetail.tasks"
                :key="task.id"
                :header="`第${index + 1}关：${formatTaskTitle(task.title)}`"
              >
                <!-- 学生端显示任务完成状态 -->
                <template v-if="courseDetail.isStudentView" #extra>
                  <div style="font-size: 12px; display: inline-flex; align-items: center;">
                    <span v-if="task.completed" style="color: #52c41a; font-weight: bold; background: #f6ffed; border: 1px solid #b7eb8f; padding: 0 4px; border-radius: 2px;">
                      ■ 通关
                    </span>
                    <span v-else style="color: #fa8c16; background: #fff7e6; border: 1px solid #ffd591; padding: 0 4px; border-radius: 2px;">
                      □ 未通关
                    </span>
                  </div>
                </template>
                
                <div class="task-content">
                  <div class="task-info">
                    <div class="task-meta" style="color: #666; font-size: 13px; margin-bottom: 8px;">
                      <span>通关: {{ task.completed ? 1 : 0 }} | 未通关: {{ task.completed ? 0 : 1 }} | 可获金币: {{ task.coins || 0 }} | 类型: {{ getTaskTypeText(task.type) }}</span>
                    </div>
                    <div class="task-description">
                      {{ task.description }}
                    </div>
                    <div class="task-skills">
                      <span class="label">相关技能:</span>
                      <a-space>
                        <a-tag 
                          v-for="skill in task.skills"
                          :key="skill"
                          color="blue"
                        >
                          {{ skill }}
                        </a-tag>
                      </a-space>
                    </div>
                  </div>
                  <div class="task-actions">
                    <a-button
                      type="primary"
                      @click="navigateToChallenge(task.id)"
                    >
                      {{ courseDetail.isStudentView ? (task.completed ? '再次挑战' : '开启挑战') : '查看挑战' }}
                    </a-button>
                    <a-button
                      v-if="isTeacher"
                      type="default"
                      @click="navigateToExam()"
                    >
                      课程考核
                    </a-button>
                  </div>
                </div>
              </a-collapse-panel>
            </a-collapse>
          </div>
        </a-card>



        <!-- 学习统计卡片 (仅学生) -->
        <a-card v-if="learningStats" class="learning-stats-card" title="学习统计">
          <template #extra>
            <bar-chart-outlined />
          </template>
          <div class="stats-grid">
            <!-- 基本统计 -->
            <div class="stat-section">
              <h4>学习进度</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <div class="stat-value">{{ learningStats.completedTasks }}/{{ learningStats.totalTasks }}</div>
                  <div class="stat-label">任务完成</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatStatisticValue(learningStats.completionRate, 'rate') }}</div>
                  <div class="stat-label">完成率</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ learningStats.totalCoins }}</div>
                  <div class="stat-label">获得金币</div>
                </div>
              </div>
            </div>

            <!-- 时间统计 -->
            <div class="stat-section">
              <h4>学习时长</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <div class="stat-value">{{ formatStatisticValue(learningStats.todayStudyTime, 'time') }}</div>
                  <div class="stat-label">今日学习</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatStatisticValue(learningStats.totalStudyTime, 'time') }}</div>
                  <div class="stat-label">总时长</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ learningStats.consistencyScore }}</div>
                  <div class="stat-label">一致性得分</div>
                </div>
              </div>
            </div>

            <!-- 学习行为 -->
            <div class="stat-section">
              <h4>学习习惯</h4>
              <div class="stat-items">
                <div class="stat-item">
                  <div class="stat-value">{{ learningStats.currentStreak }}</div>
                  <div class="stat-label">连续学习天数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ formatStatisticValue(learningStats.averageSessionTime, 'time') }}</div>
                  <div class="stat-label">平均会话时长</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ learningStats.totalSessions }}</div>
                  <div class="stat-label">学习会话数</div>
                </div>
              </div>
            </div>

            <!-- 最近活动 -->
            <div class="stat-section full-width">
              <h4>最近活动</h4>
              <div class="recent-activities">
                <div
                  v-for="activity in learningStats.recentActivities.slice(0, 3)"
                  :key="activity.id"
                  class="activity-item"
                >
                  <div class="activity-icon" :class="`activity-${activity.type}`">
                    <check-circle-outlined v-if="activity.type === 'task_completion'" />
                    <trophy-outlined v-else-if="activity.type === 'coin_earned'" />
                    <bulb-outlined v-else-if="activity.type === 'skill_unlocked'" />
                    <clock-circle-outlined v-else />
                  </div>
                  <div class="activity-content">
                    <div class="activity-description">{{ activity.description }}</div>
                    <div class="activity-time">{{ formatTimeAgo(activity.timestamp) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 推荐实践卡片 -->
        <a-card v-if="recommendations.length > 0" class="recommendations-card" title="推荐实践">
          <template #extra>
            <bulb-outlined />
          </template>
          <div class="recommendations-container">
            <div
              v-for="rec in recommendations"
              :key="rec.course.id"
              class="recommendation-item"
              @click="goToRecommendedCourse(rec.course.id)"
            >
              <div class="recommendation-content">
                <div class="recommendation-title">{{ rec.course.title }}</div>
                <div class="recommendation-meta">
                  <a-tag :color="getDifficultyColor(rec.course.difficulty)">
                    {{ getDifficultyText(rec.course.difficulty) }}
                  </a-tag>
                  <span class="recommendation-score">{{ Math.round(rec.score) }}分匹配</span>
                </div>
                <div class="recommendation-reasons">
                  <div v-for="reason in rec.reasons.slice(0, 2)" :key="reason" class="reason-item">
                    {{ reason }}
                  </div>
                </div>
              </div>
              <div class="recommendation-arrow">
                <right-outlined />
              </div>
            </div>
          </div>
        </a-card>
      </div>
      <a-result v-else status="404" title="找不到课程" sub-title="您访问的课程不存在或已被删除">
        <template #extra>
          <router-link :to="`/classroom/${classroomId}`">
            <a-button type="primary">返回课堂</a-button>
          </router-link>
        </template>
      </a-result>
    </a-spin>

    <!-- 作业提交模态框 -->
    <a-modal
      v-model:open="homeworkSubmitModalVisible"
      :title="`提交作业 - ${currentHomework?.title || ''}`"
      :width="isMobile ? '95vw' : '800px'"
      :body-style="{ maxHeight: isMobile ? '70vh' : 'auto', overflow: 'auto' }"
      @ok="submitHomework"
      :confirm-loading="submittingHomework"
    >
      <div class="homework-submit-content">
        <a-tabs v-model:activeKey="submitTabActiveKey">
          <a-tab-pane key="design" tab="设计文件">
            <div class="file-upload-section">
              <a-upload-dragger
                v-model:file-list="designFiles"
                :multiple="false"
                :max-count="1"
                accept=".fig,.sketch,.xd,.ai,.psd,.png,.jpg,.jpeg,.gif,.svg"
                :before-upload="beforeUploadDesignFile"
                @change="handleDesignFileChange"
              >
                <p class="ant-upload-drag-icon">
                  <upload-outlined />
                </p>
                <p class="ant-upload-text">点击或拖拽上传设计文件</p>
                <p class="ant-upload-hint">
                  支持格式：FIG, Sketch, XD, AI, PSD, PNG, JPG, JPEG, GIF, SVG
                </p>
              </a-upload-dragger>
            </div>
          </a-tab-pane>
          <a-tab-pane key="report" tab="实验报告">
            <div class="report-editor-section">
              <a-form-item label="报告标题">
                <a-input v-model:value="homeworkForm.reportTitle" placeholder="请输入实验报告标题" />
              </a-form-item>
              <a-form-item label="报告内容">
                <RichTextEditor
                  v-model:value="homeworkForm.reportContent"
                  placeholder="请详细描述您的实验过程、分析结果和心得体会..."
                  :height="300"
                />
              </a-form-item>
            </div>
          </a-tab-pane>
        </a-tabs>

        <a-alert
          v-if="currentHomework?.deadline && new Date() > new Date(currentHomework.deadline)"
          message="注意：已超过截止时间，此次提交将记为补交作业"
          type="warning"
          show-icon
          style="margin-top: 16px"
        />
      </div>
    </a-modal>

    <!-- 作业查看模态框 -->
    <a-modal
      v-model:open="homeworkViewModalVisible"
      :title="`查看作业 - ${currentHomework?.title || ''}`"
      width="800px"
      :footer="null"
    >
      <div class="homework-view-content">
        <a-tabs default-active-key="design">
          <a-tab-pane key="design" tab="设计文件">
            <div v-if="homeworkSubmission?.designFile" class="design-file-view">
              <img
                :src="homeworkSubmission.designFile.previewUrl"
                alt="设计文件预览"
                class="preview-image"
              />
              <div class="file-info">
                <p><strong>文件名：</strong>{{ homeworkSubmission.designFile.name }}</p>
                <p><strong>文件大小：</strong>{{ formatFileSize(homeworkSubmission.designFile.size) }}</p>
                <p><strong>上传时间：</strong>{{ formatDate(homeworkSubmission.designFile.uploadTime) }}</p>
                <a-button type="primary" @click="downloadFile(homeworkSubmission.designFile)">
                  下载文件
                </a-button>
              </div>
            </div>
            <a-empty v-else description="未上传设计文件" />
          </a-tab-pane>
          <a-tab-pane key="report" tab="实验报告">
            <div v-if="homeworkSubmission?.report" class="report-view">
              <h3>{{ homeworkSubmission.report.title }}</h3>
              <div class="report-content" v-html="homeworkSubmission.report.content"></div>
            </div>
            <a-empty v-else description="未提交实验报告" />
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import dayjs from 'dayjs';
import { getClassroomCourseDetailById, getStudentClassroomCourseDetailById } from '../../api/course';
import { post } from '../../utils/request';
import type { ClassroomCourseDetail } from '../../types/course';
import { message } from 'ant-design-vue';
import { useUserStore } from '../../stores/user';
import { useCourseStore } from '../../stores/course';
import {
  calculateCourseStatus,
  getCourseStatusChangeSuggestions,
  formatRemainingTime,
  canTeacherChangeCourseStatus,
  COURSE_STATUS_TEXT,
  COURSE_STATUS_CLASS
} from '../../utils/courseStatus';
import { getHybridRecommendations, type RecommendationResult } from '../../utils/recommendationSystem';
import {
  calculateLearningStatistics,
  formatStudyTime,
  formatStatisticValue,
  type LearningStatistics
} from '../../utils/learningStatistics';
import { useGlobalDataSyncStore, DataSyncEventType } from '../../stores/globalDataSync';
import RichTextEditor from '../../components/common/RichTextEditor.vue';
import PermissionGuard from '../../components/common/PermissionGuard.vue';
import { PermissionCode, isTeacher as checkIsTeacher, isAdmin as checkIsAdmin } from '../../utils/permissions';
import {
  ArrowLeftOutlined,
  GiftOutlined,
  TeamOutlined,
  StarOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  ReadOutlined,
  SafetyOutlined,
  TagsOutlined,
  CheckCircleOutlined,
  TrophyOutlined,
  LineChartOutlined,
  CheckOutlined,
  CloseOutlined,
  FileTextOutlined,
  UploadOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  RightOutlined,
  BarChartOutlined
} from '@ant-design/icons-vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const courseStore = useCourseStore();
const dataSyncStore = useGlobalDataSyncStore();
const classroomId = route.params.classroomId as string;
const courseId = route.params.courseId as string;
const courseDetail = ref<ClassroomCourseDetail | null>(null);
const loading = ref(true);
const activeTaskKeys = ref<string[]>([]);

// 作业相关状态
const homeworkSubmitModalVisible = ref(false);
const homeworkViewModalVisible = ref(false);
const submittingHomework = ref(false);
const currentHomework = ref<any>(null);
const submitTabActiveKey = ref('design');
const designFiles = ref<any[]>([]);
const homeworkForm = reactive({
  reportTitle: '',
  reportContent: ''
});
const homeworkSubmission = ref<any>(null);

// 推荐实践相关
const recommendations = ref<RecommendationResult[]>([]);

// 学习统计相关
const learningStats = ref<LearningStatistics | null>(null);

// 用户角色
const userRole = computed(() => userStore.userInfo.role || 'student');
const isTeacher = computed(() => checkIsTeacher(userRole.value) || checkIsAdmin(userRole.value));
const isStudent = computed(() => userRole.value === 'student');

// 移动端检测
const isMobile = computed(() => {
  if (process.client) {
    return window.innerWidth < 768
  }
  return false
});

// 安全获取课堂信息
const safeClassroom = computed(() => {
  if (!courseDetail.value || !courseDetail.value.classroom) {
    return { id: classroomId, name: '加载中...' };
  }
  return {
    id: courseDetail.value.classroom.id || classroomId,
    name: courseDetail.value.classroom.name || '未知课堂'
  };
});

// 格式化日期函数
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '未设置';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 格式化任务标题（去除"第X章："前缀）
const formatTaskTitle = (title: string): string => {
  if (!title) return '';
  // 移除 "第X章：" 或 "第X章:" 前缀
  return title.replace(/^第[一二三四五六七八九十\d]+章[：:]\s*/, '');
};

// 计算剩余时间
const calculateRemainingTime = (endDateStr?: string): string => {
  if (!endDateStr) return 'N/A';
  const end = dayjs(endDateStr);
  const now = dayjs();
  const diff = end.diff(now, 'minute');

  if (diff <= 0) {
    return '已到期';
  }

  const days = Math.floor(diff / (24 * 60));
  const hours = Math.floor((diff % (24 * 60)) / 60);
  const minutes = diff % 60;

  let result = '';
  if (days > 0) result += `${days}天`;
  if (hours > 0) result += `${hours}小时`;
  if (minutes > 0 || (days === 0 && hours === 0)) result += `${minutes}分`;

  return result || '即将到期';
};

// 课程状态样式类
const getCourseStatusClass = (status: string) => {
  return COURSE_STATUS_CLASS[status] || '';
};

// 课程状态文本
const getCourseStatusText = (status: string) => {
  return COURSE_STATUS_TEXT[status] || '未知状态';
};

// 任务类型颜色
const getTaskTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'judge': 'blue',
    'choice': 'green',
    'practice': 'orange'
  };
  return colorMap[type] || 'default';
};

// 任务类型文本
const getTaskTypeText = (type: string) => {
  const textMap: Record<string, string> = {
    'judge': '判断题',
    'choice': '选择题',
    'practice': '实践题',
    'task': '实践题',
    'challenge': '挑战题',
    'experiment': '实验题'
  };
  return textMap[type?.toLowerCase()] || '实践题';
};

// 难度文本映射
const getDifficultyText = (difficulty: string | number) => {
  const textMap: Record<string, string> = {
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级',
    '1': '初级',
    '2': '中级',
    '3': '高级',
    '4': '专家',
    '5': '大师'
  };
  return textMap[String(difficulty)?.toLowerCase()] || '初级';
};

// 难度颜色
const getDifficultyColor = (difficulty: string) => {
  const colorMap: Record<string, string> = {
    'beginner': 'green',
    'intermediate': 'orange',
    'advanced': 'red',
    'BEGINNER': 'green',
    'INTERMEDIATE': 'orange',
    'ADVANCED': 'red'
  };
  return colorMap[difficulty] || 'blue';
};

// 将难度字符串转换为数字（用于星级评分）
const getDifficultyNumber = (difficulty: string | number): number => {
  if (typeof difficulty === 'number') return difficulty;
  const numMap: Record<string, number> = {
    'beginner': 1,
    'intermediate': 3,
    'advanced': 5,
    'BEGINNER': 1,
    'INTERMEDIATE': 3,
    'ADVANCED': 5
  };
  return numMap[difficulty] || 3;
};

// 跳转到挑战详情
const navigateToChallenge = (taskId: string) => {
  // 使用实际的 course.id（从 courseDetail 获取），而不是路由参数中的 classroom_course.id
  const actualCourseId = courseDetail.value?.id || courseId;
  // 在新标签页中打开（使用 hash 路由格式）
  const url = `/#/course/challenge/${actualCourseId}/${taskId}`;
  window.open(url, '_blank');
};

// 跳转到课程考核页面
const navigateToExam = () => {
  router.push(`/classroom/${classroomId}/course/${courseId}/exams`);
};

// 跳转到成绩管理页面
const goToGrading = () => {
  router.push({
    path: `/classroom/${classroomId}/course/${courseId}/grades`,
    query: {
      courseName: courseDetail.value?.title || '',
      courseId: (courseDetail.value as any)?.course_id,
      practiceId: (courseDetail.value as any)?.practice_id
    }
  });
};

// 跳转到考核管理页面
const goToExams = () => {
  router.push(`/classroom/${classroomId}/course/${courseId}/exam`);
};

// 计算技能标签点亮状态
const calculateSkillLighting = (tasks: any[], skills: any[]) => {
  if (!skills || skills.length === 0) {
    return skills;
  }

  // 获取已通关的任务ID列表
  const completedTaskIds = tasks
    .filter(task => task.completed)
    .map(task => task.id);

  // 获取已通关任务对应的技能标签
  const masteredSkills = new Set<string>();
  tasks.forEach(task => {
    if (completedTaskIds.includes(task.id) && task.skills) {
      task.skills.forEach((skill: string) => {
        masteredSkills.add(skill);
      });
    }
  });

  // 更新技能标签的点亮状态
  return skills.map(skill => ({
    ...skill,
    isLighted: masteredSkills.has(skill.name)
  }));
};

// 作业相关函数
const openHomeworkSubmitModal = (homework: any) => {
  currentHomework.value = homework;
  submitTabActiveKey.value = 'design';
  designFiles.value = [];
  homeworkForm.reportTitle = '';
  homeworkForm.reportContent = '';
  homeworkSubmitModalVisible.value = true;
};

const viewHomeworkSubmission = (homework: any) => {
  currentHomework.value = homework;
  // 这里应该获取学生的作业提交内容
  homeworkSubmission.value = {
    designFile: {
      name: '设计文件.fig',
      size: 2048000,
      uploadTime: new Date().toISOString(),
      previewUrl: 'https://picsum.photos/400/300?random=1'
    },
    report: {
      title: '实验报告标题',
      content: '<p>这是实验报告的内容...</p>'
    }
  };
  homeworkViewModalVisible.value = true;
};

const beforeUploadDesignFile = (file: File) => {
  const isValidType = ['image/jpeg', 'image/png', 'image/gif', 'application/fig'].includes(file.type);
  if (!isValidType) {
    message.error('只支持上传设计文件格式（FIG, PNG, JPG, GIF）');
    return false;
  }
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    message.error('文件大小不能超过10MB');
    return false;
  }
  return false; // 阻止自动上传，由用户手动提交
};

const handleDesignFileChange = (info: any) => {
  designFiles.value = info.fileList;
};

const submitHomework = async () => {
  if (!currentHomework.value) return;

  // 验证至少提交了设计文件或实验报告中的一项
  if (designFiles.value.length === 0 && (!homeworkForm.reportTitle || !homeworkForm.reportContent)) {
    message.error('请至少提交设计文件或实验报告');
    return;
  }

  submittingHomework.value = true;

  try {
    // 这里应该调用实际的API提交作业
    const formData = new FormData();
    formData.append('homework_id', currentHomework.value.id);
    formData.append('student_id', userStore.userInfo.id);

    if (designFiles.value.length > 0) {
      formData.append('design_file', designFiles.value[0].originFileObj);
    }

    if (homeworkForm.reportTitle && homeworkForm.reportContent) {
      formData.append('report_title', homeworkForm.reportTitle);
      formData.append('report_content', homeworkForm.reportContent);
    }

    // 上传文件并提交作业（无附件时仍需调用接口记录报告提交）
    const uploadFormData = new FormData();
    uploadFormData.append('homework_id', currentHomework.value.id);
    uploadFormData.append('student_id', userStore.userInfo.id);
    if (designFiles.value.length > 0) {
      uploadFormData.append('file', designFiles.value[0].originFileObj);
      uploadFormData.append('submission_type', 'design_file');
    } else {
      uploadFormData.append('submission_type', 'report');
    }
    const uploadResponse = await post('/api/v1/files/upload/homework-submission', uploadFormData);
    if (uploadResponse?.code !== '0000') {
      throw new Error(uploadResponse?.message || '提交失败');
    }

    // 检查是否为补交
    const isLate = currentHomework.value.deadline && new Date() > new Date(currentHomework.value.deadline);
    message.success(isLate ? '补交成功' : '提交成功');
    currentHomework.value.status = isLate ? 'late_submitted' : 'submitted';
    currentHomework.value.submittedAt = new Date().toISOString();
    homeworkSubmitModalVisible.value = false;
    fetchCourseDetail();

  } catch (error) {
    console.error('提交作业失败:', error);
    message.error('提交作业失败，请稍后重试');
  } finally {
    submittingHomework.value = false;
  }
};

const downloadFile = (file: any) => {
  // 这里应该调用下载API
  message.info('开始下载文件...');
};

// 作业状态相关函数
const getHomeworkStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'not_submitted': '未提交',
    'submitted': '已提交',
    'late_submitted': '已补交'
  };
  return statusMap[status] || '未知状态';
};

const getHomeworkStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'not_submitted': 'default',
    'submitted': 'green',
    'late_submitted': 'orange'
  };
  return colorMap[status] || 'default';
};

// 文件大小格式化
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 生成推荐实践
const generateRecommendations = async (courseDetail: ClassroomCourseDetail) => {
  try {
    // 模拟获取所有可用课程数据
    const allCourses = await getAllAvailableCourses();

    // 获取用户学习历史（这里简化处理，实际应该从用户数据中获取）
    const userHistory = getMockUserHistory();

    // 当前课程信息
    const currentCourse = {
      id: courseDetail.id,
      title: courseDetail.name,
      type: courseDetail.courseType,
      difficulty: getDifficultyFromTasks(courseDetail.tasks),
      direction: courseDetail.tasks?.[0]?.skills?.[0] || '通用',
      tags: courseDetail.tasks?.flatMap(task => task.skills || []) || [],
      skills: courseDetail.skills?.map(skill => skill.name) || []
    };

    // 生成混合推荐
    const recs = getHybridRecommendations(currentCourse, userHistory, allCourses, {
      maxRecommendations: 3
    });

    recommendations.value = recs;
  } catch (error) {
    console.error('生成推荐实践失败:', error);
    recommendations.value = [];
  }
};

// 获取所有可用课程（暂无推荐API，返回空数组）
const getAllAvailableCourses = async () => {
  return [];
};

// 获取用户学习历史（暂无推荐API，返回空数组）
const getMockUserHistory = () => {
  return [];
};

// 从任务中推断课程难度
const getDifficultyFromTasks = (tasks?: any[]) => {
  if (!tasks || tasks.length === 0) return 'beginner';

  const difficulties = tasks.map(task => task.difficulty || 1);
  const avgDifficulty = difficulties.reduce((sum, diff) => sum + diff, 0) / difficulties.length;

  if (avgDifficulty <= 1.5) return 'beginner';
  if (avgDifficulty <= 2.5) return 'intermediate';
  return 'advanced';
};

// 跳转到推荐课程
const goToRecommendedCourse = (courseId: string) => {
  // 这里应该跳转到推荐课程的详情页
  // 暂时只是显示提示
  message.info(`跳转到推荐课程: ${courseId}`);
};

// 格式化时间显示
const formatTimeAgo = (timestamp: string) => {
  const now = dayjs();
  const time = dayjs(timestamp);
  const diffMinutes = now.diff(time, 'minute');
  const diffHours = now.diff(time, 'hour');
  const diffDays = now.diff(time, 'day');

  if (diffMinutes < 1) return '刚刚';
  if (diffMinutes < 60) return `${diffMinutes}分钟前`;
  if (diffHours < 24) return `${diffHours}小时前`;
  if (diffDays < 7) return `${diffDays}天前`;

  return time.format('MM-DD HH:mm');
};

// 数据同步事件处理函数
const handleTaskCompleted = (event: any) => {
  console.log('[DataSync] 收到任务完成事件:', event);

  // 检查是否是当前课程的任务
  if (event.data.submission.courseId === courseId && event.data.submission.classroomId === classroomId) {
    // 重新获取课程详情以更新技能标签
    fetchCourseDetail();
    message.info('检测到其他页面完成任务，已更新技能状态');
  }
};

const handleSkillUpdated = (event: any) => {
  console.log('[DataSync] 收到技能更新事件:', event);

  // 检查技能是否属于当前课程
  if (courseDetail.value?.skills?.some(skill => skill.id === event.data.skillId)) {
    // 重新获取课程详情
    fetchCourseDetail();
  }
};

const handleCoinUpdated = (event: any) => {
  console.log('[DataSync] 收到金币更新事件:', event);

  // 更新金币显示（如果有的话）
  if (courseDetail.value) {
    // 这里可以更新金币显示逻辑
    console.log('金币已更新:', event.data);
  }
};

// 教师状态管理函数
const publishCourse = async () => {
  if (!courseDetail.value || !canTeacherChangeCourseStatus(userRole.value)) {
    message.error('没有权限执行此操作');
    return;
  }

  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/courses/${courseDetail.value.id}/publish`, {
      teacher_id: userStore.userInfo.id
    });
    if (response?.code !== '0000') {
      throw new Error(response?.message || '发布失败');
    }

    courseDetail.value.status = 'learning';
    message.success('课程发布成功');

    // 重新获取课程详情
    fetchCourseDetail();
  } catch (error: any) {
    console.error('发布课程失败:', error);
    message.error(error.message || '发布课程失败，请稍后重试');
  }
};

const unpublishCourse = async () => {
  if (!courseDetail.value || !canTeacherChangeCourseStatus(userRole.value)) {
    message.error('没有权限执行此操作');
    return;
  }

  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/courses/${courseDetail.value.id}/publish`, {
      teacher_id: userStore.userInfo.id,
      action: 'unpublish'
    });
    if (response?.code !== '0000') {
      throw new Error(response?.message || '取消发布失败');
    }

    courseDetail.value.status = 'unpublished';
    message.success('课程已取消发布');

    // 重新获取课程详情
    fetchCourseDetail();
  } catch (error: any) {
    console.error('取消发布课程失败:', error);
    message.error(error.message || '取消发布课程失败，请稍后重试');
  }
};

const refreshStatus = async () => {
  if (!courseDetail.value) return;

  message.loading('正在刷新状态...', 0.5);

  try {
    // 重新计算状态
    const calculatedStatus = calculateCourseStatus(courseDetail.value);
    const suggestions = getCourseStatusChangeSuggestions(courseDetail.value);

    // 如果状态需要更新，提示用户
    if (calculatedStatus !== courseDetail.value.status) {
      message.info(`建议状态更新为：${COURSE_STATUS_TEXT[calculatedStatus]}`);
    } else {
      message.success('状态已是最新');
    }

    // 重新获取课程详情
    fetchCourseDetail();
  } catch (error) {
    console.error('刷新状态失败:', error);
    message.error('刷新状态失败');
  }
};

// 获取课程详情
const fetchCourseDetail = async () => {
  loading.value = true;
  try {
    let result: ClassroomCourseDetail;
    
    // 根据用户角色获取不同的课程详情数据
    if (isStudent.value) {
      result = await getStudentClassroomCourseDetailById(
        classroomId, 
        courseId, 
        userStore.userInfo.id || 'default-student'
      );
    } else {
      result = await getClassroomCourseDetailById(classroomId, courseId, userStore.userInfo.id);
    }
    
    // 注意：技能标签点亮状态已由后端 API 正确计算并返回 (is_unlocked -> isLighted)
    // 不再需要前端重新计算，后端根据 task_evaluation_results 表中的通关记录来判断
    // 原代码: result.skills = calculateSkillLighting(result.tasks, result.skills);

    // 如果是教师视图，自动计算和建议状态更新
    if (isTeacher.value) {
      const statusSuggestions = getCourseStatusChangeSuggestions(result);
      result.calculatedStatus = statusSuggestions.autoStatus;
      result.statusSuggestions = statusSuggestions.suggestions;
      result.canPublish = statusSuggestions.canPublish;
      result.canUnpublish = statusSuggestions.canUnpublish;
    }

    // 格式化剩余时间
    result.formattedRemainingTime = formatRemainingTime(result);

    // 生成推荐实践
    await generateRecommendations(result);

    courseDetail.value = result;

    // 计算学习统计（仅学生视图，使用真实课程数据）
    if (isStudent.value) {
      learningStats.value = calculateLearningStatistics(
        userStore.userId || 'default-user',
        courseId,
        classroomId,
        result  // 传入真实课程详情数据
      );
    }

    // 默认展开第一个任务
    if (result.tasks && result.tasks.length > 0) {
      activeTaskKeys.value = [result.tasks[0].id];
    }
  } catch (error) {
    message.error('获取课程详情失败');
    console.error('Error fetching course detail:', error);
  } finally {
    loading.value = false;
  }
};

// 监听页面重新获得焦点事件，用于更新挑战完成后的数据
const handleWindowFocus = () => {
  if (isStudent.value && courseDetail.value) {
    // 重新获取课程详情以更新技能标签状态
    fetchCourseDetail();
  }
};

// 数据同步事件监听器
let taskCompletedUnlisten: (() => void) | null = null;
let skillUpdatedUnlisten: (() => void) | null = null;
let coinUpdatedUnlisten: (() => void) | null = null;

onMounted(() => {
  fetchCourseDetail();

  // 监听页面重新获得焦点事件
  window.addEventListener('focus', handleWindowFocus);

  // 监听数据同步事件（仅学生视图）
  if (isStudent.value) {
    taskCompletedUnlisten = dataSyncStore.onEvent(DataSyncEventType.TASK_COMPLETED, handleTaskCompleted);
    skillUpdatedUnlisten = dataSyncStore.onEvent(DataSyncEventType.SKILL_UPDATED, handleSkillUpdated);
    coinUpdatedUnlisten = dataSyncStore.onEvent(DataSyncEventType.COIN_UPDATED, handleCoinUpdated);
  }
});

// 组件卸载时移除事件监听器
onUnmounted(() => {
  window.removeEventListener('focus', handleWindowFocus);

  // 清理数据同步事件监听器
  if (taskCompletedUnlisten) taskCompletedUnlisten();
  if (skillUpdatedUnlisten) skillUpdatedUnlisten();
  if (coinUpdatedUnlisten) coinUpdatedUnlisten();
});
</script>

<style scoped>
.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.back-link {
  margin-bottom: 16px;
}

.course-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  margin-right: 12px;
}

.status-unpublished {
  background-color: #d9d9d9;
  color: #666;
}

.status-learning {
  background-color: #e6f7ff;
  color: #1890ff;
}

.status-makeup {
  background-color: #fff7e6;
  color: #fa8c16;
}

.status-completed {
  background-color: #f6ffed;
  color: #52c41a;
}

.course-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.course-coins {
  display: flex;
  align-items: center;
  font-size: 16px;
  color: #722ed1;
}

.course-coins .anticon {
  margin-right: 6px;
}

.info-card,
.tasks-card,
.progress-card,
.skills-card {
  margin-bottom: 24px;
}

.card-title {
  display: flex;
  align-items: center;
}

.card-title .anticon {
  margin-right: 8px;
  font-size: 16px;
}

.basic-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item .anticon {
  margin-right: 8px;
  color: #1890ff;
}

.student-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.student-learning {
  color: #1890ff;
}

.completed-count {
  color: #52c41a;
  font-weight: 500;
}

.student-not-started {
  color: #999;
}

.remaining-time {
  color: #fa8c16;
  font-weight: 500;
}

.classroom-info {
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.info-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 12px;
  color: #333;
}

.classroom-link {
  text-decoration: none;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  padding: 0 16px;
}

.progress-label {
  margin-bottom: 8px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.tasks-container {
  margin-top: 8px;
}

.task-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.task-info {
  flex: 1;
}

.task-meta {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.task-description {
  margin-bottom: 16px;
  color: #333;
  line-height: 1.6;
}

.task-skills {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.task-skills .label {
  font-weight: 500;
  color: #666;
}

.skills-container {
  padding: 16px 0;
}

.skills-header {
  margin-bottom: 12px;
  font-size: 14px;
  color: #666;
  text-align: right;
}

.skill-lighted {
  background-color: #fa8c16 !important;
  color: white !important;
  border-color: #fa8c16 !important;
}

.skill-unlighted {
  background-color: #f5f5f5 !important;
  color: #999 !important;
  border-color: #d9d9d9 !important;
}

@media (max-width: 768px) {
  .skills-container {
    padding: 12px 0;
  }

  .skills-container .ant-space {
    gap: 8px 8px !important;
  }

  .skills-container .ant-tag {
    font-size: 12px !important;
    padding: 4px 8px !important;
  }
}

@media (max-width: 768px) {
  .course-detail-container {
    padding: 16px;
  }

  .course-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .course-header .ant-card-body {
    padding: 16px;
  }

  .info-card .ant-card-body {
    padding: 16px;
  }

  .status-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .status-actions .ant-btn {
    width: 100%;
  }

  .homework-card .ant-card-body {
    padding: 16px;
  }

  .homework-submit-content {
    padding: 16px 0;
  }

  .task-content {
    flex-direction: column;
    gap: 16px;
  }

  .task-actions {
    align-self: flex-end;
  }
}

/* 作业相关样式 */
.homework-card {
  margin-bottom: 24px;
}

.homework-content {
  padding: 8px 0;
}

.homework-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.homework-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background-color: #fafafa;
}

.homework-info {
  flex: 1;
}

.homework-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #f3f4f6;
}

.homework-desc {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
  line-height: 1.5;
}

.homework-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.submit-time, .deadline {
  font-size: 12px;
  color: #9ca3af;
}

.homework-actions {
  margin-left: 16px;
}

.homework-submit-content {
  min-height: 400px;
}

.file-upload-section, .report-editor-section {
  padding: 16px 0;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.homework-view-content {
  min-height: 300px;
}

.design-file-view {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.file-info {
  flex: 1;
}

.report-view h3 {
  margin-bottom: 16px;
  color: #f3f4f6;
}

.report-content {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  min-height: 200px;
}

/* 状态管理卡片样式 */
.status-management-card {
  margin-bottom: 24px;
  border-left: 4px solid #faad14;
}

.status-management-card .card-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-suggestions {
  margin-bottom: 16px;
}

.status-actions {
  text-align: right;
}

/* 推荐实践样式 */
.recommendations-card {
  margin-bottom: 24px;
}

.recommendations-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recommendation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  background-color: #fafafa;
  cursor: pointer;
  transition: all 0.3s ease;
}

.recommendation-item:hover {
  background-color: #f0f8ff;
  border-color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.recommendation-content {
  flex: 1;
}

.recommendation-title {
  font-size: 14px;
  font-weight: 500;
  color: #f3f4f6;
  margin-bottom: 6px;
  line-height: 1.4;
}

.recommendation-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.recommendation-score {
  font-size: 12px;
  color: #52c41a;
  font-weight: 500;
}

.recommendation-reasons {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.reason-item {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.3;
}

.recommendation-arrow {
  color: #bfbfbf;
  font-size: 14px;
  transition: color 0.3s ease;
}

.recommendation-item:hover .recommendation-arrow {
  color: #1890ff;
}

/* 学习统计样式 */
.learning-stats-card {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.stat-section {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.stat-section.full-width {
  grid-column: 1 / -1;
}

.stat-section h4 {
  margin: 0 0 16px 0;
  color: #f3f4f6;
  font-size: 16px;
  font-weight: 500;
}

.stat-items {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
  line-height: 1.2;
}

.recent-activities {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.activity-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.activity-task_completion {
  background: #f6ffed;
  color: #52c41a;
}

.activity-coin_earned {
  background: #fff7e6;
  color: #faad14;
}

.activity-skill_unlocked {
  background: #f0f9ff;
  color: #1890ff;
}

.activity-session_start,
.activity-session_end {
  background: #f9f0ff;
  color: #722ed1;
}

.activity-content {
  flex: 1;
}

.activity-description {
  font-size: 14px;
  color: #f3f4f6;
  margin-bottom: 2px;
}

.activity-time {
  font-size: 12px;
  color: #6b7280;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .stat-items {
    grid-template-columns: repeat(3, 1fr);
  }

  .stat-value {
    font-size: 16px;
  }

  .stat-label {
    font-size: 11px;
  }
}
</style> 
