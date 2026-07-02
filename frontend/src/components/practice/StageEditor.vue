<template>
  <div class="stage-editor">
    <!-- 步骤条 -->
    <a-steps :current="currentStep" style="margin-bottom: 24px">
      <a-step title="关卡任务" />
      <a-step title="任务设置" />
      <a-step title="参考答案" />
    </a-steps>

    <!-- 步骤内容 -->
    <a-spin :spinning="loadingStageData" tip="加载关卡数据...">
      <div class="step-content">
      <!-- 步骤1：关卡任务编辑 -->
      <div v-if="currentStep === 0">
        <a-form
          ref="step1FormRef"
          :model="stageData"
          :rules="step1Rules"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 18 }"
        >
          <a-form-item label="关卡名称" name="title" required>
            <a-input
              v-model:value="stageData.title"
              placeholder="请输入关卡名称（无需录入第几关，系统会自动生成）"
              :maxlength="60"
              show-count
            />
          </a-form-item>

          <a-form-item label="难易度" name="difficulty">
            <a-radio-group v-model:value="stageData.difficulty">
              <a-radio value="easy">初级</a-radio>
              <a-radio value="intermediate">中级</a-radio>
              <a-radio value="advanced">高级</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="技能标签" name="skills">
            <SkillTags
              v-model:value="stageData.skills"
              :max-count="5"
              placeholder="输入技能标签后按回车添加（最多5个）"
            />
            <div class="form-hint">
              每个关卡最多设置5个技能标签，同一课程内的技能标签不可重复
            </div>
          </a-form-item>

          <a-form-item label="过关任务" name="handbook_markdown" required>
            <MarkdownEditor
              v-model:value="stageData.handbook_markdown"
              :height="400"
              placeholder="请输入本关卡的任务描述，支持Markdown格式"
            />
            <div class="form-hint">
              过关任务将显示在关卡挑战页面的左侧栏，请详细描述本关卡的学习目标和任务要求
            </div>
          </a-form-item>

          <a-form-item label="出题类型" name="task_type" required>
            <a-radio-group v-model:value="stageData.task_type">
              <a-radio value="TRUE_FALSE">判断题</a-radio>
              <a-radio value="SINGLE_CHOICE">选择题</a-radio>
              <a-radio value="PRACTICE">实践题</a-radio>
            </a-radio-group>
          </a-form-item>
        </a-form>
      </div>

      <!-- 步骤2：任务设置 -->
      <div v-if="currentStep === 1">
        <!-- 实践题设置 -->
        <div v-if="stageData.task_type === 'PRACTICE'">
          <a-form
            ref="step2FormRef"
            :model="practiceSettings"
            :label-col="{ span: 5 }"
            :wrapper-col="{ span: 18 }"
          >
            <a-form-item label="评测时长限制" required>
              <a-input-number
                v-model:value="practiceSettings.evaluation_time_limit"
                :min="1"
                :max="300"
                addon-after="秒"
                style="width: 200px"
              />
              <span class="form-hint">程序评测运行时间限制，超时会评测失败</span>
            </a-form-item>

            <a-form-item label="学生任务文件" required>
              <a-select
                v-model:value="practiceSettings.student_task_files"
                mode="multiple"
                placeholder="请选择学生需要编辑的文件"
                style="width: 100%"
                :options="fileOptions"
                :not-found-content="fileOptions.length === 0 ? '请先在代码仓库创建文件' : undefined"
              />
              <div class="form-hint">
                这些文件将直接展示给学生，学生需要在其中填写代码
              </div>
            </a-form-item>

            <a-form-item label="评测执行文件" required>
              <a-select
                v-model:value="practiceSettings.evaluation_script_path"
                placeholder="请选择评测执行文件"
                style="width: 100%"
                :options="fileOptions"
                :not-found-content="fileOptions.length === 0 ? '请先在代码仓库创建文件' : undefined"
              />
              <div class="form-hint">
                点击评测按钮时调用的文件，用于检测学员结果是否正确
              </div>
            </a-form-item>

            <a-form-item label="评测执行命令" required>
              <a-input
                v-model:value="practiceSettings.evaluation_command"
                placeholder="例如：python 或 python3"
              />
              <div class="form-hint">
                平台在运行评测时，如何调用您的评测执行文件
              </div>
            </a-form-item>

            <a-form-item label="页面实时预览">
              <a-switch v-model:checked="practiceSettings.enable_realtime_preview" />
              <span v-if="practiceSettings.enable_realtime_preview" style="margin-left: 16px">
                <a-select
                  v-model:value="practiceSettings.preview_file_path"
                  placeholder="请选择要预览的HTML文件"
                  style="width: 300px"
                  :options="htmlFileOptions"
                  :not-found-content="htmlFileOptions.length === 0 ? '请先在代码仓库创建HTML文件' : undefined"
                />
              </span>
              <div class="form-hint">
                前端题目可开启实时预览，展示选中的HTML文件效果
              </div>
            </a-form-item>

            <a-divider>测试集设置</a-divider>

            <TestCaseEditor
              v-model="testCases"
              :min-count="1"
              :max-count="10"
            />
          </a-form>
        </div>

        <!-- 选择题设置 -->
        <div v-else-if="stageData.task_type === 'SINGLE_CHOICE'">
          <ChoiceQuestions
            v-model="choiceQuestions"
            :min-count="1"
            :max-count="10"
          />
        </div>

        <!-- 判断题设置 -->
        <div v-else-if="stageData.task_type === 'TRUE_FALSE'">
          <JudgmentQuestions
            v-model="judgmentQuestions"
            :min-count="1"
            :max-count="10"
          />
        </div>
      </div>

      <!-- 步骤3：参考答案 -->
      <div v-if="currentStep === 2">
        <a-form
          ref="step3FormRef"
          :model="answerData"
          :rules="step3Rules"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 18 }"
        >
          <a-form-item label="答案标题" name="answer_title">
            <a-input
              v-model:value="answerData.answer_title"
              placeholder="请输入参考答案标题"
              :maxlength="100"
            />
          </a-form-item>

          <a-form-item label="答案内容" name="answer_content_markdown" required>
            <MarkdownEditor
              v-model:value="answerData.answer_content_markdown"
              :height="500"
              placeholder="请输入本关卡的参考答案，支持Markdown格式"
            />
            <div class="form-hint">
              教师可以设置学生是否能在通关后查看参考答案
            </div>
          </a-form-item>
        </a-form>
      </div>
      </div>
    </a-spin>

    <!-- 操作按钮 -->
    <div class="step-actions">
      <a-button @click="handleCancel">取消</a-button>
      <a-button v-if="currentStep > 0" @click="prevStep">上一步</a-button>
      <a-button v-if="currentStep < 2" type="primary" @click="nextStep">下一步</a-button>
      <a-button v-if="currentStep === 2" type="primary" @click="handleSubmit" :loading="submitting">
        提交
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';
import SkillTags from './SkillTags.vue';
import MarkdownEditor from './MarkdownEditor.vue';
import TestCaseEditor from './TestCaseEditor.vue';
import JudgmentQuestions from './JudgmentQuestions.vue';
import ChoiceQuestions from './ChoiceQuestions.vue';
import {
  createPracticeStage,
  updateStageBasicInfo,
  updateStageSettings,
  createStageTestCases,
  updateStageAnswer,
  getRepositoryFiles,
  updateStageQuestionSettings,
  createQuestionStageComplete,
  getStageDetail,
  getStageQuestionData,
  type StageCreatePayload,
  type StageSettingsPayload,
  type TestCase,
  type RepoFile,
  type QuestionSettingsRequest,
  type JudgmentQuestion,
  type ChoiceQuestion
} from '@/api/practice';
import { useUserStore } from '@/stores/user';

const props = defineProps<{
  practiceId: number;
  stageId?: string | number; // 编辑模式时传入
}>();

const emit = defineEmits<{
  (e: 'success'): void;
  (e: 'cancel'): void;
}>();

const userStore = useUserStore();
const creatorId = computed(() => userStore.userInfo.id);

// 当前步骤
const currentStep = ref(0);
const submitting = ref(false);
const loadingStageData = ref(false);
const savingStep = ref(false); // 步骤保存中状态

// 表单引用
const step1FormRef = ref<FormInstance>();
const step2FormRef = ref<FormInstance>();
const step3FormRef = ref<FormInstance>();

// 临时保存新创建的关卡ID
const tempStageId = ref<number | null>(null);

// 获取当前操作的关卡ID（编辑模式用props.stageId，新建模式用tempStageId）
const currentStageId = computed(() => props.stageId || tempStageId.value);

// 默认的Markdown模板
const DEFAULT_HANDBOOK_TEMPLATE = `## 学习目标
（请描述本关卡的学习目标）

## 相关知识
（请描述完成本关卡需要的相关知识）

## 编程要求
（请描述本关卡的具体编程任务）

## 预期输出
（请描述正确完成任务后的预期输出或效果）
`;

// 步骤1数据：基本信息
const stageData = reactive<StageCreatePayload>({
  title: '',
  task_type: 'PRACTICE',
  difficulty: 'easy',
  skills: [],
  handbook_markdown: DEFAULT_HANDBOOK_TEMPLATE,
  coin: 0
});

// 步骤2数据：任务设置
const practiceSettings = reactive<StageSettingsPayload>({
  evaluation_time_limit: 20,
  student_task_files: [],
  evaluation_script_path: '',
  evaluation_command: 'python',
  enable_realtime_preview: false,
  preview_file_path: ''
});

// 测试集数据
const testCases = ref<TestCase[]>([
  {
    input_data: '',
    expected_output: '',
    is_hidden: false,
    match_rule: 'exact'
  }
]);

// 判断题数据
const judgmentQuestions = ref<JudgmentQuestion[]>([
  {
    question_content: '',
    correct_answer: true,
    explanation: '',
    score: 10
  }
]);

// 选择题数据
const choiceQuestions = ref<ChoiceQuestion[]>([
  {
    question_type: 'single',
    question_content: '',
    options: [
      { key: 'A', text: '', is_correct: true },
      { key: 'B', text: '', is_correct: false },
      { key: 'C', text: '', is_correct: false },
      { key: 'D', text: '', is_correct: false }
    ],
    explanation: '',
    score: 10
  }
]);

// 步骤3数据：参考答案
const answerData = reactive({
  answer_title: '参考答案',
  answer_content_markdown: ''
});

// 文件选项
const fileOptions = ref<{ label: string; value: string }[]>([]);
const htmlFileOptions = computed(() => 
  fileOptions.value.filter(f => f.value.endsWith('.html'))
);

// 表单验证规则
const step1Rules = {
  title: [
    { required: true, message: '请输入关卡名称', trigger: ['blur', 'change'] },
    { max: 60, message: '关卡名称不能超过60个字符', trigger: ['blur', 'change'] }
  ],
  handbook_markdown: [
    { required: true, message: '请输入过关任务描述', trigger: ['blur', 'change'] }
  ],
  task_type: [
    { required: true, message: '请选择出题类型', trigger: 'change' }
  ]
};

const step3Rules = {
  answer_content_markdown: [
    { required: true, message: '请输入参考答案内容', trigger: 'blur' }
  ]
};

// 加载代码仓库文件列表
const loadRepoFiles = async () => {
  try {
    const files = await getRepositoryFiles(props.practiceId, '', creatorId.value);
    fileOptions.value = convertFilesToOptions(files);
  } catch (error) {
    console.error('加载文件列表失败:', error);
  }
};

// 转换文件列表为选项
const convertFilesToOptions = (files: RepoFile[]): { label: string; value: string }[] => {
  const options: { label: string; value: string }[] = [];
  
  const processFiles = (fileList: RepoFile[], prefix = '') => {
    fileList.forEach(file => {
      if (file.type === 'file') {
        options.push({
          label: prefix + file.name,
          value: file.path
        });
      }
    });
  };
  
  processFiles(files);
  return options;
};

// 上一步
const prevStep = () => {
  currentStep.value--;
};

// 下一步
const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证步骤1
    try {
      if (!step1FormRef.value) {
        console.error('表单引用未初始化');
        return;
      }
      await step1FormRef.value.validate();
      
      // 如果是新建，先创建关卡
      if (!props.stageId) {
        const result = await createPracticeStage(
          props.practiceId,
          stageData,
          creatorId.value
        );
        
        if (result) {
          message.success('关卡基本信息保存成功');
          // 保存新创建的关卡ID，后续步骤需要使用
          tempStageId.value = result.task_id;
        } else {
          message.error('创建关卡失败');
          return;
        }
      } else {
        // 更新基本信息
        const success = await updateStageBasicInfo(
          props.stageId,
          stageData,
          creatorId.value
        );
        
        if (!success) {
          message.error('更新关卡基本信息失败');
          return;
        }
      }
      
      currentStep.value++;
      
      // 如果是实践题，加载文件列表
      if (stageData.task_type === 'PRACTICE') {
        loadRepoFiles();
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  } else if (currentStep.value === 1) {
    // 验证步骤2
    if (stageData.task_type === 'PRACTICE') {
      try {
        await step2FormRef.value?.validate();
        
        if (!currentStageId.value) {
          message.error('关卡ID不存在');
          return;
        }

        // 更新任务设置
        const success = await updateStageSettings(
          currentStageId.value,
          practiceSettings,
          creatorId.value
        );
        
        if (!success) {
          message.error('更新任务设置失败');
          return;
        }
        
        // 创建测试集
        const testSuccess = await createStageTestCases(
          currentStageId.value,
          testCases.value,
          creatorId.value
        );
        
        if (!testSuccess) {
          message.error('创建测试集失败');
          return;
        }
        
        message.success('任务设置保存成功');
        currentStep.value++;
      } catch (error) {
        console.error('表单验证失败:', error);
      }
    } else if (stageData.task_type === 'TRUE_FALSE') {
      // 验证判断题数据
      const hasEmptyQuestions = judgmentQuestions.value.some(q => !q.question_content.trim());
      if (hasEmptyQuestions) {
        message.error('请填写所有判断题的题干');
        return;
      }
      
      if (!currentStageId.value) {
        message.error('关卡ID不存在');
        return;
      }

      // 调用API保存判断题数据
      const questionSettings: QuestionSettingsRequest = {
        question_type: 'judge',
        questions: judgmentQuestions.value
      };

      const success = await updateStageQuestionSettings(
        currentStageId.value,
        questionSettings,
        creatorId.value
      );
      
      if (success) {
        message.success('判断题数据保存成功');
        currentStep.value++;
      } else {
        message.error('保存判断题数据失败');
        return;
      }
    } else if (stageData.task_type === 'SINGLE_CHOICE') {
      // 验证选择题数据
      const hasEmptyQuestions = choiceQuestions.value.some(q => {
        return !q.question_content.trim() ||
               q.options.some(opt => !opt.text.trim()) ||
               !q.options.some(opt => opt.is_correct);
      });

      if (hasEmptyQuestions) {
        message.error('请完整填写所有选择题的题干、选项和正确答案');
        return;
      }

      // 验证多选题至少选择2个正确答案
      const invalidMultipleChoice = choiceQuestions.value.some(q => {
        if (q.question_type === 'multiple') {
          const correctCount = q.options.filter(opt => opt.is_correct).length;
          return correctCount < 2;
        }
        return false;
      });

      if (invalidMultipleChoice) {
        message.error('多选题至少需要选择2个正确答案');
        return;
      }
      
      if (!currentStageId.value) {
        message.error('关卡ID不存在');
        return;
      }

      // 调用API保存选择题数据
      const questionSettings: QuestionSettingsRequest = {
        question_type: 'choice',
        questions: choiceQuestions.value
      };

      const success = await updateStageQuestionSettings(
        currentStageId.value,
        questionSettings,
        creatorId.value
      );
      
      if (success) {
        message.success('选择题数据保存成功');
        currentStep.value++;
      } else {
        message.error('保存选择题数据失败');
        return;
      }
    } else {
      // 其他题型暂时跳过
      currentStep.value++;
    }
  }
};

// 取消
const handleCancel = () => {
  emit('cancel');
};

// 提交
const handleSubmit = async () => {
  try {
    await step3FormRef.value?.validate();
    
    submitting.value = true;
    const stageId = props.stageId || (stageData as any)._tempStageId;
    
    // 更新参考答案
    const success = await updateStageAnswer(
      stageId,
      answerData.answer_title,
      answerData.answer_content_markdown,
      creatorId.value
    );
    
    if (success) {
      message.success('关卡创建成功');
      emit('success');
    } else {
      message.error('保存参考答案失败');
    }
  } catch (error) {
    console.error('提交失败:', error);
  } finally {
    submitting.value = false;
  }
};

// 加载关卡数据（编辑模式）
const loadStageData = async () => {
  if (!props.stageId || !creatorId.value) return;

  loadingStageData.value = true;
  try {
    // 获取关卡详情
    const stageDetail = await getStageDetail(props.stageId, creatorId.value);

    if (stageDetail) {
      // 填充基本信息
      stageData.title = stageDetail.title || '';
      stageData.task_type = stageDetail.task_type || 'PRACTICE';
      stageData.difficulty = stageDetail.difficulty || 'easy';
      stageData.skills = stageDetail.skills || [];
      stageData.handbook_markdown = stageDetail.handbook_markdown || DEFAULT_HANDBOOK_TEMPLATE;
      stageData.coin = stageDetail.coin || 0;

      // 填充任务设置（实践题）
      if (stageDetail.task_type === 'PRACTICE') {
        practiceSettings.evaluation_time_limit = stageDetail.evaluation_time_limit || 20;
        practiceSettings.student_task_files = stageDetail.student_task_files || [];
        practiceSettings.evaluation_script_path = stageDetail.evaluation_script_path || '';
        practiceSettings.evaluation_command = stageDetail.evaluation_command || 'python';
        practiceSettings.enable_realtime_preview = stageDetail.enable_realtime_preview || false;
        practiceSettings.preview_file_path = stageDetail.preview_file_path || '';

        // 填充测试集
        if (stageDetail.test_cases && stageDetail.test_cases.length > 0) {
          testCases.value = stageDetail.test_cases.map((tc: any) => ({
            input_data: tc.input_data || '',
            expected_output: tc.expected_output || '',
            is_hidden: tc.is_hidden || false,
            match_rule: tc.match_rule || 'exact'
          }));
        }
      }

      // 填充参考答案
      answerData.answer_title = stageDetail.answer_title || '参考答案';
      answerData.answer_content_markdown = stageDetail.answer_content_markdown || '';

      // 如果是判断题或选择题，加载题目数据
      if (stageDetail.task_type === 'TRUE_FALSE' || stageDetail.task_type === 'SINGLE_CHOICE') {
        const questionData = await getStageQuestionData(Number(props.stageId), creatorId.value);
        if (questionData) {
          if (stageDetail.task_type === 'TRUE_FALSE' && questionData.judgment_questions) {
            judgmentQuestions.value = questionData.judgment_questions;
          } else if (stageDetail.task_type === 'SINGLE_CHOICE' && questionData.choice_questions) {
            choiceQuestions.value = questionData.choice_questions;
          }
        }
      }
    }
  } catch (error) {
    console.error('加载关卡数据失败:', error);
  } finally {
    loadingStageData.value = false;
  }
};

// 初始化
onMounted(() => {
  // 如果是编辑模式，加载现有数据
  if (props.stageId) {
    loadStageData();
  }
});
</script>

<style scoped>
.stage-editor {
  padding: 24px;
  background: #fff;
  min-height: 600px;
}

.step-content {
  margin: 24px 0;
  min-height: 400px;
}

.step-actions {
  margin-top: 24px;
  text-align: center;
}

.step-actions .ant-btn {
  margin: 0 8px;
}

.form-hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  line-height: 1.5;
}

:deep(.ant-form-item) {
  margin-bottom: 24px;
}
</style>