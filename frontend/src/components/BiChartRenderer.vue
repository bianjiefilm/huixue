<template>
  <div ref="chartRef" class="bi-chart-container" :style="containerStyle"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue';
import * as echarts from 'echarts';

interface Props {
  type: string;
  data?: any[];
  width?: number;
  height?: number;
  title?: string;
  xField?: string;
  yField?: string;
  color?: string;
}

const props = withDefaults(defineProps<Props>(), {
  width: 300,
  height: 200,
  data: () => [],
  color: '#1890ff'
});

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

const containerStyle = computed(() => ({
  width: `${props.width}px`,
  height: `${props.height}px`
}));

// 默认示例数据
const getDefaultData = () => {
  const categories = ['1月', '2月', '3月', '4月', '5月', '6月'];
  const values = [Math.floor(Math.random() * 5000) + 1000, Math.floor(Math.random() * 5000) + 1000,
                  Math.floor(Math.random() * 5000) + 1000, Math.floor(Math.random() * 5000) + 1000,
                  Math.floor(Math.random() * 5000) + 1000, Math.floor(Math.random() * 5000) + 1000];
  return { categories, values };
};

// 生成图表配置
const getChartOption = (): echarts.EChartsOption => {
  const { categories, values } = props.data.length > 0 ?
    {
      categories: props.data.map(d => d[props.xField || 'category']),
      values: props.data.map(d => d[props.yField || 'value'])
    } : getDefaultData();

  const baseOption: echarts.EChartsOption = {
    title: props.title ? {
      text: props.title,
      left: 'center',
      top: 5,
      textStyle: { fontSize: 12, color: '#fff' }
    } : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      left: '10%',
      right: '10%',
      top: props.title ? '25%' : '15%',
      bottom: '15%'
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#aaa' } },
      axisLabel: { color: '#aaa', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisLabel: { color: '#aaa', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    }
  };

  const colorList = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];

  switch (props.type) {
    case 'bar-chart':
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'bar',
          data: values,
          itemStyle: { borderRadius: [4, 4, 0, 0] }
        }]
      };
    case 'line-chart':
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'line',
          data: values,
          smooth: true,
          areaStyle: { opacity: 0.3 }
        }]
      };
    case 'area-chart':
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'line',
          data: values,
          smooth: true,
          areaStyle: { opacity: 0.5 }
        }]
      };
    case 'pie-chart':
      return {
        ...baseOption,
        color: colorList,
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '55%'],
          data: categories.map((cat, idx) => ({
            name: cat,
            value: values[idx] || Math.floor(Math.random() * 1000) + 100
          })),
          label: { color: '#fff', fontSize: 10 }
        }]
      };
    case 'scatter':
      const scatterData = Array.from({ length: 50 }, () => [
        Math.random() * 100, Math.random() * 100
      ]);
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'scatter',
          symbolSize: 8,
          data: scatterData
        }]
      };
    case 'radar-chart':
      return {
        ...baseOption,
        color: [props.color],
        radar: {
          indicator: categories.map(cat => ({ name: cat, max: 100 })),
          center: ['50%', '55%'],
          radius: '60%'
        },
        series: [{
          type: 'radar',
          data: [{ name: '数据', value: values.map(v => (v as number) % 100 || 50) }]
        }]
      };
    case 'funnel':
      return {
        ...baseOption,
        color: colorList,
        series: [{
          type: 'funnel',
          left: '10%',
          top: 20,
          bottom: 20,
          width: '80%',
          min: 0,
          max: 100,
          minSize: '0%',
          maxSize: '100%',
          sort: 'descending',
          gap: 2,
          label: { show: true, position: 'inside' },
          data: categories.map((cat, idx) => ({
            name: cat,
            value: Math.floor(100 - idx * 15)
          }))
        }]
      };
    case 'gauge':
      return {
        series: [{
          type: 'gauge',
          center: ['50%', '60%'],
          radius: '80%',
          startAngle: 180,
          endAngle: 0,
          min: 0,
          max: 100,
          splitNumber: 5,
          progress: { show: true, width: 10 },
          axisLine: { lineStyle: { width: 10 } },
          axisTick: { show: false },
          splitLine: { length: 10, lineStyle: { width: 2, color: '#999' } },
          axisLabel: { distance: 15, color: '#999', fontSize: 10 },
          pointer: { show: false },
          anchor: { show: false },
          title: { show: false },
          detail: {
            valueAnimation: true,
            fontSize: 20,
            color: '#fff',
            offsetCenter: [0, '30%'],
            formatter: '{value}%'
          },
          data: [{ value: Math.floor(Math.random() * 60) + 20 }]
        }]
      };
    case 'heatmap':
      const heatmapData = [];
      for (let i = 0; i < 24; i++) {
        for (let j = 0; j < 7; j++) {
          heatmapData.push([i, j, Math.floor(Math.random() * 100)]);
        }
      }
      return {
        ...baseOption,
        color: ['#1890ff'],
        series: [{
          type: 'heatmap',
          data: heatmapData,
          label: { show: false }
        }],
        xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, i) => `${i}:00`) },
        yAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] }
      };
    case 'table':
      return {
        tooltip: { trigger: 'item' },
        color: [props.color],
        series: [{
          type: 'table',
          data: categories.map((cat, idx) => ({
            name: cat,
            value: values[idx] || Math.floor(Math.random() * 1000) + 100
          })),
          header: ['类别', '数值'],
          bodyWidth: 60,
          bodyHeight: 80
        }]
      };
    case 'boxplot':
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'boxplot',
          data: [
            [850, 740, 900, 1070],
            [740, 780, 850, 950],
            [750, 800, 850, 1000],
            [800, 850, 900, 1050],
            [780, 820, 880, 1020]
          ]
        }]
      };
    case 'kline':
      const klineData = Array.from({ length: 30 }, (_, i) => ({
        open: 100 + Math.random() * 50,
        close: 100 + Math.random() * 50,
        low: 90 + Math.random() * 30,
        high: 140 + Math.random() * 30
      }));
      return {
        ...baseOption,
        color: props.color,
        series: [{
          type: 'candlestick',
          data: klineData.map(d => [d.open, d.close, d.low, d.high])
        }]
      };
    case 'china-map':
    case 'world-map':
    case 'province-map':
      return {
        ...baseOption,
        series: [{
          type: 'map',
          map: props.type === 'china-map' ? 'china' : 'world',
          roam: true,
          data: [
            { name: '北京', value: Math.random() * 100 },
            { name: '上海', value: Math.random() * 100 },
            { name: '广东', value: Math.random() * 100 },
            { name: '浙江', value: Math.random() * 100 }
          ],
          itemStyle: {
            areaColor: '#1890ff',
            borderColor: '#fff'
          }
        }]
      };
    default:
      return {
        ...baseOption,
        color: [props.color],
        series: [{
          type: 'bar',
          data: values
        }]
      };
  }
};

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return;

  chartInstance = echarts.init(chartRef.value);
  chartInstance.setOption(getChartOption());
};

// 更新图表
const updateChart = () => {
  if (chartInstance) {
    chartInstance.setOption(getChartOption());
  }
};

// 响应式更新
watch(() => [props.width, props.height, props.data, props.type], () => {
  updateChart();
}, { deep: true });

// 窗口大小变化
const handleResize = () => {
  chartInstance?.resize();
};

onMounted(() => {
  initChart();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
});

// 暴露方法给父组件
defineExpose({
  updateChart,
  getChartDataUrl: () => chartInstance?.getDataURL({ type: 'png', pixelRatio: 2 })
});
</script>

<style scoped>
.bi-chart-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}
</style>
