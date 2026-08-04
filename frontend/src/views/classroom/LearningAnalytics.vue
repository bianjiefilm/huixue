<template>
  <PageShell max-width="wide" class="learning-analytics-page">
    <PageHeaderBar
      title="学情分析"
      subtitle="课堂学习数据总览与分课程统计"
    >
      <template #actions>
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="按姓名或学号搜索"
          style="width: 300px"
          @search="handleSearch"
          @change="handleSearch"
        />
      </template>
    </PageHeaderBar>

    <a-spin :spinning="loading" tip="加载中...">
      <a-tabs v-model:activeKey="activeTab" class="analytics-tabs">
        <!-- 学情总览 -->
        <a-tab-pane key="overview" tab="学情总览">
          <LearningOverviewTab
            :classroom-id="classroomId"
            :teacher-id="teacherId"
            :keyword="searchKeyword"
          />
        </a-tab-pane>

        <!-- 必修课程统计 -->
        <a-tab-pane key="required" tab="必修课程统计">
          <LearningStatsTab
            :classroom-id="classroomId"
            :teacher-id="teacherId"
            :course-type="'required'"
            :keyword="searchKeyword"
          />
        </a-tab-pane>

        <!-- 拓展课程统计 -->
        <a-tab-pane key="optional" tab="拓展课程统计">
          <LearningStatsTab
            :classroom-id="classroomId"
            :teacher-id="teacherId"
            :course-type="'optional'"
            :keyword="searchKeyword"
          />
        </a-tab-pane>
      </a-tabs>
    </a-spin>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useUserStore } from '@/stores/user';
import LearningOverviewTab from '../../components/classroom/LearningOverviewTab.vue';
import LearningStatsTab from '../../components/classroom/LearningStatsTab.vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

// Props when embedded in classroom detail; fall back to route for standalone
const props = defineProps<{
  classroomId?: string | number;
}>();

// 路由和用户信息
const route = useRoute();
const userStore = useUserStore();

// 调试日志
console.log('🎯 学情分析页面组件已加载');
console.log('路由参数:', route.params);
console.log('用户信息:', userStore.userInfo);

const classroomId = computed(() => {
  if (props.classroomId != null && props.classroomId !== '') {
    return typeof props.classroomId === 'number'
      ? props.classroomId
      : parseInt(String(props.classroomId), 10);
  }
  const id = parseInt(route.params.id as string);
  console.log('计算出的课堂ID:', id);
  return id;
});

const teacherId = computed(() => {
  const id = userStore.userInfo.id;
  console.log('计算出的教师ID:', id);
  return id ? parseInt(id as string) : 0;
});

// 状态管理
const loading = ref(false);
const activeTab = ref('overview');
const searchKeyword = ref('');

// 事件处理
function handleSearch() {
  // 搜索逻辑会在子组件中处理
  console.log('搜索关键词:', searchKeyword.value);
}
</script>

<style lang="less" scoped>
.learning-analytics-page {
  /* PageShell handles outer padding */

  .analytics-tabs {
    background: var(--hx-color-bg-container, #fff);
    padding: var(--hx-space-4);
    border-radius: var(--hx-radius-md, 10px);
    border: 1px solid var(--hx-color-border, #f0f0f0);

    :deep(.ant-tabs-nav) {
      margin-bottom: var(--hx-space-4);
    }

    :deep(.ant-tabs-content-holder) {
      .ant-tabs-content {
        .ant-tabs-tabpane {
          padding: 0;
        }
      }
    }

    /* chart card gap — child overview uses rows/cards */
    :deep(.ant-row) {
      row-gap: var(--hx-space-4);
    }

    :deep(.ant-card) {
      margin-bottom: 0;
    }
  }
}
</style>
