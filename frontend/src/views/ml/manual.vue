<template>
  <div class="manual-container">
    <!-- 顶部提示区域 -->
    <div class="ml-header-notice">
      <a-alert type="success" show-icon banner>
        <template #message>
          <div class="ml-welcome-title">
            机器学习实训专业指南
          </div>
        </template>
        <template #description>
          <div class="ml-welcome-desc">
            本指南涵盖从数据处理到模型部署的全流程知识，为您的机器学习项目提供专业支持。
            您可以在左侧菜单中选择需要学习的章节，或者按照学习路径从上到下依次学习。
          </div>
        </template>
      </a-alert>
    </div>
    
    <div class="action-bar">
      <a-button-group>
        <router-link to="/ml">
          <a-button type="primary">
            <template #icon><experiment-outlined /></template>
            进入实训工作区
          </a-button>
        </router-link>
        <a-button @click="saveNotes">
          <template #icon><save-outlined /></template>
          保存笔记
        </a-button>
        <a-button>
          <template #icon><printer-outlined /></template>
          打印手册
        </a-button>
      </a-button-group>
    </div>
    
    <a-row :gutter="24">
      <a-col :span="6">
        <a-affix :offset-top="80">
          <a-card class="menu-card">
            <a-menu
              mode="inline"
              style="height: 100%"
              :selectedKeys="[selectedKey]"
              @select="handleSelect"
            >
              <a-menu-item key="intro">
                <template #icon><book-outlined /></template>
                介绍
              </a-menu-item>
              
              <a-sub-menu key="dataProcessing">
                <template #icon><database-outlined /></template>
                <template #title>数据处理</template>
                <a-menu-item key="dataSource">数据源</a-menu-item>
                <a-menu-item key="dataPreprocessing">数据预处理</a-menu-item>
                <a-menu-item key="dataSplit">数据集切分</a-menu-item>
              </a-sub-menu>
              
              <a-sub-menu key="featureEng">
                <template #icon><highlight-outlined /></template>
                <template #title>特征工程</template>
                <a-menu-item key="featureSelection">特征选择</a-menu-item>
                <a-menu-item key="featureExtraction">特征提取</a-menu-item>
                <a-menu-item key="dimensionReduction">降维</a-menu-item>
              </a-sub-menu>
              
              <a-sub-menu key="mlModels">
                <template #icon><function-outlined /></template>
                <template #title>机器学习模型</template>
                <a-menu-item key="linearRegression">线性回归</a-menu-item>
                <a-menu-item key="logisticRegression">逻辑回归</a-menu-item>
                <a-menu-item key="decisionTree">决策树</a-menu-item>
                <a-menu-item key="randomForest">随机森林</a-menu-item>
                <a-menu-item key="svm">支持向量机</a-menu-item>
              </a-sub-menu>
              
              <a-sub-menu key="deepLearning">
                <template #icon><cluster-outlined /></template>
                <template #title>深度学习</template>
                <a-menu-item key="dnn">DNN</a-menu-item>
                <a-menu-item key="cnn">CNN</a-menu-item>
                <a-menu-item key="rnn">RNN</a-menu-item>
              </a-sub-menu>
              
              <a-sub-menu key="evaluation">
                <template #icon><bar-chart-outlined /></template>
                <template #title>模型评估</template>
                <a-menu-item key="modelEvaluation">评估指标</a-menu-item>
                <a-menu-item key="modelDeployment">模型部署</a-menu-item>
              </a-sub-menu>
              
              <a-menu-item key="workflow">
                <template #icon><partition-outlined /></template>
                操作流程
              </a-menu-item>
              
              <a-menu-item key="faq">
                <template #icon><question-circle-outlined /></template>
                常见问题
              </a-menu-item>
            </a-menu>
          </a-card>
        </a-affix>
      </a-col>
      
      <a-col :span="18">
        <a-card class="content-card">
          <a-typography>
            <a-typography-title :level="1">{{ getContentTitle }}</a-typography-title>
            <div v-html="formattedContent"></div>
          </a-typography>
          
          <!-- 底部导航区域 -->
          <div class="content-navigation">
            <a-space>
              <a-button 
                v-if="hasPreviousSection" 
                type="default" 
                @click="navigateToPrevious"
              >
                <template #icon><left-outlined /></template>
                上一章节
              </a-button>
              <a-button 
                v-if="hasNextSection" 
                type="primary" 
                @click="navigateToNext"
              >
                下一章节
                <template #icon><right-outlined /></template>
              </a-button>
            </a-space>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { marked } from 'marked';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  BookOutlined, 
  DatabaseOutlined, 
  HighlightOutlined, 
  FunctionOutlined,
  ClusterOutlined,
  BarChartOutlined,
  PartitionOutlined,
  QuestionCircleOutlined,
  LeftOutlined,
  RightOutlined,
  SaveOutlined,
  PrinterOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';

const router = useRouter();
const userStore = useUserStore();

// 选中的菜单项
const selectedKey = ref('intro');

// 处理菜单选择
const handleSelect = (e: { key: string }) => {
  selectedKey.value = e.key;
};

// 保存笔记
const saveNotes = () => {
  // 检查用户登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再保存笔记');
    router.push('/login?redirect=' + encodeURIComponent(router.currentRoute.value.fullPath));
    return;
  }
  
  message.success('笔记已保存');
};

// 所有章节的顺序列表，用于导航
const orderedSections = [
  'intro',
  'dataSource', 'dataPreprocessing', 'dataSplit',
  'featureSelection', 'featureExtraction', 'dimensionReduction',
  'linearRegression', 'logisticRegression', 'decisionTree', 'randomForest', 'svm',
  'dnn', 'cnn', 'rnn',
  'modelEvaluation', 'modelDeployment',
  'workflow',
  'faq'
];

// 是否有上一章节
const hasPreviousSection = computed(() => {
  const currentIndex = orderedSections.indexOf(selectedKey.value);
  return currentIndex > 0;
});

// 是否有下一章节
const hasNextSection = computed(() => {
  const currentIndex = orderedSections.indexOf(selectedKey.value);
  return currentIndex < orderedSections.length - 1 && currentIndex !== -1;
});

// 导航到上一章节
const navigateToPrevious = () => {
  const currentIndex = orderedSections.indexOf(selectedKey.value);
  if (currentIndex > 0) {
    selectedKey.value = orderedSections[currentIndex - 1];
  }
};

// 导航到下一章节
const navigateToNext = () => {
  const currentIndex = orderedSections.indexOf(selectedKey.value);
  if (currentIndex < orderedSections.length - 1) {
    selectedKey.value = orderedSections[currentIndex + 1];
  }
};

// 根据选中的菜单项获取标题
const getContentTitle = computed(() => {
  const titles: Record<string, string> = {
    'intro': '机器学习实训介绍',
    'dataSource': '数据源',
    'dataPreprocessing': '数据预处理',
    'dataSplit': '数据集切分',
    'featureSelection': '特征选择',
    'featureExtraction': '特征提取',
    'dimensionReduction': '降维',
    'linearRegression': '线性回归',
    'logisticRegression': '逻辑回归',
    'decisionTree': '决策树',
    'randomForest': '随机森林',
    'svm': '支持向量机',
    'dnn': '深度神经网络',
    'cnn': '卷积神经网络',
    'rnn': '循环神经网络',
    'modelEvaluation': '模型评估指标',
    'modelDeployment': '模型部署与服务',
    'workflow': '操作流程指南',
    'faq': '常见问题解答'
  };
  
  return titles[selectedKey.value] || '实训手册';
});

// 使用计算属性格式化内容
const formattedContent = computed(() => {
  const content = getContent(selectedKey.value);
  return marked(content);
});

// 获取内容
const getContent = (key: string) => {
  // 这里可以根据key返回不同的内容
  const contents: Record<string, string> = {
    'intro': `
# 欢迎使用机器学习实训平台

本平台采用图形化拖拽方式构建机器学习流程，帮助您轻松完成从数据处理到模型训练的全流程操作。

## 平台特点

- **直观易用**：通过拖拽方式构建模型，无需编写复杂代码
- **全流程支持**：覆盖数据处理、特征工程、模型训练、评估等全流程
- **丰富组件**：提供常用机器学习和深度学习算法
- **实时反馈**：提供模型训练过程的实时反馈和可视化结果

## 开始使用

1. 从左侧组件库中选择并拖拽组件到画布
2. 通过连线将组件连接起来形成完整流程
3. 配置各组件的参数
4. 点击"运行"按钮执行整个流程
5. 查看执行结果和模型评估报告

## 基本操作

- **添加节点**：从左侧拖拽组件到画布
- **连接节点**：点击节点的输出端口，然后连接到目标节点的输入端口
- **配置节点**：点击节点，在右侧面板中设置参数
- **删除节点**：选中节点后按Delete键或右键选择删除
- **调整视图**：使用工具栏中的缩放和重置按钮
`,

    'dataSource': `
# 数据源组件

数据源组件是模型构建的起点，用于加载和提供训练数据。

## 支持的数据来源

- **CSV文件**：支持常见的CSV格式数据文件
- **数据库**：支持从MySQL、PostgreSQL等数据库读取数据
- **API接口**：支持从RESTful API获取数据
- **内置数据集**：平台提供若干经典数据集，如MNIST、Iris等

## 参数配置

- **数据源类型**：选择数据来源类型
- **文件路径/数据库连接/API URL**：根据选择的数据源类型填写相应参数
- **字段映射**：指定数据字段与特征的映射关系
- **数据预览**：查看数据前几条记录

## 使用提示

- 确保数据格式正确，避免缺失值和异常值
- 对于大型数据集，可以设置采样比例减少训练时间
- 检查数据的基本统计信息，了解数据分布情况
`,

    'linearRegression': `
# 线性回归

线性回归是一种基础的监督学习算法，用于预测连续值。

## 算法原理

线性回归通过建立自变量（特征）和因变量（目标）之间的线性关系来进行预测：

\`\`\`
y = β₀ + β₁x₁ + β₂x₂ + ... + βₙxₙ + ε
\`\`\`

其中：
- y 是预测值
- x₁, x₂, ..., xₙ 是特征值
- β₀, β₁, β₂, ..., βₙ 是模型参数
- ε 是误差项

## 参数配置

- **正则化方法**：无、L1正则化（Lasso）、L2正则化（Ridge）或弹性网络
- **正则化强度**：控制正则化的程度（仅在选择正则化时可用）
- **拟合截距**：是否计算截距项
- **最大迭代次数**：优化算法的最大迭代次数
- **求解器**：选择优化算法，如普通最小二乘法、梯度下降等

## 适用场景

- 特征与目标之间存在线性关系
- 预测连续值，如房价、销售额、温度等
- 需要了解各特征对预测结果的影响程度

## 优缺点

**优点**：
- 简单直观，易于实现和理解
- 训练速度快，计算效率高
- 可解释性强，可分析各特征的重要性

**缺点**：
- 只能拟合线性关系，无法捕捉复杂的非线性模式
- 对异常值敏感
- 要求特征之间相互独立

## 评估指标

- 均方误差(MSE)
- 平均绝对误差(MAE)
- R²决定系数
`,

    'workflow': `
# 机器学习实训操作流程指南

本指南提供了使用本平台进行机器学习模型构建的完整流程步骤。

## 1. 数据准备阶段

### 1.1 添加数据源
- 从左侧组件库中拖拽"数据源"组件到画布
- 配置数据源参数，选择数据来源
- 预览数据，检查数据质量

### 1.2 数据预处理
- 添加"数据预处理"组件并连接到数据源
- 设置预处理参数：缺失值处理、异常值处理等
- 添加必要的数据转换步骤

### 1.3 数据集切分
- 添加"数据切分"组件并连接到预处理组件
- 设置训练集和测试集的比例（通常为8:2或7:3）
- 设置随机种子以确保结果可重现

## 2. 特征工程阶段

### 2.1 特征选择
- 视需要添加"特征选择"组件
- 选择合适的特征选择方法
- 配置重要性阈值等参数

### 2.2 特征转换
- 添加"特征提取"组件处理文本、图像等非结构化数据
- 对类别特征进行编码
- 对数值特征进行归一化或标准化

### 2.3 降维（可选）
- 针对高维数据，添加"降维"组件
- 选择合适的降维算法，如PCA、t-SNE等
- 设置目标维度和其他参数

## 3. 模型训练阶段

### 3.1 选择算法
- 根据问题类型（分类/回归）选择合适的算法组件
- 将选择的算法组件连接到特征工程的输出

### 3.2 参数配置
- 配置模型的超参数
- 对于复杂模型，考虑使用网格搜索或随机搜索

## 4. 模型评估阶段

### 4.1 添加评估组件
- 添加"评估指标"组件并连接到模型输出
- 根据问题类型选择合适的评估指标

### 4.2 可视化结果
- 查看评估报告
- 分析混淆矩阵、ROC曲线等可视化结果

## 5. 模型导出与部署

### 5.1 导出模型
- 添加"模型导出"组件
- 选择模型格式（如ONNX、PMML等）
- 设置导出路径

### 5.2 部署（可选）
- 配置部署环境参数
- 设置API接口选项

## 6. 运行与调优

### 6.1 运行流程
- 点击工具栏中的"运行"按钮
- 监控执行进度和日志

### 6.2 优化调整
- 分析评估结果
- 调整模型参数或流程结构
- 重新运行并比较结果

## 最佳实践

- 保持流程简洁清晰
- 定期保存模型配置
- 记录实验结果用于比较
- 先尝试简单模型，再逐步增加复杂度
`,

    'faq': `
# 常见问题解答

## 1. 基本操作问题

### Q: 如何连接两个节点？
A: 点击起始节点的输出端口（通常在节点的右侧），拖动连线到目标节点的输入端口（通常在节点的左侧）。

### Q: 如何删除节点或连线？
A: 选中要删除的节点或连线，然后按键盘上的Delete键，或者右键点击并选择"删除"选项。

### Q: 可以同时对多个节点进行操作吗？
A: 可以。按住Ctrl键（Windows/Linux）或Command键（Mac）并点击多个节点进行多选，然后可以同时移动或删除它们。

### Q: 如何保存我的工作流程？
A: 点击工具栏中的"保存"按钮，输入模型名称和描述，即可保存当前工作流程。

## 2. 数据相关问题

### Q: 支持哪些格式的数据？
A: 平台支持CSV、Excel、JSON、数据库表以及多种结构化和半结构化数据格式。

### Q: 如何处理数据中的缺失值？
A: 在"数据预处理"节点中，可以选择多种缺失值处理策略，包括删除、填充均值/中位数/众数、或使用高级插补算法。

### Q: 数据量过大时平台会变慢吗？
A: 为了保持性能，建议对大型数据集进行采样。您可以在数据源节点设置采样率，或者使用"数据预处理"节点中的采样功能。

## 3. 模型训练问题

### Q: 模型训练需要多长时间？
A: 训练时间取决于数据规模、模型复杂度和计算资源。简单模型通常只需几秒到几分钟，而复杂的深度学习模型可能需要数小时甚至更长时间。

### Q: 如何处理过拟合问题？
A: 可以尝试以下方法：
- 增加训练数据量
- 使用正则化技术
- 减少模型复杂度
- 使用交叉验证
- 进行特征选择

### Q: 模型训练中断后能否继续？
A: 是的，平台支持断点续训。在训练中断后，您可以从上次保存的检查点恢复训练。

## 4. 结果与评估问题

### Q: 如何比较不同模型的性能？
A: 可以创建多个工作流，或在同一工作流中并行添加多个模型，然后使用相同的评估指标进行比较。

### Q: 如何导出训练好的模型？
A: 使用"模型导出"节点，可以将模型导出为ONNX、PMML、Pickle等多种格式。

### Q: 评估结果如何解释？
A: 平台提供详细的评估指标说明和可视化结果，包括混淆矩阵、ROC曲线、特征重要性等，帮助您理解模型性能。

## 5. 系统与技术问题

### Q: 浏览器兼容性如何？
A: 平台支持最新版本的Chrome、Firefox、Safari和Edge浏览器。推荐使用Chrome浏览器获得最佳体验。

### Q: 平台是否支持协作功能？
A: 是的，多用户可以共享和协作处理相同的工作流。平台提供版本控制和变更历史记录。

### Q: 如何获取技术支持？
A: 可以通过平台内的"帮助"菜单提交问题，或发送邮件至support@example.com获取技术支持。
`
  };
  
  return contents[key] || '暂无内容';
};
</script>

<style scoped>
.manual-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.ml-header-notice {
  margin-bottom: 20px;
}

.ml-welcome-title {
  font-size: 16px;
  font-weight: bold;
}

.ml-welcome-desc {
  margin-top: 8px;
}

.action-bar {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.menu-card {
  width: 100%;
  margin-bottom: 20px;
  background-color: #fff;
}

.content-card {
  width: 100%;
  margin-bottom: 20px;
  background-color: #fff;
  min-height: 600px;
}

.content-navigation {
  margin-top: 40px;
  display: flex;
  justify-content: flex-end;
}

:deep(h1) {
  margin-top: 0;
  margin-bottom: 24px;
  font-size: 28px;
}

:deep(h2) {
  margin-top: 32px;
  margin-bottom: 16px;
  font-size: 22px;
}

:deep(h3) {
  margin-top: 24px;
  margin-bottom: 14px;
  font-size: 18px;
}

:deep(p) {
  margin-bottom: 16px;
  line-height: 1.8;
}

:deep(ul),
:deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

:deep(li) {
  margin-bottom: 8px;
  line-height: 1.8;
}

:deep(code) {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
}

:deep(pre) {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  margin-bottom: 16px;
}

:deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;
}

:deep(th),
:deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
}

:deep(th) {
  background-color: #fafafa;
  font-weight: 500;
}
</style> 