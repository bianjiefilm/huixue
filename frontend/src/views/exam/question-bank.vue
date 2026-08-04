<template>
  <!-- 嵌套在 exam/index PageShell 内，本页不再套 PageShell，避免双 padding -->
  <div class="question-bank">
    <PageHeaderBar title="题库">
      <template #actions>
        <a-button type="primary" @click="createQuestion">
          <template #icon><PlusOutlined /></template>
          新建试题
        </a-button>
        <a-button @click="showImportModal">
          <template #icon><ImportOutlined /></template>
          导入试题
        </a-button>
        <a-button
          danger
          :disabled="selectedRowKeys.length === 0"
          @click="showBatchDeleteConfirm"
        >
          <template #icon><DeleteOutlined /></template>
          删除试题 ({{ selectedRowKeys.length }})
        </a-button>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索试题内容"
            style="width: 200px"
            @search="handleSearch"
            allow-clear
          />
          <a-select
            v-model:value="filterType"
            placeholder="题目类型"
            style="width: 120px"
            @change="handleFilterChange"
            allow-clear
          >
            <a-select-option value="SINGLE_CHOICE">单选题</a-select-option>
            <a-select-option value="MULTIPLE_CHOICE">多选题</a-select-option>
            <a-select-option value="TRUE_FALSE">判断题</a-select-option>
            <a-select-option value="SHORT_ANSWER">简答题</a-select-option>
          </a-select>
          <a-select
            v-model:value="filterDirection"
            placeholder="方向分类"
            style="width: 120px"
            @change="handleFilterChange"
            allow-clear
          >
            <a-select-option v-for="tag in filterTags.directions" :key="tag" :value="tag">
              {{ tag }}
            </a-select-option>
          </a-select>
          <a-select
            v-model:value="filterDifficulty"
            placeholder="难易度"
            style="width: 100px"
            @change="handleFilterChange"
            allow-clear
          >
            <a-select-option value="BEGINNER">初级</a-select-option>
            <a-select-option value="INTERMEDIATE">中级</a-select-option>
            <a-select-option value="ADVANCED">高级</a-select-option>
          </a-select>
          <a-select
            v-model:value="filterSource"
            placeholder="来源"
            style="width: 100px"
            @change="handleFilterChange"
            allow-clear
          >
            <a-select-option value="平台">平台</a-select-option>
            <a-select-option value="个人">个人</a-select-option>
          </a-select>
        </Stack>
      </template>
    </PageHeaderBar>

    <!-- 试题列表 -->
    <div class="question-list">
      <a-spin :spinning="loading">
        <EmptyStateBlock v-if="!loading && questionList.length === 0" description="暂无试题" />
        <div v-else-if="questionList.length > 0" class="question-items">
          <a-card 
            v-for="question in questionList" 
            :key="question.id"
            class="question-card"
            :class="{ 'selected': selectedRowKeys.includes(question.id) }"
          >
            <div class="question-header">
              <div class="question-meta">
                <a-checkbox 
                  v-if="question.can_delete"
                  :checked="selectedRowKeys.includes(question.id)"
                  @change="(e: any) => toggleSelection(e, question.id)"
                />
                <a-tag :color="getTypeColor(question.question_type)">
                  {{ question.question_type_cn }}
                </a-tag>
                <a-tag :color="getDifficultyColor(question.difficulty_cn)">
                  {{ question.difficulty_cn }}
                </a-tag>
                <a-tag v-if="question.direction">{{ question.direction }}</a-tag>
                <a-tag :color="question.source === '平台' ? 'green' : 'purple'">
                  {{ question.source }}
                </a-tag>
              </div>
              <div class="question-actions">
                <a-tooltip title="复制" v-if="question.can_copy">
                  <a-button type="link" size="small" @click="copyQuestion(question)">
                    <template #icon><CopyOutlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="编辑" v-if="question.can_edit">
                  <a-button type="link" size="small" @click="editQuestion(question)">
                    <template #icon><EditOutlined /></template>
                  </a-button>
                </a-tooltip>
                <a-tooltip title="删除" v-if="question.can_delete">
                  <a-button type="link" size="small" danger @click="showDeleteConfirm(question)">
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-tooltip>
              </div>
            </div>
            <div class="question-content">
              <div class="question-text" v-html="formatQuestionContent(question.content)"></div>
              <div class="question-info">
                <span v-if="question.creator_name">创建者：{{ question.creator_name }}</span>
                <span>更新时间：{{ formatDate(question.updated_at || question.created_at) }}</span>
              </div>
            </div>
          </a-card>
        </div>
      </a-spin>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="totalQuestions > 0">
      <a-pagination
        v-model:current="currentPage"
        :total="totalQuestions"
        :pageSize="pageSize"
        show-quick-jumper
        show-size-changer
        @change="handlePageChange"
        @showSizeChange="handleSizeChange"
      />
    </div>

    <!-- 导入试题弹窗 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入试题"
      okText="导入"
      cancelText="取消"
      @ok="handleImport"
      :confirmLoading="importLoading"
    >
      <div class="import-content">
        <a-button type="link" @click="downloadTemplate">
          <template #icon><DownloadOutlined /></template>
          下载试题导入模板
        </a-button>
        <a-upload-dragger
          v-model:fileList="fileList"
          :maxCount="1"
          :beforeUpload="beforeUpload"
          accept=".json,.xlsx,.xls"
        >
          <p class="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p class="ant-upload-hint">
            支持JSON、Excel格式，文件大小不超过10MB
          </p>
        </a-upload-dragger>
      </div>
    </a-modal>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteConfirmVisible"
      title="删除确认"
      okText="确定"
      okType="danger"
      cancelText="取消"
      @ok="confirmDelete"
    >
      <p>数据删除后不可恢复，是否确定删除该试题？</p>
      <p>注意：删除试题不会影响已使用该试题的试卷和考试。</p>
    </a-modal>

    <!-- 批量删除确认弹窗 -->
    <a-modal
      v-model:open="batchDeleteConfirmVisible"
      title="批量删除确认"
      okText="确定"
      okType="danger"
      cancelText="取消"
      @ok="confirmBatchDelete"
    >
      <p>数据删除后不可恢复，是否确定删除所选的 {{ selectedRowKeys.length }} 道试题？</p>
      <p>注意：删除试题不会影响已使用这些试题的试卷和考试。</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { message, type UploadProps } from 'ant-design-vue';
import { 
  PlusOutlined, 
  ImportOutlined,
  DownloadOutlined,
  UploadOutlined,
  EditOutlined, 
  DeleteOutlined, 
  CopyOutlined
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import { useUserStore } from '@/stores/user';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import Stack from '@/components/common/Stack.vue';
import {
  getQuestionList,
  createQuestion,
  updateQuestion,
  copyQuestion as copyQuestionApi,
  deleteQuestion,
  deleteQuestions,
  importQuestions,
  downloadQuestionTemplate,
  type QuestionItem
} from '@/api/exam';

const router = useRouter();
const userStore = useUserStore();

// 搜索和筛选
const searchKeyword = ref('');
const filterType = ref<string | undefined>(undefined);
const filterDirection = ref<string | undefined>(undefined);
const filterCategory = ref<string | undefined>(undefined);
const filterDifficulty = ref<string | undefined>(undefined);
const filterSource = ref<string | undefined>(undefined);

// 筛选标签
const filterTags = ref({
  directions: [] as string[],
  categories: [] as string[],
  difficulties: ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'],
  sources: ['平台', '个人']
});

// 分页相关
const currentPage = ref(1);
const pageSize = ref(20);
const totalQuestions = ref(0);

// 加载状态
const loading = ref(false);
const importLoading = ref(false);

// 试题列表
const questionList = ref<QuestionItem[]>([]);

// 选中的行
const selectedRowKeys = ref<number[]>([]);

// 弹窗显示状态
const importModalVisible = ref(false);
const deleteConfirmVisible = ref(false);
const batchDeleteConfirmVisible = ref(false);

// 当前选中的试题（用于单个删除）
const currentQuestion = ref<QuestionItem | null>(null);

// 文件列表（上传）
const fileList = ref<any[]>([]);

// 初始化加载数据
onMounted(() => {
  loadQuestionList();
});

// 加载试题列表
const loadQuestionList = async () => {
  if (!userStore.userInfo?.id) return;
  
  loading.value = true;
  try {
    console.log('开始加载试题列表，关键词:', searchKeyword.value);

    const res = await getQuestionList({
      teacher_id: userStore.userInfo.id,
      keyword: searchKeyword.value ? encodeURIComponent(searchKeyword.value) : undefined,
      question_type: filterType.value,
      direction: filterDirection.value,
      category: filterCategory.value,
      difficulty: filterDifficulty.value,
      source: filterSource.value,
      page: currentPage.value,
      page_size: pageSize.value
    });

    console.log('API响应:', res);
    console.log('API响应状态:', res.code, res.message);

    if (res.code === '0000') {
      console.log('API响应成功，数据:', res.data);
      // 强制更新响应式数据
      questionList.value = [...res.data.list];
      totalQuestions.value = res.data.meta.total;

      console.log('更新后questionList长度:', questionList.value.length);
      console.log('更新后totalQuestions:', totalQuestions.value);
      
      // 更新筛选标签
      if (res.data.filter_tags) {
        if (res.data.filter_tags.directions) {
          filterTags.value.directions = res.data.filter_tags.directions;
        }
        if (res.data.filter_tags.categories) {
          filterTags.value.categories = res.data.filter_tags.categories;
        }
      }
      
      // 清理选中状态（只保留当前页存在的）
      selectedRowKeys.value = selectedRowKeys.value.filter(
        id => questionList.value.some(q => q.id === id)
      );

      // 强制触发视图更新
      await nextTick();
      console.log('视图更新完成');
    } else {
      message.error(res.message || '获取试题列表失败');
    }
  } catch (error) {
    console.error('获取试题列表失败:', error);
    message.error('获取试题列表失败');
  } finally {
    loading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadQuestionList();
};

// 处理筛选条件变化
const handleFilterChange = () => {
  currentPage.value = 1;
  loadQuestionList();
};

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadQuestionList();
};

// 处理每页大小变化
const handleSizeChange = (current: number, size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadQuestionList();
};

// 切换选中状态
const toggleSelection = (e: { target: { checked: boolean } }, id: number) => {
  const checked = e.target.checked;
  if (checked) {
    selectedRowKeys.value.push(id);
  } else {
    selectedRowKeys.value = selectedRowKeys.value.filter(key => key !== id);
  }
};

// 创建试题
const createQuestion = () => {
  router.push('/exam/create-question');
};

// 编辑试题
const editQuestion = (question: QuestionItem) => {
  router.push({
    path: '/exam/edit-question',
    query: {
      id: question.id,
      type: question.question_type
    }
  });
};

// 复制试题
const copyQuestion = async (question: QuestionItem) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await copyQuestionApi(question.id, userStore.userInfo.id);
    
    if (res.code === '0000') {
      message.success('试题复制成功');
      loadQuestionList(); // 重新加载列表
    } else {
      message.error(res.message || '复制试题失败');
    }
  } catch (error) {
    console.error('复制试题失败:', error);
    message.error('复制试题失败');
  }
};

// 显示导入弹窗
const showImportModal = () => {
  fileList.value = [];
  importModalVisible.value = true;
};

// 下载模板
const downloadTemplate = async () => {
  try {
    const blob = await downloadQuestionTemplate();
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `试题导入模板_${dayjs().format('YYYYMMDDHHmmss')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    message.success('模板下载成功');
  } catch (error) {
    console.error('下载模板失败:', error);
    message.error('下载模板失败');
  }
};

// 上传前处理
const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isValidType = file.type === 'application/json' || 
                     file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                     file.type === 'application/vnd.ms-excel';
  if (!isValidType) {
    message.error('只能上传JSON或Excel文件!');
  }
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    message.error('文件必须小于10MB!');
  }
  return isValidType && isLt10M ? false : false; // 返回false阻止自动上传
};

// 处理导入
const handleImport = async () => {
  if (!userStore.userInfo?.id) return;
  
  if (fileList.value.length === 0) {
    message.error('请选择要上传的文件');
    return;
  }
  
  importLoading.value = true;
  try {
    const file = fileList.value[0].originFileObj || fileList.value[0];
    const res = await importQuestions(file, userStore.userInfo.id);
    
    if (res.code === '0000') {
      const { success_count, error_count, error_details } = res.data;
      
      if (error_count === 0) {
        message.success(`导入成功，共导入 ${success_count} 道试题`);
      } else {
        message.warning(`导入完成，成功 ${success_count} 道，失败 ${error_count} 道`);
        
        // 显示错误详情
        if (error_details.length > 0) {
          console.error('导入错误详情:', error_details);
        }
      }
      
      importModalVisible.value = false;
      loadQuestionList(); // 重新加载列表
    } else {
      message.error(res.message || '导入失败');
    }
  } catch (error) {
    console.error('导入试题失败:', error);
    message.error('导入试题失败');
  } finally {
    importLoading.value = false;
  }
};

// 显示删除确认弹窗
const showDeleteConfirm = (question: QuestionItem) => {
  currentQuestion.value = question;
  deleteConfirmVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!userStore.userInfo?.id || !currentQuestion.value) return;
  
  try {
    const res = await deleteQuestion(currentQuestion.value.id, userStore.userInfo.id);
    
    if (res.code === '0000') {
      message.success('试题删除成功');
      deleteConfirmVisible.value = false;
      
      // 从选中列表中移除
      selectedRowKeys.value = selectedRowKeys.value.filter(
        id => id !== currentQuestion.value!.id
      );
      
      loadQuestionList(); // 重新加载列表
    } else {
      message.error(res.message || '删除试题失败');
    }
  } catch (error) {
    console.error('删除试题失败:', error);
    message.error('删除试题失败');
  }
};

// 显示批量删除确认弹窗
const showBatchDeleteConfirm = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请先选择要删除的试题');
    return;
  }
  batchDeleteConfirmVisible.value = true;
};

// 确认批量删除
const confirmBatchDelete = async () => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await deleteQuestions(selectedRowKeys.value, userStore.userInfo.id);
    
    if (res.code === '0000') {
      message.success(`成功删除 ${selectedRowKeys.value.length} 道试题`);
      batchDeleteConfirmVisible.value = false;
      selectedRowKeys.value = [];
      loadQuestionList(); // 重新加载列表
    } else {
      message.error(res.message || '批量删除失败');
    }
  } catch (error) {
    console.error('批量删除失败:', error);
    message.error('批量删除失败');
  }
};

// 格式化试题内容（截取前100字符）
const formatQuestionContent = (content: string) => {
  if (content.length > 100) {
    return content.substring(0, 100) + '...';
  }
  return content;
};

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
};

// 获取题型颜色
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    'SINGLE_CHOICE': 'blue',
    'MULTIPLE_CHOICE': 'cyan',
    'TRUE_FALSE': 'purple',
    'SHORT_ANSWER': 'orange'
  };
  return colorMap[type] || 'default';
};

// 获取难度颜色
const getDifficultyColor = (difficulty: string) => {
  const colorMap: Record<string, string> = {
    '初级': 'green',
    '中级': 'orange',
    '高级': 'red'
  };
  return colorMap[difficulty] || 'default';
};
</script>

<style scoped>
.question-bank {
  width: 100%;
}

.question-list {
  min-height: 200px;
}

.question-items {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-4);
}

.question-card {
  transition: all 0.3s;
}

.question-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.question-card.selected {
  border-color: var(--hx-color-primary);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--hx-space-3);
}

.question-meta {
  display: flex;
  align-items: center;
  gap: var(--hx-space-2);
  flex-wrap: wrap;
}

.question-actions {
  display: flex;
  align-items: center;
}

.question-content {
  margin-left: var(--hx-space-6);
}

.question-text {
  font-size: var(--hx-font-size-base);
  line-height: 1.6;
  color: var(--hx-color-text-primary);
  margin-bottom: var(--hx-space-2);
}

.question-info {
  display: flex;
  gap: var(--hx-space-5);
  font-size: var(--hx-font-size-sm);
  color: var(--hx-color-text-secondary);
}

.pagination-container {
  margin-top: var(--hx-space-5);
  text-align: center;
}

.import-content {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-4);
}
</style> 