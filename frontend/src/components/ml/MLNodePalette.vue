<template>
  <div class="ml-node-palette">
    <div class="palette-header">
      <h3>节点库</h3>
      <a-input-search
        v-model:value="searchText"
        placeholder="搜索节点"
        style="width: 100%"
      />
    </div>
    
    <div class="palette-content">
      <a-collapse v-model:activeKey="activeCategories" accordion>
        <a-collapse-panel v-for="category in categories" :key="category.key" :header="category.name">
          <div class="node-group">
            <div 
              v-for="nodeType in filteredNodeTypes.filter(node => node.category === category.key)" 
              :key="nodeType.type"
              class="node-item"
              draggable="true"
              @dragstart="handleDragStart($event, nodeType)"
            >
              <component :is="getNodeIcon(nodeType.type)" />
              <span>{{ nodeType.name }}</span>
            </div>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
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

// 节点类别
const categories = [
  { key: 'data', name: '数据处理' },
  { key: 'preprocessing', name: '数据预处理' },
  { key: 'feature', name: '特征工程' },
  { key: 'model', name: '机器学习模型' },
  { key: 'deeplearning', name: '深度学习' },
  { key: 'evaluation', name: '模型评估' },
];

// 活跃的类别
const activeCategories = ref(['data']);

// 搜索文本
const searchText = ref('');

// 节点类型列表
const nodeTypes = [
  // 数据处理
  {
    type: 'dataSource',
    name: '数据源',
    category: 'data',
    description: '从文件、数据库或API导入数据'
  },
  {
    type: 'dataSplit',
    name: '数据分割',
    category: 'data',
    description: '将数据集分割为训练集和测试集'
  },
  
  // 数据预处理
  {
    type: 'dataPreprocessing',
    name: '数据预处理',
    category: 'preprocessing',
    description: '数据清洗、缺失值处理和异常值检测'
  },
  {
    type: 'dataTransformation',
    name: '数据转换',
    category: 'preprocessing',
    description: '标准化、归一化和分箱处理'
  },
  
  // 特征工程
  {
    type: 'featureSelection',
    name: '特征选择',
    category: 'feature',
    description: '选择最相关的特征'
  },
  {
    type: 'featureExtraction',
    name: '特征提取',
    category: 'feature',
    description: '从原始数据中提取特征'
  },
  {
    type: 'dimensionReduction',
    name: '降维',
    category: 'feature',
    description: '使用PCA、t-SNE等降低维度'
  },
  
  // 机器学习模型
  {
    type: 'linearRegression',
    name: '线性回归',
    category: 'model',
    description: '线性回归模型'
  },
  {
    type: 'logisticRegression',
    name: '逻辑回归',
    category: 'model',
    description: '逻辑回归分类模型'
  },
  {
    type: 'decisionTree',
    name: '决策树',
    category: 'model',
    description: '决策树分类与回归模型'
  },
  {
    type: 'randomForest',
    name: '随机森林',
    category: 'model',
    description: '随机森林集成模型'
  },
  {
    type: 'svm',
    name: '支持向量机',
    category: 'model',
    description: '支持向量机分类与回归'
  },
  
  // 深度学习
  {
    type: 'dnn',
    name: '深度神经网络',
    category: 'deeplearning',
    description: '多层感知机神经网络'
  },
  {
    type: 'cnn',
    name: '卷积神经网络',
    category: 'deeplearning',
    description: '用于图像处理的卷积网络'
  },
  {
    type: 'rnn',
    name: '循环神经网络',
    category: 'deeplearning',
    description: '用于序列数据的循环网络'
  },
  
  // 模型评估
  {
    type: 'evaluation',
    name: '模型评估',
    category: 'evaluation',
    description: '评估模型性能指标'
  },
  {
    type: 'modelExport',
    name: '模型导出',
    category: 'evaluation',
    description: '导出训练好的模型'
  }
];

// 根据搜索过滤节点类型
const filteredNodeTypes = computed(() => {
  if (!searchText.value) return nodeTypes;
  
  const search = searchText.value.toLowerCase();
  return nodeTypes.filter(node => {
    return node.name.toLowerCase().includes(search) || 
           node.description.toLowerCase().includes(search);
  });
});

// 获取节点图标
const getNodeIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    'dataSource': DatabaseOutlined,
    'dataSplit': ScissorOutlined,
    'dataPreprocessing': FilterOutlined,
    'dataTransformation': FilterOutlined,
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
const handleDragStart = (event: DragEvent, nodeType: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/json', JSON.stringify(nodeType));
    event.dataTransfer.effectAllowed = 'copy';
  }
};
</script>

<style scoped>
.ml-node-palette {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
  border-right: 1px solid #f0f0f0;
}

.palette-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.palette-header h3 {
  margin-top: 0;
  margin-bottom: 16px;
}

.palette-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.node-group {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
}

.node-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  cursor: move;
  text-align: center;
  transition: background-color 0.2s, box-shadow 0.2s;
}

.node-item:hover {
  background-color: #f5f5f5;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.node-item span {
  font-size: 12px;
}

:deep(.ant-collapse-header) {
  font-weight: bold;
}

:deep(.ant-collapse-item) {
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}
</style> 