<template>
  <div class="preview-container">
    <div class="preview-content">
      <a-spin :spinning="loading" tip="加载中...">
        <div v-if="previewComponents.length > 0" class="dashboard-container">
          <div
            v-for="component in previewComponents"
            :key="component.id"
            class="chart-component"
            :style="{
              left: component.position.x + 'px',
              top: component.position.y + 'px',
              width: component.size.width + 'px',
              height: component.size.height + 'px',
              zIndex: component.zIndex,
              visibility: component.visible ? 'visible' : 'hidden'
            }"
          >
            <div class="component-title">{{ component.title }}</div>
            <BiChartRenderer
              v-if="isChartType(component.type)"
              :type="component.type"
              :data="component.chartData || []"
              :title="component.title"
              :x-field="component.config?.xField"
              :y-field="component.config?.yField"
              :color="component.props?.color || '#1890ff'"
              :height="component.size.height - 44"
              :width="component.size.width"
            />
            <div v-else class="component-preview-body">
              {{ component.name || component.type || '图表组件' }}
            </div>
          </div>
        </div>
        <a-empty v-else description="暂无可视化内容，请先在编辑器中创建图表" style="padding: 100px 0;" />
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import BiChartRenderer from '@/components/BiChartRenderer.vue';
import { useUserStore } from '../../stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const loading = ref(true);

// 预览组件数据（从BI设计器加载，初始为空）
const previewComponents = ref<any[]>([]);

const chartTypes = [
  'bar-chart', 'line-chart', 'area-chart', 'pie-chart', 'scatter',
  'radar-chart', 'funnel', 'gauge', 'heatmap', 'table',
  'boxplot', 'kline', 'china-map', 'world-map', 'province-map',
  'scatter-map', 'flow-map', 'heat-map-geo'
];

const isChartType = (type: string) => chartTypes.includes(type);

// 检查登录状态
const checkLoginStatus = () => {
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再查看预览');
    router.push('/login?redirect=' + encodeURIComponent(router.currentRoute.value.fullPath));
    return false;
  }
  return true;
};

// 初始化
onMounted(() => {
  // 检查用户登录状态
  if (!checkLoginStatus()) return;

  const previewId = route.params.id as string;
  const storedPreview = localStorage.getItem(`bi_preview_${previewId}`);
  if (storedPreview) {
    try {
      const parsed = JSON.parse(storedPreview);
      previewComponents.value = parsed.nodes || [];
    } catch (error) {
      console.error('解析预览数据失败:', error);
      message.warning('预览数据解析失败');
    }
  }
  loading.value = false;
});
</script>

<style scoped>
.preview-container {
  width: 100%;
  height: 100vh;
  background-color: #0f172a;
  overflow: hidden;
}

.preview-content {
  width: 100%;
  height: 100%;
  padding: 0;
  overflow: auto;
}

.dashboard-container {
  position: relative;
  width: 100%;
  min-height: 100vh;
  background: #fff;
}

.chart-component {
  position: absolute;
  background-color: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.component-title {
  height: 40px;
  line-height: 40px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 500;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.component-preview-body {
  height: calc(100% - 40px);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #1677ff;
  background: linear-gradient(135deg, #f6fbff 0%, #eef6ff 100%);
}
</style>
