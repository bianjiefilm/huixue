<template>
  <a-form
    :model="formState"
    :rules="rules"
    :label-col="{ span: 5 }"
    :wrapper-col="{ span: 19 }"
    @finish="onFinish"
  >
    <a-form-item name="name" label="课堂名称">
      <a-input v-model:value="formState.name" placeholder="请输入课堂名称，例如：Python 数据分析" />
    </a-form-item>
    
    <a-form-item name="description" label="课堂描述">
      <a-textarea v-model:value="formState.description" placeholder="请输入课堂描述（选填）" :rows="3" />
    </a-form-item>
    <a-form-item name="credits" label="学分">
      <a-input-number
        v-model:value="formState.credits"
        :min="1"
        :max="100"
        placeholder="1-100"
        style="width: 100%"
      />
    </a-form-item>
    
    <a-form-item name="startDate" label="开始时间">
      <a-date-picker
        v-model:value="formState.startDate"
        format="YYYY-MM-DD"
        style="width: 100%"
        :disabledDate="disabledStartDate"
      />
    </a-form-item>
    
    <a-form-item name="endDate" label="结束时间">
      <a-date-picker
        v-model:value="formState.endDate"
        format="YYYY-MM-DD"
        style="width: 100%"
        :disabledDate="disabledEndDate"
      />
    </a-form-item>
    
    <a-form-item name="modules" label="选择模块">
      <a-checkbox-group v-model:value="formState.modules">
        <a-checkbox value="course_material">课程教材</a-checkbox>
        <a-checkbox value="practice">微型实验</a-checkbox>
        <a-checkbox value="training">项目实训</a-checkbox>
        <a-checkbox value="exam">考试测验</a-checkbox>
      </a-checkbox-group>
      <div style="margin-top: 8px; color: #999; font-size: 12px;">
        选择要在该课堂中使用的功能模块
      </div>
    </a-form-item>
    
    <a-form-item name="coverImage" label="课堂封面">
      <a-upload
        name="file"
        list-type="picture-card"
        class="cover-uploader"
        :show-upload-list="false"
        :before-upload="beforeUpload"
        @change="handleCoverChange"
      >
        <div v-if="coverImageUrl">
          <img :src="coverImageUrl" alt="cover" style="width: 100%; height: 100%; object-fit: cover;" />
        </div>
        <div v-else>
          <loading-outlined v-if="uploadLoading"></loading-outlined>
          <plus-outlined v-else></plus-outlined>
          <div style="margin-top: 8px">上传封面</div>
        </div>
      </a-upload>
      <div style="margin-top: 8px; color: #999; font-size: 12px;">
        建议尺寸：16:9，支持jpg、png格式，文件大小不超过2MB
      </div>
    </a-form-item>
    
    <a-form-item :wrapper-col="{ span: 19, offset: 5 }">
      <a-button type="primary" html-type="submit" :loading="loading">提交</a-button>
      <a-button style="margin-left: 8px" @click="onCancel">取消</a-button>
    </a-form-item>
  </a-form>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { LoadingOutlined, PlusOutlined } from '@ant-design/icons-vue';
import type { Rule } from 'ant-design-vue/es/form';
import type { Dayjs } from 'dayjs';
import type { UploadChangeParam } from 'ant-design-vue';
import dayjs from 'dayjs';
import { addClassRoomByCourse } from '@/api/classrooms';

interface FormState {
  name: string;
  description: string;
  credits: number;
  startDate: Dayjs | null;
  endDate: Dayjs | null;
  modules: string[];
}

const emit = defineEmits(['success', 'cancel']);

// 表单状态
const formState = reactive<FormState>({
  name: '',
  description: '',
  credits: 1,
  startDate: null,
  endDate: null,
  modules: ['practice'] // 默认选中微型实验
});

// 加载状态
const loading = ref(false);

// 封面图片相关状态
const coverImageUrl = ref<string>('');
const uploadLoading = ref<boolean>(false);

// 表单验证规则
const rules: Record<string, Rule[]> = {
  name: [
    { required: true, message: '请输入课堂名称', trigger: 'blur' },
    { min: 2, max: 50, message: '课堂名称长度应在2-50个字符之间', trigger: 'blur' }
  ],
  credits: [
    { required: true, message: '请输入学分', trigger: 'change' },
    { type: 'number', min: 1, max: 100, message: '学分应在1-100之间', trigger: 'change' }
  ],
  startDate: [
    { required: true, message: '请选择开始时间', trigger: 'change', type: 'object' }
  ],
  endDate: [
    { required: true, message: '请选择结束时间', trigger: 'change', type: 'object' }
  ]
};

// 开始日期不做限制，允许选择过去的日期（用于创建历史课堂或补录）
const disabledStartDate = (current: Dayjs) => {
  return false;
};

// 限制结束日期必须在开始日期之后
const disabledEndDate = (current: Dayjs) => {
  if (!current || !formState.startDate) {
    return false;
  }
  return current.valueOf() <= formState.startDate.valueOf();
};

// 图片上传前验证
const beforeUpload = (file: File) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片!');
    return false;
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB!');
    return false;
  }
  return false; // 阻止自动上传，手动处理
};

// 处理图片上传
const handleCoverChange = (info: UploadChangeParam) => {
  if (info.file.originFileObj) {
    const file = info.file.originFileObj;
    uploadLoading.value = true;
    
    // 创建文件读取器来预览图片
    const reader = new FileReader();
    reader.onload = (e) => {
      coverImageUrl.value = e.target?.result as string;
      uploadLoading.value = false;
    };
    reader.readAsDataURL(file);
  }
};

// 提交表单
const onFinish = async (values: FormState) => {
  loading.value = true;
  try {
    // 转换日期格式
    const startDate = values.startDate ? values.startDate.format('YYYY-MM-DD HH:mm:ss') : '';
    const endDate = values.endDate ? values.endDate.format('YYYY-MM-DD HH:mm:ss') : '';
    
    // 自动计算学期和学年
    const startDayjs = values.startDate || dayjs();
    const month = startDayjs.month() + 1; // dayjs month is 0-based
    const year = startDayjs.year();
    const semester = month >= 2 && month < 8 ? 'SPRING' : 'FALL';
    const academic_year = semester === 'SPRING' 
      ? `${year - 1}-${year}` 
      : `${year}-${year + 1}`;
    
    // 调用新的API创建课堂
    const newClassroom = await addClassRoomByCourse({
      name: values.name,
      credit: values.credits, // 注意字段名变化
      start_date: startDate,  // 注意字段名变化
      end_date: endDate,      // 注意字段名变化
      semester: semester,
      academic_year: academic_year,
      cover_url: coverImageUrl.value || null, // 添加封面图片
      source_course_id: null, // 暂时为空
      sync_resources_from_source: false,
      sync_assessments_from_source: false
    });
    
    // 提示成功
    message.success('新建课堂成功');
    
    // 通知父组件创建成功
    emit('success', newClassroom);
  } catch (error) {
    if (error instanceof Error) {
      message.error(error.message || '创建课堂失败，请重试');
    } else {
      message.error('创建课堂失败，请重试');
    }
  } finally {
    loading.value = false;
  }
};

// 取消操作
const onCancel = () => {
  emit('cancel');
};
</script>

<style scoped>
.ant-form {
  max-width: 600px;
}

.cover-uploader {
  width: 120px;
  height: 80px;
}

.cover-uploader :deep(.ant-upload) {
  width: 120px;
  height: 80px;
  border-radius: 6px;
}

.cover-uploader :deep(.ant-upload-select) {
  width: 120px !important;
  height: 80px !important;
  border-radius: 6px;
}
</style> 