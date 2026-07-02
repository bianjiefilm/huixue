<template>
  <div class="exam-marking-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <a-button @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回
        </a-button>
        <h2>{{ examInfo?.title || '考试阅卷' }}</h2>
        <a-tag :color="getStatusColor(examInfo?.status)">
          {{ getStatusText(examInfo?.status) }}
        </a-tag>
      </div>
      <div class="header-right">
        <a-statistic title="总提交数" :value="studentList.length" />
        <a-divider type="vertical" />
        <a-statistic title="已批阅" :value="gradedCount" />
        <a-divider type="vertical" />
        <a-statistic title="待批阅" :value="pendingCount" />
      </div>
    </div>

    <!-- 加载中 -->
    <a-spin :spinning="loading">
      <!-- 空状态 -->
      <a-empty 
        v-if="!loading && studentList.length === 0"
        description="暂无学生提交"
      />

      <!-- 学生列表 -->
      <div v-else class="student-list">
        <a-table 
          :columns="columns" 
          :data-source="studentList"
          :pagination="{ pageSize: 20 }"
          row-key="attempt_id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'student'">
              <div class="student-info">
                <a-avatar :style="{ backgroundColor: getAvatarColor(record.student_name) }">
                  {{ record.student_name?.charAt(0) || '?' }}
                </a-avatar>
                <div class="student-detail">
                  <span class="student-name">{{ record.student_name }}</span>
                  <span class="student-username">{{ record.student_username }}</span>
                </div>
              </div>
            </template>

            <template v-else-if="column.key === 'submit_time'">
              {{ formatDateTime(record.submit_time) }}
            </template>

            <template v-else-if="column.key === 'score'">
              <span v-if="record.score !== null" class="score" :class="getScoreClass(record.score)">
                {{ record.score }} 分
              </span>
              <span v-else class="pending">待批阅</span>
            </template>

            <template v-else-if="column.key === 'status'">
              <a-tag v-if="record.is_graded" color="green">
                <check-circle-outlined /> 已批阅
              </a-tag>
              <a-tag v-else color="orange">
                <clock-circle-outlined /> 待批阅
              </a-tag>
            </template>

            <template v-else-if="column.key === 'action'">
              <a-space>
                <!-- PRD: 仅已批阅学生显示"查看试卷"按钮，跳转到试卷详情页 -->
                <a-button
                  v-if="record.is_graded"
                  type="link"
                  @click="goToPaperView(record)"
                >
                  <template #icon><eye-outlined /></template>
                  查看试卷
                </a-button>
                <!-- 待批阅学生显示"批阅"按钮 -->
                <a-button
                  v-if="!record.is_graded"
                  type="link"
                  @click="gradeStudent(record)"
                >
                  <template #icon><edit-outlined /></template>
                  批阅
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </div>
    </a-spin>

    <!-- 查看答卷弹窗 -->
    <a-modal
      v-model:open="paperModalVisible"
      :title="`${currentStudent?.student_name} 的答卷`"
      width="800px"
    >
      <div v-if="currentPaper" class="paper-view">
        <div class="paper-summary">
          <a-descriptions :column="3" bordered size="small">
            <a-descriptions-item label="总分">
              <span class="score-highlight">{{ currentStudent?.score ?? '待评' }} 分</span>
            </a-descriptions-item>
            <a-descriptions-item label="提交时间">
              {{ formatDateTime(currentStudent?.submit_time) }}
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="currentStudent?.is_graded ? 'green' : 'orange'">
                {{ currentStudent?.is_graded ? '已批阅' : '待批阅' }}
              </a-tag>
            </a-descriptions-item>
          </a-descriptions>
        </div>

        <a-divider>答题详情</a-divider>

        <div class="questions-list">
          <div 
            v-for="(question, index) in currentPaper.questions" 
            :key="question.id"
            class="question-item"
          >
            <div class="question-header">
              <span class="question-number">第 {{ index + 1 }} 题</span>
              <a-tag>{{ getQuestionTypeText(question.question_type) }}</a-tag>
              <span class="question-score">
                得分：
                <span :class="question.is_correct ? 'correct' : 'incorrect'">
                  {{ question.score_awarded ?? 0 }} / {{ question.max_score }} 分
                </span>
              </span>
              <a-tag v-if="question.is_correct" color="success">正确</a-tag>
              <a-tag v-else-if="question.is_correct === false" color="error">错误</a-tag>
            </div>
            
            <div class="question-content">
              {{ question.content }}
            </div>

            <div class="question-options" v-if="question.options?.length">
              <div 
                v-for="opt in question.options" 
                :key="opt.key"
                :class="['option', { 
                  'correct-option': isCorrectOption(question, opt.key),
                  'selected-option': isSelectedOption(question.student_answer, opt.key),
                  'wrong-selected': isSelectedOption(question.student_answer, opt.key) && !isCorrectOption(question, opt.key)
                }]"
              >
                {{ opt.key }}. {{ opt.content }}
                <check-outlined v-if="isCorrectOption(question, opt.key)" class="correct-icon" />
                <close-outlined v-if="isSelectedOption(question.student_answer, opt.key) && !isCorrectOption(question, opt.key)" class="wrong-icon" />
              </div>
            </div>

            <div class="answer-compare" v-if="question.question_type === 'TRUE_FALSE'">
              <div class="answer-row">
                <span class="label">学生答案：</span>
                <span :class="question.is_correct ? 'correct' : 'incorrect'">
                  {{ question.student_answer === 'true' || question.student_answer === true ? '正确' : '错误' }}
                </span>
              </div>
              <div class="answer-row">
                <span class="label">正确答案：</span>
                <span class="correct">
                  {{ getCorrectAnswerText(question) }}
                </span>
              </div>
            </div>

            <!-- 简答题显示学生答案和参考答案 -->
            <div class="essay-section" v-if="question.question_type === 'SHORT_ANSWER'">
              <div class="essay-answer">
                <div class="answer-label">学生答案：</div>
                <div class="answer-content student-answer">
                  {{ question.student_answer || '未作答' }}
                </div>
              </div>
              <div class="essay-answer">
                <div class="answer-label">参考答案：</div>
                <div class="answer-content reference-answer">
                  {{ question.correct_answer || '无参考答案' }}
                </div>
              </div>

              <!-- 评分区域（仅未批阅时显示输入框） -->
              <div class="grading-section" v-if="isGradingMode && !currentStudent?.is_graded">
                <a-divider dashed />
                <div class="grading-input">
                  <div class="score-input-row">
                    <span class="input-label">评分：</span>
                    <a-input-number
                      v-model:value="questionScores[question.id]"
                      :min="0"
                      :max="question.max_score"
                      :precision="0"
                      style="width: 80px"
                    />
                    <span class="score-max">/ {{ question.max_score }} 分</span>
                  </div>
                  <div class="comment-input-row">
                    <span class="input-label">评语：</span>
                    <a-textarea
                      v-model:value="questionComments[question.id]"
                      placeholder="请输入评语（可选）"
                      :rows="2"
                      style="flex: 1"
                    />
                  </div>
                </div>
              </div>

              <!-- 已批阅时显示只读评分信息 -->
              <div class="graded-info" v-if="currentStudent?.is_graded && question.score_awarded !== null">
                <a-divider dashed />
                <div class="graded-score">
                  <span class="label">教师评分：</span>
                  <span class="score">{{ question.score_awarded }} / {{ question.max_score }} 分</span>
                </div>
                <div class="teacher-comment" v-if="question.teacher_comment">
                  <span class="label">教师评语：</span>
                  <span class="comment">{{ question.teacher_comment }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <a-empty v-else description="加载中..." />

      <!-- 弹窗底部按钮 -->
      <template #footer>
        <div class="modal-footer">
          <a-button @click="paperModalVisible = false">关闭</a-button>
          <a-button
            v-if="hasSubjectiveQuestions && !currentStudent?.is_graded"
            type="primary"
            :loading="submitting"
            @click="submitGrading"
          >
            <template #icon><check-outlined /></template>
            提交评分
          </a-button>
        </div>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  EditOutlined,
  CheckOutlined,
  CloseOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import request from '@/utils/request';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const classroomId = computed(() => route.params.classroomId as string);
const examId = computed(() => route.params.examId as string);

const loading = ref(true);
const examInfo = ref<any>(null);
const studentList = ref<any[]>([]);
const paperModalVisible = ref(false);
const currentStudent = ref<any>(null);
const currentPaper = ref<any>(null);

// 评分相关状态
const isGradingMode = ref(true); // 始终显示评分区域
const submitting = ref(false);
const questionScores = ref<Record<string, number>>({});
const questionComments = ref<Record<string, string>>({});

// 是否有主观题
const hasSubjectiveQuestions = computed(() => {
  if (!currentPaper.value?.questions) return false;
  return currentPaper.value.questions.some((q: any) => q.question_type === 'SHORT_ANSWER');
});

// 表格列定义
const columns = [
  { title: '学生', key: 'student', dataIndex: 'student_name' },
  { title: '提交时间', key: 'submit_time', dataIndex: 'submit_time' },
  { title: '得分', key: 'score', dataIndex: 'score' },
  { title: '状态', key: 'status', dataIndex: 'is_graded' },
  { title: '操作', key: 'action' }
];

// 已批阅数量
const gradedCount = computed(() => studentList.value.filter(s => s.is_graded).length);
// 待批阅数量
const pendingCount = computed(() => studentList.value.filter(s => !s.is_graded).length);

// 获取当前用户ID（带fallback）
const getCurrentUserId = () => {
  if (userStore.userId) return userStore.userId;
  try {
    const storedUser = localStorage.getItem('userInfo');
    if (storedUser) {
      const parsed = JSON.parse(storedUser);
      return parsed.id ? parseInt(parsed.id) : null;
    }
  } catch (e) {
    console.error('解析用户信息失败:', e);
  }
  return null;
};

// 获取考试信息和学生提交列表
const fetchData = async () => {
  loading.value = true;
  const userId = getCurrentUserId();
  console.log('[exam-marking] fetchData开始, userId:', userId, 'examId:', examId.value);
  
  if (!userId) {
    console.error('[exam-marking] 无法获取用户ID');
    message.error('请先登录');
    loading.value = false;
    return;
  }
  
  try {
    // 获取考试信息
    console.log('[exam-marking] 正在获取考试信息...');
    const examRes = await request.get(`/api/v1/classroom-exams/${examId.value}`, {
      params: { student_id: userId }
    });
    console.log('[exam-marking] 考试信息响应:', examRes);
    if (examRes.code === '0000') {
      examInfo.value = examRes.data;
    }

    // 获取学生提交列表
    console.log('[exam-marking] 正在获取学生列表...');
    const studentsRes = await request.get(`/api/v1/classroom-exams/${examId.value}/students`, {
      params: { teacher_id: userId }
    });
    console.log('[exam-marking] 学生列表响应:', studentsRes);
    if (studentsRes && studentsRes.code === '0000') {
      studentList.value = studentsRes.data?.list || studentsRes.data || [];
      console.log('[exam-marking] studentList已设置:', studentList.value.length, '个学生');
    } else {
      console.warn('[exam-marking] 学生列表响应异常:', studentsRes);
    }
  } catch (error) {
    console.error('[exam-marking] 加载数据失败:', error);
    message.error('加载数据失败');
  } finally {
    loading.value = false;
    console.log('[exam-marking] fetchData完成, studentList长度:', studentList.value.length);
  }
};

// 查看学生答卷
const viewStudentPaper = async (student: any) => {
  currentStudent.value = student;
  paperModalVisible.value = true;
  currentPaper.value = null;

  // 重置评分状态
  questionScores.value = {};
  questionComments.value = {};

  try {
    const res = await request.get(`/api/v1/classroom-exams/${examId.value}/student/${student.student_id}/paper`, {
      params: { teacher_id: userStore.userId }
    });
    if (res.code === '0000') {
      currentPaper.value = res.data;

      // 初始化主观题评分（已有分数则显示，否则为0）
      if (res.data?.questions) {
        res.data.questions.forEach((q: any) => {
          if (q.question_type === 'SHORT_ANSWER') {
            questionScores.value[q.id] = q.score_awarded ?? 0;
            questionComments.value[q.id] = q.teacher_comment || '';
          }
        });
      }
    }
  } catch (error) {
    console.error('加载答卷失败:', error);
    message.error('加载答卷失败');
  }
};

// 批阅学生
const gradeStudent = (student: any) => {
  isGradingMode.value = true;
  viewStudentPaper(student);
};

// 提交评分
const submitGrading = async () => {
  if (!currentPaper.value || !currentStudent.value) return;

  // 检查所有主观题是否都已评分
  const subjectiveQuestions = currentPaper.value.questions.filter(
    (q: any) => q.question_type === 'SHORT_ANSWER'
  );

  for (const q of subjectiveQuestions) {
    const score = questionScores.value[q.id];
    if (score === undefined || score === null) {
      message.warning(`请为第${currentPaper.value.questions.indexOf(q) + 1}题评分`);
      return;
    }
    if (score < 0 || score > q.max_score) {
      message.warning(`第${currentPaper.value.questions.indexOf(q) + 1}题评分必须在0-${q.max_score}分之间`);
      return;
    }
  }

  submitting.value = true;

  try {
    // 构建评分数据 - 使用后端期望的格式
    const marksData = subjectiveQuestions.map((q: any) => ({
      question_id: parseInt(q.id) || q.id,
      score: questionScores.value[q.id],
      comment: questionComments.value[q.id] || undefined
    }));

    // 直接调用API，使用正确的请求格式
    const res = await request.post(
      `/api/v1/exams/${examId.value}/papers/${currentStudent.value.student_id}/marks`,
      {
        marks: marksData,
        overall_comments: null
      },
      {
        params: { teacher_id: getCurrentUserId() || 1 }
      }
    );

    if (res.code === '0000') {
      message.success('评分提交成功');
      paperModalVisible.value = false;
      // 刷新学生列表
      await fetchData();
    } else {
      message.error(res.message || '评分提交失败');
    }
  } catch (error) {
    console.error('评分提交失败:', error);
    message.error('评分提交失败，请重试');
  } finally {
    submitting.value = false;
  }
};

// 返回
const goBack = () => {
  router.push(`/classroom/${classroomId.value}`);
};

// PRD: 跳转到试卷详情页（仅已批阅学生）
const goToPaperView = (record: any) => {
  router.push(`/classroom/${classroomId.value}/exam/${examId.value}/paper/${record.student_id}`);
};

// 格式化时间
const formatDateTime = (time: string) => {
  if (!time) return '-';
  return dayjs(time).format('YYYY/MM/DD HH:mm');
};

// 状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'ONGOING': 'green',
    'SCHEDULED': 'blue',
    'COMPLETED': 'default',
    'UNPUBLISHED': 'orange'
  };
  return colors[status] || 'default';
};

// 状态文字
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'ONGOING': '进行中',
    'SCHEDULED': '未开始',
    'COMPLETED': '已结束',
    'UNPUBLISHED': '未发布'
  };
  return texts[status] || status;
};

// 题型文字
const getQuestionTypeText = (type: string) => {
  const types: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题'
  };
  return types[type] || type;
};

// 分数样式
const getScoreClass = (score: number) => {
  if (score >= 60) return 'pass';
  return 'fail';
};

// 头像颜色
const getAvatarColor = (name: string) => {
  const colors = ['#f56a00', '#7265e6', '#ffbf00', '#00a2ae', '#87d068'];
  const index = (name?.charCodeAt(0) || 0) % colors.length;
  return colors[index];
};

// 判断是否为正确选项
const isCorrectOption = (question: any, key: string) => {
  const correctAnswers = question.correct_answer;
  if (Array.isArray(correctAnswers)) {
    return correctAnswers.includes(key);
  }
  if (typeof correctAnswers === 'string') {
    return correctAnswers === key || correctAnswers.includes(key);
  }
  return false;
};

// 获取正确答案文本（用于判断题）
const getCorrectAnswerText = (question: any) => {
  const answer = question.correct_answer;
  if (answer === true || answer === 'true' || answer === 'True') return '正确';
  if (answer === false || answer === 'false' || answer === 'False') return '错误';
  if (Array.isArray(answer)) {
    if (answer.includes('true') || answer.includes(true)) return '正确';
    if (answer.includes('false') || answer.includes(false)) return '错误';
  }
  return answer || '-';
};

// 判断是否为学生选择的选项
const isSelectedOption = (studentAnswer: any, key: string) => {
  if (Array.isArray(studentAnswer)) {
    return studentAnswer.includes(key);
  }
  return studentAnswer === key;
};

onMounted(() => {
  fetchData();
});
</script>

<style scoped lang="less">
.exam-marking-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    h2 {
      margin: 0;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.student-list {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;

  .student-detail {
    display: flex;
    flex-direction: column;

    .student-name {
      font-weight: 500;
    }

    .student-username {
      font-size: 12px;
      color: #999;
    }
  }
}

.score {
  font-weight: 600;
  font-size: 16px;

  &.pass {
    color: #52c41a;
  }

  &.fail {
    color: #ff4d4f;
  }
}

.pending {
  color: #999;
}

.paper-view {
  .paper-summary {
    margin-bottom: 16px;
  }

  .score-highlight {
    font-size: 18px;
    font-weight: 600;
    color: #1890ff;
  }

  .questions-list {
    .question-item {
      padding: 16px;
      margin-bottom: 16px;
      background: #f9f9f9;
      border-radius: 8px;

      .question-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;

        .question-number {
          font-weight: 600;
        }

        .question-score {
          margin-left: auto;
          
          .correct {
            color: #52c41a;
            font-weight: 600;
          }

          .incorrect {
            color: #ff4d4f;
            font-weight: 600;
          }
        }
      }

      .question-content {
        font-size: 15px;
        margin-bottom: 12px;
        line-height: 1.6;
      }

      .question-options {
        .option {
          padding: 8px 12px;
          margin: 4px 0;
          border-radius: 4px;
          display: flex;
          align-items: center;
          gap: 8px;

          &.correct-option {
            background: #f6ffed;
            border: 1px solid #b7eb8f;
          }

          &.selected-option {
            background: #e6f7ff;
            border: 1px solid #91d5ff;
          }

          &.wrong-selected {
            background: #fff2f0;
            border: 1px solid #ffccc7;
          }

          .correct-icon {
            color: #52c41a;
            margin-left: auto;
          }

          .wrong-icon {
            color: #ff4d4f;
            margin-left: auto;
          }
        }
      }

      .answer-compare {
        padding: 12px;
        background: #fff;
        border-radius: 4px;

        .answer-row {
          margin: 4px 0;

          .label {
            color: #666;
          }

          .correct {
            color: #52c41a;
            font-weight: 500;
          }

          .incorrect {
            color: #ff4d4f;
            font-weight: 500;
          }
        }
      }

      // 简答题样式
      .essay-section {
        margin-top: 12px;

        .essay-answer {
          margin-bottom: 12px;

          .answer-label {
            font-weight: 500;
            color: #666;
            margin-bottom: 6px;
          }

          .answer-content {
            padding: 12px;
            border-radius: 4px;
            white-space: pre-wrap;
            line-height: 1.6;
            min-height: 60px;
          }

          .student-answer {
            background: #f0f5ff;
            border: 1px solid #adc6ff;
          }

          .reference-answer {
            background: #f6ffed;
            border: 1px solid #b7eb8f;
          }
        }

        .grading-section {
          margin-top: 16px;

          .grading-input {
            .score-input-row {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 12px;

              .input-label {
                font-weight: 500;
                min-width: 50px;
              }

              .score-max {
                color: #999;
              }
            }

            .comment-input-row {
              display: flex;
              align-items: flex-start;
              gap: 8px;

              .input-label {
                font-weight: 500;
                min-width: 50px;
                padding-top: 5px;
              }
            }
          }
        }

        // 已批阅的只读评分信息样式
        .graded-info {
          margin-top: 16px;
          padding: 12px;
          background: #f6ffed;
          border-radius: 6px;
          border: 1px solid #b7eb8f;

          .graded-score {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .label {
              font-weight: 500;
              color: #666;
            }

            .score {
              font-weight: 600;
              color: #52c41a;
              font-size: 16px;
            }
          }

          .teacher-comment {
            display: flex;
            gap: 8px;

            .label {
              font-weight: 500;
              color: #666;
              flex-shrink: 0;
            }

            .comment {
              color: #333;
              line-height: 1.5;
            }
          }
        }
      }
    }
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>

