<template>
  <PageShell max-width="wide" class="exam-result-container">
    <PageHeaderBar
      :title="examInfo?.title || '考试成绩'"
      show-back
      :back-to="`/classroom/${classroomId}`"
    />

    <!-- 加载中 -->
    <a-spin :spinning="loading">
      <!-- 无成绩 -->
      <EmptyStateBlock
        v-if="!loading && !resultData"
        description="暂无考试成绩"
      />

      <!-- 成绩详情 -->
      <div v-else-if="resultData" class="result-content">
        <!-- 成绩卡片 -->
        <div class="score-card">
          <div class="score-main">
            <div class="score-circle" :class="isPassed ? 'passed' : 'failed'">
              <div class="score-value">{{ resultData.score ?? 0 }}</div>
              <div class="score-total">/ {{ resultData.total_score || 30 }} 分</div>
            </div>
          </div>
          <div class="score-info">
            <a-row :gutter="24">
              <a-col :span="8">
                <a-statistic 
                  title="考试状态" 
                  :value="resultData.is_graded ? '已评阅' : '待评阅'"
                >
                  <template #suffix>
                    <check-circle-outlined v-if="resultData.is_graded" style="color: #52c41a" />
                    <clock-circle-outlined v-else style="color: #faad14" />
                  </template>
                </a-statistic>
              </a-col>
              <a-col :span="8">
                <a-statistic 
                  title="是否及格" 
                  :value="isPassed ? '及格' : '不及格'"
                  :value-style="{ color: isPassed ? '#52c41a' : '#ff4d4f' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic 
                  title="提交时间" 
                  :value="formatDateTime(resultData.submit_time)"
                />
              </a-col>
            </a-row>
          </div>
        </div>

        <!-- 答题详情 -->
        <div class="answer-details">
          <h3>
            <file-text-outlined /> 答题详情
          </h3>
          
          <div class="questions-list">
            <div 
              v-for="(question, index) in resultData.questions" 
              :key="question.id"
              class="question-item"
              :class="{ 'correct': question.is_correct, 'incorrect': question.is_correct === false }"
            >
              <div class="question-header">
                <span class="question-number">第 {{ index + 1 }} 题</span>
                <a-tag>{{ getQuestionTypeText(question.question_type) }}</a-tag>
                <span class="question-score">
                  得分：
                  <span :class="question.is_correct ? 'score-correct' : 'score-incorrect'">
                    {{ question.score_awarded ?? 0 }} / {{ question.max_score }} 分
                  </span>
                </span>
                <a-tag v-if="question.is_correct" color="success">
                  <check-outlined /> 正确
                </a-tag>
                <a-tag v-else-if="question.is_correct === false" color="error">
                  <close-outlined /> 错误
                </a-tag>
              </div>
              
              <div class="question-content">
                {{ question.content }}
              </div>

              <!-- 选择题选项 -->
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

              <!-- 判断题答案 -->
              <div class="answer-compare" v-if="question.question_type === 'TRUE_FALSE'">
                <div class="answer-row">
                  <span class="label">你的答案：</span>
                  <span :class="question.is_correct ? 'answer-correct' : 'answer-incorrect'">
                    {{ question.student_answer === 'true' ? '正确' : '错误' }}
                  </span>
                </div>
                <div class="answer-row">
                  <span class="label">正确答案：</span>
                  <span class="answer-correct">
                    {{ question.correct_answer?.includes('true') ? '正确' : '错误' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-spin>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  CheckOutlined,
  CloseOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
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
const resultData = ref<any>(null);

// 获取当前用户ID
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

// 是否及格
const isPassed = computed(() => {
  if (!resultData.value || !examInfo.value) return false;
  const passMark = examInfo.value.pass_mark || 60;
  return (resultData.value.score || 0) >= passMark;
});

// 获取考试信息和学生成绩
const fetchData = async () => {
  loading.value = true;
  const userId = getCurrentUserId();
  console.log('[exam-my-result] fetchData开始, userId:', userId, 'examId:', examId.value);
  
  if (!userId) {
    console.error('[exam-my-result] 无法获取用户ID');
    message.error('请先登录');
    loading.value = false;
    return;
  }
  
  try {
    // 获取考试信息
    const examRes = await request.get(`/api/v1/classroom-exams/${examId.value}`, {
      params: { student_id: userId }
    });
    console.log('[exam-my-result] 考试信息响应:', examRes);
    if (examRes.code === '0000') {
      examInfo.value = examRes.data;
    }

    // 获取学生成绩详情
    const resultRes = await request.get(`/api/v1/classroom-exams/${examId.value}/my-result`, {
      params: { student_id: userId }
    });
    console.log('[exam-my-result] 成绩详情响应:', resultRes);
    if (resultRes && resultRes.code === '0000') {
      resultData.value = resultRes.data;
    }
  } catch (error) {
    console.error('[exam-my-result] 加载数据失败:', error);
    message.error('加载成绩失败');
  } finally {
    loading.value = false;
  }
};

// 返回
const goBack = () => {
  router.push(`/classroom/${classroomId.value}`);
};

// 格式化时间
const formatDateTime = (time: string) => {
  if (!time) return '-';
  return dayjs(time).format('YYYY/MM/DD HH:mm');
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

// 判断是否为正确选项
const isCorrectOption = (question: any, key: string) => {
  const correctAnswers = question.correct_answer || [];
  return correctAnswers.includes(key);
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
.exam-result-container {
  /* PageShell handles outer padding */
}

.result-content {
  .score-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 24px;
    color: #fff;

    .score-main {
      display: flex;
      justify-content: center;
      margin-bottom: 24px;

      .score-circle {
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 4px solid rgba(255, 255, 255, 0.5);

        &.passed {
          background: rgba(82, 196, 26, 0.3);
          border-color: #52c41a;
        }

        &.failed {
          background: rgba(255, 77, 79, 0.3);
          border-color: #ff4d4f;
        }

        .score-value {
          font-size: 48px;
          font-weight: 700;
          line-height: 1;
        }

        .score-total {
          font-size: 16px;
          opacity: 0.9;
        }
      }
    }

    .score-info {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 12px;
      padding: 16px 24px;

      :deep(.ant-statistic-title) {
        color: rgba(255, 255, 255, 0.85);
      }

      :deep(.ant-statistic-content) {
        color: #fff;
      }
    }
  }

  .answer-details {
    background: #fff;
    border-radius: 12px;
    padding: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    h3 {
      margin-bottom: 20px;
      font-size: 18px;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .questions-list {
      .question-item {
        padding: 20px;
        margin-bottom: 16px;
        background: #fafafa;
        border-radius: 8px;
        border-left: 4px solid #d9d9d9;

        &.correct {
          border-left-color: #52c41a;
          background: #f6ffed;
        }

        &.incorrect {
          border-left-color: #ff4d4f;
          background: #fff2f0;
        }

        .question-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
          flex-wrap: wrap;

          .question-number {
            font-weight: 600;
            font-size: 15px;
          }

          .question-score {
            margin-left: auto;
            
            .score-correct {
              color: #52c41a;
              font-weight: 600;
            }

            .score-incorrect {
              color: #ff4d4f;
              font-weight: 600;
            }
          }
        }

        .question-content {
          font-size: 15px;
          margin-bottom: 12px;
          line-height: 1.6;
          color: #333;
        }

        .question-options {
          .option {
            padding: 10px 14px;
            margin: 6px 0;
            border-radius: 6px;
            background: #fff;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;

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
              font-size: 16px;
            }

            .wrong-icon {
              color: #ff4d4f;
              margin-left: auto;
              font-size: 16px;
            }
          }
        }

        .answer-compare {
          padding: 14px;
          background: #fff;
          border-radius: 6px;
          margin-top: 8px;

          .answer-row {
            margin: 6px 0;
            font-size: 14px;

            .label {
              color: #666;
              margin-right: 8px;
            }

            .answer-correct {
              color: #52c41a;
              font-weight: 500;
            }

            .answer-incorrect {
              color: #ff4d4f;
              font-weight: 500;
            }
          }
        }
      }
    }
  }
}
</style>



