<template>
  <div class="node-bus" :style="{ left: pos_x + 'px', top: pos_y + 'px' }">
    <div class="node-bus-content">
      <div class="node-bus-icon">
        <component :is="getIconByType" />
      </div>
      <div class="node-bus-text">{{ displayName }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
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

interface Props {
  value: string;
  pos_x: number;
  pos_y: number;
}

const props = defineProps<Props>();

// 根据节点类型获取对应的图标
const getIconByType = computed(() => {
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
  return iconMap[props.value] || DatabaseOutlined;
});

// 获取节点显示名称
const displayName = computed(() => {
  const nameMap: Record<string, string> = {
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
  return nameMap[props.value] || props.value;
});
</script>

<style scoped>
.node-bus {
  position: fixed;
  z-index: 9999;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.node-bus-content {
  background-color: #fff;
  border: 2px solid #1890ff;
  border-radius: 4px;
  padding: 8px 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.node-bus-icon {
  font-size: 24px;
  color: #1890ff;
  margin-bottom: 4px;
}

.node-bus-text {
  font-size: 12px;
  font-weight: 500;
  text-align: center;
}
</style> 