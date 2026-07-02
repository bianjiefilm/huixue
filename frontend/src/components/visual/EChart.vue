<template>
  <div ref="chartRef" class="echarts-container" :style="{ height: height, width: width }"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  options: {
    type: Object,
    required: true
  },
  theme: {
    type: String,
    default: 'default'
  },
  width: {
    type: String,
    default: '100%'
  },
  height: {
    type: String,
    default: '100%'
  },
  resize: {
    type: Boolean,
    default: true
  }
});

const chartRef = ref<HTMLElement | null>(null);
const chart = ref<echarts.ECharts | null>(null);

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return;
  
  // 如果已经存在图表实例，则销毁
  if (chart.value) {
    chart.value.dispose();
  }
  
  // 创建新的图表实例
  chart.value = echarts.init(chartRef.value, props.theme);
  
  // 设置图表配置
  chart.value.setOption(props.options);
};

// 监听窗口大小变化
const handleResize = () => {
  if (chart.value && props.resize) {
    chart.value.resize();
  }
};

// 监听options变化，更新图表
watch(() => props.options, (newOptions) => {
  if (chart.value) {
    chart.value.setOption(newOptions, { notMerge: true });
  }
}, { deep: true });

// 监听theme变化，重新初始化图表
watch(() => props.theme, () => {
  initChart();
});

// 组件挂载时初始化图表
onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

// 组件卸载前销毁图表实例
onBeforeUnmount(() => {
  if (chart.value) {
    chart.value.dispose();
    chart.value = null;
  }
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
.echarts-container {
  min-height: 200px;
}
</style> 