<template>
  <div class="dataset-tab-container">
    <div class="dataset-header">
      <h3>数据集管理</h3>
      <a-button type="primary" @click="showUploadModal = true">
        <template #icon><UploadOutlined /></template>
        上传数据集
      </a-button>
    </div>

    <!-- 数据集列表 -->
    <div class="dataset-list">
      <a-table
        :columns="columns"
        :data-source="datasets"
        :loading="loading"
        :pagination="false"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <span>
              <FileTextOutlined style="margin-right: 8px" />
              {{ record.name }}
            </span>
          </template>
          
          <template v-if="column.key === 'file_size_display'">
            {{ record.file_size_display || formatFileSize(record.file_size) }}
          </template>
          
          <template v-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-tooltip title="复制访问地址">
                <a-button
                  type="link"
                  size="small"
                  @click="copyAccessUrl(record)"
                >
                  <template #icon><CopyOutlined /></template>
                  复制地址
                </a-button>
              </a-tooltip>
              
              <a-popconfirm
                title="确定要删除这个数据集吗？"
                @confirm="deleteDataset(record)"
              >
                <a-button type="link" danger size="small">
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>

      <a-empty v-if="!loading && datasets.length === 0" description="暂无数据集">
        <a-button type="primary" @click="showUploadModal = true">
          <template #icon><UploadOutlined /></template>
          上传第一个数据集
        </a-button>
      </a-empty>
    </div>

    <!-- 上传数据集模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传数据集"
      width="600px"
      :footer="null"
    >
      <a-form :model="uploadForm" layout="vertical">
        <a-form-item label="数据集描述（可选）">
          <a-textarea
            v-model:value="uploadForm.description"
            placeholder="请输入数据集的描述信息"
            :rows="3"
          />
        </a-form-item>
      </a-form>

      <a-upload-dragger
        :multiple="true"
        :before-upload="beforeUpload"
        :file-list="fileList"
        @change="handleFileChange"
        @remove="handleFileRemove"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持的文件类型：csv, json, txt, xlsx, zip, tar.gz, sql, xml<br>
          单个文件最大支持 500MB
        </p>
      </a-upload-dragger>

      <div style="margin-top: 16px; text-align: right;">
        <a-button @click="showUploadModal = false" style="margin-right: 8px">取消</a-button>
        <a-button
          type="primary"
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="handleUpload"
        >
          开始上传
        </a-button>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { message } from 'ant-design-vue';
import {
  UploadOutlined,
  FileTextOutlined,
  CopyOutlined,
  DeleteOutlined,
  InboxOutlined
} from '@ant-design/icons-vue';
import {
  getDatasets,
  uploadDataset,
  getDatasetAccessUrl,
  deleteDataset as deleteDatasetApi,
  type PracticeDataset
} from '@/api/practice';
import { useUserStore } from '@/stores/user';
import type { UploadFile } from 'ant-design-vue';

const props = defineProps<{
  practiceId: number;
}>();

const userStore = useUserStore();
const creatorId = computed(() => userStore.userInfo.id);

// 数据
const datasets = ref<PracticeDataset[]>([]);
const loading = ref(false);
const showUploadModal = ref(false);
const uploading = ref(false);
const fileList = ref<UploadFile[]>([]);

// 上传表单
const uploadForm = reactive({
  description: ''
});

// 表格列配置
const columns = [
  {
    title: '文件名',
    dataIndex: 'name',
    key: 'name',
    width: '35%'
  },
  {
    title: '文件大小',
    dataIndex: 'file_size_display',
    key: 'file_size_display',
    width: '15%'
  },
  {
    title: '文件类型',
    dataIndex: 'file_type',
    key: 'file_type',
    width: '10%'
  },
  {
    title: '上传时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '20%'
  },
  {
    title: '操作',
    key: 'actions',
    width: '20%'
  }
];

// 格式化文件大小
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 格式化日期
const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
};

// 加载数据集列表
const loadDatasets = async () => {
  loading.value = true;
  try {
    const data = await getDatasets(props.practiceId, creatorId.value);
    datasets.value = data;
  } catch (error) {
    message.error('加载数据集列表失败');
  } finally {
    loading.value = false;
  }
};

// 复制访问地址
const copyAccessUrl = async (dataset: PracticeDataset) => {
  try {
    // 获取最新的访问URL
    const url = await getDatasetAccessUrl(props.practiceId, dataset.id, creatorId.value);
    if (url) {
      // 复制到剪贴板
      await navigator.clipboard.writeText(url);
      message.success('访问地址已复制到剪贴板');
    } else {
      message.error('获取访问地址失败');
    }
  } catch (error) {
    // 兼容处理
    const textArea = document.createElement('textarea');
    textArea.value = dataset.access_url;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      message.success('访问地址已复制到剪贴板');
    } catch (err) {
      message.error('复制失败，请手动复制');
    }
    document.body.removeChild(textArea);
  }
};

// 删除数据集
const deleteDataset = async (dataset: PracticeDataset) => {
  try {
    const success = await deleteDatasetApi(props.practiceId, dataset.id, creatorId.value);
    if (success) {
      message.success('数据集删除成功');
      loadDatasets();
    } else {
      message.error('数据集删除失败');
    }
  } catch (error) {
    message.error('数据集删除失败');
  }
};

// 上传前检查
const beforeUpload = (file: any) => {
  // 检查文件类型
  const allowedTypes = ['csv', 'json', 'txt', 'xlsx', 'zip', 'tar.gz', 'sql', 'xml'];
  const fileExt = file.name.split('.').pop()?.toLowerCase();
  const isTarGz = file.name.endsWith('.tar.gz');
  
  if (!isTarGz && (!fileExt || !allowedTypes.includes(fileExt))) {
    message.error(`不支持的文件类型：${fileExt}`);
    return false;
  }
  
  // 检查文件大小（500MB）
  const maxSize = 500 * 1024 * 1024;
  if (file.size > maxSize) {
    message.error('文件大小不能超过 500MB');
    return false;
  }
  
  return false; // 阻止自动上传
};

// 文件列表变化
const handleFileChange = (info: any) => {
  fileList.value = info.fileList;
};

// 移除文件
const handleFileRemove = (file: UploadFile) => {
  const index = fileList.value.indexOf(file);
  if (index !== -1) {
    fileList.value.splice(index, 1);
  }
};

// 处理上传
const handleUpload = async () => {
  if (fileList.value.length === 0) {
    message.warning('请选择要上传的文件');
    return;
  }

  uploading.value = true;
  let successCount = 0;

  for (const file of fileList.value) {
    try {
      const originFile = file.originFileObj as File | undefined;
      if (!originFile) {
        continue;
      }

      const result = await uploadDataset(
        props.practiceId,
        creatorId.value,
        originFile,
        uploadForm.description
      );
      if (result) {
        successCount++;
      }
    } catch (error) {
      message.error(`文件 ${file.name} 上传失败`);
    }
  }

  uploading.value = false;

  if (successCount > 0) {
    message.success(`成功上传 ${successCount} 个文件`);
    showUploadModal.value = false;
    fileList.value = [];
    uploadForm.description = '';
    loadDatasets();
  }
};

// 初始化
onMounted(() => {
  loadDatasets();
});
</script>

<style scoped>
.dataset-tab-container {
  padding: 24px;
}

.dataset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dataset-header h3 {
  margin: 0;
  font-size: 18px;
}

.dataset-list {
  background: #fff;
  border-radius: 4px;
}

:deep(.ant-table) {
  font-size: 14px;
}

:deep(.ant-upload-list) {
  max-height: 200px;
  overflow-y: auto;
}

:deep(.ant-upload-list-item-name) {
  cursor: pointer;
}
</style>