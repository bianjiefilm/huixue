<template>
  <div class="course-exam-page">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 返回按钮 -->
      <div class="back-link">
        <router-link :to="`/classroom/${classroomId}/course/${courseId}`">
          <a-button type="link">
            <template #icon><arrow-left-outlined /></template>
            返回课程
          </a-button>
        </router-link>
      </div>

      <!-- 页面标题 -->
      <div class="page-header">
        <h1>课程考核</h1>
        <a-button 
          type="primary" 
          @click="showCreateExamModal" 
          v-if="isTeacherView"
        >
          <template #icon><plus-outlined /></template>
          创建考试
        </a-button>
      </div>

      <!-- 考试列表 -->
      <div class="exams-container">
        <a-empty v-if="examList.length === 0" description="暂无考试" />
        
        <div v-else class="exam-cards">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12" :md="8" v-for="exam in examList" :key="exam.id">
              <a-card class="exam-card" :bordered="false" :class="getStatusClass(exam)">
                <template #title>
                  <div 
                    class="exam-title" 
                    :class="{ 'editable': isExamEditable(exam) && exam.id === editingExamId }"
                    @click="handleExamTitleClick(exam)"
                  >
                    <a-input 
                      v-if="isExamEditable(exam) && exam.id === editingExamId"
                      v-model:value="editingExamName"
                      @blur="saveExamName(exam)"
                      @keyup.enter="saveExamName(exam)"
                      ref="editNameInput"
                      :maxLength="50"
                    />
                    <span v-else>{{ exam.exam_name }}</span>
                  </div>
                </template>
                
                <template #extra>
                  <a-tag :color="getStatusColor(exam)">{{ getStatusText(exam) }}</a-tag>
                </template>
                
                <div class="exam-info">
                  <div class="info-item">
                    <book-outlined />
                    <span>试卷：{{ exam.test_paper_name }}</span>
                  </div>
                  
                  <div class="info-item" v-if="exam.is_published">
                    <calendar-outlined />
                    <span>时间：{{ formatDateTime(exam.start_time) }} 至 {{ formatDateTime(exam.end_time) }}</span>
                  </div>
                  
                  <div class="info-item" v-if="exam.is_published">
                    <clock-circle-outlined />
                    <span>时长：{{ exam.time_limit_minutes }} 分钟</span>
                  </div>
                  
                  <div class="info-item" v-if="exam.is_published">
                    <check-circle-outlined />
                    <span>及格分数：{{ exam.passing_score }} 分</span>
                  </div>
                  
                  <div class="info-item" v-if="exam.is_published && (getStatusText(exam) === '进行中' || getStatusText(exam) === '已结束')">
                    <team-outlined />
                    <span>完成情况：{{ exam.submitted_count || 0 }}/{{ exam.student_count || 0 }} 人</span>
                  </div>
                  
                  <div class="info-item" v-if="getStatusText(exam) === '已结束'">
                    <trophy-outlined />
                    <span>通过人数：{{ exam.graded_count || 0 }} 人（{{ getPassRate(exam) }}）</span>
                  </div>
                </div>
                
                <div class="exam-actions">
                  <!-- 教师查看考试结果和阅卷按钮 -->
                  <a-space v-if="isTeacherView && exam.is_published && (getStatusText(exam) === '进行中' || getStatusText(exam) === '已结束')">
                    <a-button 
                      type="primary"
                      @click="viewExamResults(exam)"
                    >
                      阅卷
                    </a-button>
                    <a-button 
                      @click="viewResults(exam)"
                    >
                      查看结果
                    </a-button>
                  </a-space>
                  
                  <!-- 学生开始考试按钮 -->
                  <a-button 
                    v-if="!isTeacherView && getStatusText(exam) === '进行中'"
                    type="primary"
                    @click="startExam(exam)"
                  >
                    开始考试
                  </a-button>
                  
                  <!-- 发布考试按钮 (教师) -->
                  <a-button 
                    v-if="isTeacherView && !exam.is_published"
                    type="primary"
                    @click="showPublishModal(exam)"
                  >
                    发布
                  </a-button>
                  
                  <!-- 预览试卷按钮 -->
                  <a-button 
                    v-if="isTeacherView"
                    @click="previewExamPaper(exam)"
                  >
                    预览试卷
                  </a-button>
                  
                  <!-- 更多操作下拉菜单 (教师) -->
                  <a-dropdown v-if="isTeacherView && isExamEditable(exam)" :trigger="['click']">
                    <a-button>
                      <more-outlined />
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <!-- 未发布状态下可设置 -->
                        <a-menu-item v-if="exam.is_published && getStatusText(exam) === '未开始'" key="settings" @click="showExamSettingsModal(exam)">
                          <setting-outlined />
                          <span>设置</span>
                        </a-menu-item>
                        <!-- 未开始状态下可重命名 -->
                        <a-menu-item v-if="!exam.is_published || getStatusText(exam) === '未开始'" key="rename" @click="startRenaming(exam)">
                          <edit-outlined />
                          <span>重命名</span>
                        </a-menu-item>
                        <!-- 未发布状态下可删除 -->
                        <a-menu-item v-if="!exam.is_published" key="delete" @click="showDeleteConfirm(exam)">
                          <delete-outlined />
                          <span>删除</span>
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>
      </div>
    </a-spin>

    <a-modal
      v-model:open="createExamOptionModalVisible"
      title="创建考试"
      :footer="null"
      width="400px"
    >
      <div class="create-exam-options">
        <p style="margin-bottom: 20px; color: #666;">请选择创建考试的方式：</p>
        <a-space direction="vertical" style="width: 100%">
          <a-button block size="large" @click="handleSelectFromBank">
            <template #icon><book-outlined /></template>
            从试卷库选择
          </a-button>
          <a-button block size="large" type="primary" @click="handleCreateNewPaper">
            <template #icon><plus-outlined /></template>
            新建试卷
          </a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- 创建考试模态框 -->
    <a-modal
      v-model:open="createExamModalVisible"
      title="创建考试"
      @ok="handleCreateExam"
      :confirm-loading="createExamLoading"
      @cancel="cancelCreateExam"
      :maskClosable="false"
    >
      <a-form :model="newExam" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="考试名称" name="name" :rules="[{ required: true, message: '请输入考试名称' }]">
          <a-input v-model:value="newExam.name" placeholder="请输入考试名称" />
        </a-form-item>
        <a-form-item label="试卷" name="paperId" :rules="[{ required: true, message: '请选择试卷' }]">
          <a-select
            v-model:value="newExam.paperId"
            placeholder="选择试卷"
            @change="handlePaperChange"
            :disabled="newExam.paperId !== ''"
          >
            <a-select-option v-for="paper in paperList" :key="paper.id" :value="paper.id">
              {{ paper.paper_name }} ({{ paper.question_count }}题, {{ paper.total_score }}分)
            </a-select-option>
          </a-select>
        </a-form-item>
        
        <div v-if="newExam.paperId" class="paper-info">
          <div class="paper-info-item">
            <span class="label">试卷名称：</span>
            <span>{{ getSelectedPaper?.paper_name }}</span>
          </div>
          <div class="paper-info-item">
            <span class="label">题目数量：</span>
            <span>{{ getSelectedPaper?.question_count }}题</span>
          </div>
          <div class="paper-info-item">
            <span class="label">总分值：</span>
            <span>{{ getSelectedPaper?.total_score }}分</span>
          </div>
          <div class="paper-info-item">
            <span class="label">建议时长：</span>
            <span>{{ getSelectedPaper?.pass_score || 60 }}分钟</span>
          </div>
          <div class="paper-actions">
            <a-button type="link" @click="previewPaper">
              <template #icon><eye-outlined /></template>
              预览试卷
            </a-button>
          </div>
        </div>
      </a-form>
    </a-modal>

    <!-- 发布考试模态框 -->
    <a-modal
      v-model:open="publishModalVisible"
      title="发布考试"
      @ok="handlePublishExam"
      :confirm-loading="publishLoading"
      @cancel="cancelPublish"
      :maskClosable="false"
    >
      <a-form :model="publishForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="考试时间" name="examTime" :rules="[{ required: true, message: '请选择考试时间' }]">
          <a-range-picker 
            v-model:value="examTimeRange" 
            :show-time="{ format: 'HH:mm' }" 
            format="YYYY-MM-DD HH:mm"
            :disabled-date="disabledDate"
            @change="handleTimeRangeChange"
          />
        </a-form-item>
        
        <a-form-item label="考试时长(分钟)" name="duration" :rules="[{ required: true, message: '请输入考试时长' }]">
          <a-input-number 
            v-model:value="publishForm.duration" 
            :min="1" 
            :max="300" 
            style="width: 100%;"
            @change="validateTimeRange"
          />
        </a-form-item>
        
        <a-form-item 
          label="及格分数" 
          name="passingScore" 
          :rules="[{ required: true, message: '请输入及格分数' }]"
          extra="默认为试卷总分的60%"
        >
          <a-input-number 
            v-model:value="publishForm.passingScore" 
            :min="1" 
            :max="selectedExam ? (selectedExam.paper_total_score || 100) : 100" 
            style="width: 100%;"
          />
        </a-form-item>
        
        <a-form-item label="题目随机排序" name="shuffleQuestions">
          <a-switch v-model:checked="publishForm.shuffleQuestions" />
        </a-form-item>

        <a-form-item label="选项随机打乱" name="shuffleOptions">
          <a-switch v-model:checked="publishForm.shuffleOptions" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 考试设置模态框 -->
    <a-modal
      v-model:open="settingsModalVisible"
      title="考试设置"
      @ok="handleUpdateExamSettings"
      :confirm-loading="updateSettingsLoading"
      @cancel="cancelSettings"
      :maskClosable="false"
    >
      <a-form :model="settingsForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="考试时间" name="examTime" :rules="[{ required: true, message: '请选择考试时间' }]">
          <a-range-picker 
            v-model:value="settingsTimeRange" 
            :show-time="{ format: 'HH:mm' }" 
            format="YYYY-MM-DD HH:mm"
            :disabled-date="disabledDate"
            @change="handleSettingsTimeRangeChange"
          />
        </a-form-item>
        
        <a-form-item label="考试时长(分钟)" name="duration" :rules="[{ required: true, message: '请输入考试时长' }]">
          <a-input-number 
            v-model:value="settingsForm.duration" 
            :min="1" 
            :max="300" 
            style="width: 100%;"
            @change="validateSettingsTimeRange"
          />
        </a-form-item>
        
        <a-form-item 
          label="及格分数" 
          name="passingScore" 
          :rules="[{ required: true, message: '请输入及格分数' }]"
        >
          <a-input-number 
            v-model:value="settingsForm.passingScore" 
            :min="1" 
            :max="selectedExam ? (selectedExam.paper_total_score || 100) : 100" 
            style="width: 100%;"
          />
        </a-form-item>
        
        <a-form-item label="题目随机排序" name="shuffleQuestions">
          <a-switch v-model:checked="settingsForm.shuffleQuestions" />
        </a-form-item>

        <a-form-item label="选项随机打乱" name="shuffleOptions">
          <a-switch v-model:checked="settingsForm.shuffleOptions" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 试卷预览模态框 -->
    <a-modal
      v-model:open="paperPreviewModalVisible"
      title="试卷预览"
      width="800px"
      :footer="null"
    >
      <a-spin :spinning="paperLoading">
        <div v-if="previewPaperData" class="paper-preview-container">
          <div class="paper-header">
            <h2>{{ previewPaperData.paper_name }}</h2>
            <div class="paper-meta">
              <span>总分：{{ previewPaperData.total_score }}分</span>
              <span>题目数量：{{ previewPaperData.question_count }}题</span>
              <span>建议时长：{{ previewPaperData.suggest_duration || 60 }}分钟</span>
            </div>
          </div>

          <div class="paper-questions">
            <div v-for="(section, index) in previewPaperData.sections" :key="index" class="question-section">
              <h3>{{ section.section_name }} (共{{ section.questions.length }}题，{{ section.total_score }}分)</h3>
              
              <div v-for="(question, qIndex) in section.questions" :key="question.id" class="question-item">
                <div class="question-header">
                  <span class="question-number">{{ qIndex + 1 }}.</span>
                  <span class="question-type">[{{ getQuestionTypeName(question.question_type) }}]</span>
                  <span class="question-score">({{ question.score }}分)</span>
                </div>
                
                <div class="question-content" v-html="question.question_content"></div>
                
                <!-- 选项 (单选/多选/判断题) -->
                <div v-if="['single_choice', 'multiple_choice', 'true_false'].includes(question.question_type)" class="question-options">
                  <div v-for="(option, optIndex) in question.options" :key="optIndex" class="option-item">
                    <span class="option-label">{{ String.fromCharCode(65 + optIndex) }}.</span>
                    <span class="option-content">{{ option }}</span>
                  </div>
                </div>
                
                <!-- 答案区域 -->
                <div class="question-answer">
                  <div class="answer-label">参考答案：</div>
                  <div v-if="['single_choice', 'multiple_choice'].includes(question.question_type)">
                    {{ question.correct_answer }}
                  </div>
                  <div v-else-if="question.question_type === 'true_false'">
                    {{ question.correct_answer === '1' ? '正确' : '错误' }}
                  </div>
                  <div v-else v-html="question.answer_content"></div>
                </div>
                
                <!-- 解析 -->
                <div v-if="question.explanation" class="question-explanation">
                  <div class="explanation-label">解析：</div>
                  <div v-html="question.explanation"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 模态框底部按钮 -->
        <div class="modal-footer" style="margin-top: 20px; text-align: right; border-top: 1px solid #f0f0f0; padding-top: 16px;">
          <a-button style="margin-right: 8px;" @click="paperPreviewModalVisible = false">
            关闭
          </a-button>
          <a-button type="primary" @click="exportPaperToWord" :loading="exportLoading">
            <template #icon><file-word-outlined /></template>
            导出Word
          </a-button>
        </div>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import type { Dayjs } from 'dayjs';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  BookOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  TeamOutlined,
  TrophyOutlined,
  SettingOutlined,
  EditOutlined,
  DeleteOutlined,
  MoreOutlined,
  CheckCircleOutlined,
  EyeOutlined,
  FileWordOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import { useClassroomStore } from '@/stores/classroom';
import {
  getClassroomExams,
  getTestPapers,
  createExam,
  publishExam,
  renameExam,
  updateExam,
  deleteExam,
  getExamStatusText,
  getExamStatusColor,
  getPaperDetail,
  exportPaper,
  type ExamInfo,
  type TestPaper,
  type ExamCreateRequest,
  type ExamPublishRequest,
  type ExamUpdateRequest,
  type ExamRenameRequest
} from '@/api/exam';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const classroomStore = useClassroomStore();

// 路由参数
const classroomId = ref(route.params.classroomId as string);
const courseId = ref(route.params.courseId as string);

// 用户角色
const userRole = computed(() => userStore.userInfo.role || 'student');
const isTeacherView = computed(() => userRole.value === 'teacher' || userRole.value === 'admin');

// 页面状态
const loading = ref(true);
const examList = ref<ExamInfo[]>([]);
const paperList = ref<TestPaper[]>([]);

// 创建考试相关状态
const createExamModalVisible = ref(false);
const createExamLoading = ref(false);
const newExam = reactive({
  name: '',
  paperId: null as number | null,
  paperName: '',
  paperTotalScore: 0
});

// 发布考试相关状态
const publishModalVisible = ref(false);
const publishLoading = ref(false);
const selectedExam = ref<ExamInfo | null>(null);
const examTimeRange = ref<[Dayjs, Dayjs] | null>(null);
const publishForm = reactive({
  startTime: '',
  endTime: '',
  duration: 90,
  passingScore: 60,
  randomOrder: false,
  shuffleQuestions: false,
  shuffleOptions: false
});

// 考试设置相关状态
const settingsModalVisible = ref(false);
const updateSettingsLoading = ref(false);
const settingsTimeRange = ref<[Dayjs, Dayjs] | null>(null);
const settingsForm = reactive({
  startTime: '',
  endTime: '',
  duration: 90,
  passingScore: 60,
  randomOrder: false,
  shuffleQuestions: false,
  shuffleOptions: false
});

// 重命名相关状态
const editingExamId = ref<number | null>(null);
const editingExamName = ref('');
const editNameInput = ref(null);

// 试卷预览相关状态
const paperPreviewModalVisible = ref(false);
const paperLoading = ref(false);
const previewPaperData = ref<any>(null);
const exportLoading = ref(false);

// 数据加载
onMounted(async () => {
  await fetchData();
});

// 计算属性
const getSelectedPaper = computed(() => {
  if (!newExam.paperId) return null;
  return paperList.value.find(paper => paper.id === newExam.paperId);
});

// 方法
async function fetchData() {
  loading.value = true;
  try {
    // 获取考试列表
    const examsRes = await getClassroomExams({
      classroom_id: parseInt(classroomId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (examsRes.code === '0000') {
      console.log('考试列表API响应:', examsRes.data.list);
      console.log('第一个考试数据:', examsRes.data.list[0]);
      examList.value = examsRes.data.list;
    } else {
      message.error(examsRes.message || '获取考试列表失败');
    }
    
    // 获取试卷列表
    if (isTeacherView.value) {
      const papersRes = await getTestPapers({
        classroom_id: parseInt(classroomId.value),
        teacher_id: parseInt(userStore.userInfo?.id) || 1
      });
      
      if (papersRes.code === '0000') {
        paperList.value = papersRes.data.list;
      } else {
        message.error(papersRes.message || '获取试卷列表失败');
      }
    }
  } catch (error) {
    message.error('获取数据失败，请刷新重试');
    console.error('获取数据失败:', error);
  } finally {
    loading.value = false;
  }
}

// 状态相关方法 - 使用从 API 文件导入的函数
function getStatusText(exam: ExamInfo): string {
  return getExamStatusText(exam);
}

function getStatusColor(exam: ExamInfo): string {
  return getExamStatusColor(exam);
}

function getStatusClass(exam: ExamInfo): string {
  const status = getExamStatusText(exam);
  const statusMap: Record<string, string> = {
    '未发布': 'unpublished',
    '未开始': 'upcoming',
    '进行中': 'ongoing',
    '已结束': 'ended'
  };
  return `exam-${statusMap[status] || 'unpublished'}`;
}

function getPassRate(exam: ExamInfo): string {
  const submittedCount = exam.submitted_count || 0;
  if (submittedCount === 0) return '0%';
  const passedCount = exam.graded_count || 0; // 这里可能需要根据实际API调整
  return Math.round((passedCount / submittedCount) * 100) + '%';
}

// 时间格式化方法
function formatDateTime(datetime?: string): string {
  if (!datetime) return '';
  return dayjs(datetime).format('YYYY-MM-DD HH:mm');
}

// 判断考试是否可编辑
function isExamEditable(exam: ExamInfo): boolean {
  const status = getExamStatusText(exam);
  return isTeacherView.value && 
    (!exam.is_published || status === '未开始');
}

// 查看考试结果/阅卷
function viewExamResults(exam: ExamInfo) {
  // 跳转到阅卷列表页面
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${exam.id}/marking`);
}

// 查看考试结果
function viewResults(exam: ExamInfo) {
  // 跳转到考试详情页面
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${exam.id}/results`);
}

// 学生开始考试
function startExam(exam: ExamInfo) {
  message.info(`开始参加考试: ${exam.exam_name}`);
  // TODO: 跳转到考试页面
  // router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${exam.id}/take`);
}

// 创建考试相关方法
function showCreateExamModal() {
  createExamOptionModalVisible.value = true;
}

// 新增选择弹窗状态
const createExamOptionModalVisible = ref(false);

function handleSelectFromBank() {
  createExamOptionModalVisible.value = false;
  createExamModalVisible.value = true;
  newExam.name = '';
  newExam.paperId = null;
  newExam.paperName = '';
  newExam.paperTotalScore = 0;
}

function handleCreateNewPaper() {
  createExamOptionModalVisible.value = false;
  // 跳转到试卷库并触发新建
  router.push({
    path: '/exam/paper-bank',
    query: { action: 'create' }
  });
}

function cancelCreateExam() {
  createExamModalVisible.value = false;
}

function handlePaperChange(value: number) {
  const paper = paperList.value.find(paper => paper.id === value);
  if (paper) {
    newExam.paperName = paper.paper_name;
    newExam.paperTotalScore = paper.total_score;
  }
}

async function handleCreateExam() {
  if (!newExam.name || !newExam.paperId) {
    message.error('请填写考试名称并选择试卷');
    return;
  }

  createExamLoading.value = true;
  try {
    const createData: ExamCreateRequest = {
      title: newExam.name,
      test_paper_id: newExam.paperId
    };
    
    const result = await createExam({
      classroom_id: parseInt(classroomId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      data: createData
    });

    if (result.code === '0000') {
      message.success('考试创建成功');
      createExamModalVisible.value = false;
      // 重新加载考试列表
      await fetchData();
    } else {
      message.error(result.message || '创建考试失败');
    }
  } catch (error) {
    message.error('创建考试失败，请重试');
    console.error('创建考试失败:', error);
  } finally {
    createExamLoading.value = false;
  }
}

function startRenaming(exam: ExamInfo) {
  if (!isExamEditable(exam)) return;
  
  editingExamId.value = exam.id;
  editingExamName.value = exam.exam_name;
  
  // 等待DOM更新后聚焦到输入框
  nextTick(() => {
    const input = editNameInput.value as any;
    if (input?.$el) {
      input.focus();
    }
  });
}

function handleExamTitleClick(exam: ExamInfo) {
  const status = getExamStatusText(exam);
  if (isExamEditable(exam)) {
    startRenaming(exam);
  } else if (status === '进行中' || status === '已结束') {
    router.push(`/classroom/${classroomId.value}/course/${courseId.value}/exam/${exam.id}/results`);
  }
}

async function saveExamName(exam: ExamInfo) {
  if (editingExamName.value.trim() === '') {
    editingExamName.value = exam.exam_name;
    editingExamId.value = null;
    return;
  }
  
  if (editingExamName.value === exam.exam_name) {
    editingExamId.value = null;
    return;
  }
  
  try {
    const renameData: ExamRenameRequest = {
      title: editingExamName.value
    };
    
    const result = await renameExam({
      exam_id: exam.id,
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      data: renameData
    });
    
    if (result.code === '0000') {
      message.success('考试重命名成功');
      // 更新本地列表数据
      const index = examList.value.findIndex(e => e.id === exam.id);
      if (index !== -1) {
        examList.value[index].exam_name = editingExamName.value;
      }
    } else {
      message.error(result.message || '重命名失败');
    }
  } catch (error) {
    message.error('重命名失败，请重试');
    console.error('重命名失败:', error);
    editingExamName.value = exam.exam_name;
  } finally {
    editingExamId.value = null;
  }
}

// 删除考试
function showDeleteConfirm(exam: ExamInfo) {
  Modal.confirm({
    title: '确认删除',
    content: '数据删除不可恢复，是否确认删除？',
    okText: '确认',
    okType: 'danger',
    cancelText: '取消',
    onOk: async () => {
      try {
        const result = await deleteExam({
          exam_id: exam.id,
          teacher_id: parseInt(userStore.userInfo?.id) || 1
        });
        
        if (result.code === '0000') {
          message.success('考试删除成功');
          // 从本地列表中移除
          examList.value = examList.value.filter(e => e.id !== exam.id);
        } else {
          message.error(result.message || '删除失败');
        }
      } catch (error) {
        message.error('删除失败，请重试');
        console.error('删除失败:', error);
      }
    }
  });
}

// 发布考试相关方法
function showPublishModal(exam: ExamInfo) {
  selectedExam.value = exam;
  
  // 初始化表单数据
  const now = dayjs();
  const tomorrow = dayjs().add(1, 'day').hour(10).minute(0).second(0);
  const afterTomorrow = dayjs().add(1, 'day').hour(12).minute(0).second(0);
  
  examTimeRange.value = [tomorrow, afterTomorrow];
  
  publishForm.startTime = tomorrow.format('YYYY-MM-DD HH:mm:ss');
  publishForm.endTime = afterTomorrow.format('YYYY-MM-DD HH:mm:ss');
  publishForm.duration = exam.time_limit_minutes || 90;
  publishForm.passingScore = exam.passing_score || Math.round(exam.paper_total_score * 0.6);
  publishForm.shuffleQuestions = false;
  publishForm.shuffleOptions = false;
  
  publishModalVisible.value = true;
}

function cancelPublish() {
  publishModalVisible.value = false;
  selectedExam.value = null;
  examTimeRange.value = null;
}

function disabledDate(current: Dayjs) {
  // 禁用过去的日期
  return current && current < dayjs().startOf('day');
}

function handleTimeRangeChange(dates: [Dayjs, Dayjs]) {
  if (dates && dates.length === 2) {
    publishForm.startTime = dates[0].format('YYYY-MM-DD HH:mm:ss');
    publishForm.endTime = dates[1].format('YYYY-MM-DD HH:mm:ss');
    validateTimeRange();
  }
}

function validateTimeRange() {
  if (!examTimeRange.value || examTimeRange.value.length !== 2) return;
  
  const start = examTimeRange.value[0];
  const end = examTimeRange.value[1];
  
  // 计算时间差（分钟）
  const diffMinutes = end.diff(start, 'minute');
  
  // 检查时间范围是否足够
  if (diffMinutes < publishForm.duration) {
    message.warning(`考试时间范围必须大于等于考试时长(${publishForm.duration}分钟)`);
  }
}

async function handlePublishExam() {
  if (!selectedExam.value) return;
  
  if (!publishForm.startTime || !publishForm.endTime) {
    message.error('请选择考试时间');
    return;
  }
  
  // 验证时间范围
  const start = dayjs(publishForm.startTime);
  const end = dayjs(publishForm.endTime);
  const diffMinutes = end.diff(start, 'minute');
  
  if (diffMinutes < publishForm.duration) {
    message.error(`考试时间范围(${diffMinutes}分钟)必须大于等于考试时长(${publishForm.duration}分钟)`);
    return;
  }
  
  publishLoading.value = true;
  try {
    const publishData: ExamPublishRequest = {
      exam_start_time: publishForm.startTime,
      exam_end_time: publishForm.endTime,
      duration_minutes: publishForm.duration,
      pass_mark: publishForm.passingScore,
      shuffle_questions: publishForm.shuffleQuestions,
      shuffle_options: publishForm.shuffleOptions
    };
    
    const result = await publishExam({
      exam_id: selectedExam.value.id,
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      data: publishData
    });
    
    if (result.code === '0000') {
      message.success('考试发布成功');
      publishModalVisible.value = false;
      selectedExam.value = null;
      // 重新加载考试列表
      await fetchData();
    } else {
      message.error(result.message || '发布考试失败');
    }
  } catch (error) {
    message.error('发布考试失败，请重试');
    console.error('发布考试失败:', error);
  } finally {
    publishLoading.value = false;
  }
}

// 考试设置相关方法
function showExamSettingsModal(exam: ExamInfo) {
  if (!exam.start_time || !exam.end_time) return;
  
  selectedExam.value = exam;
  
  // 初始化表单数据
  const start = dayjs(exam.start_time);
  const end = dayjs(exam.end_time);
  
  settingsTimeRange.value = [start, end];
  
  settingsForm.startTime = exam.start_time;
  settingsForm.endTime = exam.end_time;
  settingsForm.duration = exam.time_limit_minutes || 90;
  settingsForm.passingScore = exam.passing_score;
  settingsForm.shuffleQuestions = exam.shuffle_questions || false;
  settingsForm.shuffleOptions = exam.shuffle_options || false;
  
  settingsModalVisible.value = true;
}

function cancelSettings() {
  settingsModalVisible.value = false;
  selectedExam.value = null;
  settingsTimeRange.value = null;
}

function handleSettingsTimeRangeChange(dates: [Dayjs, Dayjs]) {
  if (dates && dates.length === 2) {
    settingsForm.startTime = dates[0].format('YYYY-MM-DD HH:mm:ss');
    settingsForm.endTime = dates[1].format('YYYY-MM-DD HH:mm:ss');
    validateSettingsTimeRange();
  }
}

function validateSettingsTimeRange() {
  if (!settingsTimeRange.value || settingsTimeRange.value.length !== 2) return;
  
  const start = settingsTimeRange.value[0];
  const end = settingsTimeRange.value[1];
  
  // 计算时间差（分钟）
  const diffMinutes = end.diff(start, 'minute');
  
  // 检查时间范围是否足够
  if (diffMinutes < settingsForm.duration) {
    message.warning(`考试时间范围必须大于等于考试时长(${settingsForm.duration}分钟)`);
  }
}

async function handleUpdateExamSettings() {
  if (!selectedExam.value) return;
  
  if (!settingsForm.startTime || !settingsForm.endTime) {
    message.error('请选择考试时间');
    return;
  }
  
  // 验证时间范围
  const start = dayjs(settingsForm.startTime);
  const end = dayjs(settingsForm.endTime);
  const diffMinutes = end.diff(start, 'minute');
  
  if (diffMinutes < settingsForm.duration) {
    message.error(`考试时间范围(${diffMinutes}分钟)必须大于等于考试时长(${settingsForm.duration}分钟)`);
    return;
  }
  
  updateSettingsLoading.value = true;
  try {
    const updateData: ExamUpdateRequest = {
      exam_start_time: settingsForm.startTime,
      exam_end_time: settingsForm.endTime,
      duration_minutes: settingsForm.duration,
      pass_mark: settingsForm.passingScore,
      shuffle_questions: settingsForm.shuffleQuestions,
      shuffle_options: settingsForm.shuffleOptions
    };
    
    const result = await updateExam({
      exam_id: selectedExam.value.id,
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      data: updateData
    });
    
    if (result.code === '0000') {
      message.success('考试设置更新成功');
      settingsModalVisible.value = false;
      selectedExam.value = null;
      // 重新加载考试列表
      await fetchData();
    } else {
      message.error(result.message || '更新考试设置失败');
    }
  } catch (error) {
    message.error('更新考试设置失败，请重试');
    console.error('更新考试设置失败:', error);
  } finally {
    updateSettingsLoading.value = false;
  }
}

// 试卷预览相关方法
async function previewPaper() {
  if (!newExam.paperId) {
    message.warning('请先选择试卷');
    return;
  }
  
  paperLoading.value = true;
  paperPreviewModalVisible.value = true;
  
  try {
    // 调用获取试卷详情的API
    const response = await getPaperDetail({
      paper_id: newExam.paperId,
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (response.code === '0000') {
      previewPaperData.value = response.data;
    } else {
      message.error(response.message || '获取试卷详情失败');
      paperPreviewModalVisible.value = false;
    }
  } catch (error) {
    message.error('获取试卷详情失败');
    console.error('获取试卷详情失败:', error);
    paperPreviewModalVisible.value = false;
  } finally {
    paperLoading.value = false;
  }
}

async function previewExamPaper(exam: ExamInfo) {
  paperLoading.value = true;
  paperPreviewModalVisible.value = true;
  
  try {
    // 调用获取试卷详情的API
    const response = await getPaperDetail({
      paper_id: exam.test_paper_id,
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (response.code === '0000') {
      previewPaperData.value = response.data;
    } else {
      message.error(response.message || '获取试卷详情失败');
      paperPreviewModalVisible.value = false;
    }
  } catch (error) {
    message.error('获取试卷详情失败');
    console.error('获取试卷详情失败:', error);
    paperPreviewModalVisible.value = false;
  } finally {
    paperLoading.value = false;
  }
}

async function exportPaperToWord() {
  if (!previewPaperData.value) {
    message.warning('没有可导出的试卷');
    return;
  }
  
  exportLoading.value = true;
  
  try {
    // 调用导出试卷的API
    const response = await exportPaper({
      paper_id: previewPaperData.value.id,
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      format: 'docx'
    });
    
    if (response) {
      // 下载文件
      const blob = new Blob([response], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${previewPaperData.value.paper_name}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('试卷导出成功');
    } else {
      message.error('导出试卷失败');
    }
  } catch (error) {
    message.error('导出试卷失败');
    console.error('导出试卷失败:', error);
  } finally {
    exportLoading.value = false;
  }
}

function getQuestionTypeName(type: string): string {
  const typeMap: Record<string, string> = {
    'single_choice': '单选题',
    'multiple_choice': '多选题',
    'true_false': '判断题',
    'fill_blank': '填空题',
    'short_answer': '简答题',
    'essay': '论述题',
    'calculation': '计算题'
  };
  return typeMap[type] || type;
}
</script>

<style scoped>
.course-exam-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #1f1f1f;
}

.exams-container {
  margin-top: 20px;
}

.exam-cards {
  margin-top: 16px;
}

.exam-card {
  height: 100%;
  transition: all 0.3s;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.exam-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.exam-title {
  font-weight: 500;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
}

.exam-title.editable:hover {
  text-decoration: underline;
}

.exam-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: #666;
}

.info-item .anticon {
  margin-right: 8px;
  color: #1890ff;
}

.exam-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}

/* 状态样式 */
.exam-unpublished {
  border-left: 4px solid #d9d9d9;
}

.exam-upcoming {
  border-left: 4px solid #1890ff;
}

.exam-ongoing {
  border-left: 4px solid #52c41a;
}

.exam-ended {
  border-left: 4px solid #722ed1;
}

/* 创建考试模态框样式 */
.paper-info {
  background-color: #f8f8f8;
  padding: 12px;
  border-radius: 4px;
  margin-top: 8px;
}

.paper-info-item {
  margin-bottom: 6px;
}

.paper-info-item .label {
  font-weight: 500;
  margin-right: 8px;
}

.paper-actions {
  margin-top: 12px;
  text-align: center;
}

/* 试卷预览样式 */
.paper-preview-container {
  max-height: 600px;
  overflow-y: auto;
}

.paper-header {
  text-align: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.paper-header h2 {
  font-size: 20px;
  margin-bottom: 8px;
}

.paper-meta {
  color: #666;
  font-size: 14px;
}

.paper-meta span {
  margin: 0 8px;
}

.question-section {
  margin-bottom: 32px;
}

.question-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
  color: #1890ff;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.question-header {
  margin-bottom: 12px;
}

.question-number {
  font-weight: bold;
  margin-right: 8px;
}

.question-type {
  color: #1890ff;
  margin-right: 8px;
}

.question-score {
  color: #ff7875;
}

.question-content {
  margin-bottom: 16px;
  line-height: 1.6;
}

.question-options {
  margin-bottom: 16px;
}

.option-item {
  margin-bottom: 8px;
  padding-left: 24px;
}

.option-label {
  font-weight: 500;
  margin-right: 8px;
}

.question-answer {
  border-top: 1px dashed #d9d9d9;
  padding-top: 12px;
  margin-top: 12px;
}

.answer-label {
  font-weight: 500;
  color: #52c41a;
  margin-bottom: 8px;
}

.question-explanation {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #d9d9d9;
}

.explanation-label {
  font-weight: 500;
  color: #1890ff;
  margin-bottom: 8px;
}
</style> 