<template>
  <div class="classroom-detail-page copilot-theme">
    <!-- Integrated Workspace Mode -->
    <div v-if="isWorkspaceActive" class="integrated-workspace">
      <!-- Workspace Header -->
      <div class="workspace-header">
        <div class="left-section">
          <a-button @click="exitWorkspace" type="text">
            <template #icon><ArrowLeftOutlined /></template>
            返回课堂
          </a-button>
          <span class="divider">|</span>
          <span class="workspace-title">{{ currentTrainingTitle }}</span>
        </div>
        <div class="right-section">
          <span v-if="trainingSubmissionStatus === 'submitted'" class="status-tag success">
            <CheckCircleOutlined /> 已提交
          </span>
          <span v-else-if="trainingSubmissionStatus === 'graded'" class="status-tag graded">
             已评分: {{ trainingScore }}分
          </span>
          
          <a-button 
            type="primary" 
            @click="submitAssignment" 
            :loading="submitting"
            :disabled="trainingSubmissionStatus === 'submitted' || trainingSubmissionStatus === 'graded'"
          >
            {{ trainingSubmissionStatus === 'submitted' ? '已提交' : (trainingSubmissionStatus === 'graded' ? '已评分' : '提交作业') }}
          </a-button>
        </div>
      </div>

      <!-- Workspace Body -->
      <div class="workspace-body">
        <!-- Left Panel: Handbook -->
        <div class="workspace-panel left-panel">
          <div class="panel-header">实训手册</div>
          <div class="panel-content markdown-body" v-html="renderedHandbook"></div>
        </div>

        <!-- Right Panel: BI Tool or Jupyter -->
        <div class="workspace-panel right-panel">
          <div class="panel-header">
             <div class="header-title">
               {{ ['CODING', 'JUPYTER'].includes(currentTrainingType) ? 'Jupyter 工作台' : '分析工作台' }}
             </div>
          </div>
          <div class="panel-content bi-container-wrapper">
             <!-- Jupyter/CODING Mode -->
             <div v-if="['CODING', 'JUPYTER'].includes(currentTrainingType)" class="jupyter-container">
               <div v-if="jupyterUrl" class="jupyter-frame-wrapper">
                 <iframe 
                   :src="jupyterUrl" 
                   class="jupyter-iframe"
                   frameborder="0"
                   allow="clipboard-read; clipboard-write"
                 ></iframe>
               </div>
               <div v-else class="jupyter-placeholder">
                 <a-spin tip="正在启动 Jupyter 环境..." />
               </div>
             </div>
             <!-- Graphic Walker Mode (BI) -->
             <BiDesigner 
               v-else-if="isWorkspaceActive && currentTrainingId" 
               ref="biDesignerRef"
               :training-id="currentTrainingId"
               :classroom-id="classroomId"
               :initial-data="biData"
             />
                 </div>
        </div>
      </div>
      
      <!-- Feedback Modal -->
      <a-modal v-model:open="showFeedbackModal" title="教师反馈" :footer="null">
         <div class="feedback-content">
            <h3>得分: {{ trainingScore }}</h3>
            <p class="feedback-text">{{ teacherFeedback || '暂无评语' }}</p>
         </div>
      </a-modal>
    </div>

    <!-- Standard Classroom Detail View -->
    <PageShell v-else max-width="wide">
    <a-spin :spinning="classroomStore.loading.detail" tip="加载中...">
      <div v-if="currentClassroom">
		<PageHeaderBar
		  :title="currentClassroom?.name || '课堂详情'"
		  :subtitle="headerSubtitle"
		  show-back
		>
		  <template #actions>
		    <span class="status-tag" :class="classroomStatusClass">{{ classroomStatusText }}</span>
		    <a-button
		      v-if="!isHistoricalClassroom && showTeacherView"
		      type="text"
		      @click="handleEdit"
		    >
		      <template #icon><EditOutlined /></template>
		      编辑
		    </a-button>
		    <a-button v-if="showTeacherView" type="primary" @click="openStuList">学生列表</a-button>
		  </template>
		</PageHeaderBar>
		<!-- 内容 -->
		<div class="content-container">
			<!-- 统计卡片区域 -->
			<div class="stats-card">
			  <div class="stats-container">
			    <div class="stats-item">
			      <div class="stats-title">学期</div>
			      <div class="stats-value">{{currentClassroom?.semester}}</div>
			      </div>
			    <div class="stats-divider"></div>
			    <div class="stats-item">
			      <div class="stats-title">学分</div>
			      <div class="stats-value">{{currentClassroom.credits || 0}}</div>
			    </div>
			    <div class="stats-divider"></div>
			    <div class="stats-item">
			      <div class="stats-title">实验数</div>
			      <div class="stats-value">{{coursesCount}}</div>
			    </div>
			    <div class="stats-divider"></div>
			    <div class="stats-item">
			      <div class="stats-title">实验关卡</div>
			      <div class="stats-value">{{taskCount}}</div>
			    </div>
			    <div class="stats-divider"></div>
			    <div class="stats-item">
			      <div class="stats-title">学生</div>
			      <div class="stats-value">{{ currentClassroom.student_count || 0 }}</div>
			    </div>
			  </div>
			</div>
			<!-- 侧边菜单和主内容区域 -->
			<div class="main-content">
			  <!-- 左侧侧边菜单 -->
			  <div class="sidebar">
			    <div class="menu-item" :class="{ active: activeMenu === 'practice' }" @click="changeMenu('practice')">
			      <div class="menu-icon blue-icon"></div>
			      <span>课程实践</span>
			      <span class="menu-count">{{ coursesCount }}</span>
			    </div>
			    <div class="menu-item" :class="{ active: activeMenu === 'training' }" @click="changeMenu('training')">
			      <div class="menu-icon red-icon"></div>
			      <span>项目实训</span>
			      <span class="menu-count">{{ trainingCourseCount }}</span>
			    </div>
			    <div class="menu-item" :class="{ active: activeMenu === 'resources' }" @click="changeMenu('resources')">
			      <div class="menu-icon orange-icon"></div>
			      <span>教学资源</span>
			      <span class="menu-count" v-if="resourceCount > 0">{{ resourceCount }}</span>
			    </div>
			    <div class="menu-item" :class="{ active: activeMenu === 'exams' }" @click="changeMenu('exams')">
			      <div class="menu-icon green-icon"></div>
			      <span>课程考核</span>
			      <span class="menu-count" v-if="examCount > 0">{{ examCount }}</span>
			    </div>
			    <!-- 学情分析：仅教师可见 -->
			    <div v-if="showTeacherView" class="menu-item" :class="{ active: activeMenu === 'analytics' }" @click="changeMenu('analytics')">
			      <div class="menu-icon purple-icon"></div>
			      <span>学情分析</span>
			    </div>
			    <div class="menu-item" :class="{ active: activeMenu === 'cloud' }" @click="changeMenu('cloud')">
			      <div class="menu-icon yellow-icon"></div>
			      <span>课堂云盘</span>
			      <span class="menu-count" v-if="cloudFileCount > 0">{{ cloudFileCount }}</span>
			    </div>
			  </div>
			  <!-- 右侧主内容区域 -->
			  <div class="content-area">
				  <!-- 显示课程实践内容 -->
				  <div v-if="activeMenu === 'practice'">
                      <CourseList
                        :courses="reactiveCoursesList"
                        :classroomId="classroomId"
                        :classroomStatus="computedClassroomStatus"
                        :classroomEndDate="currentClassroom.end_date"
                        :studentCount="currentClassroom.student_count || 0"
                        :userRole="userRole"
                        @update-courses="handleCoursesUpdate"
                        @view-grades="handleViewGrades"
                      />
				  </div>
				  <!-- 显示实训-->
				  <div v-if="activeMenu === 'training'">
				  		<TrainingList :classroomId="classroomId" :userRole="userRole" :classroomStatus="computedClassroomStatus" />
				  </div>
				  <!-- 显示教学资源 -->
				  <div v-if="activeMenu === 'resources'">
				  		<ResourcesList :classroomId="classroomId" />
				  </div>
				  <!-- 显示课程考核 -->
				  <div v-if="activeMenu === 'exams'">
				  		<ClassroomExamList :classroomId="classroomId" />
				  </div>
				  <!-- 学情分析：仅教师可见 -->
				  <div v-if="activeMenu === 'analytics' && showTeacherView">
					  <LearningAnalytics :classroomId="classroomId" />
				  </div>
				  <!-- 课堂云盘 -->
				  <div v-if="activeMenu === 'cloud'">
					  <CloudDisk :classroomId="classroomId" />
				  </div>
				  <!-- 实训列表已移至独立的 TrainingList 组件（通过侧边菜单"项目实训"Tab访问） -->
			  </div>
			</div>
			
		</div>
      </div>
      <a-result v-else-if="!classroomStore.loading.detail" status="404" title="找不到课堂" sub-title="您访问的课堂不存在或已被删除">
        <template #extra>
          <router-link to="/classroom">
            <a-button type="primary">返回课堂列表</a-button>
          </router-link>
        </template>
      </a-result>
       <!-- Keep the main loading spinner covering potentially empty state before fetch completes -->
       <div v-else style="min-height: 300px;"></div>
    </a-spin>
    </PageShell>

    <!-- BI环境iframe模态框 -->
    <a-modal
      v-model:open="biEnvironmentModalVisible"
      :title="currentTrainingTitle || 'BI实训课程'"
      :width="'100vw'"
      :footer="null"
      :maskClosable="false"
      :closable="true"
      @cancel="closeBIEnvironment"
      :style="{ top: '0', paddingBottom: '0', maxWidth: '100vw' }"
      :bodyStyle="{ padding: '0', display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }"
      wrapClassName="bi-dashboard-modal"
    >
      <div class="bi-modal-content">
        <!-- Removed Superset content here -->
      </div>
    </a-modal>

    <!-- Login Helper Modal -->
    <a-modal v-model:open="loginModalVisible" title="登录完整工作台" :footer="null" width="400px">
       <div class="login-helper-content">
          <a-alert message="即将在新窗口打开 BI 工作台，请使用以下账号登录：" type="info" show-icon style="margin-bottom: 16px;">
            <template #icon><InfoCircleOutlined /></template>
          </a-alert>
          
          <div class="credential-item">
             <span class="label">账号:</span>
             <code class="value">admin</code>
             <a-button type="text" size="small" @click="copyToClipboard('admin')"><CopyOutlined /></a-button>
          </div>
          <div class="credential-item">
             <span class="label">密码:</span>
             <code class="value">admin</code>
             <a-button type="text" size="small" @click="copyToClipboard('admin')"><CopyOutlined /></a-button>
          </div>

          <div class="modal-actions" style="margin-top: 24px; text-align: right;">
             <a-button @click="loginModalVisible = false" style="margin-right: 8px;">取消</a-button>
             <a-button type="primary" @click="handleLogin">前往登录 <ExportOutlined /></a-button>
          </div>
       </div>
    </a-modal>

    <!-- Delete Classroom Confirmation Modal (Stays in Parent) -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="确认删除课堂"
      @ok="confirmDeleteClassroom"
      :confirm-loading="deleteLoading"
      @cancel="cancelDelete"
    >
      <p>确定要删除课堂 "{{ currentClassroom?.name }}" 吗？
</p>
      <p style="color: red;">此操作不可恢复，将同时删除所有课程和学生数据，请谨慎操作。
</p>
    </a-modal>
	<a-modal
	      v-model:open="stulistModalVisible"
	      title="学生列表"
		  width="800px"
		  :footer="null"
	      @cancel="stulistModalVisible=false"
	    >
	      <student-list
	        ref="stulistMosdalRef"
	        :classroomId="classroomId"
	        :students="studentsList"
	        :classroomStatus="computedClassroomStatus"
	        @add-student="handleAddStudentClick"
	        @remove-student="handleRemoveStudent"
	      ></student-list>
	    </a-modal>

    <!-- 增强版添加学生弹窗 (带有组织架构树和穿梭框) -->
    <AddStudentModalEnhanced
      v-model:open="addStudentModalVisible"
      :classroomId="classroomId"
      @success="handleStudentAdded"
    />

    <!-- 环境冲突检测弹窗 -->
    <EnvironmentConflictDialog
      v-model:open="showConflictDialog"
      :activeEnvironment="activeEnvironment"
      @go-back="handleConflictGoBack"
      @switch-environment="handleConflictSwitch"
    />
  </div>

</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import { EditOutlined, ArrowLeftOutlined, CheckCircleOutlined, ExportOutlined, CopyOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
import MarkdownIt from 'markdown-it';

import { useClassroomStore } from '../../stores/classroom';
import { useUserStore } from '../../stores/user';
import { getToken } from '@/utils/auth';
import request from '@/utils/request';
import { getPracticeTasks } from '../../api/challenge';
import { launchClassroomTraining, queryEnvironmentStatus } from '@/api/training';
import type { ClassroomDetail, CourseItem } from '@/types/classroom'; 
import type { UserRole } from '../../stores/user'; 
import { launchAndPoll } from '@/utils/polling';

// Import Child Components
import CourseList from './CourseList.vue';
import StudentList from './StudentList.vue';
import AddStudentModalEnhanced from '@/components/classroom/AddStudentModalEnhanced.vue';
import ResourcesList from './ResourcesList.vue';
import TrainingList from './TrainingList.vue';
import LearningAnalytics from './LearningAnalytics.vue';
import CloudDisk from './CloudDisk.vue';
import ClassroomExamList from './ClassroomExamList.vue';
import BiDesigner from '@/components/BiDesigner.vue';
import EnvironmentConflictDialog from '@/components/common/EnvironmentConflictDialog.vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import { techerClRoomsDetail, getClassroomCourses, getRoomProjectList, getClassRoomChapter } from '@/api/classrooms';
import { checkActiveEnvironment, stopEnvironment } from '@/api/practice';
import type { ActiveEnvironment } from '@/api/practice';

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();
const userStore = useUserStore();

const formatDate = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString('zh-CN');
};

const biDesignerRef = ref<any>(null);
const isGraphicWalkerMode = ref(true); // Default to Graphic Walker
const biData = ref<any[]>([]);
const isDataLoaded = ref(false);

// Workspace State
const isWorkspaceActive = ref(false);
const handbookContent = ref('');
// 配置 MarkdownIt 允许 HTML 标签渲染（因为后端存储的是 HTML 格式）
const md = new MarkdownIt({
  html: true,        // 允许 HTML 标签
  breaks: true,      // 将换行符转换为 <br>
  linkify: true      // 自动将 URL 转换为链接
});
const renderedHandbook = computed(() => {
  const content = handbookContent.value || '暂无手册内容';
  // 如果内容已经是 HTML（以 < 开头），直接返回；否则用 MarkdownIt 渲染
  if (content.trim().startsWith('<')) {
    return content;
  }
  return md.render(content);
});
const trainingSubmissionStatus = ref('not_started'); // not_started, submitted, graded
const trainingScore = ref(0);
const teacherFeedback = ref('');
const showFeedbackModal = ref(false);

// 环境冲突检测状态
const showConflictDialog = ref(false);
const activeEnvironment = ref<ActiveEnvironment | null>(null);
const pendingTraining = ref<any>(null); // 待启动的实训（等待冲突解决后启动）
const submitting = ref(false);
const currentTrainingId = ref<number | null>(null);
const currentTrainingTitle = ref('');
const currentTrainingType = ref<string>(''); // CODING, DRAG_DROP, etc.
const jupyterUrl = ref<string>(''); // Jupyter 环境 URL
const loginModalVisible = ref(false);

// --- State ---
const classroomId = computed(() => route.params.id as string);

// 侧边菜单映射 - 定义在 watch 之前，避免 TDZ 问题
const menuRouteMap: Record<string, string> = {
  practice: '',
  training: 'trainings',
  resources: 'resources',
  exams: 'exams',
  analytics: 'analytics',
  cloud: 'drive'
};

// 左侧导航相关状态
const activeMenu = ref('practice');

// 从URL path解析当前菜单 - 必须在 watch 之前定义，避免 TDZ
const parseMenuFromPath = (path: string): string => {
  console.log('[parseMenuFromPath] 输入path:', path);

  // 安全性检查：如果path为空或undefined，返回默认菜单
  if (!path) {
    console.log('[parseMenuFromPath] path为空，返回默认practice');
    return 'practice';
  }

  // 移除 "/classroom/" 前缀
  const pathPart = path.replace(/^\/classroom\//, '');
  console.log('[parseMenuFromPath] pathPart:', pathPart);

  // 如果只是数字（课堂ID），返回 'practice' 表示默认课程实践
  if (/^\d+$/.test(pathPart)) {
    console.log('[parseMenuFromPath] 只是数字，返回practice');
    return 'practice';
  }

  // 提取路径部分（移除数字ID和斜杠）
  const routePart = pathPart.replace(/^\d+\//, '');
  console.log('[parseMenuFromPath] routePart:', routePart);

  // 反向查找：查找路径对应的菜单
  for (const [menu, routePath] of Object.entries(menuRouteMap)) {
    if (routePath === routePart) {
      console.log('[parseMenuFromPath] 匹配到菜单:', menu);
      return menu;
    }
  }

  console.log('[parseMenuFromPath] 未匹配，返回默认practice');
  return 'practice';
};

// 监听路由变化，更新activeMenu - parseMenuFromPath 必须在 watch 之前定义
watch(() => route.path, (newPath) => {
  try {
    if (newPath) {
      console.log('[watch route.path] 路由变化:', newPath);
      const menu = parseMenuFromPath(newPath);
      activeMenu.value = menu;
    } else {
      console.log('[watch route.path] 路由path为空，保持当前状态');
    }
  } catch (error) {
    console.error('[watch route.path] 解析菜单出错:', error);
  }
}, { immediate: true }); 
const currentClassroom = ref({} as any);
const coursesList = ref<CourseItem[]>([]); 
const studentsList = ref<any[]>([]); 
const cloudFileCount = ref(0); 

const reactiveCoursesList = ref<CourseItem[]>([]);

// Delete Modal State
const deleteModalVisible = ref(false);
const deleteLoading = ref(false);
const stulistModalVisible = ref(false);
const stulistMosdalRef=ref();
const addStudentModalVisible = ref(false);

// BI环境iframe状态
const biEnvironmentModalVisible = ref(false);

// --- Computed Properties ---
const userRole = computed<UserRole>(() => { return userStore.userInfo.role as UserRole || 'student'; });
const showTeacherView = computed(() => userRole.value === 'teacher' || userRole.value === 'admin');
const showStudentView = computed(() => userRole.value === 'student');

// 计算课堂真实状态（根据日期判断）
const computedClassroomStatus = computed(() => {
  if (!currentClassroom.value) return 'ONGOING';

  const now = dayjs();
  const startDate = currentClassroom.value.start_date ? dayjs(currentClassroom.value.start_date) : null;
  const endDate = currentClassroom.value.end_date ? dayjs(currentClassroom.value.end_date) : null;

  if (endDate && now.isAfter(endDate)) {
    return 'ENDED'; // 已结束
  }
  if (startDate && now.isBefore(startDate)) {
    return 'UPCOMING'; // 未开始
  }
  return 'ONGOING'; // 正在上课
});

// 是否是历史课堂（已结束）
const isHistoricalClassroom = computed(() => {
  return computedClassroomStatus.value === 'ENDED';
});

// 状态文本
const classroomStatusText = computed(() => {
  switch (computedClassroomStatus.value) {
    case 'ENDED': return '已结课';
    case 'UPCOMING': return '未开始';
    case 'ONGOING':
    default: return '正在上课';
  }
});

// 状态样式类
const classroomStatusClass = computed(() => {
  switch (computedClassroomStatus.value) {
    case 'ENDED': return 'status-ended';
    case 'UPCOMING': return 'status-upcoming';
    case 'ONGOING':
    default: return 'status-ongoing';
  }
});

const headerSubtitle = computed(() => {
  const c = currentClassroom.value;
  if (!c) return '';
  const teacher = c.teacher_name ? `授课教师: ${c.teacher_name} · ` : '';
  return `${teacher}起止时间: ${formatDate(c.start_date)} 至 ${formatDate(c.end_date)}`;
});

const coursesCount = computed(() => {
  const list = reactiveCoursesList.value || [];
  if (list.length === 0) return 0;

  // 检查是否是章节格式（每个章节包含 courses 数组）
  const firstItem = list[0];
  if (firstItem && Array.isArray(firstItem.courses)) {
    // 章节格式：累计所有章节中的课程数量
    return list.reduce((total, chapter) => {
      return total + (chapter.courses?.length || 0);
    }, 0);
  }

  // 普通课程列表格式
  return list.length;
});
const taskCount = computed(() => {
  const list = reactiveCoursesList.value || [];
  if (list.length === 0) return 0;

  // 检查是否是章节格式
  const firstItem = list[0];
  if (firstItem && Array.isArray(firstItem.courses)) {
    // 章节格式：遍历所有章节中的课程累计任务数
    return list.reduce((total, chapter) => {
      return total + (chapter.courses || []).reduce((chapterTotal: number, course: any) => {
        return chapterTotal + (course.task_count || 0);
      }, 0);
    }, 0);
  }

  // 普通课程列表格式
  return list.reduce((total, course) => {
    return total + (course.task_count || 0);
  }, 0);
});

const trainingsList = ref([]);

const getTrainingsList = async () => {
  try {
    const role = userRole.value;
    let res;
    
    console.log('[课程列表] 获取实训列表, 角色:', role);

    if (role === 'student') {
      const studentId = userStore.userInfo?.user_id || userStore.userId;
      const apiUrl = `/api/v1/classrooms/${classroomId.value}/trainings?student_id=${studentId}`;
      
      res = await fetch(apiUrl, {
        headers: {
          'Authorization': `Bearer ${getToken()}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (res.ok) {
        res = await res.json();
      } else {
        throw new Error(`API请求失败: ${res.status}`);
      }
    } else {
      res = await getRoomProjectList({ classroom_id: Number(classroomId.value) });
    }
    
    const trainings = res.data?.list || res.data || [];
    trainingsList.value = trainings;
  } catch (error) {
    console.error('[课程列表] ❌ 获取实训课程失败:', error);
    trainingsList.value = [];
  }
};

// 跳转到实训详情页
const goToTrainingDetail = (training: any) => {
  const trainingId = training.training_id || training.id;
  if (trainingId) {
    router.push(`/classroom/${classroomId.value}/training/${trainingId}`);
  } else {
    message.error('无法跳转：实训ID不存在');
  }
};

// 启动实训
const startTraining = async (training: any) => {
  console.log('[startTraining] 函数被调用, training:', training);

  try {
    if (!training || !training.training_id) {
      console.error('[startTraining] 数据格式错误:', { training, training_id: training?.training_id });
      message.error('无法启动实训：数据格式错误');
      return;
    }

    console.log('[startTraining] 开始启动实训:', {
      training_id: training.training_id,
      training_type: training.training_type,
      title: training.training_title
    });

    // 检查是否有活跃的实验环境
    console.log('[startTraining] 检查活跃环境...');
    const existingEnv = await checkActiveEnvironment();
    if (existingEnv && existingEnv.id) {
      console.log('[startTraining] 检测到活跃环境:', existingEnv);
      // 如果当前请求的就是已活跃的环境，直接进入
      if (existingEnv.practiceId === String(training.training_id)) {
        console.log('[startTraining] 请求的是同一个环境，直接进入');
      } else {
        // 不同环境，弹出冲突提示
        activeEnvironment.value = existingEnv;
        pendingTraining.value = training;
        showConflictDialog.value = true;
        return;
      }
    }

    message.loading('正在准备实训数据...', 0);
    
    // 设置基本信息
    currentTrainingTitle.value = training.training_title || 'BI实训环境';
    currentTrainingId.value = training.training_id;
    currentTrainingType.value = training.training_type || 'DRAG_DROP';
    jupyterUrl.value = ''; // 重置 Jupyter URL
    
    // Call Launch API
    try {
        const result = await launchClassroomTraining(
            training.training_id,
            classroomId.value,
            training.training_type,
            userStore.userId || ''
        );
        
        console.log('[startTraining] Launch API response:', result);

        if (result.code === '0000') {
            if (training.training_type === 'DATA_ANALYSIS' || training.training_type === 'DRAG_DROP' || training.training_type === 'BI') {
                // BI类型：跳转本站的 BiTrainingWorkspace 工作台页面
                const routeUrl = router.resolve(`/classroom/${classroomId.value}/bi-training/${training.training_id}/workspace`).href;
                window.open(routeUrl, '_blank');
                message.success('实训环境就绪，即将进入分析台');
            } else if (result.data?.url) {
                // CODING/JUPYTER类型：打开外部环境URL
                let status = result.data.status;
                let finalUrl = result.data.url;
                
                if (status === 'starting') {
                    // Show message with no timeout
                    message.loading({ content: '正在为您分配独立的云端实验舱，请稍候(预计需10秒)...', key: 'jupyterBoot' });
                    
                    let retries = 0;
                    const maxRetries = 15; // up to 30 seconds
                    
                    while (status === 'starting' && retries < maxRetries) {
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        try {
                            const pollResult = await queryEnvironmentStatus(training.training_id, userStore.userId || '');
                            if (pollResult.code === '0000' && pollResult.data) {
                                status = pollResult.data.status;
                                if (status === 'running' && pollResult.data.url) {
                                    finalUrl = pollResult.data.url;
                                    break;
                                }
                            }
                        } catch (pollErr) {
                            console.warn("Polling error", pollErr);
                        }
                        retries++;
                    }
                    
                    if (status !== 'running') {
                        message.warning({ content: '环境分配超时或响应缓慢，您可以尝试刷新页面后重新进入。', key: 'jupyterBoot', duration: 4 });
                    } else {
                        message.success({ content: '独立实验舱已成功启动！', key: 'jupyterBoot', duration: 2 });
                    }
                }
                
                let url = finalUrl;
                const hostname = window.location.hostname;
                const targetHost = (hostname === 'localhost' || hostname === '127.0.0.1') ? 'localhost' : hostname;
                url = url.replace(/https?:\/\/huixue-jupyter:8888/g, `http://${targetHost}:8888`);
                url = url.replace(/https?:\/\/jupyter:8888/g, `http://${targetHost}:8888`);
                url = url.replace(/http:\/\/localhost:8888/g, `http://${targetHost}:8888`);
                url = url.replace(/http:\/\/127\.0\.0\.1:8888/g, `http://${targetHost}:8888`);
                // 添加token自动登录
                if (url && !url.includes('token=')) {
                    url += (url.includes('?') ? '&' : '?') + 'token=huixue_token';
                }
                window.open(url, '_blank');
            } else {
                message.success('实训环境准备就绪');
            }
            // 刷新环境状态
            setTimeout(fetchClassroomData, 1500);
        } else {
            console.warn("[startTraining] Launch API did not return success code", result);
            biData.value = [];
            jupyterUrl.value = '';
            message.error(result.message || "启动实训失败: API未返回成功");
        }
    } catch (err: any) {
        console.error('[startTraining] API调用异常:', err);
        message.error(`启动异常: ${err.message}`);
    }

    message.destroy();

  } catch (error: any) {
    message.destroy();
    console.error('[startTraining] 启动实训失败:', error);
    message.error(`启动实训失败：${error.message || '未知错误'}`);
  }
};

const trainingCourseCount = computed(() => {
  return (trainingsList.value || []).length;
});
const resourceCount = computed(() => {
  return 0; 
});

const closeBIEnvironment = () => {
  biEnvironmentModalVisible.value = false;
  currentTrainingTitle.value = '';
  biData.value = [];
};

// 冲突弹窗回调：返回当前活跃的实验
const handleConflictGoBack = (env: ActiveEnvironment) => {
  console.log('[handleConflictGoBack] 返回活跃环境:', env);
  showConflictDialog.value = false;
  pendingTraining.value = null;
  // 如果有 URL，可以导航到该环境
  if (env.url) {
    message.info(`请在当前实训环境中继续：${env.practiceName}`);
  }
};

// 冲突弹窗回调：强制切换到新实验
const handleConflictSwitch = async (env: ActiveEnvironment) => {
  console.log('[handleConflictSwitch] 强制切换，关闭旧环境:', env);

  try {
    // 停止当前活跃的环境
    if (env.id) {
      message.loading('正在关闭当前实验环境...', 0);
      await stopEnvironment(env.id);
      message.destroy();
      message.success('已关闭旧实验环境');
    }

    showConflictDialog.value = false;

    // 启动新实训
    if (pendingTraining.value) {
      const trainingToStart = pendingTraining.value;
      pendingTraining.value = null;
      activeEnvironment.value = null;

      // 重新调用 startTraining（此时不会再检测到冲突）
      await startTraining(trainingToStart);
    }
  } catch (error: any) {
    message.destroy();
    console.error('[handleConflictSwitch] 切换环境失败:', error);
    message.error(`切换环境失败：${error.message || '未知错误'}`);
  }
};

const exitWorkspace = () => {
  isWorkspaceActive.value = false;
  currentTrainingId.value = null;
  currentTrainingType.value = '';
  jupyterUrl.value = '';
  biData.value = [];
  isDataLoaded.value = false;
};

const fetchTrainingDetails = async (trainingId: number) => {
   try {
     const studentId = userStore.userInfo?.user_id || userStore.userId;
     const res = await fetch(`/api/v1/classrooms/${classroomId.value}/trainings/${trainingId}/details?student_id=${studentId}`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
     });
     
     if(res.ok) {
        const data = await res.json();
        if(data.code === '0000' && data.data) {
           handbookContent.value = data.data.handbook_content || data.data.training?.handbook_content || '# 暂无手册内容';
           
           const status = data.data.student_status || data.data.status;
           const statusMap: Record<string, string> = {
             'NOT_STARTED': 'not_started',
             'IN_PROGRESS': 'in_progress',
             'SUBMITTED': 'submitted',
             'GRADED': 'graded',
             'COMPLETED': 'graded',
             'LATE_SUBMISSION': 'submitted'
           };
           trainingSubmissionStatus.value = statusMap[status] || 'not_started';
           
           if (data.data.overall_score !== undefined) {
             trainingScore.value = data.data.overall_score;
           }
           if (data.data.teacher_feedback) {
             teacherFeedback.value = data.data.teacher_feedback;
           }
        }
     }
   } catch(e) {
     console.error("Failed to fetch training details", e);
     handbookContent.value = "# 加载手册失败";
   }
};

const submitAssignment = async () => {
   if(!currentTrainingId.value) return;
   
   submitting.value = true;
   try {
      const studentId = userStore.userInfo?.user_id || userStore.userId;
      
      let snapshotJson = null;
      if (isGraphicWalkerMode.value && biDesignerRef.value) {
          try {
            snapshotJson = await biDesignerRef.value.getSpec();
            console.log("[提交作业] 获取到图表快照, 长度:", JSON.stringify(snapshotJson).length);
          } catch (e) {
            console.error("[提交作业] 获取图表快照失败:", e);
            message.warning("无法获取图表状态，将仅提交完成状态");
          }
      }

      const payload = {
          snapshot_json: snapshotJson,
          notes: "Submitted via Graphic Walker"
      };

      // Use axios request instead of fetch to ensure Authorization header is set correctly
      try {
         const data = await request.post(`/api/v1/trainings/${currentTrainingId.value}/submit`, payload, {
            params: {
               classroom_id: classroomId.value,
               student_id: studentId
            }
         });
         
         if(data.code === '0000') {
            message.success("作业提交成功！");
            trainingSubmissionStatus.value = 'submitted';
            // Refresh training details to get updated status
            if (currentTrainingId.value) {
               fetchTrainingDetails(currentTrainingId.value);
            }
         } else {
            message.error("提交失败: " + (data.message || '未知错误'));
         }
      } catch (err: any) {
         console.error("Submit API error:", err);
         message.error("提交失败: " + (err.message || '网络错误'));
      }
   } catch(e) {
      console.error("Submit failed", e);
      message.error("提交异常");
   } finally {
      submitting.value = false;
   }
};

const openFullWorkspace = () => {
  // Not implemented for GWalk
  message.info('Function not available in Graphic Walker mode');
};

const copyToClipboard = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    message.success('复制成功');
  }).catch(() => {
    message.error('复制失败');
  });
};

const handleLogin = () => {
  // Not implemented for GWalk
};

const examCount = computed(() => {
  return 0; 
});
const totalCourseCount = computed(() => coursesCount.value);
const learningCourseCount = computed(() => {
  return (reactiveCoursesList.value || []).filter(course => course.status === 'learning').length;
});
const makeupCourseCount = computed(() => {
  return (reactiveCoursesList.value || []).filter(course => course.status === 'makeup').length;
});
const completedCourseCount = computed(() => {
  return (reactiveCoursesList.value || []).filter(course => course.status === 'completed').length;
});

// fetchClassroomData
const fetchClassroomData = async () => {
  try {
    // Using timeout promise pattern
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('请求超时（8秒）')), 8000);
    });
    
    const apiPromise = techerClRoomsDetail({id:classroomId.value});
    
    const response = await Promise.race([apiPromise, timeoutPromise]);

    currentClassroom.value = response.data || response;
    studentsList.value = JSON.parse(JSON.stringify(classroomStore.currentClassroom?.students || [])); 
    
  } catch (error) {
    console.error('[课堂数据] ❌ 获取课堂详情失败:', error);
    reactiveCoursesList.value = [];
    studentsList.value = [];
  }
};

const getChapterList = async () => {
	try {
	  const userRole = userStore.userRole || 'student';
	  let res;

	  if (userRole === 'student') {
	    const studentId = userStore.userInfo?.user_id || userStore.userId;
	    const apiUrl = `/api/v1/classrooms/${classroomId.value}/practices?student_id=${studentId}`;
	    
	    const controller = new AbortController();
	    const timeoutId = setTimeout(() => {
	      controller.abort();
	    }, 5000);
	    
	    try {
	      res = await fetch(apiUrl, {
	        headers: {
	          'Authorization': `Bearer ${getToken()}`,
	          'Content-Type': 'application/json'
	        },
	        signal: controller.signal
	      });
	      
	      clearTimeout(timeoutId);
	      
	      if (res.ok) {
	        res = await res.json();
	      } else {
	        const errorText = await res.text();
	        throw new Error(`API请求失败: ${res.status}`);
	      }
	    } catch (error) {
	      clearTimeout(timeoutId);
	      throw error;
	    }
	  } else {
	    res = await getClassroomCourses(Number(classroomId.value), userStore.userId);
	  }

	  let courses = [];
	  if (userRole === 'student') {
	    // 支持多种API响应格式: list / practices / courses
	    const practices = res.data?.list || res.data?.practices || res.data?.courses || [];
	    const courseItems = practices.map(practice => ({
	      id: (practice.course_id || practice.practice_id || practice.id).toString(),
	      name: practice.title || practice.course_name,
	      name_override: practice.title || practice.course_name,
      type: (practice.source_type || 'practice') as any,
          status: practice.status || 'not_started' as any,
	      coins: practice.coin,
	      difficulty: practice.difficulty?.toUpperCase() === 'BEGINNER' ? 1 : practice.difficulty?.toUpperCase() === 'INTERMEDIATE' ? 2 : 3,
	      is_required: practice.is_mandatory !== false,
	      order: 1,
	      created_at: practice.added_at || new Date().toISOString(),
	      updated_at: practice.added_at || new Date().toISOString(),
	      task_count: practice.task_count,
	      classroom_practice_id: practice.classroom_practice_id || practice.id,
	      classroom_chapter_title: practice.classroom_chapter_title,
	      description: practice.description,
	      direction: practice.direction,
	      category: practice.category,
	      completed_task_count: practice.completed_task_count || 0
	    }));
	    courses = courseItems;
	  } else {
	    courses = res.data?.courses || res.data?.list || res.courses || [];
	  }

	  if (!Array.isArray(courses)) {
	    reactiveCoursesList.value = [];
	    return;
	  }

	  // 获取章节列表（包括空章节）
	  if (userRole !== 'student') {
	    try {
	      const chaptersRes = await getClassRoomChapter(Number(classroomId.value));
	      const chaptersData = chaptersRes.data?.chapters || [];

	      // 创建章节映射：标题 -> 章节信息
	      const chapterMap = new Map<string, any>();
	      chaptersData.forEach((chapter: any) => {
	        chapterMap.set(chapter.title, {
	          id: chapter.id,  // 使用真实的数据库ID
	          name: chapter.title,
	          order_index: chapter.order_index,
	          courses: []
	        });
	      });

	      // 将课程分配到对应章节
	      const unmatchedCourses: any[] = [];
	      courses.forEach((course: any) => {
	        const chapterTitle = course.classroom_chapter_title;
	        if (chapterTitle && chapterMap.has(chapterTitle)) {
	          chapterMap.get(chapterTitle).courses.push(course);
	        } else {
	          unmatchedCourses.push(course);
	        }
	      });
	      // 未匹配章节的课程放入"未分类"
	      if (unmatchedCourses.length > 0) {
	        chapterMap.set('__unmatched__', {
	          title: '未分类',
	          name: '未分类',
	          order_index: 9999,
	          courses: unmatchedCourses
	        });
	      }

	      // 按order_index排序并转换为数组
	      const sortedChapters = Array.from(chapterMap.values())
	        .sort((a, b) => a.order_index - b.order_index);

	      reactiveCoursesList.value = sortedChapters;
	    } catch (chapterErr) {
	      console.error('获取章节列表失败，使用课程分组:', chapterErr);
	      // 降级处理：按课程的章节标题分组
	      const hasChapterInfo = courses.some(c => c.classroom_chapter_title);
	      if (hasChapterInfo) {
	        const chapterMap = new Map<string, any>();
	        courses.forEach((course: any) => {
	          const chapterTitle = course.classroom_chapter_title || '未分类课程';
	          if (!chapterMap.has(chapterTitle)) {
	            chapterMap.set(chapterTitle, {
	              id: `chapter-${chapterMap.size + 1}`,
	              name: chapterTitle,
	              courses: []
	            });
	          }
	          chapterMap.get(chapterTitle).courses.push(course);
	        });
	        reactiveCoursesList.value = Array.from(chapterMap.values());
	      } else {
	        reactiveCoursesList.value = courses;
	      }
	    }
	  } else {
	    reactiveCoursesList.value = courses;
	  }

	} catch (err) {
	  console.error('获取课堂课程列表失败:', err);
	  reactiveCoursesList.value = [];
	}
}

const changeMenu = (menu: string) => {
  // 直接切换 activeMenu，不依赖路由 watcher（避免同组件子路由切换时 watcher 不触发）
  activeMenu.value = menu;

  // 同时更新 URL 以支持深链接/刷新恢复
  let id = classroomId.value || route.params.id;

  if (!id) {
    const pathMatch = route.path.match(/\/classroom\/(\d+)/);
    if (pathMatch && pathMatch[1]) {
      id = pathMatch[1];
      console.log('[changeMenu] 从路径中提取到classroomId:', id);
    }
  }

  if (!id) {
    console.error('[changeMenu] Classroom ID is missing', {
      classroomId: classroomId.value,
      routeParamsId: route.params.id,
      currentPath: route.path,
      menu
    });
    return;
  }

  const routePath = menuRouteMap[menu];
  const newPath = routePath
    ? `/classroom/${id}/${routePath}`
    : `/classroom/${id}`;

  console.log('[changeMenu] 导航到:', { menu, id, routePath, newPath });
  // 使用 replace 避免生成过多历史记录；静默失败防止 NavigationDuplicated 异常
  router.replace(newPath).catch(() => {});
};
const openStuList = async () => {
	stulistModalVisible.value = true;
    await nextTick();
    if (stulistMosdalRef.value) {
        stulistMosdalRef.value.open();
    }
}

const handleAddStudentClick = () => {
  addStudentModalVisible.value = true;
};

const handleStudentAdded = async () => {
  try {
    const res = await request.get(`/api/v1/classrooms/${classroomId.value}/students`);
    studentsList.value = res.data.list || [];
  } catch (error) {
    console.error('Failed to refresh student list', error);
  }
};

const handleRemoveStudent = async (studentIds: string[]) => {
  try {
    const response = await request.delete(`/api/v1/classrooms/${classroomId.value}/students`, {
      data: { student_ids: studentIds }
    });
    if (response) {
      if ((response as any).code !== '0000') {
        throw new Error((response as any).message || '移除失败');
      }
      message.success('移除成功');
      await handleStudentAdded(); // refresh list
    }
  } catch (error: any) {
    console.error('移除学生失败:', error);
    message.error(error.message || '移除学生失败');
  }
};
const handleEdit = () => {
  router.push(`/classroom/${classroomId.value}/edit`);
};

const showDeleteConfirm = () => {
  deleteModalVisible.value = true;
};

const navigateToCourseDetail = async (courseId: string) => {
  try {
    const response = await getPracticeTasks(courseId);
    const tasks = response?.data?.list || response?.data?.tasks || [];
    
    if (tasks.length === 0) {
      message.warning('该实践课程暂无关卡');
      return;
    }
    
    const firstTask = tasks.sort((a: any, b: any) => 
      (a.order_in_practice || 0) - (b.order_in_practice || 0)
    )[0];
    
    router.push(`/course/challenge/${courseId}/${firstTask.id}`);
  } catch (error) {
    console.error('获取关卡列表失败:', error);
    message.error('获取关卡列表失败');
  }
};

const handleViewGrades = (course: CourseItem) => {
  const courseName = course.name_override || course.title || course.name || course.course_name || '';
  const courseType = course.source_type || course.type || 'practice';
  const classroomCourseId = course.classroom_course_id || course.classroomCourseId || course.id;
  router.push({
    path: `/classroom/${classroomId.value}/course/${classroomCourseId}/grades`,
    query: {
      courseName,
      courseType,
      courseId: course.course_id || course.original_course_id,
      practiceId: course.practice_id
    }
  });
};

const getCourseStatusClass = (status: string) => {
  switch (status) {
    case 'learning': return 'status-learning';
    case 'completed': return 'status-completed';
    case 'unpublished': return 'status-unpublished';
    case 'makeup': return 'status-makeup';
    default: return 'status-default';
  }
};

const getCourseStatusText = (status: string) => {
  switch (status) {
    case 'not_started': return '未开始';
    case 'learning': return '学习中';
    case 'completed': return '已完成';
    case 'unpublished': return '未发布';
    case 'makeup': return '补交中';
    default: return '未知状态';
  }
};

const handleCoursesUpdate = (updatedCourses: CourseItem[]) => {
  getChapterList();
  getTrainingsList(); 
};

const handleStudentsUpdate = (updatedStudents: any[]) => {
  studentsList.value = updatedStudents;
};

const confirmDeleteClassroom = async () => {
  if (!currentClassroom.value) return;
  deleteLoading.value = true;
  try {
    await classroomStore.deleteClassroom(classroomId.value);
    message.success('课堂删除成功');
    router.push('/classroom');
  } catch (error) {
    message.error('删除课堂失败，请重试');
    console.error(error);
    deleteLoading.value = false; 
  }
};

const cancelDelete = () => {
  deleteModalVisible.value = false;
};

onMounted(async () => {
  // activeMenu 现在是 computed 属性，会自动从 route.hash 读取
  // 不需要手动初始化

  setTimeout(async () => {
    try {
      await getChapterList();
      await getTrainingsList();
    } catch (error) {
      console.error('[生命周期] ❌ 加载课程列表失败:', error);
    }
  }, 100);

  fetchClassroomData().catch(error => {
    console.error('[生命周期] ⚠️ 课堂详情加载失败（不影响课程列表）:', error);
  });
});

watch(classroomId, async (newId, oldId) => {
    if (newId && newId !== oldId) {
        await fetchClassroomData();
        await getChapterList();
        await getTrainingsList();
    }
});

// 监听activeMenu变化，加载对应的数据
watch(activeMenu, async (newMenu) => {
  if (newMenu === 'practice' || newMenu === 'training') {
    await getChapterList();
  }
});

watch(() => classroomStore.currentClassroom, (newClassroom) => {
    if (newClassroom && newClassroom.id === classroomId.value) {
        reactiveCoursesList.value = JSON.parse(JSON.stringify(newClassroom.courses || []));
        studentsList.value = JSON.parse(JSON.stringify(newClassroom.students || [])); 
    }
}, { deep: true });

</script>

<style>
/* Integrated Workspace Styles */
.integrated-workspace {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #f0f2f5;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.workspace-header {
  height: 60px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  z-index: 10;
}

.left-section, .right-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workspace-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f1f1f;
}

.divider {
  color: #e8e8e8;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
}

.status-tag.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #b7eb8f;
}

.status-tag.graded {
  background: #e6f7ff;
  color: var(--hx-color-primary);
  border: 1px solid #91d5ff;
}

.workspace-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

.workspace-panel {
  background: white;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  overflow: hidden;
}

.left-panel {
  width: 400px;
  flex-shrink: 0;
}

.right-panel {
  flex: 1;
}

.panel-header {
  height: 48px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between; 
  padding: 0 16px;
  font-weight: 500;
  background: #fafafa;
}

.header-title {
  display: flex;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  position: relative;
}

.markdown-body {
  padding: 24px;
  line-height: 1.6;
  color: #24292e;
}

.markdown-body h1, .markdown-body h2, .markdown-body h3 {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
.markdown-body h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
.markdown-body p { margin-bottom: 16px; }
.markdown-body ul { padding-left: 2em; margin-bottom: 16px; }
.markdown-body li { margin-bottom: 4px; }

.bi-container-wrapper {
  display: flex;
  flex-direction: column;
}

/* Jupyter 容器样式 */
.jupyter-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.jupyter-frame-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.jupyter-iframe {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border: none;
}

.jupyter-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 400px;
}

</style>

<style>
/* BI 仪表盘模态框优化样式 - 全屏显示 (全局样式以覆盖 Ant Design Modal) */
.bi-dashboard-modal .ant-modal {
  max-width: 100vw !important;
  width: 100vw !important;
  position: absolute !important;
  top: 0 !important;
  bottom: 0 !important;
  left: 0 !important;
  right: 0 !important;
  height: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  padding-bottom: 0 !important;
  display: flex !important;
  flex-direction: column !important;
}

.bi-dashboard-modal .ant-modal-content {
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  max-height: 100% !important;
  border-radius: 0 !important;
  background-color: #fff !important; 
  overflow: hidden !important;
}

.bi-dashboard-modal .ant-modal-header {
  flex: 0 0 auto !important;
  padding: 12px 24px !important;
  border-bottom: 1px solid #f0f0f0;
  min-height: 55px; 
  background-color: #fff !important;
}

.bi-dashboard-modal .ant-modal-body {
  flex: 1 1 auto !important;
  overflow: hidden !important; 
  display: flex !important;
  flex-direction: column !important;
  height: 0 !important; 
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  background-color: #fff !important;
  position: relative !important;
}

.bi-dashboard-modal .ant-modal-close {
  top: 12px !important;
  right: 12px !important;
}

.bi-dashboard-modal.ant-modal-wrap {
  overflow: hidden !important;
}
</style>

<style scoped>
.classroom-detail-page {
  width: 100%;
  font-family: var(--hx-font-family);
}

.status-tag {
  padding: 2px var(--hx-space-2);
  border-radius: var(--hx-radius-sm);
  font-size: var(--hx-font-size-xs);
  color: #fff;
  line-height: 1.5;
}

.status-tag.status-ongoing {
  background-color: var(--hx-color-error);
}

.status-tag.status-ended {
  background-color: var(--hx-color-text-tertiary);
}

.status-tag.status-upcoming {
  background-color: var(--hx-color-warning);
}

.content-container {
  width: 100%;
  margin: 0;
}

/* Ensure Spin takes up space while loading */
.ant-spin-nested-loading {
  min-height: 200px;
}

.stats-card {
  background-color: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
  box-shadow: var(--hx-shadow-md);
  border: 1px solid var(--hx-color-border-muted);
  width: 100%;
}

.stats-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--hx-space-4) var(--hx-space-5);
  flex-wrap: wrap;
  gap: var(--hx-space-2);
}

.stats-item {
  text-align: center;
  padding: var(--hx-space-2) var(--hx-space-3);
}

.stats-title {
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
  margin-bottom: var(--hx-space-2);
}

.stats-value {
  font-size: var(--hx-font-size-md);
  font-weight: bold;
  color: var(--hx-color-primary);
}

.stats-divider {
  width: 1px;
  height: 30px;
  background-color: var(--hx-color-border-muted);
}

.main-content {
  display: flex;
  width: 100%;
  margin-top: var(--hx-space-4);
  background-color: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
  box-shadow: var(--hx-shadow-md);
  border: 1px solid var(--hx-color-border-muted);
  min-height: 600px;
}

.sidebar {
  width: 200px;
  padding: var(--hx-space-5) 0;
  border-right: 1px solid var(--hx-color-border-muted);
  flex-shrink: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: var(--hx-space-3) var(--hx-space-5);
  cursor: pointer;
}

.menu-item.active {
  background-color: var(--hx-color-primary-dim);
  border-left: 3px solid var(--hx-color-primary);
}

.menu-icon {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: var(--hx-space-2);
}

.blue-icon { background-color: var(--hx-color-primary); }
.red-icon { background-color: var(--hx-color-error); }
.orange-icon { background-color: var(--hx-color-warning); }
.green-icon { background-color: var(--hx-color-success); }
.purple-icon { background-color: var(--hx-color-accent-purple); }
.yellow-icon { background-color: var(--hx-color-warning); }

.menu-count {
  margin-left: auto;
  background-color: var(--hx-color-bg-layout);
  color: var(--hx-color-text-secondary);
  border-radius: 10px;
  font-size: var(--hx-font-size-xs);
  padding: 0 6px;
}

.content-area {
  flex-grow: 1;
  padding: var(--hx-space-5);
  min-width: 0;
}

/* 课程列表相关样式 */
.course-list {
  width: 100%;
}

.filter-tabs {
  display: flex;
  gap: var(--hx-space-5);
  margin-bottom: var(--hx-space-5);
  border-bottom: 1px solid var(--hx-color-border-muted);
  padding-bottom: var(--hx-space-2);
}

.filter-tab {
  cursor: pointer;
  padding: 5px 0;
  font-size: 14px;
  color: var(--copilot-text-secondary, #a0a0a0);
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.filter-tab.active {
  color: var(--copilot-brand-primary, #00c6ff);
  border-bottom-color: var(--copilot-brand-primary, #00c6ff);
}

.course-items {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-3);
}

/* 实践类课程样式 - 简洁显示 */
.course-item.simple-practice-course {
  padding: 12px 15px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--copilot-bg-tertiary, #fafafa);
  transition: all 0.3s;
}

.course-item.simple-practice-course:hover {
  box-shadow: 0 4px 12px rgba(0, 198, 255, 0.1);
  background-color: var(--copilot-bg-hover, rgba(255, 255, 255, 0.05));
  border-color: var(--copilot-border-highlight, rgba(0, 198, 255, 0.3));
}

.course-header {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 12px;
}

.course-title {
  font-size: 14px;
  color: var(--copilot-text-primary, #e0e0e0);
  flex: 1;
  display: flex;
  align-items: center;
}

.course-number {
  color: var(--copilot-text-muted, #606060);
  margin-right: 5px;
  min-width: 25px;
}

.course-tags {
  display: flex;
  gap: 8px;
  align-items: center;
}

.mandatory-tag {
  background-color: rgba(250, 173, 20, 0.15);
  color: var(--copilot-semantic-warning, #facc15);
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  white-space: nowrap;
}

.course-status {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 12px;
  white-space: nowrap;
}

.course-status.published {
  background-color: rgba(34, 197, 94, 0.15);
  color: var(--copilot-semantic-success, #22c55e);
}

.course-status.learning {
  background-color: rgba(0, 198, 255, 0.15);
  color: var(--copilot-brand-primary, #00c6ff);
}

.course-status.unpublished {
  background-color: var(--copilot-bg-tertiary, #fafafa);
  color: var(--copilot-text-muted, #606060);
}

.course-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.empty-state {
  text-align: center;
  padding: var(--hx-space-6);
  color: var(--hx-color-text-secondary);
}

/* BI 仪表盘模态框优化样式 - 已移动到全局样式块中 */
/* :deep(.bi-dashboard-modal) { ... } */

.bi-modal-content {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  background-color: var(--copilot-bg-secondary, #ffffff);
}

.bi-embed-content {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden; /* 保持 hidden 避免布局溢出 */
  background-color: var(--copilot-bg-secondary, #ffffff);
}

.bi-loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  flex-direction: column;
  position: absolute;
  inset: 0;
  z-index: 10;
  background: var(--copilot-bg-secondary, #ffffff);
  gap: 16px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid var(--hx-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 16px;
  color: var(--copilot-text-primary, #e0e0e0);
  font-size: 16px;
  font-weight: 500;
}

.loading-subtext {
  color: var(--copilot-text-secondary, #a0a0a0);
  font-size: 14px;
  margin-top: 8px;
}

.bi-embed-frame {
  width: 100% !important;
  height: 100% !important;
  min-height: 100% !important;
  position: relative;
  flex: 1;
  overflow: hidden; /* 保持 hidden，但确保 iframe 内部可以滚动 */
  
  &.loading {
    visibility: hidden;
    opacity: 0;
  }
  
  :deep(iframe) {
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    max-width: 100% !important;
    max-height: 100% !important;
    border: 0 !important;
    display: block !important;
    background: #fff;
    position: absolute;
    top: 0;
    left: 0;
  }
  
  /* 确保所有子元素填充整个容器 */
  :deep(> *) {
    width: 100% !important;
    height: 100% !important;
  }
  
  /* 针对 Superset SDK 创建的容器 */
  :deep([class*="superset"]) {
    width: 100% !important;
    height: 100% !important;
  }
}

.credential-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 8px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border-radius: 4px;
}

.credential-item .label {
  width: 50px;
  color: var(--copilot-text-secondary, #a0a0a0);
  font-weight: 500;
}

.credential-item .value {
  flex: 1;
  font-family: monospace;
  font-size: 14px;
  color: var(--copilot-brand-primary, #00c6ff);
  background: rgba(0, 198, 255, 0.1);
  padding: 2px 6px;
  border-radius: 2px;
  margin-right: 8px;
}

/* ==================== 深色主题全局样式 ==================== */
.classroom-detail-page.copilot-theme {
  background-color: var(--copilot-bg-primary, #f5f5f5);
  color: var(--copilot-text-primary, #e0e0e0);
  min-height: 100%;
}

.copilot-theme .menu-item {
  color: var(--copilot-text-secondary, #a0a0a0);
}

.copilot-theme .menu-item:hover {
  background-color: var(--copilot-bg-hover, rgba(255, 255, 255, 0.05));
}

.copilot-theme .content-area {
  color: var(--copilot-text-primary, #e0e0e0);
}

/* Ant Design 组件深色覆盖 */
.copilot-theme :deep(.ant-btn-primary) {
  background: var(--copilot-brand-primary, #00c6ff);
  border-color: var(--copilot-brand-primary, #00c6ff);
}

.copilot-theme :deep(.ant-btn-primary:hover) {
  background: var(--copilot-brand-hover, #00e1ff);
  border-color: var(--copilot-brand-hover, #00e1ff);
}

.copilot-theme :deep(.ant-btn-link) {
  color: var(--copilot-brand-primary, #00c6ff);
}

.copilot-theme :deep(.ant-modal-content) {
  background: var(--copilot-bg-secondary, #ffffff);
  border: 1px solid var(--copilot-border-default, #e8e8e8);
}

.copilot-theme :deep(.ant-modal-header) {
  background: transparent;
  border-bottom-color: var(--copilot-border-default, #e8e8e8);
}

.copilot-theme :deep(.ant-modal-title) {
  color: var(--copilot-text-primary, #e0e0e0);
}

.copilot-theme :deep(.ant-modal-close-x) {
  color: var(--copilot-text-secondary, #a0a0a0);
}

.copilot-theme :deep(.ant-modal-body) {
  color: var(--copilot-text-primary, #e0e0e0);
}

.copilot-theme :deep(.ant-modal-footer) {
  border-top-color: var(--copilot-border-default, #e8e8e8);
}

.copilot-theme :deep(.ant-tag) {
  background: var(--copilot-bg-tertiary, #fafafa);
  border-color: var(--copilot-border-default, #e8e8e8);
  color: var(--copilot-text-secondary, #a0a0a0);
}

.copilot-theme :deep(.ant-spin-text) {
  color: var(--copilot-text-secondary, #a0a0a0);
}
</style>