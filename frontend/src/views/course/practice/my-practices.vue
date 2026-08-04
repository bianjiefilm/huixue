<template>
  <PageShell max-width="wide" class="my-practices-page">
    <PageHeaderBar
      title="我创建的实践"
      :subtitle="`共创建 ${practices.length} 个实践项目${searchKeyword || statusFilter ? `，当前显示 ${filteredPractices.length} 个` : ''}`"
    >
      <template #actions>
        <a-button type="primary" @click="createNewPractice">
          <template #icon><PlusOutlined /></template>
          新建实践
        </a-button>
      </template>
    </PageHeaderBar>

    <Stack direction="horizontal" :gap="3" class="practice-filters">
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="搜索实践名称"
        style="width: 250px"
        allow-clear
        @search="handleSearch"
      />
      <a-select
        v-model:value="statusFilter"
        style="width: 180px"
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
    </Stack>

    <a-spin :spinning="loading">
      <EmptyStateBlock
        v-if="!loading && practices.length === 0"
        description="暂无实践课程，点击上方按钮创建"
      >
        <template #action>
          <a-button type="primary" @click="createNewPractice">
            <template #icon><PlusOutlined /></template>
            新建实践
          </a-button>
        </template>
      </EmptyStateBlock>

      <EmptyStateBlock
        v-else-if="!loading && filteredPractices.length === 0"
        description="没有符合筛选条件的实践"
      />

      <div v-else-if="filteredPractices.length > 0" class="practices-list">
        <a-list
          :data-source="filteredPractices"
          :pagination="pagination"
          :grid="{ gutter: 16, column: 3 }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card hoverable class="practice-card" @click="handleCardClick(item)">
                <template #cover>
                  <div class="card-cover-container">
                    <img
                      alt="课程封面"
                      :src="
                        item.cover ||
                        'https://gw.alipayobjects.com/zos/rmsportal/JiqGstEfoWAOHiTxclqi.png'
                      "
                    />
                    <a-tag class="status-tag" :color="getStatusColor(item.status)">
                      {{ getStatusText(item.status, item.statusDetail) }}
                    </a-tag>
                  </div>
                </template>
                <a-card-meta :title="item.title || item.name">
                  <template #description>
                    <div class="practice-card-desc">
                      <div class="practice-intro" :title="item.intro || item.description">
                        {{ truncateText(item.intro || item.description || '', 80) }}
                      </div>
                      <div class="practice-meta">
                        <div class="meta-info">
                          <a-tag>{{ getDifficultyText(item.difficulty) }}</a-tag>
                          <a-tag v-if="(item.stageCount || item.taskCount || 0) > 0"
                            >{{ item.stageCount || item.taskCount }}个关卡</a-tag
                          >
                          <a-tag v-if="item.version">v{{ item.version }}</a-tag>
                        </div>
                        <span class="update-time"
                          >更新于 {{ formatDate(item.updateTime || item.createTime) }}</span
                        >
                      </div>
                    </div>
                  </template>
                </a-card-meta>
                <a-dropdown
                  :trigger="['click']"
                  placement="bottomRight"
                  @click.stop=""
                  overlayClassName="practice-dropdown"
                >
                  <template #overlay>
                    <a-menu @click="onMenuClick($event, item)">
                      <a-menu-item v-if="canView(item)" key="view">
                        <EyeOutlined />查看详情
                      </a-menu-item>
                      <a-menu-item v-if="canEdit(item)" key="edit">
                        <EditOutlined />编辑
                      </a-menu-item>
                      <a-menu-item key="clone">
                        <CopyOutlined />克隆
                      </a-menu-item>

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

                      <a-menu-item v-if="item.status === 'published_public'" key="addToClassroom">
                        <PlusCircleOutlined />添加到课堂
                      </a-menu-item>
                      <a-menu-item v-if="item.status === 'published_public'" key="openEdit">
                        <FormOutlined />开启编辑
                      </a-menu-item>
                      <a-menu-item v-if="item.status === 'published_public'" key="cancelPublic">
                        <RollbackOutlined />撤销公开
                      </a-menu-item>

                      <a-menu-item v-if="item.status === 'editing'" key="publishNewVersion">
                        <CloudUploadOutlined />发布新版本
                      </a-menu-item>
                      <a-menu-item v-if="item.status === 'editing'" key="cancelEdit">
                        <UndoOutlined />撤销编辑
                      </a-menu-item>

                      <a-menu-item v-if="item.status === 'pending'" key="cancelPending">
                        <StopOutlined />撤销申请
                      </a-menu-item>

                      <a-menu-item v-if="item.status === 'draft'" key="publish">
                        <CloudUploadOutlined />发布
                      </a-menu-item>
                      <a-menu-item v-if="item.status === 'draft'" key="delete">
                        <DeleteOutlined />删除
                      </a-menu-item>

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

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="确认删除"
      :okText="'删除'"
      :cancelText="'取消'"
      @ok="handleDeletePractice"
    >
      <p>确定要删除实践课程「{{ practiceToDelete?.title || practiceToDelete?.name }}」吗？</p>
      <p>此操作不可恢复，删除后该实践课程的所有内容将被清除。</p>
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
        <p>您正在为「{{ selectedPractice?.title || selectedPractice?.name }}」发布新版本</p>

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
      <p>确定要撤销对「{{ selectedPractice?.title || selectedPractice?.name }}」的编辑吗？</p>
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
      <p>确定要下架「{{ selectedPractice?.title || selectedPractice?.name }}」吗？</p>
      <p>下架后该实践将变为"编辑中"状态，仅自己可见，无法被学生访问。</p>
    </a-modal>

    <!-- 撤销公开确认弹窗 -->
    <a-modal
      v-model:open="cancelPublicModalVisible"
      title="确认撤销公开发布"
      :okText="'确认申请'"
      :cancelText="'取消'"
      @ok="handleCancelPublic"
    >
      <p>确定要申请撤销「{{ selectedPractice?.title || selectedPractice?.name }}」的公开发布吗？</p>
      <p>
        申请提交后需要等待管理员审核，审核通过后该实践将从课程库中移除，变为个人发布状态。
      </p>
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
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
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
  fetchMyPractices,
  deletePracticeById,
  updatePracticeStatusById,
  startEditMode,
  cancelEdit,
  unpublishPractice,
  applyPublicPublish,
  cancelPublicPublish,
  publishNewVersion,
  clonePractice,
  type PracticeItem,
  type VersionData
} from '@/api/practice';
import { useUserStore } from '@/stores/user';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import Stack from '@/components/common/Stack.vue';

const userStore = useUserStore();

const router = useRouter();
const loading = ref(false);
const searchKeyword = ref('');
const statusFilter = ref('');
const practices = ref<PracticeItem[]>([]);
const deleteModalVisible = ref(false);
const practiceToDelete = ref<PracticeItem | null>(null);
const selectedPractice = ref<PracticeItem | null>(null);

const publishVersionModalVisible = ref(false);
const cancelEditModalVisible = ref(false);
const unpublishModalVisible = ref(false);
const cancelPublicModalVisible = ref(false);

const versionForm = ref({
  versionType: 'minor',
  updateNotes: '',
  publishType: 'personal'
});

const cancelPublicForm = ref({
  reason: ''
});

const needPublicApproval = computed(() => {
  return (
    selectedPractice.value?.status === 'published_personal' ||
    selectedPractice.value?.status === 'editing'
  );
});

const pagination = {
  pageSize: 9,
  showSizeChanger: false,
  showTotal: (total: number) => `共 ${total} 项`
};

const filteredPractices = computed(() => {
  let result = practices.value;

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    result = result.filter(
      (item) =>
        (item.title || item.name || '').toLowerCase().includes(keyword) ||
        (item.intro || item.description || '').toLowerCase().includes(keyword)
    );
  }

  if (statusFilter.value) {
    result = result.filter((item) => item.status === statusFilter.value);
  }

  return result;
});

const getDifficultyText = (difficulty: string) => {
  const map: Record<string, string> = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级'
  };
  return map[difficulty] || '未知难度';
};

const getStatusColor = (status: string) => {
  const map: Record<string, string> = {
    draft: 'default',
    editing: 'processing',
    pending: 'warning',
    published_personal: 'success',
    published_public: 'success',
    rejected: 'error'
  };
  return map[status] || 'default';
};

const getStatusText = (status: string, detail?: string) => {
  const map: Record<string, string> = {
    draft: '编辑中',
    editing: '编辑中',
    pending: '审核中',
    published_personal: '已发布',
    published_public: '已发布',
    rejected: '审核未通过'
  };

  const baseText = map[status] || '未知状态';

  if (detail) {
    return `${baseText}（${detail}）`;
  }

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

const formatDate = (date: string | Date) => {
  if (!date) return '未知';
  return dayjs(date).format('YYYY-MM-DD');
};

const truncateText = (text: string, maxLength: number) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

const handleSearch = () => {
  console.log('搜索关键词:', searchKeyword.value);
};

const handleStatusFilterChange = () => {
  console.log('状态筛选:', statusFilter.value);
};

const createNewPractice = () => {
  router.push('/course/practice/create');
};

const canView = (practice: PracticeItem) => {
  return practice.status === 'published_personal' || practice.status === 'published_public';
};

const canEdit = (practice: PracticeItem) => {
  return (
    practice.status === 'draft' || practice.status === 'editing' || practice.status === 'rejected'
  );
};

const handleCardClick = (practice: PracticeItem) => {
  if (canView(practice)) {
    viewPractice(practice);
  } else if (canEdit(practice)) {
    editPractice(practice);
  }
};

const viewPractice = (practice: PracticeItem) => {
  router.push(`/course/practice/${practice.id}`);
};

const editPractice = (practice: PracticeItem) => {
  router.push(`/course/practice/${practice.id}/edit`);
};

const onMenuClick = (event: { key: string }, practice: PracticeItem) => {
  selectedPractice.value = practice;
  handleMenuClick(event.key, practice);
};

const handleMenuClick = (key: string, practice: PracticeItem) => {
  selectedPractice.value = practice;

  switch (key) {
    case 'view':
      viewPractice(practice);
      break;
    case 'edit':
      editPractice(practice);
      break;
    case 'clone':
      confirmClonePractice(practice);
      break;
    case 'delete':
      confirmDeletePractice(practice);
      break;
    case 'addToClassroom':
      router.push({
        path: '/classroom',
        query: { addPractice: practice.id }
      });
      break;
    case 'openEdit':
      handleStartEdit(practice);
      break;
    case 'publish':
      showPublishOptions(practice);
      break;
    case 'publishNewVersion':
      selectedPractice.value = practice;
      publishVersionModalVisible.value = true;
      break;
    case 'applyPublic':
      handleApplyPublic(practice);
      break;
    case 'cancelPublic':
      selectedPractice.value = practice;
      cancelPublicModalVisible.value = true;
      break;
    case 'unpublish':
      selectedPractice.value = practice;
      unpublishModalVisible.value = true;
      break;
    case 'cancelEdit':
      selectedPractice.value = practice;
      cancelEditModalVisible.value = true;
      break;
    case 'cancelPending':
      Modal.confirm({
        title: '确认撤销申请',
        content: '确定要撤销当前的审核申请吗？撤销后将返回到之前的状态。',
        onOk: () => {
          applyStatusChange(practice.id, 'cancel_pending');
        }
      });
      break;
    case 'viewReason':
      Modal.info({
        title: '审核未通过原因',
        content:
          '您的实践课程未通过审核，原因：内容过于简单，缺乏教学价值，请增加更多有深度的教学内容后再次提交。'
      });
      break;
    case 'reapply':
      Modal.confirm({
        title: '重新申请公开发布',
        content: '确定要重新申请公开发布吗？请确保已经根据审核意见进行了修改。',
        onOk: () => {
          applyStatusChange(practice.id, 'public_publish');
        }
      });
      break;
    default:
      break;
  }
};

const showPublishOptions = (practice: PracticeItem) => {
  Modal.confirm({
    title: '选择发布方式',
    content:
      '请选择发布方式：\n\n个人发布：实践将立即发布，仅您自己可见和使用\n\n公开发布：实践将提交审核，通过后将对所有用户可见',
    okText: '公开发布',
    cancelText: '个人发布',
    onOk: () => {
      applyStatusChange(practice.id, 'public_publish');
    },
    onCancel: () => {
      applyStatusChange(practice.id, 'publish', { visibility: 'PRIVATE' });
    }
  });
};

const applyStatusChange = async (id: string, action: string, extraParams?: any) => {
  loading.value = true;

  try {
    const success = await updatePracticeStatusById(id, action, extraParams);

    if (success) {
      await loadMyPractices();

      let successMsg = '操作成功';
      if (action === 'start_edit') {
        successMsg = '实践课程已开启编辑模式';
      } else if (action === 'publish') {
        successMsg = '实践课程已成功发布';
      } else if (action === 'public_publish') {
        successMsg = '公开发布申请已提交，请等待管理员审核';
      } else if (action === 'offline') {
        successMsg = '实践课程已下架';
      } else if (action === 'delete') {
        successMsg = '实践课程已删除';
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

const confirmDeletePractice = (practice: PracticeItem) => {
  practiceToDelete.value = practice;
  deleteModalVisible.value = true;
};

const confirmClonePractice = (practice: PracticeItem) => {
  Modal.confirm({
    title: '确认克隆',
    content: `确定要克隆实践课程「${practice.title || practice.name}」吗？`,
    okText: '克隆',
    cancelText: '取消',
    onOk: async () => {
      loading.value = true;
      try {
        const result = await clonePractice(practice.id);
        if (result && result.id) {
          message.success('克隆成功');
          router.push(`/course/practice/${result.id}/edit`);
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

const handleDeletePractice = async () => {
  if (!practiceToDelete.value) return;

  loading.value = true;

  try {
    const success = await deletePracticeById(practiceToDelete.value.id);

    if (success) {
      practices.value = practices.value.filter((p) => p.id !== practiceToDelete.value?.id);

      message.success('实践课程删除成功');
      deleteModalVisible.value = false;
      practiceToDelete.value = null;
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

const handleCancelEdit = async () => {
  if (!selectedPractice.value) return;

  loading.value = true;

  try {
    const success = await cancelEdit(selectedPractice.value.id);

    if (success) {
      const practice = practices.value.find((p) => p.id === selectedPractice.value?.id);
      if (practice) {
        practice.status = 'published_personal';
        practice.statusDetail = '个人发布';
      }

      message.success('已撤销编辑，实践课程已恢复到上一个发布版本');
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

const handleUnpublish = async () => {
  if (!selectedPractice.value) return;

  loading.value = true;

  try {
    const success = await unpublishPractice(selectedPractice.value.id);

    if (success) {
      const practice = practices.value.find((p) => p.id === selectedPractice.value?.id);
      if (practice) {
        practice.status = 'draft';
        practice.statusDetail = '创建未发布';
      }

      message.success('实践课程已下架');
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

const handleCancelPublic = async () => {
  if (!selectedPractice.value || !cancelPublicForm.value.reason) return;

  loading.value = true;

  try {
    const success = await cancelPublicPublish(
      selectedPractice.value.id,
      cancelPublicForm.value.reason
    );

    if (success) {
      const practice = practices.value.find((p) => p.id === selectedPractice.value?.id);
      if (practice) {
        practice.status = 'pending';
        practice.statusDetail = '撤销公开发布审核中';
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

const handleStartEdit = async (practice: PracticeItem) => {
  loading.value = true;

  try {
    const success = await startEditMode(practice.id);

    if (success) {
      const localPractice = practices.value.find((p) => p.id === practice.id);
      if (localPractice) {
        localPractice.status = 'editing';
        localPractice.statusDetail = '发布后编辑';
      }

      message.success('已开启编辑模式');
      router.push(`/course/practice/${practice.id}/edit`);
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

const handleApplyPublic = async (practice: PracticeItem) => {
  Modal.confirm({
    title: '确认申请公开发布',
    content:
      '申请公开发布需要管理员审核，审核通过后该实践将加入实践课程库，对所有用户可见。确定要申请吗？',
    onOk: async () => {
      loading.value = true;

      try {
        const success = await applyPublicPublish(practice.id);

        if (success) {
          const localPractice = practices.value.find((p) => p.id === practice.id);
          if (localPractice) {
            localPractice.status = 'pending';
            localPractice.statusDetail = '公开发布审核中';
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

const handlePublishNewVersion = async () => {
  if (!selectedPractice.value || !versionForm.value.updateNotes) {
    message.error('请填写更新说明');
    return;
  }

  loading.value = true;

  try {
    const versionData: VersionData = {
      versionType: versionForm.value.versionType as 'major' | 'minor',
      updateNotes: versionForm.value.updateNotes,
      publishType: versionForm.value.publishType as 'personal' | 'public'
    };

    const success = await publishNewVersion(selectedPractice.value.id, versionData);

    if (success) {
      const practice = practices.value.find((p) => p.id === selectedPractice.value?.id);
      if (practice) {
        practice.status =
          versionData.publishType === 'public' ? 'pending' : 'published_personal';
        practice.statusDetail =
          versionData.publishType === 'public' ? '公开发布审核中' : '个人发布';
      }

      const successMsg =
        versionData.publishType === 'public'
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

const loadMyPractices = async () => {
  loading.value = true;

  try {
    const creatorId = userStore.userId;
    if (!creatorId) {
      message.error('未获取到用户信息，请重新登录');
      return;
    }

    const result = await fetchMyPractices(creatorId);
    practices.value = result;
  } catch (error) {
    console.error('加载失败:', error);
    message.error('加载实践列表失败，请刷新页面重试');
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadMyPractices();
});
</script>

<style scoped>
.practice-filters {
  margin-bottom: var(--hx-space-5);
  align-items: center;
}

.practices-list {
  margin-top: 0;
}

.practice-card {
  height: 100%;
  transition: all var(--hx-transition-normal);
  position: relative;
  border-color: var(--hx-color-border-muted);
}

.practice-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--hx-shadow-md);
  border-color: var(--hx-color-primary);
}

.card-cover-container {
  position: relative;
  height: 160px;
  overflow: hidden;
  background-color: var(--hx-color-bg-layout, #f5f5f5);
}

.card-cover-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.status-tag {
  position: absolute;
  top: var(--hx-space-3);
  right: var(--hx-space-3);
  font-size: var(--hx-font-size-xs);
}

.practice-card-desc {
  display: flex;
  flex-direction: column;
  height: 110px;
}

.practice-intro {
  flex: 1;
  margin-bottom: var(--hx-space-3);
  color: var(--hx-color-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.practice-meta {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-2);
}

.meta-info {
  display: flex;
  flex-wrap: wrap;
  gap: var(--hx-space-1);
}

.meta-info :deep(.ant-tag) {
  margin-right: 0;
}

.update-time {
  font-size: var(--hx-font-size-xs);
  color: var(--hx-color-text-tertiary);
}

.more-btn {
  position: absolute;
  top: var(--hx-space-2);
  right: var(--hx-space-2);
  z-index: 10;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.publish-version-form {
  padding: 0 var(--hx-space-4);
}

.publish-tip {
  margin-top: var(--hx-space-2);
}

:deep(.practice-dropdown .ant-dropdown-menu) {
  min-width: 160px;
}

:deep(.practice-dropdown .ant-dropdown-menu-item) {
  padding: var(--hx-space-2) var(--hx-space-3);
}
</style>
