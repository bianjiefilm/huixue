<template>
  <div class="component-list">
    <div class="component-list-header">
      <h3>图表组件</h3>
    </div>
    
    <a-tabs v-model:activeKey="activeCategory">
      <a-tab-pane key="all" tab="全部">
        <div class="component-grid">
          <div 
            v-for="component in components" 
            :key="component.id"
            class="component-item"
            draggable="true"
            @dragstart="handleDragStart(component)"
          >
            <div class="component-icon">
              <component :is="getIconComponent(component.icon)" />
            </div>
            <div class="component-name">{{ component.name }}</div>
          </div>
        </div>
      </a-tab-pane>
      
      <a-tab-pane 
        v-for="category in categories" 
        :key="category.id" 
        :tab="category.name"
      >
        <div class="component-grid">
          <div 
            v-for="component in filteredComponents(category.id)" 
            :key="component.id"
            class="component-item"
            draggable="true"
            @dragstart="handleDragStart(component)"
          >
            <div class="component-icon">
              <component :is="getIconComponent(component.icon)" />
            </div>
            <div class="component-name">{{ component.name }}</div>
          </div>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  BarChartOutlined, 
  LineChartOutlined, 
  PieChartOutlined, 
  DotChartOutlined,
  AreaChartOutlined,
  RadarChartOutlined,
  FundOutlined,
  HeatMapOutlined
} from '@ant-design/icons-vue';
import type { VisualComponent, ComponentCategory } from '../../api/visual';

const props = defineProps<{
  components: VisualComponent[];
  categories: ComponentCategory[];
}>();

const activeCategory = ref<string>('all');

// 根据类别过滤组件
const filteredComponents = (categoryId: string) => {
  return props.components.filter(component => component.category === categoryId);
};

// 获取对应的图标组件
const getIconComponent = (iconName: string) => {
  const iconMap: Record<string, any> = {
    'chart-bar': BarChartOutlined,
    'chart-line': LineChartOutlined,
    'chart-pie': PieChartOutlined,
    'chart-scatter': DotChartOutlined,
    'chart-area': AreaChartOutlined,
    'chart-radar': RadarChartOutlined,
    'chart-funnel': FundOutlined,
    'chart-heatmap': HeatMapOutlined,
    'chart-map': HeatMapOutlined,
    'chart-gauge': DotChartOutlined,
    'chart-tree': FundOutlined
  };
  
  return iconMap[iconName] || BarChartOutlined;
};

// 处理拖动开始事件
const handleDragStart = (component: VisualComponent) => {
  // 将组件信息存储在拖拽数据中
  const dragData = JSON.stringify({
    componentId: component.id,
    componentType: component.type
  });
  
  // 创建一个自定义事件
  const event = new CustomEvent('component-drag-start', {
    detail: {
      component
    },
    bubbles: true
  });
  
  // 触发事件
  document.dispatchEvent(event);
};

defineExpose({
  filteredComponents,
  getIconComponent
});
</script>

<style scoped>
.component-list {
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.component-list-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.component-list-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 16px;
  overflow-y: auto;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
  background-color: #fff;
}

.component-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.component-icon {
  font-size: 24px;
  margin-bottom: 8px;
  color: #1890ff;
}

.component-name {
  font-size: 12px;
  text-align: center;
  color: rgba(0, 0, 0, 0.85);
}

:deep(.ant-tabs-content) {
  height: 100%;
  overflow: auto;
}
</style> 