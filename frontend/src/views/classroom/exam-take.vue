<template>
  <div class="exam-take-container">
    <!-- 考试头部 -->
    <div class="exam-header">
      <div class="exam-title">
        <h2>{{ examInfo?.title || '考试' }}</h2>
        <a-tag :color="getStatusColor(examInfo?.status)">
          {{ getStatusText(examInfo?.status) }}
        </a-tag>
      </div>
      <div class="exam-timer" v-if="remainingTime > 0">
        <clock-circle-outlined />
        <span>剩余时间：{{ formatTime(remainingTime) }}</span>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large" tip="正在加载试卷..." />
    </div>

    <!-- 已提交提示 -->
    <div v-else-if="examInfo?.student_submitted" class="submitted-container">
      <a-result
        status="success"
        title="您已完成本次考试"
        sub-title="试卷已提交，请等待教师批阅"
      >
        <template #extra>
          <a-button type="primary" @click="goBack">返回课堂</a-button>
        </template>
      </a-result>
    </div>

    <!-- 考试内容 -->
    <div v-else class="exam-content">
      <div class="questions-panel">
        <div 
          v-for="(question, index) in questions" 
          :key="question.id" 
          class="question-item"
          :id="`question-${index}`"
        >
          <div class="question-header">
            <span class="question-number">第 {{ index + 1 }} 题</span>
            <a-tag>{{ getQuestionTypeText(question.question_type) }}</a-tag>
            <span class="question-score">（{{ question.score }} 分）</span>
          </div>
          
          <div class="question-content">
            {{ question.content }}
          </div>

          <!-- 单选题 -->
          <div v-if="question.question_type === 'SINGLE_CHOICE'" class="question-options">
            <a-radio-group 
              v-model:value="answers[question.id]"
              @change="saveAnswerDebounced"
            >
              <a-radio 
                v-for="option in question.options" 
                :key="option.key" 
                :value="option.key"
                class="option-item"
              >
                {{ option.key }}. {{ option.content }}
              </a-radio>
            </a-radio-group>
          </div>

          <!-- 多选题 -->
          <div v-else-if="question.question_type === 'MULTIPLE_CHOICE'" class="question-options">
            <a-checkbox-group 
              v-model:value="answers[question.id]"
              @change="saveAnswerDebounced"
            >
              <a-checkbox 
                v-for="option in question.options" 
                :key="option.key" 
                :value="option.key"
                class="option-item"
              >
                {{ option.key }}. {{ option.content }}
              </a-checkbox>
            </a-checkbox-group>
          </div>

          <!-- 判断题 -->
          <div v-else-if="question.question_type === 'TRUE_FALSE'" class="question-options">
            <a-radio-group 
              v-model:value="answers[question.id]"
              @change="saveAnswerDebounced"
            >
              <a-radio value="true" class="option-item">正确</a-radio>
              <a-radio value="false" class="option-item">错误</a-radio>
            </a-radio-group>
          </div>

          <!-- 简答题 -->
          <div v-else-if="question.question_type === 'SHORT_ANSWER'" class="question-options">
            <a-textarea
              v-model:value="answers[question.id]"
              :rows="4"
              placeholder="请输入您的答案..."
              @change="saveAnswerDebounced"
            />
          </div>
        </div>
      </div>

      <!-- 答题卡 -->
      <div class="answer-card">
        <div class="card-title">答题卡</div>
        <div class="card-grid">
          <div 
            v-for="(question, index) in questions" 
            :key="question.id"
            :class="['card-item', { answered: isAnswered(question.id) }]"
            @click="scrollToQuestion(index)"
          >
            {{ index + 1 }}
          </div>
        </div>
        <div class="card-legend">
          <span class="legend-item"><span class="dot answered"></span> 已答</span>
          <span class="legend-item"><span class="dot"></span> 未答</span>
        </div>
        <div class="card-summary">
          已完成：{{ answeredCount }} / {{ questions.length }}
        </div>
        <a-button 
          type="primary" 
          block 
          size="large"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交试卷
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { ClockCircleOutlined } from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import request from '@/utils/request';
import { debounce } from 'lodash-es';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const classroomId = computed(() => route.params.classroomId as string);
const examId = computed(() => route.params.examId as string);

const loading = ref(true);
const submitting = ref(false);
const examInfo = ref<any>(null);
const questions = ref<any[]>([]);
const answers = ref<Record<string, any>>({});
const remainingTime = ref(0);
let timer: NodeJS.Timeout | null = null;

// 获取考试信息和试题
const fetchExamData = async () => {
  loading.value = true;
  try {
    // 获取考试信息
    const examRes = await request.get(`/api/v1/classroom-exams/${examId.value}`, {
      params: { student_id: userStore.userId }
    });
    
    if (examRes.code === '0000' && examRes.data) {
      examInfo.value = examRes.data;
      
      // 如果已提交，不需要加载试题
      if (examRes.data.student_submitted) {
        loading.value = false;
        return;
      }
      
      // 计算剩余时间
      const endTime = new Date(examInfo.value.exam_end_time).getTime();
      const now = Date.now();
      const durationMs = (examInfo.value.duration_minutes || 60) * 60 * 1000;
      remainingTime.value = Math.min(
        Math.floor((endTime - now) / 1000),
        examInfo.value.duration_minutes * 60
      );
      
      // 开始倒计时
      startTimer();
    }
    
    // 获取试题
    const questionsRes = await request.get(`/api/v1/classroom-exams/${examId.value}/questions`, {
      params: { student_id: userStore.userId }
    });
    
    if (questionsRes.code === '0000' && questionsRes.data) {
      questions.value = questionsRes.data.questions || questionsRes.data || [];
      
      // 初始化答案对象
      questions.value.forEach((q: any) => {
        if (q.question_type === 'MULTIPLE_CHOICE') {
          answers.value[q.id] = [];
        } else {
          answers.value[q.id] = '';
        }
      });
      
      // 恢复已保存的答案
      if (questionsRes.data.saved_answers) {
        Object.assign(answers.value, questionsRes.data.saved_answers);
      }
    }
  } catch (error) {
    console.error('加载考试数据失败:', error);
    message.error('加载考试数据失败');
  } finally {
    loading.value = false;
  }
};

// 开始倒计时
const startTimer = () => {
  timer = setInterval(() => {
    if (remainingTime.value > 0) {
      remainingTime.value--;
    } else {
      // 时间到，自动提交
      if (timer) clearInterval(timer);
      handleAutoSubmit();
    }
  }, 1000);
};

// 格式化时间
const formatTime = (seconds: number) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m}:${s.toString().padStart(2, '0')}`;
};

// 检查是否已答
const isAnswered = (questionId: string) => {
  const answer = answers.value[questionId];
  if (Array.isArray(answer)) {
    return answer.length > 0;
  }
  return !!answer;
};

// 已答题目数
const answeredCount = computed(() => {
  return questions.value.filter(q => isAnswered(q.id)).length;
});

// 保存答案（防抖）
const saveAnswerDebounced = debounce(async () => {
  try {
    await request.post(`/api/v1/classroom-exams/${examId.value}/save-answers`, {
      student_id: userStore.userId,
      answers: answers.value
    });
  } catch (error) {
    console.error('保存答案失败:', error);
  }
}, 1000);

// 提交试卷
const handleSubmit = () => {
  const unansweredCount = questions.value.length - answeredCount.value;
  
  Modal.confirm({
    title: '确认提交',
    content: unansweredCount > 0 
      ? `您还有 ${unansweredCount} 道题未作答，确定要提交吗？`
      : '确定要提交试卷吗？提交后将无法修改。',
    okText: '确认提交',
    cancelText: '继续答题',
    onOk: submitExam
  });
};

// 自动提交（超时）
const handleAutoSubmit = () => {
  message.warning('考试时间到，正在自动提交试卷...');
  submitExam();
};

// 执行提交
const submitExam = async () => {
  submitting.value = true;
  try {
    const res = await request.post(`/api/v1/classroom-exams/${examId.value}/submit`, {
      student_id: userStore.userId,
      answers: answers.value
    });
    
    if (res.code === '0000') {
      message.success('试卷提交成功！');
      // 刷新考试状态
      await fetchExamData();
    } else {
      message.error(res.message || '提交失败');
    }
  } catch (error) {
    console.error('提交试卷失败:', error);
    message.error('提交试卷失败，请重试');
  } finally {
    submitting.value = false;
  }
};

// 滚动到指定题目
const scrollToQuestion = (index: number) => {
  const el = document.getElementById(`question-${index}`);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
};

// 返回课堂
const goBack = () => {
  router.push(`/classroom/${classroomId.value}`);
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'ONGOING': 'green',
    'SCHEDULED': 'blue',
    'COMPLETED': 'default'
  };
  return colors[status] || 'default';
};

// 获取状态文字
const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    'ONGOING': '进行中',
    'SCHEDULED': '未开始',
    'COMPLETED': '已结束'
  };
  return texts[status] || status;
};

// 获取题型文字
const getQuestionTypeText = (type: string) => {
  const types: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题',
    'FILL_BLANK': '填空题'
  };
  return types[type] || type;
};

onMounted(() => {
  fetchExamData();
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<style scoped lang="less">
.exam-take-container {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #fff;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  
  .exam-title {
    display: flex;
    align-items: center;
    gap: 12px;
    
    h2 {
      margin: 0;
    }
  }
  
  .exam-timer {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 18px;
    font-weight: 600;
    color: #ff4d4f;
  }
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.submitted-container {
  background: #fff;
  border-radius: 8px;
  padding: 48px;
}

.exam-content {
  display: flex;
  gap: 24px;
  
  .questions-panel {
    flex: 1;
    background: #fff;
    border-radius: 8px;
    padding: 24px;
    
    .question-item {
      padding: 24px 0;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }
      
      .question-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        
        .question-number {
          font-weight: 600;
          font-size: 16px;
        }
        
        .question-score {
          color: #666;
        }
      }
      
      .question-content {
        font-size: 15px;
        line-height: 1.8;
        margin-bottom: 16px;
      }
      
      .question-options {
        .option-item {
          display: block;
          padding: 8px 0;
        }
      }
    }
  }
  
  .answer-card {
    width: 280px;
    background: #fff;
    border-radius: 8px;
    padding: 20px;
    position: sticky;
    top: 24px;
    height: fit-content;
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
      text-align: center;
    }
    
    .card-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 8px;
      margin-bottom: 16px;
      
      .card-item {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid #d9d9d9;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
        transition: all 0.2s;
        
        &:hover {
          border-color: #1890ff;
          color: #1890ff;
        }
        
        &.answered {
          background: #1890ff;
          border-color: #1890ff;
          color: #fff;
        }
      }
    }
    
    .card-legend {
      display: flex;
      justify-content: center;
      gap: 16px;
      margin-bottom: 12px;
      font-size: 12px;
      color: #666;
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: 4px;
        
        .dot {
          width: 12px;
          height: 12px;
          border-radius: 2px;
          border: 1px solid #d9d9d9;
          
          &.answered {
            background: #1890ff;
            border-color: #1890ff;
          }
        }
      }
    }
    
    .card-summary {
      text-align: center;
      margin-bottom: 16px;
      color: #666;
    }
  }
}
</style>



