<template>
  <div class="ml-canvas">
    <div 
      ref="canvasRef" 
      class="canvas-container"
      @drop="handleDrop"
      @dragover="handleDragOver"
      @click="clearSelection"
    >
      <!-- 节点元素 -->
      <div 
        v-for="node in nodes" 
        :key="node.id" 
        class="node" 
        :class="{ 'selected': selectedNodeId === node.id }"
        :style="{ 
          left: `${node.position.x}px`, 
          top: `${node.position.y}px` 
        }"
        @mousedown="startDragNode($event, node)"
        @click.stop="selectNode(node)"
      >
        <div class="node-header" :class="node.category">
          <component :is="getNodeIcon(node.type)" />
          <span>{{ node.name }}</span>
        </div>
        <div class="node-content">
          <div class="node-description">{{ node.description || '暂无描述' }}</div>
          
          <!-- 输入端口 -->
          <div class="node-ports node-inputs">
            <div 
              v-for="port in node.inputPorts" 
              :key="`input-${node.id}-${port.id}`"
              class="port input-port"
              @mousedown.stop="startConnection($event, node.id, port.id, 'input')"
            >
              <div class="port-point"></div>
              <span class="port-label">{{ port.label }}</span>
            </div>
          </div>
          
          <!-- 输出端口 -->
          <div class="node-ports node-outputs">
            <div 
              v-for="port in node.outputPorts" 
              :key="`output-${node.id}-${port.id}`"
              class="port output-port"
              @mousedown.stop="startConnection($event, node.id, port.id, 'output')"
            >
              <span class="port-label">{{ port.label }}</span>
              <div class="port-point"></div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 连接线 -->
      <svg class="connections-layer">
        <path
          v-for="connection in connections"
          :key="`${connection.sourceId}-${connection.sourcePort}-${connection.targetId}-${connection.targetPort}`"
          :d="generatePath(connection)"
          :class="['connection-path', { 'selected': selectedConnectionId === getConnectionId(connection) }]"
          @click.stop="selectConnection(connection)"
        ></path>
        
        <!-- 正在绘制的连接线 -->
        <path
          v-if="currentConnection"
          :d="generateDraftPath()"
          class="connection-path draft"
        ></path>
      </svg>
      
      <!-- 迷你地图 -->
      <div class="minimap">
        <div class="minimap-viewport"></div>
      </div>
      
      <!-- 画布控制按钮 -->
      <div class="canvas-controls">
        <a-button-group>
          <a-button @click="zoomIn">
            <zoom-in-outlined />
          </a-button>
          <a-button @click="resetZoom">
            <fullscreen-outlined />
          </a-button>
          <a-button @click="zoomOut">
            <zoom-out-outlined />
          </a-button>
        </a-button-group>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch } from 'vue';
import { 
  ZoomInOutlined, 
  ZoomOutOutlined, 
  FullscreenOutlined,
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
  ExportOutlined
} from '@ant-design/icons-vue';

const emit = defineEmits<{
  (e: 'node-selected', nodeId: string): void;
  (e: 'update:nodes', nodes: any[]): void;
  (e: 'update:connections', connections: any[]): void;
  (e: 'connection-created', connection: any): void;
  (e: 'connection-removed', connectionId: string): void;
  (e: 'node-added', node: any): void;
  (e: 'node-removed', nodeId: string): void;
}>();

const props = defineProps<{
  nodes: any[];
  connections: any[];
}>();

// 画布引用
const canvasRef = ref<HTMLElement | null>(null);
// 缩放级别
const scale = ref(1);
// 平移位置
const position = reactive({ x: 0, y: 0 });
// 当前选中的节点ID
const selectedNodeId = ref<string | null>(null);
// 当前选中的连接ID
const selectedConnectionId = ref<string | null>(null);
// 拖拽相关状态
const isDragging = ref(false);
const dragOffset = reactive({ x: 0, y: 0 });
const dragNodeId = ref<string | null>(null);
// 连接相关状态
const currentConnection = ref<any | null>(null);
const mousePosition = reactive({ x: 0, y: 0 });

// 获取节点对应的图标
const getNodeIcon = (type: string) => {
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

// 处理节点拖拽开始
const startDragNode = (event: MouseEvent, node: any) => {
  event.preventDefault();
  isDragging.value = true;
  dragNodeId.value = node.id;

  // 计算点击位置相对于节点左上角的偏移
  const element = event.target as HTMLElement;
  const nodeElement = element.closest('.node') as HTMLElement;
  
  if (nodeElement) {
    const rect = nodeElement.getBoundingClientRect();
    dragOffset.x = event.clientX - rect.left;
    dragOffset.y = event.clientY - rect.top;
  }

  // 添加鼠标移动和释放事件监听
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

// 处理鼠标移动（节点拖拽中）
const handleMouseMove = (event: MouseEvent) => {
  if (!isDragging.value || !dragNodeId.value) return;
  
  const canvasRect = canvasRef.value?.getBoundingClientRect();
  if (!canvasRect) return;
  
  // 找到正在拖拽的节点
  const nodeIndex = props.nodes.findIndex(node => node.id === dragNodeId.value);
  if (nodeIndex === -1) return;
  
  // 计算新位置
  const x = event.clientX - canvasRect.left - dragOffset.x;
  const y = event.clientY - canvasRect.top - dragOffset.y;
  
  // 更新节点位置
  const updatedNodes = [...props.nodes];
  updatedNodes[nodeIndex] = {
    ...updatedNodes[nodeIndex],
    position: { x, y }
  };
  
  emit('update:nodes', updatedNodes);
};

// 处理鼠标释放（结束拖拽）
const handleMouseUp = () => {
  isDragging.value = false;
  dragNodeId.value = null;
  
  // 移除事件监听
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
  
  // 若正在创建连接，尝试完成连接
  if (currentConnection.value) {
    finalizeConnection();
  }
};

// 处理拖放新节点
const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  
  if (!event.dataTransfer) return;
  
  const nodeData = event.dataTransfer.getData('application/json');
  if (!nodeData) return;
  
  try {
    const nodeType = JSON.parse(nodeData);
    
    // 获取相对于画布的位置
    const canvasRect = canvasRef.value?.getBoundingClientRect();
    if (!canvasRect) return;
    
    const x = event.clientX - canvasRect.left;
    const y = event.clientY - canvasRect.top;
    
    // 创建新节点
    const newNode = createNode(nodeType, { x, y });
    emit('node-added', newNode);
    
    // 选中新节点
    selectNode(newNode);
  } catch (e) {
    console.error('无法解析拖拽数据', e);
  }
};

// 允许拖放
const handleDragOver = (event: DragEvent) => {
  event.preventDefault();
};

// 创建新节点
const createNode = (nodeType: any, position: { x: number, y: number }) => {
  const id = `node-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
  
  // 基于节点类型创建输入/输出端口
  const inputPorts = getDefaultInputPorts(nodeType.type);
  const outputPorts = getDefaultOutputPorts(nodeType.type);
  
  return {
    id,
    name: nodeType.name,
    type: nodeType.type,
    category: nodeType.category,
    description: nodeType.description || '',
    position,
    inputPorts,
    outputPorts
  };
};

// 获取默认输入端口
const getDefaultInputPorts = (type: string) => {
  const defaultPorts: any[] = [];
  
  // 根据节点类型添加默认输入端口
  if (type !== 'dataSource') {
    defaultPorts.push({
      id: 'input',
      label: '输入'
    });
  }
  
  return defaultPorts;
};

// 获取默认输出端口
const getDefaultOutputPorts = (type: string) => {
  const defaultPorts: any[] = [];
  
  // 根据节点类型添加默认输出端口
  if (type !== 'evaluation' && type !== 'modelExport') {
    defaultPorts.push({
      id: 'output',
      label: '输出'
    });
  }
  
  if (type === 'dataSplit') {
    defaultPorts.push({
      id: 'train',
      label: '训练集'
    });
    defaultPorts.push({
      id: 'test',
      label: '测试集'
    });
  }
  
  return defaultPorts;
};

// 选择节点
const selectNode = (node: any) => {
  selectedNodeId.value = node.id;
  selectedConnectionId.value = null;
  emit('node-selected', node.id);
};

// 清除选择
const clearSelection = () => {
  selectedNodeId.value = null;
  selectedConnectionId.value = null;
  emit('node-selected', '');
};

// 开始创建连接
const startConnection = (event: MouseEvent, nodeId: string, portId: string, portType: 'input' | 'output') => {
  event.preventDefault();
  event.stopPropagation();
  
  // 如果是输入端口，则不能作为连接起点
  if (portType === 'input') return;
  
  // 初始化连接
  currentConnection.value = {
    sourceId: nodeId,
    sourcePort: portId,
    targetId: null,
    targetPort: null
  };
  
  // 记录鼠标位置
  mousePosition.x = event.clientX;
  mousePosition.y = event.clientY;
  
  // 添加鼠标移动和释放事件监听
  document.addEventListener('mousemove', handleConnectionDrag);
  document.addEventListener('mouseup', finalizeConnection);
};

// 拖动连接线过程中
const handleConnectionDrag = (event: MouseEvent) => {
  mousePosition.x = event.clientX;
  mousePosition.y = event.clientY;
};

// 生成草稿连接路径
const generateDraftPath = () => {
  if (!currentConnection.value) return '';
  
  // 找到起始节点和端口
  const sourceNode = props.nodes.find(node => node.id === currentConnection.value.sourceId);
  if (!sourceNode) return '';
  
  // 找到起始端口元素并计算其位置
  const canvasRect = canvasRef.value?.getBoundingClientRect();
  if (!canvasRect) return '';
  
  // 计算起点位置（节点的输出端口）
  const startX = sourceNode.position.x + 200; // 假设节点宽度为200px
  const startY = sourceNode.position.y + 40; // 假设输出端口在节点顶部40px位置
  
  // 计算终点（当前鼠标位置）
  const endX = mousePosition.x - canvasRect.left;
  const endY = mousePosition.y - canvasRect.top;
  
  // 生成贝塞尔曲线路径
  return `M ${startX} ${startY} C ${startX + 100} ${startY}, ${endX - 100} ${endY}, ${endX} ${endY}`;
};

// 完成连接创建
const finalizeConnection = () => {
  document.removeEventListener('mousemove', handleConnectionDrag);
  document.removeEventListener('mouseup', finalizeConnection);
  
  if (!currentConnection.value) return;
  
  // 检查鼠标是否在某个输入端口上
  const portElement = document.elementFromPoint(mousePosition.x, mousePosition.y);
  if (portElement && portElement.classList.contains('port-point')) {
    const portContainer = portElement.closest('.port') as HTMLElement;
    if (portContainer && portContainer.classList.contains('input-port')) {
      // 找到端口所属的节点
      const nodeElement = portContainer.closest('.node') as HTMLElement;
      if (nodeElement) {
        const nodeId = nodeElement.getAttribute('data-node-id');
        const portId = portContainer.getAttribute('data-port-id');
        
        if (nodeId && portId) {
          // 检查是否形成循环
          if (nodeId !== currentConnection.value.sourceId) {
            // 完成连接
            const newConnection = {
              ...currentConnection.value,
              targetId: nodeId,
              targetPort: portId
            };
            
            // 发送连接创建事件
            emit('connection-created', newConnection);
          }
        }
      }
    }
  }
  
  // 清除当前连接
  currentConnection.value = null;
};

// 生成连接路径
const generatePath = (connection: any) => {
  const sourceNode = props.nodes.find(node => node.id === connection.sourceId);
  const targetNode = props.nodes.find(node => node.id === connection.targetId);
  
  if (!sourceNode || !targetNode) return '';
  
  // 计算起点和终点
  const startX = sourceNode.position.x + 200; // 假设节点宽度为200px
  const startY = sourceNode.position.y + 40; // 假设输出端口位置
  
  const endX = targetNode.position.x;
  const endY = targetNode.position.y + 40; // 假设输入端口位置
  
  // 生成贝塞尔曲线路径
  return `M ${startX} ${startY} C ${startX + 100} ${startY}, ${endX - 100} ${endY}, ${endX} ${endY}`;
};

// 获取连接唯一ID
const getConnectionId = (connection: any) => {
  return `${connection.sourceId}-${connection.sourcePort}-${connection.targetId}-${connection.targetPort}`;
};

// 选择连接
const selectConnection = (connection: any) => {
  selectedNodeId.value = null;
  selectedConnectionId.value = getConnectionId(connection);
};

// 缩放控制
const zoomIn = () => {
  scale.value = Math.min(scale.value + 0.1, 2);
};

const zoomOut = () => {
  scale.value = Math.max(scale.value - 0.1, 0.5);
};

const resetZoom = () => {
  scale.value = 1;
  position.x = 0;
  position.y = 0;
};

// 监听画布尺寸变化
onMounted(() => {
  window.addEventListener('resize', updateMinimap);
  updateMinimap();
});

onUnmounted(() => {
  window.removeEventListener('resize', updateMinimap);
});

// 更新迷你地图
const updateMinimap = () => {
  // 这里可以实现迷你地图的逻辑
};

// 键盘事件处理（删除节点或连接）
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Delete' || event.key === 'Backspace') {
    // 删除选中的节点
    if (selectedNodeId.value) {
      emit('node-removed', selectedNodeId.value);
      selectedNodeId.value = null;
    }
    
    // 删除选中的连接
    if (selectedConnectionId.value) {
      emit('connection-removed', selectedConnectionId.value);
      selectedConnectionId.value = null;
    }
  }
};

// 添加键盘事件监听
onMounted(() => {
  document.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown);
});
</script>

<style scoped>
.ml-canvas {
  height: 100%;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.canvas-container {
  position: relative;
  width: 100%;
  height: 100%;
  background-color: #f5f5f5;
  background-image: radial-gradient(#e0e0e0 1px, transparent 0);
  background-size: 20px 20px;
  overflow: hidden;
}

.node {
  position: absolute;
  width: 200px;
  border-radius: 4px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: move;
  user-select: none;
  transition: box-shadow 0.2s;
  overflow: hidden;
}

.node:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.node.selected {
  box-shadow: 0 0 0 2px #1890ff, 0 4px 12px rgba(0, 0, 0, 0.15);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.node-header.data {
  background-color: #e6f7ff;
}

.node-header.preprocessing {
  background-color: #f6ffed;
}

.node-header.feature {
  background-color: #fff7e6;
}

.node-header.model {
  background-color: #f9f0ff;
}

.node-header.evaluation {
  background-color: #fff2e8;
}

.node-content {
  padding: 12px;
}

.node-description {
  font-size: 12px;
  color: #888;
  margin-bottom: 12px;
}

.node-ports {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.node-inputs {
  margin-bottom: 12px;
}

.port {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.input-port {
  padding-left: 0;
}

.output-port {
  justify-content: flex-end;
  padding-right: 0;
}

.port-point {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #1890ff;
  cursor: pointer;
}

.input-port .port-point {
  margin-right: 8px;
}

.output-port .port-point {
  margin-left: 8px;
}

.port-label {
  color: #666;
}

.connections-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.connection-path {
  fill: none;
  stroke: #1890ff;
  stroke-width: 2;
  pointer-events: auto;
  cursor: pointer;
}

.connection-path.draft {
  stroke-dasharray: 5, 5;
}

.connection-path.selected {
  stroke: #ff4d4f;
  stroke-width: 3;
}

.minimap {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 150px;
  height: 100px;
  background-color: rgba(255, 255, 255, 0.8);
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.minimap-viewport {
  position: absolute;
  border: 1px solid #1890ff;
  background-color: rgba(24, 144, 255, 0.1);
  pointer-events: none;
}

.canvas-controls {
  position: absolute;
  bottom: 16px;
  left: 16px;
  z-index: 10;
}
</style> 