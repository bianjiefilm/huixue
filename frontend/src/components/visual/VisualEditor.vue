<template>
  <div class="visual-editor">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <a-button-group>
          <a-button>
            <template #icon><ZoomInOutlined /></template>
            放大
          </a-button>
          <a-button>
            <template #icon><ZoomOutOutlined /></template>
            缩小
          </a-button>
          <a-button>
            <template #icon><UndoOutlined /></template>
            撤销
          </a-button>
          <a-button>
            <template #icon><RedoOutlined /></template>
            重做
          </a-button>
        </a-button-group>
      </div>
      <div class="toolbar-right">
        <a-select
          v-model:value="currentTheme"
          style="width: 120px;"
          placeholder="选择主题"
        >
          <a-select-option value="default">默认主题</a-select-option>
          <a-select-option value="dark">暗色主题</a-select-option>
          <a-select-option value="vintage">复古主题</a-select-option>
        </a-select>
        <a-button type="primary" @click="handleSave">
          <template #icon><SaveOutlined /></template>
          保存
        </a-button>
        <a-button @click="handlePreview">
          <template #icon><EyeOutlined /></template>
          预览
        </a-button>
      </div>
    </div>
    
    <div class="editor-main">
      <div class="editor-sidebar">
        <div class="component-list">
          <h3>图表组件</h3>
          <a-collapse v-model:activeKey="activeCategories" accordion>
            <a-collapse-panel key="basic" header="基础图表">
              <div class="component-grid">
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'line')">
                  <img src="https://img.alicdn.com/imgextra/i3/O1CN01YDAjuZ1NZ8pPfJ58j_!!6000000001582-2-tps-200-200.png" alt="折线图" />
                  <span>折线图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'bar')">
                  <img src="https://img.alicdn.com/imgextra/i2/O1CN018Oo3bP1ZnKjHiJdGq_!!6000000003244-2-tps-200-200.png" alt="柱状图" />
                  <span>柱状图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'pie')">
                  <img src="https://img.alicdn.com/imgextra/i1/O1CN01TgkCwL1XOUVTZkFWS_!!6000000002913-2-tps-200-200.png" alt="饼图" />
                  <span>饼图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'scatter')">
                  <img src="https://img.alicdn.com/imgextra/i4/O1CN01SOEzSg1NTkEfTUg7H_!!6000000001575-2-tps-200-200.png" alt="散点图" />
                  <span>散点图</span>
                </div>
              </div>
            </a-collapse-panel>
            <a-collapse-panel key="advanced" header="高级图表">
              <div class="component-grid">
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'radar')">
                  <img src="https://img.alicdn.com/imgextra/i2/O1CN01nUIXEk1nJhjGZhSXf_!!6000000005062-2-tps-200-200.png" alt="雷达图" />
                  <span>雷达图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'heatmap')">
                  <img src="https://img.alicdn.com/imgextra/i2/O1CN01T0V8v11xpEw1FZYkN_!!6000000006495-2-tps-200-200.png" alt="热力图" />
                  <span>热力图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'tree')">
                  <img src="https://img.alicdn.com/imgextra/i4/O1CN01sNcksG1lsXfU2Tyet_!!6000000004875-2-tps-200-200.png" alt="树图" />
                  <span>树图</span>
                </div>
                <div class="component-item" draggable="true" @dragstart="dragStart($event, 'graph')">
                  <img src="https://img.alicdn.com/imgextra/i3/O1CN01PXs5X91qw1Ku7WMQU_!!6000000005556-2-tps-200-200.png" alt="关系图" />
                  <span>关系图</span>
                </div>
              </div>
            </a-collapse-panel>
          </a-collapse>
        </div>
      </div>
      
      <div 
        class="canvas-container" 
        @dragover="allowDrop"
        @drop="handleDrop"
        @click="deselectAll"
      >
        <div class="canvas" ref="canvasRef">
          <div 
            v-for="component in components" 
            :key="component.id"
            :class="['chart-component', {'selected': component.id === selectedComponentId}]"
            :style="{
              left: component.position.x + 'px',
              top: component.position.y + 'px',
              width: component.size.width + 'px',
              height: component.size.height + 'px',
              zIndex: component.zIndex
            }"
            @click.stop="selectComponent(component.id)"
            @mousedown="startDrag($event, component.id)"
          >
            <EChart 
              v-if="component.chartConfig"
              :options="component.chartConfig" 
              :theme="currentTheme"
              :height="component.size.height + 'px'" 
            />
            <div class="component-title">{{ component.title }}</div>
            <div v-if="component.id === selectedComponentId" class="resize-handle" @mousedown.stop="startResize($event, component.id)"></div>
          </div>
        </div>
      </div>
      
      <div class="editor-panel">
        <h3>属性设置</h3>
        <div v-if="selectedComponent" class="property-form">
          <a-form layout="vertical">
            <a-form-item label="标题">
              <a-input v-model:value="selectedComponent.title" @change="updateComponent" />
            </a-form-item>
            
            <a-form-item label="数据源">
              <a-select 
                v-model:value="selectedComponent.dataSource"
                style="width: 100%"
                @change="updateComponent"
              >
                <a-select-option value="data1">示例数据1</a-select-option>
                <a-select-option value="data2">示例数据2</a-select-option>
                <a-select-option value="data3">示例数据3</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-divider />
            
            <a-form-item label="图表尺寸">
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-input-number 
                    v-model:value="selectedComponent.size.width" 
                    style="width: 100%" 
                    addon-before="宽"
                    @change="updateComponent"
                  />
                </a-col>
                <a-col :span="12">
                  <a-input-number 
                    v-model:value="selectedComponent.size.height" 
                    style="width: 100%" 
                    addon-before="高"
                    @change="updateComponent"
                  />
                </a-col>
              </a-row>
            </a-form-item>
            
            <a-form-item>
              <a-button danger @click="deleteComponent">删除组件</a-button>
            </a-form-item>
          </a-form>
        </div>
        <a-empty v-else description="请选择组件编辑" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { message } from 'ant-design-vue';
import { 
  ZoomInOutlined, 
  ZoomOutOutlined, 
  UndoOutlined, 
  RedoOutlined,
  SaveOutlined,
  EyeOutlined
} from '@ant-design/icons-vue';
import EChart from './EChart.vue';

// 组件类别
const activeCategories = ref<string[]>(['basic']);

// 当前主题
const currentTheme = ref('default');

// 画布上的组件列表
const components = ref<any[]>([]);

// 选中的组件ID
const selectedComponentId = ref<string | null>(null);

// 通过ID获取选中的组件
const selectedComponent = computed(() => {
  if (!selectedComponentId.value) return null;
  return components.value.find(item => item.id === selectedComponentId.value);
});

// 画布引用
const canvasRef = ref<HTMLElement | null>(null);

// 拖拽状态
const dragState = reactive({
  isDragging: false,
  startX: 0,
  startY: 0,
  origX: 0,
  origY: 0,
  componentId: ''
});

// 调整大小状态
const resizeState = reactive({
  isResizing: false,
  startX: 0,
  startY: 0,
  origWidth: 0,
  origHeight: 0,
  componentId: ''
});

// 生成唯一ID
const generateId = () => {
  return 'chart-' + Date.now() + '-' + Math.floor(Math.random() * 1000);
};

// 开始拖拽组件
const dragStart = (event: DragEvent, type: string) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('type', type);
  }
};

// 允许放置
const allowDrop = (event: DragEvent) => {
  event.preventDefault();
};

// 处理放置
const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  if (!event.dataTransfer) return;
  
  const type = event.dataTransfer.getData('type');
  const canvas = canvasRef.value;
  
  if (canvas) {
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    
    // 创建新组件
    const newComponent = {
      id: generateId(),
      type: type,
      title: getChartTitle(type),
      position: { x, y },
      size: { width: 400, height: 300 },
      zIndex: components.value.length + 1,
      dataSource: 'data1',
      chartConfig: getDefaultConfig(type)
    };
    
    // 添加到组件列表
    components.value.push(newComponent);
    
    // 选中新组件
    selectedComponentId.value = newComponent.id;
    
    message.success(`添加了${getChartTitle(type)}`);
  }
};

// 获取图表标题
const getChartTitle = (type: string) => {
  const titles: Record<string, string> = {
    'line': '折线图',
    'bar': '柱状图',
    'pie': '饼图',
    'scatter': '散点图',
    'radar': '雷达图',
    'heatmap': '热力图',
    'tree': '树图',
    'graph': '关系图'
  };
  return titles[type] || '图表组件';
};

// 获取默认配置
const getDefaultConfig = (type: string) => {
  switch (type) {
    case 'line':
      return {
        title: {
          text: '折线图示例'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: [150, 230, 224, 218, 135, 147, 260],
          type: 'line'
        }]
      };
    case 'bar':
      return {
        title: {
          text: '柱状图示例'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          data: [120, 200, 150, 80, 70, 110, 130],
          type: 'bar'
        }]
      };
    case 'pie':
      return {
        title: {
          text: '饼图示例'
        },
        tooltip: {
          trigger: 'item'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [{
          type: 'pie',
          radius: '50%',
          data: [
            { value: 1048, name: '数据1' },
            { value: 735, name: '数据2' },
            { value: 580, name: '数据3' },
            { value: 484, name: '数据4' },
            { value: 300, name: '数据5' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      };
    default:
      return {
        title: {
          text: '图表示例'
        },
        tooltip: {},
        xAxis: {
          data: ['类别1', '类别2', '类别3', '类别4', '类别5']
        },
        yAxis: {},
        series: [{
          type: type,
          data: [5, 20, 36, 10, 10]
        }]
      };
  }
};

// 选择组件
const selectComponent = (id: string) => {
  selectedComponentId.value = id;
};

// 取消选择所有组件
const deselectAll = () => {
  selectedComponentId.value = null;
};

// 开始拖动组件
const startDrag = (event: MouseEvent, id: string) => {
  const component = components.value.find(item => item.id === id);
  if (!component) return;
  
  dragState.isDragging = true;
  dragState.componentId = id;
  dragState.startX = event.clientX;
  dragState.startY = event.clientY;
  dragState.origX = component.position.x;
  dragState.origY = component.position.y;
  
  document.addEventListener('mousemove', onDragMove);
  document.addEventListener('mouseup', onDragEnd);
};

// 拖动移动
const onDragMove = (event: MouseEvent) => {
  if (!dragState.isDragging) return;
  
  const deltaX = event.clientX - dragState.startX;
  const deltaY = event.clientY - dragState.startY;
  
  const index = components.value.findIndex(item => item.id === dragState.componentId);
  if (index !== -1) {
    components.value[index].position.x = dragState.origX + deltaX;
    components.value[index].position.y = dragState.origY + deltaY;
  }
};

// 拖动结束
const onDragEnd = () => {
  dragState.isDragging = false;
  document.removeEventListener('mousemove', onDragMove);
  document.removeEventListener('mouseup', onDragEnd);
  
  // 更新组件状态
  updateComponent();
};

// 开始调整大小
const startResize = (event: MouseEvent, id: string) => {
  event.stopPropagation();
  
  const component = components.value.find(item => item.id === id);
  if (!component) return;
  
  resizeState.isResizing = true;
  resizeState.componentId = id;
  resizeState.startX = event.clientX;
  resizeState.startY = event.clientY;
  resizeState.origWidth = component.size.width;
  resizeState.origHeight = component.size.height;
  
  document.addEventListener('mousemove', onResizeMove);
  document.addEventListener('mouseup', onResizeEnd);
};

// 调整大小移动
const onResizeMove = (event: MouseEvent) => {
  if (!resizeState.isResizing) return;
  
  const deltaX = event.clientX - resizeState.startX;
  const deltaY = event.clientY - resizeState.startY;
  
  const index = components.value.findIndex(item => item.id === resizeState.componentId);
  if (index !== -1) {
    // 最小尺寸限制
    const newWidth = Math.max(200, resizeState.origWidth + deltaX);
    const newHeight = Math.max(150, resizeState.origHeight + deltaY);
    
    components.value[index].size.width = newWidth;
    components.value[index].size.height = newHeight;
  }
};

// 调整大小结束
const onResizeEnd = () => {
  resizeState.isResizing = false;
  document.removeEventListener('mousemove', onResizeMove);
  document.removeEventListener('mouseup', onResizeEnd);
  
  // 更新组件状态
  updateComponent();
};

// 更新组件
const updateComponent = () => {
  // 此处可以添加保存逻辑
  console.log('组件已更新', components.value);
};

// 删除组件
const deleteComponent = () => {
  if (!selectedComponentId.value) return;
  
  const index = components.value.findIndex(item => item.id === selectedComponentId.value);
  if (index !== -1) {
    components.value.splice(index, 1);
    selectedComponentId.value = null;
    message.success('组件已删除');
  }
};

// 保存
const handleSave = () => {
  if (components.value.length === 0) {
    message.warning('请先添加图表组件');
    return;
  }
  
  message.success('保存成功');
};

// 预览
const handlePreview = () => {
  if (components.value.length === 0) {
    message.warning('请先添加图表组件');
    return;
  }
  
  message.info('正在预览...');
};
</script>

<style scoped>
.visual-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #f5f5f5;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  padding: 8px 16px;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-main {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.editor-sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #e8e8e8;
  padding: 16px;
  overflow-y: auto;
}

.component-list h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 8px;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
}

.component-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

.component-item img {
  width: 40px;
  height: 40px;
  margin-bottom: 4px;
}

.component-item span {
  font-size: 12px;
}

.canvas-container {
  flex: 1;
  position: relative;
  overflow: auto;
  background-color: #f0f2f5;
}

.canvas {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 800px;
}

.chart-component {
  position: absolute;
  background-color: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.chart-component.selected {
  border: 2px solid #1890ff;
}

.component-title {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  padding: 4px 8px;
  background-color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: bold;
  border-bottom: 1px solid #f0f0f0;
  z-index: 1;
}

.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 10px;
  height: 10px;
  background-color: #1890ff;
  cursor: nwse-resize;
}

.editor-panel {
  width: 280px;
  background-color: #fff;
  border-left: 1px solid #e8e8e8;
  padding: 16px;
  overflow-y: auto;
}

.editor-panel h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.property-form {
  margin-top: 16px;
}
</style> 