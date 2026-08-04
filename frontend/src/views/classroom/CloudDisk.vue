<template>
  <div class="cloud-disk-container">
    <PageHeaderBar
      title="课堂云盘"
      subtitle="教师可将课件、文档等课程资源上传分享给课程内学生。支持常用格式在线预览。"
    >
      <template #actions>
        <a-button v-if="isTeacher" type="primary" @click="openUploadDialog">
          <UploadOutlined /> 上传文件
        </a-button>
        <a-button v-if="selectedFiles.length > 0" @click="handleBatchDownload">
          <DownloadOutlined /> 批量下载 ({{ selectedFiles.length }})
        </a-button>
        <a-button v-if="isTeacher && selectedFiles.length > 0" danger @click="handleBatchDelete">
          <DeleteOutlined /> 批量删除 ({{ selectedFiles.length }})
        </a-button>
      </template>
    </PageHeaderBar>

    <Stack direction="vertical" :gap="4">
    <!-- 筛选器 -->
    <Stack direction="horizontal" :gap="3" align="center" class="filters">
      <a-input
        v-model:value="keyword"
        placeholder="搜索文件名"
        style="width: 200px;"
        @press-enter="handleFilter"
      >
        <template #suffix>
          <SearchOutlined @click="handleFilter" style="cursor: pointer;" />
        </template>
      </a-input>
      <a-select
        v-model:value="fileTypeFilter"
        placeholder="文件类型"
        style="width: 120px;"
        allowClear
        @change="handleFilter"
      >
        <a-select-option value="pdf">PDF文档</a-select-option>
        <a-select-option value="doc">Word文档</a-select-option>
        <a-select-option value="ppt">PPT演示文稿</a-select-option>
        <a-select-option value="image">图片</a-select-option>
        <a-select-option value="video">视频</a-select-option>
      </a-select>
    </Stack>

    <!-- 文件列表 -->
    <a-spin :spinning="loading" tip="加载中...">
      <EmptyStateBlock
        v-if="filesList.length === 0 && !loading"
        description="暂无文件，点击上传文件开始分享"
      >
        <template v-if="isTeacher" #action>
          <a-button type="primary" @click="openUploadDialog">
            <UploadOutlined /> 上传文件
          </a-button>
        </template>
      </EmptyStateBlock>
      
      <div v-else class="files-grid">
        <a-row :gutter="[16, 16]">
          <a-col v-for="file in filesList" :key="file.id" :xs="24" :sm="12" :md="8" :lg="6">
            <a-card 
              hoverable 
              class="file-card"
              :class="{ 'selected': selectedFiles.includes(file.id) }"
            >
              <template #cover>
                <div class="file-preview-container" @click="handlePreview(file)">
                  <component :is="getFileIcon(file.file_type)" class="file-icon" />
                </div>
              </template>
              
              <a-card-meta>
                <template #title>
                  <a-checkbox 
                    :checked="selectedFiles.includes(file.id)"
                    @change="(e) => handleSelectFile(file.id, e.target.checked)"
                    @click.stop
                  >
                    <span class="file-name" :title="file.name">{{ file.name }}</span>
                  </a-checkbox>
                </template>
                <template #description>
                  <div class="file-info">
                    <div>大小: {{ formatFileSize(file.file_size) }}</div>
                    <div>上传时间: {{ formatDate(file.upload_time) }}</div>
                    <div>下载次数: {{ file.download_count || 0 }}</div>
                  </div>
                </template>
              </a-card-meta>
              
              <template #actions>
                <a-tooltip title="预览">
                  <EyeOutlined @click="handlePreview(file)" />
                </a-tooltip>
                <a-tooltip title="下载">
                  <DownloadOutlined @click="handleDownload(file)" />
                </a-tooltip>
                <a-tooltip v-if="isTeacher" title="删除">
                  <DeleteOutlined @click="handleDelete(file)" />
                </a-tooltip>
              </template>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </a-spin>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination-container">
      <a-pagination
        v-model:current="currentPage"
        :total="total"
        :page-size="pageSize"
        :show-size-changer="true"
        :show-quick-jumper="true"
        :show-total="(total) => `共 ${total} 个文件`"
        @change="handlePageChange"
        @showSizeChange="handlePageSizeChange"
      />
    </div>

    <!-- 上传文件弹窗 -->
    <a-modal
      v-model:open="uploadModalVisible"
      title="上传文件"
      :confirm-loading="uploadLoading"
      @ok="handleUpload"
      @cancel="uploadModalVisible = false"
    >
      <a-form layout="vertical">
        <a-form-item label="选择文件" required>
          <a-upload
            v-model:file-list="fileList"
            :before-upload="beforeUpload"
            :max-count="1"
          >
            <a-button>
              <UploadOutlined /> 选择文件
            </a-button>
          </a-upload>
          <div class="upload-tips">
            支持格式：PDF、DOC、DOCX、PPT、PPTX、JPG、PNG、MOV、MP4等
          </div>
        </a-form-item>
        
        <a-form-item label="文件名" required>
          <a-input 
            v-model:value="uploadFormData.file_name" 
            placeholder="请输入文件显示名称"
          />
        </a-form-item>
        
        <a-form-item label="是否共享给学生">
          <a-switch v-model:checked="uploadFormData.is_shared" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 文件预览弹窗 -->
    <a-modal
      v-model:open="previewModalVisible"
      :title="currentPreview.name"
      width="80%"
      :footer="null"
    >
      <div class="preview-content">
        <!-- PDF预览 -->
        <iframe 
          v-if="currentPreview.type === 'pdf'" 
          :src="currentPreview.url" 
          class="pdf-preview"
        />
        
        <!-- 图片预览 -->
        <img 
          v-else-if="['jpg', 'jpeg', 'png', 'gif'].includes(currentPreview.type)" 
          :src="currentPreview.url"
          class="image-preview"
        />
        
        <!-- 视频预览 -->
        <video 
          v-else-if="['mp4', 'mov'].includes(currentPreview.type)"
          controls
          class="video-preview"
        >
          <source :src="currentPreview.url" :type="`video/${currentPreview.type}`">
          您的浏览器不支持视频播放
        </video>
        
        <!-- 不支持预览 -->
        <div v-else class="unsupported-preview">
          <FileUnknownOutlined style="font-size: 64px; color: #999;" />
          <p>当前文件不支持预览，请点击下载</p>
          <a-button type="primary" @click="handleDownload(currentPreview)">
            <DownloadOutlined /> 下载文件
          </a-button>
        </div>
      </div>
    </a-modal>
    </Stack>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { 
  UploadOutlined, 
  DownloadOutlined, 
  DeleteOutlined, 
  SearchOutlined,
  EyeOutlined,
  FilePdfOutlined,
  FileWordOutlined,
  FilePptOutlined,
  FileImageOutlined,
  PlayCircleOutlined,
  FileUnknownOutlined
} from '@ant-design/icons-vue';
import type { UploadFile } from 'ant-design-vue';
import { useUserStore } from '../../stores/user';
import {
  getCloudDiskFiles,
  uploadCloudDiskFile,
  downloadCloudDiskFile,
  deleteCloudDiskFile,
  batchCloudDiskOperation,
  previewCloudDiskFile,
  formatFileSize
} from '../../api/resources';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import Stack from '@/components/common/Stack.vue';

// Props
interface Props {
  classroomId: string;
}

const props = defineProps<Props>();

// Store
const userStore = useUserStore();
const teacherId = computed(() => userStore.userInfo.id);
const isTeacher = computed(() => userStore.userInfo.role === 'teacher');

// 状态管理
const loading = ref(false);
const uploadLoading = ref(false);
const filesList = ref<any[]>([]);
const selectedFiles = ref<number[]>([]);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);

// 筛选器
const keyword = ref('');
const fileTypeFilter = ref<string | undefined>(undefined);

// 上传相关
const uploadModalVisible = ref(false);
const fileList = ref<UploadFile[]>([]);
const uploadFormData = ref({
  file_name: '',
  is_shared: true
});

// 预览相关
const previewModalVisible = ref(false);
const currentPreview = ref<any>({});

// 加载文件列表
async function loadFiles() {
  loading.value = true;
  try {
    const response = await getCloudDiskFiles({
      classroom_id: parseInt(props.classroomId),
      teacher_id: teacherId.value,
      user_role: userStore.userInfo.role || 'teacher',
      folder_path: '',
      keyword: keyword.value || undefined,
      file_type: fileTypeFilter.value,
      page: currentPage.value,
      page_size: pageSize.value
    });

    if (response.code === '0000') {
      filesList.value = response.data.list || [];
      total.value = response.data.meta?.total || 0;
    } else {
      message.error(response.message || '加载文件列表失败');
    }
  } catch (error) {
    console.error('加载云盘文件失败:', error);
    message.error('加载云盘文件失败');
  } finally {
    loading.value = false;
  }
}

// 打开上传对话框
function openUploadDialog() {
  uploadModalVisible.value = true;
  fileList.value = [];
  uploadFormData.value = {
    file_name: '',
    is_shared: true
  };
}

// 上传前处理
function beforeUpload(file: File) {
  const isLt2G = file.size / 1024 / 1024 / 1024 < 2;
  if (!isLt2G) {
    message.error('文件大小不能超过2GB！');
    return false;
  }
  
  // 设置默认文件名
  if (!uploadFormData.value.file_name) {
    uploadFormData.value.file_name = file.name;
  }
  
  return false; // 阻止自动上传
}

// 处理上传
async function handleUpload() {
  if (!fileList.value.length) {
    message.error('请选择要上传的文件');
    return;
  }

  if (!uploadFormData.value.file_name) {
    message.error('请输入文件名');
    return;
  }

  uploadLoading.value = true;
  try {
    const uploadFile = fileList.value[0];
    const file = uploadFile.originFileObj as File;

    if (!file) {
      message.error('无法获取文件内容');
      uploadLoading.value = false;
      return;
    }

    // 创建FormData对象来上传文件
    const formData = new FormData();
    formData.append('file', file);
    formData.append('classroom_id', props.classroomId);
    formData.append('teacher_id', teacherId.value.toString());
    formData.append('file_name', uploadFormData.value.file_name);
    formData.append('folder_path', '');
    formData.append('is_shared', uploadFormData.value.is_shared.toString());

    // 直接上传文件到后端
    const token = localStorage.getItem('huixue_token') || localStorage.getItem('access_token') || '';
    const response = await fetch('/api/v1/files/upload/classroom-disk', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });
    
    const result = await response.json();

    if (result.code === '0000') {
      message.success('文件上传成功');
      uploadModalVisible.value = false;
      // 重置表单
      uploadFormData.value = {
        file_name: '',
        is_shared: false
      };
      fileList.value = [];
      loadFiles();
    } else {
      message.error(result.message || '上传失败');
    }
  } catch (error) {
    console.error('上传文件失败:', error);
    message.error('上传文件失败');
  } finally {
    uploadLoading.value = false;
  }
}

// 文件选择
function handleSelectFile(fileId: number, checked: boolean) {
  if (checked) {
    selectedFiles.value.push(fileId);
  } else {
    selectedFiles.value = selectedFiles.value.filter(id => id !== fileId);
  }
}

// 预览文件
async function handlePreview(file: any) {
  try {
    const response = await previewCloudDiskFile({
      classroom_id: parseInt(props.classroomId),
      file_id: file.id,
      teacher_id: teacherId.value
    });

    if (response.code === '0000') {
      currentPreview.value = {
        ...file,
        type: file.file_type.toLowerCase()
      };
      previewModalVisible.value = true;
    } else {
      message.error('获取预览信息失败');
    }
  } catch (error) {
    console.error('预览失败:', error);
    // 即使预览API失败也显示预览
    currentPreview.value = {
      ...file,
      type: file.file_type.toLowerCase()
    };
    previewModalVisible.value = true;
  }
}

// 下载文件
async function handleDownload(file: any) {
  try {
    const response = await downloadCloudDiskFile({
      classroom_id: parseInt(props.classroomId),
      file_id: file.id,
      teacher_id: teacherId.value
    });

    if (response.code === '0000') {
      // 创建下载链接
      const link = document.createElement('a');
      link.href = response.data.download_url;
      link.download = file.name;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success('开始下载');
      // 刷新列表以更新下载次数
      loadFiles();
    } else {
      message.error(response.message || '下载失败');
    }
  } catch (error) {
    console.error('下载失败:', error);
    message.error('下载失败');
  }
}

// 批量下载
async function handleBatchDownload() {
  if (selectedFiles.value.length === 0) {
    message.warning('请选择要下载的文件');
    return;
  }

  try {
    const response = await batchCloudDiskOperation({
      classroom_id: parseInt(props.classroomId),
      teacher_id: teacherId.value,
      data: {
        action: 'download',
        file_ids: selectedFiles.value
      }
    });

    if (response.code === '0000') {
      message.success('批量下载准备中，将以压缩包形式下载');
      // 这里应该处理批量下载的逻辑
      selectedFiles.value = [];
    } else {
      message.error(response.message || '批量下载失败');
    }
  } catch (error) {
    console.error('批量下载失败:', error);
    message.error('批量下载失败');
  }
}

// 删除文件
function handleDelete(file: any) {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除文件"${file.name}"吗？`,
    onOk: async () => {
      try {
        const response = await deleteCloudDiskFile({
          classroom_id: parseInt(props.classroomId),
          file_id: file.id,
          teacher_id: teacherId.value
        });

        if (response.code === '0000') {
          message.success('删除成功');
          loadFiles();
        } else {
          message.error(response.message || '删除失败');
        }
      } catch (error) {
        console.error('删除文件失败:', error);
        message.error('删除文件失败');
      }
    }
  });
}

// 批量删除
function handleBatchDelete() {
  if (selectedFiles.value.length === 0) {
    message.warning('请选择要删除的文件');
    return;
  }

  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
    onOk: async () => {
      try {
        const response = await batchCloudDiskOperation({
          classroom_id: parseInt(props.classroomId),
          teacher_id: teacherId.value,
          data: {
            action: 'delete',
            file_ids: selectedFiles.value
          }
        });

        if (response.code === '0000') {
          message.success(`成功删除 ${response.data.deleted_count} 个文件`);
          selectedFiles.value = [];
          loadFiles();
        } else {
          message.error(response.message || '批量删除失败');
        }
      } catch (error) {
        console.error('批量删除失败:', error);
        message.error('批量删除失败');
      }
    }
  });
}

// 筛选处理
function handleFilter() {
  currentPage.value = 1;
  loadFiles();
}

// 分页变化
function handlePageChange(page: number) {
  currentPage.value = page;
  loadFiles();
}

// 每页大小变化
function handlePageSizeChange(current: number, size: number) {
  currentPage.value = 1;
  pageSize.value = size;
  loadFiles();
}

// 辅助函数
function getFileIcon(fileType: string) {
  const type = fileType.toLowerCase();
  if (type === 'pdf') return h(FilePdfOutlined);
  if (['doc', 'docx'].includes(type)) return h(FileWordOutlined);
  if (['ppt', 'pptx'].includes(type)) return h(FilePptOutlined);
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return h(FileImageOutlined);
  if (['mp4', 'mov'].includes(type)) return h(PlayCircleOutlined);
  return h(FileUnknownOutlined);
}

function getFileType(fileName: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase() || '';
  return ext;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN');
}

// 组件挂载
onMounted(() => {
  loadFiles();
});
</script>

<style scoped>
.cloud-disk-container {
  /* nested in classroom detail PageShell */
}

.files-grid {
  margin-bottom: var(--hx-space-4);
}

.file-card {
  transition: all 0.3s;
}

.file-card.selected {
  border-color: #1677ff;
  box-shadow: 0 0 0 2px rgba(22, 119, 255, 0.2);
}

.file-preview-container {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  cursor: pointer;
  border-radius: var(--hx-radius-md, 10px);
}

.file-icon {
  font-size: 48px;
  color: #1677ff;
}

.file-name {
  display: inline-block;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-info {
  font-size: 12px;
  color: var(--hx-color-text-tertiary, #999);
  line-height: 1.6;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: var(--hx-space-4);
}

.upload-tips {
  margin-top: var(--hx-space-2);
  font-size: 12px;
  color: var(--hx-color-text-tertiary, #999);
}

.preview-content {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-preview {
  width: 100%;
  height: 700px;
  border: none;
}

.image-preview {
  max-width: 100%;
  max-height: 700px;
  object-fit: contain;
}

.video-preview {
  width: 100%;
  max-height: 700px;
}

.unsupported-preview {
  text-align: center;
  padding: var(--hx-space-7);
}

.unsupported-preview p {
  margin: var(--hx-space-4) 0;
  color: var(--hx-color-text-secondary, #666);
}
</style>