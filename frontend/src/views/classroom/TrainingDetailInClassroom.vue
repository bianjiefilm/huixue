<template>
  <PageShell max-width="wide" class="training-detail-page">
    <a-spin :spinning="loading" tip="加载中...">
      <PageHeaderBar
        v-if="training"
        :title="training.title"
        :subtitle="headerSubtitle"
        show-back
        :back-to="`/classroom/${classroomId}`"
      >
        <template #actions>
          <a-button type="primary" size="large" @click="launchTraining" :loading="launching">
            {{ isTeacher ? '👁️ 查看实训' : '🚀 开启实训' }}
          </a-button>
        </template>
      </PageHeaderBar>

      <!-- 顶部项目数据看板 (学生端个人看板) -->
      <div class="project-dashboard student-dashboard" v-if="training && !isTeacher">
        <div class="dashboard-header" v-if="training.coin">
          <div class="project-coin">
            <span class="coin-icon">🪙</span>
            <span>{{ training.coin }}</span>
          </div>
        </div>

        <div class="dashboard-stats">
          <div class="stat-item">
            <span class="stat-label">我的学习时长</span>
            <span class="stat-value primary">{{ myLearningDuration }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">完成进度</span>
            <span class="stat-value success">{{ studentProgress.completedPercentage || 0 }}%</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">学习状态</span>
            <span class="stat-value">{{ getStatusText(studentProgress.status) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">难易程度</span>
            <span class="stat-value">{{ getDifficultyText(training.difficulty) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">所属行业</span>
            <span class="stat-value">{{ training.industry || '其他' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">模式</span>
            <span class="stat-value">{{ getTrainingModeText(training.training_type) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">工具</span>
            <span class="stat-value">{{ getToolName(training.training_type) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">起止时间</span>
            <span class="stat-value">{{ formatDateRange(classroomInfo.start_date, classroomInfo.end_date) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">剩余时间</span>
            <span class="stat-value countdown" :class="{ expired: isExpired }">{{ remainingTimeText }}</span>
          </div>
        </div>
      </div>

      <!-- 顶部项目数据看板 (教师端专属) -->
      <div class="project-dashboard" v-if="training && isTeacher">
        <div class="dashboard-header" v-if="training.coin">
          <div class="project-coin">
            <span class="coin-icon">🪙</span>
            <span>{{ training.coin }}</span>
          </div>
        </div>

        <div class="dashboard-stats">
          <div class="stat-item">
            <span class="stat-label">学习中</span>
            <span class="stat-value primary">{{ classroomStats.learning || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已完成</span>
            <span class="stat-value success">{{ classroomStats.completed || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">未开始</span>
            <span class="stat-value">{{ classroomStats.not_started || 0 }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">难易程度</span>
            <span class="stat-value">{{ getDifficultyText(training.difficulty) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">所属行业</span>
            <span class="stat-value">{{ training.industry || '其他' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">模式</span>
            <span class="stat-value">{{ getTrainingModeText(training.training_type) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">工具</span>
            <span class="stat-value">{{ getToolName(training.training_type) }}</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-label">起止时间</span>
            <span class="stat-value">{{ formatDateRange(classroomInfo.start_date, classroomInfo.end_date) }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">学习剩余时间</span>
            <span class="stat-value countdown">{{ remainingTimeText }}</span>
          </div>
        </div>
      </div>

      <a-row :gutter="16" v-if="training">
        <!-- 左侧：手册内容 -->
        <a-col :xs="24" :lg="16">
          <div class="handbook-section">
            <a-card class="handbook-card">
              <template #title>
                📄 实训手册
              </template>

              <!-- 手册内容渲染 -->
              <div class="handbook-content" ref="handbookRef">
                <div v-html="renderedHandbookContent" class="markdown-body"></div>
              </div>
            </a-card>
          </div>
        </a-col>

        <!-- 右侧：操作面板 -->
        <a-col :xs="24" :lg="8">
          <!-- 学生端专属：提交作业按钮（次要 CTA，主 CTA 在页头） -->
          <div
            class="action-buttons"
            v-if="!isTeacher && studentProgress.status === 'in_progress'"
          >
            <a-button
              size="large"
              block
              @click="openSubmitModal"
              :loading="submitting"
            >
              ⬆️ 提交作业
            </a-button>
          </div>

          <!-- 所属课堂卡片 -->
          <a-card class="classroom-card" v-if="classroomInfo.name">
            <template #title>📚 所属课堂</template>
            <div class="classroom-link">
              <router-link :to="`/classroom/${classroomId}`">
                <div class="classroom-item">
                  <div class="classroom-cover-gradient"></div>
                  <div class="classroom-info">
                    <span class="classroom-name">{{ classroomInfo.name }}</span>
                    <span class="classroom-teacher">👨‍🏫 {{ classroomInfo.teacher_name || '教师' }}</span>
                  </div>
                </div>
              </router-link>
            </div>
          </a-card>

          <!-- 目录章节导航树 -->
          <a-card class="toc-card" v-if="tocItems.length > 0">
            <template #title>📑 目录章节</template>
            <div class="toc-list">
              <div
                v-for="item in tocItems"
                :key="item.id"
                :class="['toc-item', `level-${item.level}`, { active: activeTocId === item.id }]"
                @click="scrollToHeading(item.id)"
              >
                {{ item.text }}
              </div>
            </div>
          </a-card>

          <!-- 学生端专属：作业列表卡片 -->
          <a-card class="assignments-card" v-if="!isTeacher">
            <template #title><FileTextOutlined /> 作业列表</template>
            <template #extra>
              <a-button
                size="small"
                @click="openSubmitModal"
                :disabled="!canSubmitAssignment"
              >提交作业</a-button>
            </template>

            <!-- 空状态 -->
            <div v-if="assignments.length === 0" class="empty-assignments">
              <div style="text-align: center; color: #8c8c8c; padding: 20px 0;">暂无提交作业</div>
            </div>

            <!-- 作业列表 -->
            <div v-else class="assignments-list">
              <div
                v-for="assignment in assignments"
                :key="assignment.id"
                class="assignment-item"
                :class="{ 'graded': assignment.status === 'graded' }"
              >
                <div class="assignment-header">
                  <span class="assignment-title">{{ assignment.title || '作业提交' }}</span>
                  <span class="assignment-status" :class="assignment.status">
                    {{ getAssignmentStatusText(assignment.status) }}
                  </span>
                </div>
                <div class="assignment-meta">
                  <span class="submit-time" v-if="assignment.submit_time">
                    提交时间：{{ formatDateTime(assignment.submit_time) }}
                  </span>
                  <span class="score" v-if="assignment.score !== null">
                    得分：{{ assignment.score }}分
                  </span>
                </div>
                <div class="assignment-files" v-if="assignment.files && assignment.files.length > 0">
                  <a-tag v-for="file in assignment.files" :key="file.id" color="blue">
                    📎 {{ file.name }}
                  </a-tag>
                </div>
              </div>
            </div>

            <!-- 提交作业区域移至右上角 extra -->
            <div class="submit-section" v-if="isExpired || hasGradedAssignment">
              <p class="submit-tip" v-if="isExpired" style="text-align: center; color: #ff4d4f;">已超过截止时间，无法提交</p>
              <p class="submit-tip" v-else-if="hasGradedAssignment" style="text-align: center; color: #faad14;">已评分的作业无法重新提交</p>
            </div>
          </a-card>

          <!-- 学生端专属：进度卡片 -->
          <a-card class="progress-card" v-if="!isTeacher">
            <template #title>📊 学习进度</template>

            <div class="progress-content">
              <div class="progress-stat">
                <span class="label">完成度</span>
                <div class="progress-bar">
                  <a-progress :percent="studentProgress.completedPercentage || 0" />
                </div>
              </div>

              <div class="progress-stat">
                <span class="label">状态</span>
                <span class="status-badge">{{ getStatusText(studentProgress.status) }}</span>
              </div>
            </div>
          </a-card>

          <!-- 任务卡片 -->
          <a-card class="tasks-card" v-if="tasks.length > 0">
            <template #title>✓ 课程任务</template>

            <div class="tasks-list">
              <div v-for="(task, index) in tasks" :key="task.id" class="task-item">
                <div class="task-header">
                  <span class="task-number">{{ index + 1 }}</span>
                  <span class="task-title">{{ task.title }}</span>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 基本信息（学生端） -->
          <a-card class="info-card" v-if="!isTeacher">
            <template #title>ℹ️ 基本信息</template>

            <div class="info-list">
              <div class="info-item" v-if="training.difficulty">
                <span class="label">难度</span>
                <span class="value">{{ getDifficultyText(training.difficulty) }}</span>
              </div>
              <div class="info-item" v-if="training.industry">
                <span class="label">行业</span>
                <span class="value">{{ training.industry }}</span>
              </div>
              <div class="info-item" v-if="training.course_hours">
                <span class="label">时长</span>
                <span class="value">{{ training.course_hours }} 小时</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 404 状态 -->
      <a-empty v-else description="实训不存在或已删除" />
    </a-spin>

    <!-- 提交作业弹窗 -->
    <a-modal
      v-model:open="submitModalVisible"
      title="📤 提交作业"
      :confirm-loading="submitting"
      @ok="handleSubmitAssignment"
      @cancel="closeSubmitModal"
      width="520px"
    >
      <a-form layout="vertical" class="submit-form">
        <a-form-item label="作业文件" required>
          <a-upload
            v-model:file-list="uploadFileList"
            :before-upload="beforeUpload"
            :max-count="5"
            multiple
          >
            <a-button>
              <upload-outlined />
              选择文件上传
            </a-button>
          </a-upload>
          <p class="upload-tip">支持上传多个文件，单个文件不超过50MB</p>
        </a-form-item>

        <a-form-item label="作业备注">
          <a-textarea
            v-model:value="submitNotes"
            placeholder="请输入作业备注或说明（可选）"
            :rows="4"
            :maxlength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { UploadOutlined, FileTextOutlined } from '@ant-design/icons-vue';
import type { UploadProps } from 'ant-design-vue';
import MarkdownIt from 'markdown-it';
import { useUserStore } from '@/stores/user';
import request from '@/utils/request';
import { getToken } from '@/utils/auth';
import { launchClassroomTraining } from '@/api/training';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

// 路由和状态
const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const classroomId = computed(() => parseInt(route.params.classroomId as string));
const trainingId = computed(() => parseInt(route.params.trainingId as string));

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再访问实训详情');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};
const classroomName = ref('');
const loading = ref(false);
const launching = ref(false);
const submitting = ref(false);

// 判断是否为教师
const isTeacher = computed(() => userStore.userRole === 'teacher');

const headerSubtitle = computed(() => {
  const room = classroomInfo.value.name || classroomName.value;
  if (!room) return '课堂实训';
  return `所属课堂 · ${room}`;
});

// 数据
const training = ref<any>(null);
const tasks = ref<any[]>([]);
const studentProgress = ref({
  status: 'not_started',
  completedPercentage: 0,
  lastActivity: null,
});

// 课堂信息和统计（教师端用）
const classroomInfo = ref<{
  name: string;
  cover?: string;
  teacher_name?: string;
  start_date?: string;
  end_date?: string;
}>({ name: '' });

const classroomStats = ref<{
  learning: number;
  completed: number;
  not_started: number;
}>({
  learning: 0,
  completed: 0,
  not_started: 0,
});

// 作业相关数据
const assignments = ref<any[]>([]);
const submitModalVisible = ref(false);
const uploadFileList = ref<any[]>([]);
const submitNotes = ref('');

// 学生个人学习时长
const myLearningDuration = ref('0小时0分');

// 是否已超时
const isExpired = computed(() => {
  if (!classroomInfo.value.end_date) return false;
  return new Date() > new Date(classroomInfo.value.end_date);
});

// 是否有已评分的作业
const hasGradedAssignment = computed(() => {
  return assignments.value.some(a => a.status === 'graded');
});

// 是否可以提交作业
const canSubmitAssignment = computed(() => {
  // 未超时、未评分、已开始学习
  return !isExpired.value && !hasGradedAssignment.value && studentProgress.value.status !== 'not_started';
});

// 提交按钮文字
const submitButtonText = computed(() => {
  if (isExpired.value) return '已超时';
  if (hasGradedAssignment.value) return '已评分';
  if (studentProgress.value.status === 'not_started') return '请先开始学习';
  return '⬆️ 提交作业';
});

// 剩余时间倒计时
const remainingTimeText = ref('计算中...');
let remainingTimeInterval: any = null;

// 目录导航相关
const handbookRef = ref<HTMLElement | null>(null);
const tocItems = ref<{ id: string; text: string; level: number }[]>([]);
const activeTocId = ref('');

// Markdown 渲染器配置 - 为标题添加ID
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

// 自定义标题渲染，添加ID
md.renderer.rules.heading_open = (tokens, idx) => {
  const token = tokens[idx];
  const level = token.tag.slice(1);
  const nextToken = tokens[idx + 1];
  const text = nextToken?.content || '';
  const id = `heading-${encodeURIComponent(text.replace(/\s+/g, '-').toLowerCase())}`;
  return `<${token.tag} id="${id}">`;
};

const renderedHandbookContent = computed(() => {
  if (!training.value?.handbookContent) return '';
  return md.render(training.value.handbookContent);
});

// 从Markdown内容提取目录
function extractTocItems(markdown: string) {
  const headingRegex = /^(#{1,3})\s+(.+)$/gm;
  const items: { id: string; text: string; level: number }[] = [];
  let match;

  while ((match = headingRegex.exec(markdown)) !== null) {
    const level = match[1].length;
    const text = match[2].trim();
    const id = `heading-${encodeURIComponent(text.replace(/\s+/g, '-').toLowerCase())}`;
    items.push({ id, text, level });
  }

  return items;
}

// 滚动到指定标题
function scrollToHeading(id: string) {
  const element = document.getElementById(id);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    activeTocId.value = id;
  }
}

// 监听滚动，更新当前激活的目录项
let scrollHandler: (() => void) | null = null;

function setupScrollListener() {
  scrollHandler = () => {
    if (!handbookRef.value || tocItems.value.length === 0) return;

    const headings = tocItems.value.map(item => document.getElementById(item.id)).filter(Boolean);
    const scrollTop = window.scrollY + 100;

    for (let i = headings.length - 1; i >= 0; i--) {
      const heading = headings[i];
      if (heading && heading.offsetTop <= scrollTop) {
        activeTocId.value = tocItems.value[i].id;
        return;
      }
    }

    if (tocItems.value.length > 0) {
      activeTocId.value = tocItems.value[0].id;
    }
  };

  window.addEventListener('scroll', scrollHandler);
}

// 监听内容变化，更新目录
watch(() => training.value?.handbookContent, (newContent) => {
  if (newContent) {
    tocItems.value = extractTocItems(newContent);
    nextTick(() => {
      if (tocItems.value.length > 0) {
        activeTocId.value = tocItems.value[0].id;
      }
    });
  }
}, { immediate: true });

// 获取实训详情
async function fetchTrainingDetail() {
  loading.value = true;
  try {
    const paramName = userStore.userRole === 'teacher' ? 'teacher_id' : 'student_id';
    const paramValue = requireCurrentUserId();
    const url = `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/details?${paramName}=${paramValue}`;

    const response = await fetch(url);
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      training.value = {
        ...result.data,
        handbookContent: result.data.handbook_content || ''
      };
      tasks.value = result.data.tasks || [];
      studentProgress.value = result.data.progress || {
        status: 'not_started',
        completedPercentage: 0,
        lastActivity: null
      };

      // 设置课堂信息
      if (result.data.classroom) {
        classroomInfo.value = {
          name: result.data.classroom.name || '',
          cover: result.data.classroom.cover,
          teacher_name: result.data.classroom.teacher_name,
          start_date: result.data.classroom.start_date,
          end_date: result.data.classroom.end_date
        };
        classroomName.value = result.data.classroom.name || '';

        // 计算剩余时间
        calculateRemainingTime(result.data.classroom.end_date);
      }

      // 设置学习统计（教师端用）
      if (result.data.stats) {
        classroomStats.value = {
          learning: result.data.stats.learning || 0,
          completed: result.data.stats.completed || 0,
          not_started: result.data.stats.not_started || 0
        };
      }
    } else {
      console.error('API error:', result);
      message.error(result.message || '加载实训详情失败');
    }
  } catch (error) {
    console.error('获取实训详情失败:', error);
    message.error('加载实训详情失败');
  } finally {
    loading.value = false;
  }
}

// 获取课堂基础信息（如果API没有返回）
async function fetchClassroomInfo() {
  try {
    const response = await fetch(`/api/v1/classrooms/${classroomId.value}`);
    const result = await response.json();
    if (result.code === '0000' && result.data) {
      classroomInfo.value = {
        name: result.data.name || '',
        cover: result.data.cover_url,
        teacher_name: result.data.teacher_name,
        start_date: result.data.start_date,
        end_date: result.data.end_date
      };
      classroomName.value = result.data.name || '';
      calculateRemainingTime(result.data.end_date);
    }
  } catch (error) {
    console.error('获取课堂信息失败:', error);
  }
}

// 开启实训
async function launchTraining() {
  launching.value = true;
  try {
    const trainingType = training.value?.training_type || 'DRAG_DROP';
    
    // 调用统一封装的API层纯函数
    const result = await launchClassroomTraining(
      trainingId.value,
      classroomId.value,
      trainingType,
      requireCurrentUserId()
    );

    if (result.code === '0000') {
      if (trainingType === 'DATA_ANALYSIS' || trainingType === 'DRAG_DROP' || trainingType === 'BI') {
        // BI类型：跳转本站 BI 设计器，课堂上下文下支持保存草稿
        const routeUrl = router.resolve(`/classroom/${classroomId.value}/training/${trainingId.value}/bi-designer`).href;
        window.open(routeUrl, '_blank');
        message.success('实训数据加载成功，即将进入分析台');
      } else if (result.data?.url) {
        // CODING/JUPYTER类型：打开外部环境URL
        window.open(result.data.url, '_blank');
        message.success('实训环境已启动');
      } else {
        // 兜底逻辑
        message.success('实训环境准备就绪');
      }
      // 更新前端状态
      studentProgress.value.status = 'in_progress';
      // 刷新页面数据以获取最新状态
      await fetchTrainingDetail();
    } else {
      message.error(result.message || '启动实训失败');
    }
  } catch (error) {
    console.error('启动实训失败:', error);
    message.error('启动实训失败');
  } finally {
    launching.value = false;
  }
}

// 打开提交作业弹窗
function openSubmitModal() {
  if (!canSubmitAssignment.value) {
    return;
  }
  submitModalVisible.value = true;
  uploadFileList.value = [];
  submitNotes.value = '';
}

// 关闭提交作业弹窗
function closeSubmitModal() {
  submitModalVisible.value = false;
  uploadFileList.value = [];
  submitNotes.value = '';
}

// 上传前校验
const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isLt50M = file.size / 1024 / 1024 < 50;
  if (!isLt50M) {
    message.error('文件大小不能超过50MB');
    return false;
  }
  return false; // 阻止自动上传，手动处理
};

// 提交作业（弹窗方式）
async function handleSubmitAssignment() {
  if (uploadFileList.value.length === 0) {
    message.warning('请选择至少一个文件');
    return;
  }

  submitting.value = true;
  try {
    // 构建FormData用于文件上传
    const formData = new FormData();
    formData.append('training_id', trainingId.value.toString());
    formData.append('classroom_id', classroomId.value.toString());
    formData.append('notes', submitNotes.value);

    uploadFileList.value.forEach(file => {
      formData.append('files', file.originFileObj || file);
    });

    const url = `/api/v1/trainings/${trainingId.value}/submit-assignment`;
    // 获取token并添加到请求头
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData
    });

    const result = await response.json();
    if (result.code === '0000') {
      message.success('作业提交成功！');
      submitModalVisible.value = false;
      // 刷新作业列表
      await fetchAssignments();
    } else {
      message.error(result.message || '提交作业失败');
    }
  } catch (error) {
    console.error('提交作业失败:', error);
    message.error('提交作业失败');
  } finally {
    submitting.value = false;
  }
}

// 获取作业列表
async function fetchAssignments() {
  try {
    const url = `/api/v1/trainings/${trainingId.value}/assignments?student_id=${userStore.userId}&classroom_id=${classroomId.value}`;
    // 获取token并添加到请求头
    const token = getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, { headers });
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      assignments.value = result.data;
    }
  } catch (error) {
    console.error('获取作业列表失败:', error);
  }
}

// 获取作业状态文字
function getAssignmentStatusText(status: string) {
  const texts: any = {
    'pending': '待批改',
    'graded': '已评分',
    'submitted': '已提交'
  };
  return texts[status] || status;
}

// 格式化日期时间
function formatDateTime(dateStr: string) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

// 旧的简单提交作业函数（保留作备用）
async function submitAssignment() {
  submitting.value = true;
  try {
    const url = `/api/v1/trainings/${trainingId.value}/submit`;
    // 获取token并添加到请求头
    const token = getToken();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        classroom_training_id: trainingId.value,
        notes: '作业提交'
      })
    });

    const result = await response.json();
    if (result.code === '0000') {
      message.success('作业已提交');
      studentProgress.value.status = 'completed';
      studentProgress.value.completedPercentage = 100;
    } else {
      message.error('提交作业失败');
    }
  } catch (error) {
    console.error('提交作业失败:', error);
    message.error('提交作业失败');
  } finally {
    submitting.value = false;
  }
}

// 工具函数
function getDifficultyText(difficulty: string) {
  const texts: any = {
    easy: '初级', beginner: '初级',
    medium: '中级', intermediate: '中级',
    hard: '高级', advanced: '高级'
  };
  return texts[difficulty?.toLowerCase()] || difficulty || '中级';
}

function getStatusText(status: string) {
  const texts: any = { not_started: '未开始', in_progress: '进行中', completed: '已完成' };
  return texts[status] || status;
}

// 获取实训模式文本
function getTrainingModeText(trainingType: string) {
  const modeTexts: any = {
    'DRAG_DROP': '拖拽式',
    'DATA_ANALYSIS': '拖拽式',
    'BI': '拖拽式',
    'CODING': '编码式',
    'JUPYTER': '编码式',  // JUPYTER类型也是编码式
    'MIXED': '混合式'
  };
  return modeTexts[trainingType] || '拖拽式';
}

// 获取工具名称
function getToolName(trainingType: string) {
  const toolNames: any = {
    'DRAG_DROP': 'TempoBI',
    'DATA_ANALYSIS': 'TempoBI',
    'BI': 'TempoBI',
    'CODING': 'Jupyter',
    'JUPYTER': 'Jupyter',  // JUPYTER类型使用Jupyter工具
    'MIXED': 'TempoBI/Jupyter'
  };
  return toolNames[trainingType] || 'TempoBI';
}

// 格式化日期范围
function formatDateRange(startDate?: string, endDate?: string) {
  if (!startDate || !endDate) return '未设置';
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };
  return `${formatDate(startDate)} — ${formatDate(endDate)}`;
}

// 计算剩余时间
function calculateRemainingTime(endDate?: string) {
  if (!endDate) {
    remainingTimeText.value = '未设置截止时间';
    return;
  }

  const updateTime = () => {
    const now = new Date().getTime();
    const end = new Date(endDate).getTime();
    const diff = end - now;

    if (diff <= 0) {
      remainingTimeText.value = '已结束';
      if (remainingTimeInterval) {
        clearInterval(remainingTimeInterval);
      }
      return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    remainingTimeText.value = `${days}天${hours}小时${minutes}分${seconds}秒`;
  };

  updateTime();
  remainingTimeInterval = setInterval(updateTime, 1000); // 每一秒更新一次
}

// 生命周期
onMounted(async () => {
  await fetchTrainingDetail();
  // 如果API没有返回课堂信息，单独获取
  if (!classroomInfo.value.name) {
    await fetchClassroomInfo();
  }
  // 学生端：获取作业列表
  if (!isTeacher.value) {
    await fetchAssignments();
  }
  setupScrollListener();
});

onUnmounted(() => {
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler);
  }
  // 清理倒计时
  if (remainingTimeInterval) {
    clearInterval(remainingTimeInterval);
  }
});
</script>

<style scoped lang="less">
.training-detail-page {
  // 顶部项目数据看板（教师端）
  .project-dashboard {
    background: linear-gradient(135deg, var(--hx-color-primary) 0%, #096dd9 100%);
    border-radius: var(--hx-radius-md, 8px);
    padding: var(--hx-space-5);
    margin-bottom: var(--hx-space-5);
    color: white;

    .dashboard-header {
      display: flex;
      justify-content: flex-end;
      align-items: center;
      margin-bottom: var(--hx-space-4);

      .project-coin {
        display: flex;
        align-items: center;
        gap: var(--hx-space-2);
        background: rgba(255, 255, 255, 0.2);
        padding: var(--hx-space-1) var(--hx-space-4);
        border-radius: 20px;
        font-size: var(--hx-font-size-base);
        font-weight: 500;

        .coin-icon {
          font-size: 18px;
        }
      }
    }

    .dashboard-stats {
      display: flex;
      flex-wrap: wrap;
      gap: var(--hx-space-5);
      align-items: center;

      .stat-item {
        display: flex;
        flex-direction: column;
        gap: var(--hx-space-1);

        .stat-label {
          font-size: 12px;
          opacity: 0.85;
        }

        .stat-value {
          font-size: 16px;
          font-weight: 600;

          &.primary {
            color: #52c41a;
          }

          &.success {
            color: #52c41a;
          }

          &.countdown {
            color: #ffc53d;
          }
        }
      }

      .stat-divider {
        width: 1px;
        height: 40px;
        background: rgba(255, 255, 255, 0.3);
      }
    }
  }

  // 所属课堂卡片
  .classroom-card {
    margin-bottom: var(--hx-space-4);
    background: var(--hx-color-bg-container);

    .classroom-link {
      a {
        text-decoration: none;
        color: inherit;
      }

      .classroom-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px;
        border-radius: 8px;
        transition: background 0.2s;

        &:hover {
          background: #f5f5f5;
        }

        .classroom-cover-gradient {
          width: 48px;
          height: 48px;
          border-radius: 6px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          flex-shrink: 0;
        }

        .classroom-info {
          display: flex;
          flex-direction: column;
          gap: 4px;

          .classroom-name {
            font-weight: 600;
            color: #262626;
            font-size: 14px;
          }

          .classroom-teacher {
            font-size: 12px;
            color: #8c8c8c;
          }
        }
      }
    }
  }

  // 目录导航样式
  .toc-card {
    background: var(--hx-color-bg-container);
    max-height: calc(100vh - 120px);
    overflow-y: auto;

    .toc-list {
      .toc-item {
        padding: var(--hx-space-2) var(--hx-space-3);
        cursor: pointer;
        border-radius: 4px;
        margin-bottom: var(--hx-space-1);
        font-size: 13px;
        color: var(--hx-color-text-secondary);
        transition: all 0.2s;
        border-left: 2px solid transparent;

        &:hover {
          background: #f0f5ff;
          color: var(--hx-color-primary);
        }

        &.active {
          background: #e6f7ff;
          color: var(--hx-color-primary);
          border-left-color: var(--hx-color-primary);
          font-weight: 500;
        }

        &.level-1 {
          padding-left: var(--hx-space-3);
          font-weight: 500;
        }

        &.level-2 {
          padding-left: var(--hx-space-5);
        }

        &.level-3 {
          padding-left: 36px;
          font-size: 12px;
        }
      }
    }
  }

  .handbook-section {
    .handbook-card {
      background: var(--hx-color-bg-container);
      margin-bottom: var(--hx-space-5);

      .handbook-content {
        :deep(.markdown-body) {
          h2, h3 {
            margin-top: 24px;
            margin-bottom: 12px;
            color: #262626;
          }

          p {
            line-height: 1.8;
            color: #595959;
            margin-bottom: 12px;
          }

          ul, ol {
            padding-left: 24px;
            margin-bottom: 12px;

            li {
              line-height: 1.8;
              color: #595959;
              margin-bottom: 8px;
            }
          }

          code {
            background: #f5f5f5;
            padding: 2px 6px;
            border-radius: 3px;
          }

          pre {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 4px;
            overflow-x: auto;
          }
        }
      }
    }
  }

  .progress-card,
  .tasks-card,
  .info-card {
    margin-bottom: var(--hx-space-4);
    background: var(--hx-color-bg-container);

    .progress-stat {
      margin-bottom: var(--hx-space-4);
      display: flex;
      flex-direction: column;

      .label {
        font-weight: 600;
        color: var(--hx-color-text-primary);
        margin-bottom: var(--hx-space-2);
        font-size: 14px;
      }

      .status-badge {
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        background: #e6f7ff;
        color: var(--hx-color-primary);
      }
    }

    .tasks-list {
      .task-item {
        padding: var(--hx-space-3);
        margin-bottom: var(--hx-space-3);
        background: var(--hx-color-bg-layout);
        border-left: 3px solid var(--hx-color-primary);
        border-radius: 4px;

        .task-header {
          display: flex;
          align-items: center;
          gap: var(--hx-space-2);

          .task-number {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            background: var(--hx-color-primary);
            color: white;
            border-radius: 50%;
            font-size: 12px;
            font-weight: 600;
          }

          .task-title {
            font-weight: 600;
            color: var(--hx-color-text-primary);
          }
        }
      }
    }

    .info-list {
      .info-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: var(--hx-space-2) 0;
        border-bottom: 1px solid var(--hx-color-border-muted);

        .label {
          font-weight: 600;
          color: var(--hx-color-text-tertiary);
          font-size: 12px;
        }

        .value {
          color: var(--hx-color-text-primary);
          font-size: 12px;
        }

        &:last-child {
          border-bottom: none;
        }
      }
    }
  }

  .action-buttons {
    margin-bottom: var(--hx-space-4);

    :deep(.ant-btn) {
      height: 40px;
      font-size: 14px;
    }
  }

  // 学生端个人看板样式
  .student-dashboard {
    background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);

    .stat-value.countdown.expired {
      color: #ff4d4f;
    }
  }

  // 作业列表卡片
  .assignments-card {
    margin-bottom: var(--hx-space-4);
    background: var(--hx-color-bg-container);

    .empty-assignments {
      padding: var(--hx-space-5) 0;
      text-align: center;

      .empty-tip {
        color: var(--hx-color-text-tertiary);
        font-size: 12px;
        margin-top: var(--hx-space-2);
      }
    }

    .assignments-list {
      .assignment-item {
        padding: var(--hx-space-3);
        margin-bottom: var(--hx-space-3);
        background: var(--hx-color-bg-layout);
        border-radius: 6px;
        border-left: 3px solid var(--hx-color-primary);

        &.graded {
          border-left-color: #52c41a;
        }

        .assignment-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: var(--hx-space-2);

          .assignment-title {
            font-weight: 600;
            color: var(--hx-color-text-primary);
          }

          .assignment-status {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;

            &.pending, &.submitted {
              background: #fff7e6;
              color: #fa8c16;
            }

            &.graded {
              background: #f6ffed;
              color: #52c41a;
            }
          }
        }

        .assignment-meta {
          display: flex;
          gap: var(--hx-space-4);
          font-size: 12px;
          color: var(--hx-color-text-tertiary);
        }

        .assignment-files {
          margin-top: var(--hx-space-2);
        }
      }
    }

    .submit-section {
      margin-top: var(--hx-space-4);
      padding-top: var(--hx-space-4);
      border-top: 1px solid var(--hx-color-border-muted);

      .submit-tip {
        font-size: 12px;
        color: #ff4d4f;
        margin-top: var(--hx-space-2);
        text-align: center;
      }
    }
  }

  // 提交作业弹窗
  .submit-form {
    .upload-tip {
      font-size: 12px;
      color: #8c8c8c;
      margin-top: 8px;
    }
  }
}
</style>
