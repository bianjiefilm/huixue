<template>
  <PageShell max-width="wide" class="myprojects-page">
    <PageHeaderBar
      title="我创建的实训"
      subtitle="管理您创建的所有实训项目，包括公开发布的和草稿状态的实训"
      show-back
      back-to="/project"
    >
      <template #actions>
        <a-button type="primary" @click="handleCreateNew">
          <plus-outlined />
          新建实训
        </a-button>
      </template>
    </PageHeaderBar>

    <a-card class="projects-card">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="published" tab="已发布">
          <a-spin :spinning="loading" tip="加载中...">
            <a-table 
              :columns="columns" 
              :data-source="publishedProjects" 
              :pagination="pagination"
              @change="handleTableChange"
            >
              <template #bodyCell="{ column, record }">
                <!-- 实训类型 -->
                <template v-if="column.key === 'type'">
                  <a-tag :color="record.type === 'dragdrop' ? 'blue' : 'green'">
                    {{ record.type === 'dragdrop' ? '拖拽式' : '编码式' }}
                  </a-tag>
                </template>
                
                <!-- 审核状态 -->
                <template v-if="column.key === 'status'">
                  <a-tag :color="getStatusColor(record.status)">
                    {{ getStatusText(record.status) }}
                  </a-tag>
                </template>
                
                <!-- 操作列 -->
                <template v-if="column.key === 'action'">
                  <a-button type="link" @click="viewProject(record)">查看</a-button>
                  <a-divider type="vertical" />
                  <a-button type="link" @click="editProject(record)">编辑</a-button>
                  <a-divider type="vertical" />
                  <a-dropdown>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="copy" @click="copyProject(record)">
                          <copy-outlined />
                          复制
                        </a-menu-item>
                        <a-menu-item key="delete" @click="confirmDelete(record)">
                          <delete-outlined />
                          删除
                        </a-menu-item>
                      </a-menu>
                    </template>
                    <a-button type="link">
                      更多 <down-outlined />
                    </a-button>
                  </a-dropdown>
                </template>
              </template>
            </a-table>
          </a-spin>
        </a-tab-pane>
        
        <a-tab-pane key="draft" tab="草稿箱">
          <a-spin :spinning="loading" tip="加载中...">
            <a-table 
              :columns="draftColumns" 
              :data-source="draftProjects" 
              :pagination="pagination"
              @change="handleTableChange"
            >
              <template #bodyCell="{ column, record }">
                <!-- 实训类型 -->
                <template v-if="column.key === 'type'">
                  <a-tag :color="record.type === 'dragdrop' ? 'blue' : 'green'">
                    {{ record.type === 'dragdrop' ? '拖拽式' : '编码式' }}
                  </a-tag>
                </template>
                
                <!-- 操作列 -->
                <template v-if="column.key === 'action'">
                  <a-button type="link" @click="continueEdit(record)">继续编辑</a-button>
                  <a-divider type="vertical" />
                  <a-button type="link" @click="publishDraft(record)">发布</a-button>
                  <a-divider type="vertical" />
                  <a-dropdown>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="copy" @click="copyProject(record)">
                          <copy-outlined />
                          复制
                        </a-menu-item>
                        <a-menu-item key="delete" @click="confirmDelete(record)">
                          <delete-outlined />
                          删除
                        </a-menu-item>
                      </a-menu>
                    </template>
                    <a-button type="link">
                      更多 <down-outlined />
                    </a-button>
                  </a-dropdown>
                </template>
              </template>
            </a-table>
          </a-spin>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { 
  PlusOutlined, 
  DeleteOutlined, 
  CopyOutlined,
  DownOutlined
} from '@ant-design/icons-vue';
import { fetchMyTrainings, deleteTrainingById, publishTraining, unpublishTraining, type TrainingItem, type TrainingStatusType } from '@/api/training';
import { useUserStore } from '@/stores/user';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const router = useRouter();
const loading = ref(false);
const activeTab = ref('published');
const projects = ref([]);

// 用户store
const userStore = useUserStore();

// 所有实训数据
const allTrainings = ref<TrainingItem[]>([]);

// 状态映射到前端格式
const statusMapping: Record<TrainingStatusType, string> = {
  'draft': 'draft',
  'editing': 'draft',
  'pending': 'pending',
  'published_personal': 'approved',
  'published_public': 'approved',
  'rejected': 'rejected'
};

// 类型映射
const typeMapping: Record<string, string> = {
  'CODING': 'coding',
  'DRAG_DROP': 'dragdrop'
};

// 表格列定义
const columns = [
  {
    title: '实训名称',
    dataIndex: 'name',
    key: 'name',
    sorter: true,
  },
  {
    title: '实训类型',
    dataIndex: 'type',
    key: 'type',
    filters: [
      { text: '拖拽式', value: 'dragdrop' },
      { text: '编码式', value: 'coding' },
    ],
  },
  {
    title: '所属行业',
    dataIndex: 'industry',
    key: 'industry',
  },
  {
    title: '难度',
    dataIndex: 'difficulty',
    key: 'difficulty',
    filters: [
      { text: '初级', value: 'basic' },
      { text: '中级', value: 'intermediate' },
      { text: '高级', value: 'advanced' },
    ],
  },
  {
    title: '审核状态',
    dataIndex: 'status',
    key: 'status',
    filters: [
      { text: '审核中', value: 'pending' },
      { text: '已通过', value: 'approved' },
      { text: '已拒绝', value: 'rejected' },
    ],
  },
  {
    title: '创建时间',
    dataIndex: 'createTime',
    key: 'createTime',
    sorter: true,
  },
  {
    title: '操作',
    key: 'action',
  },
];

// 草稿表格列定义 - 不需要审核状态列
const draftColumns = columns.filter(col => col.key !== 'status');

// 分页配置
const pagination = ref({
  current: 1,
  pageSize: 10,
  showSizeChanger: true,
  showQuickJumper: true,
  total: 0,
  showTotal: (total: number) => `共 ${total} 条`
});

// 根据当前tab过滤项目
const publishedProjects = computed(() => {
  return allTrainings.value.filter(t => 
    t.status === 'published_personal' || 
    t.status === 'published_public' || 
    t.status === 'pending' || 
    t.status === 'rejected'
  ).map(t => ({
    id: t.id,
    name: t.title || t.name,
    type: typeMapping[t.type] || t.type,
    industry: t.categories?.[0] || t.direction || '',
    difficulty: t.difficulty,
    status: statusMapping[t.status] || 'pending',
    createTime: t.createTime
  }));
});

const draftProjects = computed(() => {
  return allTrainings.value.filter(t => 
    t.status === 'draft' || t.status === 'editing'
  ).map(t => ({
    id: t.id,
    name: t.title || t.name,
    type: typeMapping[t.type] || t.type,
    industry: t.categories?.[0] || t.direction || '',
    difficulty: t.difficulty,
    createTime: t.createTime
  }));
});

// 获取状态对应的颜色
const getStatusColor = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'orange',
    'approved': 'green',
    'rejected': 'red',
  };
  return statusMap[status] || 'default';
};

// 获取状态对应的文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '审核中',
    'approved': '已通过',
    'rejected': '已拒绝',
  };
  return statusMap[status] || '未知状态';
};

// 表格变化处理
const handleTableChange = (pag: any, filters: any, sorter: any) => {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  
  // 在实际应用中，这里应该调用API重新获取数据
  console.log('表格变化:', pag, filters, sorter);
};

// 处理新建实训
const handleCreateNew = () => {
  router.push('/project/create');
};

// 查看项目
const viewProject = (record: any) => {
  router.push(`/project/${record.id}`);
};

// 编辑项目
const editProject = (record: any) => {
  const route = record.type === 'dragdrop' 
    ? `/project/create/dragdrop?id=${record.id}` 
    : `/project/create/coding?id=${record.id}`;
  router.push(route);
};

// 继续编辑草稿
const continueEdit = (record: any) => {
  const route = record.type === 'dragdrop' 
    ? `/project/create/dragdrop?id=${record.id}&draft=true` 
    : `/project/create/coding?id=${record.id}&draft=true`;
  router.push(route);
};

// 发布草稿
const publishDraft = (record: any) => {
  Modal.confirm({
    title: '确认发布',
    content: `确定要发布"${record.name}"吗？发布后将提交审核。`,
    onOk: async () => {
      try {
        const success = await publishTraining(Number(record.id), { visibility: 'private' });
        if (success) {
          message.success('发布成功，等待审核');
          await fetchProjects();
        } else {
          message.error('发布失败，请重试');
        }
      } catch (error) {
        message.error('发布失败，请重试');
      }
    },
  });
};

// 复制项目
const copyProject = (record: any) => {
  Modal.confirm({
    title: '确认复制',
    content: `确定要复制"${record.name}"吗？这将创建一个相同内容的草稿。`,
    onOk: async () => {
      try {
        // TODO: 实现复制功能API
        message.info('复制功能开发中');
      } catch (error) {
        message.error('复制失败，请重试');
      }
    },
  });
};

// 确认删除
const confirmDelete = (record: any) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除"${record.name}"吗？删除后不可恢复。`,
    okType: 'danger',
    onOk: async () => {
      try {
        const success = await deleteTrainingById(record.id);
        if (success) {
          message.success('删除成功');
          await fetchProjects();
        } else {
          message.error('删除失败，请重试');
        }
      } catch (error) {
        message.error('删除失败，请重试');
      }
    },
  });
};

// 获取项目列表
const fetchProjects = async () => {
  try {
    loading.value = true;
    
    // 调用真实API获取数据
    const trainings = await fetchMyTrainings();
    allTrainings.value = trainings;
    
    // 设置总数
    pagination.value.total = activeTab.value === 'published' 
      ? publishedProjects.value.length 
      : draftProjects.value.length;
  } catch (error) {
    console.error('获取项目列表失败:', error);
    message.error('获取数据失败，请刷新页面重试');
  } finally {
    loading.value = false;
  }
};

// 监听tab变化
const handleTabChange = () => {
  pagination.value.current = 1;
  fetchProjects();
};

// 生命周期钩子
onMounted(() => {
  fetchProjects();
});
</script>

<style scoped>
.myprojects-page {
  min-height: 100%;
}

.projects-card {
  margin-bottom: var(--hx-space-5);
}
</style> 