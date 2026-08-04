<template>
  <PageShell max-width="wide" class="exam-marking-detail-page">
    <PageHeaderBar
      :title="`${exam?.exam_name || '考试'} - ${studentPaper?.student_name || '学生'}的试卷`"
      show-back
      :back-to="`/classroom/${classroomId}/course/${courseId}/exam/${examId}/marking`"
    >
      <template #actions>
        <a-tag v-if="studentPaper" :color="studentPaper.is_graded ? 'green' : 'red'">
          {{ studentPaper.is_graded ? '已批阅' : '未批阅' }}
        </a-tag>
      </template>
    </PageHeaderBar>

    <a-spin :spinning="loading" tip="加载中...">
      <div v-if="studentPaper" class="marking-container">
        <!-- 左侧题目导航 -->
        <div class="question-nav">
          <div class="student-info">
            <h3>{{ studentPaper.student_name }}</h3>
            <p>提交时间：{{ formatDateTime(studentPaper.attempt_submission_time) || '未提交' }}</p>
            <p>得分：{{ getTotalScore() }}/{{ getTotalPossibleScore() }}</p>
          </div>
          
          <a-divider />
          
          <div class="question-list">
            <h3>试题列表</h3>
            <div 
              v-for="(question, index) in studentPaper.questions" 
              :key="question.question_id"
              class="question-list-item"
              :class="{
                'active': currentQuestionIndex === index,
                'unmarked': isQuestionUnmarked(question),
                'marked': isQuestionMarked(question),
                'auto-marked': isQuestionAutoMarked(question)
              }"
              @click="currentQuestionIndex = index"
            >
              <div class="question-item-content">
                <div class="question-num">{{ index + 1 }}</div>
                <div class="question-type">
                  {{ getQuestionTypeText(question.question_type) }}
                  <span class="question-score">({{ question.question_score }}分)</span>
                </div>
              </div>
              <div class="question-status">
                <a-tag v-if="question.question_type === 'essay'" :color="getQuestionStatusColor(question)">
                  {{ getQuestionStatusText(question) }}
                </a-tag>
                <span v-else class="auto-score">
                  {{ getQuestionScore(question) }}/{{ question.question_score }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="action-buttons">
            <a-button 
              type="primary" 
              :disabled="!canSubmitMarking"
              @click="submitMarking"
              block
            >
              提交评分
            </a-button>
            <a-button 
              style="margin-top: 10px;"
              @click="goToNextUnmarked"
              block
            >
              查找未评分题目
            </a-button>
          </div>
        </div>
        
        <!-- 右侧题目详情和打分 -->
        <div class="question-detail">
          <div v-if="currentQuestion" class="question-content">
            <!-- 题目信息 -->
            <div class="question-header">
              <h3>
                {{ currentQuestionIndex + 1 }}. {{ getQuestionTypeText(currentQuestion.question_type) }}
                ({{ currentQuestion.question_score }}分)
              </h3>
              <a-tag v-if="currentQuestion.question_type === 'essay'" :color="getQuestionStatusColor(currentQuestion)">
                {{ getQuestionStatusText(currentQuestion) }}
              </a-tag>
            </div>
            
            <div class="question-body">
              <!-- 题目内容 -->
              <div class="question-content-text">{{ currentQuestion.question_content }}</div>
              
              <!-- 选项（单选、多选、判断题） -->
              <div v-if="['single', 'multiple', 'judge'].includes(currentQuestion.question_type)" class="question-options">
                <div 
                  v-for="option in currentQuestion.options" 
                  :key="option.option_id"
                  class="option-item"
                  :class="{
                    'selected': isOptionSelected(option.option_id),
                    'correct': option.is_correct,
                    'incorrect': isOptionSelected(option.option_id) && !option.is_correct
                  }"
                >
                  <div class="option-letter">{{ option.option_label }}</div>
                  <div class="option-content">{{ option.option_content }}</div>
                </div>
              </div>
              
              <!-- 简答题学生答案 -->
              <div v-if="currentQuestion.question_type === 'essay'" class="essay-answer">
                <h4>学生答案:</h4>
                <div class="student-answer-box">
                  {{ getStudentAnswer(currentQuestion) || '未作答' }}
                </div>
                
                <h4 class="mt-4">参考答案:</h4>
                <div class="reference-answer-box">
                  {{ currentQuestion.question_answer || '无参考答案' }}
                </div>
              </div>
              
              <!-- 自动评分的题目展示分数 -->
              <div v-if="isQuestionAutoMarked(currentQuestion)" class="auto-graded">
                <a-alert 
                  message="此题为客观题，系统已自动评分" 
                  type="info" 
                  show-icon
                />
                <div class="score-display">
                  得分: {{ getQuestionScore(currentQuestion) }}/{{ currentQuestion.question_score }}
                </div>
              </div>
              
              <!-- 主观题评分区域 -->
              <div v-if="currentQuestion.question_type === 'essay'" class="marking-area">
                <h4>教师评分:</h4>
                <div class="score-input">
                  <span class="score-label">得分：</span>
                  <a-input-number
                    v-model:value="essayScore"
                    :min="0"
                    :max="currentQuestion.question_score"
                    :precision="0"
                    @change="handleScoreChange"
                  />
                  <span class="score-max">/ {{ currentQuestion.question_score }}</span>
                </div>
                
                <div class="teacher-comment">
                  <h4>教师评语:</h4>
                  <a-textarea
                    v-model:value="essayComment"
                    placeholder="请输入评语..."
                    :rows="4"
                    @change="handleCommentChange"
                  />
                </div>
                
                <div class="save-marking">
                  <a-button 
                    type="primary"
                    @click="saveQuestionMarking"
                    :disabled="!canSaveQuestionMarking"
                  >
                    保存评分
                  </a-button>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-question-selected">
            <a-empty description="请从左侧选择题目进行批阅" />
          </div>
        </div>
      </div>
      
      <div v-else-if="!loading" class="no-paper">
        <a-result
          status="warning"
          title="未找到试卷"
          sub-title="找不到该学生的试卷信息或者试卷尚未提交"
        >
          <template #extra>
            <router-link :to="`/classroom/${classroomId}/course/${courseId}/exam/${examId}/marking`">
              <a-button type="primary">
                返回学生列表
              </a-button>
            </router-link>
          </template>
        </a-result>
      </div>
    </a-spin>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  ArrowLeftOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined
} from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import { 
  getExamDetail,
  getStudentPaper,
  submitGrading,
  type ExamInfo,
  type ExamPaperDetail,
  type GradingRequest
} from '@/api/exam';
import { useUserStore } from '@/stores/user';

// 路由相关
const route = useRoute();
const router = useRouter();
const classroomId = computed(() => route.params.classroomId as string);
const courseId = computed(() => route.params.courseId as string);
const examId = computed(() => route.params.examId as string);
const studentId = computed(() => route.params.studentId as string);

// 状态管理
const loading = ref(false);
const exam = ref<ExamInfo | null>(null);
const studentPaper = ref<ExamPaperDetail | null>(null);
const userStore = useUserStore();
const currentQuestionIndex = ref(0);
const essayScore = ref(0);
const essayComment = ref('');
const questionScores = ref<Map<number, { score: number; comment: string }>>(new Map());

// 计算属性
const currentQuestion = computed(() => {
  if (!studentPaper.value || currentQuestionIndex.value < 0 || 
      currentQuestionIndex.value >= studentPaper.value.questions.length) {
    return undefined;
  }
  return studentPaper.value.questions[currentQuestionIndex.value];
});

const unmarkedEssayQuestions = computed(() => {
  if (!studentPaper.value) return [];
  
  return studentPaper.value.questions
    .map((q, idx) => ({ question: q, index: idx }))
    .filter(item => item.question.question_type === 'essay' && !isQuestionMarked(item.question));
});

const canSubmitMarking = computed(() => {
  if (!studentPaper.value) return false;
  
  // 检查是否所有简答题都已评分
  return !studentPaper.value.questions.some(q => 
    q.question_type === 'essay' && !isQuestionMarked(q)
  );
});

const canSaveQuestionMarking = computed(() => {
  if (!currentQuestion.value || currentQuestion.value.question_type !== 'essay') return false;
  
  // 检查分数是否已设置
  return essayScore.value >= 0 && essayScore.value <= currentQuestion.value.question_score;
});

// 新增辅助函数
function formatDateTime(datetime?: string | null): string {
  if (!datetime) return '';
  return new Date(datetime).toLocaleString('zh-CN');
}

function getTotalScore(): number {
  if (!studentPaper.value) return 0;
  return studentPaper.value.total_score_achieved || 0;
}

function getTotalPossibleScore(): number {
  if (!studentPaper.value) return 0;
  return studentPaper.value.questions.reduce((total, q) => total + q.question_score, 0);
}

function isQuestionUnmarked(question: any): boolean {
  if (question.question_type !== 'essay') return false;
  const questionId = question.question_id;
  return !questionScores.value.has(questionId) && !getAnswerScore(question);
}

function isQuestionMarked(question: any): boolean {
  if (question.question_type !== 'essay') return false;
  const questionId = question.question_id;
  return questionScores.value.has(questionId) || getAnswerScore(question) !== null;
}

function isQuestionAutoMarked(question: any): boolean {
  return question.question_type !== 'essay';
}

function getQuestionScore(question: any): number {
  const questionId = question.question_id;
  
  // 先查看本地评分
  const localScore = questionScores.value.get(questionId);
  if (localScore) return localScore.score;
  
  // 再查看学生答案中的得分
  const answerScore = getAnswerScore(question);
  if (answerScore !== null) return answerScore;
  
  return 0;
}

function getAnswerScore(question: any): number | null {
  if (!studentPaper.value) return null;
  const answer = studentPaper.value.answers.find(a => a.question_id === question.question_id);
  return answer?.score_achieved ?? null;
}

function getStudentAnswer(question: any): string {
  if (!studentPaper.value) return '';
  const answer = studentPaper.value.answers.find(a => a.question_id === question.question_id);
  return answer?.answer_text || '';
}

// 辅助函数
function getQuestionTypeText(type: string): string {
  switch (type) {
    case 'single':
      return '单选题';
    case 'multiple':
      return '多选题';
    case 'judge':
      return '判断题';
    case 'essay':
      return '简答题';
    default:
      return '未知类型';
  }
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'green';
    case 'partial':
      return 'orange';
    case 'unmarked':
      return 'red';
    default:
      return 'default';
  }
}

function getStatusText(status: string): string {
  switch (status) {
    case 'completed':
      return '已批阅';
    case 'partial':
      return '部分批阅';
    case 'unmarked':
      return '未批阅';
    default:
      return '未知状态';
  }
}

function getQuestionStatusColor(question: any): string {
  if (isQuestionAutoMarked(question)) return 'blue';
  if (isQuestionMarked(question)) return 'green';
  return 'red';
}

function getQuestionStatusText(question: any): string {
  if (isQuestionAutoMarked(question)) return '自动评分';
  if (isQuestionMarked(question)) return '已评分';
  return '未评分';
}

function isOptionSelected(optionId: string): boolean {
  if (!currentQuestion.value || !studentPaper.value) return false;
  const answer = studentPaper.value.answers.find(a => a.question_id === currentQuestion.value!.question_id);
  if (!answer) return false;
  
  // 单选和判断题
  if (currentQuestion.value.question_type === 'single' || currentQuestion.value.question_type === 'judge') {
    return answer.answer_text === optionId;
  }
  
  // 多选题
  if (currentQuestion.value.question_type === 'multiple') {
    try {
      const selectedOptions = JSON.parse(answer.answer_text || '[]');
      return Array.isArray(selectedOptions) && selectedOptions.includes(optionId);
    } catch {
      return false;
    }
  }
  
  return false;
}

// 事件处理
function handleScoreChange(value: number) {
  essayScore.value = value;
}

function handleCommentChange(e: Event) {
  // 评语变更逻辑
}

function saveQuestionMarking() {
  if (!currentQuestion.value || !studentPaper.value) return;
  
  // 保存到本地Map中
  questionScores.value.set(currentQuestion.value.question_id, {
    score: essayScore.value,
    comment: essayComment.value
  });
  
  message.success('评分已保存');
  
  // 自动跳转到下一个未评分的题目
  goToNextUnmarked();
}

function goToNextUnmarked() {
  if (unmarkedEssayQuestions.value.length > 0) {
    currentQuestionIndex.value = unmarkedEssayQuestions.value[0].index;
  } else {
    message.info('所有题目已评分完成');
  }
}

async function submitMarking() {
  if (!studentPaper.value) return;
  
  // 准备提交数据
  const marks: GradingRequest['question_scores'] = [];
  
  // 收集所有主观题的评分
  studentPaper.value.questions.forEach(question => {
    if (question.question_type === 'essay') {
      const questionId = question.question_id;
      const localScore = questionScores.value.get(questionId);
      
      if (localScore) {
        marks.push({
          question_id: questionId,
          score: localScore.score,
          comment: localScore.comment || undefined
        });
      } else {
        // 检查是否已经有得分
        const existingScore = getAnswerScore(question);
        if (existingScore !== null) {
          marks.push({
            question_id: questionId,
            score: existingScore,
            comment: undefined
          });
        }
      }
    }
  });
  
  try {
    const result = await submitGrading({
      exam_id: parseInt(examId.value),
      student_id: parseInt(studentId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1,
      data: {
        question_scores: marks,
        total_score: marks.reduce((sum, m) => sum + m.score, 0)
      }
    });
    
    if (result.code === '0000') {
      message.success('试卷评分提交成功');
      
      // 清空本地评分
      questionScores.value.clear();
      
      // 刷新试卷数据
      await fetchData();
    } else {
      message.error(result.message || '提交评分失败');
    }
  } catch (error) {
    console.error('提交评分失败:', error);
    message.error('提交评分失败，请重试');
  }
}

// 数据加载
async function fetchData() {
  loading.value = true;
  try {
    // 获取考试信息
    const examRes = await getExamDetail({
      exam_id: parseInt(examId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (examRes.code === '0000') {
      exam.value = examRes.data;
    } else {
      message.error(examRes.message || '获取考试信息失败');
      return;
    }
    
    // 获取学生试卷
    const paperRes = await getStudentPaper({
      exam_id: parseInt(examId.value),
      student_id: parseInt(studentId.value),
      teacher_id: parseInt(userStore.userInfo?.id) || 1
    });
    
    if (paperRes.code === '0000') {
      studentPaper.value = paperRes.data;
      
      // 如果是第一道简答题并且未评分，则预设评分为0
      setupInitialEssayQuestion();
    } else {
      message.warning(paperRes.message || '未找到学生试卷');
    }
  } catch (error) {
    console.error('获取数据失败:', error);
    message.error('获取数据失败');
  } finally {
    loading.value = false;
  }
}

function setupInitialEssayQuestion() {
  if (!studentPaper.value) return;
  
  // 初始化到第一道未评分的简答题
  if (unmarkedEssayQuestions.value.length > 0) {
    currentQuestionIndex.value = unmarkedEssayQuestions.value[0].index;
  }
}

// 监听当前题目变化
watch(currentQuestion, (newQuestion) => {
  if (newQuestion && newQuestion.question_type === 'essay') {
    // 更新评分和评语
    const questionId = newQuestion.question_id;
    const localScore = questionScores.value.get(questionId);
    
    if (localScore) {
      essayScore.value = localScore.score;
      essayComment.value = localScore.comment;
    } else {
      const existingScore = getAnswerScore(newQuestion);
      essayScore.value = existingScore !== null ? existingScore : 0;
      essayComment.value = '';
    }
  }
});

// 生命周期钩子
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.exam-marking-detail-page {
  /* PageShell handles outer padding */
}



.marking-container {
  display: flex;
  gap: var(--hx-space-4);
  background: var(--hx-color-bg-container);
  border-radius: 8px;
  border: 1px solid var(--hx-color-border-muted);
  min-height: 600px;
  margin-top: var(--hx-space-4);
  overflow: hidden;
}

.question-nav {
  width: 280px;
  min-width: 280px;
  background: var(--hx-color-bg-layout);
  padding: var(--hx-space-5);
  border-right: 1px solid #e8e8e8;
  border-radius: 8px 0 0 8px;
  display: flex;
  flex-direction: column;
}

.student-info {
  margin-bottom: 16px;
}

.student-info h3 {
  margin-top: 0;
}

.question-list {
  flex: 1;
  overflow-y: auto;
}

.question-list h3 {
  margin-top: 0;
}

.question-list-item {
  padding: 10px;
  margin-bottom: 8px;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 4px solid transparent;
  transition: all 0.3s;
}

.question-list-item:hover {
  background: #f0f0f0;
}

.question-list-item.active {
  background: #e6f7ff;
  border-left: 4px solid #1890ff;
}

.question-list-item.unmarked {
  border-left: 4px solid #ff4d4f;
}

.question-list-item.marked {
  border-left: 4px solid #52c41a;
}

.question-list-item.auto-marked {
  border-left: 4px solid #1890ff;
}

.question-item-content {
  display: flex;
  align-items: center;
}

.question-num {
  width: 24px;
  height: 24px;
  background: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  font-weight: bold;
}

.active .question-num {
  background: #1890ff;
  color: #fff;
}

.question-type {
  font-size: 14px;
}

.question-score {
  color: #999;
  font-size: 12px;
}

.auto-score {
  font-size: 12px;
  color: #1890ff;
}

.action-buttons {
  margin-top: 20px;
}

.question-detail {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #f0f0f0;
}

.question-header h3 {
  margin: 0;
}

.question-content-text {
  margin-bottom: 20px;
  font-size: 16px;
  line-height: 1.6;
}

.question-options {
  margin-bottom: 20px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.option-letter {
  width: 30px;
  height: 30px;
  background: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 10px;
  font-weight: bold;
}

.option-item.selected {
  background: rgba(24, 144, 255, 0.1);
  border-color: #1890ff;
}

.option-item.correct {
  background: rgba(82, 196, 26, 0.1);
  border-color: #52c41a;
}

.option-item.incorrect {
  background: rgba(255, 77, 79, 0.1);
  border-color: #ff4d4f;
}

.option-item.selected .option-letter {
  background: #1890ff;
  color: #fff;
}

.option-item.correct .option-letter {
  background: #52c41a;
  color: #fff;
}

.option-item.incorrect .option-letter {
  background: #ff4d4f;
  color: #fff;
}

.essay-answer {
  margin-bottom: 20px;
}

.essay-answer h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.student-answer-box, .reference-answer-box {
  padding: 15px;
  background: #f9f9f9;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  white-space: pre-wrap;
  min-height: 100px;
}

.reference-answer-box {
  background: #f0f8ff;
}

.auto-graded {
  margin-top: 20px;
}

.score-display {
  margin-top: 10px;
  font-size: 16px;
  font-weight: bold;
}

.marking-area {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px dashed #e8e8e8;
}

.marking-area h4 {
  margin-top: 0;
  margin-bottom: 10px;
}

.score-input {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.score-label {
  margin-right: 10px;
}

.score-max {
  margin-left: 10px;
}

.teacher-comment {
  margin-bottom: 20px;
}

.save-marking {
  margin-top: 20px;
}

.no-question-selected, .no-paper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 400px;
}

.mt-4 {
  margin-top: 16px;
}
</style> 