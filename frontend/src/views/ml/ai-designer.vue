<template>
  <div class="ai-designer-page">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <!-- 模式切换Tab -->
        <div class="mode-tabs">
          <div
            class="mode-tab"
            :class="{ active: designMode === 'modeling' }"
            @click="designMode = 'modeling'"
          >
            建模
          </div>
          <div
            class="mode-tab"
            :class="{ active: designMode === 'insight' }"
            @click="designMode = 'insight'"
          >
            洞察
          </div>
        </div>
      </div>

      <div class="header-center">
        <div class="flow-name">
          <ThunderboltOutlined style="color: #1890ff;" />
          <span>{{ currentFlow?.name || '流程1' }}</span>
        </div>
        <a-space class="toolbar-actions">
          <a-tooltip title="保存">
            <a-button type="text" @click="handleSave" :loading="saving">
              <SaveOutlined />
            </a-button>
          </a-tooltip>
          <a-divider type="vertical" />
          <a-tooltip title="运行">
            <a-button type="text" @click="handleRun" :loading="running" style="color: #52c41a;">
              <CaretRightOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="单步运行">
            <a-button
              type="text"
              @click="handleSingleStep"
              :disabled="running || nodes.length === 0"
              :style="{ color: isSingleStepActive ? '#52c41a' : undefined }"
            >
              <StepForwardOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="停止">
            <a-button type="text" @click="handleStop" :disabled="!running && !isSingleStepActive">
              <BorderOutlined />
            </a-button>
          </a-tooltip>
          <a-divider type="vertical" />
          <a-tooltip title="撤销">
            <a-button type="text" @click="undo" :disabled="!canUndo">
              <UndoOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="重做">
            <a-button type="text" @click="redo" :disabled="!canRedo">
              <RedoOutlined />
            </a-button>
          </a-tooltip>
          <a-divider type="vertical" />
          <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
          <a-divider type="vertical" />
          <a-tooltip title="设置">
            <a-button type="text">
              <SettingOutlined />
            </a-button>
          </a-tooltip>
        </a-space>
      </div>

      <div class="header-right">
        <a-avatar :src="userStore.userInfo.avatar" size="small" />
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="designer-body">
      <!-- 左侧算子库 -->
      <div class="operator-panel">
        <!-- 算子库/模型库切换 -->
        <div class="panel-tabs">
          <div
            class="panel-tab"
            :class="{ active: leftPanelTab === 'operators' }"
            @click="leftPanelTab = 'operators'"
          >
            算子库
          </div>
          <div
            class="panel-tab"
            :class="{ active: leftPanelTab === 'models' }"
            @click="leftPanelTab = 'models'"
          >
            模型库
          </div>
        </div>

        <!-- 算子库内容 -->
        <div v-if="leftPanelTab === 'operators'" class="panel-content">
          <div class="category-filter">
            <a-select v-model:value="categoryFilter" style="width: 100%" size="small">
              <a-select-option value="all">全部</a-select-option>
              <a-select-option value="common">常用</a-select-option>
            </a-select>
          </div>
          <div class="search-box">
            <a-input-search
              v-model:value="searchKeyword"
              placeholder="搜索节点名称"
              size="small"
            />
          </div>
          <div class="operator-tree">
            <a-tree
              v-model:expandedKeys="expandedCategories"
              :tree-data="operatorTreeData"
              :selectable="false"
              block-node
            >
              <template #title="{ title, key, isLeaf, icon, type }">
                <div v-if="!isLeaf" class="tree-category">
                  <component :is="icon" v-if="icon" style="margin-right: 6px;" />
                  <span>{{ title }}</span>
                </div>
                <div
                  v-else
                  class="tree-operator"
                  draggable="true"
                  @dragstart="handleDragStart($event, { type, name: title, icon })"
                >
                  <component :is="icon" v-if="icon" class="op-icon" />
                  <span>{{ title }}</span>
                </div>
              </template>
            </a-tree>
          </div>
        </div>

        <!-- 模型库内容 -->
        <div v-if="leftPanelTab === 'models'" class="panel-content">
          <!-- 模型库工具栏 -->
          <div class="model-toolbar">
            <a-button type="primary" size="small" @click="modelLibraryState.showSaveModal = true">
              <template #icon><PlusOutlined /></template>
              保存为模型
            </a-button>
          </div>

          <!-- 搜索框 -->
          <div class="model-search">
            <a-input-search
              v-model:value="modelLibraryState.searchKeyword"
              placeholder="搜索模型名称"
              size="small"
              @search="fetchModelList"
              allow-clear
            />
          </div>

          <!-- 类型筛选 -->
          <div class="model-filter">
            <a-select
              v-model:value="modelLibraryState.filterType"
              placeholder="模型类型"
              size="small"
              style="width: 100%"
              allow-clear
              @change="fetchModelList"
            >
              <a-select-option value="regression">回归</a-select-option>
              <a-select-option value="classification">分类</a-select-option>
              <a-select-option value="clustering">聚类</a-select-option>
              <a-select-option value="recommendation">推荐</a-select-option>
            </a-select>
          </div>

          <!-- 模型列表 -->
          <div class="model-list">
            <a-spin :spinning="modelLibraryState.loading">
              <a-empty v-if="modelLibraryState.models.length === 0" description="暂无已保存模型" />
              <a-list
                v-else
                :data-source="filteredModelList"
                size="small"
                :split="false"
              >
                <template #renderItem="{ item }">
                  <a-list-item class="model-item" @click="loadModelToCanvas(item)">
                    <div class="model-item-content">
                      <div class="model-name">{{ item.name }}</div>
                      <div class="model-meta">
                        <a-tag size="small">{{ item.type }}</a-tag>
                        <a-tag size="small" color="blue">{{ item.algorithm }}</a-tag>
                      </div>
                      <div class="model-desc">{{ item.description }}</div>
                      <div class="model-time">{{ formatDate(item.created_at) }}</div>
                    </div>
                  </a-list-item>
                </template>
              </a-list>
            </a-spin>
          </div>
        </div>

        <!-- 保存模型模态框 -->
        <a-modal
          v-model:open="modelLibraryState.showSaveModal"
          title="保存为模型"
          :confirm-loading="modelLibraryState.saving"
          @ok="handleSaveModel"
          @cancel="modelLibraryState.showSaveModal = false"
          ok-text="保存"
          cancel-text="取消"
        >
          <a-form :model="modelLibraryState.saveForm" layout="vertical">
            <a-form-item label="模型名称" required>
              <a-input
                v-model:value="modelLibraryState.saveForm.name"
                placeholder="请输入模型名称"
                :maxlength="50"
                show-count
              />
            </a-form-item>
            <a-form-item label="模型类型" required>
              <a-radio-group v-model:value="modelLibraryState.saveForm.type">
                <a-radio value="regression">回归</a-radio>
                <a-radio value="classification">分类</a-radio>
                <a-radio value="clustering">聚类</a-radio>
                <a-radio value="recommendation">推荐</a-radio>
                <a-radio value="other">其他</a-radio>
              </a-radio-group>
            </a-form-item>
            <a-form-item label="算法" required>
              <a-select
                v-model:value="modelLibraryState.saveForm.algorithm"
                placeholder="请选择算法"
              >
                <a-select-opt-group label="回归">
                  <a-select-option value="linear">线性回归</a-select-option>
                  <a-select-option value="ridge">岭回归</a-select-option>
                  <a-select-option value="lasso">Lasso回归</a-select-option>
                  <a-select-option value="tree">决策树回归</a-select-option>
                  <a-select-option value="forest">随机森林回归</a-select-option>
                  <a-select-option value="gbdt">GBDT回归</a-select-option>
                </a-select-opt-group>
                <a-select-opt-group label="分类">
                  <a-select-option value="logistic">逻辑回归</a-select-option>
                  <a-select-option value="decision_tree">决策树</a-select-option>
                  <a-select-option value="random_forest">随机森林</a-select-option>
                  <a-select-option value="svm">SVM</a-select-option>
                  <a-select-option value="naive_bayes">朴素贝叶斯</a-select-option>
                  <a-select-option value="knn">KNN</a-select-option>
                </a-select-opt-group>
                <a-select-opt-group label="聚类">
                  <a-select-option value="kmeans">K-Means</a-select-option>
                  <a-select-option value="dbscan">DBSCAN</a-select-option>
                  <a-select-option value="hierarchical">层次聚类</a-select-option>
                </a-select-opt-group>
                <a-select-opt-group label="推荐">
                  <a-select-option value="cf">协同过滤</a-select-option>
                  <a-select-option value="content_based">内容推荐</a-select-option>
                </a-select-opt-group>
              </a-select>
            </a-form-item>
            <a-form-item label="模型描述">
              <a-textarea
                v-model:value="modelLibraryState.saveForm.description"
                placeholder="请输入模型描述（可选）"
                :rows="3"
                :maxlength="200"
                show-count
              />
            </a-form-item>
          </a-form>
        </a-modal>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-container">
        <!-- 画布 -->
        <div
          ref="canvasRef"
          class="flow-canvas"
          @drop="handleDrop"
          @dragover.prevent
          @click="handleCanvasClick"
          @keydown="handleKeyDown"
          tabindex="0"
        >
          <!-- 空状态提示 -->
          <div v-if="nodes.length === 0" class="empty-canvas">
            <div class="empty-content">
              <DatabaseOutlined class="empty-icon" />
              <h3>开始构建AI工作流</h3>
              <p>从左侧算子库拖拽组件到此处，连接它们构建数据处理流程</p>
              <div class="empty-steps">
                <div class="step">
                  <span class="step-number">1</span>
                  <span>拖拽数据源算子</span>
                </div>
                <div class="step">
                  <span class="step-number">2</span>
                  <span>添加处理算子并连接</span>
                </div>
                <div class="step">
                  <span class="step-number">3</span>
                  <span>点击运行查看结果</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 运行状态指示器 -->
          <div v-if="running" class="running-indicator">
            <div class="running-content">
              <LoadingOutlined spin />
              <span>工作流运行中...</span>
              <div class="running-stats">
                <span>运行中: {{ runningNodes.length }}</span>
                <span>已完成: {{ completedNodes.length }}</span>
                <span>错误: {{ errorNodes.length }}</span>
              </div>
            </div>
          </div>

          <!-- 快捷键提示面板 -->
          <div v-if="showKeyboardHints" class="keyboard-hints-panel">
            <div class="hints-header">
              <h4>键盘快捷键</h4>
              <a-button type="text" size="small" @click="showKeyboardHints = false">
                <template #icon>
                  <CloseOutlined />
                </template>
              </a-button>
            </div>
            <div class="hints-content">
              <div class="hint-item">
                <kbd>Ctrl+S</kbd> <span>保存工作流</span>
              </div>
              <div class="hint-item">
                <kbd>Ctrl+R</kbd> <span>运行工作流</span>
              </div>
              <div class="hint-item">
                <kbd>Delete</kbd> <span>删除选中项</span>
              </div>
              <div class="hint-item">
                <kbd>F1</kbd> <span>显示/隐藏此面板</span>
              </div>
            </div>
          </div>
          <svg
            class="flow-svg"
            :viewBox="`0 0 ${canvasSize.width} ${canvasSize.height}`"
            :style="{ transform: `scale(${zoomLevel})` }"
          >
            <!-- 连线层 -->
            <g class="edges-layer">
              <path
                v-for="edge in edges"
                :key="edge.id"
                :d="getEdgePath(edge)"
                class="flow-edge"
                :class="{ 'selected': selectedEdge?.id === edge.id }"
                @click.stop="selectEdge(edge)"
              />
            </g>
          </svg>
          
          <!-- 节点层 -->
          <div class="nodes-layer" :style="{ transform: `scale(${zoomLevel})` }">
            <div
              v-for="node in nodes"
              :key="node.id"
              :id="`node-${node.id}`"
              :data-node-id="node.id"
              class="flow-node"
              :class="{ 
                'selected': selectedNode?.id === node.id,
                'running': runningNodes.includes(node.id),
                'completed': completedNodes.includes(node.id),
                'error': errorNodes.includes(node.id)
              }"
              :style="{
                left: node.position.x + 'px',
                top: node.position.y + 'px'
              }"
              @click.stop="selectNode(node)"
              @mousedown.stop="selectNode(node); startDragNode($event, node)"
            >
              <div class="node-header">
                <component :is="getNodeIcon(node.type)" class="node-icon" />
                <span class="node-title">{{ node.label }}</span>
              </div>
              <div class="node-ports">
                <div 
                  class="port port-input"
                  v-if="hasInputPort(node.type)"
                  @mousedown.stop="startConnection($event, node, 'input')"
                ></div>
                <div 
                  class="port port-output"
                  v-if="hasOutputPort(node.type)"
                  @mousedown.stop="startConnection($event, node, 'output')"
                ></div>
              </div>
              <div class="node-status" v-if="node.status">
                <LoadingOutlined v-if="node.status === 'running'" spin />
                <CheckCircleOutlined v-if="node.status === 'completed'" style="color: #52c41a;" />
                <CloseCircleOutlined v-if="node.status === 'error'" style="color: #ff4d4f;" />
              </div>
            </div>
          </div>

          <!-- 临时连线 -->
          <svg
            v-if="isConnecting"
            class="temp-connection"
            :style="{ pointerEvents: 'none' }"
          >
            <path
              :d="tempConnectionPath"
              stroke="#1890ff"
              stroke-width="2"
              fill="none"
              stroke-dasharray="5,5"
            />
          </svg>
        </div>

        <!-- 底部流程标签页 -->
        <div class="flow-tabs">
          <div class="flow-tabs-left">
            <a-button type="text" size="small" @click="scrollFlowTabs('left')">
              <LeftOutlined />
            </a-button>
            <a-button type="text" size="small" @click="scrollFlowTabs('right')">
              <RightOutlined />
            </a-button>
          </div>
          <div class="flow-tab-list" ref="flowTabListRef">
            <div
              v-for="flow in flows"
              :key="flow.id"
              class="flow-tab"
              :class="{ active: currentFlowId === flow.id }"
              @click="switchFlow(flow.id)"
            >
              <FileOutlined />
              <span>{{ flow.name }}</span>
              <CloseOutlined class="close-btn" @click.stop="removeFlow(flow.id)" />
            </div>
          </div>
          <a-button type="text" size="small" @click="addFlow">
            <PlusOutlined />
          </a-button>
        </div>

        <!-- 底部日志面板 -->
        <div class="log-panel" :class="{ 'expanded': showLogs }">
          <div class="log-header">
            <span @click="showLogs = !showLogs" class="log-toggle">
              <UpOutlined v-if="showLogs" />
              <DownOutlined v-else />
              日志
            </span>
            <a-dropdown>
              <a-button type="text" size="small">
                <DownloadOutlined /> 日志 <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu>
                  <a-menu-item key="export">导出日志</a-menu-item>
                  <a-menu-item key="clear">清空日志</a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </div>
          <div class="log-content" v-show="showLogs">
            <div class="log-tabs">
              <a-tabs v-model:activeKey="activeLogTab">
                <a-tab-pane key="output" tab="输出">
                  <div class="log-list">
                    <div v-for="(log, index) in outputLogs" :key="index" class="log-item">
                      <span class="log-time">{{ log.time }}</span>
                      <span class="log-level" :class="`level-${log.level}`">{{ log.level }}</span>
                      <span class="log-message">{{ log.message }}</span>
                    </div>
                  </div>
                </a-tab-pane>
                <a-tab-pane key="insight" tab="洞察">
                  <div class="insight-content" v-if="insightData">
                    <!-- 统计概览 -->
                    <div class="insight-overview">
                      <a-row :gutter="16">
                        <a-col :span="6">
                          <a-card size="small" class="insight-card">
                            <a-statistic
                              title="总节点数"
                              :value="insightData.total_nodes"
                              :value-style="{ color: '#1890ff' }"
                            />
                          </a-card>
                        </a-col>
                        <a-col :span="6">
                          <a-card size="small" class="insight-card">
                            <a-statistic
                              title="已执行"
                              :value="insightData.executed_nodes"
                              :value-style="{ color: '#52c41a' }"
                            />
                          </a-card>
                        </a-col>
                        <a-col :span="6">
                          <a-card size="small" class="insight-card">
                            <a-statistic
                              title="失败"
                              :value="insightData.failed_nodes"
                              :value-style="{ color: insightData.failed_nodes > 0 ? '#ff4d4f' : '#52c41a' }"
                            />
                          </a-card>
                        </a-col>
                        <a-col :span="6">
                          <a-card size="small" class="insight-card">
                            <a-statistic
                              title="执行时间"
                              :value="insightData.execution_time"
                              suffix="秒"
                              :value-style="{ color: '#faad14' }"
                            />
                          </a-card>
                        </a-col>
                      </a-row>
                    </div>

                    <!-- 模型指标 -->
                    <div class="insight-metrics" v-if="insightData.model_insights">
                      <h4>模型性能指标</h4>
                      <a-row :gutter="16">
                        <a-col :span="8" v-if="insightData.model_insights.accuracy !== undefined">
                          <div class="metric-item">
                            <span class="metric-label">准确率</span>
                            <a-progress
                              :percent="insightData.model_insights.accuracy * 100"
                              size="small"
                              :stroke-color="getMetricColor(insightData.model_insights.accuracy)"
                            />
                          </div>
                        </a-col>
                        <a-col :span="8" v-if="insightData.model_insights.precision !== undefined">
                          <div class="metric-item">
                            <span class="metric-label">精确率</span>
                            <a-progress
                              :percent="insightData.model_insights.precision * 100"
                              size="small"
                              :stroke-color="getMetricColor(insightData.model_insights.precision)"
                            />
                          </div>
                        </a-col>
                        <a-col :span="8" v-if="insightData.model_insights.recall !== undefined">
                          <div class="metric-item">
                            <span class="metric-label">召回率</span>
                            <a-progress
                              :percent="insightData.model_insights.recall * 100"
                              size="small"
                              :stroke-color="getMetricColor(insightData.model_insights.recall)"
                            />
                          </div>
                        </a-col>
                        <a-col :span="8" v-if="insightData.model_insights.f1_score !== undefined">
                          <div class="metric-item">
                            <span class="metric-label">F1分数</span>
                            <a-progress
                              :percent="insightData.model_insights.f1_score * 100"
                              size="small"
                              :stroke-color="getMetricColor(insightData.model_insights.f1_score)"
                            />
                          </div>
                        </a-col>
                        <a-col :span="8" v-if="insightData.model_insights.auc !== undefined">
                          <div class="metric-item">
                            <span class="metric-label">AUC</span>
                            <a-progress
                              :percent="insightData.model_insights.auc * 100"
                              size="small"
                              :stroke-color="getMetricColor(insightData.model_insights.auc)"
                            />
                          </div>
                        </a-col>
                      </a-row>
                      <div class="sample-info">
                        <span>训练样本: {{ insightData.model_insights.training_samples }}</span>
                        <span>验证样本: {{ insightData.model_insights.validation_samples }}</span>
                        <span>测试样本: {{ insightData.model_insights.test_samples }}</span>
                      </div>
                    </div>

                    <!-- 节点执行详情 -->
                    <div class="insight-nodes" v-if="insightData.node_insights && insightData.node_insights.length > 0">
                      <h4>节点执行详情</h4>
                      <a-table
                        :data-source="insightData.node_insights"
                        size="small"
                        :pagination="false"
                        :columns="nodeInsightColumns"
                      >
                        <template #bodyCell="{ column, record }">
                          <template v-if="column.key === 'status'">
                            <a-tag :color="getStatusColor(record.status)">
                              {{ getStatusText(record.status) }}
                            </a-tag>
                          </template>
                          <template v-if="column.key === 'execution_time'">
                            {{ record.execution_time?.toFixed(2) || 0 }}s
                          </template>
                          <template v-if="column.key === 'memory_usage'">
                            {{ formatMemory(record.memory_usage) }}
                          </template>
                        </template>
                      </a-table>
                    </div>

                    <!-- 优化建议 -->
                    <div class="insight-suggestions" v-if="suggestions.length > 0">
                      <h4>优化建议</h4>
                      <a-list size="small" :data-source="suggestions">
                        <template #renderItem="{ item }">
                          <a-list-item>
                            <template #prefix>
                              <BulbOutlined style="color: #faad14;" />
                            </template>
                            {{ item }}
                          </a-list-item>
                        </template>
                      </a-list>
                    </div>
                  </div>
                  <a-empty v-else description="暂无洞察数据" />
                </a-tab-pane>
              </a-tabs>
            </div>
          </div>
          </div>
        </div>

      <!-- 右侧配置面板 -->
      <div class="config-panel" v-show="selectedNode">
        <div class="panel-header">
          <h3>节点配置</h3>
          <a-button type="text" size="small" @click="selectedNode = null">
            <template #icon><CloseOutlined /></template>
          </a-button>
        </div>
        <div class="config-content" v-if="selectedNode">
          <a-form layout="vertical" size="small">
            <a-form-item label="节点名称">
              <a-input v-model:value="selectedNode.label" />
            </a-form-item>

            <a-divider>参数配置</a-divider>

            <!-- 读取数据节点配置 -->
            <template v-if="selectedNode.type === 'readData'">
              <a-form-item label="数据集">
                <a-select v-model:value="selectedNode.config.dataset" placeholder="选择数据集">
                  <a-select-option
                    v-for="dataset in datasetOptions"
                    :key="dataset.value"
                    :value="dataset.value"
                  >
                    {{ dataset.label }}
                  </a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="文件路径">
                <a-input v-model:value="selectedNode.config.filePath" placeholder="例如: data/sample.csv" />
              </a-form-item>
            </template>

            <!-- 写入数据节点配置 -->
            <template v-if="selectedNode.type === 'writeData'">
              <a-form-item label="输出路径">
                <a-input v-model:value="selectedNode.config.filePath" placeholder="例如: results/output.csv" />
              </a-form-item>
              <a-form-item label="输出格式">
                <a-select v-model:value="selectedNode.config.format" placeholder="选择格式">
                  <a-select-option value="csv">CSV</a-select-option>
                  <a-select-option value="json">JSON</a-select-option>
                  <a-select-option value="xlsx">Excel</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 数据拆分节点配置 -->
            <template v-if="selectedNode.type === 'dataSplit'">
              <a-form-item label="测试集比例">
                <a-slider v-model:value="selectedNode.config.testSize" :min="0.1" :max="0.9" :step="0.05" :marks="{ 0.2: '20%', 0.5: '50%', 0.8: '80%' }" />
              </a-form-item>
              <a-form-item label="随机种子">
                <a-input-number v-model:value="selectedNode.config.randomState" :min="0" style="width: 100%;" placeholder="可选，设为固定值可复现结果" />
              </a-form-item>
              <a-form-item label="分层抽样">
                <a-switch v-model:value="selectedNode.config.stratify" />
              </a-form-item>
            </template>

            <!-- 数据过滤节点配置 -->
            <template v-if="selectedNode.type === 'dataFilter'">
              <a-form-item label="过滤字段">
                <a-input v-model:value="selectedNode.config.column" placeholder="例如: age" />
              </a-form-item>
              <a-form-item label="操作符">
                <a-select v-model:value="selectedNode.config.operator" placeholder="选择操作符">
                  <a-select-option value="==">等于</a-select-option>
                  <a-select-option value="!=">不等于</a-select-option>
                  <a-select-option value=">">大于</a-select-option>
                  <a-select-option value="<">小于</a-select-option>
                  <a-select-option value=">=">大于等于</a-select-option>
                  <a-select-option value="<=">小于等于</a-select-option>
                  <a-select-option value="contains">包含</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="过滤值">
                <a-input v-model:value="selectedNode.config.value" placeholder="输入过滤值" />
              </a-form-item>
            </template>

            <!-- 数据合并节点配置 -->
            <template v-if="selectedNode.type === 'dataMerge'">
              <a-form-item label="合并方式">
                <a-select v-model:value="selectedNode.config.mergeType" placeholder="选择合并方式">
                  <a-select-option value="inner">内连接</a-select-option>
                  <a-select-option value="left">左连接</a-select-option>
                  <a-select-option value="right">右连接</a-select-option>
                  <a-select-option value="outer">外连接</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="合并键">
                <a-input v-model:value="selectedNode.config.on" placeholder="例如: id" />
              </a-form-item>
            </template>

            <!-- 表连接节点配置 -->
            <template v-if="selectedNode.type === 'tableJoin'">
              <a-form-item label="左表连接键">
                <a-input v-model:value="selectedNode.config.leftOn" placeholder="左表连接字段" />
              </a-form-item>
              <a-form-item label="右表连接键">
                <a-input v-model:value="selectedNode.config.rightOn" placeholder="右表连接字段" />
              </a-form-item>
              <a-form-item label="连接方式">
                <a-select v-model:value="selectedNode.config.how" placeholder="选择连接方式">
                  <a-select-option value="inner">内连接</a-select-option>
                  <a-select-option value="left">左连接</a-select-option>
                  <a-select-option value="right">右连接</a-select-option>
                  <a-select-option value="outer">外连接</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 特征选择节点配置 -->
            <template v-if="selectedNode.type === 'featureSelect'">
              <a-form-item label="选择方法">
                <a-select v-model:value="selectedNode.config.method" placeholder="选择方法">
                  <a-select-option value="variance">方差过滤</a-select-option>
                  <a-select-option value="correlation">相关性过滤</a-select-option>
                  <a-select-option value="rfe">递归特征消除</a-select-option>
                  <a-select-option value="selectkbest">SelectKBest</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="特征数量">
                <a-input-number v-model:value="selectedNode.config.nFeatures" :min="1" style="width: 100%;" />
              </a-form-item>
            </template>

            <!-- PCA降维节点配置 -->
            <template v-if="selectedNode.type === 'pca'">
              <a-form-item label="主成分数量">
                <a-input-number v-model:value="selectedNode.config.nComponents" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="是否白化">
                <a-switch v-model:value="selectedNode.config.whiten" />
              </a-form-item>
            </template>

            <!-- 标准化节点配置 -->
            <template v-if="selectedNode.type === 'standardize'">
              <a-form-item label="中心化">
                <a-switch v-model:value="selectedNode.config.withMean" />
              </a-form-item>
              <a-form-item label="缩放">
                <a-switch v-model:value="selectedNode.config.withStd" />
              </a-form-item>
            </template>

            <!-- 归一化节点配置 -->
            <template v-if="selectedNode.type === 'normalize'">
              <a-form-item label="归一化方式">
                <a-select v-model:value="selectedNode.config.norm" placeholder="选择归一化方式">
                  <a-select-option value="l1">L1范数</a-select-option>
                  <a-select-option value="l2">L2范数</a-select-option>
                  <a-select-option value="max">最大范数</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 线性回归节点配置 -->
            <template v-if="selectedNode.type === 'linearReg'">
              <a-form-item label="拟合截距">
                <a-switch v-model:value="selectedNode.config.fitIntercept" />
              </a-form-item>
              <a-form-item label="归一化数据">
                <a-switch v-model:value="selectedNode.config.normalize" />
              </a-form-item>
              <a-form-item label="复制X数据">
                <a-switch v-model:value="selectedNode.config.copyX" />
              </a-form-item>
            </template>

            <!-- 决策树回归节点配置 -->
            <template v-if="selectedNode.type === 'treeReg'">
              <a-form-item label="最大深度">
                <a-input-number v-model:value="selectedNode.config.maxDepth" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小分裂样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesSplit" :min="2" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小叶节点样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesLeaf" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="分裂准则">
                <a-select v-model:value="selectedNode.config.criterion" placeholder="选择准则">
                  <a-select-option value="mse">均方误差</a-select-option>
                  <a-select-option value="friedman_mse">费里德曼均方误差</a-select-option>
                  <a-select-option value="mae">平均绝对误差</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 随机森林回归节点配置 -->
            <template v-if="selectedNode.type === 'forestReg'">
              <a-form-item label="树的数量">
                <a-input-number v-model:value="selectedNode.config.nEstimators" :min="1" :max="500" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最大深度">
                <a-input-number v-model:value="selectedNode.config.maxDepth" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小分裂样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesSplit" :min="2" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="随机种子">
                <a-input-number v-model:value="selectedNode.config.randomState" :min="0" style="width: 100%;" placeholder="可选" />
              </a-form-item>
            </template>

            <!-- 逻辑回归节点配置 -->
            <template v-if="selectedNode.type === 'logisticReg'">
              <a-form-item label="正则化">
                <a-select v-model:value="selectedNode.config.penalty" placeholder="选择正则化">
                  <a-select-option value="l1">L1正则</a-select-option>
                  <a-select-option value="l2">L2正则</a-select-option>
                  <a-select-option value="elasticnet">Elastic-Net</a-select-option>
                  <a-select-option value="none">无</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="正则化强度">
                <a-input-number v-model:value="selectedNode.config.C" :min="0.001" :step="0.1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最大迭代次数">
                <a-input-number v-model:value="selectedNode.config.maxIter" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="拟合截距">
                <a-switch v-model:value="selectedNode.config.fitIntercept" />
              </a-form-item>
            </template>

            <!-- 决策树分类节点配置 -->
            <template v-if="selectedNode.type === 'decisionTree'">
              <a-form-item label="最大深度">
                <a-input-number v-model:value="selectedNode.config.maxDepth" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小分裂样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesSplit" :min="2" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小叶节点样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesLeaf" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="分裂准则">
                <a-select v-model:value="selectedNode.config.criterion" placeholder="选择准则">
                  <a-select-option value="gini">基尼系数</a-select-option>
                  <a-select-option value="entropy">信息增益</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 随机森林分类节点配置 -->
            <template v-if="selectedNode.type === 'randomForest'">
              <a-form-item label="树的数量">
                <a-input-number v-model:value="selectedNode.config.nEstimators" :min="1" :max="500" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最大深度">
                <a-input-number v-model:value="selectedNode.config.maxDepth" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="最小分裂样本数">
                <a-input-number v-model:value="selectedNode.config.minSamplesSplit" :min="2" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="随机种子">
                <a-input-number v-model:value="selectedNode.config.randomState" :min="0" style="width: 100%;" placeholder="可选" />
              </a-form-item>
            </template>

            <!-- SVM节点配置 -->
            <template v-if="selectedNode.type === 'svm'">
              <a-form-item label="核函数">
                <a-select v-model:value="selectedNode.config.kernel" placeholder="选择核函数">
                  <a-select-option value="linear">线性核</a-select-option>
                  <a-select-option value="poly">多项式核</a-select-option>
                  <a-select-option value="rbf">RBF核</a-select-option>
                  <a-select-option value="sigmoid">Sigmoid核</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="惩罚参数C">
                <a-input-number v-model:value="selectedNode.config.C" :min="0.01" :step="0.1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="Gamma">
                <a-input-number v-model:value="selectedNode.config.gamma" :min="0.0001" :step="0.001" style="width: 100%;" />
              </a-form-item>
            </template>

            <!-- K-Means聚类节点配置 -->
            <template v-if="selectedNode.type === 'kmeans'">
              <a-form-item label="聚类数量">
                <a-input-number v-model:value="selectedNode.config.nClusters" :min="2" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="初始化方法">
                <a-select v-model:value="selectedNode.config.init" placeholder="选择初始化方法">
                  <a-select-option value="k-means++">K-Means++</a-select-option>
                  <a-select-option value="random">随机</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="初始化次数">
                <a-input-number v-model:value="selectedNode.config.nInit" :min="1" style="width: 100%;" />
              </a-form-item>
              <a-form-item label="随机种子">
                <a-input-number v-model:value="selectedNode.config.randomState" :min="0" style="width: 100%;" placeholder="可选" />
              </a-form-item>
            </template>

            <!-- 模型评估节点配置 -->
            <template v-if="selectedNode.type === 'modelEval'">
              <a-form-item label="评估指标">
                <a-select v-model:value="selectedNode.config.metrics" placeholder="选择评估指标" mode="multiple" :max-tag-count="2">
                  <a-select-option value="accuracy">准确率</a-select-option>
                  <a-select-option value="precision">精确率</a-select-option>
                  <a-select-option value="recall">召回率</a-select-option>
                  <a-select-option value="f1">F1分数</a-select-option>
                  <a-select-option value="auc">AUC</a-select-option>
                  <a-select-option value="mse">均方误差</a-select-option>
                  <a-select-option value="r2">R2分数</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="平均方式">
                <a-select v-model:value="selectedNode.config.average" placeholder="选择平均方式">
                  <a-select-option value="binary">二进制</a-select-option>
                  <a-select-option value="micro">微平均</a-select-option>
                  <a-select-option value="macro">宏平均</a-select-option>
                  <a-select-option value="weighted">加权平均</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 描述统计节点配置 -->
            <template v-if="selectedNode.type === 'describe'">
              <a-form-item label="分析列">
                <a-input v-model:value="selectedNode.config.columns" placeholder="用逗号分隔列名" />
              </a-form-item>
              <a-form-item label="包含类型">
                <a-select v-model:value="selectedNode.config.include" placeholder="选择类型">
                  <a-select-option value="all">全部</a-select-option>
                  <a-select-option value="number">数值型</a-select-option>
                  <a-select-option value="object">类别型</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 相关性分析节点配置 -->
            <template v-if="selectedNode.type === 'correlation'">
              <a-form-item label="相关系数">
                <a-select v-model:value="selectedNode.config.method" placeholder="选择相关系数">
                  <a-select-option value="pearson">皮尔逊</a-select-option>
                  <a-select-option value="spearman">斯皮尔曼</a-select-option>
                  <a-select-option value="kendall">肯德尔</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="分析列">
                <a-input v-model:value="selectedNode.config.columns" placeholder="用逗号分隔列名，留空则分析全部" />
              </a-form-item>
            </template>

            <!-- 柱状图配置 -->
            <template v-if="selectedNode.type === 'barChart'">
              <a-form-item label="X轴字段">
                <a-input v-model:value="selectedNode.config.xField" placeholder="X轴字段名" />
              </a-form-item>
              <a-form-item label="Y轴字段">
                <a-input v-model:value="selectedNode.config.yField" placeholder="Y轴字段名" />
              </a-form-item>
              <a-form-item label="颜色">
                <a-input v-model:value="selectedNode.config.color" placeholder="例如: #5470c6" />
              </a-form-item>
            </template>

            <!-- 折线图配置 -->
            <template v-if="selectedNode.type === 'lineChart'">
              <a-form-item label="X轴字段">
                <a-input v-model:value="selectedNode.config.xField" placeholder="X轴字段名" />
              </a-form-item>
              <a-form-item label="Y轴字段">
                <a-input v-model:value="selectedNode.config.yField" placeholder="Y轴字段名" />
              </a-form-item>
              <a-form-item label="平滑曲线">
                <a-switch v-model:value="selectedNode.config.smooth" />
              </a-form-item>
            </template>

            <!-- 散点图配置 -->
            <template v-if="selectedNode.type === 'scatterChart'">
              <a-form-item label="X轴字段">
                <a-input v-model:value="selectedNode.config.xField" placeholder="X轴字段名" />
              </a-form-item>
              <a-form-item label="Y轴字段">
                <a-input v-model:value="selectedNode.config.yField" placeholder="Y轴字段名" />
              </a-form-item>
            </template>

            <!-- 数据采样节点配置 -->
            <template v-if="selectedNode.type === 'dataSample'">
              <a-form-item label="样本类型">
                <a-select v-model:value="selectedNode.config.sampleType" placeholder="选择采样类型">
                  <a-select-option value="random">随机样本</a-select-option>
                  <a-select-option value="stratified">分层采样</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="样本数量">
                <a-input-number v-model:value="selectedNode.config.sampleSize" :min="1" :max="10000" style="width: 100%;" />
              </a-form-item>
            </template>

            <!-- 设置角色节点配置 -->
            <template v-if="selectedNode.type === 'setRole'">
              <a-form-item label="特征列">
                <a-input v-model:value="selectedNode.config.features" placeholder="用逗号分隔特征列名" />
              </a-form-item>
              <a-form-item label="目标列">
                <a-input v-model:value="selectedNode.config.target" placeholder="目标列名" />
              </a-form-item>
            </template>

            <!-- 表合并节点配置 -->
            <template v-if="selectedNode.type === 'tableUnion'">
              <a-form-item label="合并方式">
                <a-select v-model:value="selectedNode.config.how" placeholder="选择合并方式">
                  <a-select-option value="inner">内连接</a-select-option>
                  <a-select-option value="outer">外连接</a-select-option>
                </a-select>
              </a-form-item>
            </template>

            <!-- 其他节点类型 -->
            <template v-if="!hasNodeConfig(selectedNode.type)">
              <a-empty description="该节点类型暂无配置参数" />
            </template>
          </a-form>
        </div>
      </div>
    </div>

    <!-- 实训手册悬浮按钮 -->
    <div class="manual-floating-btn" @click="showManual = true">
      <div class="manual-btn-content">
        <BookOutlined />
        <span>实训手册</span>
      </div>
    </div>

    <!-- 实训手册抽屉 -->
    <a-drawer
      v-model:open="showManual"
      title="实训手册"
      placement="right"
      :width="480"
    >
      <div class="manual-content" v-html="manualContent"></div>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  PlayCircleOutlined,
  PauseOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  SaveOutlined,
  BookOutlined,
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
  LoadingOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  CloseOutlined,
  UpOutlined,
  DownOutlined,
  InfoCircleOutlined,
  QuestionCircleOutlined,
  ThunderboltOutlined,
  CaretRightOutlined,
  StepForwardOutlined,
  BorderOutlined,
  UndoOutlined,
  RedoOutlined,
  SettingOutlined,
  LeftOutlined,
  RightOutlined,
  FileOutlined,
  PlusOutlined,
  DownloadOutlined,
  FolderOutlined,
  CloudOutlined,
  SplitCellsOutlined,
  MergeCellsOutlined,
  TableOutlined,
  BarChartOutlined,
  DotChartOutlined,
  RobotOutlined,
  ExperimentOutlined,
  SlidersOutlined,
  ForkOutlined,
  BranchesOutlined,
  ApiOutlined,
  BlockOutlined,
  ThunderboltFilled,
  BulbOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import {
  runAIPipeline,
  getAIRunLogs,
  getSavedAIPipeline,
  saveAIPipeline,
  stopAIRun,
  getTrainingManual,
  getProjectDatasets,
  getModelList,
  saveModel,
  deleteModel,
  executeSingleStep,
  getPipelineInsights
} from '@/api/training';
import type { PipelineDAG, DagNode, DagEdge, HistoryEntry, HistoryActionType, HistoryState, AIModel, PipelineInsight, Dataset } from '@/api/types/project';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 状态
const projectId = ref((route.params.id as string) || (route.query.projectId as string) || '');
const projectName = ref('AI机器学习实训');
const running = ref(false);
const saving = ref(false);
const showManual = ref(false);
const showLogs = ref(false);
const activeLogTab = ref('output');
const manualContent = ref('');
const trainingDatasets = ref<Dataset[]>([]);
const fallbackDatasets = [
  { value: 'iris', label: '鸢尾花数据集' },
  { value: 'boston', label: '波士顿房价数据集' },
  { value: 'diabetes', label: '糖尿病数据集' },
  { value: 'digits', label: '手写数字数据集' },
  { value: 'wine', label: '葡萄酒数据集' },
  { value: 'breast_cancer', label: '乳腺癌数据集' }
];
const searchKeyword = ref('');
const showKeyboardHints = ref(false);
const zoomLevel = ref(1);
const runId = ref('');

// 历史记录状态
const historyState = ref<HistoryState>({
  undoStack: [],
  redoStack: [],
  maxHistorySize: 50
});

const canUndo = computed(() => historyState.value.undoStack.length > 0);
const canRedo = computed(() => historyState.value.redoStack.length > 0);

// 单步运行状态
const singleStepState = ref({
  isActive: false,
  currentStepIndex: 0,
  executionOrder: [] as string[],  // 节点执行顺序
  isPaused: false,
  stepResults: [] as Array<{ nodeId: string; status: string; message: string }>
});

// 模板使用的计算属性，避免直接访问嵌套属性
const isSingleStepActive = computed(() => singleStepState.value?.isActive ?? false);
const isSingleStepPaused = computed(() => singleStepState.value?.isPaused ?? false);

// 洞察数据状态
const insightData = ref<{
  total_nodes: number;
  executed_nodes: number;
  failed_nodes: number;
  execution_time: number;
  model_insights?: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    auc?: number;
    training_samples: number;
    validation_samples: number;
    test_samples: number;
  };
  node_insights?: Array<{
    node_id: string;
    node_type: string;
    status: string;
    execution_time?: number;
    memory_usage?: number;
  }>;
} | null>(null);

// 加载洞察数据
const loadInsights = async (id: string) => {
  try {
    const data = await getPipelineInsights(id);
    if (data) {
      insightData.value = {
        total_nodes: data.total_nodes || data.node_insights?.length || 0,
        executed_nodes: data.executed_nodes || data.node_insights?.filter((n: { status: string }) => n.status === 'completed').length || 0,
        failed_nodes: data.failed_nodes || data.node_insights?.filter((n: { status: string }) => n.status === 'error').length || 0,
        execution_time: data.execution_time || 0,
        model_insights: data.model_insights,
        node_insights: data.node_insights?.map((n: { node_id: string; node_type: string; status: string; execution_time?: number; memory_usage?: number }) => ({
          node_id: n.node_id,
          node_type: n.node_type,
          status: n.status,
          execution_time: n.execution_time,
          memory_usage: n.memory_usage
        }))
      };
    }
  } catch (error) {
    console.error('加载洞察数据失败:', error);
  }
};

// 洞察建议列表
const suggestions = computed(() => {
  if (!insightData.value) return [];

  const suggestions: string[] = [];

  // 基于失败节点数添加建议
  if (insightData.value.failed_nodes > 0) {
    suggestions.push(`有 ${insightData.value.failed_nodes} 个节点执行失败，请检查节点配置和输入数据`);
  }

  // 基于执行时间添加建议
  if (insightData.value.execution_time > 60) {
    suggestions.push('执行时间较长，建议优化Pipeline结构或使用更高效的数据处理方式');
  }

  // 基于模型指标添加建议
  if (insightData.value.model_insights) {
    const { model_insights } = insightData.value;
    if (model_insights.accuracy !== undefined && model_insights.accuracy < 0.7) {
      suggestions.push('模型准确率较低，建议增加训练数据或调整模型参数');
    }
    if (model_insights.precision !== undefined && model_insights.precision < 0.7) {
      suggestions.push('精确率较低，模型可能存在较多误报，建议调整阈值或优化特征');
    }
    if (model_insights.recall !== undefined && model_insights.recall < 0.7) {
      suggestions.push('召回率较低，模型可能存在较多漏报，建议增加训练样本多样性');
    }
    if (model_insights.f1_score !== undefined && model_insights.f1_score < 0.7) {
      suggestions.push('F1分数较低，建议平衡精确率和召回率');
    }
  }

  return suggestions;
});

// 节点洞察表格列配置
const nodeInsightColumns = [
  {
    title: '节点',
    dataIndex: 'node_id',
    key: 'node_id',
    ellipsis: true
  },
  {
    title: '类型',
    dataIndex: 'node_type',
    key: 'node_type'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  },
  {
    title: '执行时间',
    dataIndex: 'execution_time',
    key: 'execution_time'
  },
  {
    title: '内存使用',
    dataIndex: 'memory_usage',
    key: 'memory_usage'
  }
];

// 获取指标颜色
const getMetricColor = (value: number): string => {
  if (value >= 0.9) return '#52c41a';
  if (value >= 0.7) return '#faad14';
  return '#ff4d4f';
};

// 获取状态颜色
const getStatusColor = (status: string): string => {
  const statusColors: Record<string, string> = {
    completed: 'success',
    running: 'processing',
    pending: 'default',
    error: 'error'
  };
  return statusColors[status] || 'default';
};

// 获取状态文本
const getStatusText = (status: string): string => {
  const statusTexts: Record<string, string> = {
    completed: '完成',
    running: '运行中',
    pending: '等待',
    error: '错误'
  };
  return statusTexts[status] || status;
};

// 格式化内存使用量
const formatMemory = (bytes?: number): string => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
};

// 拓扑排序辅助函数 - 确定节点执行顺序
const getTopologicalExecutionOrder = (): string[] => {
  const nodeIds = nodes.value.map(n => n.id);
  const inDegree: Record<string, number> = {};
  const adjList: Record<string, string[]> = {};

  // 初始化
  nodeIds.forEach(id => {
    inDegree[id] = 0;
    adjList[id] = [];
  });

  // 构建图
  edges.value.forEach(edge => {
    if (adjList[edge.source]) {
      adjList[edge.source].push(edge.target);
      inDegree[edge.target] = (inDegree[edge.target] || 0) + 1;
    }
  });

  // 拓扑排序 (Kahn算法)
  const queue: string[] = [];
  const result: string[] = [];

  // 入度为0的节点加入队列
  nodeIds.forEach(id => {
    if (inDegree[id] === 0) {
      queue.push(id);
    }
  });

  while (queue.length > 0) {
    const current = queue.shift()!;
    result.push(current);

    adjList[current].forEach(neighbor => {
      inDegree[neighbor]--;
      if (inDegree[neighbor] === 0) {
        queue.push(neighbor);
      }
    });
  }

  return result;
};

// 模式和面板状态
const designMode = ref<'modeling' | 'insight'>('modeling');
const leftPanelTab = ref<'operators' | 'models'>('operators');
const categoryFilter = ref('all');
const expandedCategories = ref<string[]>(['data-management', 'data-processing', 'ml']);

// 模型库状态
const modelLibraryState = ref({
  models: [] as AIModel[],
  loading: false,
  saving: false,
  selectedModel: null as AIModel | null,
  searchKeyword: '',
  filterType: '',
  showSaveModal: false,
  saveForm: {
    name: '',
    type: 'regression',
    algorithm: 'linear',
    description: ''
  }
});

// 过滤后的模型列表
const filteredModelList = computed(() => {
  let models = modelLibraryState.value.models;

  // 按名称搜索
  if (modelLibraryState.value.searchKeyword) {
    const keyword = modelLibraryState.value.searchKeyword.toLowerCase();
    models = models.filter(model =>
      model.name.toLowerCase().includes(keyword) ||
      model.description.toLowerCase().includes(keyword)
    );
  }

  // 按类型筛选
  if (modelLibraryState.value.filterType) {
    models = models.filter(model => model.type === modelLibraryState.value.filterType);
  }

  return models;
});

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
};

const datasetOptions = computed(() => {
  if (trainingDatasets.value.length === 0) {
    return fallbackDatasets;
  }
  return trainingDatasets.value.map(dataset => ({
    value: String(dataset.id),
    label: dataset.name || `数据集 ${dataset.id}`
  }));
});

const loadTrainingDatasets = async () => {
  if (!projectId.value) {
    trainingDatasets.value = [];
    return;
  }
  trainingDatasets.value = await getProjectDatasets(projectId.value);
};

const loadSavedPipeline = async () => {
  if (!projectId.value) return;

  const savedPipeline = await getSavedAIPipeline(projectId.value);
  if (!savedPipeline || savedPipeline.nodes.length === 0) return;

  nodes.value = savedPipeline.nodes.map(node => ({
    ...node,
    config: node.config || {},
    position: node.position || { x: 120, y: 120 }
  }));
  edges.value = (savedPipeline.edges || []).map(edge => ({ ...edge }));
  selectedNode.value = null;
  selectedEdge.value = null;
  runningNodes.value = [];
  completedNodes.value = [];
  errorNodes.value = [];
  historyState.value.undoStack = [];
  historyState.value.redoStack = [];
  await nextTick();
  fitLoadedPipelineToCanvas();
};

const fitLoadedPipelineToCanvas = () => {
  if (!canvasRef.value || nodes.value.length === 0) return;

  const maxNodeRight = Math.max(...nodes.value.map(node => (node.position?.x || 0) + 160));
  const canvasWidth = canvasRef.value.clientWidth || canvasRef.value.getBoundingClientRect().width;
  if (!maxNodeRight || !canvasWidth) return;

  const fitScale = Math.max(0.5, Math.min(1, (canvasWidth - 40) / maxNodeRight));
  zoomLevel.value = Number(fitScale.toFixed(2));
};

// 获取模型列表
const fetchModelList = async () => {
  try {
    modelLibraryState.value.loading = true;
    modelLibraryState.value.models = await getModelList();
  } catch (error) {
    console.error('获取模型列表失败:', error);
  } finally {
    modelLibraryState.value.loading = false;
  }
};

// 保存模型
const handleSaveModel = async () => {
  if (!modelLibraryState.value.saveForm.name.trim()) {
    message.warning('请输入模型名称');
    return;
  }

  if (nodes.value.length === 0) {
    message.warning('画布中没有节点，无法保存模型');
    return;
  }

  try {
    modelLibraryState.value.saving = true;
    const success = await saveModel({
      name: modelLibraryState.value.saveForm.name,
      type: modelLibraryState.value.saveForm.type,
      algorithm: modelLibraryState.value.saveForm.algorithm,
      description: modelLibraryState.value.saveForm.description,
      pipeline: {
        nodes: nodes.value,
        edges: edges.value
      }
    });

    if (success) {
      message.success('模型保存成功');
      modelLibraryState.value.showSaveModal = false;
      modelLibraryState.value.saveForm = { name: '', type: 'regression', algorithm: 'linear', description: '' };
      fetchModelList();
    }
  } catch (error) {
    console.error('保存模型失败:', error);
    message.error('保存模型失败');
  } finally {
    modelLibraryState.value.saving = false;
  }
};

// 将模型加载到画布
const loadModelToCanvas = (model: AIModel) => {
  if (model.pipeline) {
    // 恢复节点位置偏移，避免完全重叠
    const offsetX = 50;
    const offsetY = 50;

    if (model.pipeline.nodes && model.pipeline.nodes.length > 0) {
      nodes.value = model.pipeline.nodes.map(node => ({
        ...node,
        id: `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        position: {
          x: node.position.x + offsetX,
          y: node.position.y + offsetY
        }
      }));
    }

    if (model.pipeline.edges && model.pipeline.edges.length > 0) {
      // 更新边的源和目标ID
      const idMap: Record<string, string> = {};
      nodes.value.forEach((node, index) => {
        idMap[model.pipeline!.nodes[index].id] = node.id;
      });

      edges.value = model.pipeline.edges.map((edge, index) => ({
        ...edge,
        id: `edge_${Date.now()}_${index}`,
        source: idMap[edge.source] || edge.source,
        target: idMap[edge.target] || edge.target
      }));
    }

    message.success(`模型 "${model.name}" 已加载到画布`);
    selectedNode.value = null;
    selectedEdge.value = null;
  }
};

// 流程管理
const flows = ref([
  { id: 'flow1', name: '流程1' }
]);
const currentFlowId = ref('flow1');
const flowTabListRef = ref<HTMLElement>();

// 当前流程
const currentFlow = computed(() => flows.value.find(f => f.id === currentFlowId.value));

// 画布相关
const canvasRef = ref<HTMLElement>();
const canvasSize = ref({ width: 2000, height: 2000 });
const nodes = ref<DagNode[]>([]);
const edges = ref<DagEdge[]>([]);
const selectedNode = ref<DagNode | null>(null);
const selectedEdge = ref<DagEdge | null>(null);
const runningNodes = ref<string[]>([]);
const completedNodes = ref<string[]>([]);
const errorNodes = ref<string[]>([]);
const outputLogs = ref<any[]>([]);

// 连线相关
const isConnecting = ref(false);
const connectionStart = ref<any>(null);
const tempConnectionPath = ref('');

// 算子树形数据
const operatorTreeData = computed(() => [
  {
    title: '数据管理',
    key: 'data-management',
    icon: FolderOutlined,
    children: [
      { title: '读取数据', key: 'readData', type: 'readData', icon: DatabaseOutlined, isLeaf: true },
      { title: '写入数据', key: 'writeData', type: 'writeData', icon: CloudOutlined, isLeaf: true },
      { title: '样例数据', key: 'sampleData', type: 'sampleData', icon: TableOutlined, isLeaf: true }
    ]
  },
  {
    title: '数据处理',
    key: 'data-processing',
    icon: FilterOutlined,
    children: [
      { title: '数据过滤', key: 'dataFilter', type: 'dataFilter', icon: FilterOutlined, isLeaf: true },
      { title: '数据拆分', key: 'dataSplit', type: 'dataSplit', icon: SplitCellsOutlined, isLeaf: true },
      { title: '数据合并', key: 'dataMerge', type: 'dataMerge', icon: MergeCellsOutlined, isLeaf: true },
      { title: '数据采样', key: 'dataSample', type: 'dataSample', icon: DotChartOutlined, isLeaf: true },
      { title: '设置角色', key: 'setRole', type: 'setRole', icon: SlidersOutlined, isLeaf: true }
    ]
  },
  {
    title: '数据融合',
    key: 'data-fusion',
    icon: MergeCellsOutlined,
    children: [
      { title: '表连接', key: 'tableJoin', type: 'tableJoin', icon: ApiOutlined, isLeaf: true },
      { title: '表合并', key: 'tableUnion', type: 'tableUnion', icon: BlockOutlined, isLeaf: true }
    ]
  },
  {
    title: '特征工程',
    key: 'feature-engineering',
    icon: HighlightOutlined,
    children: [
      { title: '特征选择', key: 'featureSelect', type: 'featureSelect', icon: HighlightOutlined, isLeaf: true },
      { title: '特征提取', key: 'featureExtract', type: 'featureExtract', icon: BuildOutlined, isLeaf: true },
      { title: 'PCA降维', key: 'pca', type: 'pca', icon: NodeIndexOutlined, isLeaf: true },
      { title: '标准化', key: 'standardize', type: 'standardize', icon: SlidersOutlined, isLeaf: true },
      { title: '归一化', key: 'normalize', type: 'normalize', icon: SlidersOutlined, isLeaf: true }
    ]
  },
  {
    title: '统计分析',
    key: 'statistics',
    icon: BarChartOutlined,
    children: [
      { title: '描述统计', key: 'describe', type: 'describe', icon: BarChartOutlined, isLeaf: true },
      { title: '相关性分析', key: 'correlation', type: 'correlation', icon: DotChartOutlined, isLeaf: true }
    ]
  },
  {
    title: '图表分析',
    key: 'chart-analysis',
    icon: LineChartOutlined,
    children: [
      { title: '柱状图', key: 'barChart', type: 'barChart', icon: BarChartOutlined, isLeaf: true },
      { title: '折线图', key: 'lineChart', type: 'lineChart', icon: LineChartOutlined, isLeaf: true },
      { title: '散点图', key: 'scatterChart', type: 'scatterChart', icon: DotChartOutlined, isLeaf: true }
    ]
  },
  {
    title: '机器学习',
    key: 'ml',
    icon: RobotOutlined,
    children: [
      {
        title: '回归',
        key: 'ml-regression',
        children: [
          { title: '线性回归', key: 'linearReg', type: 'linearReg', icon: LineChartOutlined, isLeaf: true },
          { title: '决策树回归', key: 'treeReg', type: 'treeReg', icon: ApartmentOutlined, isLeaf: true },
          { title: '随机森林回归', key: 'forestReg', type: 'forestReg', icon: ClusterOutlined, isLeaf: true }
        ]
      },
      {
        title: '分类',
        key: 'ml-classification',
        children: [
          { title: '逻辑回归', key: 'logisticReg', type: 'logisticReg', icon: FunctionOutlined, isLeaf: true },
          { title: '决策树', key: 'decisionTree', type: 'decisionTree', icon: ApartmentOutlined, isLeaf: true },
          { title: '随机森林', key: 'randomForest', type: 'randomForest', icon: ClusterOutlined, isLeaf: true },
          { title: 'SVM', key: 'svm', type: 'svm', icon: RadarChartOutlined, isLeaf: true }
        ]
      },
      {
        title: '聚类',
        key: 'ml-clustering',
        children: [
          { title: 'K-Means', key: 'kmeans', type: 'kmeans', icon: DotChartOutlined, isLeaf: true }
        ]
      },
      {
        title: '关联',
        key: 'ml-association',
        children: [
          { title: 'Apriori', key: 'apriori', type: 'apriori', icon: BranchesOutlined, isLeaf: true }
        ]
      },
      {
        title: '时间序列',
        key: 'ml-timeseries',
        children: [
          { title: 'ARIMA', key: 'arima', type: 'arima', icon: LineChartOutlined, isLeaf: true }
        ]
      },
      {
        title: '综合评价',
        key: 'ml-evaluation',
        children: [
          { title: '模型评估', key: 'modelEval', type: 'modelEval', icon: CheckCircleOutlined, isLeaf: true }
        ]
      },
      {
        title: '推荐',
        key: 'ml-recommend',
        children: [
          { title: '协同过滤', key: 'collaborative', type: 'collaborative', icon: ForkOutlined, isLeaf: true }
        ]
      }
    ]
  },
  {
    title: '深度学习',
    key: 'deep-learning',
    icon: ThunderboltFilled,
    children: [
      { title: 'DNN', key: 'dnn', type: 'dnn', icon: ApiOutlined, isLeaf: true },
      { title: 'CNN', key: 'cnn', type: 'cnn', icon: BlockOutlined, isLeaf: true },
      { title: 'RNN', key: 'rnn', type: 'rnn', icon: BranchesOutlined, isLeaf: true }
    ]
  },
  {
    title: '集成学习',
    key: 'ensemble',
    icon: ClusterOutlined,
    children: [
      { title: 'Bagging', key: 'bagging', type: 'bagging', icon: ClusterOutlined, isLeaf: true },
      { title: 'Boosting', key: 'boosting', type: 'boosting', icon: ClusterOutlined, isLeaf: true }
    ]
  },
  {
    title: '自动学习',
    key: 'auto-ml',
    icon: RobotOutlined,
    children: [
      { title: 'AutoML', key: 'automl', type: 'automl', icon: RobotOutlined, isLeaf: true }
    ]
  },
  {
    title: '扩展编程',
    key: 'extend',
    icon: ExperimentOutlined,
    children: [
      { title: 'Python脚本', key: 'python', type: 'python', icon: ExperimentOutlined, isLeaf: true },
      { title: 'SQL脚本', key: 'sql', type: 'sql', icon: DatabaseOutlined, isLeaf: true }
    ]
  },
  {
    title: '文本分析',
    key: 'text-analysis',
    icon: FileOutlined,
    children: [
      { title: '分词', key: 'tokenize', type: 'tokenize', icon: ScissorOutlined, isLeaf: true },
      { title: '词频统计', key: 'wordFreq', type: 'wordFreq', icon: BarChartOutlined, isLeaf: true }
    ]
  },
  {
    title: '模型管理',
    key: 'model-management',
    icon: FolderOutlined,
    children: [
      { title: '保存模型', key: 'saveModel', type: 'saveModel', icon: SaveOutlined, isLeaf: true },
      { title: '加载模型', key: 'loadModel', type: 'loadModel', icon: CloudOutlined, isLeaf: true }
    ]
  },
  {
    title: '流程控制',
    key: 'flow-control',
    icon: ForkOutlined,
    children: [
      { title: '多分支', key: 'branch', type: 'branch', icon: ForkOutlined, isLeaf: true }
    ]
  },
  {
    title: '金融分析',
    key: 'finance',
    icon: LineChartOutlined,
    children: [
      { title: '风险评估', key: 'riskEval', type: 'riskEval', icon: ExperimentOutlined, isLeaf: true }
    ]
  },
  {
    title: '自定义算法',
    key: 'custom',
    icon: BuildOutlined,
    children: [
      { title: '自定义算子', key: 'customOp', type: 'customOp', icon: BuildOutlined, isLeaf: true }
    ]
  }
]);

// 流程管理函数
const switchFlow = (flowId: string) => {
  currentFlowId.value = flowId;
  // TODO: 加载对应流程的节点和边
};

const addFlow = () => {
  const newId = `flow_${Date.now()}`;
  flows.value.push({
    id: newId,
    name: `流程${flows.value.length + 1}`
  });
  currentFlowId.value = newId;
};

const removeFlow = (flowId: string) => {
  if (flows.value.length <= 1) {
    message.warning('至少保留一个流程');
    return;
  }
  const index = flows.value.findIndex(f => f.id === flowId);
  if (index > -1) {
    flows.value.splice(index, 1);
    if (currentFlowId.value === flowId) {
      currentFlowId.value = flows.value[0].id;
    }
  }
};

const scrollFlowTabs = (direction: 'left' | 'right') => {
  if (flowTabListRef.value) {
    const scrollAmount = 100;
    flowTabListRef.value.scrollLeft += direction === 'left' ? -scrollAmount : scrollAmount;
  }
};

// 辅助函数：从树中查找所有算子
const findAllOperators = (treeData: any[]): any[] => {
  const operators: any[] = [];
  const traverse = (nodes: any[]) => {
    for (const node of nodes) {
      if (node.isLeaf) {
        operators.push(node);
      }
      if (node.children) {
        traverse(node.children);
      }
    }
  };
  traverse(treeData);
  return operators;
};

// 节点端口配置
const hasInputPort = (type: string) => {
  const noInputTypes = ['readData', 'sampleData'];
  return !noInputTypes.includes(type);
};

const hasOutputPort = (type: string) => {
  const noOutputTypes = ['writeData', 'modelEval', 'saveModel'];
  return !noOutputTypes.includes(type);
};

// 检查节点类型是否有配置
const hasNodeConfig = (type: string): boolean => {
  const configTypes = [
    'readData', 'writeData', 'sampleData', 'dataFilter', 'dataSplit',
    'dataMerge', 'tableJoin', 'tableUnion', 'featureSelect', 'pca',
    'standardize', 'normalize', 'linearReg', 'treeReg', 'forestReg',
    'logisticReg', 'decisionTree', 'randomForest', 'svm', 'kmeans',
    'modelEval', 'describe', 'correlation', 'barChart', 'lineChart',
    'scatterChart', 'dataSample', 'setRole'
  ];
  return configTypes.includes(type);
};

// 获取节点图标
const getNodeIcon = (type: string) => {
  const allOperators = findAllOperators(operatorTreeData.value);
  const operator = allOperators.find(op => op.type === type);
  return operator?.icon || DatabaseOutlined;
};

// 拖拽功能
const handleDragStart = (event: DragEvent, operator: any) => {
  event.dataTransfer!.effectAllowed = 'copy';
  event.dataTransfer!.setData('operator', JSON.stringify(operator));
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();
  
  const operatorData = event.dataTransfer!.getData('operator');
  if (!operatorData) return;
  
  const operator = JSON.parse(operatorData);
  const rect = canvasRef.value!.getBoundingClientRect();
  const x = (event.clientX - rect.left) / zoomLevel.value;
  const y = (event.clientY - rect.top) / zoomLevel.value;
  
  const newNode: DagNode = {
    id: `node_${Date.now()}`,
    type: operator.type,
    label: operator.name,
    config: {},
    position: { x, y }
  };

  nodes.value.push(newNode);
  saveHistory('add_node', `添加节点: ${operator.name}`);
};

// 节点选择
const selectNode = (node: DagNode) => {
  selectedNode.value = node;
  selectedEdge.value = null;
};

// 边选择
const selectEdge = (edge: DagEdge) => {
  selectedEdge.value = edge;
  selectedNode.value = null;
};

// 画布点击
const handleCanvasClick = (event?: MouseEvent) => {
  const target = event?.target as HTMLElement | null;
  const nodeElement = target?.closest?.('.flow-node') as HTMLElement | null;
  const nodeId = nodeElement?.dataset.nodeId;

  if (nodeId) {
    const node = nodes.value.find(item => item.id === nodeId);
    if (node) {
      selectNode(node);
      return;
    }
  }

  selectedNode.value = null;
  selectedEdge.value = null;
};

// 键盘事件处理
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (selectedNode.value) {
      // 删除选中的节点及其相关连接
      const nodeId = selectedNode.value.id;
      const nodeLabel = selectedNode.value.label;

      // 删除相关的边
      edges.value = edges.value.filter(edge =>
        edge.source !== nodeId && edge.target !== nodeId
      );

      // 删除节点
      nodes.value = nodes.value.filter(node => node.id !== nodeId);

      selectedNode.value = null;
      saveHistory('delete_node', `删除节点: ${nodeLabel}`);
      message.success('节点已删除');
    } else if (selectedEdge.value) {
      // 删除选中的边
      const edgeId = selectedEdge.value.id;
      const sourceNode = nodes.value.find(n => n.id === selectedEdge.value?.source);
      const targetNode = nodes.value.find(n => n.id === selectedEdge.value?.target);
      edges.value = edges.value.filter(edge => edge.id !== edgeId);
      selectedEdge.value = null;
      saveHistory('delete_edge', `删除连接: ${sourceNode?.label || '?'} → ${targetNode?.label || '?'}`);
      message.success('连接已删除');
    }
  }
};

// 保存历史记录
const saveHistory = (action: HistoryActionType, description: string) => {
  const entry: HistoryEntry = {
    id: `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    action,
    timestamp: Date.now(),
    description,
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  };

  // 添加到撤销栈
  historyState.value.undoStack.push(entry);

  // 限制历史栈大小
  if (historyState.value.undoStack.length > historyState.value.maxHistorySize) {
    historyState.value.undoStack.shift();
  }

  // 每次新操作后清空重做栈
  historyState.value.redoStack = [];

  console.log(`[历史记录] ${description}, 撤销栈: ${historyState.value.undoStack.length}, 重做栈: ${historyState.value.redoStack.length}`);
};

// 撤销操作
const undo = () => {
  if (!canUndo.value) {
    message.warning('没有可撤销的操作');
    return;
  }

  const entry = historyState.value.undoStack.pop();
  if (!entry) return;

  // 将当前状态添加到重做栈
  const currentEntry: HistoryEntry = {
    id: `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    action: entry.action,
    timestamp: Date.now(),
    description: `撤销: ${entry.description}`,
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  };
  historyState.value.redoStack.push(currentEntry);

  // 恢复历史状态
  nodes.value = entry.nodes;
  edges.value = entry.edges;

  // 清除选择状态
  selectedNode.value = null;
  selectedEdge.value = null;

  message.success(`已撤销: ${entry.description}`);
  console.log(`[撤销] ${entry.description}, 撤销栈: ${historyState.value.undoStack.length}, 重做栈: ${historyState.value.redoStack.length}`);
};

// 重做操作
const redo = () => {
  if (!canRedo.value) {
    message.warning('没有可重做的操作');
    return;
  }

  const entry = historyState.value.redoStack.pop();
  if (!entry) return;

  // 将当前状态添加到撤销栈
  const currentEntry: HistoryEntry = {
    id: `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    action: entry.action,
    timestamp: Date.now(),
    description: `重做: ${entry.description}`,
    nodes: JSON.parse(JSON.stringify(nodes.value)),
    edges: JSON.parse(JSON.stringify(edges.value))
  };
  historyState.value.undoStack.push(currentEntry);

  // 恢复历史状态
  nodes.value = entry.nodes;
  edges.value = entry.edges;

  // 清除选择状态
  selectedNode.value = null;
  selectedEdge.value = null;

  message.success(`已重做: ${entry.description}`);
  console.log(`[重做] ${entry.description}, 撤销栈: ${historyState.value.undoStack.length}, 重做栈: ${historyState.value.redoStack.length}`);
};

// 全局键盘快捷键处理
const handleGlobalKeydown = (event: KeyboardEvent) => {
  // Ctrl+Z 或 Cmd+Z: 撤销
  if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
    event.preventDefault();
    undo();
  }

  // Ctrl+Y 或 Ctrl+Shift+Z: 重做
  if ((event.ctrlKey || event.metaKey) && (event.key === 'y' || (event.shiftKey && event.key === 'z'))) {
    event.preventDefault();
    redo();
  }

  // Ctrl+S 或 Cmd+S: 保存
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault();
    handleSave();
  }

  // Ctrl+R 或 Cmd+R: 运行
  if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
    event.preventDefault();
    if (!running.value) {
      handleRun();
    }
  }

  // F1: 显示/隐藏快捷键提示
  if (event.key === 'F1') {
    event.preventDefault();
    showKeyboardHints.value = !showKeyboardHints.value;
  }

  // F5 或 Ctrl+R: 阻止默认刷新
  if (event.key === 'F5' || ((event.ctrlKey || event.metaKey) && event.key === 'r' && event.shiftKey)) {
    event.preventDefault();
    message.warning('请使用保存按钮保存工作流');
  }
};

// 节点拖拽
const startDragNode = (event: MouseEvent, node: DagNode) => {
  const startX = event.clientX;
  const startY = event.clientY;
  const startNodeX = node.position.x;
  const startNodeY = node.position.y;
  
  const handleMouseMove = (e: MouseEvent) => {
    const deltaX = (e.clientX - startX) / zoomLevel.value;
    const deltaY = (e.clientY - startY) / zoomLevel.value;
    node.position.x = startNodeX + deltaX;
    node.position.y = startNodeY + deltaY;
  };
  
  const handleMouseUp = () => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    // 保存移动节点的历史记录
    saveHistory('move_node', `移动节点: ${node.label}`);
  };
  
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

// 连线功能
const startConnection = (event: MouseEvent, node: DagNode, portType: 'input' | 'output') => {
  if (portType === 'input') return; // 只能从输出端口开始连线
  
  isConnecting.value = true;
  connectionStart.value = { node, port: portType };
  
  const handleMouseMove = (e: MouseEvent) => {
    updateTempConnection(e);
  };
  
  const handleMouseUp = (e: MouseEvent) => {
    finishConnection(e);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };
  
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
};

const updateTempConnection = (event: MouseEvent) => {
  if (!connectionStart.value || !canvasRef.value) return;
  
  const rect = canvasRef.value.getBoundingClientRect();
  const endX = (event.clientX - rect.left) / zoomLevel.value;
  const endY = (event.clientY - rect.top) / zoomLevel.value;
  
  const startNode = connectionStart.value.node;
  const startX = startNode.position.x + 160; // 节点宽度
  const startY = startNode.position.y + 30; // 节点高度的一半
  
  tempConnectionPath.value = `M ${startX} ${startY} L ${endX} ${endY}`;
};

const finishConnection = (event: MouseEvent) => {
  isConnecting.value = false;
  tempConnectionPath.value = '';

  if (!connectionStart.value) return;

  const { node: sourceNode, port: sourcePort } = connectionStart.value;

  // 只有从输出端口开始连接才有意义
  if (sourcePort !== 'output') return;

  // 检查鼠标位置是否在某个输入端口上
  const mouseX = event.clientX;
  const mouseY = event.clientY;

  let targetNode: DagNode | null = null;

  // 遍历所有节点，检查鼠标是否在输入端口区域
  for (const node of nodes.value) {
    if (node.id === sourceNode.id) continue; // 不能连接到自己

    // 获取节点的实际DOM元素
    const nodeElement = document.getElementById(`node-${node.id}`);
    if (!nodeElement) continue;

    const nodeRect = nodeElement.getBoundingClientRect();

    // 检查鼠标是否在节点范围内
    if (mouseX >= nodeRect.left && mouseX <= nodeRect.right &&
        mouseY >= nodeRect.top && mouseY <= nodeRect.bottom) {

      // 检查是否是有效的连接目标（有输入端口且不是输出到输出）
      if (hasInputPort(node.type)) {
        targetNode = node;
        break;
      }
    }
  }

  if (targetNode) {
    // 检查是否已存在相同的连接
    const existingEdge = edges.value.find(edge =>
      edge.source === sourceNode.id && edge.target === targetNode.id
    );

    if (!existingEdge) {
      // 创建新连接
      const newEdge: DagEdge = {
        id: `edge_${Date.now()}`,
        source: sourceNode.id,
        target: targetNode.id,
        sourceHandle: 'output',
        targetHandle: 'input'
      };

      edges.value.push(newEdge);
      saveHistory('add_edge', `添加连接: ${sourceNode.label} → ${targetNode.label}`);
      message.success('连接创建成功');
    } else {
      message.warning('连接已存在');
    }
  } else {
    // 检查是否尝试连接到输出端口（非法连接）
    for (const node of nodes.value) {
      // 获取节点的实际DOM元素
      const nodeElement = document.getElementById(`node-${node.id}`);
      if (!nodeElement) continue;

      const nodeRect = nodeElement.getBoundingClientRect();

      // 输出端口区域（节点右侧）
      const outputPortRect = {
        left: nodeRect.right - 20,
        top: nodeRect.top + nodeRect.height / 2 - 10,
        right: nodeRect.right,
        bottom: nodeRect.top + nodeRect.height / 2 + 10
      };

      if (mouseX >= outputPortRect.left && mouseX <= outputPortRect.right &&
          mouseY >= outputPortRect.top && mouseY <= outputPortRect.bottom) {
        message.error('不能连接输出端口到输出端口');
        return;
      }
    }

    // 没有找到有效的连接目标
    message.info('请连接到有效的输入端口');
  }

  connectionStart.value = null;
};

// 获取边的路径
const getEdgePath = (edge: DagEdge) => {
  const sourceNode = nodes.value.find(n => n.id === edge.source);
  const targetNode = nodes.value.find(n => n.id === edge.target);

  if (!sourceNode || !targetNode) return '';

  // 获取节点的实际DOM元素来计算屏幕坐标
  const sourceElement = document.getElementById(`node-${sourceNode.id}`);
  const targetElement = document.getElementById(`node-${targetNode.id}`);

  if (!sourceElement || !targetElement) return '';

  const sourceRect = sourceElement.getBoundingClientRect();
  const targetRect = targetElement.getBoundingClientRect();

  // 计算连接点：输出端口在节点右侧，输入端口在节点左侧
  const startX = sourceRect.right;
  const startY = sourceRect.top + sourceRect.height / 2;
  const endX = targetRect.left;
  const endY = targetRect.top + targetRect.height / 2;

  // 转换为SVG坐标系（相对于canvas）
  const svgElement = document.querySelector('.flow-svg');
  if (!svgElement) return '';

  const svgRect = svgElement.getBoundingClientRect();
  const scale = zoomLevel.value;

  const svgStartX = (startX - svgRect.left) / scale;
  const svgStartY = (startY - svgRect.top) / scale;
  const svgEndX = (endX - svgRect.left) / scale;
  const svgEndY = (endY - svgRect.top) / scale;

  // 贝塞尔曲线控制点
  const controlX1 = svgStartX + (svgEndX - svgStartX) / 3;
  const controlY1 = svgStartY;
  const controlX2 = svgEndX - (svgEndX - svgStartX) / 3;
  const controlY2 = svgEndY;

  return `M ${svgStartX} ${svgStartY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${svgEndX} ${svgEndY}`;
};

// 缩放功能
const handleZoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value + 0.1, 2);
};

const handleZoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.5);
};

// 单步运行
const handleSingleStep = async () => {
  // 检查是否有节点
  if (nodes.value.length === 0) {
    message.warning('请先添加节点');
    return;
  }

  // 如果已经在单步运行中，检查是否暂停
  if (singleStepState.value.isActive && singleStepState.value.isPaused) {
    // 继续执行下一步
    await executeNextStep();
    return;
  }

  // 初始化单步运行
  singleStepState.value.isActive = true;
  singleStepState.value.isPaused = true;  // 立即暂停，等待用户点击继续
  singleStepState.value.currentStepIndex = 0;
  singleStepState.value.stepResults = [];

  // 计算拓扑执行顺序
  const executionOrder = getTopologicalExecutionOrder();
  singleStepState.value.executionOrder = executionOrder;

  // 重置节点状态
  runningNodes.value = [];
  completedNodes.value = [];
  errorNodes.value = [];

  message.info(`单步运行已就绪，共 ${executionOrder.length} 个节点，点击"单步运行"按钮执行下一步`);

  // 输出日志
  outputLogs.value.push({
    time: new Date().toLocaleTimeString(),
    level: 'info',
    message: `单步运行已启动，等待执行第 1 个节点（共 ${executionOrder.length} 个节点）`
  });
};

// 执行下一步
const executeNextStep = async () => {
  if (!singleStepState.value.isActive) return;

  const order = singleStepState.value.executionOrder;
  const currentIndex = singleStepState.value.currentStepIndex;

  if (currentIndex >= order.length) {
    // 所有节点执行完毕
    singleStepState.value.isActive = false;
    singleStepState.value.isPaused = false;

    outputLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'success',
      message: '所有节点执行完成'
    });

    message.success('Pipeline执行完成');

    // 加载洞察数据
    if (runId.value) {
      await loadInsights(runId.value);
    }

    // 切换到洞察模式
    designMode.value = 'insight';

    // 重置状态
    singleStepState.value.currentStepIndex = 0;
    return;
  }

  const currentNodeId = order[currentIndex];
  const currentNode = nodes.value.find(n => n.id === currentNodeId);

  if (!currentNode) return;

  // 标记当前节点为运行中
  runningNodes.value = [currentNodeId];
  errorNodes.value = errorNodes.value.filter(id => id !== currentNodeId);

  outputLogs.value.push({
    time: new Date().toLocaleTimeString(),
    level: 'running',
    message: `开始执行节点: ${currentNode.label} (${currentIndex + 1}/${order.length})`
  });

  try {
    // 调用后端API执行单步
    const result = await executeSingleStep(
      projectId.value || 'default',
      currentNodeId,
      { node_type: currentNode.type },
      currentNode.config || {}
    );

    if (result) {
      runId.value = result.execution_id || result.run_id;

      // 标记为完成
      runningNodes.value = [];
      if (!completedNodes.value.includes(currentNodeId)) {
        completedNodes.value.push(currentNodeId);
      }

      // 记录结果
      singleStepState.value.stepResults.push({
        nodeId: currentNodeId,
        status: 'success',
        message: `${currentNode.label} 执行成功`
      });

      outputLogs.value.push({
        time: new Date().toLocaleTimeString(),
        level: 'success',
        message: `节点执行完成: ${currentNode.label}`
      });
    } else {
      throw new Error('执行返回空结果');
    }
  } catch (error) {
    // 执行失败
    runningNodes.value = [];
    errorNodes.value.push(currentNodeId);

    singleStepState.value.stepResults.push({
      nodeId: currentNodeId,
      status: 'error',
      message: `${currentNode.label} 执行失败`
    });

    outputLogs.value.push({
      time: new Date().toLocaleTimeString(),
      level: 'error',
      message: `节点执行失败: ${currentNode.label}`
    });
  }

  // 继续下一步
  singleStepState.value.currentStepIndex++;

  if (singleStepState.value.isActive && singleStepState.value.isPaused) {
    message.info(`下一步: ${singleStepState.value.currentStepIndex < order.length ? nodes.value.find(n => n.id === order[singleStepState.value.currentStepIndex])?.label : '完成'}`);
  }
};

// 停止单步运行
const stopSingleStep = () => {
  singleStepState.value.isActive = false;
  singleStepState.value.isPaused = false;
  singleStepState.value.currentStepIndex = 0;
  runningNodes.value = [];

  outputLogs.value.push({
    time: new Date().toLocaleTimeString(),
    level: 'info',
    message: '单步运行已停止'
  });

  message.info('单步运行已停止');
};

// 运行管道
const handleRun = async () => {
  try {
    running.value = true;
    runningNodes.value = [];
    completedNodes.value = [];
    errorNodes.value = [];
    outputLogs.value = [];
    
    const pipeline: PipelineDAG = {
      nodes: nodes.value,
      edges: edges.value
    };
    
    const response = await runAIPipeline(projectId.value, pipeline);
    runId.value = response.run_id;

    // 开始轮询日志
    pollLogs();
  } catch (error) {
    console.error('运行失败:', error);
    message.error('运行失败，请检查管道配置');
    running.value = false;
  }
};

// 停止运行
const handleStop = async () => {
  try {
    // 停止普通运行
    if (running.value) {
      await stopAIRun(runId.value);
      running.value = false;
    }

    // 停止单步运行
    if (singleStepState.value.isActive) {
      stopSingleStep();
    }

    message.success('已停止运行');
  } catch (error) {
    console.error('停止失败:', error);
    message.error('停止失败');
  }
};

// 轮询日志（带防抖优化）
let pollTimeout: number | null = null;

const pollLogs = async () => {
  if (!running.value) return;

  try {
    const logs = await getAIRunLogs(runId.value);
    outputLogs.value = logs;
    
    // 更新节点状态（兼容不同的nodeId格式和缺失nodeId的情况）
    logs.forEach(log => {
      // 如果有nodeId，使用精确匹配
      if (log.nodeId) {
        // 标准化nodeId格式（移除时间戳后缀，只保留前缀）
        let normalizedNodeId = log.nodeId;
        if (log.nodeId.startsWith('node_')) {
          // 如果是简单格式，尝试匹配现有节点
          const matchingNode = nodes.value.find(node => node.id.startsWith(log.nodeId));
          if (matchingNode) {
            normalizedNodeId = matchingNode.id;
          }
        }

        if (log.level === 'running') {
          // 只有不在运行列表中才添加
          if (!runningNodes.value.includes(normalizedNodeId)) {
            runningNodes.value.push(normalizedNodeId);
          }
          // 从完成和错误列表中移除
          completedNodes.value = completedNodes.value.filter(id => id !== normalizedNodeId);
          errorNodes.value = errorNodes.value.filter(id => id !== normalizedNodeId);
        } else if (log.level === 'success') {
          // 从运行列表中移除
          runningNodes.value = runningNodes.value.filter(id => id !== normalizedNodeId);
          // 添加到完成列表（避免重复）
          if (!completedNodes.value.includes(normalizedNodeId)) {
            completedNodes.value.push(normalizedNodeId);
          }
          // 从错误列表中移除
          errorNodes.value = errorNodes.value.filter(id => id !== normalizedNodeId);
        } else if (log.level === 'error') {
          // 从运行列表中移除
          runningNodes.value = runningNodes.value.filter(id => id !== normalizedNodeId);
          // 从完成列表中移除
          completedNodes.value = completedNodes.value.filter(id => id !== normalizedNodeId);
          // 添加到错误列表（避免重复）
          if (!errorNodes.value.includes(normalizedNodeId)) {
            errorNodes.value.push(normalizedNodeId);
          }
        }
      } else {
        // 如果没有nodeId，根据消息内容推断状态
        if (log.level === 'running' && log.message.includes('started')) {
          // Pipeline启动，将所有节点标记为运行中
          nodes.value.forEach(node => {
            if (!runningNodes.value.includes(node.id)) {
              runningNodes.value.push(node.id);
            }
          });
        } else if (log.message.includes('completed') || log.message.includes('finished')) {
          // Pipeline完成，将所有节点标记为完成
          nodes.value.forEach(node => {
            runningNodes.value = runningNodes.value.filter(id => id !== node.id);
            if (!completedNodes.value.includes(node.id)) {
              completedNodes.value.push(node.id);
            }
          });
        }
      }
    });
    
    // 检查是否完成
    if (logs.some(log => log.message.includes('Pipeline completed'))) {
      running.value = false;
      message.success('运行完成');
      return;
    }
    
    // 继续轮询（使用防抖优化）
    if (pollTimeout) {
      clearTimeout(pollTimeout);
    }
    pollTimeout = window.setTimeout(pollLogs, 1000);
  } catch (error) {
    console.error('获取日志失败:', error);
  }
};

// 保存管道
const handleSave = async () => {
  try {
    saving.value = true;
    
    const pipeline: PipelineDAG = {
      nodes: nodes.value,
      edges: edges.value
    };
    
    await saveAIPipeline(projectId.value, pipeline);
    message.success('保存成功');
  } catch (error) {
    console.error('保存失败:', error);
    message.error('保存失败');
  } finally {
    saving.value = false;
  }
};

// 获取实训手册
const fetchManual = async () => {
  try {
    manualContent.value = await getTrainingManual(projectId.value);
  } catch (error) {
    console.error('获取实训手册失败:', error);
  }
};

// 返回
const goBack = () => {
  router.push('/project');
};

// 监听面板切换，自动获取模型库数据
watch(leftPanelTab, (newTab) => {
  if (newTab === 'models') {
    fetchModelList();
  }
});

// 生命周期
onMounted(() => {
  fetchManual();
  loadTrainingDatasets();
  loadSavedPipeline();
  // 添加全局键盘快捷键监听
  document.addEventListener('keydown', handleGlobalKeydown);
});

onUnmounted(() => {
  // 移除全局键盘快捷键监听
  document.removeEventListener('keydown', handleGlobalKeydown);

  // 清理轮询定时器
  if (pollTimeout) {
    clearTimeout(pollTimeout);
    pollTimeout = null;
  }
});
</script>

<style scoped>
.ai-designer-page {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  background: #f0f2f5;
}

.designer-header {
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-name {
  font-size: 16px;
  font-weight: 500;
  color: #262626;
}

.zoom-level {
  padding: 0 8px;
  color: #595959;
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;
  min-height: 0;
}

.operator-panel {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.operator-categories {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.operator-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.operator-item {
  padding: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: move;
  text-align: center;
  transition: all 0.3s;
  background: #fafafa;
}

.operator-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.operator-icon {
  font-size: 20px;
  color: #1890ff;
  display: block;
  margin-bottom: 4px;
}

.operator-name {
  font-size: 12px;
  color: #595959;
}

.canvas-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  min-width: 0;
  min-height: 0;
}

.flow-canvas {
  flex: 1;
  position: relative;
  overflow: auto;
  cursor: grab;
  min-height: 0;
}

.flow-canvas:active {
  cursor: grabbing;
}

.flow-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  transform-origin: top left;
}

.flow-edge {
  stroke: #b8b8b8;
  stroke-width: 2;
  fill: none;
  cursor: pointer;
  transition: stroke 0.3s;
}

.flow-edge:hover,
.flow-edge.selected {
  stroke: #1890ff;
  stroke-width: 3;
}

.nodes-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transform-origin: top left;
}

.flow-node {
  position: absolute;
  width: 160px;
  background: #fff;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  cursor: move;
  transition: all 0.3s;
  user-select: none;
}

.flow-node.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.2);
}

.flow-node.running {
  border-color: #faad14;
  animation: pulse 1s infinite;
}

.flow-node.completed {
  border-color: #52c41a;
}

.flow-node.error {
  border-color: #ff4d4f;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(250, 173, 20, 0.4); }
  70% { box-shadow: 0 0 0 10px rgba(250, 173, 20, 0); }
  100% { box-shadow: 0 0 0 0 rgba(250, 173, 20, 0); }
}

.node-header {
  padding: 12px;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  gap: 8px;
}

.node-icon {
  font-size: 16px;
  color: #1890ff;
}

.node-title {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-ports {
  position: relative;
  height: 20px;
}

.port {
  position: absolute;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #1890ff;
  cursor: crosshair;
  transition: all 0.3s;
}

.port:hover {
  transform: scale(1.2);
  box-shadow: 0 0 0 4px rgba(24, 144, 255, 0.2);
}

.port-input {
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.port-output {
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
}

.node-status {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 16px;
}

.temp-connection {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.log-panel {
  background: #fff;
  border-top: 1px solid #e8e8e8;
  transition: height 0.3s;
  height: 48px;
  flex-shrink: 0;
}

.log-panel.expanded {
  height: 300px;
}

.log-header {
  height: 48px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  border-bottom: 1px solid #e8e8e8;
}

.log-content {
  height: calc(100% - 48px);
  overflow: hidden;
}

.log-tabs {
  height: 100%;
}

.log-list {
  height: calc(100% - 46px);
  overflow-y: auto;
  padding: 8px 16px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}

.log-item {
  margin-bottom: 4px;
  display: flex;
  gap: 8px;
}

.log-time {
  color: #8c8c8c;
}

.log-level {
  font-weight: 600;
  min-width: 60px;
}

.log-level.level-info { color: #1890ff; }
.log-level.level-running { color: #faad14; }
.log-level.level-success { color: #52c41a; }
.log-level.level-error { color: #ff4d4f; }

.log-message {
  flex: 1;
  color: #262626;
}

.config-panel {
  width: 320px;
  flex-shrink: 0;
  height: 100%;
  background: #fff;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.config-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.floating-buttons {
  position: fixed;
  right: 24px;
  bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.manual-btn {
  width: 56px;
  height: 56px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.manual-content {
  padding: 16px;
  line-height: 1.8;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
  padding: 8px 12px !important;
}

:deep(.ant-collapse-content-box) {
  padding: 8px !important;
}

/* 用户引导和反馈样式 */
.operator-tip {
  display: inline-block;
}

.empty-canvas {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #999;
  z-index: 10;
}

.empty-content {
  max-width: 400px;
}

.empty-icon {
  font-size: 48px;
  color: #d9d9d9;
  margin-bottom: 16px;
}

.empty-content h3 {
  color: #666;
  margin-bottom: 8px;
}

.empty-content p {
  color: #999;
  margin-bottom: 24px;
}

.empty-steps {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-top: 16px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.step-number {
  display: inline-block;
  width: 24px;
  height: 24px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  text-align: center;
  line-height: 24px;
  font-size: 12px;
  font-weight: 500;
}

.running-indicator {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 12px 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
}

.running-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.running-content span {
  font-weight: 500;
  color: #1890ff;
}

.running-stats {
  display: flex;
  gap: 16px;
  margin-left: 12px;
  font-size: 12px;
  color: #666;
}

.running-stats span {
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
}

:deep(.ant-tabs) {
  height: 100%;
}

:deep(.ant-tabs-content) {
  height: 100%;
}

/* 快捷键提示面板 */
.keyboard-hints-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  background: rgba(255, 255, 255, 0.98);
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  min-width: 220px;
  backdrop-filter: blur(8px);
}

.hints-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  border-radius: 8px 8px 0 0;
}

.hints-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #262626;
}

.hints-content {
  padding: 8px 0;
}

.hint-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  transition: background-color 0.2s;
}

.hint-item:hover {
  background: #f5f5f5;
}

.hint-item kbd {
  background: #f6f6f6;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.1);
}

.hint-item span {
  font-size: 13px;
  color: #595959;
}

/* 新增样式 - 模式切换Tab */
.mode-tabs {
  display: flex;
  gap: 0;
  background: #f5f5f5;
  border-radius: 4px;
  padding: 2px;
}

.mode-tab {
  padding: 6px 24px;
  font-size: 14px;
  cursor: pointer;
  color: #595959;
  border-radius: 3px;
  transition: all 0.2s;
}

.mode-tab.active {
  background: #fff;
  color: #1890ff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.mode-tab:hover:not(.active) {
  color: #1890ff;
}

/* 流程名称 */
.flow-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  margin-right: 24px;
}

/* 工具栏操作 */
.toolbar-actions {
  display: flex;
  align-items: center;
}

.header-center {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
}

/* 左侧面板Tab */
.panel-tabs {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
}

.panel-tab {
  flex: 1;
  padding: 12px 16px;
  text-align: center;
  cursor: pointer;
  color: #595959;
  font-size: 14px;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.panel-tab.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
}

.panel-tab:hover:not(.active) {
  color: #1890ff;
}

/* 面板内容 */
.panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.category-filter {
  padding: 12px 12px 8px;
}

.search-box {
  padding: 0 12px 12px;
}

/* 算子树 */
.operator-tree {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.tree-category {
  display: flex;
  align-items: center;
  font-weight: 500;
  color: #262626;
}

.tree-operator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  cursor: move;
  border-radius: 4px;
  transition: background 0.2s;
}

.tree-operator:hover {
  background: rgba(24, 144, 255, 0.1);
}

/* 模型库样式 */
.model-toolbar {
  padding: 12px 12px 8px;
}

.model-search {
  padding: 0 12px 8px;
}

.model-filter {
  padding: 0 12px 12px;
}

.model-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.model-item {
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: background 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.model-item:hover {
  background: rgba(24, 144, 255, 0.08);
}

.model-item-content {
  width: 100%;
}

.model-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
}

.model-meta {
  display: flex;
  gap: 4px;
  margin-bottom: 4px;
}

.model-desc {
  font-size: 12px;
  color: #8c8c8c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 4px;
}

.model-time {
  font-size: 12px;
  color: #bfbfbf;
}

.tree-operator .op-icon {
  color: #1890ff;
  font-size: 14px;
}

/* 洞察Tab样式 */
.insight-content {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.insight-overview {
  margin-bottom: 16px;
}

.insight-card {
  border-radius: 6px;
}

.insight-metrics {
  margin-bottom: 16px;
}

.insight-metrics h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.metric-item {
  padding: 8px 0;
}

.metric-label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #595959;
}

.sample-info {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 4px;
  font-size: 12px;
  color: #8c8c8c;
}

.insight-nodes {
  margin-bottom: 16px;
}

.insight-nodes h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.insight-suggestions h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

/* 底部流程标签页 */
.flow-tabs {
  height: 36px;
  flex-shrink: 0;
  background: #fafafa;
  border-top: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.flow-tabs-left {
  display: flex;
  gap: 2px;
}

.flow-tab-list {
  flex: 1;
  display: flex;
  overflow-x: auto;
  gap: 2px;
  padding: 0 8px;
  scrollbar-width: none;
}

.flow-tab-list::-webkit-scrollbar {
  display: none;
}

.flow-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 4px 4px 0 0;
  cursor: pointer;
  font-size: 12px;
  color: #595959;
  white-space: nowrap;
  transition: all 0.2s;
}

.flow-tab:hover {
  background: #e6f7ff;
}

.flow-tab.active {
  background: #fff;
  color: #1890ff;
  border-color: #1890ff;
  border-bottom-color: #fff;
}

.flow-tab .close-btn {
  font-size: 10px;
  opacity: 0.6;
  margin-left: 4px;
}

.flow-tab .close-btn:hover {
  opacity: 1;
  color: #ff4d4f;
}

/* 日志面板更新 */
.log-header {
  height: 36px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
  border-top: 1px solid #e8e8e8;
  cursor: default;
}

.log-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #595959;
  font-size: 13px;
}

.log-toggle:hover {
  color: #1890ff;
}

/* 实训手册悬浮按钮 */
.manual-floating-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
}

.manual-btn-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
  color: #fff;
  border-radius: 8px 0 0 8px;
  cursor: pointer;
  font-size: 12px;
  box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
}

.manual-btn-content:hover {
  padding-right: 16px;
}

.manual-btn-content span {
  writing-mode: vertical-rl;
}

/* Ant Design Tree 样式覆盖 */
:deep(.ant-tree-title) {
  display: block;
  width: 100%;
}

:deep(.ant-tree-node-content-wrapper) {
  width: 100%;
}

:deep(.ant-tree-treenode) {
  width: 100%;
  padding: 2px 0;
}
</style>
