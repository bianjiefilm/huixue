<template>
  <div class="edit-paper-container">
    <!-- 左侧悬浮栏 -->
    <div class="floating-sidebar">
      <div class="sidebar-header">
        <h3>试卷概览</h3>
      </div>
      
      <div class="sidebar-content">
        <!-- 试卷信息摘要 -->
        <div class="paper-summary">
          <div class="summary-item">
            <span class="label">总题数：</span>
            <span class="value">{{ paperInfo.question_count }}道</span>
          </div>
          <div class="summary-item">
            <span class="label">总分：</span>
            <span class="value">{{ paperInfo.total_score }}分</span>
          </div>
        </div>

        <!-- 大题列表（可拖拽排序） -->
        <div class="sections-list">
          <h4>大题排序</h4>
          <draggable
            v-model="sectionList"
            item-key="question_type"
            @end="handleSectionOrderChange"
            class="draggable-sections"
          >
            <template #item="{ element, index }">
              <div class="section-item" :key="element.question_type">
                <div class="section-header">
                  <i class="drag-handle">⋮⋮</i>
                  <span class="section-title">
                    {{ index + 1 }}. {{ element.question_type_cn }}
                  </span>
                  <span class="section-count">
                    ({{ element.count }}题 {{ element.total_score }}分)
                  </span>
                </div>
                
                <!-- 每题分数设置 -->
                <div class="score-setting">
                  <label>每题分数：</label>
                  <a-input-number
                    v-model:value="element.score_per_question"
                    :min="0.5"
                    :max="100"
                    :step="0.5"
                    size="small"
                    @change="(value) => handleBatchScoreChange(element.question_type, value)"
                  />
                </div>
              </div>
            </template>
          </draggable>
        </div>

        <!-- 完成按钮 -->
        <div class="sidebar-actions">
          <a-button type="primary" block @click="handleComplete" :loading="saving">
            完成编辑
          </a-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="page-header">
        <h1 class="page-title">{{ isEdit ? '编辑试卷' : '新建试卷' }}</h1>
        <a-space>
          <a-button @click="goBack">取消</a-button>
          <a-button type="primary" :loading="saving" @click="handleComplete">完成编辑</a-button>
        </a-space>
      </div>

      <!-- 试卷基本信息 -->
      <a-card class="paper-info" title="试卷基本信息">
        <template #extra>
          <a-button type="link" @click="editBasicInfo">
            <EditOutlined />
            编辑
          </a-button>
        </template>
        
        <a-descriptions :column="2" :label-style="{ fontWeight: 500 }">
          <a-descriptions-item label="试卷名称">{{ paperInfo.title }}</a-descriptions-item>
          <a-descriptions-item label="难易度">{{ paperInfo.difficulty_cn || '-' }}</a-descriptions-item>
          <a-descriptions-item label="方向分类">{{ paperInfo.direction || '-' }}</a-descriptions-item>
          <a-descriptions-item label="试卷总分">{{ paperInfo.total_score }}分</a-descriptions-item>
          <a-descriptions-item label="题目数量">{{ paperInfo.question_count }}道</a-descriptions-item>
          <a-descriptions-item label="组卷方式">{{ getCompositionMethodText(paperInfo.composition_method) }}</a-descriptions-item>
        </a-descriptions>
        <a-descriptions :column="1" :label-style="{ fontWeight: 500 }" v-if="paperInfo.description">
          <a-descriptions-item label="试卷描述">{{ paperInfo.description }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 试题内容区域 -->
      <a-card class="question-section" title="试题内容">
        <template #extra>
          <div class="score-info">
            当前总分：{{ paperInfo.total_score }}分
          </div>
        </template>

        <div class="question-groups">
          <!-- 按题型分组显示 -->
          <div
            v-for="(group, index) in questionGroups"
            :key="group.questionType"
            class="question-group"
          >
            <div class="group-header">
              <h3 class="group-title">
                <span class="group-index">{{ index + 1 }}.</span>
                {{ group.title }}
                <span class="group-info">（共{{ group.questions.length }}道题，{{ group.totalScore }}分）</span>
              </h3>
              <div class="group-actions">
                <a-button type="primary" @click="openCreateQuestionModal(group.questionType)">
                  新建{{ group.title.replace('题', '') }}
                </a-button>
                <a-button @click="openImportModal(group.questionType)">
                  导入试题
                </a-button>
              </div>
            </div>

            <!-- 试题列表（可拖拽排序） -->
            <div class="questions-list" v-if="group.questions.length > 0">
              <draggable
                v-model="group.questions"
                item-key="question_id"
                @end="(evt) => handleQuestionOrderChange(group.questionType, evt)"
                class="draggable-questions"
              >
                <template #item="{ element }">
                  <div class="question-item" :key="element.question_id">
                    <div class="question-header">
                      <i class="drag-handle">⋮⋮</i>
                      <span class="question-number">{{ element.order_in_paper }}</span>
                      <div class="question-actions">
                        <a-input-number
                          v-model:value="element.score_for_question"
                          :min="0.5"
                          :max="100"
                          :step="0.5"
                          size="small"
                          @change="(value) => handleScoreChange(element, value)"
                          class="score-input"
                        />
                        <span class="score-label">分</span>
                        <a-dropdown>
                          <template #overlay>
                            <a-menu>
                              <a-menu-item @click="editQuestion(element)">
                                <EditOutlined />
                                编辑试题
                              </a-menu-item>
                              <a-menu-item @click="removeQuestion(element)">
                                <DeleteOutlined />
                                移除试题
                              </a-menu-item>
                            </a-menu>
                          </template>
                          <a-button type="link" size="small">
                            <MoreOutlined />
                          </a-button>
                        </a-dropdown>
                      </div>
                    </div>
                    
                    <div class="question-content" v-html="formatQuestionContent(element.content)"></div>
                    
                    <!-- 选择题选项 -->
                    <div v-if="element.options && element.options.length > 0" class="question-options">
                      <div
                        v-for="(option, optionIndex) in element.options"
                        :key="optionIndex"
                        class="option-item"
                      >
                        <span class="option-label">{{ String.fromCharCode(65 + optionIndex) }}.</span>
                        <span class="option-content">{{ option }}</span>
                      </div>
                    </div>
                  </div>
                </template>
              </draggable>
            </div>

            <!-- 空状态 -->
            <div v-else class="empty-state">
              <a-empty description="暂无试题">
                <a-button type="primary" @click="openCreateQuestionModal(group.questionType)">
                  新建{{ group.title.replace('题', '') }}
                </a-button>
                <a-button style="margin-left: 8px;" @click="openImportModal(group.questionType)">
                  导入试题
                </a-button>
              </a-empty>
            </div>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 导入试题弹窗 -->
    <a-modal
      v-model:open="importModalVisible"
      :title="`导入${currentQuestionType ? getQuestionTypeText(currentQuestionType) : '试题'}`"
      width="1000px"
      :footer="null"
      @cancel="closeImportModal"
    >
      <div class="import-content">
        <!-- 筛选条件 -->
        <div class="filter-section">
          <a-form layout="inline">
            <a-form-item label="来源">
              <a-select v-model:value="importFilters.source" style="width: 120px" @change="loadAvailableQuestions">
                <a-select-option value="">全部</a-select-option>
                <a-select-option value="personal">个人题库</a-select-option>
                <a-select-option value="platform">平台题库</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="方向">
              <a-select v-model:value="importFilters.direction" style="width: 150px" @change="loadAvailableQuestions">
                <a-select-option value="">全部方向</a-select-option>
                <a-select-option value="大数据">大数据</a-select-option>
                <a-select-option value="人工智能">人工智能</a-select-option>
                <a-select-option value="云计算">云计算</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="难度">
              <a-select v-model:value="importFilters.difficulty" style="width: 120px" @change="loadAvailableQuestions">
                <a-select-option value="">全部难度</a-select-option>
                <a-select-option value="BEGINNER">初级</a-select-option>
                <a-select-option value="INTERMEDIATE">中级</a-select-option>
                <a-select-option value="ADVANCED">高级</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item>
              <a-input
                v-model:value="importFilters.keyword"
                placeholder="搜索试题内容"
                style="width: 200px"
                @change="loadAvailableQuestions"
              />
            </a-form-item>
          </a-form>
        </div>

        <!-- 试题列表 -->
        <div class="questions-grid">
          <div
            v-for="question in availableQuestions"
            :key="question.id"
            :class="['question-card', { selected: selectedQuestionIds.includes(question.id) }]"
            @click="toggleQuestion(question.id)"
          >
            <div class="card-header">
              <a-checkbox :checked="selectedQuestionIds.includes(question.id)" />
              <span class="question-type-tag">{{ question.question_type_cn }}</span>
              <span class="difficulty-tag">{{ question.difficulty_cn }}</span>
            </div>
            <div class="card-content" v-html="formatQuestionContent(question.content)"></div>
          </div>
        </div>

        <!-- 分页 -->
        <div class="pagination-section">
          <a-pagination
            v-model:current="importPagination.page"
            :page-size="importPagination.pageSize"
            :total="importPagination.total"
            @change="loadAvailableQuestions"
            show-size-changer
            show-quick-jumper
          />
        </div>

        <!-- 底部操作栏 -->
        <div class="selected-section" v-if="selectedQuestionIds.length > 0">
          <div class="selected-header">
            <span>已选试题（{{ selectedQuestionIds.length }}道）</span>
            <a-button type="link" size="small" @click="clearSelection">清空</a-button>
          </div>
          <div class="selected-count">
            预计总分：{{ selectedTotalScore }}分
          </div>
          <a-button type="primary" block @click="confirmImport">
            确定添加
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 新建试题弹窗 -->
    <a-modal
      v-model:open="createQuestionVisible"
      :title="`新建${currentQuestionType ? getQuestionTypeText(currentQuestionType) : '试题'}`"
      :footer="null"
      width="800px"
      :destroy-on-close="true"
    >
      <CreateQuestionForm
        :question-type="currentQuestionType"
        :paper-id="paperId"
        @success="handleCreateQuestionSuccess"
        @cancel="createQuestionVisible = false"
      />
    </a-modal>

    <!-- 编辑试卷基本信息弹窗 -->
    <a-modal
      v-model:open="basicInfoModalVisible"
      title="编辑试卷基本信息"
      @ok="handleBasicInfoUpdate"
      width="600px"
    >
      <a-form layout="vertical">
        <a-form-item label="试卷名称" required>
          <a-input
            v-model:value="editingBasicInfo.title"
            placeholder="请输入试卷名称"
            :max-length="60"
            show-count
          />
        </a-form-item>
        <a-form-item label="方向分类">
          <a-select v-model:value="editingBasicInfo.direction" placeholder="请选择方向">
            <a-select-option value="大数据">大数据</a-select-option>
            <a-select-option value="人工智能">人工智能</a-select-option>
            <a-select-option value="云计算">云计算</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="难易度">
          <a-select v-model:value="editingBasicInfo.difficulty" placeholder="请选择难度">
            <a-select-option value="BEGINNER">初级</a-select-option>
            <a-select-option value="INTERMEDIATE">中级</a-select-option>
            <a-select-option value="ADVANCED">高级</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="试卷描述">
          <a-textarea
            v-model:value="editingBasicInfo.description"
            placeholder="请输入试卷描述"
            :rows="4"
            :max-length="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { message, Empty } from 'ant-design-vue';
import { EditOutlined, DeleteOutlined, MoreOutlined } from '@ant-design/icons-vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '@/stores/user';
import draggable from 'vuedraggable';
import {
  getPaperDetail,
  getQuestionList,
  addQuestionsToPaper,
  removeQuestionsFromPaper,
  updateQuestionScore,
  batchUpdateQuestionsScore,
  updateQuestionsOrder,
  updateSectionsOrder,
  updatePaperBasicInfo,
  completePaperEditing,
  type PaperDetail,
  type PaperQuestion,
  type QuestionItem
} from '@/api/exam';
import CreateQuestionForm from '@/components/exam/CreateQuestionForm.vue';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();

// 状态变量
const loading = ref(false);
const saving = ref(false);
const paperId = ref<number>(0);
const isEdit = ref(false);

// 试卷信息
const paperInfo = ref<PaperDetail>({
  id: 0,
  title: '',
  direction: '',
  difficulty: '',
  difficulty_cn: '',
  source: '',
  question_count: 0,
  total_score: 0,
  created_at: '',
  can_create_exam: false,
  can_copy: false,
  can_export: false,
  can_edit: false,
  can_delete: false,
  questions: []
});

// 弹窗状态
const importModalVisible = ref(false);
const createQuestionVisible = ref(false);
const basicInfoModalVisible = ref(false);

// 当前操作的数据
const currentQuestionType = ref<string>('');
const editingBasicInfo = reactive({
  title: '',
  direction: '',
  difficulty: '',
  description: ''
});

// 导入相关
const selectedQuestionIds = ref<number[]>([]);
const availableQuestions = ref<QuestionItem[]>([]);

// 导入筛选条件
const importFilters = reactive({
  source: '',
  direction: '',
  difficulty: '',
  keyword: ''
});

// 导入分页
const importPagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0
});

// 大题排序列表
const sectionList = ref<any[]>([]);

// 计算属性
const questionGroups = computed(() => {
  const groups: Record<string, any> = {};
  const typeOrder = ['SINGLE_CHOICE', 'MULTIPLE_CHOICE', 'TRUE_FALSE', 'SHORT_ANSWER'];
  const typeNames: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题'
  };
  
  // 初始化所有题型分组
  typeOrder.forEach(type => {
    groups[type] = {
      questionType: type,
      title: typeNames[type],
      questions: [],
      totalScore: 0
    };
  });
  
  // 分组试题
  paperInfo.value.questions.forEach(q => {
    if (groups[q.question_type]) {
      groups[q.question_type].questions.push(q);
      groups[q.question_type].totalScore += q.score_for_question || 0;
    }
  });
  
  // 按大题排序返回有试题的分组
  const sortedTypes = sectionList.value.length > 0 
    ? sectionList.value.map(s => s.question_type)
    : typeOrder;
    
  return sortedTypes.map(type => groups[type]).filter(g => g.questions.length > 0);
});

// 计算已选试题的预计总分
const selectedTotalScore = computed(() => {
  const defaultScores: Record<string, number> = {
    'SINGLE_CHOICE': 5,
    'MULTIPLE_CHOICE': 10,
    'TRUE_FALSE': 5,
    'SHORT_ANSWER': 20
  };
  
  return selectedQuestionIds.value.reduce((sum, id) => {
    const question = availableQuestions.value.find(q => q.id === id);
    if (question) {
      return sum + (defaultScores[question.question_type] || 10);
    }
    return sum;
  }, 0);
});

// 页面加载
onMounted(() => {
  const id = route.query.id || route.params.id;
  if (id) {
    paperId.value = Number(id);
    isEdit.value = true;
    loadPaperDetail();
  } else {
    isEdit.value = false;
  }
});

// 加载试卷详情
const loadPaperDetail = async () => {
  if (!userStore.userInfo?.id) return;
  
  loading.value = true;
  try {
    const res = await getPaperDetail(paperId.value, userStore.userInfo.id);
    if (res.code === '0000' && res.data) {
      paperInfo.value = res.data;
      updateSectionList();
    } else {
      message.error(res.message || '获取试卷详情失败');
    }
  } catch (error) {
    console.error('获取试卷详情失败:', error);
    message.error('获取试卷详情失败');
  } finally {
    loading.value = false;
  }
};

// 更新大题列表
const updateSectionList = () => {
  if (!paperInfo.value?.questions) return;
  const sections: Record<string, any> = {};
  const typeNames: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题'
  };
  
  paperInfo.value.questions.forEach(q => {
    if (!sections[q.question_type]) {
      sections[q.question_type] = {
        question_type: q.question_type,
        question_type_cn: typeNames[q.question_type],
        count: 0,
        total_score: 0,
        score_per_question: q.score_for_question
      };
    }
    sections[q.question_type].count++;
    sections[q.question_type].total_score += q.score_for_question;
  });
  
  sectionList.value = Object.values(sections);
};

// 处理大题排序变化
const handleSectionOrderChange = async (evt: any) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const sectionOrders = sectionList.value.map((section, index) => ({
      question_type: section.question_type,
      order_index: index + 1
    }));
    
    const res = await updateSectionsOrder(paperId.value, sectionOrders, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('大题排序更新成功');
      loadPaperDetail();
    } else {
      message.error(res.message || '更新大题排序失败');
    }
  } catch (error) {
    console.error('更新大题排序失败:', error);
    message.error('更新大题排序失败');
  }
};

// 处理题目排序变化
const handleQuestionOrderChange = async (questionType: string, evt: any) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const group = questionGroups.value.find(g => g.questionType === questionType);
    if (!group) return;
    
    const questionOrders = group.questions.map((question: any, index: number) => ({
      question_id: question.question_id,
      order_index: index + 1
    }));
    
    const res = await updateQuestionsOrder(paperId.value, questionOrders, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('题目排序更新成功');
      loadPaperDetail();
    } else {
      message.error(res.message || '更新题目排序失败');
    }
  } catch (error) {
    console.error('更新题目排序失败:', error);
    message.error('更新题目排序失败');
  }
};

// 处理批量分值设置
const handleBatchScoreChange = async (questionType: string, scorePerQuestion: number) => {
  if (!userStore.userInfo?.id || !scorePerQuestion) return;
  
  try {
    const res = await batchUpdateQuestionsScore(paperId.value, questionType, scorePerQuestion, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success(`成功更新${res.data.updated_count}道题目分值`);
      loadPaperDetail();
      updateSectionList();
    } else {
      message.error(res.message || '批量更新分值失败');
    }
  } catch (error) {
    console.error('批量更新分值失败:', error);
    message.error('批量更新分值失败');
  }
};

// 处理单个题目分值变化
const handleScoreChange = async (question: PaperQuestion, newScore: number) => {
  if (!userStore.userInfo?.id || !newScore) return;
  
  try {
    const res = await updateQuestionScore(paperId.value, question.question_id, newScore, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('分值更新成功');
      loadPaperDetail();
      updateSectionList();
    } else {
      message.error(res.message || '更新分值失败');
    }
  } catch (error) {
    console.error('更新分值失败:', error);
    message.error('更新分值失败');
  }
};

// 打开创建试题弹窗
const openCreateQuestionModal = (questionType: string) => {
  currentQuestionType.value = questionType;
  createQuestionVisible.value = true;
};

// 打开导入试题弹窗
const openImportModal = (questionType: string) => {
  currentQuestionType.value = questionType;
  importModalVisible.value = true;
  loadAvailableQuestions();
};

// 关闭导入弹窗
const closeImportModal = () => {
  selectedQuestionIds.value = [];
  currentQuestionType.value = '';
  Object.assign(importFilters, {
    source: '',
    direction: '',
    difficulty: '',
    keyword: ''
  });
};

// 加载可用试题
const loadAvailableQuestions = async () => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const params = {
      teacher_id: userStore.userInfo.id,
      question_type: currentQuestionType.value,
      ...importFilters,
      page: importPagination.page,
      page_size: importPagination.pageSize
    };
    
    const res = await getQuestionList(params);
    if (res.code === '0000') {
      availableQuestions.value = res.data.list;
      importPagination.total = res.data.meta.total;
    }
  } catch (error) {
    console.error('加载试题失败:', error);
    message.error('加载试题失败');
  }
};

// 切换试题选择
const toggleQuestion = (questionId: number) => {
  const index = selectedQuestionIds.value.indexOf(questionId);
  if (index > -1) {
    selectedQuestionIds.value.splice(index, 1);
  } else {
    selectedQuestionIds.value.push(questionId);
  }
};

// 清空选择
const clearSelection = () => {
  selectedQuestionIds.value = [];
};

// 确认导入
const confirmImport = async () => {
  if (!userStore.userInfo?.id || selectedQuestionIds.value.length === 0) return;
  
  try {
    const defaultScores: Record<string, number> = {
      'SINGLE_CHOICE': 5,
      'MULTIPLE_CHOICE': 10,
      'TRUE_FALSE': 5,
      'SHORT_ANSWER': 20
    };
    
    const scores = selectedQuestionIds.value.map(id => {
      const question = availableQuestions.value.find(q => q.id === id);
      return defaultScores[question?.question_type || 'SINGLE_CHOICE'] || 10;
    });
    
    const res = await addQuestionsToPaper(
      paperId.value,
      selectedQuestionIds.value,
      scores,
      userStore.userInfo.id
    );
    
    if (res.code === '0000') {
      message.success(`成功添加${res.data.added_count}道试题`);
      importModalVisible.value = false;
      loadPaperDetail();
    } else {
      message.error(res.message || '添加试题失败');
    }
  } catch (error) {
    console.error('添加试题失败:', error);
    message.error('添加试题失败');
  }
};

// 编辑试题
const editQuestion = (question: PaperQuestion) => {
  router.push({
    path: '/exam/edit-question',
    query: {
      id: question.question_id,
      type: question.question_type,
      from: 'paper',
      paperId: paperId.value
    }
  });
};

// 移除试题
const removeQuestion = async (question: PaperQuestion) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await removeQuestionsFromPaper(
      paperId.value,
      [question.question_id],
      userStore.userInfo.id
    );
    
    if (res.code === '0000') {
      message.success('试题已从试卷中移除');
      loadPaperDetail();
    } else {
      message.error(res.message || '移除试题失败');
    }
  } catch (error) {
    console.error('移除试题失败:', error);
    message.error('移除试题失败');
  }
};

// 编辑基本信息
const editBasicInfo = () => {
  Object.assign(editingBasicInfo, {
    title: paperInfo.value.title,
    direction: paperInfo.value.direction,
    difficulty: paperInfo.value.difficulty,
    description: paperInfo.value.description
  });
  basicInfoModalVisible.value = true;
};

// 更新基本信息
const handleBasicInfoUpdate = async () => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await updatePaperBasicInfo(paperId.value, editingBasicInfo, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('试卷基本信息更新成功');
      basicInfoModalVisible.value = false;
      loadPaperDetail();
    } else {
      message.error(res.message || '更新失败');
    }
  } catch (error) {
    console.error('更新基本信息失败:', error);
    message.error('更新基本信息失败');
  }
};

// 处理创建试题成功
const handleCreateQuestionSuccess = (questionId: number) => {
  createQuestionVisible.value = false;
  message.success('试题创建成功并已添加到试卷');
  loadPaperDetail();
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 完成编辑
const handleComplete = async () => {
  if (!userStore.userInfo?.id) return;
  
  if (paperInfo.value.questions.length === 0) {
    message.warning('试卷中至少需要一道试题');
    return;
  }
  
  saving.value = true;
  try {
    const res = await completePaperEditing(paperId.value, userStore.userInfo.id);
    if (res.code === '0000') {
      message.success('试卷编辑完成');
      router.push('/exam/paper-bank');
    } else {
      message.error(res.message || '完成编辑失败');
    }
  } catch (error) {
    console.error('完成编辑失败:', error);
    message.error('完成编辑失败');
  } finally {
    saving.value = false;
  }
};

// 工具函数
const getCompositionMethodText = (method: string) => {
  const methods: Record<string, string> = {
    'MANUAL_SELECTION': '选题组卷',
    'TEMPLATE_BASED': '模板组卷'
  };
  return methods[method] || method;
};

const getQuestionTypeText = (type: string) => {
  const types: Record<string, string> = {
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'TRUE_FALSE': '判断题',
    'SHORT_ANSWER': '简答题'
  };
  return types[type] || type;
};

const formatQuestionContent = (content: string) => {
  return content ? content.replace(/\n/g, '<br>') : '';
};
</script>

<style scoped>
.edit-paper-container {
  display: flex;
  min-height: 100vh;
  background-color: #f0f2f5;
}

/* 左侧悬浮栏 */
.floating-sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 280px;
  height: 100vh;
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow-y: auto;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.sidebar-content {
  padding: 20px;
}

.paper-summary {
  margin-bottom: 24px;
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.summary-item .label {
  color: #666;
}

.summary-item .value {
  font-weight: 600;
  color: #1890ff;
}

.sections-list h4 {
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
}

.section-item {
  margin-bottom: 16px;
  padding: 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: move;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.drag-handle {
  margin-right: 8px;
  color: #999;
  cursor: move;
}

.section-title {
  flex: 1;
  font-weight: 500;
}

.section-count {
  font-size: 12px;
  color: #666;
}

.score-setting {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-setting label {
  font-size: 12px;
  color: #666;
}

.sidebar-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f0f0f0;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  margin-left: 280px;
  padding: 24px;
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

.paper-info {
  margin-bottom: 24px;
}

.question-section {
  margin-bottom: 24px;
}

.score-info {
  font-size: 16px;
  color: #1890ff;
  font-weight: 500;
}

.question-groups {
  padding: 16px;
}

.question-group {
  margin-bottom: 32px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  background: #fafafa;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.group-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
}

.group-index {
  font-weight: 600;
  margin-right: 8px;
}

.group-info {
  color: #888;
  font-size: 14px;
  font-weight: normal;
  margin-left: 8px;
}

.group-actions {
  display: flex;
  gap: 8px;
}

.question-item {
  padding: 12px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  transition: all 0.3s;
  cursor: move;
}

.question-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.question-number {
  font-weight: 600;
  color: #1890ff;
  margin-left: 8px;
}

.question-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-input {
  width: 80px;
}

.score-label {
  font-size: 12px;
  color: #666;
}

.question-content {
  margin-bottom: 12px;
  line-height: 1.6;
}

.question-options {
  margin-top: 12px;
}

.option-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 6px;
}

.option-label {
  margin-right: 8px;
  font-weight: 500;
  min-width: 20px;
}

.option-content {
  flex: 1;
}

/* 导入弹窗样式 */
.import-content {
  max-height: 600px;
}

.filter-section {
  margin-bottom: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.questions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.question-card {
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.question-card:hover {
  border-color: #1890ff;
}

.question-card.selected {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.question-type-tag,
.difficulty-tag {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.question-type-tag {
  background: #e6f7ff;
  color: #1890ff;
}

.difficulty-tag {
  background: #f6ffed;
  color: #52c41a;
}

.card-content {
  font-size: 14px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.pagination-section {
  text-align: center;
  margin: 16px 0;
}

.selected-section {
  padding: 16px;
  background: #f6f8fa;
  border-radius: 6px;
  margin-top: 16px;
}

.selected-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selected-count {
  margin-bottom: 12px;
  color: #1890ff;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
}

/* 拖拽相关样式 */
.draggable-sections,
.draggable-questions {
  min-height: 20px;
}

.sortable-ghost {
  opacity: 0.5;
}

.sortable-chosen {
  cursor: grabbing;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .floating-sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  .main-content {
    margin-left: 0;
  }
}
</style> 