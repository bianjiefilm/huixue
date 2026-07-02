<template>
  <div class="exam-paper-view-page">
    <a-spin :spinning="loading" tip="加载中...">
      <div v-if="paperData" class="paper-container">
        <!-- 顶部信息栏 -->
        <div class="page-header">
          <div class="header-left">
            <a-button type="text" @click="goBack">
              <template #icon><arrow-left-outlined /></template>
              返回
            </a-button>
            <h1>{{ examInfo?.title || '考试' }}</h1>
            <a-tag color="green">已批阅</a-tag>
          </div>
          <div class="header-meta">
            <span>考试时长: {{ examInfo?.duration_minutes || 60 }}分钟</span>
            <a-divider type="vertical" />
            <span>试题总数: {{ questions.length }}题</span>
            <a-divider type="vertical" />
            <span>试卷满分: {{ totalPossibleScore }}分</span>
          </div>
        </div>

        <!-- 左侧题号导航 -->
        <div class="question-nav">
          <div class="nav-title">题目导航</div>

          <!-- 状态图例 -->
          <div class="status-legend">
            <span class="legend-item correct"><check-circle-filled /> 正确</span>
            <span class="legend-item incorrect"><close-circle-filled /> 错误</span>
            <span class="legend-item graded"><edit-filled /> 已评分</span>
          </div>

          <a-divider />

          <!-- 按题型分组显示 -->
          <div v-for="(group, groupName) in questionGroups" :key="groupName" class="question-group">
            <div class="group-title">{{ groupName }}</div>
            <div class="question-numbers">
              <div
                v-for="(q, idx) in group"
                :key="q.id"
                class="question-number"
                :class="getQuestionStatusClass(q)"
                @click="scrollToQuestion(q.globalIndex)"
              >
                {{ q.globalIndex + 1 }}
              </div>
            </div>
          </div>
        </div>

        <!-- 中间答题区 -->
        <div class="question-content-area" ref="contentAreaRef">
          <div
            v-for="(question, index) in questions"
            :key="question.id"
            :ref="el => setQuestionRef(el, index)"
            class="question-card"
          >
            <div class="question-header">
              <div class="question-title">
                <span class="question-num">第 {{ index + 1 }} 题</span>
                <a-tag>{{ getQuestionTypeText(question.question_type) }}</a-tag>
              </div>
              <div class="question-score-info">
                <span class="label">得分：</span>
                <span :class="['score', question.is_correct ? 'correct' : 'incorrect']">
                  {{ question.score_awarded || 0 }} / {{ question.max_score }} 分
                </span>
                <a-tag v-if="question.is_correct" color="green">正确</a-tag>
                <a-tag v-else-if="question.is_correct === false" color="red">错误</a-tag>
              </div>
            </div>

            <div class="question-body">
              <div class="question-text">{{ question.content }}</div>

              <!-- 选择题选项 -->
              <div v-if="hasOptions(question)" class="options-list">
                <div
                  v-for="(option, optIdx) in parseOptions(question.options)"
                  :key="optIdx"
                  class="option-item"
                  :class="getOptionClass(question, option, optIdx)"
                >
                  <span class="option-label">{{ String.fromCharCode(65 + optIdx) }}</span>
                  <span class="option-text">{{ option }}</span>
                  <check-circle-filled v-if="isCorrectOption(question, option, optIdx)" class="icon correct" />
                  <close-circle-filled v-if="isWrongSelected(question, option, optIdx)" class="icon incorrect" />
                </div>
              </div>

              <!-- 判断题答案 -->
              <div v-if="question.question_type === 'TRUE_FALSE'" class="judge-answer">
                <div class="answer-row">
                  <span class="label">学生答案：</span>
                  <span :class="question.is_correct ? 'correct' : 'incorrect'">
                    {{ formatJudgeAnswer(question.student_answer) }}
                  </span>
                </div>
                <div class="answer-row">
                  <span class="label">正确答案：</span>
                  <span class="correct">{{ formatJudgeAnswer(question.correct_answer) }}</span>
                </div>
              </div>

              <!-- 简答题 -->
              <div v-if="question.question_type === 'SHORT_ANSWER'" class="essay-section">
                <div class="answer-block student">
                  <div class="block-title">学生答案</div>
                  <div class="block-content">{{ question.student_answer || '未作答' }}</div>
                </div>
                <div class="answer-block reference">
                  <div class="block-title">参考答案 / 评分点</div>
                  <div class="block-content">{{ question.correct_answer || '无参考答案' }}</div>
                </div>
                <div v-if="question.teacher_comment" class="answer-block comment">
                  <div class="block-title">教师评语</div>
                  <div class="block-content">{{ question.teacher_comment }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧成绩看板 -->
        <div class="score-card">
          <div class="card-title">成绩看板</div>

          <div class="student-info">
            <a-avatar :size="48" style="background-color: #1890ff">
              {{ studentInfo?.name?.charAt(0) || '学' }}
            </a-avatar>
            <div class="info-text">
              <div class="name">{{ studentInfo?.name || '学生' }}</div>
              <div class="username">{{ studentInfo?.username || '' }}</div>
            </div>
          </div>

          <div class="total-score">
            <div class="score-label">总成绩</div>
            <div class="score-value" :class="isPassed ? 'pass' : 'fail'">
              {{ paperData.total_score_achieved || 0 }}<span class="unit">分</span>
            </div>
          </div>

          <a-divider />

          <div class="score-breakdown">
            <div class="breakdown-title">分项得分</div>
            <div v-for="(score, type) in scoreByType" :key="type" class="breakdown-item">
              <span class="type-name">{{ type }}：</span>
              <span class="type-score">{{ score.achieved }}/{{ score.total }}分</span>
            </div>
          </div>

          <a-divider />

          <div class="submit-info">
            <div class="info-row">
              <span class="label">提交时间：</span>
              <span class="value">{{ formatDateTime(paperData.attempt_submission_time) }}</span>
            </div>
            <div class="info-row">
              <span class="label">用时：</span>
              <span class="value">{{ Math.round((paperData.actual_duration_seconds || 0) / 60) }}分钟</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!loading" class="no-paper">
        <a-result
          :status="errorMessage ? 'warning' : 'info'"
          :title="errorMessage || '未找到试卷'"
          :sub-title="errorMessage || '该学生暂无答卷记录，可能尚未提交考试'"
        >
          <template #extra>
            <a-button type="primary" @click="goBack">返回</a-button>
          </template>
        </a-result>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  CheckCircleFilled,
  CloseCircleFilled,
  EditFilled
} from '@ant-design/icons-vue';
import request from '@/utils/request';

const route = useRoute();
const router = useRouter();

const classroomId = computed(() => route.params.classroomId as string);
const examId = computed(() => route.params.examId as string);
const studentId = computed(() => route.params.studentId as string);

const loading = ref(false);
const examInfo = ref<any>(null);
const paperData = ref<any>(null);
const contentAreaRef = ref<HTMLElement | null>(null);
const questionRefs = ref<Record<number, HTMLElement>>({});
const errorMessage = ref('');

// 计算属性 - 合并questions和answers数据
const questions = computed(() => {
  if (!paperData.value) return [];
  const rawQuestions = paperData.value.questions || [];
  const answers = paperData.value.answers || [];

  // 创建答案映射 (question_id -> answer)
  const answerMap: Record<string, any> = {};
  answers.forEach((a: any) => {
    answerMap[String(a.question_id)] = a;
  });

  // 合并题目和答案
  return rawQuestions.map((q: any) => {
    const answer = answerMap[String(q.id)] || {};
    return {
      ...q,
      max_score: q.score || 0,
      student_answer: answer.answer_data,
      score_awarded: answer.score_awarded,
      is_correct: answer.is_correct,
      teacher_comment: answer.teacher_comments,
      correct_answer: q.correct_answers || q.correct_answer
    };
  });
});

const totalPossibleScore = computed(() => {
  return questions.value.reduce((sum: number, q: any) => sum + (q.max_score || 0), 0);
});

const studentInfo = computed(() => ({
  name: paperData.value?.student_name,
  username: paperData.value?.student_number || paperData.value?.student_username
}));

const isPassed = computed(() => {
  const passScore = examInfo.value?.pass_mark || 60;
  return (paperData.value?.total_score_achieved || 0) >= passScore;
});

// 按题型分组
const questionGroups = computed(() => {
  const groups: Record<string, any[]> = {};
  questions.value.forEach((q: any, index: number) => {
    const typeName = getQuestionTypeText(q.question_type);
    if (!groups[typeName]) {
      groups[typeName] = [];
    }
    groups[typeName].push({ ...q, globalIndex: index });
  });
  return groups;
});

// 分项得分统计
const scoreByType = computed(() => {
  const breakdown: Record<string, { achieved: number; total: number }> = {};
  questions.value.forEach((q: any) => {
    const typeName = getQuestionTypeText(q.question_type);
    if (!breakdown[typeName]) {
      breakdown[typeName] = { achieved: 0, total: 0 };
    }
    breakdown[typeName].achieved += q.score_awarded || 0;
    breakdown[typeName].total += q.max_score || 0;
  });
  return breakdown;
});

// 辅助函数
function getQuestionTypeText(type: string): string {
  const typeMap: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题',
    'FILL_BLANK': '填空题'
  };
  return typeMap[type] || type;
}

function hasOptions(question: any): boolean {
  return ['SINGLE_CHOICE', 'MULTIPLE_CHOICE'].includes(question.question_type);
}

function parseOptions(options: any): string[] {
  if (!options) return [];
  if (Array.isArray(options)) return options;
  try {
    return JSON.parse(options);
  } catch {
    return [];
  }
}

function getQuestionStatusClass(question: any): string {
  if (question.question_type === 'SHORT_ANSWER') {
    return question.score_awarded !== null ? 'graded' : 'ungraded';
  }
  return question.is_correct ? 'correct' : 'incorrect';
}

function getOptionClass(question: any, option: string, index: number): string {
  const classes: string[] = [];
  const isSelected = isStudentSelected(question, option, index);
  const isCorrect = isCorrectOption(question, option, index);

  if (isSelected && isCorrect) {
    classes.push('correct-selected');
  } else if (isSelected && !isCorrect) {
    classes.push('wrong-selected');
  } else if (isCorrect) {
    classes.push('correct-not-selected');
  }

  return classes.join(' ');
}

function isStudentSelected(question: any, option: string, index: number): boolean {
  const answer = question.student_answer;
  if (!answer) return false;

  const optionKey = String.fromCharCode(65 + index);
  if (Array.isArray(answer)) {
    return answer.includes(option) || answer.includes(optionKey);
  }
  return answer === option || answer === optionKey;
}

function isCorrectOption(question: any, option: string, index: number): boolean {
  const correct = question.correct_answer;
  if (!correct) return false;

  const optionKey = String.fromCharCode(65 + index);
  if (Array.isArray(correct)) {
    return correct.includes(option) || correct.includes(optionKey);
  }
  if (typeof correct === 'string' && correct.includes(',')) {
    const correctList = correct.split(',').map((s: string) => s.trim());
    return correctList.includes(option) || correctList.includes(optionKey);
  }
  return correct === option || correct === optionKey;
}

function isWrongSelected(question: any, option: string, index: number): boolean {
  return isStudentSelected(question, option, index) && !isCorrectOption(question, option, index);
}

function formatJudgeAnswer(answer: any): string {
  if (answer === null || answer === undefined) {
    return '未作答';
  }
  if (answer === true || answer === 'true' || answer === 'True' || answer === '正确') {
    return '正确';
  }
  if (answer === false || answer === 'false' || answer === 'False' || answer === '错误') {
    return '错误';
  }
  return String(answer);
}

function formatDateTime(dateStr: string): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function setQuestionRef(el: any, index: number) {
  if (el) {
    questionRefs.value[index] = el;
  }
}

function scrollToQuestion(index: number) {
  const el = questionRefs.value[index];
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function goBack() {
  router.push(`/classroom/${classroomId.value}/exam/${examId.value}/marking`);
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
  errorMessage.value = '';
  try {
    const teacherId = getCurrentUserId();

    // 获取考试信息
    const examRes = await request.get(`/api/v1/classroom-exams/${examId.value}`, {
      params: { student_id: teacherId }
    });
    examInfo.value = examRes.data;

    // 获取学生试卷详情
    const paperRes = await request.get(
      `/api/v1/exams/${examId.value}/papers/${studentId.value}`,
      { params: { teacher_id: teacherId } }
    );
    paperData.value = paperRes.data;
  } catch (error: any) {
    console.error('获取数据失败:', error);
    // 处理404错误（试卷不存在）
    if (error.response?.status === 404) {
      errorMessage.value = '该学生暂无答卷记录，可能尚未提交考试';
    } else {
      errorMessage.value = error.response?.data?.detail || '获取数据失败';
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchData();
});
</script>

<style scoped lang="less">
.exam-paper-view-page {
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

  .header-meta {
    color: #666;
    font-size: 14px;
  }
}

.paper-container {
  display: flex;
  padding: 24px;
  gap: 24px;
  max-width: 1600px;
  margin: 0 auto;
}

// 左侧题号导航
.question-nav {
  width: 200px;
  min-width: 200px;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  height: fit-content;
  position: sticky;
  top: 24px;

  .nav-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 12px;
  }

  .status-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 12px;

    .legend-item {
      display: flex;
      align-items: center;
      gap: 4px;

      &.correct { color: #52c41a; }
      &.incorrect { color: #ff4d4f; }
      &.graded { color: #1890ff; }
    }
  }

  .question-group {
    margin-bottom: 16px;

    .group-title {
      font-size: 13px;
      color: #666;
      margin-bottom: 8px;
    }

    .question-numbers {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .question-number {
      width: 32px;
      height: 32px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-size: 14px;
      font-weight: 500;
      transition: all 0.2s;
      border: 1px solid #d9d9d9;
      background: #fff;

      &:hover {
        border-color: #1890ff;
        color: #1890ff;
      }

      &.correct {
        background: #f6ffed;
        border-color: #52c41a;
        color: #52c41a;
      }

      &.incorrect {
        background: #fff2f0;
        border-color: #ff4d4f;
        color: #ff4d4f;
      }

      &.graded {
        background: #e6f7ff;
        border-color: #1890ff;
        color: #1890ff;
      }
    }
  }
}

// 中间答题区
.question-content-area {
  flex: 1;
  min-width: 0;
  max-height: calc(100vh - 140px);
  overflow-y: auto;
  padding-right: 8px;

  .question-card {
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;

    .question-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid #f0f0f0;

      .question-title {
        display: flex;
        align-items: center;
        gap: 8px;

        .question-num {
          font-weight: 600;
          font-size: 16px;
        }
      }

      .question-score-info {
        display: flex;
        align-items: center;
        gap: 8px;

        .score {
          font-weight: 600;
          font-size: 16px;

          &.correct { color: #52c41a; }
          &.incorrect { color: #ff4d4f; }
        }
      }
    }

    .question-text {
      font-size: 15px;
      line-height: 1.6;
      margin-bottom: 16px;
    }

    .options-list {
      .option-item {
        display: flex;
        align-items: center;
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 6px;
        border: 1px solid #e8e8e8;
        transition: all 0.2s;

        .option-label {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: #f5f5f5;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 500;
          margin-right: 12px;
        }

        .option-text {
          flex: 1;
        }

        .icon {
          font-size: 18px;
          margin-left: 8px;

          &.correct { color: #52c41a; }
          &.incorrect { color: #ff4d4f; }
        }

        &.correct-selected {
          background: #f6ffed;
          border-color: #52c41a;

          .option-label {
            background: #52c41a;
            color: #fff;
          }
        }

        &.wrong-selected {
          background: #fff2f0;
          border-color: #ff4d4f;

          .option-label {
            background: #ff4d4f;
            color: #fff;
          }
        }

        &.correct-not-selected {
          background: #f6ffed;
          border-color: #b7eb8f;
        }
      }
    }

    .judge-answer {
      .answer-row {
        margin-bottom: 8px;

        .label {
          color: #666;
        }

        .correct { color: #52c41a; font-weight: 500; }
        .incorrect { color: #ff4d4f; font-weight: 500; }
      }
    }

    .essay-section {
      .answer-block {
        margin-bottom: 16px;

        .block-title {
          font-weight: 500;
          margin-bottom: 8px;
          color: #333;
        }

        .block-content {
          padding: 12px;
          border-radius: 6px;
          white-space: pre-wrap;
          line-height: 1.6;
          min-height: 60px;
        }

        &.student .block-content {
          background: #f0f5ff;
          border: 1px solid #adc6ff;
        }

        &.reference .block-content {
          background: #f6ffed;
          border: 1px solid #b7eb8f;
        }

        &.comment .block-content {
          background: #fffbe6;
          border: 1px solid #ffe58f;
        }
      }
    }
  }
}

// 右侧成绩看板
.score-card {
  width: 280px;
  min-width: 280px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  height: fit-content;
  position: sticky;
  top: 24px;

  .card-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 16px;
  }

  .student-info {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;

    .info-text {
      .name {
        font-size: 16px;
        font-weight: 500;
      }

      .username {
        font-size: 12px;
        color: #999;
      }
    }
  }

  .total-score {
    text-align: center;
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;

    .score-label {
      font-size: 14px;
      color: #666;
      margin-bottom: 8px;
    }

    .score-value {
      font-size: 48px;
      font-weight: 700;
      line-height: 1;

      .unit {
        font-size: 18px;
        font-weight: normal;
        margin-left: 4px;
      }

      &.pass { color: #52c41a; }
      &.fail { color: #ff4d4f; }
    }
  }

  .score-breakdown {
    .breakdown-title {
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 12px;
    }

    .breakdown-item {
      display: flex;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px dashed #f0f0f0;

      &:last-child {
        border-bottom: none;
      }

      .type-name {
        color: #666;
      }

      .type-score {
        font-weight: 500;
      }
    }
  }

  .submit-info {
    .info-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;

      .label {
        color: #999;
      }

      .value {
        color: #333;
      }
    }
  }
}

.no-paper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}
</style>
