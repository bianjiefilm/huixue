<template>
  <div class="node-config-panel" v-if="selectedNode">
    <a-card :title="selectedNode.label" :bordered="false">
      <a-descriptions bordered size="small" :column="1" layout="vertical">
        <a-descriptions-item label="组件ID">{{ selectedNode.id }}</a-descriptions-item>
        <a-descriptions-item label="组件类型">{{ selectedNode.type }}</a-descriptions-item>
      </a-descriptions>
      
      <div class="config-form">
        <a-divider orientation="left">参数配置</a-divider>
        
        <!-- 根据节点类型显示不同的配置表单 -->
        <div v-if="selectedNode.type === 'dataSource'">
          <a-form layout="vertical">
            <a-form-item label="数据源类型">
              <a-select v-model:value="nodeConfig.dataSourceType">
                <a-select-option value="csv">CSV文件</a-select-option>
                <a-select-option value="database">数据库</a-select-option>
                <a-select-option value="api">API接口</a-select-option>
                <a-select-option value="builtIn">内置数据集</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.dataSourceType === 'csv'" label="文件路径">
              <a-input v-model:value="nodeConfig.filePath" placeholder="请输入CSV文件路径" />
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.dataSourceType === 'builtIn'" label="内置数据集">
              <a-select v-model:value="nodeConfig.builtInDataset">
                <a-select-option value="iris">鸢尾花数据集</a-select-option>
                <a-select-option value="boston">波士顿房价数据集</a-select-option>
                <a-select-option value="mnist">手写数字数据集</a-select-option>
                <a-select-option value="titanic">泰坦尼克号数据集</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.dataSourceType === 'database'" label="数据库类型">
              <a-select v-model:value="nodeConfig.databaseType">
                <a-select-option value="mysql">MySQL</a-select-option>
                <a-select-option value="postgresql">PostgreSQL</a-select-option>
                <a-select-option value="sqlite">SQLite</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.dataSourceType === 'api'" label="API URL">
              <a-input v-model:value="nodeConfig.apiUrl" placeholder="请输入API URL" />
            </a-form-item>
            
            <a-form-item label="数据预览行数">
              <a-input-number v-model:value="nodeConfig.previewRows" :min="1" :max="100" />
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'dataPreprocessing'">
          <a-form layout="vertical">
            <a-form-item label="缺失值处理">
              <a-select v-model:value="nodeConfig.missingValueStrategy">
                <a-select-option value="drop">删除缺失值行</a-select-option>
                <a-select-option value="mean">填充均值</a-select-option>
                <a-select-option value="median">填充中位数</a-select-option>
                <a-select-option value="mode">填充众数</a-select-option>
                <a-select-option value="constant">填充常数</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.missingValueStrategy === 'constant'" label="填充值">
              <a-input v-model:value="nodeConfig.fillValue" placeholder="请输入填充值" />
            </a-form-item>
            
            <a-form-item label="异常值处理">
              <a-select v-model:value="nodeConfig.outlierStrategy">
                <a-select-option value="none">不处理</a-select-option>
                <a-select-option value="clip">截断处理</a-select-option>
                <a-select-option value="remove">删除异常值</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="数据标准化">
              <a-select v-model:value="nodeConfig.standardization">
                <a-select-option value="none">不标准化</a-select-option>
                <a-select-option value="minmax">最小最大值缩放</a-select-option>
                <a-select-option value="zscore">Z-score标准化</a-select-option>
                <a-select-option value="robust">稳健标准化</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'dataSplit'">
          <a-form layout="vertical">
            <a-form-item label="拆分比例 (训练集)">
              <a-slider v-model:value="nodeConfig.trainRatio" :min="50" :max="90" :step="5" />
              <span>{{ nodeConfig.trainRatio }}% 训练集 / {{ 100 - nodeConfig.trainRatio }}% 测试集</span>
            </a-form-item>
            
            <a-form-item label="随机种子">
              <a-input-number v-model:value="nodeConfig.randomSeed" :min="0" :step="1" />
            </a-form-item>
            
            <a-form-item label="拆分策略">
              <a-select v-model:value="nodeConfig.splitStrategy">
                <a-select-option value="random">随机拆分</a-select-option>
                <a-select-option value="stratified">分层拆分</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'linearRegression'">
          <a-form layout="vertical">
            <a-form-item label="正则化方法">
              <a-select v-model:value="nodeConfig.regularization">
                <a-select-option value="none">无</a-select-option>
                <a-select-option value="l1">L1 (Lasso)</a-select-option>
                <a-select-option value="l2">L2 (Ridge)</a-select-option>
                <a-select-option value="elasticnet">弹性网络</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.regularization !== 'none'" label="正则化强度">
              <a-input-number v-model:value="nodeConfig.alpha" :min="0" :step="0.01" />
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.regularization === 'elasticnet'" label="L1比例">
              <a-slider v-model:value="nodeConfig.l1Ratio" :min="0" :max="1" :step="0.1" />
            </a-form-item>
            
            <a-form-item label="拟合截距">
              <a-switch v-model:checked="nodeConfig.fitIntercept" />
            </a-form-item>
            
            <a-form-item label="最大迭代次数">
              <a-input-number v-model:value="nodeConfig.maxIter" :min="100" :step="100" />
            </a-form-item>
            
            <a-form-item label="求解器">
              <a-select v-model:value="nodeConfig.solver">
                <a-select-option value="auto">自动选择</a-select-option>
                <a-select-option value="svd">奇异值分解</a-select-option>
                <a-select-option value="lsqr">最小二乘法</a-select-option>
                <a-select-option value="sag">随机平均梯度下降</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'logisticRegression'">
          <a-form layout="vertical">
            <a-form-item label="正则化方法">
              <a-select v-model:value="nodeConfig.regularization">
                <a-select-option value="none">无</a-select-option>
                <a-select-option value="l1">L1 (Lasso)</a-select-option>
                <a-select-option value="l2">L2 (Ridge)</a-select-option>
                <a-select-option value="elasticnet">弹性网络</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.regularization !== 'none'" label="正则化强度">
              <a-input-number v-model:value="nodeConfig.C" :min="0.01" :step="0.1" />
            </a-form-item>
            
            <a-form-item label="多分类策略">
              <a-select v-model:value="nodeConfig.multiClass">
                <a-select-option value="ovr">一对多</a-select-option>
                <a-select-option value="multinomial">多项式</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="最大迭代次数">
              <a-input-number v-model:value="nodeConfig.maxIter" :min="100" :step="100" />
            </a-form-item>
            
            <a-form-item label="求解器">
              <a-select v-model:value="nodeConfig.solver">
                <a-select-option value="lbfgs">LBFGS</a-select-option>
                <a-select-option value="liblinear">LIBLINEAR</a-select-option>
                <a-select-option value="newton-cg">Newton-CG</a-select-option>
                <a-select-option value="sag">SAG</a-select-option>
                <a-select-option value="saga">SAGA</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'randomForest'">
          <a-form layout="vertical">
            <a-form-item label="树的数量">
              <a-input-number v-model:value="nodeConfig.nEstimators" :min="10" :max="1000" :step="10" />
            </a-form-item>
            
            <a-form-item label="最大深度">
              <a-input-number v-model:value="nodeConfig.maxDepth" :min="1" :max="100" />
            </a-form-item>
            
            <a-form-item label="最小样本分割">
              <a-input-number v-model:value="nodeConfig.minSamplesSplit" :min="2" :step="1" />
            </a-form-item>
            
            <a-form-item label="最小样本叶子">
              <a-input-number v-model:value="nodeConfig.minSamplesLeaf" :min="1" :step="1" />
            </a-form-item>
            
            <a-form-item label="特征选择方式">
              <a-select v-model:value="nodeConfig.criterion">
                <a-select-option value="gini">基尼不纯度</a-select-option>
                <a-select-option value="entropy">信息熵</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="特征比例">
              <a-input-number v-model:value="nodeConfig.maxFeatures" :min="0.1" :max="1" :step="0.1" />
            </a-form-item>
            
            <a-form-item label="随机种子">
              <a-input-number v-model:value="nodeConfig.randomState" :min="0" :step="1" />
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else-if="selectedNode.type === 'evaluation'">
          <a-form layout="vertical">
            <a-form-item label="评估指标">
              <a-checkbox-group v-model:value="nodeConfig.metrics">
                <a-row>
                  <a-col :span="12">
                    <a-checkbox value="accuracy">准确率</a-checkbox>
                  </a-col>
                  <a-col :span="12">
                    <a-checkbox value="precision">精确率</a-checkbox>
                  </a-col>
                </a-row>
                <a-row>
                  <a-col :span="12">
                    <a-checkbox value="recall">召回率</a-checkbox>
                  </a-col>
                  <a-col :span="12">
                    <a-checkbox value="f1">F1分数</a-checkbox>
                  </a-col>
                </a-row>
                <a-row>
                  <a-col :span="12">
                    <a-checkbox value="auc">AUC</a-checkbox>
                  </a-col>
                  <a-col :span="12">
                    <a-checkbox value="mse">均方误差</a-checkbox>
                  </a-col>
                </a-row>
                <a-row>
                  <a-col :span="12">
                    <a-checkbox value="mae">平均绝对误差</a-checkbox>
                  </a-col>
                  <a-col :span="12">
                    <a-checkbox value="r2">R²</a-checkbox>
                  </a-col>
                </a-row>
              </a-checkbox-group>
            </a-form-item>
            
            <a-form-item label="交叉验证">
              <a-switch v-model:checked="nodeConfig.crossValidation" />
            </a-form-item>
            
            <a-form-item v-if="nodeConfig.crossValidation" label="折数">
              <a-input-number v-model:value="nodeConfig.kFold" :min="2" :max="10" :step="1" />
            </a-form-item>
            
            <a-form-item label="生成报告">
              <a-switch v-model:checked="nodeConfig.generateReport" />
            </a-form-item>
          </a-form>
        </div>
        
        <div v-else>
          <a-empty description="暂无配置项" />
        </div>
      </div>
      
      <div class="action-buttons">
        <a-button type="primary" @click="applyConfig">应用配置</a-button>
        <a-button @click="resetConfig">重置</a-button>
      </div>
    </a-card>
  </div>
  <div v-else class="empty-panel">
    <a-empty description="请选择一个节点进行配置" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue';

// 定义组件属性
const props = defineProps({
  selectedNode: {
    type: Object,
    default: null
  }
});

// 定义组件事件
const emit = defineEmits(['updateConfig']);

// 节点配置
const nodeConfig = reactive({
  // 数据源配置
  dataSourceType: 'csv',
  filePath: '',
  builtInDataset: 'iris',
  databaseType: 'mysql',
  apiUrl: '',
  previewRows: 10,
  
  // 数据预处理配置
  missingValueStrategy: 'mean',
  fillValue: '0',
  outlierStrategy: 'none',
  standardization: 'none',
  
  // 数据集切分配置
  trainRatio: 80,
  randomSeed: 42,
  splitStrategy: 'random',
  
  // 线性回归配置
  regularization: 'none',
  alpha: 0.01,
  l1Ratio: 0.5,
  fitIntercept: true,
  maxIter: 1000,
  solver: 'auto',
  
  // 逻辑回归配置
  C: 1.0,
  multiClass: 'ovr',
  
  // 随机森林配置
  nEstimators: 100,
  maxDepth: 10,
  minSamplesSplit: 2,
  minSamplesLeaf: 1,
  criterion: 'gini',
  maxFeatures: 0.8,
  randomState: 42,
  
  // 评估配置
  metrics: ['accuracy', 'precision', 'recall', 'f1'],
  crossValidation: false,
  kFold: 5,
  generateReport: true,
});

// 默认配置备份
const defaultConfig = { ...nodeConfig };

// 监听选中节点变化
watch(() => props.selectedNode, (newNode) => {
  if (newNode && newNode.config) {
    // 如果节点有配置，则加载配置
    Object.assign(nodeConfig, { ...defaultConfig, ...newNode.config });
  } else {
    // 否则使用默认配置
    Object.assign(nodeConfig, defaultConfig);
  }
}, { immediate: true });

// 应用配置
const applyConfig = () => {
  if (props.selectedNode) {
    emit('updateConfig', {
      nodeId: props.selectedNode.id,
      config: { ...nodeConfig }
    });
  }
};

// 重置配置
const resetConfig = () => {
  Object.assign(nodeConfig, defaultConfig);
};
</script>

<style scoped>
.node-config-panel {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.empty-panel {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.config-form {
  margin-top: 16px;
}

.action-buttons {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style> 