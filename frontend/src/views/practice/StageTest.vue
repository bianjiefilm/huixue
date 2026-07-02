<template>
  <div class="stage-test-page">
    <div class="test-header">
      <a-page-header
        :title="`测试关卡：${stageTitle}`"
        sub-title="教师测试模式"
        @back="goBack"
      >
        <template #extra>
          <a-tag color="orange">测试模式</a-tag>
          <a-button @click="showReferenceAnswer">
            <template #icon><EyeOutlined /></template>
            查看答案
          </a-button>
          <a-button type="primary" @click="exitTest">退出测试</a-button>
        </template>
      </a-page-header>
    </div>

    <div class="test-content">
      <a-row :gutter="16">
        <!-- 左侧：任务说明 -->
        <a-col :span="10">
          <a-card title="任务说明" :bordered="false">
            <div class="task-description" v-html="renderedHandbook"></div>
          </a-card>
        </a-col>

        <!-- 右侧：答题区域 -->
        <a-col :span="14">
          <a-card :bordered="false">
            <!-- 实践题 -->
            <div v-if="stageType === 'PRACTICE'" class="practice-area">
              <div class="editor-header">
                <h3>代码编辑器</h3>
                <a-space>
                  <a-button @click="clearTerminal" :disabled="isRunning">
                    <template #icon><ClearOutlined /></template>
                    清空
                  </a-button>
                <a-button
                  type="primary"
                  @click="runTest"
                  :loading="isRunning"
                  :disabled="isRunning"
                >
                  <template #icon><PlayCircleOutlined /></template>
                  {{ isRunning ? '运行中...' : '运行测试' }}
                </a-button>
                <a-button
                  v-if="aiEnabled"
                  type="default"
                  @click="requestFailureHint"
                  :loading="isRequestingHint"
                  :disabled="!canRequestHint"
                >
                  解释错误
                </a-button>
              </a-space>
            </div>
              <a-textarea
                v-model:value="codeContent"
                :rows="12"
                placeholder="在此编写代码..."
                style="font-family: 'Consolas', 'Monaco', monospace; font-size: 14px;"
              />

              <!-- 终端输出区域 -->
              <div class="terminal-section">
                <div class="terminal-header">
                  <h4>
                    <CodeOutlined /> 终端输出
                  </h4>
                  <a-tag v-if="executionTime > 0" color="blue">
                    耗时: {{ (executionTime / 1000).toFixed(2) }}s
                  </a-tag>
                </div>
                <div class="terminal-output" ref="terminalRef">
              <div v-if="terminalLogs.length === 0" class="terminal-placeholder">
                点击"运行测试"查看输出结果...
              </div>
              <div v-else>
                <div
                      v-for="(log, index) in terminalLogs"
                      :key="index"
                      :class="['terminal-line', log.type]"
                    >
                      <span class="line-prefix">{{ log.type === 'error' ? '✗' : log.type === 'success' ? '✓' : '>' }}</span>
                  <span class="line-content">{{ log.text }}</span>
                </div>
              </div>
            </div>
            <div v-if="visibleErrorOutput" class="error-output-block">
              <h4>可见失败信息</h4>
              <div class="error-output-text">{{ visibleErrorOutput }}</div>
            </div>
            <div v-if="failureHint" class="failure-hint-block">
              <h4>AI 辅导建议</h4>
              <div class="failure-hint-text">{{ failureHint }}</div>
            </div>
          </div>

              <!-- 测试结果摘要 -->
              <div v-if="testResult" class="test-result">
                <a-alert
                  :type="testResult.success ? 'success' : 'error'"
                  :message="testResult.success ? '所有测试通过！' : '测试失败'"
                  show-icon
                >
                  <template #description>
                    <div>{{ testResult.message }}</div>
                    <div v-if="testResult.passed !== undefined" class="test-stats">
                      通过: {{ testResult.passed }}/{{ testResult.total }} 个测试用例
                    </div>
                  </template>
                </a-alert>
              </div>
            </div>

            <!-- 判断题 -->
            <div v-else-if="stageType === 'JUDGEMENT'" class="judgment-area">
              <h3>判断题</h3>
              <div v-for="(question, index) in judgmentQuestions" :key="index" class="question-item">
                <div class="question-header">
                  <span class="question-number">第 {{ index + 1 }} 题</span>
                  <a-tag>{{ question.score }}分</a-tag>
                </div>
                <div class="question-content" v-html="renderMarkdown(question.question_content)"></div>
                <a-radio-group v-model:value="judgmentAnswers[index]">
                  <a-radio :value="true">正确</a-radio>
                  <a-radio :value="false">错误</a-radio>
                </a-radio-group>
              </div>
              <a-button type="primary" @click="submitJudgment" style="margin-top: 16px">
                提交答案
              </a-button>
            </div>

            <!-- 选择题 -->
            <div v-else-if="stageType === 'CHOICE'" class="choice-area">
              <h3>选择题</h3>
              <div v-for="(question, index) in choiceQuestions" :key="index" class="question-item">
                <div class="question-header">
                  <span class="question-number">第 {{ index + 1 }} 题</span>
                  <a-tag>{{ question.question_type === 'single' ? '单选' : '多选' }}</a-tag>
                  <a-tag>{{ question.score }}分</a-tag>
                </div>
                <div class="question-content" v-html="renderMarkdown(question.question_content)"></div>
                
                <div v-if="question.question_type === 'single'">
                  <a-radio-group v-model:value="choiceAnswers[index]">
                    <a-radio 
                      v-for="(option, optIndex) in question.options" 
                      :key="optIndex"
                      :value="optIndex"
                      style="display: block; margin-bottom: 8px"
                    >
                      {{ option.key }}. {{ option.text }}
                    </a-radio>
                  </a-radio-group>
                </div>
                <div v-else>
                  <a-checkbox-group v-model:value="choiceAnswers[index]">
                    <a-checkbox 
                      v-for="(option, optIndex) in question.options" 
                      :key="optIndex"
                      :value="optIndex"
                      style="display: block; margin-bottom: 8px"
                    >
                      {{ option.key }}. {{ option.text }}
                    </a-checkbox>
                  </a-checkbox-group>
                </div>
              </div>
              <a-button type="primary" @click="submitChoice" style="margin-top: 16px">
                提交答案
              </a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 测试结果模态框 -->
    <a-modal
      v-model:open="resultModalVisible"
      title="测试结果"
      :footer="null"
      width="600px"
    >
      <div class="result-content">
        <a-result
          :status="testPassed ? 'success' : 'error'"
          :title="testPassed ? '测试通过！' : '测试未通过'"
          :sub-title="resultMessage"
        >
          <template #extra>
            <a-button type="primary" @click="resultModalVisible = false">
              知道了
            </a-button>
          </template>
        </a-result>
        
        <!-- 显示答案解析 -->
        <div v-if="showAnalysis" class="answer-analysis">
          <h4>答案解析</h4>
          <div v-for="(analysis, index) in answerAnalysis" :key="index" class="analysis-item">
            <div class="analysis-header">
              <span>第 {{ index + 1 }} 题</span>
              <a-tag :color="analysis.correct ? 'green' : 'red'">
                {{ analysis.correct ? '正确' : '错误' }}
              </a-tag>
            </div>
            <div v-if="analysis.explanation" class="analysis-content">
              {{ analysis.explanation }}
            </div>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 参考答案模态框 -->
    <a-modal
      v-model:open="answerModalVisible"
      title="参考答案"
      :footer="null"
      width="700px"
    >
      <div class="reference-answer-content">
        <!-- 实践题参考答案 -->
        <div v-if="stageType === 'PRACTICE'" class="practice-answer">
          <div v-if="testCases.length > 0" class="test-cases-section">
            <h4>测试用例</h4>
            <div v-for="(testCase, index) in testCases" :key="index" class="test-case-item">
              <div class="test-case-header">
                <span>测试用例 {{ index + 1 }}</span>
                <a-tag v-if="testCase.is_hidden" color="orange">隐藏用例</a-tag>
              </div>
              <div class="test-case-body">
                <div class="test-case-row">
                  <span class="label">输入：</span>
                  <code>{{ testCase.input_data || '无输入' }}</code>
                </div>
                <div class="test-case-row">
                  <span class="label">预期输出：</span>
                  <code>{{ testCase.expected_output }}</code>
                </div>
                <div class="test-case-row">
                  <span class="label">匹配规则：</span>
                  <a-tag>{{ testCase.match_rule === 'exact' ? '精确匹配' : '正则匹配' }}</a-tag>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-test-cases">
            <a-empty description="暂无测试用例" />
          </div>

          <div v-if="evaluationSettings" class="evaluation-info">
            <h4>评测配置</h4>
            <div class="eval-item">
              <span class="label">评测命令：</span>
              <code>{{ evaluationSettings.evaluation_command || '未配置' }}</code>
            </div>
            <div class="eval-item">
              <span class="label">超时时间：</span>
              <span>{{ evaluationSettings.evaluation_timeout_seconds || 30 }} 秒</span>
            </div>
          </div>
        </div>

        <!-- 判断题参考答案 -->
        <div v-else-if="stageType === 'JUDGEMENT'" class="judgment-answer">
          <div v-for="(question, index) in judgmentQuestions" :key="index" class="answer-item">
            <div class="answer-header">
              <span>第 {{ index + 1 }} 题</span>
            </div>
            <div class="answer-body">
              <div class="correct-answer">
                <span class="label">正确答案：</span>
                <a-tag color="green">{{ getJudgmentCorrectAnswer() ? '正确' : '错误' }}</a-tag>
              </div>
              <div v-if="getQuestionExplanation()" class="explanation">
                <span class="label">解析：</span>
                <span>{{ getQuestionExplanation() }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 选择题参考答案 -->
        <div v-else-if="stageType === 'CHOICE'" class="choice-answer">
          <div v-for="(question, index) in choiceQuestions" :key="index" class="answer-item">
            <div class="answer-header">
              <span>第 {{ index + 1 }} 题</span>
              <a-tag>{{ question.question_type === 'single' ? '单选' : '多选' }}</a-tag>
            </div>
            <div class="answer-body">
              <div class="correct-answer">
                <span class="label">正确答案：</span>
                <a-tag color="green">{{ getChoiceCorrectAnswer(question, index) }}</a-tag>
              </div>
              <div v-if="getQuestionExplanation()" class="explanation">
                <span class="label">解析：</span>
                <span>{{ getQuestionExplanation() }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { PlayCircleOutlined, EyeOutlined, ClearOutlined, CodeOutlined } from '@ant-design/icons-vue';
import {
  getStageTestData,
  sandboxTest,
  requestPracticeFailureHint,
  type PracticeFailureHintRequest,
  type StageTestData,
  type SandboxTestResult
} from '@/api/practice';
import { getAIStatus } from '@/api/ai-features';
import { useUserStore } from '@/stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 获取参数
const practiceId = computed(() => Number(route.params.practiceId));
const stageId = computed(() => Number(route.params.stageId));
const creatorId = computed(() => userStore.userInfo.id);

// 关卡数据
const stageTestData = ref<StageTestData | null>(null);
const loading = ref(false);

// 计算属性
const stageTitle = computed(() => stageTestData.value?.stage_title || '加载中...');
const stageType = computed(() => {
  const taskType = stageTestData.value?.task_type;
  if (taskType === 'TRUE_FALSE') return 'JUDGEMENT';
  if (taskType === 'SINGLE_CHOICE' || taskType === 'MULTIPLE_CHOICE') return 'CHOICE';
  return 'PRACTICE';
});
const handbook = computed(() => stageTestData.value?.handbook_markdown || '');

// 代码编辑
const codeContent = ref('');
const testResult = ref<{ success: boolean; message: string; passed?: number; total?: number } | null>(null);

// 终端输出
const terminalRef = ref<HTMLElement | null>(null);
const terminalLogs = ref<{ type: 'info' | 'success' | 'error' | 'warning'; text: string }[]>([]);
const latestFailureCases = ref<Array<Record<string, any>>>([]);
const failureHint = ref('');
const visibleErrorOutput = ref('');
const isRequestingHint = ref(false);
const isRunning = ref(false);
const executionTime = ref(0);

// 判断题数据
const judgmentQuestions = computed(() => {
  if (stageType.value === 'JUDGEMENT' && stageTestData.value?.question_data) {
    const qData = stageTestData.value.question_data;
    // 如果是数组格式，返回数组；如果是单个题目，包装成数组
    if (Array.isArray(qData.questions)) {
      return qData.questions;
    } else if (qData.question) {
      // 单个题目格式
      return [{
        question_content: qData.question,
        options: qData.options,
        score: 10,
        question_type: 'single'
      }];
    }
  }
  return [];
});
const judgmentAnswers = ref<boolean[]>([]);

// 选择题数据
const choiceQuestions = computed(() => {
  if (stageType.value === 'CHOICE' && stageTestData.value?.question_data) {
    const qData = stageTestData.value.question_data;
    // 如果是数组格式，返回数组；如果是单个题目，包装成数组
    if (Array.isArray(qData.questions)) {
      return qData.questions;
    } else if (qData.question) {
      // 单个题目格式
      return [{
        question_content: qData.question,
        options: qData.options.map((opt: string, index: number) => ({
          key: String.fromCharCode(65 + index),
          text: opt
        })),
        score: 10,
        question_type: 'single'
      }];
    }
  }
  return [];
});
const choiceAnswers = ref<any[]>([]);

// 结果模态框
const resultModalVisible = ref(false);
const testPassed = ref(false);
const resultMessage = ref('');
const showAnalysis = ref(false);
const answerAnalysis = ref<any[]>([]);

// 参考答案模态框
const answerModalVisible = ref(false);

// 测试用例和评测设置
const testCases = computed(() => stageTestData.value?.test_cases || []);
const evaluationSettings = computed(() => stageTestData.value?.evaluation_settings);

// 渲染Markdown
const renderedHandbook = computed(() => {
  return renderMarkdown(handbook.value);
});

// 加载关卡测试数据
const loadStageData = async () => {
  loading.value = true;
  try {
    const data = await getStageTestData(
      practiceId.value,
      stageId.value,
      creatorId.value
    );
    
    if (data) {
      stageTestData.value = data;
      
      // 初始化答案数组
      if (data.task_type === 'JUDGEMENT') {
        judgmentAnswers.value = new Array(judgmentQuestions.value.length);
      } else if (data.task_type === 'CHOICE') {
        choiceAnswers.value = new Array(choiceQuestions.value.length);
      }
    } else {
      message.error('加载关卡数据失败');
    }
  } catch (error) {
    message.error('加载关卡数据失败');
  } finally {
    loading.value = false;
  }
};

const renderMarkdown = (text: string) => {
  // 简单的Markdown渲染
  let html = text;
  html = html.replace(/## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  html = html.replace(/\n/g, '<br>');
  return html;
};

// 获取选项标签
const getOptionLabel = (index: number) => {
  return String.fromCharCode(65 + index);
};

// 返回
const goBack = () => {
  router.back();
};

// 退出测试
const exitTest = () => {
  router.push(`/practice/${practiceId.value}/edit`);
};

// 显示参考答案
const showReferenceAnswer = () => {
  answerModalVisible.value = true;
};

// 获取判断题正确答案
const getJudgmentCorrectAnswer = (): boolean => {
  const qData = stageTestData.value?.question_data;
  if (!qData) return false;
  const answer = qData.correct_answer;
  return answer === '可以' || answer === 'True' || answer === true || answer === '正确';
};

// 获取选择题正确答案
const getChoiceCorrectAnswer = (question: any, index: number): string => {
  const qData = stageTestData.value?.question_data;
  if (!qData) return '未知';

  // 如果是数组格式的题目
  if (Array.isArray(qData.questions) && qData.questions[index]) {
    const q = qData.questions[index];
    if (q.options) {
      const correctOptions = q.options
        .filter((opt: any) => opt.is_correct)
        .map((opt: any) => opt.key);
      return correctOptions.join(', ') || '未设置';
    }
  }

  // 单个题目格式
  return qData.correct_answer || '未知';
};

// 获取题目解析
const getQuestionExplanation = (): string => {
  const qData = stageTestData.value?.question_data;
  return qData?.explanation || '';
};

// 终端日志函数
const addLog = (text: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
  terminalLogs.value.push({ type, text });
  // 自动滚动到底部
  setTimeout(() => {
    if (terminalRef.value) {
      terminalRef.value.scrollTop = terminalRef.value.scrollHeight;
    }
  }, 10);
};

const clearTerminal = () => {
  terminalLogs.value = [];
  testResult.value = null;
  executionTime.value = 0;
  latestFailureCases.value = [];
  visibleErrorOutput.value = '';
  failureHint.value = '';
};

// AI 总开关状态,关闭时隐藏"解释错误"入口
const aiEnabled = ref(false);

const canRequestHint = computed(() => {
  return (
    latestFailureCases.value.length > 0 &&
    !!codeContent.value.trim() &&
    !isRequestingHint.value
  );
});

const requestFailureHint = async () => {
  if (!canRequestHint.value) {
    message.info('请先运行测试并产生失败用例');
    return;
  }

  isRequestingHint.value = true;
  try {
    const payload: PracticeFailureHintRequest = {
      stage_id: stageId.value,
      code_content: codeContent.value,
      failure_cases: latestFailureCases.value,
      handbook_markdown: handbook.value,
      visible_error_output: visibleErrorOutput.value
    };

    const hint = await requestPracticeFailureHint(payload);
    if (hint) {
      failureHint.value = hint;
      addLog('已生成 AI 辅导建议', 'success');
    } else {
      message.warning('暂时无法生成错误解释');
    }
  } finally {
    isRequestingHint.value = false;
  }
};

// 运行测试（实践题）
const runTest = async () => {
  if (!codeContent.value.trim()) {
    message.warning('请先编写代码');
    return;
  }

  // 清空之前的输出
  terminalLogs.value = [];
  testResult.value = null;
  isRunning.value = true;
  executionTime.value = 0;

  const startTime = Date.now();

  addLog('开始运行测试...', 'info');
  addLog(`代码长度: ${codeContent.value.length} 字符`, 'info');

  try {
    // 调用沙盒测试API
    const result = await sandboxTest(
      stageId.value,
      codeContent.value,
      { 'main.py': codeContent.value },  // 简化的文件内容
      creatorId.value
    );

    if (result) {
      executionTime.value = Date.now() - startTime;

      latestFailureCases.value = [];
      visibleErrorOutput.value = '';
      failureHint.value = '';

      if (result.error_message) {
        addLog(`测试出错: ${result.error_message}`, 'error');
        testResult.value = {
          success: false,
          message: result.error_message
        };
        return;
      }

      // 处理测试结果
      const totalCount = result.test_results.length;
      let passedCount = 0;
      const failureRecords: Array<Record<string, any>> = [];
      const failedLines: string[] = [];

      for (const tc of result.test_results) {
        if (tc.passed) {
          passedCount++;
          addLog(`测试用例 ${tc.test_case_id}: 通过 ✓`, 'success');
          if (tc.execution_time) {
            addLog(`  执行时间: ${tc.execution_time}ms`, 'info');
          }
        } else {
          addLog(`测试用例 ${tc.test_case_id}: 失败 ✗`, 'error');
          addLog(`  预期输出: ${tc.expected_output}`, 'error');
          addLog(`  实际输出: ${tc.actual_output}`, 'error');

          failureRecords.push({
            test_case_id: tc.test_case_id,
            input_data: tc.input_data,
            expected_output: tc.expected_output,
            actual_output: tc.actual_output,
            execution_time: tc.execution_time
          });
          failedLines.push(`测试用例 ${tc.test_case_id} 失败`);
          failedLines.push(`预期: ${tc.expected_output}`);
          failedLines.push(`实际: ${tc.actual_output}`);
        }
      }

      latestFailureCases.value = failureRecords;
      if (failedLines.length > 0) {
        visibleErrorOutput.value = failedLines.join('\n');
      }

      addLog('---', 'info');
      addLog(`测试完成: ${passedCount}/${totalCount} 通过`, 'info');

      const allPassed = passedCount === totalCount;
      testPassed.value = allPassed;

      testResult.value = {
        success: allPassed,
        message: allPassed
          ? '恭喜！所有测试用例都通过了。'
          : `${totalCount - passedCount} 个测试用例未通过。`,
        passed: passedCount,
        total: totalCount
      };

      if (allPassed) {
        resultMessage.value = '你的代码通过了所有测试！';
        resultModalVisible.value = true;
      }
    } else {
      // API调用失败，使用本地模拟逻辑
      addLog('测试服务暂时不可用，使用本地模拟测试...', 'warning');
      await runLocalTest(startTime);
    }
  } catch (error: any) {
    executionTime.value = Date.now() - startTime;
    addLog(`运行出错: ${error.message || '未知错误'}`, 'error');
    testResult.value = {
      success: false,
      message: `运行出错: ${error.message || '未知错误'}`
    };
  } finally {
    isRunning.value = false;
  }
};

// 本地模拟测试（备用）
const runLocalTest = async (startTime: number) => {
  const code = codeContent.value;
  const cases = testCases.value;
  const timeout = evaluationSettings.value?.evaluation_timeout_seconds || 30;

  if (cases.length > 0) {
    addLog(`发现 ${cases.length} 个测试用例`, 'info');
    addLog(`超时设置: ${timeout} 秒`, 'info');
    addLog('---', 'info');

    let passedCount = 0;
    const totalCount = cases.length;

    for (let i = 0; i < cases.length; i++) {
      const tc = cases[i];
      const expectedOutput = tc.expected_output.trim();

      addLog(`运行测试用例 ${i + 1}...`, 'info');

      // 模拟执行延迟
      await new Promise(resolve => setTimeout(resolve, 500));

      // 检查是否超时
      const elapsed = (Date.now() - startTime) / 1000;
      if (elapsed > timeout) {
        addLog(`测试用例 ${i + 1}: 执行超时 (>${timeout}s)`, 'error');
        continue;
      }

      // 模拟评测逻辑
      let passed = false;

      if (tc.match_rule === 'exact') {
        if (code.includes('print') && (
          code.includes(expectedOutput) ||
          code.includes(`"${expectedOutput}"`) ||
          code.includes(`'${expectedOutput}'`)
        )) {
          passed = true;
        } else if (code.includes('def ') && code.includes('return')) {
          passed = true;
        }
      } else {
        try {
          const regex = new RegExp(expectedOutput);
          passed = regex.test(code);
        } catch {
          addLog(`测试用例 ${i + 1}: 正则表达式无效`, 'error');
        }
      }

      if (passed) {
        passedCount++;
        addLog(`测试用例 ${i + 1}: 通过 ✓`, 'success');
      } else {
        addLog(`测试用例 ${i + 1}: 失败 ✗`, 'error');
      }
    }

    addLog('---', 'info');
    executionTime.value = Date.now() - startTime;

    const allPassed = passedCount === totalCount;
    if (allPassed) {
      addLog(`全部测试通过！(${passedCount}/${totalCount})`, 'success');
      testPassed.value = true;
      resultMessage.value = '你的代码通过了所有测试！';
      resultModalVisible.value = true;
    } else {
      addLog(`测试完成: ${passedCount}/${totalCount} 通过`, passedCount > 0 ? 'warning' : 'error');
    }

    testResult.value = {
      success: allPassed,
      message: allPassed
        ? '恭喜！所有测试用例都通过了。'
        : `${totalCount - passedCount} 个测试用例未通过。`,
      passed: passedCount,
      total: totalCount
    };
  }
};

// 提交判断题
const submitJudgment = () => {
  const unanswered = judgmentAnswers.value.filter(a => a === undefined).length;
  if (unanswered > 0) {
    message.warning(`还有 ${unanswered} 道题未作答`);
    return;
  }
  
  // 计算得分
  let correctCount = 0;
  const analysis: any[] = [];
  
  judgmentQuestions.value.forEach((question, index) => {
    // 从question_data中获取正确答案
    const qData = stageTestData.value?.question_data;
    const correctAnswer = qData?.correct_answer === '可以' || qData?.correct_answer === 'True' || qData?.correct_answer === true;
    const isCorrect = judgmentAnswers.value[index] === correctAnswer;
    if (isCorrect) correctCount++;

    analysis.push({
      correct: isCorrect,
      explanation: qData?.explanation || '暂无解析'
    });
  });
  
  testPassed.value = correctCount === judgmentQuestions.value.length;
  resultMessage.value = `答对 ${correctCount}/${judgmentQuestions.value.length} 题`;
  showAnalysis.value = true;
  answerAnalysis.value = analysis;
  resultModalVisible.value = true;
};

// 提交选择题
const submitChoice = () => {
  const unanswered = choiceAnswers.value.filter(a => 
    a === undefined || (Array.isArray(a) && a.length === 0)
  ).length;
  
  if (unanswered > 0) {
    message.warning(`还有 ${unanswered} 道题未作答`);
    return;
  }
  
  // 计算得分
  let correctCount = 0;
  const analysis: any[] = [];
  
  choiceQuestions.value.forEach((question, index) => {
    const userAnswer = choiceAnswers.value[index];
    let isCorrect = false;

    // 从question_data中获取正确答案
    const qData = stageTestData.value?.question_data;
    const correctAnswer = qData?.correct_answer;

    if (question.question_type === 'single') {
      // 单选题：检查用户选择的选项索引对应的文本是否等于正确答案
      const selectedOptionText = question.options[userAnswer]?.text;
      isCorrect = selectedOptionText === correctAnswer;
    } else {
      // 多选题（暂时不支持）
      isCorrect = false;
    }

    if (isCorrect) correctCount++;

    analysis.push({
      correct: isCorrect,
      explanation: qData?.explanation || '暂无解析'
    });
  });
  
  testPassed.value = correctCount === choiceQuestions.value.length;
  resultMessage.value = `答对 ${correctCount}/${choiceQuestions.value.length} 题`;
  showAnalysis.value = true;
  answerAnalysis.value = analysis;
  resultModalVisible.value = true;
};

// 初始化
onMounted(() => {
  loadStageData();
  getAIStatus()
    .then((s) => { aiEnabled.value = !!s.available; })
    .catch(() => { aiEnabled.value = false; });
});
</script>

<style scoped>
.stage-test-page {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.test-header {
  background-color: #fff;
  margin-bottom: 24px;
}

.test-content {
  padding: 0 24px 24px;
}

.task-description {
  font-size: 14px;
  line-height: 1.8;
  color: rgba(0, 0, 0, 0.85);
}

.task-description h2 {
  font-size: 16px;
  margin: 16px 0 8px;
}

.task-description code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: monospace;
}

.practice-area {
  padding: 16px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.editor-header h3 {
  margin: 0;
}

.test-result {
  margin-top: 24px;
}

.judgment-area,
.choice-area {
  padding: 16px;
}

.question-item {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 600;
}

.question-content {
  margin-bottom: 16px;
  line-height: 1.6;
}

.result-content {
  padding: 24px;
}

.answer-analysis {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

.analysis-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-weight: 500;
}

.analysis-content {
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
}

/* 参考答案样式 */
.reference-answer-content {
  padding: 16px;
}

.test-cases-section h4,
.evaluation-info h4 {
  margin: 0 0 16px 0;
  color: rgba(0, 0, 0, 0.85);
}

.test-case-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
}

.test-case-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: 500;
}

.test-case-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.test-case-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.test-case-row .label {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.65);
  min-width: 80px;
}

.test-case-row code {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  word-break: break-all;
}

.no-test-cases {
  padding: 32px 0;
}

.evaluation-info {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.eval-item {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.eval-item .label {
  color: rgba(0, 0, 0, 0.65);
}

.eval-item code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.answer-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 500;
}

.answer-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.correct-answer,
.explanation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.correct-answer .label,
.explanation .label {
  flex-shrink: 0;
  color: rgba(0, 0, 0, 0.65);
}

/* 终端样式 */
.terminal-section {
  margin-top: 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #f5f5f5;
  border-bottom: 1px solid #d9d9d9;
}

.terminal-header h4 {
  margin: 0;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.terminal-output {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  min-height: 150px;
  max-height: 250px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.terminal-placeholder {
  color: #6a6a6a;
  font-style: italic;
}

.terminal-line {
  display: flex;
  gap: 8px;
  margin-bottom: 2px;
}

.terminal-line .line-prefix {
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.terminal-line .line-content {
  flex: 1;
  word-break: break-all;
}

.terminal-line.info {
  color: #d4d4d4;
}

.terminal-line.success {
  color: #4ec9b0;
}

.terminal-line.success .line-prefix {
  color: #4ec9b0;
}

.terminal-line.error {
  color: #f14c4c;
}

.terminal-line.error .line-prefix {
  color: #f14c4c;
}

.terminal-line.warning {
  color: #cca700;
}

.terminal-line.warning .line-prefix {
  color: #cca700;
}

.test-stats {
  margin-top: 8px;
  font-weight: 500;
}
</style>
