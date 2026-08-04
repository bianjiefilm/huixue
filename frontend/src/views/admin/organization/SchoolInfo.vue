<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell. Routed school info is system/school-info.vue -->
  <div class="admin-page">
    <PageHeaderBar title="学校信息" subtitle="查看和编辑学校基础信息" />

    <a-card title="基础信息" :bordered="false" class="info-card">
      <a-descriptions :column="1" bordered>
        <a-descriptions-item label="学校名称">
          <template v-if="editing.schoolName">
            <a-input 
              v-model:value="formState.schoolName" 
              placeholder="请输入学校名称" 
              :maxLength="50"
              allow-clear
              class="edit-input"
            />
            <a-button type="primary" @click="saveSchoolName" class="action-btn">保存</a-button>
            <a-button @click="cancelEdit('schoolName')" class="action-btn">取消</a-button>
          </template>
          <template v-else>
            <span>{{ schoolInfo.schoolName || '未设置' }}</span>
            <a-button type="link" @click="startEdit('schoolName')">修改</a-button>
          </template>
        </a-descriptions-item>

        <a-descriptions-item label="学校简称">
          <template v-if="editing.shortName">
            <a-input 
              v-model:value="formState.shortName" 
              placeholder="请输入学校简称" 
              :maxLength="20"
              allow-clear
              class="edit-input"
            />
            <a-button type="primary" @click="saveShortName" class="action-btn">保存</a-button>
            <a-button @click="cancelEdit('shortName')" class="action-btn">取消</a-button>
          </template>
          <template v-else>
            <span>{{ schoolInfo.shortName || '未设置' }}</span>
            <a-button type="link" @click="startEdit('shortName')">修改</a-button>
          </template>
        </a-descriptions-item>

        <a-descriptions-item label="校训">
          <template v-if="editing.motto">
            <a-textarea 
              v-model:value="formState.motto" 
              placeholder="请输入校训" 
              :maxLength="200"
              :rows="3"
              allow-clear
              class="edit-input"
            />
            <a-button type="primary" @click="saveMotto" class="action-btn">保存</a-button>
            <a-button @click="cancelEdit('motto')" class="action-btn">取消</a-button>
          </template>
          <template v-else>
            <span>{{ schoolInfo.motto || '未设置' }}</span>
            <a-button type="link" @click="startEdit('motto')">修改</a-button>
          </template>
        </a-descriptions-item>

        <a-descriptions-item label="学校LOGO">
          <div class="logo-container">
            <img 
              :src="schoolInfo.logo" 
              alt="学校LOGO" 
              class="school-logo" 
            />
            <a-upload
              name="logo"
              :showUploadList="false"
              :beforeUpload="beforeUpload"
              @change="handleLogoChange"
              accept=".jpg,.jpeg,.png"
            >
              <a-button type="primary">上传图片</a-button>
            </a-upload>
            <div class="upload-tip">支持 .jpg、.png 格式，文件大小不超过 2MB</div>
          </div>
        </a-descriptions-item>
      </a-descriptions>
    </a-card>

    <!-- 图片裁剪模态框 -->
    <a-modal
      v-model:open="cropModalVisible"
      title="裁剪图片"
      :footer="null"
      @cancel="cancelCrop"
      width="800px"
    >
      <div class="crop-container">
        <div style="max-height: 500px; overflow: auto;">
          <!-- 此处实际项目中应引入图片裁剪组件 -->
          <img :src="previewImage" alt="预览图" style="max-width: 100%;" v-if="previewImage" />
        </div>
        <div class="crop-actions" style="margin-top: 16px; text-align: right;">
          <a-button @click="cancelCrop" style="margin-right: 8px;">取消</a-button>
          <a-button type="primary" @click="saveCrop">保存</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { getSchoolInfo, updateSchoolInfo } from '@/api/system';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const SCHOOL_ID = 1; // 默认学校ID

// 学校信息数据
const schoolInfo = reactive({
  schoolName: '',
  shortName: '',
  motto: '',
  logo: ''
});

// 表单数据
const formState = reactive({
  schoolName: '',
  shortName: '',
  motto: ''
});

// 编辑状态控制
const editing = reactive({
  schoolName: false,
  shortName: false,
  motto: false
});

// 图片裁剪相关
const cropModalVisible = ref(false);
const previewImage = ref('');
const fileList = ref([]);

// 加载学校信息
onMounted(async () => {
  try {
    console.log('开始加载学校信息, SCHOOL_ID:', SCHOOL_ID);
    const response = await getSchoolInfo(SCHOOL_ID);
    console.log('学校信息响应:', response);
    console.log('响应类型:', typeof response);
    console.log('响应code:', response?.code);
    console.log('响应data:', response?.data);
    
    // 处理响应数据
    if (response) {
      // 如果响应本身就是数据对象（没有包装）
      if (response.name) {
        schoolInfo.schoolName = response.name || '未设置';
        schoolInfo.shortName = response.short_name || '未设置';
        schoolInfo.motto = response.motto || '未设置';
        schoolInfo.logo = response.logo_url || '';
        console.log('直接使用响应数据:', schoolInfo);
      }
      // 如果响应有code和data字段
      else if (response.code === '0000' && response.data) {
        schoolInfo.schoolName = response.data.name || '未设置';
        schoolInfo.shortName = response.data.short_name || '未设置';
        schoolInfo.motto = response.data.motto || '未设置';
        schoolInfo.logo = response.data.logo_url || '';
        console.log('使用响应data字段:', schoolInfo);
      }
      // 如果响应就是data对象
      else if (response.data && !response.code) {
        schoolInfo.schoolName = response.data.name || '未设置';
        schoolInfo.shortName = response.data.short_name || '未设置';
        schoolInfo.motto = response.data.motto || '未设置';
        schoolInfo.logo = response.data.logo_url || '';
        console.log('使用响应data（无code）:', schoolInfo);
      } else {
        console.warn('无法解析响应格式:', response);
      }
    } else {
      console.warn('响应为空');
    }
    
    console.log('最终学校信息:', schoolInfo);
  } catch (error: any) {
    message.error('获取学校信息失败');
    console.error('获取学校信息失败:', error);
    console.error('错误详情:', error.response?.data || error.message);
  }
});

// 开始编辑
const startEdit = (field: keyof typeof editing) => {
  // 重置表单值为当前值
  formState[field] = schoolInfo[field];
  // 设置编辑状态
  editing[field] = true;
};

// 取消编辑
const cancelEdit = (field: keyof typeof editing) => {
  editing[field] = false;
};

// 保存学校名称
const saveSchoolName = async () => {
  try {
    if (!formState.schoolName.trim()) {
      message.error('学校名称不能为空');
      return;
    }
    
    const response = await updateSchoolInfo(SCHOOL_ID, {
      name: formState.schoolName.trim()
    });
    
    console.log('保存学校名称响应:', response);
    
    if (response && response.code === '0000') {
      // 更新本地状态
      schoolInfo.schoolName = formState.schoolName.trim();
      message.success('学校名称修改成功');
      editing.schoolName = false;
      // 重新加载数据以确保同步
      const refreshResponse = await getSchoolInfo(SCHOOL_ID);
      if (refreshResponse && refreshResponse.code === '0000' && refreshResponse.data) {
        schoolInfo.schoolName = refreshResponse.data.name || '未设置';
      }
    } else {
      message.error(response?.message || '保存失败');
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '保存失败');
    console.error('保存学校名称失败:', error);
  }
};

// 保存学校简称
const saveShortName = async () => {
  try {
    const response = await updateSchoolInfo(SCHOOL_ID, {
      short_name: formState.shortName.trim()
    });
    
    if (response && response.code === '0000') {
      schoolInfo.shortName = formState.shortName.trim();
      message.success('学校简称修改成功');
      editing.shortName = false;
      // 重新加载数据
      const refreshResponse = await getSchoolInfo(SCHOOL_ID);
      if (refreshResponse && refreshResponse.code === '0000' && refreshResponse.data) {
        schoolInfo.shortName = refreshResponse.data.short_name || '未设置';
      }
    } else {
      message.error(response?.message || '保存失败');
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '保存失败');
    console.error('保存学校简称失败:', error);
  }
};

// 保存校训
const saveMotto = async () => {
  try {
    const response = await updateSchoolInfo(SCHOOL_ID, {
      motto: formState.motto.trim()
    });
    
    if (response && response.code === '0000') {
      schoolInfo.motto = formState.motto.trim();
      message.success('校训修改成功');
      editing.motto = false;
      // 重新加载数据
      const refreshResponse = await getSchoolInfo(SCHOOL_ID);
      if (refreshResponse && refreshResponse.code === '0000' && refreshResponse.data) {
        schoolInfo.motto = refreshResponse.data.motto || '未设置';
      }
    } else {
      message.error(response?.message || '保存失败');
    }
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '保存失败');
    console.error('保存校训失败:', error);
  }
};

// 图片上传前验证
const beforeUpload = (file: File) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('只能上传JPG/PNG格式的图片!');
    return false;
  }
  
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过2MB!');
    return false;
  }
  
  // 显示裁剪模态框
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = () => {
    previewImage.value = reader.result as string;
    cropModalVisible.value = true;
  };
  
  // 阻止自动上传
  return false;
};

// 处理Logo上传
const handleLogoChange = (info: any) => {
  // 由于我们阻止了自动上传，这里主要用于处理文件列表
  fileList.value = info.fileList.slice(-1);
};

// 取消裁剪
const cancelCrop = () => {
  cropModalVisible.value = false;
  previewImage.value = '';
  fileList.value = [];
};

// 保存裁剪后的图片
const saveCrop = () => {
  // 在实际项目中，这里应该处理裁剪后的图片并上传
  // 模拟上传成功
  schoolInfo.logo = previewImage.value;
  message.success('学校LOGO修改成功');
  cropModalVisible.value = false;
};
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.info-card {
  margin-top: 0;
}

.edit-input {
  width: 300px;
  margin-right: 8px;
}

.action-btn {
  margin-right: 8px;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.school-logo {
  width: 150px;
  height: 150px;
  object-fit: contain;
  border: 1px solid #d9d9d9;
  margin-bottom: 16px;
}

.upload-tip {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 8px;
}
</style> 