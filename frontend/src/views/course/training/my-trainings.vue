<template>
  <div class="my-trainings-page">
    <div class="page-header">
      <div class="header-content">
        <div class="left-content">
          <h2>我创建的实训</h2>
          <p class="training-count">共创建 {{ trainings.length }} 个实训项目{{ searchKeyword || statusFilter || typeFilter ? `，当前显示 ${filteredTrainings.length} 个` : '' }}</p>
        </div>
        <a-space>
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索实训名称"
            style="width: 250px"
            @search="handleSearch"
          />
          <a-select
            v-model:value="typeFilter"
            style="width: 150px"
            placeholder="类型筛选"
            @change="handleTypeFilterChange"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="bi">BI可视化分析</a-select-option>
            <a-select-option value="ai">AI机器学习</a-select-option>
            <a-select-option value="jupyter">Jupyter编码式</a-select-option>
          </a-select>
          <a-select
            v-model:value="statusFilter"
            style="width: 150px"
            placeholder="状态筛选"
            @change="handleStatusFilterChange"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="draft">编辑中（创建未发布）</a-select-option>
            <a-select-option value="editing">编辑中（发布后编辑）</a-select-option>
            <a-select-option value="pending">审核中</a-select-option>
            <a-select-option value="published_personal">已发布（个人）</a-select-option>
            <a-select-option value="published_public">已发布（公开）</a-select-option>
            <a-select-option value="rejected">审核未通过</a-select-option>
          </a-select>
          <a-button type="primary" @click="createNewTraining">
            <template #icon><PlusOutlined /></template>
            新建实训
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="page-content">
      <a-spin :spinning="loading">
        <a-empty v-if="trainings.length === 0" description="暂无实训课程，点击上方按钮创建" />
        
        <div v-else class="trainings-list">
          <a-list
            :data-source="filteredTrainings"
            :pagination="pagination"
            :grid="{ gutter: 24, column: 3 }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card hoverable class="training-card" @click="handleCardClick(item)">
                  <template #cover>
                    <div class="card-cover-container">
                      <img alt="课程封面" :src="item.cover || getDefaultCover(item.type)" />
                      <a-tag class="status-tag" :color="getStatusColor(item.status)">
                        {{ getStatusText(item.status, item.statusDetail) }}
                      </a-tag>
                      <a-tag class="type-tag" :color="getTypeColor(item.type)">
                        {{ getTypeText(item.type) }}
                      </a-tag>
                    </div>
                  </template>
                  <a-card-meta :title="item.title || item.name">
                    <template #description>
                      <div class="training-card-desc">
                        <div class="training-intro" :title="item.intro">
                          {{ truncateText(item.intro || '', 80) }}
                        </div>
                        <div class="training-meta">
                          <div class="meta-info">
                            <a-tag>{{ getDifficultyText(item.difficulty) }}</a-tag>
                            <a-tag v-if="item.duration">{{ item.duration }}分钟</a-tag>
                            <a-tag v-if="item.version">v{{ item.version }}</a-tag>
                          </div>
                          <span class="update-time">更新于 {{ formatDate(item.updateTime || item.createTime) }}</span>
                        </div>
                      </div>
                    </template>
                  </a-card-meta>
                  <a-dropdown :trigger="['click']" placement="bottomRight" @click.stop="" overlayClassName="training-dropdown">
                    <template #overlay>
                      <a-menu @click="onMenuClick($event, item)">
                        <!-- 查看/编辑选项 - 根据不同状态显示不同的默认操作 -->
                        <a-menu-item v-if="canView(item)" key="view">
                          <EyeOutlined />查看详情
                        </a-menu-item>
                        <a-menu-item v-if="canEdit(item)" key="edit">
                          <EditOutlined />编辑
                        </a-menu-item>
                        <a-menu-item key="clone">
                          <CopyOutlined />克隆
                        </a-menu-item>
                        
                        <!-- 已发布（个人）状态的选项 -->
                        <a-menu-item v-if="item.status === 'published_personal'" key="addToClassroom">
                          <PlusCircleOutlined />添加到课堂
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'published_personal'" key="openEdit">
                          <FormOutlined />开启编辑
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'published_personal'" key="applyPublic">
                          <CloudUploadOutlined />公开发布
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'published_personal'" key="unpublish">
                          <CloudDownloadOutlined />下架
                        </a-menu-item>
                        
                        <!-- 已发布（公开）状态的选项 -->
                        <a-menu-item v-if="item.status === 'published_public'" key="addToClassroom">
                          <PlusCircleOutlined />添加到课堂
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'published_public'" key="openEdit">
                          <FormOutlined />开启编辑
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'published_public'" key="cancelPublic">
                          <RollbackOutlined />撤销公开
                        </a-menu-item>
                        
                        <!-- 编辑中（发布后编辑）状态的选项 -->
                        <a-menu-item v-if="item.status === 'editing'" key="publishNewVersion">
                          <CloudUploadOutlined />发布新版本
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'editing'" key="cancelEdit">
                          <UndoOutlined />撤销编辑
                        </a-menu-item>
                        
                        <!-- 审核中状态的选项 -->
                        <a-menu-item v-if="item.status === 'pending'" key="cancelPending">
                          <StopOutlined />撤销申请
                        </a-menu-item>
                        
                        <!-- 编辑中（创建未发布）状态的选项 -->
                        <a-menu-item v-if="item.status === 'draft'" key="publish">
                          <CloudUploadOutlined />发布
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'draft'" key="delete">
                          <DeleteOutlined />删除
                        </a-menu-item>
                        
                        <!-- 审核未通过状态的选项 -->
                        <a-menu-item v-if="item.status === 'rejected'" key="viewReason">
                          <InfoCircleOutlined />查看原因
                        </a-menu-item>
                        <a-menu-item v-if="item.status === 'rejected'" key="reapply">
                          <ReloadOutlined />重新申请
                        </a-menu-item>
                      </a-menu>
                    </template>
                    <a-button class="more-btn" type="text" @click.stop="">
                      <EllipsisOutlined style="font-size: 20px" />
                    </a-button>
                  </a-dropdown>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-spin>
    </div>
    
    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="确认删除"
      :okText="'删除'"
      :cancelText="'取消'"
      @ok="handleDeleteTraining"
    >
      <p>确定要删除实训课程「{{ trainingToDelete?.title || trainingToDelete?.name }}」吗？</p>
      <p>此操作不可恢复，删除后该实训课程的所有内容将被清除。</p>
    </a-modal>
    
    <!-- 发布新版本弹窗 -->
    <a-modal
      v-model:open="publishVersionModalVisible"
      title="发布新版本"
      :okText="'发布'"
      :cancelText="'取消'"
      @ok="handlePublishNewVersion"
    >
      <div class="publish-version-form">
        <p>您正在为「{{ selectedTraining?.title || selectedTraining?.name }}」发布新版本</p>
        
        <a-form :model="versionForm" layout="vertical">
          <a-form-item label="版本升级类型" name="versionType">
            <a-radio-group v-model:value="versionForm.versionType">
              <a-radio value="minor">小版本升级</a-radio>
              <a-radio value="major">大版本升级</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <a-form-item 
            label="更新内容" 
            name="updateNotes"
            :rules="[{ required: true, message: '请输入本次更新的内容' }]"
          >
            <a-textarea 
              v-model:value="versionForm.updateNotes" 
              placeholder="请描述本次更新的主要内容..." 
              :rows="4"
              :maxLength="500"
              showCount
            />
          </a-form-item>
          
          <a-form-item v-if="needPublicApproval" label="发布方式" name="publishType">
            <a-radio-group v-model:value="versionForm.publishType">
              <a-radio value="personal">个人发布</a-radio>
              <a-radio value="public">公开发布</a-radio>
            </a-radio-group>
            <div v-if="versionForm.publishType === 'public'" class="publish-tip">
              <a-alert message="公开发布需要管理员审核通过后才能生效" type="info" showIcon />
            </div>
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
    
    <!-- 撤销编辑确认弹窗 -->
    <a-modal
      v-model:open="cancelEditModalVisible"
      title="确认撤销编辑"
      :okText="'确认撤销'"
      :cancelText="'取消'"
      @ok="handleCancelEdit"
    >
      <p>确定要撤销对「{{ selectedTraining?.title || selectedTraining?.name }}」的编辑吗？</p>
      <p>撤销后将恢复到上一次发布的版本，所有未保存的修改将丢失。</p>
    </a-modal>
    
    <!-- 下架确认弹窗 -->
    <a-modal
      v-model:open="unpublishModalVisible"
      title="确认下架"
      :okText="'确认下架'"
      :cancelText="'取消'"
      @ok="handleUnpublish"
    >
      <p>确定要下架「{{ selectedTraining?.title || selectedTraining?.name }}」吗？</p>
      <p>下架后该实训将变为"编辑中"状态，仅自己可见，无法被学生访问。</p>
    </a-modal>
    
    <!-- 撤销公开确认弹窗 -->
    <a-modal
      v-model:open="cancelPublicModalVisible"
      title="确认撤销公开发布"
      :okText="'确认申请'"
      :cancelText="'取消'"
      @ok="handleCancelPublic"
    >
      <p>确定要申请撤销「{{ selectedTraining?.title || selectedTraining?.name }}」的公开发布吗？</p>
      <p>申请提交后需要等待管理员审核，审核通过后该实训将从课程库中移除，变为个人发布状态。</p>
      <a-form :model="cancelPublicForm" layout="vertical">
        <a-form-item 
          label="撤销原因" 
          name="reason"
          :rules="[{ required: true, message: '请输入撤销公开发布的原因' }]"
        >
          <a-textarea 
            v-model:value="cancelPublicForm.reason" 
            placeholder="请描述撤销公开发布的原因..." 
            :rows="3"
            :maxLength="200"
            showCount
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal, Radio } from 'ant-design-vue';
import dayjs from 'dayjs';
import { 
  PlusOutlined, 
  EyeOutlined, 
  EditOutlined, 
  DeleteOutlined,
  EllipsisOutlined,
  PlusCircleOutlined,
  FormOutlined,
  CloudUploadOutlined,
  CloudDownloadOutlined,
  RollbackOutlined,
  UndoOutlined,
  StopOutlined,
  InfoCircleOutlined,
  ReloadOutlined,
  CopyOutlined
} from '@ant-design/icons-vue';
import { 
  fetchMyTrainings, 
  deleteTrainingById, 
  updateTrainingStatusById,
  startEditModeTraining,
  cancelEditTraining,
  unpublishTraining,
  applyPublicPublishTraining,
  cancelPublicPublishTraining,
  publishNewTrainingVersion,
  cloneTraining,
  type TrainingItem,
  type TrainingStatusType,
  type TrainingVersionData
} from '@/api/training';

const router = useRouter();
const loading = ref(false);
const searchKeyword = ref('');
const statusFilter = ref('');
const typeFilter = ref('');
const trainings = ref<TrainingItem[]>([]);
const deleteModalVisible = ref(false);
const trainingToDelete = ref<TrainingItem | null>(null);
const selectedTraining = ref<TrainingItem | null>(null);

// 更多操作相关模态框
const publishVersionModalVisible = ref(false);
const cancelEditModalVisible = ref(false);
const unpublishModalVisible = ref(false);
const cancelPublicModalVisible = ref(false);

// 表单
const versionForm = ref({
  versionType: 'minor',
  updateNotes: '',
  publishType: 'personal'
});

const cancelPublicForm = ref({
  reason: ''
});

// 判断是否需要公开发布审批
const needPublicApproval = computed(() => {
  // 如果当前版本是个人发布，则需要选择发布方式
  return selectedTraining.value?.status === 'published_personal' || 
    selectedTraining.value?.status === 'editing';
});

// 分页配置
const pagination = {
  pageSize: 9,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`
};

// 筛选实训列表
const filteredTrainings = computed(() => {
  let result = trainings.value;
  
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(item => 
      (item.title || item.name || '').toLowerCase().includes(keyword) || 
      (item.intro || '').toLowerCase().includes(keyword)
    );
  }
  
  if (statusFilter.value) {
    result = result.filter(item => item.status === statusFilter.value);
  }
  
  if (typeFilter.value) {
    result = result.filter(item => item.type === typeFilter.value);
  }
  
  return result;
});

// 获取默认封面
const getDefaultCover = (type: string) => {
  const covers: Record<string, string> = {
    'bi': 'https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png',
    'ai': 'https://gw.alipayobjects.com/zos/rmsportal/mqaQswcyDLcXyDKnZfES.png',
    'jupyter': 'https://gw.alipayobjects.com/zos/rmsportal/QBnOOoLaAfKPirc.png'
  };
  return covers[type] || covers['bi'];
};

// 获取类型文本
const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    'bi': 'BI可视化',
    'ai': 'AI机器学习',
    'jupyter': 'Jupyter编码'
  };
  return map[type] || '未知类型';
};

// 获取类型颜色
const getTypeColor = (type: string) => {
  const map: Record<string, string> = {
    'bi': 'blue',
    'ai': 'purple',
    'jupyter': 'orange'
  };
  return map[type] || 'default';
};

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
    'draft': 'default', // 编辑中（创建但未发布）
    'editing': 'processing', // 编辑中（发布后编辑）
    'pending': 'warning', // 审核中
    'published_personal': 'success', // 已发布（个人）
    'published_public': 'success', // 已发布（公开）
    'rejected': 'error' // 审核未通过
  };
  return map[status] || 'default';
};

// 获取状态文本
const getStatusText = (status: string, detail?: string) => {
  const map: Record<string, string> = {
    'draft': '编辑中',
    'editing': '编辑中',
    'pending': '审核中',
    'published_personal': '已发布',
    'published_public': '已发布',
    'rejected': '审核未通过'
  };
  
  const baseText = map[status] || '未知状态';
  
  // 如果有详细状态，拼接在后面
  if (detail) {
    return `${baseText}（${detail}）`;
  }
  
  // 否则根据状态添加默认的详细描述
  if (status === 'published_personal') {
    return `${baseText}（个人）`;
  } else if (status === 'published_public') {
    return `${baseText}（公开）`;
  } else if (status === 'draft') {
    return `${baseText}（创建未发布）`;
  } else if (status === 'editing') {
    return `${baseText}（发布后编辑）`;
  }
  
  return baseText;
};

// 格式化日期
const formatDate = (date: string | Date) => {
  if (!date) return '未知';
  return dayjs(date).format('YYYY-MM-DD');
};

// 截断文本
const truncateText = (text: string, maxLength: number) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

// 搜索
const handleSearch = () => {
  // 搜索功能由filteredTrainings计算属性自动处理，这里可以添加额外的搜索逻辑
  console.log('搜索关键词:', searchKeyword.value);
};

// 状态筛选改变
const handleStatusFilterChange = () => {
  // 筛选功能由filteredTrainings计算属性自动处理，这里可以添加额外的筛选逻辑
  console.log('状态筛选:', statusFilter.value);
};

// 类型筛选改变
const handleTypeFilterChange = () => {
  // 筛选功能由filteredTrainings计算属性自动处理，这里可以添加额外的筛选逻辑
  console.log('类型筛选:', typeFilter.value);
};

// 新建实训
const createNewTraining = () => {
  router.push('/course/training/create');
};

// 判断是否可以查看（已发布状态的课程）
const canView = (training: TrainingItem) => {
  return training.status === 'published_personal' || 
    training.status === 'published_public';
};

// 判断是否可以编辑（编辑中状态的课程）
const canEdit = (training: TrainingItem) => {
  return training.status === 'draft' || 
    training.status === 'editing' || 
    training.status === 'rejected';
};

// 处理卡片点击
const handleCardClick = (training: TrainingItem) => {
  // 根据状态不同，点击卡片执行不同的默认操作
  if (canView(training)) {
    viewTraining(training);
  } else if (canEdit(training)) {
    editTraining(training);
  }
};

// 查看实训详情
const viewTraining = (training: TrainingItem) => {
  // 根据实训类型跳转到不同的页面
  switch (training.type) {
    case 'bi':
      router.push(`/visual?trainingId=${training.id}`);
      break;
    case 'ai':
      router.push(`/ml?trainingId=${training.id}`);
      break;
    case 'jupyter':
      router.push(`/project/jupyter/${training.id}`);
      break;
    default:
      router.push(`/course/training/${training.id}`);
  }
};

// 编辑实训
const editTraining = (training: TrainingItem) => {
  router.push(`/course/training/${training.id}/edit`);
};

// 处理菜单点击事件
const onMenuClick = (event: { key: string }, training: TrainingItem) => {
  selectedTraining.value = training;
  
  handleMenuClick(event.key, training);
};

// 处理菜单点击
const handleMenuClick = (key: string, training: TrainingItem) => {
  selectedTraining.value = training;
  
  switch (key) {
    case 'view':
      viewTraining(training);
      break;
    case 'edit':
      editTraining(training);
      break;
    case 'clone':
      confirmCloneTraining(training);
      break;
    case 'delete':
      confirmDeleteTraining(training);
      break;
    case 'addToClassroom':
      // 跳转到添加课堂页面
      router.push({
        path: '/classroom',
        query: { addTraining: training.id }
      });
      break;
    case 'openEdit':
      // 开启编辑，将状态更改为"编辑中"
      handleStartEdit(training);
      break;
    case 'publish':
      // 简单发布，显示发布选项
      showPublishOptions(training);
      break;
    case 'publishNewVersion':
      // 显示发布新版本模态框
      selectedTraining.value = training;
      publishVersionModalVisible.value = true;
      break;
    case 'applyPublic':
      // 申请公开发布
      handleApplyPublic(training);
      break;
    case 'cancelPublic':
      // 显示撤销公开模态框
      selectedTraining.value = training;
      cancelPublicModalVisible.value = true;
      break;
    case 'unpublish':
      // 显示下架确认模态框
      selectedTraining.value = training;
      unpublishModalVisible.value = true;
      break;
    case 'cancelEdit':
      // 显示撤销编辑确认模态框
      selectedTraining.value = training;
      cancelEditModalVisible.value = true;
      break;
    case 'cancelPending':
      // 撤销申请，返回到之前的状态
      Modal.confirm({
        title: '确认撤销申请',
        content: '确定要撤销当前的审核申请吗？撤销后将返回到之前的状态。',
        onOk: () => {
          // 判断之前的状态，如果是编辑中发布后应该回到editing，如果是申请公开发布应该回到personal
          const prevStatus = training.statusDetail?.includes('公开') ? 'published_personal' : 'editing';
          const prevDetail = prevStatus === 'published_personal' ? '个人发布' : '发布后编辑';
          applyStatusChange(training.id, prevStatus as TrainingStatusType, prevDetail);
        }
      });
      break;
    case 'viewReason':
      // 查看审核未通过原因
      Modal.info({
        title: '审核未通过原因',
        content: '您的实训课程未通过审核，原因：内容过于简单，缺乏教学价值，请增加更多有深度的教学内容后再次提交。'
      });
      break;
    case 'reapply':
      // 重新申请公开发布
      Modal.confirm({
        title: '重新申请公开发布',
        content: '确定要重新申请公开发布吗？请确保已经根据审核意见进行了修改。',
        onOk: () => {
          applyStatusChange(training.id, 'pending', '公开发布审核中（重新申请）');
        }
      });
      break;
    default:
      break;
  }
};

// 显示发布选项
const showPublishOptions = (training: TrainingItem) => {
  Modal.confirm({
    title: '选择发布方式',
    content: '请选择发布方式：\n\n个人发布：实训将立即发布，仅您自己可见和使用\n\n公开发布：实训将提交审核，通过后将对所有用户可见',
    okText: '公开发布',
    cancelText: '个人发布',
    onOk: () => {
      // 选择公开发布
      applyStatusChange(training.id, 'pending', '公开发布审核中');
    },
    onCancel: () => {
      // 选择个人发布
      applyStatusChange(training.id, 'published_personal', '个人发布');
    }
  });
};

// 更改状态
const applyStatusChange = async (id: string, status: TrainingStatusType, statusDetail?: string) => {
  loading.value = true;
  
  try {
    const success = await updateTrainingStatusById(id, status, statusDetail);
    
    if (success) {
      // 更新本地数据
      const training = trainings.value.find(p => p.id === id);
      if (training) {
        training.status = status;
        if (statusDetail) {
          training.statusDetail = statusDetail;
        }
      }
      
      // 根据操作类型显示不同的成功消息
      let successMsg = '状态更新成功';
      if (status === 'editing') {
        successMsg = '实训课程已开启编辑模式';
      } else if (status === 'published_personal') {
        successMsg = '实训课程已成功发布，现在可以添加到课堂中使用';
      } else if (status === 'pending') {
        successMsg = '申请已提交，请等待管理员审核';
      } else if (status === 'draft') {
        successMsg = '实训课程已下架';
      }
      
      message.success(successMsg);
    } else {
      message.error('操作失败，请稍后重试');
    }
  } catch (error) {
    console.error('状态更新失败:', error);
    message.error('操作失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 确认删除实训
const confirmDeleteTraining = (training: TrainingItem) => {
  trainingToDelete.value = training;
  deleteModalVisible.value = true;
};

// 确认克隆实训
const confirmCloneTraining = (training: TrainingItem) => {
  Modal.confirm({
    title: '确认克隆',
    content: `确定要克隆实训课程「${training.title || training.name}」吗？`,
    okText: '克隆',
    cancelText: '取消',
    onOk: async () => {
      loading.value = true;
      try {
        const result = await cloneTraining(training.id);
        if (result && result.id) {
          message.success('克隆成功');
          // 跳转到新实训的编辑页面
          router.push(`/course/training/${result.id}/edit`);
        } else {
          message.error('克隆失败，请稍后重试');
        }
      } catch (error) {
        console.error('克隆失败:', error);
        message.error('克隆失败，请稍后重试');
      } finally {
        loading.value = false;
      }
    }
  });
};

// 删除实训
const handleDeleteTraining = async () => {
  if (!trainingToDelete.value) return;
  
  loading.value = true;
  
  try {
    const success = await deleteTrainingById(trainingToDelete.value.id);
    
    if (success) {
      // 从列表中移除被删除的实训
      trainings.value = trainings.value.filter(p => p.id !== trainingToDelete.value?.id);
      
      message.success('实训课程删除成功');
      deleteModalVisible.value = false;
      trainingToDelete.value = null;
    } else {
      message.error('删除失败，请稍后重试');
    }
  } catch (error) {
    console.error('删除失败:', error);
    message.error('删除失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 处理撤销编辑
const handleCancelEdit = async () => {
  if (!selectedTraining.value) return;
  
  loading.value = true;
  
  try {
    const success = await cancelEditTraining(selectedTraining.value.id);
    
    if (success) {
      // 更新本地数据
      const training = trainings.value.find(p => p.id === selectedTraining.value?.id);
      if (training) {
        training.status = 'published_personal';
        training.statusDetail = '个人发布';
      }
      
      message.success('已撤销编辑，实训课程已恢复到上一个发布版本');
      cancelEditModalVisible.value = false;
    } else {
      message.error('操作失败，请稍后重试');
    }
  } catch (error) {
    console.error('撤销编辑失败:', error);
    message.error('操作失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 处理下架
const handleUnpublish = async () => {
  if (!selectedTraining.value) return;
  
  loading.value = true;
  
  try {
    const success = await unpublishTraining(selectedTraining.value.id);
    
    if (success) {
      // 更新本地数据
      const training = trainings.value.find(p => p.id === selectedTraining.value?.id);
      if (training) {
        training.status = 'draft';
        training.statusDetail = '创建未发布';
      }
      
      message.success('实训课程已下架');
      unpublishModalVisible.value = false;
    } else {
      message.error('下架失败，请稍后重试');
    }
  } catch (error) {
    console.error('下架失败:', error);
    message.error('下架失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 处理撤销公开发布
const handleCancelPublic = async () => {
  if (!selectedTraining.value || !cancelPublicForm.value.reason) return;
  
  loading.value = true;
  
  try {
    const success = await cancelPublicPublishTraining(selectedTraining.value.id, cancelPublicForm.value.reason);
    
    if (success) {
      // 更新本地数据
      const training = trainings.value.find(p => p.id === selectedTraining.value?.id);
      if (training) {
        training.status = 'pending';
        training.statusDetail = '撤销公开发布审核中';
      }
      
      message.success('撤销公开发布申请已提交，请等待管理员审核');
      cancelPublicModalVisible.value = false;
      cancelPublicForm.value.reason = '';
    } else {
      message.error('申请提交失败，请稍后重试');
    }
  } catch (error) {
    console.error('申请提交失败:', error);
    message.error('申请提交失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 开启编辑模式
const handleStartEdit = async (training: TrainingItem) => {
  loading.value = true;
  
  try {
    const success = await startEditModeTraining(training.id);
    
    if (success) {
      // 更新本地数据
      const localTraining = trainings.value.find(p => p.id === training.id);
      if (localTraining) {
        localTraining.status = 'editing';
        localTraining.statusDetail = '发布后编辑';
      }
      
      message.success('已开启编辑模式');
      // 跳转到编辑页面
      router.push(`/course/training/${training.id}/edit`);
    } else {
      message.error('开启编辑失败，请稍后重试');
    }
  } catch (error) {
    console.error('开启编辑失败:', error);
    message.error('开启编辑失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 申请公开发布
const handleApplyPublic = async (training: TrainingItem) => {
  Modal.confirm({
    title: '确认申请公开发布',
    content: '申请公开发布需要管理员审核，审核通过后该实训将加入实训课程库，对所有用户可见。确定要申请吗？',
    onOk: async () => {
      loading.value = true;
      
      try {
        const success = await applyPublicPublishTraining(training.id);
        
        if (success) {
          // 更新本地数据
          const localTraining = trainings.value.find(p => p.id === training.id);
          if (localTraining) {
            localTraining.status = 'pending';
            localTraining.statusDetail = '公开发布审核中';
          }
          
          message.success('公开发布申请已提交，请等待管理员审核');
        } else {
          message.error('申请提交失败，请稍后重试');
        }
      } catch (error) {
        console.error('申请提交失败:', error);
        message.error('申请提交失败，请稍后重试');
      } finally {
        loading.value = false;
      }
    }
  });
};

// 发布新版本
const handlePublishNewVersion = async () => {
  if (!selectedTraining.value || !versionForm.value.updateNotes) {
    message.error('请填写更新说明');
    return;
  }
  
  loading.value = true;
  
  try {
    const versionData: TrainingVersionData = {
      versionType: versionForm.value.versionType as 'major' | 'minor',
      updateNotes: versionForm.value.updateNotes,
      publishType: versionForm.value.publishType as 'personal' | 'public'
    };
    
    const success = await publishNewTrainingVersion(selectedTraining.value.id, versionData);
    
    if (success) {
      // 更新本地数据
      const training = trainings.value.find(p => p.id === selectedTraining.value?.id);
      if (training) {
        training.status = versionData.publishType === 'public' ? 'pending' : 'published_personal';
        training.statusDetail = versionData.publishType === 'public' ? '公开发布审核中' : '个人发布';
      }
      
      const successMsg = versionData.publishType === 'public' 
        ? '新版本已提交审核，请等待管理员审核' 
        : '新版本发布成功';
      message.success(successMsg);
      publishVersionModalVisible.value = false;
      resetForms();
    } else {
      message.error('发布失败，请稍后重试');
    }
  } catch (error) {
    console.error('发布失败:', error);
    message.error('发布失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 重置表单
const resetForms = () => {
  versionForm.value = {
    versionType: 'minor',
    updateNotes: '',
    publishType: 'personal'
  };
  
  cancelPublicForm.value = {
    reason: ''
  };
};

// 加载我创建的实训列表
const loadMyTrainings = async () => {
  loading.value = true;

  try {
    console.log('=== 开始加载实训列表 ===');
    // 手动测试API调用
    const testResponse = await fetch('/api/v1/trainings/my-trainings');
    console.log('Test API response status:', testResponse.status);
    const testData = await testResponse.json();
    console.log('Test API response data:', testData);

    // 调用API获取用户创建的实训列表
    const result = await fetchMyTrainings();
    console.log('fetchMyTrainings result:', result);
    trainings.value = result;
  } catch (error) {
    console.error('加载失败:', error);
    message.error('加载实训列表失败，请刷新页面重试');
  } finally {
    loading.value = false;
  }
};

// 页面初始化
onMounted(() => {
  // 调试代码：检查token状态
  console.log('=== 实训列表页面调试信息 ===');
  console.log('localStorage token:', localStorage.getItem('token'));
  console.log('sessionStorage huixue_token:', sessionStorage.getItem('huixue_token'));
  console.log('document.cookie:', document.cookie);

  // 测试getToken函数
  import('@/utils/auth').then(({ getToken }) => {
    const token = getToken();
    console.log('getToken() result:', token);
    console.log('Token length:', token?.length);
  });

  loadMyTrainings();
});
</script>

<style scoped>
.my-trainings-page {
  background-color: #f0f2f5;
  min-height: 100vh;
}

.page-header {
  background-color: #fff;
  padding: 24px 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
}

.left-content {
  display: flex;
  flex-direction: column;
}

.left-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.training-count {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.page-content {
  max-width: 1200px;
  margin: 24px auto;
  padding: 0 24px;
}

.trainings-list {
  margin-top: 16px;
}

.training-card {
  height: 100%;
  transition: all 0.3s;
  position: relative;
}

.training-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.card-cover-container {
  position: relative;
  height: 160px;
  overflow: hidden;
  background-color: #f5f5f5;
}

.card-cover-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 12px;
}

.type-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  font-size: 12px;
}

.training-card-desc {
  display: flex;
  flex-direction: column;
  height: 110px;
}

.training-intro {
  flex: 1;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.65);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.training-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-info {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.meta-info :deep(.ant-tag) {
  margin-right: 0;
}

.update-time {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.more-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 发布新版本表单 */
.publish-version-form {
  padding: 0 16px;
}

.publish-tip {
  margin-top: 8px;
}

/* 让弹出菜单更宽一些 */
:deep(.training-dropdown .ant-dropdown-menu) {
  min-width: 160px;
}

:deep(.training-dropdown .ant-dropdown-menu-item) {
  padding: 8px 12px;
}
</style>