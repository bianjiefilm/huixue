<template>
  <div class="create-question-container">
    <a-page-header
      title="新建试题"
      :back-icon="true"
      @back="goBack"
    />
    
    <div class="question-form">
      <a-card :loading="loading">
        <!-- 试题类型选择 -->
        <div class="type-select-container">
          <a-radio-group v-model:value="currentType" button-style="solid" @change="handleTypeChange">
            <a-radio-button value="SINGLE_CHOICE">单选题</a-radio-button>
            <a-radio-button value="MULTIPLE_CHOICE">多选题</a-radio-button>
            <a-radio-button value="TRUE_FALSE">判断题</a-radio-button>
            <a-radio-button value="SHORT_ANSWER">简答题</a-radio-button>
          </a-radio-group>
        </div>
        
        <!-- 试题基本信息 -->
        <a-form
          ref="formRef"
          :model="formState"
          :rules="formRules"
          :label-col="{ span: 3 }"
          :wrapper-col="{ span: 21 }"
        >
          <a-form-item name="direction" label="方向分类" required>
            <a-select v-model:value="formState.direction" placeholder="请选择方向分类" style="width: 300px">
              <a-select-option value="Python基础">Python基础</a-select-option>
              <a-select-option value="大数据">大数据</a-select-option>
              <a-select-option value="人工智能">人工智能</a-select-option>
              <a-select-option value="数据库">数据库</a-select-option>
              <a-select-option value="数据分析">数据分析</a-select-option>
              <a-select-option value="机器学习">机器学习</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item name="category" label="二级分类">
            <a-input v-model:value="formState.category" placeholder="请输入二级分类（选填）" style="width: 300px" />
          </a-form-item>
          
          <a-form-item name="difficulty" label="难易度" required>
            <a-select v-model:value="formState.difficulty" placeholder="请选择难易度" style="width: 200px">
              <a-select-option value="BEGINNER">初级</a-select-option>
              <a-select-option value="INTERMEDIATE">中级</a-select-option>
              <a-select-option value="ADVANCED">高级</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item name="content" label="题目" required>
            <a-textarea
              v-model:value="formState.content"
              placeholder="请输入题目内容"
              :rows="4"
              :maxLength="1000"
              show-count
            />
          </a-form-item>
          
          <!-- 选择题选项区域 -->
          <template v-if="currentType === 'SINGLE_CHOICE' || currentType === 'MULTIPLE_CHOICE'">
            <div
              v-for="(option, index) in formState.options"
              :key="index"
              class="option-form-item"
            >
              <a-form-item
                :name="['options', index, 'content']"
                :label="`选项${option.key}`"
                required
                :rules="[{ required: true, message: '请输入选项内容' }]"
              >
                <div class="option-item">
                  <a-textarea
                    v-model:value="option.content"
                    placeholder="请输入选项内容"
                    :rows="2"
                    style="width: calc(100% - 160px)"
                  />
                  <div class="option-actions">
                    <a-checkbox
                      :checked="formState.correct_answers.includes(option.key)"
                      @change="(e: any) => handleAnswerChange(option.key, e.target.checked)"
                    >
                      正确答案
                    </a-checkbox>
                    <a-button
                      danger
                      type="link"
                      v-if="formState.options.length > 2 && index >= 2"
                      @click="removeOption(index)"
                    >
                      <template #icon><DeleteOutlined /></template>
                      删除
                    </a-button>
                  </div>
                </div>
              </a-form-item>
            </div>
            
            <a-form-item :wrapper-col="{ offset: 3 }">
              <a-button 
                type="dashed" 
                @click="addOption" 
                style="width: 200px" 
                :disabled="formState.options.length >= 10"
              >
                <template #icon><PlusOutlined /></template>
                新增选项
              </a-button>
              <div class="option-tip">
                <InfoCircleOutlined style="margin-right: 4px" />
                {{ currentType === 'SINGLE_CHOICE' ? '单选题只能有一个正确答案' : '多选题至少需要2个正确答案' }}
              </div>
            </a-form-item>
          </template>
          
          <!-- 判断题选项区域 -->
          <template v-if="currentType === 'TRUE_FALSE'">
            <a-form-item name="judgeAnswer" label="正确答案" required>
              <a-radio-group v-model:value="formState.judgeAnswer">
                <a-radio value="true">正确</a-radio>
                <a-radio value="false">错误</a-radio>
              </a-radio-group>
            </a-form-item>
          </template>
          
          <!-- 简答题答案区域 -->
          <template v-if="currentType === 'SHORT_ANSWER'">
            <a-form-item name="essayAnswer" label="参考答案" required>
              <a-textarea
                v-model:value="formState.essayAnswer"
                placeholder="请输入参考答案（若无参考答案可填略或暂无）"
                :rows="6"
                :maxLength="2000"
                show-count
              />
            </a-form-item>
          </template>
          
          <a-form-item name="explanation" label="解析">
            <a-textarea
              v-model:value="formState.explanation"
              placeholder="请输入解析内容（选填）通过解析可以帮助学生理解试题知识点"
              :rows="4"
              :maxLength="1000"
              show-count
            />
          </a-form-item>
          
          <a-form-item :wrapper-col="{ span: 24 }">
            <div class="form-actions">
              <a-button @click="goBack">取消</a-button>
              <a-button type="primary" @click="saveQuestion" :loading="saving">保存</a-button>
            </div>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { 
  PlusOutlined, 
  DeleteOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue';
import type { FormInstance } from 'ant-design-vue';
import { useUserStore } from '@/stores/user';
import { createQuestion, type CreateQuestionRequest, type QuestionType } from '@/api/exam';

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();

// 加载状态
const loading = ref(false);
const saving = ref(false);

// 当前题目类型
const currentType = ref<QuestionType>('SINGLE_CHOICE');

// 表单数据
const formState = reactive({
  content: '',
  direction: undefined as string | undefined,
  category: '',
  difficulty: 'INTERMEDIATE',
  options: [
    { key: 'A', content: '' },
    { key: 'B', content: '' },
    { key: 'C', content: '' },
    { key: 'D', content: '' }
  ],
  correct_answers: [] as string[],
  judgeAnswer: 'true',
  essayAnswer: '',
  explanation: ''
});

// 表单验证规则
const formRules = {
  direction: [{ required: true, message: '请选择方向分类' }],
  difficulty: [{ required: true, message: '请选择难易度' }],
  content: [
    { required: true, message: '请输入题目内容' },
    { max: 1000, message: '题目内容不能超过1000个字符' }
  ],
  essayAnswer: [
    { required: true, message: '请输入参考答案' },
    { max: 2000, message: '参考答案不能超过2000个字符' }
  ],
  judgeAnswer: [{ required: true, message: '请选择正确答案' }]
};

// 处理题目类型变更
const handleTypeChange = () => {
  Modal.confirm({
    title: '切换题型确认',
    content: '切换题型会清空已填写的内容，是否继续？',
    onOk() {
      // 重置表单数据
      formState.options = [
        { key: 'A', content: '' },
        { key: 'B', content: '' },
        { key: 'C', content: '' },
        { key: 'D', content: '' }
      ];
      formState.correct_answers = [];
      formState.judgeAnswer = 'true';
      formState.essayAnswer = '';
    },
    onCancel() {
      // 恢复原来的题型
      if (formState.correct_answers.length > 0 || formState.essayAnswer) {
        currentType.value = detectCurrentType();
      }
    }
  });
};

// 检测当前实际的题型
const detectCurrentType = (): QuestionType => {
  if (formState.essayAnswer) {
    return 'SHORT_ANSWER';
  } else if (formState.judgeAnswer) {
    return 'TRUE_FALSE';
  } else if (formState.correct_answers.length > 1) {
    return 'MULTIPLE_CHOICE';
  } else {
    return 'SINGLE_CHOICE';
  }
};

// 添加选项
const addOption = () => {
  if (formState.options.length < 10) {
    const nextKey = String.fromCharCode(65 + formState.options.length);
    formState.options.push({ key: nextKey, content: '' });
  } else {
    message.warning('最多只能添加10个选项');
  }
};

// 删除选项
const removeOption = (index: number) => {
  const removedKey = formState.options[index].key;
  formState.options.splice(index, 1);
  
  // 重新分配选项标识
  formState.options.forEach((option, i) => {
    option.key = String.fromCharCode(65 + i);
  });
  
  // 更新正确答案
  formState.correct_answers = formState.correct_answers
    .filter(key => key !== removedKey)
    .map(key => {
      const oldIndex = key.charCodeAt(0) - 65;
      if (oldIndex > index) {
        return String.fromCharCode(64 + oldIndex);
      }
      return key;
    });
};

// 处理答案变更
const handleAnswerChange = (key: string, checked: boolean) => {
  if (currentType.value === 'SINGLE_CHOICE') {
    // 单选题只能有一个正确答案
    formState.correct_answers = checked ? [key] : [];
  } else {
    // 多选题
    if (checked) {
      formState.correct_answers.push(key);
    } else {
      formState.correct_answers = formState.correct_answers.filter(k => k !== key);
    }
  }
};

// 检查答案是否有效
const isAnswerValid = computed(() => {
  if (currentType.value === 'SINGLE_CHOICE') {
    // 单选题必须有一个正确答案
    return formState.correct_answers.length === 1;
  } else if (currentType.value === 'MULTIPLE_CHOICE') {
    // 多选题必须有至少两个正确答案
    return formState.correct_answers.length >= 2;
  } else if (currentType.value === 'TRUE_FALSE') {
    // 判断题必须选择正确或错误
    return !!formState.judgeAnswer;
  } else if (currentType.value === 'SHORT_ANSWER') {
    // 简答题必须有参考答案
    return !!formState.essayAnswer;
  }
  return false;
});

// 保存试题
const saveQuestion = async () => {
  if (!userStore.userInfo?.id) {
    message.error('用户信息不完整');
    return;
  }
  
  try {
    await formRef.value?.validate();
    
    // 验证答案
    if (!isAnswerValid.value) {
      if (currentType.value === 'SINGLE_CHOICE') {
        message.error('请选择一个正确答案');
      } else if (currentType.value === 'MULTIPLE_CHOICE') {
        message.error('多选题至少需要选择两个正确答案');
      } else if (currentType.value === 'SHORT_ANSWER') {
        message.error('请填写参考答案');
      }
      return;
    }
    
    // 构建请求数据
    const questionData: CreateQuestionRequest = {
      content: formState.content,
      question_type: currentType.value,
      difficulty: formState.difficulty as 'BEGINNER' | 'INTERMEDIATE' | 'ADVANCED',
      direction: formState.direction,
      category: formState.category || undefined,
      explanation: formState.explanation || undefined,
      options: undefined,
      correct_answers: []
    };
    
    // 根据题型设置选项和答案
    if (currentType.value === 'SINGLE_CHOICE' || currentType.value === 'MULTIPLE_CHOICE') {
      // 过滤掉空选项
      const validOptions = formState.options.filter(opt => opt.content.trim());
      if (validOptions.length < 2) {
        message.error('至少需要2个选项');
        return;
      }
      questionData.options = validOptions;
      questionData.correct_answers = formState.correct_answers;
    } else if (currentType.value === 'TRUE_FALSE') {
      questionData.correct_answers = [formState.judgeAnswer];
    } else if (currentType.value === 'SHORT_ANSWER') {
      questionData.correct_answers = [formState.essayAnswer];
    }
    
    saving.value = true;
    const response = await createQuestion(questionData, userStore.userInfo.id);
    
    if (response.code === '0000') {
      message.success('试题创建成功');
      router.push('/exam/question-bank');
    } else {
      message.error(response.message || '创建试题失败');
    }
  } catch (error) {
    console.error('保存试题失败:', error);
    message.error('保存试题失败');
  } finally {
    saving.value = false;
  }
};

// 返回上一页
const goBack = () => {
  router.back();
};
</script>

<style scoped>
.create-question-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.type-select-container {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.question-form {
  margin-top: 16px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.option-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 120px;
}

.option-tip {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  gap: 16px;
}

:deep(.ant-form-item-label) {
  text-align: left;
}
</style> 