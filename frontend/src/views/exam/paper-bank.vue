<template>
  <!-- 嵌套在 exam/index PageShell 内，本页不再套 PageShell，避免双 padding -->
  <div class="paper-bank">
    <PageHeaderBar title="试卷库">
      <template #actions>
        <a-button type="primary" @click="showCreatePaperModal">
          <template #icon><PlusOutlined /></template>
          新建试卷
        </a-button>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索试卷名称"
            style="width: 300px"
            @search="handleSearch"
            allow-clear
          />
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
            <a-select-option value="platform">平台</a-select-option>
            <a-select-option value="personal">个人</a-select-option>
          </a-select>
        </Stack>
      </template>
    </PageHeaderBar>

    <!-- 试卷列表 -->
    <div class="paper-list">
      <a-spin :spinning="loading">
        <EmptyStateBlock v-if="!loading && paperList.length === 0" description="暂无试卷" />
        <a-row :gutter="[16, 16]" v-else-if="paperList.length > 0">
          <a-col :xs="24" :sm="12" :md="8" :xl="6" v-for="paper in paperList" :key="paper.id">
            <a-card class="paper-card" :class="{ 'system-paper': paper.source === 'platform' }">
              <template #title>
                <div class="paper-title">{{ paper.title }}</div>
              </template>
              <div class="paper-info">
                <div class="paper-tags">
                  <a-tag v-if="paper.direction" color="blue">{{ paper.direction }}</a-tag>
                  <a-tag :color="getDifficultyColor(paper.difficulty_cn)">{{ paper.difficulty_cn }}</a-tag>
                  <a-tag :color="paper.source === 'platform' ? 'green' : 'purple'">{{ paper.source }}</a-tag>
                </div>
                <div class="paper-detail">
                  <div class="paper-detail-item">
                    <span class="detail-label">题目数:</span>
                    <span class="detail-value">{{ paper.question_count }}</span>
                  </div>
                  <div class="paper-detail-item">
                    <span class="detail-label">总分:</span>
                    <span class="detail-value">{{ paper.total_score }}</span>
                  </div>
                  <div class="paper-detail-item">
                    <span class="detail-label">创建时间:</span>
                    <span class="detail-value">{{ formatDate(paper.created_at) }}</span>
                  </div>
                  <div class="paper-detail-item" v-if="paper.creator_name">
                    <span class="detail-label">创建者:</span>
                    <span class="detail-value">{{ paper.creator_name }}</span>
                  </div>
                </div>
              </div>
              <div class="paper-actions">
                <!-- 移除创建考试按钮 -->
                <a-tooltip title="复制试卷" v-if="paper.can_copy">
                  <a-button size="small" @click="copyPaper(paper)">
                    <template #icon><CopyOutlined /></template>
                    复制
                  </a-button>
                </a-tooltip>
                <a-tooltip title="导出试卷" v-if="paper.can_export">
                  <a-button size="small" @click="exportPaper(paper)">
                    <template #icon><DownloadOutlined /></template>
                    导出
                  </a-button>
                </a-tooltip>
                <a-tooltip title="编辑" v-if="paper.can_edit">
                  <a-button size="small" type="link" @click="editPaper(paper)">
                    <template #icon><EditOutlined /></template>
                    编辑
                  </a-button>
                </a-tooltip>
                <a-tooltip title="删除" v-if="paper.can_delete">
                  <a-button size="small" type="link" danger @click="showDeleteConfirm(paper)">
                    <template #icon><DeleteOutlined /></template>
                    删除
                  </a-button>
                </a-tooltip>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </a-spin>
    </div>

    <!-- 分页 -->
    <div class="pagination-container" v-if="totalPapers > 0">
      <a-pagination
        v-model:current="currentPage"
        :total="totalPapers"
        :pageSize="pageSize"
        show-quick-jumper
        show-size-changer
        @change="handlePageChange"
        @showSizeChange="handleSizeChange"
      />
    </div>

    <!-- 新建试卷弹窗 -->
    <a-modal
      v-model:open="createPaperModalVisible"
      title="新建试卷"
      okText="确定"
      cancelText="取消"
      @ok="handleCreatePaper"
    >
      <a-form
        ref="createPaperFormRef"
        :model="createPaperForm"
        :rules="createPaperRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item name="title" label="试卷名称" required>
          <a-input 
            v-model:value="createPaperForm.title" 
            placeholder="请输入试卷名称"
            :maxLength="60"
            show-count
          />
        </a-form-item>
        <a-form-item name="direction" label="方向分类" required>
          <a-select v-model:value="createPaperForm.direction" placeholder="请选择方向分类">
            <a-select-option v-for="tag in filterTags.directions" :key="tag" :value="tag">
              {{ tag }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="difficulty" label="难易度" required>
          <a-select v-model:value="createPaperForm.difficulty" placeholder="请选择难易度">
            <a-select-option value="BEGINNER">初级</a-select-option>
            <a-select-option value="INTERMEDIATE">中级</a-select-option>
            <a-select-option value="ADVANCED">高级</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item name="composition_method" label="组卷方式" required>
          <a-radio-group v-model:value="createPaperForm.composition_method">
            <a-radio value="MANUAL_SELECTION">选题组卷</a-radio>
            <a-radio value="TEMPLATE_BASED">模板组卷</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item name="description" label="试卷描述">
          <a-textarea 
            v-model:value="createPaperForm.description" 
            placeholder="请输入试卷描述（选填）"
            :rows="3"
          />
        </a-form-item>
      </a-form>
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
      <p>数据删除后不可恢复，是否确定删除该试卷？</p>
      <p>注意：删除试卷不会影响已使用该试卷的考试。</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  CopyOutlined, 
  DownloadOutlined
} from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import { useUserStore } from '@/stores/user';
import { useClassroomStore } from '@/stores/classroom';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import Stack from '@/components/common/Stack.vue';
import { 
  getPaperList,
  createPaper,
  copyPaper as copyPaperApi,
  deletePaper,
  exportPaper as exportPaperApi,
  type PaperItem,
  type CreatePaperRequest
} from '@/api/exam';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const classroomStore = useClassroomStore();

// 搜索和筛选
const searchKeyword = ref('');
const filterDirection = ref<string | undefined>(undefined);
const filterDifficulty = ref<string | undefined>(undefined);
const filterSource = ref<string | undefined>(undefined);

// 筛选标签
const filterTags = ref({
  directions: [] as string[],
  difficulties: ['BEGINNER', 'INTERMEDIATE', 'ADVANCED'],
  sources: ['platform', 'personal']
});

// 分页相关
const currentPage = ref(1);
const pageSize = ref(12);
const totalPapers = ref(0);

// 加载状态
const loading = ref(false);

// 试卷列表
const paperList = ref<PaperItem[]>([]);

// 课堂列表
const classroomList = ref<any[]>([]);

// 弹窗显示状态
const createPaperModalVisible = ref(false);
const deleteConfirmVisible = ref(false);

// 当前选中的试卷
const currentPaper = ref<PaperItem | null>(null);

// 新建试卷表单
const createPaperFormRef = ref();
const createPaperForm = reactive<CreatePaperRequest>({
  title: '',
  direction: '',
  difficulty: 'INTERMEDIATE',
  composition_method: 'MANUAL_SELECTION',
  description: ''
});

// 表单校验规则
const createPaperRules = {
  title: [
    { required: true, message: '请输入试卷名称', trigger: 'blur' },
    { max: 60, message: '试卷名称不能超过60个字符', trigger: 'blur' }
  ],
  direction: [{ required: true, message: '请选择方向分类', trigger: 'change' }],
  difficulty: [{ required: true, message: '请选择难易度', trigger: 'change' }],
  composition_method: [{ required: true, message: '请选择组卷方式', trigger: 'change' }]
};

// 初始化加载数据
onMounted(() => {
  loadPaperList();
  loadClassroomList();
  
  // 检查是否有自动新建的请求
  if (route.query.action === 'create') {
    showCreatePaperModal();
  }
});

// 加载试卷列表
const loadPaperList = async () => {
  if (!userStore.userInfo?.id) return;

  loading.value = true;
  try {
    const res = await getPaperList({
      teacher_id: parseInt(userStore.userInfo.id),
      keyword: searchKeyword.value ? encodeURIComponent(searchKeyword.value) : undefined,
      direction: filterDirection.value,
      difficulty: filterDifficulty.value,
      source: filterSource.value,
      page: currentPage.value,
      page_size: pageSize.value
    });

    if (res.code === '0000') {
      paperList.value = res.data.list;
      totalPapers.value = res.data.meta.total;

      // 更新筛选标签
      if (res.data.filter_tags?.directions) {
        filterTags.value.directions = res.data.filter_tags.directions;
      }
    } else {
      message.error(res.message || '获取试卷列表失败');
    }
  } catch (error) {
    console.error('获取试卷列表失败:', error);
    message.error('获取试卷列表失败');
  } finally {
    loading.value = false;
  }
};

// 加载课堂列表
const loadClassroomList = async () => {
  // 从课堂store获取教师的课堂列表
  if (classroomStore.classrooms.length > 0) {
    classroomList.value = classroomStore.classrooms;
  } else {
    // 如果store中没有数据，触发加载
    await classroomStore.fetchClassrooms();
    classroomList.value = classroomStore.classrooms;
  }
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadPaperList();
};

// 处理筛选条件变化
const handleFilterChange = () => {
  currentPage.value = 1;
  loadPaperList();
};

// 处理分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
  loadPaperList();
};

// 处理每页大小变化
const handleSizeChange = (current: number, size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
  loadPaperList();
};

// 显示创建试卷弹窗
const showCreatePaperModal = () => {
  createPaperForm.title = '';
  createPaperForm.direction = '';
  createPaperForm.difficulty = 'INTERMEDIATE';
  createPaperForm.composition_method = 'MANUAL_SELECTION';
  createPaperForm.description = '';
  createPaperModalVisible.value = true;
};

// 处理创建试卷
const handleCreatePaper = async () => {
  if (!userStore.userInfo?.id) return;

  try {
    await createPaperFormRef.value?.validate();

    const res = await createPaper(createPaperForm, userStore.userInfo.id);

    if (res.code === '0000') {
      message.success('试卷创建成功');
      createPaperModalVisible.value = false;

      // 根据组卷方式跳转
      if (createPaperForm.composition_method === 'MANUAL_SELECTION') {
        // 选题组卷，跳转到编辑页面
        router.push({
          path: '/exam/edit-paper',
          query: {
            id: res.data.paper_id,
            type: 'edit'
          }
        });
      } else {
        // 模板组卷，跳转到模板选择页面
        router.push({
          path: '/exam/template-paper',
          query: {
            paper_id: res.data.paper_id
          }
        });
      }
    } else {
      message.error(res.message || '创建试卷失败');
    }
  } catch (error: any) {
    console.error('创建试卷失败:', error);

    // 处理Pydantic验证错误
    if (error?.type === 'validation_error' && error?.errors) {
      // 显示第一个验证错误
      const firstError = error.errors[0];
      if (firstError?.loc?.includes('title')) {
        message.error(firstError.msg || '试卷名称验证失败');
        createPaperFormRef.value?.scrollToField('title');
      } else {
        message.error(firstError?.msg || '输入验证失败');
      }
    } else {
      message.error('创建试卷失败，请检查输入信息');
    }
  }
};

// 复制试卷
const copyPaper = async (paper: PaperItem) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const res = await copyPaperApi(paper.id, userStore.userInfo.id);
    
    if (res.code === '0000') {
      message.success(`已复制试卷"${paper.title}"`);
      loadPaperList(); // 重新加载列表
    } else {
      message.error(res.message || '复制试卷失败');
    }
  } catch (error) {
    console.error('复制试卷失败:', error);
    message.error('复制试卷失败');
  }
};

// 导出试卷
const exportPaper = async (paper: PaperItem) => {
  if (!userStore.userInfo?.id) return;
  
  try {
    const blob = await exportPaperApi(paper.id, userStore.userInfo.id);
    
    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `试卷_${paper.title}_${dayjs().format('YYYYMMDDHHmmss')}.docx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
    message.success('试卷导出成功');
  } catch (error) {
    console.error('导出试卷失败:', error);
    message.error('导出试卷失败');
  }
};

// 编辑试卷
const editPaper = (paper: PaperItem) => {
  router.push({
    path: '/exam/edit-paper',
    query: {
      id: paper.id,
      type: 'edit'
    }
  });
};

// 显示删除确认弹窗
const showDeleteConfirm = (paper: PaperItem) => {
  currentPaper.value = paper;
  deleteConfirmVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  if (!userStore.userInfo?.id || !currentPaper.value) return;
  
  try {
    const res = await deletePaper(currentPaper.value.id, userStore.userInfo.id);
    
    if (res.code === '0000') {
      message.success('试卷删除成功');
      deleteConfirmVisible.value = false;
      loadPaperList(); // 重新加载列表
    } else {
      message.error(res.message || '删除试卷失败');
    }
  } catch (error) {
    console.error('删除试卷失败:', error);
    message.error('删除试卷失败');
  }
};

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm');
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
.paper-bank {
  width: 100%;
}

.paper-list {
  min-height: 200px;
}

.paper-card {
  height: 100%;
  transition: all 0.3s;
}

.paper-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.system-paper {
  border-top: 3px solid #52c41a;
}

.paper-title {
  font-size: var(--hx-font-size-md);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-info {
  margin-top: var(--hx-space-3);
}

.paper-tags {
  margin-bottom: var(--hx-space-3);
}

.paper-tags .ant-tag {
  margin-bottom: var(--hx-space-2);
}

.paper-detail {
  font-size: var(--hx-font-size-base);
}

.paper-detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--hx-space-2);
  color: var(--hx-color-text-secondary);
}

.detail-label {
  color: var(--hx-color-text-tertiary, var(--hx-color-text-secondary));
}

.detail-value {
  font-weight: 500;
}

.paper-actions {
  margin-top: var(--hx-space-4);
  display: flex;
  flex-wrap: wrap;
  gap: var(--hx-space-2);
}

.paper-actions .ant-btn {
  flex: 1;
  min-width: 0;
}

.pagination-container {
  margin-top: var(--hx-space-5);
  text-align: center;
}
</style> 