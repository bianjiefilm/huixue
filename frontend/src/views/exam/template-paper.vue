<template>
  <div class="template-paper-container">
    <div class="page-header">
      <h1 class="page-title">模板组卷</h1>
      <a-space>
        <a-button @click="goBack">取消</a-button>
        <a-button type="primary" :loading="generating" @click="handleGenerate">生成试卷</a-button>
      </a-space>
    </div>

    <a-card class="paper-form">
      <a-form :model="paperForm" layout="vertical">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="试卷名称" required>
              <a-input v-model:value="paperForm.title" placeholder="请输入试卷名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="考试时长(分钟)" required>
              <a-input-number v-model:value="paperForm.duration" :min="1" :max="300" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="及格分数">
              <a-input-number v-model:value="paperForm.passingScore" :min="0" :max="100" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="总分">
              <a-input-number v-model:value="paperForm.totalScore" :min="0" :max="100" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="试卷说明">
          <a-textarea v-model:value="paperForm.description" placeholder="请输入试卷说明" :rows="4" />
        </a-form-item>
      </a-form>
    </a-card>

    <a-card class="template-rules" title="模板规则配置">
      <div class="rule-buttons">
        <a-button type="primary" @click="addTemplateRule">
          <plus-outlined />
          添加规则
        </a-button>
      </div>

      <div v-if="templateRules.length > 0" class="rule-list">
        <a-collapse v-model:activeKey="activeRuleKeys">
          <a-collapse-panel v-for="(rule, index) in templateRules" :key="rule.id" :header="getRuleHeader(rule)">
            <a-form layout="vertical">
              <a-row :gutter="24">
                <a-col :span="12">
                  <a-form-item label="题型" required>
                    <a-select v-model:value="rule.type" style="width: 100%">
                      <a-select-option value="single">单选题</a-select-option>
                      <a-select-option value="multiple">多选题</a-select-option>
                      <a-select-option value="truefalse">判断题</a-select-option>
                      <a-select-option value="shortanswer">简答题</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="题量" required>
                    <a-input-number v-model:value="rule.count" :min="1" :max="100" style="width: 100%" />
                  </a-form-item>
                </a-col>
              </a-row>

              <a-row :gutter="24">
                <a-col :span="12">
                  <a-form-item label="每题分值" required>
                    <a-input-number 
                      v-model:value="rule.score" 
                      :min="0.5" 
                      :max="50" 
                      :step="0.5" 
                      style="width: 100%" 
                      @change="updateTotalScore"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="难度">
                    <a-select v-model:value="rule.difficulty" style="width: 100%" allowClear>
                      <a-select-option value="easy">简单</a-select-option>
                      <a-select-option value="medium">中等</a-select-option>
                      <a-select-option value="hard">困难</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="分类">
                <a-cascader
                  v-model:value="rule.category"
                  :options="categoryOptions"
                  placeholder="请选择分类"
                  style="width: 100%"
                />
              </a-form-item>

              <a-form-item label="关键词">
                <a-input v-model:value="rule.keyword" placeholder="题干关键词，可不填" />
              </a-form-item>

              <div class="rule-actions">
                <a-space>
                  <a-button danger @click="removeRule(index)">
                    <delete-outlined />
                    删除规则
                  </a-button>
                </a-space>
              </div>
            </a-form>
          </a-collapse-panel>
        </a-collapse>
      </div>

      <a-empty v-else description="暂无规则，请添加模板规则" />
    </a-card>

    <a-card class="preview-section" title="匹配试题预览" v-if="previewQuestions.length > 0">
      <a-alert
        type="info"
        message="以下为根据规则匹配到的试题预览，生成试卷后规则中指定数量的试题将被随机选择"
        style="margin-bottom: 16px"
      />

      <a-table
        :dataSource="previewQuestions"
        :columns="columns"
        rowKey="id"
        :pagination="{ pageSize: 5 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="getQuestionTypeColor(record.type)">
              {{ getQuestionTypeText(record.type) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'difficulty'">
            {{ getDifficultyText(record.difficulty) }}
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { v4 as uuidv4 } from 'uuid';
import { useUserStore } from '@/stores/user';
import { 
  getQuestionList,
  createPaper,
  type QuestionItem,
  type CreatePaperRequest
} from '@/api/exam';

const router = useRouter();
const userStore = useUserStore();
const generating = ref(false);
const activeRuleKeys = ref<string[]>([]);

// 表格列配置
const columns = [
  { title: '题型', dataIndex: 'type', key: 'type', width: 100 },
  { title: '题干', dataIndex: 'content', key: 'content', ellipsis: true },
  { title: '分值', dataIndex: 'score', key: 'score', width: 100 },
  { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 100 }
];

// 试卷表单数据
const paperForm = reactive({
  title: '',
  description: '',
  duration: 60,
  passingScore: 60,
  totalScore: 100
});

// 模板规则
interface TemplateRule {
  id: string;
  type: string;
  count: number;
  score: number;
  difficulty?: string;
  category?: string[];
  keyword?: string;
}

const templateRules = reactive<TemplateRule[]>([]);

// 分类选项
const categoryOptions = ref([
  {
    value: 'basic',
    label: '基础知识',
    children: [
      { value: 'concept', label: '概念理解' },
      { value: 'theory', label: '基本理论' }
    ]
  },
  {
    value: 'application',
    label: '应用知识',
    children: [
      { value: 'scenario', label: '场景应用' },
      { value: 'casestudy', label: '案例分析' }
    ]
  },
  {
    value: 'advanced',
    label: '高级知识',
    children: [
      { value: 'research', label: '研究方向' },
      { value: 'frontier', label: '前沿技术' }
    ]
  }
]);

// 预览试题
const previewQuestions = ref<any[]>([]);

// 添加模板规则
const addTemplateRule = () => {
  const newRule: TemplateRule = {
    id: uuidv4(),
    type: 'single',
    count: 5,
    score: 2
  };
  
  templateRules.push(newRule);
  activeRuleKeys.value = [...activeRuleKeys.value, newRule.id];
  updateTotalScore();
  
  // 触发试题预览
  generatePreview();
};

// 移除规则
const removeRule = (index: number) => {
  const ruleId = templateRules[index].id;
  templateRules.splice(index, 1);
  activeRuleKeys.value = activeRuleKeys.value.filter(key => key !== ruleId);
  updateTotalScore();
  
  // 更新预览
  generatePreview();
};

// 获取规则标题
const getRuleHeader = (rule: TemplateRule) => {
  const typeMap: {[key: string]: string} = {
    single: '单选题',
    multiple: '多选题',
    truefalse: '判断题',
    shortanswer: '简答题'
  };
  
  return `${typeMap[rule.type] || rule.type} - ${rule.count}道 - 每题${rule.score}分`;
};

// 获取试题类型颜色
const getQuestionTypeColor = (type: string) => {
  const typeColorMap: {[key: string]: string} = {
    single: 'blue',
    multiple: 'purple',
    truefalse: 'green',
    shortanswer: 'orange'
  };
  return typeColorMap[type] || 'default';
};

// 获取试题类型文本
const getQuestionTypeText = (type: string) => {
  const typeTextMap: {[key: string]: string} = {
    single: '单选题',
    multiple: '多选题',
    truefalse: '判断题',
    shortanswer: '简答题'
  };
  return typeTextMap[type] || type;
};

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  const difficultyMap: {[key: string]: string} = {
    easy: '简单',
    medium: '中等',
    hard: '困难'
  };
  return difficultyMap[difficulty] || difficulty;
};

// 更新总分
const updateTotalScore = () => {
  let totalScore = 0;
  templateRules.forEach(rule => {
    totalScore += rule.count * rule.score;
  });
  paperForm.totalScore = totalScore;
};

// 生成预览
const generatePreview = async () => {
  if (templateRules.length === 0) {
    previewQuestions.value = [];
    return;
  }
  
  if (!userStore.userInfo?.id) return;
  
  try {
    // 清空当前预览
    previewQuestions.value = [];
    
    // 为每个规则查询符合条件的题目
    for (const rule of templateRules) {
      const res = await getQuestionList({
        teacher_id: userStore.userInfo.id,
        question_type: rule.type.toUpperCase(),
        difficulty: rule.difficulty?.toUpperCase(),
        keyword: rule.keyword,
        page: 1,
        page_size: rule.count * 2  // 查询更多题目用于预览
      });
      
      if (res.code === '0000' && res.data.list.length > 0) {
        // 添加到预览，但不超过count*2个
        const previewCount = Math.min(res.data.list.length, rule.count * 2);
        previewQuestions.value = [...previewQuestions.value, ...res.data.list.slice(0, previewCount)];
      }
    }
  } catch (error) {
    console.error('生成预览失败:', error);
  }
};

// 监听规则变化，更新预览
watch(templateRules, () => {
  generatePreview();
}, { deep: true });

// 返回上一页
const goBack = () => {
  router.back();
};

// 生成试卷
const handleGenerate = async () => {
  if (!userStore.userInfo?.id) return;
  
  generating.value = true;
  try {
    // 表单验证
    if (!paperForm.title) {
      message.warning('请输入试卷名称');
      generating.value = false;
      return;
    }

    if (templateRules.length === 0) {
      message.warning('请至少添加一条模板规则');
      generating.value = false;
      return;
    }

    // 创建试卷
    const createData: CreatePaperRequest = {
      title: paperForm.title,
      description: paperForm.description,
      direction: paperForm.direction,
      difficulty: paperForm.difficulty,
      composition_method: 'TEMPLATE_BASED'
    };
    
    const res = await createPaper(createData, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('试卷生成成功');
      // 跳转到编辑页面完善试卷
      router.push(`/exam/edit-paper?id=${res.data.paper_id}`);
    } else {
      message.error(res.message || '生成失败');
    }
  } catch (error) {
    message.error('生成失败');
    console.error('生成失败', error);
  } finally {
    generating.value = false;
  }
};
</script>

<style scoped>
.template-paper-container {
  padding: 24px;
  background-color: #f0f2f5;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.paper-form, .template-rules, .preview-section {
  margin-bottom: 24px;
}

.rule-buttons {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}

.rule-list {
  margin-bottom: 16px;
}

.rule-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style> 