<template>
  <div class="dag-board">
    <div class="dag-canvas" @click="handleCanvasClick">
      <!-- 节点 -->
      <div 
        v-for="node in DataAll.nodes" 
        :key="node.id" 
        class="dag-node"
        :class="{ 'node-selected': selectedNode && selectedNode.id === node.id }"
        :style="{ left: node.left + 'px', top: node.top + 'px' }"
        @click.stop="selectNode(node)"
        @mousedown.stop="startDragNode($event, node)"
      >
        <div class="node-icon">
          <component :is="getIconByType(node.name)" />
        </div>
        <div class="node-title">{{ node.label || getNodeTitle(node.name) }}</div>
        <div class="node-status" :class="node.state">
          <div class="status-dot"></div>
        </div>
        <div class="node-anchors">
          <div class="anchor anchor-left" @mousedown.stop="startDrawEdge($event, node, 'left')"></div>
          <div class="anchor anchor-right" @mousedown.stop="startDrawEdge($event, node, 'right')"></div>
          <div class="anchor anchor-top" @mousedown.stop="startDrawEdge($event, node, 'top')"></div>
          <div class="anchor anchor-bottom" @mousedown.stop="startDrawEdge($event, node, 'bottom')"></div>
        </div>
        <div class="node-remove" @click.stop="removeNode(node)">
          <close-outlined />
        </div>
      </div>
      
      <!-- 连接线 -->
      <svg class="dag-edges" :width="canvasWidth" :height="canvasHeight">
        <g>
          <path 
            v-for="edge in DataAll.edges" 
            :key="edge.id" 
            :d="getEdgePath(edge)" 
            :class="['edge-path', { 'edge-selected': selectedEdge && selectedEdge.id === edge.id }]"
            @click.stop="selectEdge(edge)"
          ></path>
          <path 
            v-if="drawingEdge" 
            :d="getTempEdgePath()" 
            class="edge-path edge-drawing"
          ></path>
        </g>
      </svg>
      
      <!-- 临时连接线 -->
      <div v-if="drawingEdge" class="temp-edge-target" :style="{ left: mousePos.x + 'px', top: mousePos.y + 'px' }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { v4 as uuidv4 } from 'uuid';
import { 
  DatabaseOutlined,
  FilterOutlined,
  ScissorOutlined,
  HighlightOutlined,
  BuildOutlined,
  NodeIndexOutlined,
  LineChartOutlined,
  FunctionOutlined,
  ApartmentOutlined,
  ClusterOutlined,
  RadarChartOutlined,
  DeploymentUnitOutlined,
  FundProjectionScreenOutlined,
  PartitionOutlined,
  BarChartOutlined,
  ExportOutlined,
  CloseOutlined
} from '@ant-design/icons-vue';

interface Props {
  DataAll: {
    nodes: any[];
    edges: any[];
    GlobalConfig?: Record<string, any>;
  };
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'updateDAG', data: any, action: string): void;
  (e: 'editNodeDetails', node: any): void;
}>();

// 画布大小
const canvasWidth = ref(2000);
const canvasHeight = ref(1500);

// 选中的节点和边
const selectedNode = ref<any>(null);
const selectedEdge = ref<any>(null);

// 节点拖拽状态
const isDraggingNode = ref(false);
const draggedNode = ref<any>(null);
const dragOffset = reactive({ x: 0, y: 0 });

// 边绘制状态
const drawingEdge = ref(false);
const sourceNode = ref<any>(null);
const sourceAnchor = ref<string>('');
const mousePos = reactive({ x: 0, y: 0 });

// 获取节点图标
const getIconByType = (type: string) => {
  const iconMap: Record<string, any> = {
    'dataSource': DatabaseOutlined,
    'dataPreprocessing': FilterOutlined,
    'dataSplit': ScissorOutlined,
    'featureSelection': HighlightOutlined,
    'featureExtraction': BuildOutlined,
    'dimensionReduction': NodeIndexOutlined,
    'linearRegression': LineChartOutlined,
    'logisticRegression': FunctionOutlined,
    'decisionTree': ApartmentOutlined,
    'randomForest': ClusterOutlined,
    'svm': RadarChartOutlined,
    'dnn': DeploymentUnitOutlined,
    'cnn': FundProjectionScreenOutlined,
    'rnn': PartitionOutlined,
    'evaluation': BarChartOutlined,
    'modelExport': ExportOutlined
  };
  return iconMap[type] || DatabaseOutlined;
};

// 获取节点标题
const getNodeTitle = (type: string) => {
  const titles: Record<string, string> = {
    'dataSource': '数据源',
    'dataPreprocessing': '数据预处理',
    'dataSplit': '数据切分',
    'featureSelection': '特征选择',
    'featureExtraction': '特征提取',
    'dimensionReduction': '降维',
    'linearRegression': '线性回归',
    'logisticRegression': '逻辑回归',
    'decisionTree': '决策树',
    'randomForest': '随机森林',
    'svm': '支持向量机',
    'dnn': 'DNN',
    'cnn': 'CNN',
    'rnn': 'RNN',
    'evaluation': '评估指标',
    'modelExport': '模型导出'
  };
  return titles[type] || '未知节点';
};

// 点击画布
const handleCanvasClick = () => {
  selectedNode.value = null;
  selectedEdge.value = null;
  drawingEdge.value = false;
};

// 选择节点
const selectNode = (node: any) => {
  selectedNode.value = node;
  selectedEdge.value = null;
  
  // 通知父组件编辑节点详情
  emit('editNodeDetails', node);
};

// 开始拖拽节点
const startDragNode = (event: MouseEvent, node: any) => {
  isDraggingNode.value = true;
  draggedNode.value = node;
  
  // 计算鼠标位置与节点位置的偏移
  dragOffset.x = event.clientX - node.left;
  dragOffset.y = event.clientY - node.top;
  
  document.addEventListener('mousemove', dragNode);
  document.addEventListener('mouseup', stopDragNode);
};

// 拖拽节点
const dragNode = (event: MouseEvent) => {
  if (!isDraggingNode.value || !draggedNode.value) return;
  
  // 更新节点位置
  draggedNode.value.left = Math.max(0, event.clientX - dragOffset.x);
  draggedNode.value.top = Math.max(0, event.clientY - dragOffset.y);
};

// 停止拖拽节点
const stopDragNode = () => {
  isDraggingNode.value = false;
  draggedNode.value = null;
  
  document.removeEventListener('mousemove', dragNode);
  document.removeEventListener('mouseup', stopDragNode);
  
  // 通知父组件更新DAG
  emit('updateDAG', {}, 'update-node-position');
};

// 开始绘制边
const startDrawEdge = (event: MouseEvent, node: any, anchorPos: string) => {
  drawingEdge.value = true;
  sourceNode.value = node;
  sourceAnchor.value = anchorPos;
  
  // 初始鼠标位置
  mousePos.x = event.clientX;
  mousePos.y = event.clientY;
  
  document.addEventListener('mousemove', dragEdge);
  document.addEventListener('mouseup', stopDrawEdge);
};

// 拖拽边
const dragEdge = (event: MouseEvent) => {
  if (!drawingEdge.value) return;
  
  // 更新鼠标位置
  mousePos.x = event.clientX;
  mousePos.y = event.clientY;
};

// 停止绘制边
const stopDrawEdge = (event: MouseEvent) => {
  if (!drawingEdge.value) return;
  
  // 检查目标节点
  const targetNode = findNodeAtPosition(event.clientX, event.clientY);
  
  if (targetNode && targetNode.id !== sourceNode.value.id) {
    // 创建新的边
    const newEdge = {
      id: uuidv4(),
      startId: sourceNode.value.id,
      endId: targetNode.id,
      source: sourceNode.value.id,
      target: targetNode.id,
      sourceAnchor: getAnchorIndex(sourceAnchor.value),
      targetAnchor: getOppositeAnchorIndex(sourceAnchor.value),
      type: 'link',
      label: ''
    };
    
    // 添加到边列表
    props.DataAll.edges.push(newEdge);
    
    // 通知父组件更新DAG
    emit('updateDAG', newEdge, 'add-edge');
  }
  
  // 清除状态
  drawingEdge.value = false;
  sourceNode.value = null;
  sourceAnchor.value = '';
  
  document.removeEventListener('mousemove', dragEdge);
  document.removeEventListener('mouseup', stopDrawEdge);
};

// 查找位置上的节点
const findNodeAtPosition = (x: number, y: number) => {
  return props.DataAll.nodes.find(node => {
    const nodeWidth = 120;
    const nodeHeight = 60;
    
    return (
      x >= node.left && 
      x <= node.left + nodeWidth && 
      y >= node.top && 
      y <= node.top + nodeHeight
    );
  });
};

// 获取锚点索引
const getAnchorIndex = (anchor: string) => {
  switch (anchor) {
    case 'left': return 3;
    case 'right': return 1;
    case 'top': return 0;
    case 'bottom': return 2;
    default: return 1;
  }
};

// 获取相对的锚点索引
const getOppositeAnchorIndex = (anchor: string) => {
  switch (anchor) {
    case 'left': return 1;
    case 'right': return 3;
    case 'top': return 2;
    case 'bottom': return 0;
    default: return 3;
  }
};

// 选择边
const selectEdge = (edge: any) => {
  selectedEdge.value = edge;
  selectedNode.value = null;
};

// 删除节点
const removeNode = (node: any) => {
  // 找到需要删除的节点索引
  const index = props.DataAll.nodes.findIndex(n => n.id === node.id);
  if (index === -1) return;
  
  // 删除节点
  props.DataAll.nodes.splice(index, 1);
  
  // 删除与该节点相关的边
  const edgesToRemove = props.DataAll.edges.filter(
    edge => edge.startId === node.id || edge.endId === node.id
  );
  
  for (const edge of edgesToRemove) {
    const edgeIndex = props.DataAll.edges.findIndex(e => e.id === edge.id);
    if (edgeIndex !== -1) {
      props.DataAll.edges.splice(edgeIndex, 1);
    }
  }
  
  // 如果删除的是当前选中的节点，取消选中
  if (selectedNode.value && selectedNode.value.id === node.id) {
    selectedNode.value = null;
  }
  
  // 通知父组件更新DAG
  emit('updateDAG', { nodeId: node.id }, 'delete-node');
};

// 计算边的路径
const getEdgePath = (edge: any) => {
  const startNode = props.DataAll.nodes.find(node => node.id === edge.startId);
  const endNode = props.DataAll.nodes.find(node => node.id === edge.endId);
  
  if (!startNode || !endNode) return '';
  
  const nodeWidth = 120;
  const nodeHeight = 60;
  
  let startX, startY, endX, endY;
  
  // 根据锚点位置确定起点
  switch (edge.sourceAnchor) {
    case 0: // top
      startX = startNode.left + nodeWidth / 2;
      startY = startNode.top;
      break;
    case 1: // right
      startX = startNode.left + nodeWidth;
      startY = startNode.top + nodeHeight / 2;
      break;
    case 2: // bottom
      startX = startNode.left + nodeWidth / 2;
      startY = startNode.top + nodeHeight;
      break;
    case 3: // left
      startX = startNode.left;
      startY = startNode.top + nodeHeight / 2;
      break;
    default:
      startX = startNode.left + nodeWidth;
      startY = startNode.top + nodeHeight / 2;
  }
  
  // 根据锚点位置确定终点
  switch (edge.targetAnchor) {
    case 0: // top
      endX = endNode.left + nodeWidth / 2;
      endY = endNode.top;
      break;
    case 1: // right
      endX = endNode.left + nodeWidth;
      endY = endNode.top + nodeHeight / 2;
      break;
    case 2: // bottom
      endX = endNode.left + nodeWidth / 2;
      endY = endNode.top + nodeHeight;
      break;
    case 3: // left
      endX = endNode.left;
      endY = endNode.top + nodeHeight / 2;
      break;
    default:
      endX = endNode.left;
      endY = endNode.top + nodeHeight / 2;
  }
  
  // 计算控制点
  const controlPointX1 = startX + (endX - startX) / 3;
  const controlPointY1 = startY;
  const controlPointX2 = startX + (endX - startX) * 2 / 3;
  const controlPointY2 = endY;
  
  // 返回贝塞尔曲线路径
  return `M ${startX} ${startY} C ${controlPointX1} ${controlPointY1}, ${controlPointX2} ${controlPointY2}, ${endX} ${endY}`;
};

// 计算临时边的路径
const getTempEdgePath = () => {
  if (!sourceNode.value || !drawingEdge.value) return '';
  
  const nodeWidth = 120;
  const nodeHeight = 60;
  
  let startX, startY;
  
  // 根据锚点位置确定起点
  switch (sourceAnchor.value) {
    case 'top':
      startX = sourceNode.value.left + nodeWidth / 2;
      startY = sourceNode.value.top;
      break;
    case 'right':
      startX = sourceNode.value.left + nodeWidth;
      startY = sourceNode.value.top + nodeHeight / 2;
      break;
    case 'bottom':
      startX = sourceNode.value.left + nodeWidth / 2;
      startY = sourceNode.value.top + nodeHeight;
      break;
    case 'left':
      startX = sourceNode.value.left;
      startY = sourceNode.value.top + nodeHeight / 2;
      break;
    default:
      startX = sourceNode.value.left + nodeWidth;
      startY = sourceNode.value.top + nodeHeight / 2;
  }
  
  const endX = mousePos.x;
  const endY = mousePos.y;
  
  // 计算控制点
  const controlPointX1 = startX + (endX - startX) / 3;
  const controlPointY1 = startY;
  const controlPointX2 = startX + (endX - startX) * 2 / 3;
  const controlPointY2 = endY;
  
  // 返回贝塞尔曲线路径
  return `M ${startX} ${startY} C ${controlPointX1} ${controlPointY1}, ${controlPointX2} ${controlPointY2}, ${endX} ${endY}`;
};

// 组件挂载和卸载
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
  document.removeEventListener('mousemove', dragNode);
  document.removeEventListener('mouseup', stopDragNode);
  document.removeEventListener('mousemove', dragEdge);
  document.removeEventListener('mouseup', stopDrawEdge);
});

// 处理键盘事件
const handleKeyDown = (event: KeyboardEvent) => {
  // 删除选中的元素
  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (selectedNode.value) {
      removeNode(selectedNode.value);
    } else if (selectedEdge.value) {
      const index = props.DataAll.edges.findIndex(e => e.id === selectedEdge.value.id);
      if (index !== -1) {
        props.DataAll.edges.splice(index, 1);
        emit('updateDAG', { edgeId: selectedEdge.value.id }, 'delete-edge');
        selectedEdge.value = null;
      }
    }
  }
};
</script>

<style scoped>
.dag-board {
  width: 100%;
  height: 100%;
  overflow: auto;
  position: relative;
}

.dag-canvas {
  width: 100%;
  height: 100%;
  min-width: 2000px;
  min-height: 1500px;
  position: relative;
}

.dag-edges {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.edge-path {
  fill: none;
  stroke: #bfbfbf;
  stroke-width: 2px;
  pointer-events: stroke;
  cursor: pointer;
  transition: stroke 0.3s;
}

.edge-selected {
  stroke: #1890ff;
  stroke-width: 2.5px;
}

.edge-drawing {
  stroke: #1890ff;
  stroke-dasharray: 5,5;
  animation: dash 1s linear infinite;
}

@keyframes dash {
  to {
    stroke-dashoffset: 10;
  }
}

.dag-node {
  position: absolute;
  width: 120px;
  height: 60px;
  background-color: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  cursor: move;
  user-select: none;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: all 0.3s;
}

.node-selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.node-icon {
  font-size: 18px;
  color: #1890ff;
  margin-bottom: 4px;
}

.node-title {
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.node-status {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.node-status .status-dot {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: #bfbfbf;
}

.node-status.success .status-dot {
  background-color: #52c41a;
}

.node-status.running .status-dot {
  background-color: #1890ff;
  animation: pulse 1.5s infinite;
}

.node-status.error .status-dot {
  background-color: #f5222d;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.node-anchors {
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
}

.anchor {
  position: absolute;
  width: 10px;
  height: 10px;
  background-color: #fff;
  border: 1px solid #1890ff;
  border-radius: 50%;
  cursor: crosshair;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.3s;
}

.dag-node:hover .anchor {
  opacity: 1;
}

.anchor-left {
  left: -5px;
  top: 50%;
  transform: translateY(-50%);
}

.anchor-right {
  right: -5px;
  top: 50%;
  transform: translateY(-50%);
}

.anchor-top {
  top: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.anchor-bottom {
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
}

.node-remove {
  position: absolute;
  top: -8px;
  left: -8px;
  width: 16px;
  height: 16px;
  background-color: #ff4d4f;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 10px;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.3s;
  z-index: 3;
}

.dag-node:hover .node-remove {
  opacity: 1;
}

.temp-edge-target {
  position: absolute;
  width: a8px;
  height: 8px;
  border-radius: 50%;
  background-color: #1890ff;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 2;
}
</style> 