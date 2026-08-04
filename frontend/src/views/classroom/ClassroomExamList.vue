<template>
  <div class="classroom-exam-list">
    <PageHeaderBar title="课程考核">
      <template #actions>
        <a-button
          v-if="isTeacher"
          type="primary"
          @click="showCreateExamModal"
        >
          <template #icon><plus-outlined /></template>
          创建考试
        </a-button>
      </template>
    </PageHeaderBar>

    <a-spin :spinning="loading">
      <!-- 空状态 -->
      <EmptyStateBlock
        v-if="!loading && examList.length === 0"
        description="暂无考试"
      />

      <!-- 考试列表 -->
      <div v-else class="exam-cards">
        <a-row :gutter="[16, 16]">
          <a-col :xs="24" :sm="12" :md="8" v-for="exam in examList" :key="exam.id">
            <a-card class="exam-card" :bordered="false" hoverable>
              <template #title>
                <div class="exam-title-row">
                  <!-- 行内编辑模式 -->
                  <div v-if="editingExamId === exam.id" class="inline-edit">
                    <a-input
                      v-model:value="editingExamTitle"
                      size="small"
                      :maxlength="50"
                      @pressEnter="confirmRename"
                      ref="renameInputRef"
                      class="rename-input"
                    />
                    <a-button type="text" size="small" class="edit-btn confirm-btn" @click="confirmRename">
                      <CheckOutlined />
                    </a-button>
                    <a-button type="text" size="small" class="edit-btn cancel-btn" @click="cancelRename">
                      <CloseOutlined />
                    </a-button>
                  </div>
                  <!-- 正常显示模式 -->
                  <span v-else class="exam-title">{{ exam.title }}</span>
                  <div class="title-actions">
                    <a-tag :color="getStatusColor(exam.status)">
                      {{ getStatusText(exam.status) }}
                    </a-tag>
                    <!-- 更多操作按钮 -->
                    <a-dropdown v-if="isTeacher" :trigger="['click']" placement="bottomRight">
                      <a-button type="text" class="more-btn" @click.stop>
                        <EllipsisOutlined />
                      </a-button>
                      <template #overlay>
                        <a-menu @click="handleExamMenuClick($event, exam)">
                          <a-menu-item
                            key="setting"
                            :disabled="!canEditExam(exam)"
                          >
                            <a-tooltip
                              v-if="!canEditExam(exam)"
                              :title="getDisabledReason(exam)"
                              placement="left"
                            >
                              <span><SettingOutlined /> 设置</span>
                            </a-tooltip>
                            <span v-else><SettingOutlined /> 设置</span>
                          </a-menu-item>
                          <a-menu-item
                            key="rename"
                            :disabled="!canEditExam(exam)"
                          >
                            <a-tooltip
                              v-if="!canEditExam(exam)"
                              :title="getDisabledReason(exam)"
                              placement="left"
                            >
                              <span><EditOutlined /> 重命名</span>
                            </a-tooltip>
                            <span v-else><EditOutlined /> 重命名</span>
                          </a-menu-item>
                          <a-menu-divider />
                          <a-menu-item
                            key="delete"
                            :disabled="!canEditExam(exam)"
                            class="delete-menu-item"
                          >
                            <a-tooltip
                              v-if="!canEditExam(exam)"
                              :title="getDisabledReason(exam)"
                              placement="left"
                            >
                              <span><DeleteOutlined /> 删除</span>
                            </a-tooltip>
                            <span v-else><DeleteOutlined /> 删除</span>
                          </a-menu-item>
                        </a-menu>
                      </template>
                    </a-dropdown>
                  </div>
                </div>
              </template>

              <div class="exam-info">
                <div class="info-row">
                  <calendar-outlined />
                  <span>开始：{{ formatDateTime(exam.exam_start_time) }}</span>
                </div>
                <div class="info-row">
                  <calendar-outlined />
                  <span>结束：{{ formatDateTime(exam.exam_end_time) }}</span>
                </div>
                <div class="info-row">
                  <clock-circle-outlined />
                  <span>时长：{{ exam.duration_minutes }} 分钟</span>
                </div>
                <div class="info-row" v-if="exam.pass_mark">
                  <check-circle-outlined />
                  <span>及格分：{{ exam.pass_mark }} 分</span>
                </div>
              </div>

              <template #actions>
                <!-- 教师操作 -->
                <template v-if="isTeacher">
                  <a-button
                    v-if="exam.status === 'UNPUBLISHED'"
                    type="primary"
                    @click="showPublishModal(exam)"
                  >
                    发布
                  </a-button>
                  <a-button
                    type="link"
                    @click="handleViewResults(exam)"
                    :disabled="exam.status === 'UNPUBLISHED'"
                  >
                    查看结果
                  </a-button>
                  <a-button
                    type="link"
                    @click="handleMarkExam(exam)"
                    :disabled="exam.status !== 'ONGOING' && exam.status !== 'COMPLETED'"
                  >
                    阅卷
                  </a-button>
                </template>

                <!-- 学生操作 -->
                <template v-else>
                  <a-button 
                    v-if="exam.status === 'ONGOING' && !exam.student_submitted"
                    type="primary" 
                    @click="handleStartExam(exam)"
                  >
                    开始考试
                  </a-button>
                  <a-button 
                    v-else-if="exam.student_submitted"
                    type="link"
                    @click="handleViewMyResult(exam)"
                  >
                    查看成绩
                  </a-button>
                  <span v-else-if="exam.status === 'SCHEDULED'" class="status-hint">
                    尚未开始
                  </span>
                  <span v-else-if="exam.status === 'COMPLETED'" class="status-hint">
                    已结束
                  </span>
                </template>
              </template>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </a-spin>

    <!-- 创建考试选项弹窗 -->
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
            <template #icon><edit-outlined /></template>
            新建试卷
          </a-button>
        </a-space>
      </div>
    </a-modal>

    <!-- 从试卷库选择弹窗 -->
    <a-modal
      v-model:open="selectPaperModalVisible"
      title="选择试卷创建考试"
      width="500px"
      @ok="confirmSelectPaper"
      :confirm-loading="createExamLoading"
      okText="创建考试"
    >
      <a-spin :spinning="paperLoading">
        <a-form :model="examForm" layout="vertical">
          <a-form-item label="考试名称" required>
            <a-input v-model:value="examForm.name" placeholder="请输入考试名称" />
          </a-form-item>
          <a-form-item label="选择试卷" required>
            <a-select
              v-model:value="examForm.paperId"
              placeholder="请选择试卷"
              show-search
              option-filter-prop="label"
              :options="paperOptions"
            />
          </a-form-item>
          <a-alert 
            v-if="paperOptions.length === 0 && !paperLoading"
            message="暂无可用试卷"
            description="请先在试卷库中创建试卷"
            type="info"
            show-icon
          />
        </a-form>
      </a-spin>
    </a-modal>

    <!-- 发布/编辑考试设置弹窗 -->
    <a-modal
      v-model:open="publishModalVisible"
      :title="isEditMode ? '考试设置' : '发布考试'"
      width="520px"
      @ok="handleModalOk"
      :confirm-loading="publishLoading"
      :okText="isEditMode ? '保存修改' : '确定'"
      cancelText="取消"
    >
      <a-form :model="publishForm" layout="vertical">
        <a-form-item label="考试时间" required>
          <a-range-picker
            v-model:value="publishForm.examTimeRange"
            show-time
            format="YYYY-MM-DD HH:mm"
            :placeholder="['开始时间', '结束时间']"
            style="width: 100%"
            @change="validateTimeRange"
          />
          <div v-if="timeRangeError" class="error-text">{{ timeRangeError }}</div>
        </a-form-item>
        <a-form-item label="考试时长（分钟）" required>
          <a-input-number
            v-model:value="publishForm.durationMinutes"
            :min="1"
            :max="480"
            style="width: 100%"
            @change="validateTimeRange"
          />
          <div class="form-hint">考试时长不能超过考试时间窗口</div>
        </a-form-item>
        <a-form-item label="及格分数" required>
          <a-input-number
            v-model:value="publishForm.passMark"
            :min="0"
            :max="currentExamTotalScore"
            style="width: 100%"
          />
          <div class="form-hint">
            试卷总分：{{ currentExamTotalScore }} 分，默认为总分的60%
          </div>
        </a-form-item>
        <a-form-item label="防作弊设置">
          <a-checkbox v-model:checked="publishForm.shuffleQuestions">
            题目乱序（打乱题目出现顺序）
          </a-checkbox>
          <br />
          <a-checkbox v-model:checked="publishForm.shuffleOptions" style="margin-top: 8px">
            选项乱序（打乱选择题选项顺序）
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="提示"
      width="400px"
      @ok="confirmDelete"
      :confirm-loading="deleteLoading"
      okText="确定"
      cancelText="取消"
      :okButtonProps="{ danger: true }"
    >
      <div class="delete-confirm-content">
        <ExclamationCircleOutlined class="warning-icon" />
        <span>数据删除不可恢复，是否确认删除？</span>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  CalendarOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
  BookOutlined,
  EditOutlined,
  EllipsisOutlined,
  SettingOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  CheckOutlined,
  CloseOutlined
} from '@ant-design/icons-vue';
import { getClassroomExams, getPaperList, createExamFromPaper, publishExam, updateExam, renameExam, deleteExam } from '@/api/exam';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import request from '@/utils/request';
import { useUserStore } from '@/stores/user';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

const props = defineProps<{
  classroomId: number | string;
}>();

const router = useRouter();
const userStore = useUserStore();

const loading = ref(false);
const examList = ref<any[]>([]);

const isTeacher = computed(() => userStore.userRole === 'teacher' || userStore.userRole === 'admin');

// 创建考试相关状态
const createExamOptionModalVisible = ref(false);
const selectPaperModalVisible = ref(false);
const paperLoading = ref(false);
const createExamLoading = ref(false);
const paperOptions = ref<{ value: number; label: string }[]>([]);

const examForm = ref({
  name: '',
  paperId: null as number | null
});

// 发布/编辑考试相关状态
const publishModalVisible = ref(false);
const publishLoading = ref(false);
const currentExam = ref<any>(null);
const currentExamTotalScore = ref(100);
const timeRangeError = ref('');
const isEditMode = ref(false); // 是否为编辑模式

const publishForm = ref({
  examTimeRange: null as [Dayjs, Dayjs] | null,
  durationMinutes: 60,
  passMark: 60,
  shuffleQuestions: false,
  shuffleOptions: false
});

// 重命名相关状态
const editingExamId = ref<number | null>(null);
const editingExamTitle = ref('');
const renameInputRef = ref<any>(null);

// 删除相关状态
const deleteModalVisible = ref(false);
const deleteLoading = ref(false);
const examToDelete = ref<any>(null);

// 显示创建考试选项弹窗
const showCreateExamModal = () => {
  createExamOptionModalVisible.value = true;
};

// 从试卷库选择
const handleSelectFromBank = async () => {
  createExamOptionModalVisible.value = false;
  selectPaperModalVisible.value = true;
  
  // 加载试卷列表
  paperLoading.value = true;
  try {
    const response = await getPaperList({
      teacher_id: Number(userStore.userId),
      page: 1,
      page_size: 100
    });
    if (response.code === '0000' && response.data) {
      const list = response.data.list || [];
      paperOptions.value = list.map((paper: any) => ({
        value: paper.id,
        label: `${paper.title || paper.paper_name} (${paper.question_count}题, ${paper.total_score}分)`
      }));
    }
  } catch (error) {
    console.error('加载试卷列表失败:', error);
    message.error('加载试卷列表失败');
  } finally {
    paperLoading.value = false;
  }
};

// 新建试卷
const handleCreateNewPaper = () => {
  createExamOptionModalVisible.value = false;
  router.push('/exam/edit-paper');
};

// 确认选择试卷并创建考试
const confirmSelectPaper = async () => {
  if (!examForm.value.name) {
    message.warning('请输入考试名称');
    return;
  }
  if (!examForm.value.paperId) {
    message.warning('请选择试卷');
    return;
  }
  
  createExamLoading.value = true;
  try {
    const response = await createExamFromPaper(
      examForm.value.paperId,
      {
        exam_title: examForm.value.name,
        classroom_id: Number(props.classroomId)
      },
      Number(userStore.userId)
    );
    
    if (response.code === '0000') {
      message.success('创建考试成功');
      selectPaperModalVisible.value = false;
      // 重置表单
      examForm.value = {
        name: '',
        paperId: null
      };
      // 刷新考试列表
      fetchExams();
    } else {
      message.error(response.message || '创建考试失败');
    }
  } catch (error) {
    console.error('创建考试失败:', error);
    message.error('创建考试失败');
  } finally {
    createExamLoading.value = false;
  }
};

// 判断是否可以编辑考试设置
const canEditExam = (exam: any): boolean => {
  // 只有未发布和已安排（未开始）的考试可以编辑
  return exam.status === 'UNPUBLISHED' || exam.status === 'SCHEDULED';
};

// 获取禁用原因
const getDisabledReason = (exam: any): string => {
  if (exam.status === 'ONGOING') {
    return '考试进行中，无法修改设置';
  }
  if (exam.status === 'COMPLETED' || exam.status === 'GRADING') {
    return '考试已结束，无法修改设置';
  }
  return '';
};

// 处理考试菜单点击
const handleExamMenuClick = ({ key }: { key: string }, exam: any) => {
  if (key === 'setting') {
    if (canEditExam(exam)) {
      showEditSettingsModal(exam);
    }
  } else if (key === 'rename') {
    if (canEditExam(exam)) {
      startRename(exam);
    }
  } else if (key === 'delete') {
    if (canEditExam(exam)) {
      showDeleteConfirm(exam);
    }
  }
};

// 开始重命名
const startRename = (exam: any) => {
  editingExamId.value = exam.id;
  editingExamTitle.value = exam.title || '';
  // 等待DOM更新后聚焦输入框
  setTimeout(() => {
    if (renameInputRef.value) {
      renameInputRef.value.focus();
      renameInputRef.value.select();
    }
  }, 100);
};

// 确认重命名
const confirmRename = async () => {
  if (!editingExamTitle.value.trim()) {
    message.warning('考试名称不能为空');
    return;
  }

  try {
    const response = await renameExam({
      exam_id: editingExamId.value!,
      teacher_id: Number(userStore.userId),
      data: { title: editingExamTitle.value.trim() }
    });

    if (response.code === '0000') {
      message.success('重命名成功');
      editingExamId.value = null;
      editingExamTitle.value = '';
      fetchExams(); // 刷新列表
    } else {
      message.error(response.message || '重命名失败');
    }
  } catch (error) {
    console.error('重命名失败:', error);
    message.error('重命名失败');
  }
};

// 取消重命名
const cancelRename = () => {
  editingExamId.value = null;
  editingExamTitle.value = '';
};

// 显示删除确认弹窗
const showDeleteConfirm = (exam: any) => {
  examToDelete.value = exam;
  deleteModalVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!examToDelete.value) return;

  deleteLoading.value = true;
  try {
    const response = await deleteExam({
      exam_id: examToDelete.value.id,
      teacher_id: Number(userStore.userId)
    });

    if (response.code === '0000') {
      message.success('删除成功');
      deleteModalVisible.value = false;
      examToDelete.value = null;
      fetchExams(); // 刷新列表
    } else {
      message.error(response.message || '删除失败');
    }
  } catch (error) {
    console.error('删除失败:', error);
    message.error('删除失败');
  } finally {
    deleteLoading.value = false;
  }
};

// 显示发布考试弹窗
const showPublishModal = (exam: any) => {
  currentExam.value = exam;
  isEditMode.value = false; // 发布模式
  // 获取试卷总分，默认100
  const totalScore = exam.test_paper_total_score || exam.paper_total_score || 100;
  currentExamTotalScore.value = totalScore;

  // 设置默认值
  const now = dayjs();
  publishForm.value = {
    examTimeRange: [now.add(1, 'hour'), now.add(3, 'hour')],
    durationMinutes: exam.duration_minutes || 60,
    passMark: Math.round(totalScore * 0.6), // 默认60%
    shuffleQuestions: false,
    shuffleOptions: false
  };
  timeRangeError.value = '';
  publishModalVisible.value = true;
};

// 显示编辑设置弹窗（回显现有数据）
const showEditSettingsModal = (exam: any) => {
  currentExam.value = exam;
  isEditMode.value = true; // 编辑模式
  // 获取试卷总分，默认100
  const totalScore = exam.test_paper_total_score || exam.paper_total_score || 100;
  currentExamTotalScore.value = totalScore;

  // 回显现有数据
  const startTime = exam.exam_start_time ? dayjs(exam.exam_start_time) : null;
  const endTime = exam.exam_end_time ? dayjs(exam.exam_end_time) : null;

  publishForm.value = {
    examTimeRange: startTime && endTime ? [startTime, endTime] : null,
    durationMinutes: exam.duration_minutes || 60,
    passMark: exam.pass_mark || Math.round(totalScore * 0.6),
    shuffleQuestions: exam.shuffle_questions || false,
    shuffleOptions: exam.shuffle_options || false
  };
  timeRangeError.value = '';
  publishModalVisible.value = true;
};

// 弹窗确认按钮处理
const handleModalOk = () => {
  if (isEditMode.value) {
    confirmEditSettings();
  } else {
    confirmPublish();
  }
};

// 验证时间范围
const validateTimeRange = () => {
  if (!publishForm.value.examTimeRange || publishForm.value.examTimeRange.length !== 2) {
    timeRangeError.value = '';
    return true;
  }

  const [start, end] = publishForm.value.examTimeRange;
  const windowMinutes = end.diff(start, 'minute');

  if (publishForm.value.durationMinutes > windowMinutes) {
    timeRangeError.value = `考试窗口期（${windowMinutes}分钟）不能小于考试时长（${publishForm.value.durationMinutes}分钟）`;
    return false;
  }

  timeRangeError.value = '';
  return true;
};

// 确认发布考试
const confirmPublish = async () => {
  // 表单验证
  if (!publishForm.value.examTimeRange || publishForm.value.examTimeRange.length !== 2) {
    message.warning('请选择考试时间');
    return;
  }

  if (!publishForm.value.durationMinutes || publishForm.value.durationMinutes < 1) {
    message.warning('请设置有效的考试时长');
    return;
  }

  if (!validateTimeRange()) {
    message.warning(timeRangeError.value);
    return;
  }

  const [start, end] = publishForm.value.examTimeRange;

  publishLoading.value = true;
  try {
    const response = await publishExam({
      exam_id: currentExam.value.id,
      teacher_id: Number(userStore.userId),
      data: {
        exam_start_time: start.format('YYYY-MM-DD HH:mm:ss'),
        exam_end_time: end.format('YYYY-MM-DD HH:mm:ss'),
        duration_minutes: publishForm.value.durationMinutes,
        pass_mark: publishForm.value.passMark,
        shuffle_questions: publishForm.value.shuffleQuestions,
        shuffle_options: publishForm.value.shuffleOptions
      }
    });

    if (response.code === '0000') {
      message.success('考试发布成功');
      publishModalVisible.value = false;
      // 刷新考试列表
      fetchExams();
    } else {
      message.error(response.message || '发布考试失败');
    }
  } catch (error) {
    console.error('发布考试失败:', error);
    message.error('发布考试失败');
  } finally {
    publishLoading.value = false;
  }
};

// 确认编辑考试设置
const confirmEditSettings = async () => {
  // 表单验证
  if (!publishForm.value.examTimeRange || publishForm.value.examTimeRange.length !== 2) {
    message.warning('请选择考试时间');
    return;
  }

  if (!publishForm.value.durationMinutes || publishForm.value.durationMinutes < 1) {
    message.warning('请设置有效的考试时长');
    return;
  }

  if (!validateTimeRange()) {
    message.warning(timeRangeError.value);
    return;
  }

  const [start, end] = publishForm.value.examTimeRange;

  // 如果考试已发布但未开始，检查修改的开始时间是否在当前时间之后
  if (currentExam.value.status === 'SCHEDULED') {
    const now = dayjs();
    if (start.isBefore(now)) {
      message.warning('考试开始时间不能早于当前时间');
      return;
    }
  }

  publishLoading.value = true;
  try {
    const response = await updateExam({
      exam_id: currentExam.value.id,
      teacher_id: Number(userStore.userId),
      data: {
        exam_start_time: start.format('YYYY-MM-DD HH:mm:ss'),
        exam_end_time: end.format('YYYY-MM-DD HH:mm:ss'),
        duration_minutes: publishForm.value.durationMinutes,
        pass_mark: publishForm.value.passMark,
        shuffle_questions: publishForm.value.shuffleQuestions,
        shuffle_options: publishForm.value.shuffleOptions
      }
    });

    if (response.code === '0000') {
      message.success('考试设置保存成功');
      publishModalVisible.value = false;
      // 刷新考试列表
      fetchExams();
    } else {
      message.error(response.message || '保存设置失败');
    }
  } catch (error) {
    console.error('保存设置失败:', error);
    message.error('保存设置失败');
  } finally {
    publishLoading.value = false;
  }
};

// 获取考试列表
const fetchExams = async () => {
  loading.value = true;
  try {
    const userId = userStore.userId;
    let response;
    
    if (isTeacher.value) {
      // 教师使用教师API
      response = await getClassroomExams({
        classroom_id: props.classroomId,
        teacher_id: userId,
        page: 1,
        page_size: 50
      });
    } else {
      // 学生使用学生API
      response = await request.get(`/api/v1/classrooms/${props.classroomId}/exams/student`, {
        params: {
          student_id: userId,
          page: 1,
          page_size: 50
        }
      });
    }
    
    if (response.code === '0000' && response.data) {
      examList.value = response.data.list || [];
    }
  } catch (error) {
    console.error('获取考试列表失败:', error);
    message.error('获取考试列表失败');
  } finally {
    loading.value = false;
  }
};

// 状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'UNPUBLISHED': 'default',
    'SCHEDULED': 'blue',
    'ONGOING': 'green',
    'GRADING': 'orange',
    'COMPLETED': 'gray'
  };
  return colors[status] || 'default';
};

// 状态文本
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'UNPUBLISHED': '未发布',
    'SCHEDULED': '已安排',
    'ONGOING': '进行中',
    'GRADING': '阅卷中',
    'COMPLETED': '已完成'
  };
  return texts[status] || status;
};

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 查看结果
const handleViewResults = (exam: any) => {
  router.push(`/classroom/${props.classroomId}/exam/${exam.id}/results`);
};

// 阅卷
const handleMarkExam = (exam: any) => {
  router.push(`/classroom/${props.classroomId}/exam/${exam.id}/marking`);
};

// 学生开始考试
const handleStartExam = (exam: any) => {
  router.push(`/classroom/${props.classroomId}/exam/${exam.id}/take`);
};

// 学生查看成绩
const handleViewMyResult = (exam: any) => {
  router.push(`/classroom/${props.classroomId}/exam/${exam.id}/my-result`);
};

onMounted(() => {
  fetchExams();
});
</script>

<style scoped lang="less">
.classroom-exam-list {
  /* nested in classroom detail or PageShell; no extra outer padding */
}

.exam-cards {
  margin-top: var(--hx-space-4);
}

.exam-card {
  height: 100%;
  
  :deep(.ant-card-head) {
    padding: var(--hx-space-3) var(--hx-space-4);
    min-height: auto;
  }
  
  :deep(.ant-card-body) {
    padding: var(--hx-space-4);
  }
  
  :deep(.ant-card-actions) {
    background: var(--hx-color-bg-layout);
  }
}

.exam-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-actions {
  display: flex;
  align-items: center;
  gap: var(--hx-space-2);
}

.more-btn {
  padding: 0 4px;
  font-size: 16px;
  color: var(--hx-color-text-secondary);

  &:hover {
    color: var(--hx-color-primary);
  }
}

.exam-title {
  font-weight: 500;
  font-size: 15px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.exam-info {
  .info-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    color: #666;
    font-size: 13px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.status-hint {
  color: #999;
  font-size: 13px;
}

.create-exam-options {
  padding: 16px 0;
}

.error-text {
  color: #ff4d4f;
  font-size: 12px;
  margin-top: 4px;
}

.form-hint {
  color: #999;
  font-size: 12px;
  margin-top: 4px;
}

// 行内编辑样式
.inline-edit {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;

  .rename-input {
    flex: 1;
    max-width: 160px;
  }

  .edit-btn {
    padding: 2px 6px;
    font-size: 14px;

    &.confirm-btn {
      color: #52c41a;
      &:hover {
        color: #73d13d;
      }
    }

    &.cancel-btn {
      color: #999;
      &:hover {
        color: #ff4d4f;
      }
    }
  }
}

// 删除菜单项样式
.delete-menu-item {
  color: #ff4d4f !important;
}

// 删除确认弹窗内容
.delete-confirm-content {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;

  .warning-icon {
    font-size: 22px;
    color: #faad14;
  }
}
</style>

