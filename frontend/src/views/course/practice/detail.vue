<template>
  <div class="practice-detail-page">
    <div class="page-header">
      <a-page-header
        :title="practiceInfo.name"
        :sub-title="getDifficultyText(practiceInfo.difficulty)"
        @back="goBack"
      >
        <template #tags>
          <a-tag :color="getStatusColor(practiceInfo.status)">{{ getStatusText(practiceInfo.status) }}</a-tag>
        </template>
        <template #extra>
          <a-space>
            <!-- 草稿/编辑中/审核未通过状态：显示编辑按钮 -->
            <a-button v-if="canEditBasicInfo" @click="editPractice">编辑</a-button>
            <!-- 已发布状态：显示开启编辑按钮 -->
            <a-button v-if="canStartEdit" type="primary" @click="handleStartEdit">开启编辑</a-button>
            <!-- 克隆按钮始终可见 -->
            <a-button @click="handleClonePractice">克隆</a-button>
            <!-- 已发布状态：添加到课堂 -->
            <a-button v-if="isPublished" type="primary" @click="showAddToClassroomModal">添加到课堂</a-button>
          </a-space>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <a-row :gutter="24">
        <a-col :span="16">
          <a-card class="practice-info-card">
            <a-typography-title :level="4">实践介绍</a-typography-title>
            <a-typography-paragraph>
              {{ practiceInfo.introduction || '暂无实践介绍' }}
            </a-typography-paragraph>
            
            <a-divider />
            
            <a-typography-title :level="4">实践任务</a-typography-title>
            <div v-if="practiceInfo.tasks && practiceInfo.tasks.length > 0">
              <a-collapse v-model:activeKey="activePanelKey">
                <a-collapse-panel 
                  v-for="(task, index) in practiceInfo.tasks" 
                  :key="task.id" 
                  :header="(index + 1) + '. ' + task.title"
                >
                  <a-typography-paragraph>
                    {{ task.description }}
                  </a-typography-paragraph>
                </a-collapse-panel>
              </a-collapse>
            </div>
            <a-empty v-else description="暂无实践任务" />
          </a-card>
        </a-col>
        
        <a-col :span="8">
          <a-card class="practice-meta-card">
            <a-typography-title :level="4">实践信息</a-typography-title>
            
            <a-descriptions :column="1">
              <a-descriptions-item label="创建者">{{ practiceInfo.author || '未知' }}</a-descriptions-item>
              <a-descriptions-item label="实践类型">{{ getPracticeTypeText(practiceInfo.type) }}</a-descriptions-item>
              <a-descriptions-item label="创建时间">{{ formatDate(practiceInfo.createdAt) }}</a-descriptions-item>
              <a-descriptions-item label="更新时间">{{ formatDate(practiceInfo.updatedAt) }}</a-descriptions-item>
            </a-descriptions>
            
            <a-divider />
            
            <a-typography-title :level="4">环境配置</a-typography-title>
            
            <a-descriptions :column="1">
              <a-descriptions-item label="代码编辑器">
                <a-tag :color="practiceInfo.config?.codeEditor ? 'green' : 'red'">
                  {{ practiceInfo.config?.codeEditor ? '已开启' : '已关闭' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="命令行">
                <a-tag :color="practiceInfo.config?.commandLine ? 'green' : 'red'">
                  {{ practiceInfo.config?.commandLine ? '已开启' : '已关闭' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="代码仓库可见性">
                <a-tag :color="practiceInfo.config?.repoVisibility === 'visible' ? 'green' : 'orange'">
                  {{ practiceInfo.config?.repoVisibility === 'visible' ? '可见' : '不可见' }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="允许跳关">
                <a-tag :color="practiceInfo.config?.allowSkip === 'allow' ? 'green' : 'orange'">
                  {{ practiceInfo.config?.allowSkip === 'allow' ? '允许' : '不允许' }}
                </a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>
      </a-row>
    </div>
    
    <!-- 添加到课堂模态框 -->
    <a-modal
      v-model:open="addToClassroomVisible"
      title="添加到课堂"
      :footer="null"
      @cancel="addToClassroomVisible = false"
    >
      <div class="add-to-classroom-content">
        <p>选择要添加此实践的课堂：</p>
        
        <div v-if="myClassrooms.length > 0" class="classroom-list">
          <a-radio-group v-model:value="selectedClassroomId" class="classroom-radio-group">
            <a-space direction="vertical" style="width: 100%">
              <a-radio v-for="classroom in myClassrooms" :key="classroom.id" :value="classroom.id">
                <div class="classroom-item">
                  <div class="classroom-title">{{ classroom.name }}</div>
                  <div class="classroom-desc">{{ classroom.description }}</div>
                </div>
              </a-radio>
            </a-space>
          </a-radio-group>
        </div>
        <a-empty v-else description="暂无可用课堂，请先创建课堂" />
        
        <div class="add-classroom-footer">
          <a-space>
            <a-button @click="addToClassroomVisible = false">取消</a-button>
            <a-button 
              type="primary" 
              @click="addToClassroom" 
              :loading="addingToClassroom"
              :disabled="!selectedClassroomId || myClassrooms.length === 0"
            >
              确认添加
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import dayjs from 'dayjs';
import { clonePractice, startEditMode } from '@/api/practice';
import { get } from '@/utils/request';

const route = useRoute();
const router = useRouter();
const activePanelKey = ref<string[]>([]);
const addToClassroomVisible = ref(false);
const selectedClassroomId = ref<string>('');
const addingToClassroom = ref(false);
const loading = ref(true);

const practiceInfo = reactive({
  id: route.params.id as string,
  name: '',
  introduction: '',
  type: 'code',
  difficulty: '',
  status: 'draft',
  author: '',
  createdAt: null as Date | null,
  updatedAt: null as Date | null,
  config: {
    codeEditor: true,
    commandLine: true,
    repoVisibility: 'visible',
    allowSkip: 'allow'
  },
  tasks: [] as Array<{ id: string; title: string; description: string }>
});

const myClassrooms = ref<Array<{ id: string; name: string; description: string }>>([]);

// 计算属性：是否可以编辑基本信息（草稿/编辑中/审核未通过状态）
const canEditBasicInfo = computed(() => {
  return practiceInfo.status === 'draft' ||
    practiceInfo.status === 'editing' ||
    practiceInfo.status === 'rejected';
});

// 计算属性：是否可以开启编辑（已发布状态）
const canStartEdit = computed(() => {
  return practiceInfo.status === 'published' ||
    practiceInfo.status === 'published_personal' ||
    practiceInfo.status === 'published_public' ||
    practiceInfo.status === 'approved';
});

// 计算属性：是否已发布（可添加到课堂）
const isPublished = computed(() => {
  return practiceInfo.status === 'published' ||
    practiceInfo.status === 'published_personal' ||
    practiceInfo.status === 'published_public' ||
    practiceInfo.status === 'approved';
});

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  const map: Record<string, string> = {
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级'
  };
  return map[difficulty] || '未知难度';
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    'draft': 'default',
    'pending': 'orange',
    'published': 'green',
    'approved': 'green',
    'rejected': 'red'
  };
  return map[status] || 'default';
};

// 获取状态文本
const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'draft': '草稿',
    'pending': '审核中',
    'published': '已发布',
    'approved': '已审核通过',
    'rejected': '审核未通过'
  };
  return map[status] || '未知状态';
};

// 获取实践类型文本
const getPracticeTypeText = (type: string) => {
  const map: Record<string, string> = {
    'code': '在线编码实践',
    'desktop': '云桌面实践'
  };
  return map[type] || '未知类型';
};

// 格式化日期
const formatDate = (date: Date) => {
  if (!date) return '未知';
  return dayjs(date).format('YYYY-MM-DD');
};

// 返回上一页
const goBack = () => {
  router.go(-1);
};

// 编辑实践
const editPractice = () => {
  router.push(`/course/practice/${practiceInfo.id}/edit`);
};

// 开启编辑（已发布状态）
const handleStartEdit = async () => {
  Modal.confirm({
    title: '确认开启编辑',
    content: `确定要开启「${practiceInfo.name}」的编辑吗？开启后将创建新的编辑版本，当前发布内容保持不变。`,
    okText: '确认开启',
    cancelText: '取消',
    onOk: async () => {
      try {
        const success = await startEditMode(practiceInfo.id);
        if (success) {
          message.success('已开启编辑模式');
          // 跳转到编辑页面
          router.push(`/course/practice/${practiceInfo.id}/edit`);
        } else {
          message.error('开启编辑失败，请稍后重试');
        }
      } catch (error) {
        console.error('开启编辑失败:', error);
        message.error('开启编辑失败，请稍后重试');
      }
    }
  });
};

// 克隆实践
const handleClonePractice = () => {
  Modal.confirm({
    title: '确认克隆',
    content: `确定要克隆实践课程「${practiceInfo.name}」吗？`,
    okText: '克隆',
    cancelText: '取消',
    onOk: async () => {
      try {
        const result = await clonePractice(practiceInfo.id);
        if (result && result.id) {
          message.success('克隆成功');
          // 跳转到新实践的编辑页面
          router.push(`/course/practice/${result.id}/edit`);
        } else {
          message.error('克隆失败，请稍后重试');
        }
      } catch (error) {
        console.error('克隆失败:', error);
        message.error('克隆失败，请稍后重试');
      }
    }
  });
};

// 显示添加到课堂模态框
const showAddToClassroomModal = () => {
  addToClassroomVisible.value = true;
};

// 添加到课堂
const addToClassroom = async () => {
  if (!selectedClassroomId.value) {
    message.warning('请选择一个课堂');
    return;
  }
  
  addingToClassroom.value = true;
  
  try {
    // 这里应该调用API将实践添加到课堂
    await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟API调用延迟
    
    const classroomName = myClassrooms.value.find(c => c.id === selectedClassroomId.value)?.name || '选中的课堂';
    
    message.success(`成功将《${practiceInfo.name}》添加到课堂"${classroomName}"`);
    addToClassroomVisible.value = false;
    selectedClassroomId.value = '';
  } catch (error) {
    console.error('添加到课堂失败:', error);
    message.error('添加到课堂失败，请稍后重试');
  } finally {
    addingToClassroom.value = false;
  }
};

// 加载实践详情
const loadPracticeDetail = async () => {
  loading.value = true;
  try {
    const practiceId = route.params.id;
    const response = await get(`/api/v1/practices/${practiceId}`);
    if (response?.code === '0000' && response.data) {
      const data = response.data;
      practiceInfo.id = String(data.id);
      practiceInfo.name = data.title || '';
      practiceInfo.introduction = data.description || '';
      practiceInfo.difficulty = data.difficulty || '';
      practiceInfo.type = 'code';
      practiceInfo.status = 'published';
      practiceInfo.author = '';
      practiceInfo.createdAt = data.created_at ? new Date(data.created_at) : null;
      practiceInfo.updatedAt = data.updated_at ? new Date(data.updated_at) : null;
      practiceInfo.tasks = (data.tasks || []).map((t: any) => ({
        id: String(t.id),
        title: t.title || '',
        description: t.task_type ? `类型: ${t.task_type}` + (t.difficulty ? ` | 难度: ${t.difficulty}` : '') + (t.coin ? ` | 积分: ${t.coin}` : '') : ''
      }));
    }
  } catch (error) {
    console.error('加载实践详情失败:', error);
    message.error('加载实践详情失败');
  } finally {
    loading.value = false;
  }
};

// 加载我的课堂列表
const loadMyClassrooms = async () => {
  try {
    const response = await get('/api/v1/classrooms', { page: 1, page_size: 50 });
    if (response?.code === '0000' && response.data?.items) {
      myClassrooms.value = response.data.items.map((c: any) => ({
        id: String(c.id),
        name: c.name || '',
        description: c.description || ''
      }));
    }
  } catch (error) {
    console.error('加载课堂列表失败:', error);
  }
};

// 页面初始化
onMounted(() => {
  loadPracticeDetail();
  loadMyClassrooms();
});
</script>

<style scoped>
.practice-detail-page {
  background-color: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.page-content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.practice-info-card,
.practice-meta-card {
  margin-bottom: 24px;
}

.practice-meta-card :deep(.ant-descriptions-item-label) {
  font-weight: 500;
}

/* 添加到课堂模态框样式 */
.add-to-classroom-content {
  padding: 0 16px;
}

.classroom-list {
  max-height: 300px;
  overflow-y: auto;
  margin: 16px 0;
  border: 1px solid #f0f0f0;
  border-radius: 2px;
  padding: 8px;
}

.classroom-radio-group {
  width: 100%;
}

.classroom-item {
  padding: 8px 0;
}

.classroom-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.classroom-desc {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.add-classroom-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}
</style> 