<template>
  <div class="exam-center-container">
    <div class="page-header">
      <h1>考试中心</h1>
      <p>创建试卷、管理考试，提供完整的在线考试解决方案</p>
    </div>
    
    <a-tabs
      v-model:activeKey="activeTab"
      @change="handleTabChange"
      class="tab-container"
    >
      <a-tab-pane key="paper-bank" tab="试卷库">
        <router-view v-if="activeTab === 'paper-bank'" />
      </a-tab-pane>
      <a-tab-pane key="question-bank" tab="试题库">
        <router-view v-if="activeTab === 'question-bank'" />
      </a-tab-pane>
      <a-tab-pane key="my-exams" tab="我的考试">
        <router-view v-if="activeTab === 'my-exams'" />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// 根据路由路径设置激活的标签页
const activeTab = ref('paper-bank');

// 处理标签页切换
const handleTabChange = (key: string) => {
  if (key === 'paper-bank') {
    router.push('/exam/paper-bank');
  } else if (key === 'question-bank') {
    router.push('/exam/question-bank');
  } else if (key === 'my-exams') {
    router.push('/exam/my-exams');
  }
};

// 根据当前路由设置激活的标签页
onMounted(() => {
  const path = route.path;
  if (path.includes('paper-bank')) {
    activeTab.value = 'paper-bank';
  } else if (path.includes('question-bank')) {
    activeTab.value = 'question-bank';
  } else if (path.includes('my-exams')) {
    activeTab.value = 'my-exams';
  }
});

// 监听路由变化，更新激活的标签页
watch(
  () => route.path,
  (path) => {
    if (path.includes('paper-bank')) {
      activeTab.value = 'paper-bank';
    } else if (path.includes('question-bank')) {
      activeTab.value = 'question-bank';
    } else if (path.includes('my-exams')) {
      activeTab.value = 'my-exams';
    }
  }
);
</script>

<style scoped>
.exam-center-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background-color: #fff;
  min-height: calc(100vh - 64px - 70px);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.page-header p {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.tab-container {
  background-color: #fff;
}
</style> 