<template>
  <a-config-provider :theme="lightThemeConfig">
    <div class="bi-designer-page">
    <!-- 顶部工具栏 -->
    <div class="designer-header">
      <div class="header-left">
        <a-tabs v-model:activeKey="headerTab" size="small">
          <a-tab-pane key="query" tab="数据查询" />
          <a-tab-pane key="design" tab="可视化设计" />
        </a-tabs>
      </div>

      <div class="header-right">
        <a-button v-if="!isReadOnly" @click="handleSave" :loading="saving">
          <SaveOutlined /> 保存
        </a-button>
        <a-button
          v-if="canSubmitAssignment"
          type="primary"
          @click="handleSubmitAssignment"
          :loading="submittingAssignment"
        >
          <UploadOutlined /> 提交作业
        </a-button>
        <a-button @click="handlePreview">
          <EyeOutlined /> 预览
        </a-button>
        <a-dropdown>
          <a-button>
            <CameraOutlined /> 快照 <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu @click="handleSnapshotMenu">
              <a-menu-item key="png">导出为PNG</a-menu-item>
              <a-menu-item key="jpg">导出为JPG</a-menu-item>
              <a-menu-item key="pdf">导出为PDF</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-tooltip title="切换主题">
          <a-button type="text" @click="toggleTheme">
            <BgColorsOutlined />
          </a-button>
        </a-tooltip>
        <a-avatar :src="userStore.userInfo.avatar" size="small" />
        <a-tooltip title="帮助">
          <a-button type="text">
            <QuestionCircleOutlined />
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="designer-body">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 数据源/图层切换 -->
        <div class="panel-tabs">
          <a-tabs v-model:activeKey="leftPanelTab" size="small">
            <a-tab-pane key="data" tab="数据" />
            <a-tab-pane key="layer" tab="图层" />
          </a-tabs>
        </div>

        <!-- 数据源面板 -->
        <div v-if="leftPanelTab === 'data'" class="data-panel">
          <div class="add-data-btn">
            <a-button type="link" size="small">
              <PlusOutlined /> 添加数据
            </a-button>
          </div>
          <div class="data-source-list">
            <a-select
              v-model:value="selectedDataSource"
              :loading="datasetsLoading"
              placeholder="选择数据集"
              style="width: 100%"
            >
              <a-select-option v-if="datasetsLoading" value="">
                数据集加载中...
              </a-select-option>
              <a-select-option v-else-if="datasets.length === 0" value="">
                暂无可用数据集
              </a-select-option>
              <a-select-option
                v-for="dataset in datasets"
                :key="dataset.id"
                :value="dataset.id"
              >
                {{ dataset.name }}
              </a-select-option>
            </a-select>
            <div v-if="selectedDataset" class="dataset-summary">
              <div class="dataset-name">{{ selectedDataset.name }}</div>
              <div class="dataset-description">{{ selectedDataset.description || '暂无描述' }}</div>
              <div class="dataset-meta">
                {{ formatDatasetSize(selectedDataset.size) }} · {{ selectedDataset.path }}
              </div>
            </div>
            <a-alert
              v-else-if="datasetLoadError"
              type="warning"
              :message="datasetLoadError"
              show-icon
              class="dataset-alert"
            />
          </div>
          <div class="field-search">
            <a-input-search placeholder="搜索表格字段名称" size="small" />
          </div>
          <div v-if="selectedDatasetFields.length > 0" class="field-list">
            <div class="field-list-title">字段</div>
            <div
              v-for="field in selectedDatasetFields"
              :key="field.name"
              class="field-item"
              :data-field-name="field.name"
            >
              <span class="field-name">{{ field.name }}</span>
              <span class="field-type">{{ field.type }}</span>
            </div>
          </div>
        </div>

        <!-- 图层面板 -->
        <div v-if="leftPanelTab === 'layer'" class="layer-panel">
          <div class="layer-list">
            <div v-for="(item, index) in canvasItems" :key="item.id" class="layer-item" @click="selectItem(item)">
              <span>{{ item.name || '图层 ' + (index + 1) }}</span>
              <EyeOutlined v-if="item.visible !== false" />
              <EyeInvisibleOutlined v-else />
            </div>
            <div v-if="canvasItems.length === 0" class="empty-layer">
              暂无图层
            </div>
          </div>
        </div>

        <!-- 图表组件面板 -->
        <div class="component-section">
          <div class="section-title">图表</div>

          <!-- 常用图形 -->
          <div class="component-group">
            <div class="group-title">常用图形</div>
            <div class="component-grid">
              <div
                v-for="comp in commonCharts"
                :key="comp.type"
                class="comp-item"
                draggable="true"
                @dragstart="handleDragStart($event, comp)"
              >
                <component :is="comp.icon" />
              </div>
            </div>
          </div>

          <!-- 地理图形 -->
          <div class="component-group">
            <div class="group-title">地理图形</div>
            <div class="component-grid">
              <div
                v-for="comp in geoCharts"
                :key="comp.type"
                class="comp-item"
                draggable="true"
                @dragstart="handleDragStart($event, comp)"
              >
                <component :is="comp.icon" />
              </div>
            </div>
          </div>

          <!-- 配置区域 -->
          <div class="config-section">
            <div class="section-title">配置</div>
            <a-form layout="vertical" size="small">
              <a-form-item label="自动出图">
                <a-checkbox v-model:checked="autoRender">启用</a-checkbox>
              </a-form-item>
              <a-form-item label="展示类型">
                <a-select v-model:value="displayType" style="width: 100%">
                  <a-select-option value="default">默认</a-select-option>
                  <a-select-option value="full">全屏</a-select-option>
                </a-select>
              </a-form-item>
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-form-item label="宽度">
                    <a-input-number v-model:value="canvasWidth" :min="800" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="高度">
                    <a-input-number v-model:value="canvasHeight" :min="600" style="width: 100%" />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-form-item label="尺寸模式">
                <a-select v-model:value="sizeMode" style="width: 100%">
                  <a-select-option value="auto">适应</a-select-option>
                  <a-select-option value="fixed">固定</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="显示方式">
                <a-select v-model:value="displayMode" style="width: 100%">
                  <a-select-option value="fit">实际大小</a-select-option>
                  <a-select-option value="cover">铺满</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item>
                <a-checkbox v-model:checked="showBgColor">背景补色</a-checkbox>
              </a-form-item>
              <a-form-item>
                <a-checkbox v-model:checked="showGrid">显示网格线</a-checkbox>
              </a-form-item>
            </a-form>
          </div>
        </div>

        <!-- 参数区域 -->
        <div class="params-section">
          <div class="section-title">参数</div>
          <div class="toolbar-mode">
            <span class="label">工具栏显示模式</span>
            <a-radio-group v-model:value="toolbarMode" size="small">
              <a-radio-button value="light">浅色模式</a-radio-button>
              <a-radio-button value="dark">深色模式</a-radio-button>
            </a-radio-group>
          </div>
          <div class="toolbar-icons">
            <a-tooltip title="日历"><a-button type="text" size="small"><CalendarOutlined /></a-button></a-tooltip>
            <a-tooltip title="表格"><a-button type="text" size="small"><TableOutlined /></a-button></a-tooltip>
            <a-tooltip title="缩放"><a-button type="text" size="small"><FullscreenOutlined /></a-button></a-tooltip>
            <a-tooltip title="分享"><a-button type="text" size="small"><ShareAltOutlined /></a-button></a-tooltip>
            <a-tooltip title="编辑"><a-button type="text" size="small"><EditOutlined /></a-button></a-tooltip>
            <a-tooltip title="刷新"><a-button type="text" size="small"><ReloadOutlined /></a-button></a-tooltip>
          </div>
          <a-form-item>
            <a-checkbox v-model:checked="showToolbar">显示网格线</a-checkbox>
          </a-form-item>
        </div>
      </div>

      <!-- 中间画布区域 -->
      <div class="canvas-area">
        <!-- 画布工具栏 -->
        <div class="canvas-toolbar">
          <a-space>
            <a-input-group compact size="small">
              <a-input v-model:value="canvasX" prefix="X:" style="width: 80px" />
              <a-input v-model:value="canvasY" prefix="Y:" style="width: 80px" />
            </a-input-group>
            <a-input-group compact size="small">
              <a-input v-model:value="canvasW" prefix="W:" style="width: 80px" />
              <a-input v-model:value="canvasH" prefix="H:" style="width: 80px" />
            </a-input-group>
          </a-space>
          <div class="toolbar-center">
            <!-- 对齐工具 -->
          </div>
          <a-space>
            <a-button size="small" @click="handleZoomOut">
              <ZoomOutOutlined />
            </a-button>
            <span class="zoom-level">{{ Math.round(zoomLevel * 100) }}%</span>
            <a-button size="small" @click="handleZoomIn">
              <ZoomInOutlined />
            </a-button>
            <a-button size="small" @click="handleZoomReset">
              <FullscreenOutlined />
            </a-button>
          </a-space>
        </div>

        <!-- 画布主体 -->
        <div class="canvas-wrapper" ref="canvasWrapper">
          <div
            class="design-canvas"
            :class="{ 'show-grid': showGrid }"
            :style="{
              width: canvasWidth + 'px',
              height: canvasHeight + 'px',
              transform: `scale(${zoomLevel})`,
              background: isDarkTheme ? 'linear-gradient(135deg, #f5f7fa 0%, #e8f0fe 100%)' : '#ffffff'
            }"
            @drop="handleDrop"
            @dragover.prevent
          >
            <!-- 深色主题装饰 -->
            <div v-if="isDarkTheme" class="canvas-decoration">
              <div class="corner-decoration top-left"></div>
              <div class="corner-decoration top-right"></div>
              <div class="corner-decoration bottom-left"></div>
              <div class="corner-decoration bottom-right"></div>
            </div>

            <!-- 空状态提示 -->
            <div v-if="canvasItems.length === 0" class="empty-canvas">
              <div class="empty-content">
                <BarChartOutlined class="empty-icon" />
                <h3>开始创建仪表板</h3>
                <p>从左侧组件库拖拽图表组件到此处，构建数据可视化看板</p>
                <div class="empty-steps">
                  <div class="step"><span class="step-number">1</span><span>拖拽图表组件</span></div>
                  <div class="step"><span class="step-number">2</span><span>配置数据源</span></div>
                  <div class="step"><span class="step-number">3</span><span>调整样式布局</span></div>
                </div>
              </div>
            </div>

            <!-- 渲染的组件 -->
            <div
              v-for="item in canvasItems"
              :key="item.id"
              class="canvas-item"
              :class="{ 'selected': selectedItem?.id === item.id }"
              :style="{
                left: item.position.x + 'px',
                top: item.position.y + 'px',
                width: item.size.width + 'px',
                height: item.size.height + 'px'
              }"
              @click="selectItem(item)"
              @mousedown="startDrag($event, item)"
            >
              <div class="item-header" v-if="item.title">{{ item.title }}</div>
              <div class="item-content">
                <BiChartRenderer
                  v-if="isChartType(item.type)"
                  :type="item.type"
                  :width="item.size.width - 4"
                  :height="item.size.height - (item.title ? 44 : 4)"
                  :data="item.chartData || []"
                  :title="item.title"
                  :color="item.props?.color || '#1890ff'"
                  :x-field="item.config?.xField"
                  :y-field="item.config?.yField"
                />
                <div v-else class="placeholder-content">
                  {{ item.name }}
                </div>
              </div>
              <div class="resize-handles" v-if="selectedItem?.id === item.id">
                <div class="resize-handle nw" @mousedown.stop="startResize($event, 'nw', item)"></div>
                <div class="resize-handle ne" @mousedown.stop="startResize($event, 'ne', item)"></div>
                <div class="resize-handle sw" @mousedown.stop="startResize($event, 'sw', item)"></div>
                <div class="resize-handle se" @mousedown.stop="startResize($event, 'se', item)"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 底部场景标签页 -->
        <div class="scene-tabs">
          <div class="scene-tab-list">
            <div
              v-for="scene in scenes"
              :key="scene.id"
              class="scene-tab"
              :class="{ active: currentSceneId === scene.id }"
              @click="switchScene(scene.id)"
            >
              <FileOutlined />
              <span>{{ scene.name }}</span>
              <CloseOutlined v-if="scenes.length > 1" class="close-btn" @click.stop="removeScene(scene.id)" />
            </div>
            <div class="scene-tab add-tab" @click="addScene">
              <PlusOutlined />
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="right-panel" v-show="selectedItem || showRightPanel">
        <div class="panel-header">
          <span>{{ selectedItem ? '组件属性' : '画布属性' }}</span>
        </div>

        <div class="panel-content">
          <!-- 组件属性 -->
          <template v-if="selectedItem">
            <a-form layout="vertical" size="small">
              <a-form-item label="组件标题">
                <a-input v-model:value="selectedItem.title" placeholder="输入标题" />
              </a-form-item>

              <a-divider>位置尺寸</a-divider>
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-form-item label="X">
                    <a-input-number v-model:value="selectedItem.position.x" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="Y">
                    <a-input-number v-model:value="selectedItem.position.y" style="width: 100%" />
                  </a-form-item>
                </a-col>
              </a-row>
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-form-item label="宽度">
                    <a-input-number v-model:value="selectedItem.size.width" :min="50" style="width: 100%" />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="高度">
                    <a-input-number v-model:value="selectedItem.size.height" :min="50" style="width: 100%" />
                  </a-form-item>
                </a-col>
              </a-row>

              <a-divider>数据配置</a-divider>
              <a-form-item label="数据源">
                <a-select
                  v-model:value="selectedItem.dataSource"
                  placeholder="选择数据源"
                  @change="refreshSelectedItemData"
                >
                  <a-select-option
                    v-for="dataset in datasets"
                    :key="dataset.id"
                    :value="dataset.id"
                  >
                    {{ dataset.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="X 轴字段">
                <a-select
                  v-model:value="selectedItem.config.xField"
                  placeholder="选择维度字段"
                  @change="refreshSelectedItemData"
                >
                  <a-select-option
                    v-for="field in fieldsForItem(selectedItem)"
                    :key="field.name"
                    :value="field.name"
                  >
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="Y 轴字段">
                <a-select
                  v-model:value="selectedItem.config.yField"
                  placeholder="选择指标字段"
                  @change="refreshSelectedItemData"
                >
                  <a-select-option
                    v-for="field in numericFieldsForItem(selectedItem)"
                    :key="field.name"
                    :value="field.name"
                  >
                    {{ field.name }}
                  </a-select-option>
                </a-select>
              </a-form-item>

              <a-divider>样式配置</a-divider>
              <a-form-item label="背景颜色">
                <a-input v-model:value="selectedItem.props.backgroundColor" type="color" />
              </a-form-item>
              <a-form-item label="边框样式">
                <a-select v-model:value="selectedItem.props.borderStyle">
                  <a-select-option value="none">无边框</a-select-option>
                  <a-select-option value="solid">实线</a-select-option>
                  <a-select-option value="dashed">虚线</a-select-option>
                </a-select>
              </a-form-item>
              <a-form-item label="透明度">
                <a-slider v-model:value="selectedItem.props.opacity" :min="0" :max="100" />
              </a-form-item>
            </a-form>

            <div class="panel-actions">
              <a-button danger block @click="deleteSelectedItem">
                <DeleteOutlined /> 删除组件
              </a-button>
            </div>
          </template>

          <!-- 画布属性 -->
          <template v-else>
            <a-form layout="vertical" size="small">
              <a-form-item label="画布宽度">
                <a-input-number v-model:value="canvasWidth" :min="800" style="width: 100%" />
              </a-form-item>
              <a-form-item label="画布高度">
                <a-input-number v-model:value="canvasHeight" :min="600" style="width: 100%" />
              </a-form-item>
              <a-form-item label="背景样式">
                <a-select v-model:value="canvasBgStyle" style="width: 100%">
                  <a-select-option value="dark">深蓝科技风</a-select-option>
                  <a-select-option value="light">简约白色</a-select-option>
                  <a-select-option value="gradient">渐变色</a-select-option>
                </a-select>
              </a-form-item>
            </a-form>
          </template>
        </div>
      </div>
    </div>

    <!-- 实训手册浮动按钮 -->
    <div class="manual-floating-btn" @click="openManual">
      <div class="manual-btn-content">
        <BookOutlined />
        <span>实训手册</span>
      </div>
    </div>

    <!-- 实训手册弹窗 -->
    <a-modal
      v-model:open="showManual"
      title="实训手册"
      width="900px"
      :footer="null"
      centered
      class="manual-modal"
    >
      <div class="manual-layout">
        <!-- 左侧目录 -->
        <div class="manual-sidebar">
          <div class="sidebar-title">目录</div>
          <a-menu
            v-model:selectedKeys="manualSelectedKeys"
            mode="inline"
            :inline-collapsed="false"
          >
            <a-menu-item key="1-intro">
              <span>1 项目简介</span>
            </a-menu-item>
            <a-sub-menu key="1-1" title="1.1 分析目标">
              <a-menu-item key="1-1-1">分析目标详情</a-menu-item>
            </a-sub-menu>
            <a-sub-menu key="1-2" title="1.2 项目收益">
              <a-menu-item key="1-2-1">收益说明</a-menu-item>
            </a-sub-menu>
            <a-menu-item key="2-understand">
              <span>2 业务理解</span>
            </a-menu-item>
            <a-menu-item key="3-data">
              <span>3 数据理解</span>
            </a-menu-item>
            <a-menu-item key="4-thinking">
              <span>4 分析思路</span>
            </a-menu-item>
            <a-sub-menu key="5" title="5 分析过程">
              <a-sub-menu key="5-1" title="5.1 数据准备">
                <a-menu-item key="5-1-1">5.1.1 添加数据</a-menu-item>
                <a-menu-item key="5-1-2">5.1.2 数据预览</a-menu-item>
              </a-sub-menu>
              <a-sub-menu key="5-2" title="5.2 数据可视化">
                <a-menu-item key="5-2-1">5.2.1 网站运营数据分析</a-menu-item>
                <a-menu-item key="5-2-2">5.2.2 网站访客分析</a-menu-item>
              </a-sub-menu>
              <a-menu-item key="5-3">5.3 页面美化</a-menu-item>
            </a-sub-menu>
            <a-menu-item key="6-report">
              <span>6 分析报告</span>
            </a-menu-item>
            <a-menu-item key="7-value">
              <span>7 应用价值</span>
            </a-menu-item>
          </a-menu>
        </div>

        <!-- 右侧内容 -->
        <div class="manual-content">
          <div class="content-header">
            <a-breadcrumb>
              <a-breadcrumb-item>项目实训</a-breadcrumb-item>
              <a-breadcrumb-item>开始实训</a-breadcrumb-item>
              <a-breadcrumb-item>文档简介</a-breadcrumb-item>
            </a-breadcrumb>
            <a-button type="link" @click="showManual = false">返回上一页</a-button>
          </div>
          <div class="content-body" v-html="manualContent"></div>
        </div>
      </div>
    </a-modal>

    <!-- 预览弹窗 -->
    <a-modal
      v-model:open="showPreview"
      title="场景预览"
      width="95%"
      :footer="null"
      centered
    >
      <div class="preview-container">
        <iframe :src="previewUrl" frameborder="0" style="width: 100%; height: 85vh;"></iframe>
      </div>
    </a-modal>
    </div>
  </a-config-provider>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, theme } from 'ant-design-vue';
import BiChartRenderer from '@/components/BiChartRenderer.vue';
import {
  ArrowLeftOutlined,
  SaveOutlined,
  UploadOutlined,
  EyeOutlined,
  CameraOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  BookOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  AreaChartOutlined,
  RadarChartOutlined,
  HeatMapOutlined,
  DashboardOutlined,
  TableOutlined,
  QuestionCircleOutlined,
  PlusOutlined,
  DownOutlined,
  BgColorsOutlined,
  EyeInvisibleOutlined,
  CalendarOutlined,
  FullscreenOutlined,
  ShareAltOutlined,
  EditOutlined,
  ReloadOutlined,
  FileOutlined,
  CloseOutlined,
  DeleteOutlined,
  GlobalOutlined,
  FundOutlined,
  DotChartOutlined,
  BoxPlotOutlined,
  StockOutlined,
  EnvironmentOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import {
  saveBIScene,
  getBIPreviewUrl,
  exportBISnapshot,
  downloadBISnapshot,
  getProjectDetail,
  getProjectDatasets,
  getBISceneDetail
} from '@/api/training';
import type { Dataset, SceneJSON } from '@/api/types/project';
import { getToken } from '@/utils/auth';
import { request } from '@/utils/request';

// 强制亮色主题配置
const lightThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorBgContainer: '#ffffff',
    colorBgElevated: '#ffffff',
    colorBgLayout: '#f5f5f5',
    colorText: '#262626',
    colorTextSecondary: '#595959',
    colorBorder: '#d9d9d9',
  },
  algorithm: theme.defaultAlgorithm,
};

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

type BIDatasetField = {
  name: string;
  type: string;
  semanticType?: string;
};

type RichBIDataset = Dataset & {
  columns?: Array<string | BIDatasetField>;
  data?: Record<string, any>[];
  totalRows?: number;
};

// 基础状态
const resolveProjectId = () => (
  (route.params.trainingId as string)
  || (route.params.id as string)
  || (route.query.projectId as string)
  || '1'
);
const projectId = ref(resolveProjectId());
const isClassroomContext = computed(() => Boolean(route.params.classroomId && route.params.trainingId));
const isReadOnly = computed(() => !isClassroomContext.value);
const canSubmitAssignment = computed(() => {
  const role = String(userStore.userInfo?.role || '').toLowerCase();
  return isClassroomContext.value && role === 'student';
});
const saving = ref(false);
const submittingAssignment = ref(false);
const showManual = ref(false);
const showPreview = ref(false);
const previewUrl = ref('');
const manualContent = ref('');
const manualSelectedKeys = ref(['1-intro']);

// 面板状态
const headerTab = ref('design');
const leftPanelTab = ref('data');
const showRightPanel = ref(true);

// 主题（固定亮色）
const isDarkTheme = ref(false);
const toolbarMode = ref('light');

// 数据源
const selectedDataSource = ref<number | string>('');
const datasets = ref<RichBIDataset[]>([]);
const datasetsLoading = ref(false);
const datasetLoadError = ref('');
const selectedDataset = computed(() => (
  datasets.value.find(dataset => dataset.id === Number(selectedDataSource.value))
));
const selectedDatasetFields = computed(() => getDatasetFields(selectedDataset.value));

// 画布配置
const canvasWidth = ref(1920);
const canvasHeight = ref(1080);
const zoomLevel = ref(0.5);
const showGrid = ref(false);
const autoRender = ref(true);
const displayType = ref('default');
const sizeMode = ref('auto');
const displayMode = ref('fit');
const showBgColor = ref(false);
const showToolbar = ref(true);
const canvasBgStyle = ref('dark');

// 坐标显示
const canvasX = ref(0);
const canvasY = ref(0);
const canvasW = ref(1920);
const canvasH = ref(1080);

// 场景管理
const scenes = ref([
  { id: 'scene1', name: '场景1' },
  { id: 'scene2', name: '场景1' },
  { id: 'word1', name: 'word模板1' },
  { id: 'scene3', name: '场景2' },
  { id: 'report1', name: '报表1' }
]);
const currentSceneId = ref('scene1');

// 画布元素
const canvasItems = ref<any[]>([]);
const selectedItem = ref<any>(null);
const draggedComponent = ref<any>(null);
const canvasWrapper = ref<HTMLElement | null>(null);

// 常用图表组件
const commonCharts = ref([
  { type: 'bar-chart', name: '柱状图', icon: BarChartOutlined },
  { type: 'line-chart', name: '折线图', icon: LineChartOutlined },
  { type: 'area-chart', name: '面积图', icon: AreaChartOutlined },
  { type: 'pie-chart', name: '饼图', icon: PieChartOutlined },
  { type: 'scatter', name: '散点图', icon: DotChartOutlined },
  { type: 'radar-chart', name: '雷达图', icon: RadarChartOutlined },
  { type: 'funnel', name: '漏斗图', icon: FundOutlined },
  { type: 'gauge', name: '仪表盘', icon: DashboardOutlined },
  { type: 'boxplot', name: '箱线图', icon: BoxPlotOutlined },
  { type: 'kline', name: 'K线图', icon: StockOutlined },
  { type: 'table', name: '表格', icon: TableOutlined },
  { type: 'heatmap', name: '热力图', icon: HeatMapOutlined }
]);

// 地理图表组件
const geoCharts = ref([
  { type: 'china-map', name: '中国地图', icon: GlobalOutlined },
  { type: 'world-map', name: '世界地图', icon: GlobalOutlined },
  { type: 'province-map', name: '省份地图', icon: EnvironmentOutlined },
  { type: 'scatter-map', name: '散点地图', icon: DotChartOutlined },
  { type: 'flow-map', name: '迁徙图', icon: FundOutlined },
  { type: 'heat-map-geo', name: '热力地图', icon: HeatMapOutlined }
]);

// 拖拽功能
const handleDragStart = (event: DragEvent, component: any) => {
  draggedComponent.value = component;
  event.dataTransfer!.effectAllowed = 'copy';
};

const handleDrop = (event: DragEvent) => {
  event.preventDefault();

  if (!draggedComponent.value) return;

  const canvas = event.currentTarget as HTMLElement;
  const rect = canvas.getBoundingClientRect();
  const x = (event.clientX - rect.left) / zoomLevel.value;
  const y = (event.clientY - rect.top) / zoomLevel.value;

  const isChart = isChartType(draggedComponent.value.type);

  const newItem: any = {
    id: `comp_${Date.now()}`,
    type: draggedComponent.value.type,
    name: draggedComponent.value.name,
    title: draggedComponent.value.name,
    position: { x: Math.max(0, x - 150), y: Math.max(0, y - 100) },
    size: { width: 400, height: 300 },
    props: {
      backgroundColor: 'transparent',
      borderStyle: 'solid',
      opacity: 100,
      color: '#1890ff'
    },
    dataSource: 'static',
    visible: true,
    config: {}
  };

  // 图表类型添加默认数据和特殊配置
  if (isChart) {
    applyDatasetToChartItem(newItem);
    newItem.size = { width: 500, height: 350 };
    newItem.title = draggedComponent.value.name;
  }

  canvasItems.value.push(newItem);
  selectedItem.value = newItem;
  draggedComponent.value = null;

  message.success(`已添加${newItem.name}`);
};

const normalizeRowKeys = (row: Record<string, any>) => {
  const normalized: Record<string, any> = {};
  Object.keys(row || {}).forEach(key => {
    normalized[key.replace(/^\uFEFF/, '')] = row[key];
  });
  return normalized;
};

const normalizeColumn = (column: string | BIDatasetField, rows: Record<string, any>[] = []): BIDatasetField => {
  if (typeof column !== 'string') {
    return {
      name: column.name.replace(/^\uFEFF/, ''),
      type: column.type || 'string',
      semanticType: column.semanticType
    };
  }

  const name = column.replace(/^\uFEFF/, '');
  const sampleValue = rows.find(row => row[name] !== undefined && row[name] !== null && row[name] !== '')?.[name];
  const isNumber = sampleValue !== undefined && sampleValue !== '' && Number.isFinite(Number(sampleValue));
  return {
    name,
    type: isNumber ? 'number' : 'string',
    semanticType: isNumber ? 'quantitative' : 'nominal'
  };
};

const getDatasetRows = (dataset?: RichBIDataset) => (
  (dataset?.data || []).map(normalizeRowKeys)
);

const getDatasetFields = (dataset?: RichBIDataset): BIDatasetField[] => {
  if (!dataset) return [];
  const rows = getDatasetRows(dataset);
  if (dataset.columns && dataset.columns.length > 0) {
    return dataset.columns.map(column => normalizeColumn(column, rows));
  }
  if (rows.length === 0) return [];
  return Object.keys(rows[0]).map(column => normalizeColumn(column, rows));
};

const getDatasetById = (datasetId: number | string) => (
  datasets.value.find(dataset => dataset.id === Number(datasetId))
);

const fieldsForItem = (item: any) => getDatasetFields(getDatasetById(item?.dataSource || selectedDataSource.value));

const numericFieldsForItem = (item: any) => {
  const dataset = getDatasetById(item?.dataSource || selectedDataSource.value);
  const fields = getDatasetFields(dataset);
  const rows = getDatasetRows(dataset);
  const numericFields = fields.filter(field => (
    field.type === 'number'
    || field.semanticType === 'quantitative'
    || rows.some(row => row[field.name] !== '' && row[field.name] !== null && Number.isFinite(Number(row[field.name])))
  ));
  return numericFields.length > 0 ? numericFields : fields;
};

const pickDefaultXField = (dataset?: RichBIDataset) => {
  const fields = getDatasetFields(dataset);
  const numericNames = new Set(
    fields.filter(field => field.type === 'number' || field.semanticType === 'quantitative').map(field => field.name)
  );
  return fields.find(field => !numericNames.has(field.name))?.name || fields[0]?.name || 'category';
};

const pickDefaultYField = (dataset?: RichBIDataset) => {
  const fields = getDatasetFields(dataset);
  const rows = getDatasetRows(dataset);
  return fields.find(field => (
    field.type === 'number'
    || field.semanticType === 'quantitative'
    || rows.some(row => row[field.name] !== '' && row[field.name] !== null && Number.isFinite(Number(row[field.name])))
  ))?.name || fields[1]?.name || fields[0]?.name || 'value';
};

const buildChartData = (dataset: RichBIDataset | undefined, xField: string, yField: string, type: string) => {
  const rows = getDatasetRows(dataset).filter(row => row[xField] !== undefined && row[yField] !== undefined);
  const limitedRows = rows.slice(0, type === 'scatter' ? 80 : 30);

  if (type === 'pie-chart' || type === 'funnel') {
    const grouped = new Map<string, number>();
    rows.forEach(row => {
      const category = String(row[xField] ?? '未命名');
      const value = Number(row[yField]);
      grouped.set(category, (grouped.get(category) || 0) + (Number.isFinite(value) ? value : 1));
    });
    return Array.from(grouped.entries()).slice(0, 12).map(([category, value]) => ({ category, value }));
  }

  return limitedRows.map(row => ({
    ...row,
    [xField]: row[xField],
    [yField]: Number.isFinite(Number(row[yField])) ? Number(row[yField]) : row[yField],
    category: row[xField],
    value: Number.isFinite(Number(row[yField])) ? Number(row[yField]) : 0
  }));
};

const applyDatasetToChartItem = (item: any) => {
  const dataset = getDatasetById(item.dataSource || selectedDataSource.value) || selectedDataset.value || datasets.value[0];
  if (!dataset) {
    item.chartData = [];
    return;
  }

  item.dataSource = dataset.id;
  item.config = item.config || {};
  item.config.datasetId = dataset.id;
  item.config.datasetName = dataset.name;
  item.config.xField = item.config.xField || pickDefaultXField(dataset);
  item.config.yField = item.config.yField || pickDefaultYField(dataset);
  item.chartData = buildChartData(dataset, item.config.xField, item.config.yField, item.type);
};

const refreshSelectedItemData = () => {
  if (!selectedItem.value || !isChartType(selectedItem.value.type)) return;
  const dataset = getDatasetById(selectedItem.value.dataSource || selectedDataSource.value);
  if (dataset) {
    const availableFieldNames = new Set(getDatasetFields(dataset).map(field => field.name));
    if (!availableFieldNames.has(selectedItem.value.config?.xField)) {
      selectedItem.value.config.xField = pickDefaultXField(dataset);
    }
    if (!availableFieldNames.has(selectedItem.value.config?.yField)) {
      selectedItem.value.config.yField = pickDefaultYField(dataset);
    }
  }
  applyDatasetToChartItem(selectedItem.value);
};

const createAutoChartFromDataset = () => {
  if (!autoRender.value || canvasItems.value.length > 0 || datasets.value.length === 0) return;
  const dataset = selectedDataset.value || datasets.value[0];
  const newItem: any = {
    id: `auto_${projectId.value}_${Date.now()}`,
    type: 'bar-chart',
    name: '真实数据柱状图',
    title: `${dataset.name} - ${pickDefaultYField(dataset)}`,
    position: { x: 120, y: 100 },
    size: { width: 620, height: 380 },
    props: {
      backgroundColor: 'transparent',
      borderStyle: 'solid',
      opacity: 100,
      color: '#1890ff'
    },
    dataSource: dataset.id,
    visible: true,
    config: {
      datasetId: dataset.id,
      datasetName: dataset.name,
      xField: pickDefaultXField(dataset),
      yField: pickDefaultYField(dataset)
    }
  };
  applyDatasetToChartItem(newItem);
  canvasItems.value.push(newItem);
  selectedItem.value = newItem;
};

// 选择组件
const selectItem = (item: any) => {
  selectedItem.value = item;
};

// 删除组件
const deleteSelectedItem = () => {
  if (!selectedItem.value) return;
  const index = canvasItems.value.findIndex(item => item.id === selectedItem.value.id);
  if (index > -1) {
    canvasItems.value.splice(index, 1);
    selectedItem.value = null;
    message.success('组件已删除');
  }
};

// 拖拽移动组件
const startDrag = (event: MouseEvent, item: any) => {
  if (event.target !== event.currentTarget) return;

  const startX = event.clientX;
  const startY = event.clientY;
  const startPosX = item.position.x;
  const startPosY = item.position.y;

  const onMove = (e: MouseEvent) => {
    const dx = (e.clientX - startX) / zoomLevel.value;
    const dy = (e.clientY - startY) / zoomLevel.value;
    item.position.x = Math.max(0, startPosX + dx);
    item.position.y = Math.max(0, startPosY + dy);
  };

  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };

  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};

// 调整大小
const startResize = (event: MouseEvent, handle: string, item: any) => {
  const startX = event.clientX;
  const startY = event.clientY;
  const startW = item.size.width;
  const startH = item.size.height;
  const startPosX = item.position.x;
  const startPosY = item.position.y;

  const onMove = (e: MouseEvent) => {
    const dx = (e.clientX - startX) / zoomLevel.value;
    const dy = (e.clientY - startY) / zoomLevel.value;

    if (handle.includes('e')) {
      item.size.width = Math.max(50, startW + dx);
    }
    if (handle.includes('w')) {
      item.size.width = Math.max(50, startW - dx);
      item.position.x = startPosX + dx;
    }
    if (handle.includes('s')) {
      item.size.height = Math.max(50, startH + dy);
    }
    if (handle.includes('n')) {
      item.size.height = Math.max(50, startH - dy);
      item.position.y = startPosY + dy;
    }
  };

  const onUp = () => {
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onUp);
  };

  document.addEventListener('mousemove', onMove);
  document.addEventListener('mouseup', onUp);
};

// 缩放功能
const handleZoomIn = () => {
  zoomLevel.value = Math.min(zoomLevel.value + 0.1, 2);
};

const handleZoomOut = () => {
  zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.2);
};

const handleZoomReset = () => {
  zoomLevel.value = 0.5;
};

// 主题切换（已移除暗色主题，保持亮色）
const toggleTheme = () => {
  // 暗色主题已移除，保持亮色
  console.log('暗色主题已移除，仅支持亮色模式');
};

// 场景管理
const switchScene = (sceneId: string) => {
  currentSceneId.value = sceneId;
};

const addScene = () => {
  const newScene = {
    id: `scene_${Date.now()}`,
    name: `场景${scenes.value.length + 1}`
  };
  scenes.value.push(newScene);
  currentSceneId.value = newScene.id;
};

const removeScene = (sceneId: string) => {
  if (scenes.value.length <= 1) return;
  const index = scenes.value.findIndex(s => s.id === sceneId);
  if (index > -1) {
    scenes.value.splice(index, 1);
    if (currentSceneId.value === sceneId) {
      currentSceneId.value = scenes.value[0].id;
    }
  }
};

// 获取组件
const chartTypes = [
  'bar-chart', 'line-chart', 'area-chart', 'pie-chart', 'scatter',
  'radar-chart', 'funnel', 'gauge', 'heatmap', 'table',
  'boxplot', 'kline', 'china-map', 'world-map', 'province-map',
  'scatter-map', 'flow-map', 'heat-map-geo'
];

const isChartType = (type: string) => chartTypes.includes(type);

const getComponentByType = (type: string) => {
  if (isChartType(type)) {
    return BiChartRenderer;
  }
  return 'div';
};

const buildSceneData = (): SceneJSON => ({
  nodes: canvasItems.value,
  links: [],
  props: {
    title: '可视化场景',
    theme: isDarkTheme.value ? 'dark' : 'light',
    backgroundColor: isDarkTheme.value ? '#f5f7fa' : '#ffffff',
    width: canvasWidth.value,
    height: canvasHeight.value
  },
  training_id: Number(route.params.trainingId),
  classroom_id: Number(route.params.classroomId)
} as SceneJSON);

// 保存场景
const handleSave = async () => {
  if (isReadOnly.value) {
    message.warning('请从课堂中打开实训才能保存');
    return;
  }

  try {
    saving.value = true;

    const sceneData = buildSceneData();
    await saveBIScene(projectId.value, sceneData);
    message.success('保存成功');
  } catch (error) {
    console.error('保存失败:', error);
    message.error('保存失败，请重试');
  } finally {
    saving.value = false;
  }
};

// 预览
const handlePreview = async () => {
  try {
    previewUrl.value = await getBIPreviewUrl(projectId.value);
    const sceneData = {
      nodes: canvasItems.value,
      links: [],
      props: {
        title: '可视化场景',
        theme: isDarkTheme.value ? 'dark' : 'light',
        backgroundColor: isDarkTheme.value ? '#f5f7fa' : '#ffffff',
        width: canvasWidth.value,
        height: canvasHeight.value
      }
    };
    localStorage.setItem(`bi_preview_${projectId.value}`, JSON.stringify(sceneData));

    const previewTarget = new URL(previewUrl.value, window.location.origin);
    const hashUrl = `${window.location.origin}/#${previewTarget.pathname}${previewTarget.search}`;
    window.open(hashUrl, '_blank');
  } catch (error) {
    console.error('获取预览URL失败:', error);
    message.error('预览失败，请重试');
  }
};

// 快照
const handleSnapshotMenu = async ({ key }: { key: string }) => {
  try {
    message.loading({ content: '正在生成快照...', key: 'snapshot' });

    // 先导出
    await exportBISnapshot(projectId.value, key);

    // 然后下载
    await downloadBISnapshot(projectId.value);

    message.success({ content: `已导出为${key.toUpperCase()}格式`, key: 'snapshot' });
  } catch (error) {
    console.error('保存快照失败:', error);
    message.error({ content: '保存快照失败，请重试', key: 'snapshot' });
  }
};

// 打开手册
const openManual = () => {
  showManual.value = true;
};

// 获取实训手册
const fetchManual = async () => {
  try {
    const projectDetail = await getProjectDetail(projectId.value);
    if (projectDetail.manualSections && projectDetail.manualSections.length > 0) {
      let content = '<div class="manual-sections">';
      projectDetail.manualSections.forEach((section: any) => {
        content += `<h2>${section.title}</h2>`;
        content += `<div>${section.content}</div>`;
      });
      content += '</div>';
      manualContent.value = content;
    } else {
      manualContent.value = getDefaultManualContent();
    }
  } catch (error) {
    console.error('获取实训手册失败:', error);
    manualContent.value = getDefaultManualContent();
  }
};

const getDefaultManualContent = () => {
  return `
    <h2>1 项目简介</h2>
    <p>几年前，马云曾经说过："互联网已经从IT时代向DT时代迈进"。或许，关于互联网是否DT时代尚无定论，但是，DT时代所依托的大数据分析却已经得到了共识。</p>
    <p>有一个笑话，就是在微信朋友圈曾发过了朋友几天可以的动态之后，一度引起了大家对朋友及朋友的议论。其实，这下重要，真正重要的是微信运营团队几乎一个重要的数据没有提供给用户，那就是每天有多少人访问过你，当然，这个数据微信没有奉出来。而微信之所以推出朋友发圈功能，是有大量数据依托的，你不是大家所议论的那样简单。</p>

    <h3>1.1 分析目标</h3>
    <p>网站相关的数据来源与类型是非常多的，本案例中通过对某企业官方网站的访客来源、地域、搜索引擎与每日获客广告花费等数据的分析，来指导运营人员的工作方向。</p>
    <p>主要有以下几个方面：</p>
    <ol>
      <li>用户都是通过什么搜索引擎来访问网站的，各个搜索引擎对网站访客的贡献度、访客忠诚度如何？</li>
      <li>影响网站获取有效线索数量的原因是什么？</li>
      <li>访问用户集中在哪些区域，通过什么渠道访问的网站？</li>
    </ol>

    <h3>1.2 项目收益</h3>
    <p>通过对本案例数据的分析，得出结论指导运营人员后期的工作侧重点，针对效果好的渠道，搜索引擎作为工作重点，结合实际的业务最大的提升网站对公司业绩的贡献。</p>

    <h2>2 业务理解</h2>
    <p>在互联网时代公司的网站承载了互联网端的曝光，吸引有兴趣与需求的用户前来访问，网站为用户提供有价值的内容或使用户进一步的想要与我们产生联络缓解期获得信息链接...</p>
  `;
};

const formatDatasetSize = (size?: number) => {
  if (!size && size !== 0) return '未知大小';
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
};

const loadDatasets = async () => {
  datasetsLoading.value = true;
  datasetLoadError.value = '';

  try {
    const response = await fetch(`/api/v1/trainings/${projectId.value}/bi-dataset?limit=500`, {
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();
    const richDatasets = result?.code === '0000' ? (result.data?.datasets || []) : [];

    if (richDatasets.length > 0) {
      datasets.value = richDatasets;
    } else {
      const trainingDatasets = await getProjectDatasets(projectId.value);
      datasets.value = trainingDatasets;
    }

    selectedDataSource.value = datasets.value[0]?.id || '';
    createAutoChartFromDataset();
  } catch (error) {
    console.error('加载实训数据集失败:', error);
    datasets.value = [];
    selectedDataSource.value = '';
    datasetLoadError.value = '数据集加载失败';
  } finally {
    datasetsLoading.value = false;
  }
};

const handleSubmitAssignment = async () => {
  if (!canSubmitAssignment.value) {
    message.warning('请从课堂学生端提交作业');
    return;
  }

  try {
    submittingAssignment.value = true;
    const sceneData = buildSceneData();
    await saveBIScene(projectId.value, sceneData);
    const result = await request.post(
      `/api/v1/trainings/${route.params.trainingId}/submit`,
      {
        snapshot_json: sceneData,
        notes: 'Submitted from Tempo BI designer'
      },
      {
        params: {
          classroom_id: Number(route.params.classroomId)
        }
      }
    );

    if (result.code === '0000') {
      message.success('作业提交成功');
    } else {
      message.error(result.message || '提交作业失败');
    }
  } catch (error) {
    console.error('提交作业失败:', error);
    message.error('提交作业失败，请重试');
  } finally {
    submittingAssignment.value = false;
  }
};

const loadSavedScene = async () => {
  if (!isClassroomContext.value || !userStore.userInfo.id) return;

  try {
    const detail = await getBISceneDetail(projectId.value, {
      training_id: Number(route.params.trainingId),
      classroom_id: Number(route.params.classroomId),
      student_id: Number(userStore.userInfo.id)
    });
    const config = detail?.config || detail?.data?.config;
    const nodes = config?.nodes || config?.snapshot?.nodes;
    if (Array.isArray(nodes) && nodes.length > 0) {
      canvasItems.value = nodes;
      selectedItem.value = nodes[0];
      message.info('已恢复上次保存的 BI 场景');
    }
  } catch (error) {
    console.warn('暂无可恢复 BI 场景或恢复失败:', error);
  }
};

const reloadTrainingContext = () => {
  projectId.value = resolveProjectId();
  selectedDataSource.value = '';
  datasets.value = [];
  canvasItems.value = [];
  selectedItem.value = null;
  fetchManual();
  loadDatasets().then(loadSavedScene);
};

// 生命周期
onMounted(() => {
  reloadTrainingContext();
});

watch(
  () => [route.params.id, route.params.trainingId, route.query.projectId],
  () => {
    reloadTrainingContext();
  }
);

watch(selectedDataSource, () => {
  if (selectedItem.value?.dataSource !== selectedDataSource.value) {
    createAutoChartFromDataset();
  }
});
</script>

<style scoped>
.bi-designer-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

/* 顶部工具栏 */
.designer-header {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-left :deep(.ant-tabs-nav) {
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主体区域 */
.designer-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧面板 */
.left-panel {
  width: 260px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.panel-tabs {
  padding: 8px 12px;
  border-bottom: 1px solid #e8e8e8;
}

.data-panel, .layer-panel {
  padding: 12px;
}

.add-data-btn {
  margin-bottom: 8px;
}

.data-source-list {
  margin-bottom: 12px;
}

.field-list {
  margin-top: 10px;
  border: 1px solid #eef1f5;
  border-radius: 4px;
  max-height: 220px;
  overflow: auto;
  background: #fff;
}

.field-list-title {
  padding: 6px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #595959;
  border-bottom: 1px solid #eef1f5;
}

.field-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  font-size: 12px;
  border-bottom: 1px solid #f5f5f5;
}

.field-name {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-type {
  flex: 0 0 auto;
  color: #8c8c8c;
}

.dataset-summary {
  margin-top: 8px;
  padding: 8px;
  background: #f7fbff;
  border: 1px solid #d6e8ff;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
}

.dataset-name {
  color: #1677ff;
  font-weight: 600;
}

.dataset-description,
.dataset-meta {
  margin-top: 4px;
  color: #595959;
  word-break: break-all;
}

.dataset-alert {
  margin-top: 8px;
}

.field-search {
  margin-bottom: 12px;
}

.layer-list {
  min-height: 100px;
}

.layer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.layer-item:hover {
  background: rgba(24, 144, 255, 0.1);
}

.empty-layer {
  text-align: center;
  color: #999;
  padding: 20px;
}

/* 组件区域 */
.component-section {
  padding: 12px;
  border-top: 1px solid #e8e8e8;
}

.section-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #262626;
}

.component-group {
  margin-bottom: 16px;
}

.group-title {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 8px;
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 4px;
}

.comp-item {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  cursor: move;
  transition: all 0.2s;
  font-size: 16px;
  color: #1890ff;
}

.comp-item:hover {
  border-color: #1890ff;
  background: rgba(24, 144, 255, 0.1);
}

/* 配置区域 */
.config-section {
  padding: 12px;
  border-top: 1px solid #e8e8e8;
}

/* 参数区域 */
.params-section {
  padding: 12px;
  border-top: 1px solid #e8e8e8;
}

.toolbar-mode {
  margin-bottom: 12px;
}

.toolbar-mode .label {
  display: block;
  font-size: 12px;
  margin-bottom: 8px;
}

.toolbar-icons {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
}

/* 画布区域 */
.canvas-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #e8e8e8;
  overflow: hidden;
}

.canvas-toolbar {
  height: 40px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
}

.zoom-level {
  font-size: 12px;
  min-width: 40px;
  text-align: center;
}

.canvas-wrapper {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.design-canvas {
  position: relative;
  transform-origin: center center;
  transition: transform 0.2s;
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.design-canvas.show-grid {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px) !important;
  background-size: 20px 20px !important;
}

/* 深色主题装饰 */
.canvas-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.corner-decoration {
  position: absolute;
  width: 60px;
  height: 60px;
  border: 2px solid rgba(0, 200, 255, 0.3);
}

.corner-decoration.top-left {
  top: 10px;
  left: 10px;
  border-right: none;
  border-bottom: none;
}

.corner-decoration.top-right {
  top: 10px;
  right: 10px;
  border-left: none;
  border-bottom: none;
}

.corner-decoration.bottom-left {
  bottom: 10px;
  left: 10px;
  border-right: none;
  border-top: none;
}

.corner-decoration.bottom-right {
  bottom: 10px;
  right: 10px;
  border-left: none;
  border-top: none;
}

/* 空状态 - 在深色画布上显示 */
.empty-canvas {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  z-index: 10;
}

.empty-content {
  max-width: 400px;
}

.empty-icon {
  font-size: 64px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 16px;
}

.empty-content h3 {
  color: rgba(255, 255, 255, 0.9);
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}

.empty-content p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
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
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: #1890ff;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: 500;
}

/* 画布元素 - 在深色画布上显示 */
.canvas-item {
  position: absolute;
  background: rgba(10, 30, 60, 0.85);
  border: 1px solid rgba(0, 200, 255, 0.4);
  border-radius: 4px;
  cursor: move;
  transition: box-shadow 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.canvas-item.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.4), 0 2px 8px rgba(0, 0, 0, 0.3);
}

.item-header {
  padding: 8px 12px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(0, 100, 200, 0.2);
}

.item-content {
  width: 100%;
  height: calc(100% - 40px);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 2px;
}

.placeholder-content {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  text-align: center;
}

/* 调整大小手柄 */
.resize-handles {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
}

.resize-handle {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #1890ff;
  border: 1px solid #fff;
}

.resize-handle.nw { top: 0; left: 0; cursor: nw-resize; }
.resize-handle.ne { top: 0; right: 0; cursor: ne-resize; }
.resize-handle.sw { bottom: 0; left: 0; cursor: sw-resize; }
.resize-handle.se { bottom: 0; right: 0; cursor: se-resize; }

/* 场景标签页 */
.scene-tabs {
  height: 36px;
  background: #fff;
  border-top: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  padding: 0 8px;
}

.scene-tab-list {
  display: flex;
  gap: 2px;
}

.scene-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f5f5f5;
  border-radius: 4px 4px 0 0;
  color: #595959;
  cursor: pointer;
  font-size: 12px;
  border: 1px solid #e8e8e8;
  border-bottom: none;
}

.scene-tab:hover {
  background: #e6f7ff;
}

.scene-tab.active {
  background: #fff;
  color: #1890ff;
  border-color: #1890ff;
}

.scene-tab .close-btn {
  font-size: 10px;
  opacity: 0.6;
}

.scene-tab .close-btn:hover {
  opacity: 1;
}

.scene-tab.add-tab {
  padding: 6px 10px;
}

/* 右侧面板 */
.right-panel {
  width: 280px;
  background: #fff;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #e8e8e8;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.panel-actions {
  padding: 16px;
  border-top: 1px solid #e8e8e8;
}

/* 实训手册浮动按钮 */
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

/* 手册弹窗 */
.manual-modal :deep(.ant-modal-body) {
  padding: 0;
  max-height: 70vh;
  overflow: hidden;
}

.manual-layout {
  display: flex;
  height: 70vh;
}

.manual-sidebar {
  width: 240px;
  background: #fafafa;
  border-right: 1px solid #e8e8e8;
  overflow-y: auto;
}

.sidebar-title {
  padding: 16px;
  font-weight: 600;
  border-bottom: 1px solid #e8e8e8;
}

.manual-sidebar :deep(.ant-menu) {
  border-right: none;
}

.manual-content {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid #e8e8e8;
  background: #fafafa;
}

.content-body {
  padding: 20px;
  line-height: 1.8;
}

.content-body h2 {
  font-size: 18px;
  margin-top: 24px;
  margin-bottom: 12px;
}

.content-body h3 {
  font-size: 16px;
  margin-top: 20px;
  margin-bottom: 10px;
}

.content-body p {
  margin-bottom: 12px;
  text-indent: 2em;
}

.content-body ol, .content-body ul {
  padding-left: 2em;
  margin-bottom: 12px;
}

/* 预览容器 */
.preview-container {
  background: #000;
  border-radius: 4px;
  overflow: hidden;
}

/* 白色主题 - 覆盖Ant Design组件样式 */
.bi-designer-page :deep(.ant-select) {
  background: #fff;
}

.bi-designer-page :deep(.ant-select-selector) {
  background: #fff !important;
  border-color: #d9d9d9 !important;
}

.bi-designer-page :deep(.ant-select-selection-item) {
  color: #262626 !important;
}

.bi-designer-page :deep(.ant-input) {
  background: #fff !important;
  border-color: #d9d9d9 !important;
  color: #262626 !important;
}

.bi-designer-page :deep(.ant-input-search) {
  background: #fff;
}

.bi-designer-page :deep(.ant-input-search .ant-input) {
  background: #fff !important;
}

.bi-designer-page :deep(.ant-input-number) {
  background: #fff !important;
  border-color: #d9d9d9 !important;
}

.bi-designer-page :deep(.ant-input-number-input) {
  background: #fff !important;
  color: #262626 !important;
}

.bi-designer-page :deep(.ant-checkbox-wrapper) {
  color: #262626;
}

.bi-designer-page :deep(.ant-radio-wrapper) {
  color: #262626;
}

.bi-designer-page :deep(.ant-btn) {
  background: #fff;
  border-color: #d9d9d9;
  color: #262626;
}

.bi-designer-page :deep(.ant-btn:hover) {
  border-color: #1890ff;
  color: #1890ff;
}

.bi-designer-page :deep(.ant-btn-primary) {
  background: #1890ff;
  border-color: #1890ff;
  color: #fff;
}

.bi-designer-page :deep(.ant-tabs-tab) {
  color: #595959;
}

.bi-designer-page :deep(.ant-tabs-tab-active .ant-tabs-tab-btn) {
  color: #1890ff;
}

/* 左侧面板表单样式 */
.left-panel :deep(.ant-select-selector) {
  background: #fff !important;
}

.left-panel :deep(.ant-input) {
  background: #fff !important;
}

/* 右侧面板表单样式 */
.right-panel :deep(.ant-select-selector) {
  background: #fff !important;
}

.right-panel :deep(.ant-input-number) {
  background: #fff !important;
}

.right-panel :deep(.ant-input-number-input) {
  background: #fff !important;
}

/* 工具栏坐标输入框 */
.canvas-toolbar :deep(.ant-input) {
  background: #f5f5f5 !important;
  border-color: #e8e8e8 !important;
}

/* 配置区域样式 */
.config-section :deep(.ant-select-selector) {
  background: #fff !important;
}

.config-section :deep(.ant-input-number) {
  background: #fff !important;
}
</style>
