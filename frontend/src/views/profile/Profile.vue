<template>
  <div class="profile-container">
    <div class="profile-header">
      <h2>个人中心</h2>
    </div>

    <div class="profile-content">
      <!-- User Info Card -->
      <a-card title="基本信息" class="profile-card">
        <a-descriptions :column="2" bordered>
          <a-descriptions-item label="用户名">{{ userStore.userInfo.username }}</a-descriptions-item>
          <a-descriptions-item label="姓名">{{ userStore.userInfo.realname || '-' }}</a-descriptions-item>
          <a-descriptions-item label="角色">
            <a-tag :color="roleColor">{{ roleText }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="邮箱">{{ profileData.email || '-' }}</a-descriptions-item>
          <a-descriptions-item label="注册时间">{{ profileData.created_at || '-' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- Change Password Card -->
      <a-card title="修改密码" class="profile-card" style="margin-top: 24px;">
        <a-form
          :model="passwordForm"
          :rules="passwordRules"
          ref="passwordFormRef"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 12 }"
          @finish="handleChangePassword"
        >
          <a-form-item label="当前密码" name="old_password">
            <a-input-password v-model:value="passwordForm.old_password" placeholder="请输入当前密码" />
          </a-form-item>
          <a-form-item label="新密码" name="new_password">
            <a-input-password v-model:value="passwordForm.new_password" placeholder="请输入新密码（至少6位）" />
          </a-form-item>
          <a-form-item label="确认密码" name="confirm_password">
            <a-input-password v-model:value="passwordForm.confirm_password" placeholder="请再次输入新密码" />
          </a-form-item>
          <a-form-item :wrapper-col="{ offset: 4 }">
            <a-button type="primary" html-type="submit" :loading="changingPassword">
              修改密码
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useUserStore } from '@/stores/user';
import axios from 'axios';

const userStore = useUserStore();
const passwordFormRef = ref();
const changingPassword = ref(false);

const profileData = ref({
  email: '',
  created_at: '',
});

const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
});

const roleText = computed(() => {
  switch (userStore.userInfo.role) {
    case 'admin': return '管理员';
    case 'teacher': return '教师';
    case 'student': return '学生';
    default: return '未知';
  }
});

const roleColor = computed(() => {
  switch (userStore.userInfo.role) {
    case 'admin': return 'red';
    case 'teacher': return 'blue';
    case 'student': return 'green';
    default: return 'default';
  }
});

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码' }],
  new_password: [
    { required: true, message: '请输入新密码' },
    { min: 6, message: '密码至少6位' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码' },
    {
      validator: (_rule: any, value: string) => {
        if (value && value !== passwordForm.value.new_password) {
          return Promise.reject('两次输入的密码不一致');
        }
        return Promise.resolve();
      },
    },
  ],
};

const loadProfile = async () => {
  try {
    const token = localStorage.getItem('token');
    const res = await axios.get('/api/user/profile', {
      headers: { Authorization: `Bearer ${token}` },
    });
    profileData.value = res.data;
  } catch {
    // Fallback to store data
  }
};

const handleChangePassword = async () => {
  changingPassword.value = true;
  try {
    const token = localStorage.getItem('token');
    await axios.post(
      '/api/change-password',
      {
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password,
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    message.success('密码修改成功');
    passwordForm.value = { old_password: '', new_password: '', confirm_password: '' };
    passwordFormRef.value?.resetFields();
  } catch (err: any) {
    const detail = err?.response?.data?.detail || '密码修改失败';
    message.error(detail);
  } finally {
    changingPassword.value = false;
  }
};

onMounted(() => {
  loadProfile();
});
</script>

<style scoped>
.profile-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
}

.profile-header {
  margin-bottom: 24px;
}

.profile-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
  margin: 0;
}

.profile-card {
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
</style>
