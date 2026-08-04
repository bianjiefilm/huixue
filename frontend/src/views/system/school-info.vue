<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar title="学校信息管理" subtitle="查看和编辑学校基础信息" />

    <a-card :title="undefined" :bordered="false" :loading="loading">
      <a-form 
        :model="formData" 
        :label-col="{ span: 4 }" 
        :wrapper-col="{ span: 12 }"
      >
        <!-- 学校名称 -->
        <a-form-item label="学校名称" name="name" :rules="[{ required: true, message: '请输入学校名称' }]">
          <div class="editable-field">
            <span v-if="!editingFields.name" class="field-value">{{ formData.name || '未设置' }}</span>
            <a-input v-else v-model:value="formData.name" :maxlength="50" placeholder="请输入学校名称" />
            <a-button 
              type="link" 
              size="small"
              @click="toggleEdit('name')"
            >
              {{ editingFields.name ? '保存' : '修改' }}
            </a-button>
          </div>
        </a-form-item>

        <!-- 学校简称 -->
        <a-form-item label="学校简称" name="short_name">
          <div class="editable-field">
            <span v-if="!editingFields.short_name" class="field-value">{{ formData.short_name || '未设置' }}</span>
            <a-input v-else v-model:value="formData.short_name" :maxlength="20" placeholder="请输入学校简称" />
            <a-button 
              type="link" 
              size="small"
              @click="toggleEdit('short_name')"
            >
              {{ editingFields.short_name ? '保存' : '修改' }}
            </a-button>
          </div>
        </a-form-item>

        <!-- 校训 -->
        <a-form-item label="校训" name="motto">
          <div class="editable-field">
            <span v-if="!editingFields.motto" class="field-value">{{ formData.motto || '未设置' }}</span>
            <a-textarea 
              v-else 
              v-model:value="formData.motto" 
              :maxlength="200" 
              :rows="3"
              placeholder="请输入校训"
            />
            <a-button 
              type="link" 
              size="small"
              @click="toggleEdit('motto')"
            >
              {{ editingFields.motto ? '保存' : '修改' }}
            </a-button>
          </div>
        </a-form-item>

        <!-- 学校Logo -->
        <a-form-item label="学校Logo">
          <div class="logo-section">
            <div class="logo-preview">
              <img 
                v-if="formData.logo_url" 
                :src="formData.logo_url" 
                alt="学校Logo"
                class="logo-image"
              />
              <div v-else class="logo-placeholder">
                <PictureOutlined />
                <p>暂无Logo</p>
              </div>
            </div>
            <div class="logo-actions">
              <a-upload
                :before-upload="handleBeforeUpload"
                :show-upload-list="false"
                accept=".jpg,.jpeg,.png"
              >
                <a-button type="primary" :loading="uploading">
                  <UploadOutlined />
                  上传图片
                </a-button>
              </a-upload>
              <p class="upload-tip">支持 JPG、PNG 格式，文件大小不超过 2MB</p>
            </div>
          </div>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 图片裁剪弹窗 -->
    <a-modal
      v-model:open="cropModalVisible"
      title="裁剪Logo"
      width="800px"
      @ok="handleCropConfirm"
      @cancel="handleCropCancel"
    >
      <div class="crop-container">
        <img
          ref="cropImage"
          :src="cropImageSrc"
          alt="待裁剪图片"
          style="max-width: 100%"
        />
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { PictureOutlined, UploadOutlined } from '@ant-design/icons-vue';
import { getSchoolInfo, updateSchoolInfo, uploadSchoolLogo } from '@/api/system';
import type { SchoolInfo } from '@/api/system';
import Cropper from 'cropperjs';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

// 响应式数据
const loading = ref(false);
const uploading = ref(false);
const cropModalVisible = ref(false);
const cropImageSrc = ref('');
const cropImage = ref<HTMLImageElement>();
const cropper = ref<Cropper>();
const currentFile = ref<File>();

// 表单数据
const formData = reactive<Partial<SchoolInfo>>({
  name: '',
  short_name: '',
  motto: '',
  logo_url: ''
});

// 编辑状态
const editingFields = reactive({
  name: false,
  short_name: false,
  motto: false
});

// 原始数据备份
const originalData = reactive<Partial<SchoolInfo>>({});

// 学校ID（这里假设为1，实际应该从路由或配置获取）
const schoolId = 1;

// 获取学校信息
const loadSchoolInfo = async () => {
  loading.value = true;
  try {
    const response = await getSchoolInfo(schoolId);
    console.log('学校信息响应:', response);
    
    // 处理不同的响应格式
    let schoolData = null;
    if (response && response.code === '0000' && response.data) {
      // 标准ApiResponse格式
      schoolData = response.data;
    } else if (response && response.id) {
      // 直接是数据对象
      schoolData = response;
    } else if (response && response.data && !response.code) {
      // 有data字段但没有code
      schoolData = response.data;
    }
    
    if (schoolData) {
      Object.assign(formData, {
        name: schoolData.name || '',
        short_name: schoolData.short_name || '',
        motto: schoolData.motto || '',
        logo_url: schoolData.logo_url || ''
      });
      Object.assign(originalData, formData);
      console.log('学校信息已加载:', formData);
    } else {
      console.warn('无法解析响应格式:', response);
      message.error('加载学校信息失败');
    }
  } catch (error) {
    console.error('加载学校信息失败:', error);
    message.error('加载学校信息失败');
  } finally {
    loading.value = false;
  }
};

// 切换编辑状态
const toggleEdit = async (field: string) => {
  if (editingFields[field]) {
    // 保存字段
    await saveField(field);
  } else {
    // 开始编辑
    editingFields[field] = true;
  }
};

// 保存单个字段
const saveField = async (field: string) => {
  if (!formData[field] && field === 'name') {
    message.error('学校名称不能为空');
    return;
  }

  // 验证字符长度
  const maxLengths = { name: 50, short_name: 20, motto: 200 };
  if (formData[field] && formData[field].length > maxLengths[field]) {
    message.error(`字符长度不能超过${maxLengths[field]}个`);
    return;
  }

  try {
    const updateData = { [field]: formData[field] };
    const response = await updateSchoolInfo(schoolId, updateData);
    console.log('保存响应:', response);
    
    // 处理不同的响应格式
    let success = false;
    if (response && response.code === '0000') {
      // 标准ApiResponse格式
      success = true;
      // 如果有data字段，更新formData
      if (response.data) {
        formData[field] = response.data[field] || formData[field];
      }
    } else if (response && response.id) {
      // 直接是数据对象
      success = true;
      formData[field] = response[field] || formData[field];
    }
    
    if (success) {
      message.success(`${getFieldLabel(field)}修改成功`);
      editingFields[field] = false;
      originalData[field] = formData[field];
      // 重新加载数据以确保同步
      await loadSchoolInfo();
    } else {
      message.error(response?.message || '修改失败');
      // 回滚数据
      formData[field] = originalData[field];
    }
  } catch (error: any) {
    console.error('保存失败:', error);
    message.error(error.response?.data?.detail || error.message || '保存失败');
    // 回滚数据
    formData[field] = originalData[field];
  }
};

// 获取字段标签
const getFieldLabel = (field: string): string => {
  const labels = {
    name: '学校名称',
    short_name: '学校简称', 
    motto: '校训'
  };
  return labels[field] || field;
};

// 文件上传前处理
const handleBeforeUpload = (file: File) => {
  // 验证文件类型
  const isImage = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isImage) {
    message.error('只能上传 JPG/PNG 格式的图片');
    return false;
  }

  // 验证文件大小
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB');
    return false;
  }

  // 显示裁剪弹窗
  currentFile.value = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    cropImageSrc.value = e.target?.result as string;
    cropModalVisible.value = true;
  };
  reader.readAsDataURL(file);

  return false; // 阻止自动上传
};

// 初始化裁剪器
const initCropper = () => {
  if (cropImage.value && cropImageSrc.value) {
    cropper.value = new Cropper(cropImage.value, {
      aspectRatio: 1, // 1:1比例
      viewMode: 1,
      autoCropArea: 0.8,
      responsive: true,
      cropBoxResizable: true,
      cropBoxMovable: true
    });
  }
};

// 确认裁剪
const handleCropConfirm = async () => {
  if (!cropper.value || !currentFile.value) return;

  uploading.value = true;
  try {
    // 获取裁剪数据
    const cropData = cropper.value.getCropBoxData();
    const imageData = cropper.value.getImageData();
    
    // 计算实际的裁剪坐标
    const scaleX = cropper.value.getCanvasData().naturalWidth / imageData.width;
    const scaleY = cropper.value.getCanvasData().naturalHeight / imageData.height;
    
    const actualCropData = {
      x: Math.round(cropData.left * scaleX),
      y: Math.round(cropData.top * scaleY),
      width: Math.round(cropData.width * scaleX),
      height: Math.round(cropData.height * scaleY)
    };

    // 上传裁剪后的图片
    const response = await uploadSchoolLogo(schoolId, currentFile.value, actualCropData);
    
    // 如果响应有logo_url字段，说明上传成功
    if (response && response.logo_url) {
      message.success('Logo上传成功');
      formData.logo_url = response.logo_url;
      cropModalVisible.value = false;
    } else {
      message.error('上传失败');
    }
  } catch (error) {
    console.error('上传失败:', error);
    message.error('上传失败');
  } finally {
    uploading.value = false;
  }
};

// 取消裁剪
const handleCropCancel = () => {
  cropModalVisible.value = false;
  if (cropper.value) {
    cropper.value.destroy();
    cropper.value = undefined;
  }
};

// 监听裁剪弹窗打开
const watchCropModal = () => {
  if (cropModalVisible.value) {
    // 等待DOM更新后初始化裁剪器
    setTimeout(initCropper, 100);
  }
};

// 页面初始化
onMounted(() => {
  loadSchoolInfo();
});

// 监听裁剪弹窗状态
watch(cropModalVisible, watchCropModal);
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.editable-field {
  display: flex;
  align-items: center;
  gap: 12px;
}

.field-value {
  flex: 1;
  min-height: 32px;
  line-height: 32px;
  color: rgba(0, 0, 0, 0.85);
}

.logo-section {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.logo-preview {
  width: 120px;
  height: 120px;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

.logo-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.logo-placeholder {
  text-align: center;
  color: #bfbfbf;
}

.logo-placeholder .anticon {
  font-size: 32px;
  margin-bottom: 8px;
}

.logo-actions {
  flex: 1;
}

.upload-tip {
  margin-top: 8px;
  color: #8c8c8c;
  font-size: 12px;
}

.crop-container {
  max-height: 400px;
  overflow: hidden;
  position: relative;
}

/* Cropper styles */
.crop-container img {
  display: block;
  max-width: 100%;
}

:deep(.cropper-container) {
  direction: ltr;
  position: relative;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

:deep(.cropper-wrap-box),
:deep(.cropper-canvas),
:deep(.cropper-drag-box),
:deep(.cropper-crop-box),
:deep(.cropper-modal) {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

:deep(.cropper-canvas) {
  overflow: hidden;
}

:deep(.cropper-drag-box) {
  opacity: 0;
  background-color: #fff;
}

:deep(.cropper-modal) {
  background-color: #000;
  opacity: 0.5;
}

:deep(.cropper-view-box) {
  display: block;
  overflow: hidden;
  width: 100%;
  height: 100%;
  outline: 1px solid #39f;
  outline-color: rgba(51, 153, 255, 0.75);
}

:deep(.cropper-dashed) {
  position: absolute;
  display: block;
  opacity: 0.5;
  border: 0 dashed #eee;
}

:deep(.cropper-dashed.dashed-h) {
  top: 33.33333%;
  left: 0;
  width: 100%;
  height: 33.33333%;
  border-top-width: 1px;
  border-bottom-width: 1px;
}

:deep(.cropper-dashed.dashed-v) {
  top: 0;
  left: 33.33333%;
  width: 33.33333%;
  height: 100%;
  border-right-width: 1px;
  border-left-width: 1px;
}

:deep(.cropper-center) {
  position: absolute;
  top: 50%;
  left: 50%;
  display: block;
  width: 0;
  height: 0;
  opacity: 0.75;
  transform: translate(-50%, -50%);
}

:deep(.cropper-center::before),
:deep(.cropper-center::after) {
  position: absolute;
  display: block;
  content: ' ';
  background-color: #eee;
}

:deep(.cropper-center::before) {
  top: 0;
  left: -3px;
  width: 7px;
  height: 1px;
}

:deep(.cropper-center::after) {
  top: -3px;
  left: 0;
  width: 1px;
  height: 7px;
}

:deep(.cropper-face),
:deep(.cropper-line),
:deep(.cropper-point) {
  position: absolute;
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0.1;
}

:deep(.cropper-face) {
  top: 0;
  left: 0;
  background-color: #fff;
}

:deep(.cropper-line) {
  background-color: #39f;
}

:deep(.cropper-line.line-e) {
  top: 0;
  right: -3px;
  width: 5px;
  cursor: ew-resize;
}

:deep(.cropper-line.line-n) {
  top: -3px;
  left: 0;
  height: 5px;
  cursor: ns-resize;
}

:deep(.cropper-line.line-w) {
  top: 0;
  left: -3px;
  width: 5px;
  cursor: ew-resize;
}

:deep(.cropper-line.line-s) {
  bottom: -3px;
  left: 0;
  height: 5px;
  cursor: ns-resize;
}

:deep(.cropper-point) {
  width: 5px;
  height: 5px;
  opacity: 0.75;
  background-color: #39f;
}

:deep(.cropper-point.point-e) {
  top: 50%;
  right: -3px;
  margin-top: -3px;
  cursor: ew-resize;
}

:deep(.cropper-point.point-n) {
  top: -3px;
  left: 50%;
  margin-left: -3px;
  cursor: ns-resize;
}

:deep(.cropper-point.point-w) {
  top: 50%;
  left: -3px;
  margin-top: -3px;
  cursor: ew-resize;
}

:deep(.cropper-point.point-s) {
  bottom: -3px;
  left: 50%;
  margin-left: -3px;
  cursor: ns-resize;
}

:deep(.cropper-point.point-ne) {
  top: -3px;
  right: -3px;
  cursor: nesw-resize;
}

:deep(.cropper-point.point-nw) {
  top: -3px;
  left: -3px;
  cursor: nwse-resize;
}

:deep(.cropper-point.point-sw) {
  bottom: -3px;
  left: -3px;
  cursor: nesw-resize;
}

:deep(.cropper-point.point-se) {
  right: -3px;
  bottom: -3px;
  width: 20px;
  height: 20px;
  cursor: nwse-resize;
  opacity: 1;
}

:deep(.cropper-point.point-se::before) {
  position: absolute;
  right: -50%;
  bottom: -50%;
  display: block;
  width: 200%;
  height: 200%;
  content: ' ';
  opacity: 0;
  background-color: #39f;
}

:deep(.cropper-invisible) {
  opacity: 0;
}

:deep(.cropper-bg) {
  background-image: url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAQMAAAAlPW0iAAAAA3NCSVQICAjb4U/gAAAABlBMVBEUd3cAAACO6jvdAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAHHRFWHRTb2Z0d2FyZQBBZG9iZSBGaXJld29ya3MgQ1M26LyyjAAAABFJREFUCJlj+M/AgBVhF/0PAH6/D/HkDxOGAAAAAElFTkSuQmCC');
}

:deep(.cropper-hide) {
  position: absolute;
  display: block;
  width: 0;
  height: 0;
}

:deep(.cropper-hidden) {
  display: none !important;
}

:deep(.cropper-move) {
  cursor: move;
}

:deep(.cropper-crop) {
  cursor: crosshair;
}

:deep(.cropper-disabled .cropper-drag-box),
:deep(.cropper-disabled .cropper-face),
:deep(.cropper-disabled .cropper-line),
:deep(.cropper-disabled .cropper-point) {
  cursor: not-allowed;
}

:deep(.ant-card-head-title) {
  font-size: 18px;
  font-weight: 600;
}
</style> 