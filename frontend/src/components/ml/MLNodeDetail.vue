<template>
  <div class="ml-node-detail" v-if="selectedNode">
    <div class="detail-header">
      <component :is="getNodeIcon(selectedNode.type)" />
      <h3>{{ selectedNode.name }}</h3>
      <a-button type="text" class="close-btn" @click="handleClose">
        <close-outlined />
      </a-button>
    </div>
    
    <div class="detail-content">
      <div class="node-description">
        {{ getNodeDescription(selectedNode.type) }}
      </div>
      
      <a-divider />
      
      <div class="node-config">
        <h4>节点配置</h4>
        
        <!-- 数据源配置 -->
        <template v-if="selectedNode.type === 'dataSource'">
          <a-form layout="vertical">
            <a-form-item label="数据来源">
              <a-select v-model:value="selectedNode.config.sourceType" @change="updateNodeConfig">
                <a-select-option value="file">文件</a-select-option>
                <a-select-option value="database">数据库</a-select-option>
                <a-select-option value="api">API</a-select-option>
              </a-select>
            </a-form-item>
            
            <template v-if="selectedNode.config.sourceType === 'file'">
              <a-form-item label="文件类型">
                <a-select v-model:value="selectedNode.config.fileType" @change="updateNodeConfig">
                  <a-select-option value="csv">CSV</a-select-option>
                  <a-select-option value="excel">Excel</a-select-option>
                  <a-select-option value="json">JSON</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="文件路径">
                <a-input v-model:value="selectedNode.config.filePath" @change="updateNodeConfig" />
              </a-form-item>
            </template>
            
            <template v-if="selectedNode.config.sourceType === 'database'">
              <a-form-item label="数据库类型">
                <a-select v-model:value="selectedNode.config.dbType" @change="updateNodeConfig">
                  <a-select-option value="mysql">MySQL</a-select-option>
                  <a-select-option value="postgresql">PostgreSQL</a-select-option>
                  <a-select-option value="mongodb">MongoDB</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="连接字符串">
                <a-input v-model:value="selectedNode.config.connectionString" @change="updateNodeConfig" />
              </a-form-item>
            </template>
          </a-form>
        </template>
        
        <!-- 数据预处理配置 -->
        <template v-if="selectedNode.type === 'dataPreprocessing'">
          <a-form layout="vertical">
            <a-form-item label="处理选项">
              <a-checkbox-group v-model:value="selectedNode.config.options" @change="updateNodeConfig">
                <a-checkbox value="missing">缺失值处理</a-checkbox>
                <a-checkbox value="outlier">异常值检测</a-checkbox>
                <a-checkbox value="duplicate">重复数据删除</a-checkbox>
              </a-checkbox-group>
            </a-form-item>
            <a-form-item v-if="selectedNode.config.options.includes('missing')" label="缺失值处理方式">
              <a-select v-model:value="selectedNode.config.missingStrategy" @change="updateNodeConfig">
                <a-select-option value="drop">删除行</a-select-option>
                <a-select-option value="fill_mean">均值填充</a-select-option>
                <a-select-option value="fill_median">中位数填充</a-select-option>
                <a-select-option value="fill_mode">众数填充</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </template>
        
        <!-- 机器学习模型配置 -->
        <template v-if="selectedNode.type === 'linearRegression' || selectedNode.type === 'logisticRegression'">
          <a-form layout="vertical">
            <a-form-item label="正则化">
              <a-select v-model:value="selectedNode.config.regularization" @change="updateNodeConfig">
                <a-select-option value="none">无</a-select-option>
                <a-select-option value="l1">L1 (Lasso)</a-select-option>
                <a-select-option value="l2">L2 (Ridge)</a-select-option>
                <a-select-option value="elasticnet">ElasticNet</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="学习率">
              <a-slider
                v-model:value="selectedNode.config.learningRate"
                :min="0.001"
                :max="1"
                :step="0.001"
                @change="updateNodeConfig"
              />
              <a-input-number
                v-model:value="selectedNode.config.learningRate"
                :min="0.001"
                :max="1"
                :step="0.001"
                style="width: 100px"
                @change="updateNodeConfig"
              />
            </a-form-item>
            <a-form-item label="最大迭代次数">
              <a-input-number 
                v-model:value="selectedNode.config.maxIterations" 
                :min="1" 
                :max="10000" 
                @change="updateNodeConfig" 
              />
            </a-form-item>
          </a-form>
        </template>
        
        <!-- 决策树配置 -->
        <template v-if="selectedNode.type === 'decisionTree'">
          <a-form layout="vertical">
            <a-form-item label="最大深度">
              <a-input-number 
                v-model:value="selectedNode.config.maxDepth" 
                :min="1" 
                :max="100"
                @change="updateNodeConfig" 
              />
            </a-form-item>
            <a-form-item label="最小样本分割数">
              <a-input-number 
                v-model:value="selectedNode.config.minSamplesSplit" 
                :min="2" 
                @change="updateNodeConfig" 
              />
            </a-form-item>
            <a-form-item label="评价标准">
              <a-select v-model:value="selectedNode.config.criterion" @change="updateNodeConfig">
                <a-select-option value="gini">基尼不纯度</a-select-option>
                <a-select-option value="entropy">信息熵</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </template>
        
        <!-- 深度学习配置 -->
        <template v-if="selectedNode.type === 'dnn'">
          <a-form layout="vertical">
            <a-form-item label="隐藏层">
              <a-button @click="addHiddenLayer" size="small" type="primary">
                添加隐藏层
              </a-button>
              <div v-for="(layer, index) in selectedNode.config.hiddenLayers" :key="index" class="layer-item">
                <span>层 {{ index + 1 }}: </span>
                <a-input-number 
                  v-model:value="layer.units" 
                  :min="1" 
                  :max="1000" 
                  @change="updateNodeConfig" 
                />
                <a-select 
                  v-model:value="layer.activation" 
                  style="width: 120px" 
                  @change="updateNodeConfig"
                >
                  <a-select-option value="relu">ReLU</a-select-option>
                  <a-select-option value="sigmoid">Sigmoid</a-select-option>
                  <a-select-option value="tanh">Tanh</a-select-option>
                </a-select>
                <a-button 
                  type="text" 
                  danger 
                  @click="removeHiddenLayer(index)" 
                  size="small"
                >
                  <delete-outlined />
                </a-button>
              </div>
            </a-form-item>
            <a-form-item label="优化器">
              <a-select v-model:value="selectedNode.config.optimizer" @change="updateNodeConfig">
                <a-select-option value="adam">Adam</a-select-option>
                <a-select-option value="sgd">SGD</a-select-option>
                <a-select-option value="rmsprop">RMSprop</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </template>
        
        <!-- 数据分割配置 -->
        <template v-if="selectedNode.type === 'dataSplit'">
          <a-form layout="vertical">
            <a-form-item label="测试集比例">
              <a-slider
                v-model:value="selectedNode.config.testSize"
                :min="0.1"
                :max="0.5"
                :step="0.05"
                @change="updateNodeConfig"
              />
              <span>{{ Math.round(selectedNode.config.testSize * 100) }}%</span>
            </a-form-item>
            <a-form-item label="随机种子">
              <a-input-number 
                v-model:value="selectedNode.config.randomSeed" 
                :min="1" 
                @change="updateNodeConfig" 
              />
            </a-form-item>
            <a-form-item label="分层抽样">
              <a-switch 
                v-model:checked="selectedNode.config.stratify" 
                @change="updateNodeConfig" 
              />
            </a-form-item>
          </a-form>
        </template>
        
        <!-- 缺少具体配置的节点显示默认消息 -->
        <template v-if="!hasSpecificConfig(selectedNode.type)">
          <a-empty description="该节点暂无可配置项" />
        </template>
      </div>
    </div>
  </div>
  <div class="ml-node-detail-empty" v-else>
    <a-empty description="请选择一个节点进行配置" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { 
  CloseOutlined, 
  DeleteOutlined,
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

const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  }
});

const emit = (['close', 'update']);

// 处理关闭
const handleClose = () => {
  emit('close');
};

// 更新节点配置
const updateNodeConfig = () => {
  if (props.selectedNode) {
    emit('update', props.selectedNode);
  }
};

// 添加隐藏层（用于DNN配置）
const addHiddenLayer = () => {
  if (props.selectedNode && props.selectedNode.config && props.selectedNode.config.hiddenLayers) {
    props.selectedNode.config.hiddenLayers.push({
      units: 64,
      activation: 'relu'
    });
    updateNodeConfig();
  }
};

// 移除隐藏层
const removeHiddenLayer = (index: number) => {
  if (props.selectedNode && props.selectedNode.config && props.selectedNode.config.hiddenLayers) {
    props.selectedNode.config.hiddenLayers.splice(index, 1);
    updateNodeConfig();
  }
};

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

// 获取节点描述
const getNodeDescription = (type: string) => {
  const descriptionMap: Record<string, string> = {
    'dataSource': '用于从文件、数据库或API导入数据集，支持多种数据格式。',
    'dataSplit': '将数据集分割为训练集和测试集，可配置分割比例和随机种子。',
    'dataPreprocessing': '执行数据清洗、缺失值处理和异常值检测等预处理操作。',
    'dataTransformation': '对数据进行标准化、归一化和分箱处理等转换操作。',
    'featureSelection': '通过统计方法选择最相关的特征，减少数据维度。',
    'featureExtraction': '从原始数据中提取有意义的特征，增强模型性能。',
    'dimensionReduction': '使用PCA、t-SNE等算法降低数据维度，保留关键信息。',
    'linearRegression': '线性回归模型，适用于预测连续变量的值。',
    'logisticRegression': '逻辑回归分类模型，适用于二分类问题。',
    'decisionTree': '决策树模型，适用于分类和回归问题，具有良好的可解释性。',
    'randomForest': '随机森林集成模型，由多个决策树组成，提高预测准确性。',
    'svm': '支持向量机算法，适用于分类和回归任务，支持非线性边界。',
    'dnn': '深度神经网络，可配置多个隐藏层，适用于复杂模式识别。',
    'cnn': '卷积神经网络，专为图像处理和计算机视觉任务设计。',
    'rnn': '循环神经网络，适用于序列数据和时间序列分析。',
    'evaluation': '评估模型性能指标，包括精确度、召回率、F1分数等。',
    'modelExport': '导出训练好的模型，支持多种格式和部署选项。'
  };
  
  return descriptionMap[type] || '无可用描述';
};

// 检查是否有特定配置
const hasSpecificConfig = (type: string) => {
  const typesWithConfig = [
    'dataSource', 'dataPreprocessing', 'linearRegression', 
    'logisticRegression', 'decisionTree', 'dnn', 'dataSplit'
  ];
  
  return typesWithConfig.includes(type);
};
</script>

<style scoped>
.ml-node-detail, .ml-node-detail-empty {
  height: 100%;
  background-color: #fff;
  border-left: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.ml-node-detail-empty {
  align-items: center;
  justify-content: center;
}

.detail-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  position: relative;
}

.detail-header h3 {
  margin: 0 0 0 12px;
  flex: 1;
}

.close-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.node-description {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 16px;
}

.node-config {
  margin-top: 16px;
}

.node-config h4 {
  margin-top: 0;
  margin-bottom: 16px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
}
</style> 