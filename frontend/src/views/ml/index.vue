<template>
  <div>
    <div class="ml-intro-section">
      <a-row>
        <a-col :span="16">
          <div class="intro-content">
            <h2>机器学习工作区</h2>
            <p>欢迎使用机器学习实训工作区，您可以通过拖拽组件创建完整的机器学习工作流。从数据处理、特征工程到模型训练和评估，全流程支持可视化操作。</p>
            <div class="action-btns">
              <a-button type="primary" @click="runModel">
                <template #icon><PlayCircleOutlined /></template>
                运行工作流
              </a-button>
              <a-button @click="saveModel">
                <template #icon><SaveOutlined /></template>
                保存工作流
              </a-button>
              <router-link to="/ml/manual">
                <a-button>
                  <template #icon><QuestionCircleOutlined /></template>
                  查看实训手册
                </a-button>
              </router-link>
            </div>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="intro-stats">
            <a-card title="我的工作流" :bordered="false">
              <a-statistic
                title="已保存工作流"
                :value="3"
                style="margin-right: 16px"
              />
              <a-statistic
                title="已完成实训"
                :value="2"
                style="margin-right: 16px"
              />
              <template #extra>
                <a-button type="link" size="small">查看历史</a-button>
              </template>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>
    
    <div class="tool-bar">
      <div class="tool-left">
        <a-button-group>
          <a-button @click="resetView">
            <template #icon><ReloadOutlined /></template>
            重置视图
          </a-button>
          <a-button @click="zoomIn">
            <template #icon><ZoomInOutlined /></template>
            放大
          </a-button>
          <a-button @click="zoomOut">
            <template #icon><ZoomOutOutlined /></template>
            缩小
          </a-button>
          <a-button @click="runModel" type="primary">
            <template #icon><PlayCircleOutlined /></template>
            运行
          </a-button>
        </a-button-group>
      </div>
      <div class="tool-right">
        <a-button @click="saveModel">
          <template #icon><SaveOutlined /></template>
          保存
        </a-button>
        <router-link to="/ml/manual">
          <a-button>
            <template #icon><QuestionCircleOutlined /></template>
            实训手册
          </a-button>
        </router-link>
      </div>
    </div>

    <!-- 拖拽区域 -->
    <div class="ml-container">
      <!-- 左侧算法组件库 -->
      <div class="component-sidebar">
        <h3>算法组件</h3>
        <a-collapse v-model:activeKey="activeCategories" accordion>
          <a-collapse-panel key="dataProcessing" header="数据处理">
            <div class="node-list">
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'dataSource')">
                <database-outlined />
                <span>数据源</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'dataPreprocessing')">
                <filter-outlined />
                <span>数据预处理</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'dataSplit')">
                <scissor-outlined />
                <span>数据切分</span>
              </div>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="featureEng" header="特征工程">
            <div class="node-list">
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'featureSelection')">
                <highlight-outlined />
                <span>特征选择</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'featureExtraction')">
                <build-outlined />
                <span>特征提取</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'dimensionReduction')">
                <node-index-outlined />
                <span>降维</span>
              </div>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="mlModels" header="机器学习模型">
            <div class="node-list">
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'linearRegression')">
                <line-chart-outlined />
                <span>线性回归</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'logisticRegression')">
                <function-outlined />
                <span>逻辑回归</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'decisionTree')">
                <apartment-outlined />
                <span>决策树</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'randomForest')">
                <cluster-outlined />
                <span>随机森林</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'svm')">
                <radar-chart-outlined />
                <span>支持向量机</span>
              </div>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="deepLearning" header="深度学习">
            <div class="node-list">
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'dnn')">
                <deployment-unit-outlined />
                <span>DNN</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'cnn')">
                <fund-projection-screen-outlined />
                <span>CNN</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'rnn')">
                <partition-outlined />
                <span>RNN</span>
              </div>
            </div>
          </a-collapse-panel>
          
          <a-collapse-panel key="evaluation" header="模型评估">
            <div class="node-list">
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'evaluation')">
                <bar-chart-outlined />
                <span>评估指标</span>
              </div>
              <div class="node-item" draggable="true" @dragstart="dragStart($event, 'modelExport')">
                <export-outlined />
                <span>模型导出</span>
              </div>
            </div>
          </a-collapse-panel>
        </a-collapse>
      </div>
      
      <!-- 中间DAG编辑区 -->
      <div class="dag-container">
        <DAGBoard 
          :DataAll="dagData" 
          @updateDAG="updateDAG"
          @editNodeDetails="editNodeDetails"
        />
        <node-bus 
          v-if="nodeBusDragging" 
          :value="nodeName"
          :pos_x="nodeBusPositionX"
          :pos_y="nodeBusPositionY"
        />
      </div>
      
      <!-- 右侧属性配置 -->
      <div class="config-panel">
        <div v-if="selectedNode" class="node-config">
          <h3>{{ getNodeTitle(selectedNode?.name || '') }}配置</h3>
          <a-divider />
          
          <div class="config-form">
            <a-form layout="vertical">
              <a-form-item label="节点名称">
                <a-input v-model:value="selectedNode.customName" />
              </a-form-item>
              
              <component 
                :is="getConfigComponent(selectedNode?.name || '')" 
                :node="selectedNode"
                @update:config="updateNodeConfig"
              />
              
              <a-form-item>
                <a-button type="primary" @click="applyConfig">应用配置</a-button>
              </a-form-item>
            </a-form>
          </div>
        </div>
        <a-empty v-else description="请选择一个节点进行配置" />
      </div>
    </div>

    <!-- 模型保存对话框 -->
    <a-modal
      v-model:open="saveModalVisible"
      title="保存模型"
      @ok="handleSaveOk"
      :okButtonProps="{ props: { type: 'primary' } }"
    >
      <a-form :model="saveForm" layout="vertical">
        <a-form-item label="模型名称" name="name" :rules="[{ required: true, message: '请输入模型名称' }]">
          <a-input v-model:value="saveForm.name" placeholder="请输入模型名称" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="saveForm.description" placeholder="请输入模型描述信息" :rows="4" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
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
  ReloadOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  PlayCircleOutlined,
  SaveOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';
import { fetchDagGraph, type DagGraph } from '../../api/ml';
import NodeBus from '../../components/ml/NodeBus.vue';
import DAGBoard from '../../components/ml/DAGBoard.vue';
import { useUserStore } from '../../stores/user';

const router = useRouter();
const userStore = useUserStore();

// 激活的组件类别
const activeCategories = ref<string[]>(['dataProcessing']);

// DAG数据
const dagData = reactive<DagGraph>({
  nodes: [],
  edges: [],
  GlobalConfig: {
    isVertical: false
  }
});

// 选中的节点
const selectedNode = ref<any>(null);

// 节点拖拽状态
const nodeBusDragging = ref(false);
const nodeName = ref('');
const nodeBusPositionX = ref(0);
const nodeBusPositionY = ref(0);

// 保存对话框
const saveModalVisible = ref(false);
const saveForm = reactive({
  name: '',
  description: ''
});

// 处理拖拽开始
const dragStart = (event: DragEvent, type: string) => {
  nodeBusDragging.value = true;
  nodeName.value = type;
  
  // 监听鼠标移动
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
  
  // 阻止浏览器默认拖拽行为
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
  }
};

// 鼠标移动
const onMouseMove = (event: MouseEvent) => {
  nodeBusPositionX.value = event.clientX;
  nodeBusPositionY.value = event.clientY;
};

// 鼠标释放
const onMouseUp = () => {
  nodeBusDragging.value = false;
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);
};

// 更新DAG
const updateDAG = (data: any, action: string) => {
  console.log('DAG更新:', action, data);
  
  if (action === 'add-node') {
    message.success('添加节点成功');
  } else if (action === 'delete-node') {
    message.success('删除节点成功');
    if (selectedNode.value && selectedNode.value.id === data.nodeId) {
      selectedNode.value = null;
    }
  } else if (action === 'add-edge') {
    message.success('添加连接成功');
  } else if (action === 'delete-edge') {
    message.success('删除连接成功');
  }
};

// 编辑节点详情
const editNodeDetails = (nodeData: any) => {
  selectedNode.value = nodeData;
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

// 获取配置组件
const getConfigComponent = (type: string) => {
  // 这里可以根据节点类型返回不同的配置组件
  // 简化处理，此处未实现
  return null;
};

// 更新节点配置
const updateNodeConfig = (config: any) => {
  if (selectedNode.value) {
    selectedNode.value.config = { ...selectedNode.value.config, ...config };
  }
};

// 应用配置
const applyConfig = () => {
  if (selectedNode.value) {
    // 更新节点数据
    const index = dagData.nodes.findIndex((node: any) => node.id === selectedNode.value.id);
    if (index !== -1) {
      dagData.nodes[index] = { ...selectedNode.value };
      message.success('配置已应用');
    }
  }
};

const loadDagData = async () => {
  const projectId = router.currentRoute.value.query.projectId as string | undefined
  if (!projectId) {
    return
  }
  try {
    const data = await fetchDagGraph(projectId)
    dagData.nodes = data.nodes || []
    dagData.edges = data.edges || []
    dagData.GlobalConfig = data.GlobalConfig || { isVertical: false }
  } catch (error) {
    console.error('加载DAG数据失败:', error)
    message.error('加载工作流数据失败，请稍后重试')
  }
}

// 重置视图
const resetView = () => {
  // 简化处理，实际实现可能更复杂
  message.info('视图已重置');
};

// 放大
const zoomIn = () => {
  message.info('视图已放大');
};

// 缩小
const zoomOut = () => {
  message.info('视图已缩小');
};

// 运行模型
const runModel = () => {
  // 检查用户登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再运行模型');
    router.push('/login?redirect=' + encodeURIComponent(router.currentRoute.value.fullPath));
    return;
  }
  
  message.loading('模型运行中...', 2.5)
    .then(() => message.success('模型运行成功'));
};

// 保存模型
const saveModel = () => {
  // 检查用户登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再保存模型');
    router.push('/login?redirect=' + encodeURIComponent(router.currentRoute.value.fullPath));
    return;
  }
  
  saveModalVisible.value = true;
};

// 确认保存
const handleSaveOk = () => {
  if (!saveForm.name) {
    message.warning('请输入模型名称');
    return;
  }
  
  message.success(`模型 "${saveForm.name}" 保存成功`);
  saveModalVisible.value = false;
  
  // 重置表单
  saveForm.name = '';
  saveForm.description = '';
};

// 检查登录状态
const checkLoginStatus = () => {
  if (userStore.isLoggedIn) {
    // 已登录，可以使用高级功能
    console.log('用户已登录:', userStore.userInfo.username);
  } else {
    console.log('用户未登录');
    // 权限受限的功能在调用时检查权限
  }
};

// 生命周期钩子
onMounted(() => {
  // 初始化操作
  checkLoginStatus();
  loadDagData();
});
</script>

<style scoped>
.ml-intro-section {
  background-color: #fff;
  border-radius: 4px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.intro-content {
  padding-right: 20px;
}

.intro-content h2 {
  font-size: 24px;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
}

.intro-content p {
  font-size: 14px;
  line-height: 1.6;
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 20px;
}

.action-btns {
  display: flex;
  gap: 12px;
}

.intro-stats {
  height: 100%;
}

.tool-bar {
  height: 48px;
  background-color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.tool-left,
.tool-right {
  display: flex;
  gap: 8px;
}

.ml-container {
  display: flex;
  overflow: hidden;
  height: calc(100vh - 240px);
  margin-bottom: 20px;
}

.component-sidebar {
  width: 240px;
  background-color: #fff;
  border-right: 1px solid #f0f0f0;
  overflow-y: auto;
  padding: 16px;
}

.component-sidebar h3 {
  margin-bottom: 16px;
  font-size: 16px;
}

.node-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.node-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
}

.node-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

.node-item :deep(.anticon) {
  font-size: 24px;
  margin-bottom: 4px;
}

.node-item span {
  font-size: 12px;
  text-align: center;
}

.dag-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background-color: #f0f2f5;
}

.config-panel {
  width: 300px;
  background-color: #fff;
  border-left: 1px solid #f0f0f0;
  overflow-y: auto;
  padding: 16px;
}

.node-config h3 {
  font-size: 16px;
  margin-bottom: 16px;
}

.config-form {
  margin-top: 16px;
}
</style> 