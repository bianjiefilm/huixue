<template>
  <div class="ml-toolbox">
    <div class="toolbox-header">
      <h3>组件库</h3>
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索组件..."
        style="width: 100%"
        @change="handleSearch"
      />
    </div>
    
    <a-collapse v-model:activeKey="activeCategories" :bordered="false">
      <!-- 数据处理 -->
      <a-collapse-panel key="data" header="数据处理">
        <div class="node-category">
          <div 
            v-for="node in filteredNodes.data" 
            :key="node.type" 
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <div class="node-icon">
              <component :is="node.icon" />
            </div>
            <div class="node-name">{{ node.name }}</div>
          </div>
        </div>
      </a-collapse-panel>

      <!-- 特征工程 -->
      <a-collapse-panel key="feature" header="特征工程">
        <div class="node-category">
          <div 
            v-for="node in filteredNodes.feature" 
            :key="node.type" 
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <div class="node-icon">
              <component :is="node.icon" />
            </div>
            <div class="node-name">{{ node.name }}</div>
          </div>
        </div>
      </a-collapse-panel>

      <!-- 机器学习模型 -->
      <a-collapse-panel key="model" header="机器学习模型">
        <div class="node-category">
          <div 
            v-for="node in filteredNodes.model" 
            :key="node.type" 
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <div class="node-icon">
              <component :is="node.icon" />
            </div>
            <div class="node-name">{{ node.name }}</div>
          </div>
        </div>
      </a-collapse-panel>

      <!-- 深度学习模型 -->
      <a-collapse-panel key="deep" header="深度学习模型">
        <div class="node-category">
          <div 
            v-for="node in filteredNodes.deep" 
            :key="node.type" 
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <div class="node-icon">
              <component :is="node.icon" />
            </div>
            <div class="node-name">{{ node.name }}</div>
          </div>
        </div>
      </a-collapse-panel>

      <!-- 评估及工具 -->
      <a-collapse-panel key="evaluation" header="评估及工具">
        <div class="node-category">
          <div 
            v-for="node in filteredNodes.evaluation" 
            :key="node.type" 
            class="node-item"
            draggable="true"
            @dragstart="handleDragStart($event, node)"
          >
            <div class="node-icon">
              <component :is="node.icon" />
            </div>
            <div class="node-name">{{ node.name }}</div>
          </div>
        </div>
      </a-collapse-panel>
    </a-collapse>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
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
  ExportOutlined
} from '@ant-design/icons-vue';

// 默认展开的分类
const activeCategories = ref(['data', 'model']);

// 搜索文本
const searchText = ref('');

// 发射事件
const emit = defineEmits<{
  (e: 'dragNode', nodeInfo: any): void;
}>();

// 节点定义
const nodeDefinitions = reactive({
  data: [
    { type: 'dataSource', name: '数据源', icon: DatabaseOutlined, category: 'data' },
    { type: 'dataPreprocessing', name: '数据预处理', icon: FilterOutlined, category: 'data' },
    { type: 'dataSplit', name: '数据切分', icon: ScissorOutlined, category: 'data' }
  ],
  feature: [
    { type: 'featureSelection', name: '特征选择', icon: HighlightOutlined, category: 'feature' },
    { type: 'featureExtraction', name: '特征提取', icon: BuildOutlined, category: 'feature' },
    { type: 'dimensionReduction', name: '降维', icon: NodeIndexOutlined, category: 'feature' }
  ],
  model: [
    { type: 'linearRegression', name: '线性回归', icon: LineChartOutlined, category: 'model' },
    { type: 'logisticRegression', name: '逻辑回归', icon: FunctionOutlined, category: 'model' },
    { type: 'decisionTree', name: '决策树', icon: ApartmentOutlined, category: 'model' },
    { type: 'randomForest', name: '随机森林', icon: ClusterOutlined, category: 'model' },
    { type: 'svm', name: '支持向量机', icon: RadarChartOutlined, category: 'model' }
  ],
  deep: [
    { type: 'dnn', name: 'DNN', icon: DeploymentUnitOutlined, category: 'deep' },
    { type: 'cnn', name: 'CNN', icon: FundProjectionScreenOutlined, category: 'deep' },
    { type: 'rnn', name: 'RNN', icon: PartitionOutlined, category: 'deep' }
  ],
  evaluation: [
    { type: 'evaluation', name: '评估指标', icon: BarChartOutlined, category: 'evaluation' },
    { type: 'modelExport', name: '模型导出', icon: ExportOutlined, category: 'evaluation' }
  ]
});

// 过滤后的节点
const filteredNodes = computed(() => {
  if (!searchText.value) {
    return nodeDefinitions;
  }

  const filterNodesBySearch = (nodes: any[]) => {
    return nodes.filter(node => 
      node.name.toLowerCase().includes(searchText.value.toLowerCase()) ||
      node.type.toLowerCase().includes(searchText.value.toLowerCase())
    );
  };

  return {
    data: filterNodesBySearch(nodeDefinitions.data),
    feature: filterNodesBySearch(nodeDefinitions.feature),
    model: filterNodesBySearch(nodeDefinitions.model),
    deep: filterNodesBySearch(nodeDefinitions.deep),
    evaluation: filterNodesBySearch(nodeDefinitions.evaluation)
  };
});

// 拖拽开始
const handleDragStart = (event: DragEvent, node: any) => {
  if (event.dataTransfer) {
    // 设置拖拽数据
    event.dataTransfer.setData('application/json', JSON.stringify(node));
    
    // 设置拖拽效果
    event.dataTransfer.effectAllowed = 'copy';
    
    // 发送事件到父组件
    emit('dragNode', node);
  }
};

// 搜索处理
const handleSearch = () => {
  // 如果搜索文本不为空，展开所有分类
  if (searchText.value) {
    activeCategories.value = ['data', 'feature', 'model', 'deep', 'evaluation'];
  }
};
</script>

<style scoped>
.ml-toolbox {
  height: 100%;
  overflow-y: auto;
  border-right: 1px solid #f0f0f0;
  background-color: #fafafa;
  padding: 16px 0;
}

.toolbox-header {
  padding: 0 16px 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.toolbox-header h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 16px;
  color: rgba(0, 0, 0, 0.85);
}

.node-category {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0;
}

.node-item {
  width: calc(50% - 4px);
  height: 72px;
  background-color: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: grab;
  transition: all 0.3s;
  padding: 8px;
}

.node-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.node-icon {
  font-size: 20px;
  color: #1890ff;
  margin-bottom: 8px;
}

.node-name {
  font-size: 12px;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

:deep(.ant-collapse) {
  background: transparent;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
}

:deep(.ant-collapse-content) {
  border-top: none;
}
</style> 