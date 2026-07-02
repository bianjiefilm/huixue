<template>
  <div class="teacher-form-container">
    <a-page-header
      :title="isEdit ? '编辑教师' : '添加教师'"
      :subtitle="isEdit ? '更新教师信息' : '创建新教师账号'"
      @back="goBack"
    />
    
    <div class="teacher-form-content">
      <a-card :bordered="false">
        <a-form
          :model="formState"
          :rules="formRules"
          ref="formRef"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 16 }"
        >
          <a-form-item name="name" label="姓名" required>
            <a-input v-model:value="formState.name" placeholder="请输入姓名" />
          </a-form-item>
          
          <a-form-item name="code" label="工号" required>
            <a-input v-model:value="formState.code" placeholder="请输入工号" />
          </a-form-item>
          
          <a-form-item name="gender" label="性别">
            <a-radio-group v-model:value="formState.gender">
              <a-radio value="male">男</a-radio>
              <a-radio value="female">女</a-radio>
              <a-radio value="other">其他</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <a-form-item name="phone" label="手机号">
            <a-input v-model:value="formState.phone" placeholder="请输入手机号" />
          </a-form-item>
          
          <a-form-item name="email" label="邮箱">
            <a-input v-model:value="formState.email" placeholder="请输入邮箱" />
          </a-form-item>
          
          <a-form-item name="department" label="所属部门">
            <a-tree-select
              v-model:value="formState.organizationId"
              :tree-data="treeData"
              placeholder="请选择部门"
              style="width: 100%"
              :dropdown-style="{ maxHeight: '400px', overflow: 'auto' }"
              :field-names="{ children: 'children', label: 'title', value: 'key' }"
            />
          </a-form-item>
          
          <a-form-item name="status" label="状态">
            <a-switch v-model:checked="formState.status" />
            <span style="margin-left: 8px">{{ formState.status ? '在职' : '离职' }}</span>
          </a-form-item>
          
          <a-form-item name="avatar" label="头像">
            <a-upload
              name="avatar"
              list-type="picture-card"
              :show-upload-list="false"
              :before-upload="beforeUpload"
              @change="handleAvatarChange"
            >
              <div v-if="!formState.avatar">
                <upload-outlined />
                <div style="margin-top: 8px">上传</div>
              </div>
              <img v-else :src="formState.avatar" style="width: 100%" />
            </a-upload>
          </a-form-item>
          
          <a-form-item :wrapper-col="{ offset: 4, span: 16 }">
            <a-space>
              <a-button type="primary" @click="handleSubmit">提交</a-button>
              <a-button @click="goBack">取消</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import { useDepartmentStore } from '@/stores/department';
import { useTeacherStore } from '@/stores/teacher';

const router = useRouter();
const route = useRoute();
const departmentStore = useDepartmentStore();
const teacherStore = useTeacherStore();

// 判断是否为编辑模式
const isEdit = computed(() => !!route.params.id);

// 表单引用
const formRef = ref();

// 树形数据
const treeData = ref<any[]>([]);

// 表单状态
const formState = reactive({
  name: '',
  code: '',
  gender: 'male',
  phone: '',
  email: '',
  organizationId: '',
  status: true,
  avatar: '',
});

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度必须在2-20个字符之间', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入工号', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_-]+$/, message: '工号只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3456789]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  organizationId: [
    { required: true, message: '请选择所属部门', trigger: 'change' }
  ]
};

// 返回上一页
const goBack = () => {
  router.back();
};

// 上传头像前的处理
const beforeUpload = (file: File) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('只能上传JPG或PNG格式的图片!');
    return false;
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过2MB!');
    return false;
  }
  return false; // 返回false阻止默认上传行为
};

// 处理头像变更
const handleAvatarChange = (info: any) => {
  if (info.file.status === 'uploading') {
    return;
  }
  if (info.file.status === 'done') {
    // 获取上传的头像URL
    formState.avatar = info.file.response.url;
  } else if (info.file.status === 'error') {
    message.error('头像上传失败');
  }
  
  // 这里为了演示，直接使用本地预览
  const reader = new FileReader();
  reader.addEventListener('load', () => {
    formState.avatar = reader.result as string;
  });
  reader.readAsDataURL(info.file.originFileObj);
};

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    
    const teacherData = {
      name: formState.name,
      code: formState.code,
      gender: formState.gender as 'male' | 'female' | 'other',
      phone: formState.phone,
      email: formState.email,
      organizationId: formState.organizationId,
      status: formState.status,
      avatar: formState.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${formState.name}`
    };
    
    if (isEdit.value) {
      // 编辑模式
      await teacherStore.updateTeacher(route.params.id as string, teacherData);
      message.success('教师信息更新成功');
    } else {
      // 添加模式
      await teacherStore.createTeacher(teacherData);
      message.success('教师添加成功');
    }
    
    // 返回列表页
    router.push('/admin/user/teacher');
  } catch (error) {
    console.error('表单验证错误或提交失败:', error);
  }
};

// 加载组织结构树
const loadTreeData = async () => {
  try {
    const result = await departmentStore.getOrganizationTree();
    treeData.value = result || [];
  } catch (error) {
    console.error('加载组织结构树失败:', error);
    message.error('加载组织结构数据失败');
  }
};

// 加载教师信息（编辑模式）
const loadTeacherData = async () => {
  if (!isEdit.value) return;
  
  try {
    const teacherId = route.params.id as string;
    const teacher = await teacherStore.getTeacherDetail(teacherId);
    
    if (teacher) {
      // 填充表单数据
      formState.name = teacher.name;
      formState.code = teacher.code;
      formState.gender = teacher.gender;
      formState.phone = teacher.phone || '';
      formState.email = teacher.email || '';
      formState.organizationId = teacher.organizationId;
      formState.status = teacher.status;
      formState.avatar = teacher.avatar || '';
    } else {
      message.error('未找到教师信息');
      router.push('/admin/user/teacher');
    }
  } catch (error) {
    console.error('加载教师信息失败:', error);
    message.error('加载教师信息失败');
    router.push('/admin/user/teacher');
  }
};

// 组件挂载时执行
onMounted(() => {
  loadTreeData();
  loadTeacherData();
});
</script>

<style scoped>
.teacher-form-container {
  padding: 16px;
}

.teacher-form-content {
  margin-top: 16px;
}
</style> 