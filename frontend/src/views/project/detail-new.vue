<template>
  <PageShell max-width="wide" class="project-detail-shell">
    <PageHeaderBar
      :title="projectDetail?.title || '实训详情'"
      :subtitle="detailSubtitle"
      show-back
      back-to="/project"
    >
      <template #actions>
        <a-button
          v-if="primaryEnterAction"
          type="primary"
          @click="primaryEnterAction.handler"
        >
          {{ primaryEnterAction.label }}
        </a-button>
        <a-button
          v-if="userStore.isLoggedIn && (userStore.userInfo?.role === 'teacher' || userStore.userInfo?.role === 'admin')"
          @click="showAddToClassroomModal = true"
        >
          <PlusOutlined /> 添加至课堂
        </a-button>
      </template>
    </PageHeaderBar>

  <div class="project-detail-page">
    <a-spin :spinning="loading" tip="加载中...">
      <template v-if="projectDetail">
        <!-- Banner横幅 -->
        <div class="project-banner">
          <div class="banner-content">
            <h1 class="banner-title">{{ projectDetail.title }}</h1>
            <div class="banner-stats">
              <span class="stat-item">
                <TeamOutlined /> {{ projectDetail.enrollCount || 0 }}人已参与
              </span>
              <span class="stat-item">
                <ClockCircleOutlined /> 预计{{ projectDetail.duration }}
              </span>
            </div>
          </div>
          <div class="banner-decoration">
            <!-- 装饰性图标 -->
            <div class="decoration-icon"></div>
          </div>
        </div>

        <!-- 元信息条 -->
        <div class="breadcrumb-section">
          <div class="breadcrumb-container">
            <div class="breadcrumb-items">
              <span class="breadcrumb-item">
                <span class="breadcrumb-label">难易程度</span>
                <span class="breadcrumb-separator">-</span>
                <span class="breadcrumb-value">{{ getDifficultyName(projectDetail.difficulty) }}</span>
              </span>
              <span class="breadcrumb-divider">/</span>
              <span class="breadcrumb-item">
                <span class="breadcrumb-label">所属行业</span>
                <span class="breadcrumb-separator">-</span>
                <span class="breadcrumb-value">{{ getIndustryName(projectDetail.industry) }}</span>
              </span>
              <span class="breadcrumb-divider">/</span>
              <span class="breadcrumb-item">
                <span class="breadcrumb-label">模式</span>
                <span class="breadcrumb-separator">-</span>
                <span class="breadcrumb-value">{{ getTrainingTypeName(projectDetail.trainingType) }}</span>
              </span>
              <span class="breadcrumb-divider">/</span>
              <span class="breadcrumb-item">
                <span class="breadcrumb-label">工具</span>
                <span class="breadcrumb-separator">-</span>
                <span class="breadcrumb-value">TempoBi</span>
              </span>
            </div>
          </div>
        </div>

        <!-- 主要内容区域 -->
        <div class="detail-container">
          <a-row :gutter="[16, 16]">
            <!-- 左侧内容区域 -->
            <a-col :xs="24" :lg="18">
              <!-- 实训手册内容 -->
              <div class="handbook-content-wrapper">
                <div class="handbook-title">实训手册</div>
                <div class="handbook-body">
                  <div v-html="renderMarkdown(processedHandbookContent)"></div>
                </div>
              </div>
            </a-col>

            <!-- 右侧侧边栏 -->
            <a-col :xs="24" :lg="6">
              <!-- 实训资讯（目录导航） -->
              <a-card class="toc-card" title="实训资讯">
                <div class="toc-wrapper">
                  <TOCTree
                    :nodes="handbookTOC"
                    :activeAnchor="activeAnchor"
                    @node-click="handleTOCClick"
                  />
                </div>
              </a-card>

              <!-- 操作卡片 -->
              <a-card class="action-card">
                <div class="action-buttons">
                  <a-button
                    v-if="canViewTraining"
                    type="primary"
                    size="large"
                    block
                    @click="handleViewTraining"
                  >
                    <EyeOutlined /> 查看实训
                  </a-button>

                  <a-button
                    v-if="userStore.isLoggedIn && (userStore.userInfo?.role === 'teacher' || userStore.userInfo?.role === 'admin')"
                    size="large"
                    block
                    @click="showAddToClassroomModal = true"
                  >
                    <PlusOutlined /> 添加至课堂
                  </a-button>

                  <a-button
                    v-if="codeTasks.length > 0"
                    type="primary"
                    size="large"
                    block
                    @click="openFirstCodeTask"
                  >
                    <CodeOutlined /> 编程实训
                  </a-button>
                </div>

                <a-divider />

                <!-- 项目信息 -->
                <div class="project-info">
                  <div class="info-item">
                    <span class="info-label">实训模式</span>
                    <span class="info-value">{{ getEnvironmentTypeText() }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">创建时间</span>
                    <span class="info-value">{{ projectDetail.createdAt }}</span>
                  </div>
                  <div class="info-item" v-if="projectDetail.creator_name">
                    <span class="info-label">创建者</span>
                    <div class="author-info">
                      <span>{{ projectDetail.creator_name }}</span>
                    </div>
                  </div>
                </div>
              </a-card>

              <!-- 编程实训成绩（教师/Admin） -->
              <a-card
                v-if="isTeacherRole && codeTasks.length > 0"
                class="code-grades-card"
                title="编程实训成绩"
              >
                <div class="code-grades-controls">
                  <a-select
                    v-model:value="selectedGradeTaskId"
                    placeholder="选择关卡"
                    size="small"
                    style="width: 100%"
                    @change="fetchCodeTaskGrades"
                  >
                    <a-select-option
                      v-for="task in codeTasks"
                      :key="task.id"
                      :value="task.id"
                    >
                      {{ task.order_in_training }}. {{ task.title }}
                    </a-select-option>
                  </a-select>

                  <a-select
                    v-model:value="selectedGradeClassroomId"
                    placeholder="选择课堂"
                    size="small"
                    style="width: 100%"
                    @change="fetchCodeTaskGrades"
                  >
                    <a-select-option
                      v-for="classroom in userClassrooms"
                      :key="classroom.id"
                      :value="classroom.id"
                    >
                      {{ classroom.name || `课堂 ${classroom.id}` }}
                    </a-select-option>
                  </a-select>

                  <a-select
                    v-model:value="selectedGradeStatus"
                    size="small"
                    style="width: 100%"
                    @change="fetchCodeTaskGrades"
                  >
                    <a-select-option
                      v-for="option in gradeStatusOptions"
                      :key="option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </a-select-option>
                  </a-select>
                </div>

                <div v-if="codeGradeSummary" class="code-grade-summary">
                  <span>全部 {{ codeGradeSummary.all || 0 }}</span>
                  <span>已提交 {{ codeGradeSummary.submitted || 0 }}</span>
                  <span>已通过 {{ codeGradeSummary.passed || 0 }}</span>
                </div>

                <a-table
                  :columns="codeGradeColumns"
                  :data-source="codeGradeRows"
                  :loading="codeGradesLoading"
                  :pagination="false"
                  size="small"
                  row-key="student_id"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'status'">
                      <a-tag :color="getCodeGradeStatusColor(record.grade_status)">
                        {{ getCodeGradeStatusText(record.grade_status) }}
                      </a-tag>
                    </template>
                    <template v-else-if="column.key === 'score'">
                      {{ record.passed_tests }}/{{ record.total_tests }} · {{ record.score }}分
                    </template>
                  </template>
                </a-table>
              </a-card>

              <!-- 数据集资源 -->
              <a-card class="resource-card" v-if="projectDetail.datasets && projectDetail.datasets.length > 0">
                <h3>数据集资源</h3>
                <div class="dataset-list">
                  <div
                    v-for="dataset in projectDetail.datasets"
                    :key="dataset.id"
                    class="dataset-item"
                  >
                    <span class="dataset-name">{{ dataset.name }}</span>
                    <span class="dataset-size">{{ formatFileSize(dataset.size) }}</span>
                  </div>
                </div>
              </a-card>

              <!-- 标签云 -->
              <a-card class="tags-card" v-if="projectDetail.tags && projectDetail.tags.length > 0">
                <h3>相关标签</h3>
                <div class="tag-cloud">
                  <a-tag v-for="tag in projectDetail.tags" :key="tag" color="blue">
                    {{ tag }}
                  </a-tag>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </template>

      <!-- 404页面 -->
      <template v-else-if="!loading">
        <a-result
          status="404"
          title="项目不存在"
          sub-title="您访问的项目可能已被删除或暂时不可用"
        >
          <template #extra>
            <a-button type="primary" @click="goBack">
              返回列表
            </a-button>
          </template>
        </a-result>
      </template>
    </a-spin>

    <!-- 添加至课堂弹窗 -->
    <a-modal
      v-model:open="showAddToClassroomModal"
      title="添加至课堂"
      width="600px"
      @ok="handleAddToClassroom"
      :confirmLoading="addingToClassroom"
    >
      <div class="add-classroom-content">
        <a-form :model="classroomForm" layout="vertical">
          <a-form-item label="选择课堂" required>
            <a-select
              v-model:value="classroomForm.classroomId"
              placeholder="请选择要添加到的课堂"
              size="large"
              @change="onClassroomChange"
            >
              <a-select-option
                v-for="classroom in userClassrooms"
                :key="classroom.id"
                :value="classroom.id"
              >
                {{ classroom.name || `课堂 ${classroom.id}` }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="开始时间">
            <a-date-picker
              v-model:value="classroomForm.startDate"
              format="YYYY-MM-DD"
              placeholder="选择开始时间"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="结束时间">
            <a-date-picker
              v-model:value="classroomForm.endDate"
              format="YYYY-MM-DD"
              placeholder="选择结束时间"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item>
            <a-checkbox v-model:checked="classroomForm.isRequired">
              设为必修项目
            </a-checkbox>
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
  </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  TeamOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  PlusOutlined,
  EyeOutlined,
  CodeOutlined
} from '@ant-design/icons-vue';
import {
  getProjectDetail,
  addProjectToClassroom,
  getTrainingCodeTasks,
  getTrainingCodeTaskGrades
} from '@/api/training';
import { getUserClassrooms, techerClassRooms } from '@/api/classrooms';
import type { ProjectDetail } from '@/api/types/project';
import type { TrainingCodeGradeRow, TrainingCodeTask } from '@/api/training';
import MarkdownIt from 'markdown-it';
// useEnvironmentControl 已移除 - Phase 1 修复
// 环境启动将在"我的课堂"的"开始实训"功能中实现
import { useUserStore } from '@/stores/user';
import { useHandbookParser } from '@/composables/useHandbookParser';
import type { TOCNode } from '@/composables/useHandbookParser';
import TOCTree from '@/components/common/TOCTree.vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const route = useRoute();
const router = useRouter();
// const environmentControl = useEnvironmentControl(); // 已移除
const userStore = useUserStore();
const handbookParser = useHandbookParser();

// 状态
const loading = ref(false);
const projectDetail = ref<ProjectDetail | null>(null);
const activeTab = ref('manual');
const showAddToClassroomModal = ref(false);
const addingToClassroom = ref(false);
const userClassrooms = ref<any[]>([]);
const codeTasks = ref<TrainingCodeTask[]>([]);
const selectedGradeTaskId = ref<number | undefined>();
const selectedGradeClassroomId = ref<number | string | undefined>();
const selectedGradeStatus = ref('all');
const codeGradesLoading = ref(false);
const codeGradeRows = ref<TrainingCodeGradeRow[]>([]);
const codeGradeSummary = ref<Record<string, number> | null>(null);

// 手册相关状态
const handbookContent = ref<string>(''); // 原始Markdown内容
const handbookTOC = ref<TOCNode[]>([]); // 目录树
const processedHandbookContent = ref<string>(''); // 添加了锚点的内容
const activeAnchor = ref<string>(''); // 当前激活的锚点

// 表单
const classroomForm = ref({
  classroomId: '',
  startDate: null,
  endDate: null,
  isRequired: false
});

// Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

// 计算属性
const projectId = computed(() => route.params.id as string);

// 课堂选项 - 转换为 Ant Design Select 格式
const classroomOptions = computed(() => {
  return userClassrooms.value.map(classroom => ({
    label: classroom.name || `课堂 ${classroom.id}`,
    value: classroom.id
  }));
});

const isTeacherRole = computed(() => {
  return userStore.userRole === 'teacher' || userStore.userRole === 'admin';
});

const canViewTraining = computed(() => {
  return ['BI', 'AI', 'JUPYTER'].includes(projectDetail.value?.designer_type || '');
});

const detailSubtitle = computed(() => {
  if (!projectDetail.value) return '项目实训详情';
  const parts = [
    getDifficultyName(projectDetail.value.difficulty),
    getIndustryName(projectDetail.value.industry),
    getTrainingTypeName(projectDetail.value.trainingType),
  ].filter(Boolean);
  return parts.join(' · ') || '项目实训详情';
});

/** Header 单一 primary：优先编程实训，否则进入设计器/Jupyter */
const primaryEnterAction = computed(() => {
  if (codeTasks.value.length > 0) {
    return { label: '进入实训', handler: openFirstCodeTask };
  }
  if (canViewTraining.value) {
    return { label: '进入实训', handler: handleViewTraining };
  }
  return null;
});

const gradeStatusOptions = [
  { value: 'all', label: '全部' },
  { value: 'not_started', label: '未开始' },
  { value: 'submitted', label: '已提交' },
  { value: 'passed', label: '已通过' },
  { value: 'failed', label: '未通过' },
  { value: 'completed', label: '已完成' },
  { value: 'incomplete', label: '未完成' },
  { value: 'perfect', label: '满分' }
];

const codeGradeColumns = [
  { title: '学生', dataIndex: 'student_name', key: 'student_name' },
  { title: '状态', dataIndex: 'grade_status', key: 'status' },
  { title: '成绩', dataIndex: 'score', key: 'score' }
];

// 获取名称的辅助函数
const getIndustryName = (industry: any) => {
  return typeof industry === 'string' ? industry : industry?.name || '未知';
};

const getTrainingTypeName = (type: any) => {
  if (typeof type === 'string') {
    const typeMap: Record<string, string> = {
      'dragdrop': '拖拽式',
      'DRAG_DROP': '拖拽式',
      'coding': '编码式',
      'CODING': '编码式',
      'JUPYTER': 'Jupyter编码式',
      'DATA_ANALYSIS': '数据分析',
      'BI': 'BI可视化分析'
    };
    return typeMap[type] || type;
  }
  return type?.name || '未知';
};

const getDifficultyName = (difficulty: any) => {
  if (typeof difficulty === 'string') {
    const map: Record<string, string> = {
      'easy': '初级',
      'beginner': '初级',
      'medium': '中级',
      'intermediate': '中级',
      'hard': '高级',
      'advanced': '高级'
    };
    return map[difficulty] || difficulty;
  }
  return difficulty?.name || '未知';
};

const getEnvironmentTypeText = () => {
  if (!projectDetail.value) return '';

  // 环境类型映射
  const typeMap: Record<string, string> = {
    'jupyter': 'Jupyter编码式',
    'visual': 'BI可视化分析',
    'ml': 'AI机器学习',
    'code': '编程环境',
    'gwalk_bi': 'BI可视化分析',
    'tempo_ai': 'AI机器学习'
  };

  // 优先使用 environment_type，其次根据 training_type 推断
  const envType = projectDetail.value.environment_type;
  if (envType && typeMap[envType]) {
    return typeMap[envType];
  }

  // 根据 training_type 推断
  const trainingType = projectDetail.value.trainingType;
  const trainingTypeStr = typeof trainingType === 'string' ? trainingType : trainingType?.id;

  if (['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(trainingTypeStr)) {
    return 'BI可视化分析';
  }
  if (['CODING', 'JUPYTER'].includes(trainingTypeStr)) {
    return 'Jupyter编码式';
  }
  if (['ML', 'AI'].includes(trainingTypeStr)) {
    return 'AI机器学习';
  }

  return projectDetail.value.model_text || '未知类型';
};

// 方法
const fetchProjectDetail = async () => {
  try {
    loading.value = true;
    const response = await getProjectDetail(projectId.value);

    console.log('[DEBUG] 获取到的项目详情:', response);
    console.log('[DEBUG] response的所有字段:', Object.keys(response));
    console.log('[DEBUG] content字段:', response.content);
    console.log('[DEBUG] handbook_content字段:', response.handbook_content);

    projectDetail.value = response;

    // 解析handbook内容 - backend返回的是content字段
    if (projectDetail.value && projectDetail.value.content) {
      handbookContent.value = projectDetail.value.content;
      console.log('[DEBUG] 成功获取handbook内容，长度:', handbookContent.value.length);

      // 生成目录树
      handbookTOC.value = handbookParser.parseMarkdownTOC(handbookContent.value);
      console.log('[DEBUG] 生成的目录树:', handbookTOC.value);

      // 添加锚点
      processedHandbookContent.value = handbookParser.addAnchorsToMarkdown(handbookContent.value);
      console.log('[DEBUG] 处理后的内容长度:', processedHandbookContent.value.length);
    } else {
      console.warn('[DEBUG] 没有找到content字段或为空');
      console.log('[DEBUG] projectDetail.value:', projectDetail.value);
      console.log('[DEBUG] 尝试使用第一段description作为placeholder...');
      // 如果没有content，使用description作为临时内容
      if (projectDetail.value && projectDetail.value.description) {
        handbookContent.value = `# ${projectDetail.value.title}\n\n${projectDetail.value.description}`;
        processedHandbookContent.value = handbookParser.addAnchorsToMarkdown(handbookContent.value);
      }
    }
  } catch (error) {
    console.error('获取项目详情失败:', error);
    message.error('获取项目详情失败');
  } finally {
    loading.value = false;
  }
};

const fetchCodeTasks = async () => {
  try {
    const response = await getTrainingCodeTasks(projectId.value);
    codeTasks.value = response.tasks || [];
    if (!selectedGradeTaskId.value && codeTasks.value.length > 0) {
      selectedGradeTaskId.value = codeTasks.value[0].id;
    }
    await fetchCodeTaskGrades();
  } catch (error) {
    console.warn('获取编程实训任务失败:', error);
    codeTasks.value = [];
  }
};

const fetchUserClassrooms = async () => {
  try {
    console.log('[DEBUG] fetchUserClassrooms called, userRole:', userStore.userRole);
    
    if (userStore.userRole === 'teacher' || userStore.userRole === 'admin') {
      // 教师或管理员获取他们创建的课堂
      console.log('[DEBUG] 教师角色，调用 techerClassRooms');
      const response = await techerClassRooms({ teacher_id: userStore.userId });
      console.log('[DEBUG] techerClassRooms response:', response);
      
      // 合并各个状态的课堂
      const classroomsList = [
        ...(response.data?.ongoing || []),
        ...(response.data?.upcoming || []),
        ...(response.data?.ended || [])
      ];
      
      console.log('[DEBUG] 合并后的课堂列表:', classroomsList);
      userClassrooms.value = classroomsList;
      if (!selectedGradeClassroomId.value && classroomsList.length > 0) {
        selectedGradeClassroomId.value = classroomsList[0].id;
      }
    } else if (userStore.userRole === 'student' && userStore.userId) {
      // 学生获取他们加入的课堂
      console.log('[DEBUG] 学生角色，调用 getUserClassrooms');
      const response = await getUserClassrooms(userStore.userId);
      console.log('[DEBUG] getUserClassrooms response:', response);
      userClassrooms.value = response.data || [];
    } else {
      userClassrooms.value = [];
    }
    
    console.log('[DEBUG] 最终课堂列表:', userClassrooms.value);
    await fetchCodeTaskGrades();
  } catch (error) {
    console.error('获取课堂列表失败:', error);
    userClassrooms.value = [];
  }
};

const fetchCodeTaskGrades = async () => {
  if (!isTeacherRole.value || !selectedGradeTaskId.value || !selectedGradeClassroomId.value) {
    return;
  }

  try {
    codeGradesLoading.value = true;
    const response = await getTrainingCodeTaskGrades(
      projectId.value,
      selectedGradeTaskId.value,
      selectedGradeClassroomId.value,
      selectedGradeStatus.value
    );
    codeGradeRows.value = response.grades || [];
    codeGradeSummary.value = response.summary || null;
  } catch (error) {
    console.warn('获取编程实训成绩失败:', error);
    codeGradeRows.value = [];
    codeGradeSummary.value = null;
  } finally {
    codeGradesLoading.value = false;
  }
};

const renderMarkdown = (content: string) => {
  // 如果是处理过的内容（包含锚点），直接渲染
  // 否则使用传入的content
  const contentToRender = content || processedHandbookContent.value || handbookContent.value;
  return md.render(contentToRender);
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 课堂选择变化事件处理
const onClassroomChange = (classroomId: number | string) => {
  console.log('[DEBUG] 课堂选择变化:', classroomId);
  classroomForm.value.classroomId = String(classroomId);
};

const goBack = () => {
  router.push('/project');
};

const openFirstCodeTask = () => {
  const firstTask = codeTasks.value[0];
  if (firstTask) {
    router.push(`/project/${projectId.value}/code/${firstTask.id}`);
  }
};

const getCodeGradeStatusText = (status: string) => {
  const map: Record<string, string> = {
    not_started: '未开始',
    submitted: '已提交',
    passed: '已通过',
    failed: '未通过'
  };
  return map[status] || status || '未开始';
};

const getCodeGradeStatusColor = (status: string) => {
  const map: Record<string, string> = {
    not_started: 'default',
    submitted: 'blue',
    passed: 'green',
    failed: 'red'
  };
  return map[status] || 'default';
};

const handleTOCClick = (anchorId: string) => {
  // 更新当前激活的锚点
  activeAnchor.value = anchorId;

  // 滚动到对应的章节
  const element = document.getElementById(anchorId);
  if (element) {
    element.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
  }
};

const handleViewTraining = () => {
  const designerType = projectDetail.value?.designer_type;
  const trainingId = projectDetail.value?.id || projectId.value;

  if (designerType === 'BI') {
    router.push(`/bi-designer/${trainingId}`);
    return;
  }
  if (designerType === 'AI') {
    router.push(`/ai-designer/${trainingId}`);
    return;
  }
  if (designerType === 'JUPYTER') {
    router.push(`/jupyter/${trainingId}`);
    return;
  }

  message.warning('该实训暂未配置操作环境');
};

const handleAddToClassroom = async () => {
  if (!classroomForm.value.classroomId) {
    message.warning('请选择课堂');
    return;
  }
  
  if (!projectDetail.value) return;
  
  try {
    addingToClassroom.value = true;
    
    await addProjectToClassroom(classroomForm.value.classroomId, {
      id: projectDetail.value.id,
      title: projectDetail.value.title,
      description: projectDetail.value.description,
      industry: typeof projectDetail.value.industry === 'object' 
        ? projectDetail.value.industry 
        : { id: projectDetail.value.industry, name: projectDetail.value.industry },
      trainingType: typeof projectDetail.value.trainingType === 'object'
        ? projectDetail.value.trainingType
        : { id: projectDetail.value.trainingType, name: projectDetail.value.trainingType },
      startDate: classroomForm.value.startDate?.format('YYYY-MM-DD'),
      endDate: classroomForm.value.endDate?.format('YYYY-MM-DD'),
      isRequired: classroomForm.value.isRequired
    });
    
    message.success('已成功添加到课堂');
    showAddToClassroomModal.value = false;
    
    // 重置表单
    classroomForm.value = {
      classroomId: '',
      startDate: null,
      endDate: null,
      isRequired: false
    };
  } catch (error) {
    console.error('添加到课堂失败:', error);
    message.error('添加失败，请重试');
  } finally {
    addingToClassroom.value = false;
  }
};

// 生命周期
onMounted(() => {
  fetchProjectDetail();
  fetchCodeTasks();
  fetchUserClassrooms();

  // 添加滚动监听
  window.addEventListener('scroll', handleScroll);
});

// 监听模态框打开，当打开时重新获取课堂列表
watch(showAddToClassroomModal, async (newVal) => {
  if (newVal) {
    console.log('[DEBUG] 模态框打开，重新获取课堂列表');
    await fetchUserClassrooms();
    await nextTick(); // 确保 DOM 更新
    console.log('[DEBUG] 课堂列表获取完成，userClassrooms:', userClassrooms.value);
    console.log('[DEBUG] classroomOptions 计算结果:', classroomOptions.value);
  }
});

onUnmounted(() => {
  // 移除滚动监听
  window.removeEventListener('scroll', handleScroll);
});

// 滚动监听处理函数
const handleScroll = () => {
  // 使用节流避免频繁触发
  if (!handbookTOC.value.length) return;

  // 获取所有章节元素
  const flattenedNodes = handbookParser.flattenTOC(handbookTOC.value);

  let currentAnchor = '';
  let minDistance = Infinity;

  // 查找当前最接近顶部的章节
  flattenedNodes.forEach((node) => {
    const element = document.getElementById(node.anchorId);
    if (element) {
      const rect = element.getBoundingClientRect();
      const distance = Math.abs(rect.top - 100); // 100px 的偏移量

      if (rect.top < 200 && distance < minDistance) {
        minDistance = distance;
        currentAnchor = node.anchorId;
      }
    }
  });

  if (currentAnchor && currentAnchor !== activeAnchor.value) {
    activeAnchor.value = currentAnchor;
  }
};
</script>

<style scoped>
.project-detail-page {
  background-color: #f0f2f5;
  min-height: 100vh;
  padding-bottom: 40px;
}

/* ==================== Banner横幅 ==================== */
.project-banner {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 60px 24px 40px;
  margin-bottom: 0;
  overflow: hidden;
}

.project-banner::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 300"><path fill="%23ffffff" fill-opacity="0.05" d="M0,100 Q300,150 600,100 T1200,100 L1200,300 L0,300 Z"/></svg>') no-repeat bottom center;
  background-size: cover;
}

.banner-content {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
}

.banner-title {
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.banner-stats {
  display: flex;
  gap: 24px;
  font-size: 14px;
  opacity: 0.95;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.banner-decoration {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  width: 200px;
  height: 200px;
  opacity: 0.1;
}

.decoration-icon {
  width: 100%;
  height: 100%;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><circle cx="100" cy="100" r="80" fill="%23ffffff"/></svg>') no-repeat center;
  background-size: contain;
}

/* ==================== 面包屑导航 ==================== */
.breadcrumb-section {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
  margin-bottom: 24px;
}

.breadcrumb-container {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-detail-shell {
  min-height: 100%;
}

.back-btn {
  padding: 0;
  height: auto;
  font-size: 14px;
  color: #1677ff;
}

.breadcrumb-items {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 14px;
  color: #595959;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.breadcrumb-label {
  color: #8c8c8c;
}

.breadcrumb-separator {
  color: #bfbfbf;
  margin: 0 2px;
}

.breadcrumb-value {
  color: #262626;
  font-weight: 500;
}

.breadcrumb-divider {
  color: #d9d9d9;
  margin: 0 4px;
}

/* ==================== 主要内容区域 ==================== */
.detail-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 0;
}

.code-grades-card {
  margin-top: 16px;
}

.code-grades-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.code-grade-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  margin-bottom: 12px;
  color: #595959;
  font-size: 13px;
}

/* ==================== 实训手册内容 ==================== */
.handbook-content-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 32px;
  margin-bottom: 24px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
}

.handbook-title {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #1890ff;
}

.handbook-body {
  line-height: 1.8;
  color: #595959;
}

/* Markdown内容样式 */
.handbook-body :deep(h1) {
  font-size: 28px;
  font-weight: 600;
  color: #262626;
  margin-top: 32px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.handbook-body :deep(h2) {
  font-size: 24px;
  font-weight: 600;
  color: #262626;
  margin-top: 28px;
  margin-bottom: 14px;
}

.handbook-body :deep(h3) {
  font-size: 20px;
  font-weight: 600;
  color: #262626;
  margin-top: 24px;
  margin-bottom: 12px;
}

.handbook-body :deep(h4) {
  font-size: 18px;
  font-weight: 600;
  color: #595959;
  margin-top: 20px;
  margin-bottom: 10px;
}

.handbook-body :deep(p) {
  margin-bottom: 16px;
}

.handbook-body :deep(ul),
.handbook-body :deep(ol) {
  margin-left: 24px;
  margin-bottom: 16px;
}

.handbook-body :deep(li) {
  margin-bottom: 8px;
}

.handbook-body :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
}

.handbook-body :deep(pre) {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 16px;
}

.handbook-body :deep(pre code) {
  background: none;
  padding: 0;
}

.handbook-body :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  margin: 16px 0;
}

.handbook-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

.handbook-body :deep(th),
.handbook-body :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}

.handbook-body :deep(th) {
  background-color: #fafafa;
  font-weight: 600;
}

.handbook-body :deep(blockquote) {
  border-left: 4px solid #1890ff;
  padding-left: 16px;
  margin: 16px 0;
  color: #595959;
  background-color: #f0f7ff;
  padding: 12px 16px;
  border-radius: 4px;
}

/* ==================== 右侧侧边栏 ==================== */
.toc-card {
  position: sticky;
  top: 24px;
  margin-bottom: 24px;
  max-height: calc(100vh - 100px);
  overflow: hidden;
}

.toc-wrapper {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 8px;
}

.toc-wrapper::-webkit-scrollbar {
  width: 6px;
}

.toc-wrapper::-webkit-scrollbar-track {
  background: #f0f0f0;
  border-radius: 3px;
}

.toc-wrapper::-webkit-scrollbar-thumb {
  background: #bfbfbf;
  border-radius: 3px;
}

.toc-wrapper::-webkit-scrollbar-thumb:hover {
  background: #8c8c8c;
}

.action-card {
  position: sticky;
  top: calc(24px + 560px);
  margin-bottom: 24px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.add-classroom-btn {
  border-color: #52c41a;
  color: #52c41a;
}

.add-classroom-btn:hover {
  border-color: #73d13d;
  color: #73d13d;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.info-label {
  color: #8c8c8c;
}

.info-value {
  color: #262626;
  font-weight: 500;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.resource-card,
.tags-card {
  margin-bottom: 24px;
}

.resource-card h3,
.tags-card h3 {
  font-size: 16px;
  margin-bottom: 16px;
  color: #262626;
}

.dataset-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dataset-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 14px;
}

.dataset-name {
  color: #262626;
}

.dataset-size {
  color: #8c8c8c;
  font-size: 12px;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.add-classroom-content {
  padding: 16px 0;
}

/* ==================== 响应式布局 ==================== */
@media (max-width: 768px) {
  .project-banner {
    padding: 40px 16px 24px;
  }

  .banner-title {
    font-size: 24px;
  }

  .banner-decoration {
    display: none;
  }

  .breadcrumb-section {
    padding: 12px 16px;
  }

  .breadcrumb-items {
    font-size: 13px;
  }

  .detail-container {
    padding: 0 16px;
  }

  .handbook-content-wrapper {
    padding: 20px;
  }

  .handbook-title {
    font-size: 20px;
  }

  .toc-card,
  .action-card {
    position: static;
  }
}
</style>
