<template>
  <div class="create-question-form">
    <a-form :model="formState" :rules="rules" layout="vertical" ref="formRef">
      <a-form-item label="题目类型" name="question_type" required>
        <a-radio-group v-model:value="formState.question_type" :disabled="!!questionType">
          <a-radio value="SINGLE_CHOICE">单选题</a-radio>
          <a-radio value="MULTIPLE_CHOICE">多选题</a-radio>
          <a-radio value="TRUE_FALSE">判断题</a-radio>
          <a-radio value="SHORT_ANSWER">简答题</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item label="题干内容" name="content" required>
        <a-textarea
          v-model:value="formState.content"
          placeholder="请输入题干内容"
          :rows="4"
          :maxlength="1000"
          show-count
        />
      </a-form-item>

      <!-- 选择题选项 -->
      <template v-if="formState.question_type === 'SINGLE_CHOICE' || formState.question_type === 'MULTIPLE_CHOICE'">
        <a-form-item label="选项设置" required>
          <div v-for="(option, index) in formState.options" :key="index" class="option-item">
            <div class="option-header">
              <span class="option-key">选项{{ option.key }}</span>
              <a-button
                v-if="formState.options.length > 2"
                type="link"
                danger
                size="small"
                @click="removeOption(index)"
              >
                删除
              </a-button>
            </div>
            <a-textarea
              v-model:value="option.content"
              placeholder="请输入选项内容"
              :rows="2"
            />
          </div>
          <a-button
            v-if="formState.options.length < 10"
            type="dashed"
            block
            @click="addOption"
          >
            <template #icon><PlusOutlined /></template>
            添加选项
          </a-button>
        </a-form-item>

        <a-form-item :label="formState.question_type === 'SINGLE_CHOICE' ? '正确答案' : '正确答案（可多选）'" name="correct_answers" required>
          <a-checkbox-group v-model:value="formState.correct_answers">
            <a-checkbox v-for="option in formState.options" :key="option.key" :value="option.key">
              选项{{ option.key }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </template>

      <!-- 判断题答案 -->
      <template v-if="formState.question_type === 'TRUE_FALSE'">
        <a-form-item label="正确答案" name="correct_answers" required>
          <a-radio-group v-model:value="trueFalseAnswer">
            <a-radio value="true">正确</a-radio>
            <a-radio value="false">错误</a-radio>
          </a-radio-group>
        </a-form-item>
      </template>

      <!-- 简答题参考答案 -->
      <template v-if="formState.question_type === 'SHORT_ANSWER'">
        <a-form-item label="参考答案" name="correct_answers" required>
          <a-textarea
            v-model:value="shortAnswer"
            placeholder="请输入参考答案"
            :rows="4"
          />
        </a-form-item>
      </template>

      <a-form-item label="答案解析" name="explanation">
        <a-textarea
          v-model:value="formState.explanation"
          placeholder="请输入答案解析（选填）"
          :rows="3"
        />
      </a-form-item>

      <a-row :gutter="16">
        <a-col :span="12">
          <a-form-item label="难易度" name="difficulty" required>
            <a-select v-model:value="formState.difficulty" placeholder="请选择难易度">
              <a-select-option value="BEGINNER">初级</a-select-option>
              <a-select-option value="INTERMEDIATE">中级</a-select-option>
              <a-select-option value="ADVANCED">高级</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="12">
          <a-form-item label="分值" name="score" required>
            <a-input-number
              v-model:value="formState.score"
              :min="0.5"
              :max="100"
              :step="0.5"
              style="width: 100%"
              placeholder="请输入分值"
            />
          </a-form-item>
        </a-col>
      </a-row>

      <a-form-item>
        <a-space>
          <a-button type="primary" @click="handleSubmit" :loading="loading">
            创建并添加到试卷
          </a-button>
          <a-button @click="handleCancel">取消</a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { message } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import { createQuestion, addQuestionsToPaper } from '@/api/exam';

interface Props {
  questionType?: string;
  paperId?: number;
}

const props = defineProps<Props>();
const emit = defineEmits(['success', 'cancel']);

const userStore = useUserStore();
const formRef = ref<FormInstance>();
const loading = ref(false);

// 表单数据
const formState = reactive({
  content: '',
  question_type: props.questionType || 'SINGLE_CHOICE',
  options: [
    { key: 'A', content: '' },
    { key: 'B', content: '' },
    { key: 'C', content: '' },
    { key: 'D', content: '' }
  ],
  correct_answers: [] as string[],
  explanation: '',
  difficulty: 'INTERMEDIATE',
  score: 10
});

// 判断题答案（临时变量）
const trueFalseAnswer = ref<string>('');

// 简答题答案（临时变量）
const shortAnswer = ref<string>('');

// 监听题型变化，重置选项
watch(() => formState.question_type, (newType) => {
  if (newType === 'SINGLE_CHOICE' || newType === 'MULTIPLE_CHOICE') {
    // 重置选项为默认4个
    formState.options = [
      { key: 'A', content: '' },
      { key: 'B', content: '' },
      { key: 'C', content: '' },
      { key: 'D', content: '' }
    ];
    formState.correct_answers = [];
  } else if (newType === 'TRUE_FALSE') {
    trueFalseAnswer.value = '';
  } else if (newType === 'SHORT_ANSWER') {
    shortAnswer.value = '';
  }
});

// 监听答案变化，同步到correct_answers
watch(trueFalseAnswer, (val) => {
  if (val) {
    formState.correct_answers = [val];
  }
});

watch(shortAnswer, (val) => {
  if (val) {
    formState.correct_answers = [val];
  }
});

// 表单验证规则
const rules = computed(() => {
  const baseRules = {
    content: [
      { required: true, message: '请输入题干内容', trigger: 'blur' },
      { max: 1000, message: '题干内容不能超过1000个字符', trigger: 'blur' }
    ],
    difficulty: [
      { required: true, message: '请选择难易度', trigger: 'change' }
    ],
    score: [
      { required: true, message: '请输入分值', trigger: 'blur' }
    ]
  };

  if (formState.question_type === 'SINGLE_CHOICE' || formState.question_type === 'MULTIPLE_CHOICE') {
    return {
      ...baseRules,
      correct_answers: [
        { required: true, message: '请选择正确答案', trigger: 'change' },
        {
          validator: (_: any, value: string[]) => {
            if (formState.question_type === 'SINGLE_CHOICE' && value.length !== 1) {
              return Promise.reject('单选题只能选择一个正确答案');
            }
            if (formState.question_type === 'MULTIPLE_CHOICE' && value.length < 2) {
              return Promise.reject('多选题至少选择两个正确答案');
            }
            return Promise.resolve();
          },
          trigger: 'change'
        }
      ]
    };
  }

  return {
    ...baseRules,
    correct_answers: [
      { required: true, message: '请设置正确答案', trigger: 'change' }
    ]
  };
});

// 添加选项
const addOption = () => {
  const nextKey = String.fromCharCode(65 + formState.options.length); // A, B, C...
  formState.options.push({
    key: nextKey,
    content: ''
  });
};

// 删除选项
const removeOption = (index: number) => {
  const removedKey = formState.options[index].key;
  formState.options.splice(index, 1);
  
  // 重新分配选项键
  formState.options.forEach((option, idx) => {
    option.key = String.fromCharCode(65 + idx);
  });
  
  // 更新正确答案
  formState.correct_answers = formState.correct_answers.filter(key => key !== removedKey);
};

// 提交表单
const handleSubmit = async () => {
  if (!userStore.userInfo?.id) return;
  
  try {
    await formRef.value?.validate();
    
    loading.value = true;
    
    // 准备提交数据
    const submitData = {
      content: formState.content,
      question_type: formState.question_type,
      options: formState.question_type === 'SINGLE_CHOICE' || formState.question_type === 'MULTIPLE_CHOICE'
        ? formState.options.filter(opt => opt.content) // 过滤空选项
        : undefined,
      correct_answers: formState.correct_answers,
      explanation: formState.explanation,
      difficulty: formState.difficulty
    };
    
    // 创建试题
    const createRes = await createQuestion(submitData, userStore.userInfo.id);
    
    if (createRes.code === '0000') {
      const questionId = createRes.data.question_id;
      
      // 如果有试卷ID，直接添加到试卷
      if (props.paperId) {
        const addRes = await addQuestionsToPaper(
          props.paperId,
          [questionId],
          [formState.score],
          userStore.userInfo.id
        );
        
        if (addRes.code === '0000') {
          message.success('试题创建成功并已添加到试卷');
          emit('success', questionId);
        } else {
          message.error('试题创建成功但添加到试卷失败');
        }
      } else {
        message.success('试题创建成功');
        emit('success', questionId);
      }
    } else {
      message.error(createRes.message || '创建试题失败');
    }
  } catch (error) {
    console.error('创建试题失败:', error);
  } finally {
    loading.value = false;
  }
};

// 取消
const handleCancel = () => {
  emit('cancel');
};
</script>

<style scoped>
.create-question-form {
  padding: 16px;
}

.option-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.option-key {
  font-weight: 500;
  color: #1890ff;
}
</style> 