<template>
  <PageShell max-width="wide" class="create-project-page">
    <PageHeaderBar
      title="新建实训项目"
      subtitle="教师用户可根据教学安排创建实训项目；公开发布后将显示在项目实训资源库中"
      show-back
      back-to="/project"
    />

    <a-card class="select-card">
      <h2>选择实训类型</h2>
      <p>请选择要创建的实训类型</p>

      <div class="training-type-container">
        <a-row :gutter="[16, 16]">
          <a-col :span="12">
            <a-card hoverable class="type-card" @click="goToDragDropTraining">
              <template #cover>
                <img alt="拖拽式实训封面" src="https://picsum.photos/600/300?random=1" class="card-cover-img" />
              </template>
              <a-card-meta title="拖拽式实训">
                <template #description>
                  <p>拖拽式实训中使用 bigdata-huigoo可视化分析平台与 bigdata-huigoo机器学习开发平台作为实训工具，可使学生通过拖拽式、低代码的方式实现数据分析，满足应用型教学需求。</p>
                  <a-button type="primary" class="btn-select" size="large">选择此类型</a-button>
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
          <a-col :span="12">
            <a-card hoverable class="type-card" @click="goToCodingTraining">
              <template #cover>
                <img alt="编码式实训封面" src="https://picsum.photos/600/300?random=2" class="card-cover-img" />
              </template>
              <a-card-meta title="编码式实训">
                <template #description>
                  <p>编码式实训 Jupyter notebook 作为实训工具，支持创建在线编码式的实训课程，帮助学生进行编码形式的数据清理、建模分析、机器学习等方向的练习。</p>
                  <a-button type="primary" class="btn-select" size="large">选择此类型</a-button>
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
        </a-row>
      </div>
    </a-card>
  </PageShell>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useUserStore } from '../../../stores/user';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const router = useRouter();
const userStore = useUserStore();

// 检查用户是否为教师
const checkTeacherRole = () => {
  if (!userStore.isLoggedIn) {
    router.push('/auth/login');
    return false;
  }
  
  if (userStore.userInfo.role !== 'teacher' && userStore.userInfo.role !== 'admin') {
    // 如果不是教师或管理员，跳转到项目页面
    router.push('/project');
    return false;
  }
  
  return true;
};

// 前往拖拽式实训创建页面
const goToDragDropTraining = () => {
  if (checkTeacherRole()) {
    router.push('/project/create/dragdrop');
  }
};

// 前往编码式实训创建页面
const goToCodingTraining = () => {
  if (checkTeacherRole()) {
    router.push('/project/create/coding');
  }
};
</script>

<style scoped>
.create-project-page {
  min-height: 100%;
}

.select-card {
  margin-bottom: var(--hx-space-5);
  text-align: center;
}

.select-card h2 {
  font-size: var(--hx-font-size-lg, 18px);
  margin-bottom: var(--hx-space-3);
}

.training-type-container {
  margin-top: var(--hx-space-5);
}

.type-card {
  height: 100%;
  transition: all 0.3s;
  margin-bottom: var(--hx-space-4);
}

.type-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.09);
}

.card-cover-img {
  height: 200px;
  object-fit: cover;
}

.btn-select {
  margin-top: var(--hx-space-4);
}
</style> 