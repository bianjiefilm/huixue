<template>
  <div class="exam-center">
    <!-- 列表三页：父级 L-Full 壳 + Tab；表单/编辑页自带壳，避免双 padding -->
    <PageShell v-if="isListRoute" max-width="wide">
      <PageHeaderBar
        title="考试中心"
        subtitle="创建试卷、管理考试，提供完整的在线考试解决方案"
      />
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
    </PageShell>
    <router-view v-else />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'

const router = useRouter()
const route = useRoute()

const LIST_KEYS = ['paper-bank', 'question-bank', 'my-exams'] as const

const activeTab = ref<string>('paper-bank')

const isListRoute = computed(() => {
  const path = route.path
  return LIST_KEYS.some((key) => path.includes(key))
})

const syncActiveTab = (path: string) => {
  if (path.includes('paper-bank')) {
    activeTab.value = 'paper-bank'
  } else if (path.includes('question-bank')) {
    activeTab.value = 'question-bank'
  } else if (path.includes('my-exams')) {
    activeTab.value = 'my-exams'
  }
}

const handleTabChange = (key: string | number) => {
  const k = String(key)
  if (k === 'paper-bank') {
    router.push('/exam/paper-bank')
  } else if (k === 'question-bank') {
    router.push('/exam/question-bank')
  } else if (k === 'my-exams') {
    router.push('/exam/my-exams')
  }
}

onMounted(() => {
  syncActiveTab(route.path)
})

watch(
  () => route.path,
  (path) => {
    syncActiveTab(path)
  }
)
</script>

<style scoped>
.exam-center {
  width: 100%;
  min-height: 0;
}

.tab-container {
  background-color: transparent;
}
</style>
