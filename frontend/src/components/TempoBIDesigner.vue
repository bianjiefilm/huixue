<template>
  <div class="tempo-bi-designer">
    <!-- 顶部工具栏 -->
    <div class="bi-toolbar">
      <div class="toolbar-left">
        <a-button type="link" @click="goBack">
          <ArrowLeftOutlined /> 返回
        </a-button>
        <span class="project-title">{{ projectTitle }}</span>
      </div>

      <div class="toolbar-center">
        <a-space>
          <a-tooltip title="保存">
            <a-button @click="handleSave" :loading="saving">
              <SaveOutlined /> 保存
            </a-button>
          </a-tooltip>
          <a-tooltip title="预览">
            <a-button @click="handlePreview">
              <EyeOutlined /> 预览
            </a-button>
          </a-tooltip>
          <a-dropdown>
            <a-button>
              <CameraOutlined /> 快照 <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu @click="({key}) => handleSnapshot(key)">
                <a-menu-item key="png">保存为 PNG</a-menu-item>
                <a-menu-item key="json">保存为 JSON</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
          <a-tooltip title="清空画布">
            <a-button @click="handleClear">
              <DeleteOutlined /> 清空
            </a-button>
          </a-tooltip>
        </a-space>
      </div>

      <div class="toolbar-right">
        <a-dropdown>
          <a-button>
            <BgColorsOutlined /> 主题 <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu @click="({key}) => changeTheme(key)" :selectedKeys="[currentTheme]">
              <a-menu-item key="dark">深色科技风</a-menu-item>
              <a-menu-item key="light">浅色简洁风</a-menu-item>
              <a-menu-item key="blue">商务蓝</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
        <a-avatar size="small" style="margin-left: 12px; cursor: pointer;">
          <UserOutlined />
        </a-avatar>
        <a-tooltip title="帮助">
          <a-button type="text" icon="<QuestionCircleOutlined />" style="margin-left: 8px;" />
        </a-tooltip>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="bi-content" :class="`theme-${currentTheme}`">
      <!-- 左侧组件库 -->
      <div class="components-panel" :style="{ width: componentsPanelWidth + 'px' }">
        <div class="panel-header">
          <span>组件库</span>
          <a-button type="text" size="small" @click="toggleComponentsPanel">
            <MenuFoldOutlined v-if="!componentsPanelCollapsed" />
            <MenuUnfoldOutlined v-else />
          </a-button>
        </div>
        <div class="panel-body" v-show="!componentsPanelCollapsed">
          <!-- 搜索框 -->
          <a-input-search
            v-model:value="componentSearch"
            placeholder="搜索组件..."
            size="small"
            style="margin-bottom: 12px;"
          />

          <!-- 组件分类Tab -->
          <a-tabs v-model:activeKey="componentTab" size="small">
            <a-tab-pane key="charts" tab="图表">
              <div class="component-list">
                <div
                  v-for="comp in filteredChartComponents"
                  :key="comp.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="onDragStart($event, comp)"
                  @click="addComponent(comp)"
                >
                  <component :is="comp.icon" />
                  <span>{{ comp.name }}</span>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="widgets" tab="组件">
              <div class="component-list">
                <div
                  v-for="comp in filteredWidgetComponents"
                  :key="comp.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="onDragStart($event, comp)"
                  @click="addComponent(comp)"
                >
                  <component :is="comp.icon" />
                  <span>{{ comp.name }}</span>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="media" tab="素材">
              <div class="component-list">
                <div
                  v-for="comp in filteredMediaComponents"
                  :key="comp.type"
                  class="component-item"
                  draggable="true"
                  @dragstart="onDragStart($event, comp)"
                  @click="addComponent(comp)"
                >
                  <component :is="comp.icon" />
                  <span>{{ comp.name }}</span>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>
      </div>

      <!-- 分割线 -->
      <div class="resizer-h" @mousedown="startResizeH"></div>

      <!-- 中央画布 -->
      <div class="canvas-area" ref="canvasAreaRef">
        <div
          class="canvas-wrapper"
          :style="canvasStyle"
          @dragover="onCanvasDragOver"
          @drop="onCanvasDrop"
          @click="selectComponent(null)"
        >
          <!-- 网格背景 -->
          <div class="grid-background"></div>

          <!-- 画布上的组件 -->
          <div
            v-for="comp in components"
            :key="comp.id"
            class="canvas-component"
            :class="{ selected: selectedComponentId === comp.id, [comp.type]: true }"
            :style="getComponentStyle(comp)"
            @click.stop="selectComponent(comp.id)"
            @mousedown="onComponentMouseDown($event, comp)"
          >
            <!-- 选中时的控制点 -->
            <template v-if="selectedComponentId === comp.id">
              <div class="resize-handle resize-n" @mousedown.stop="onResizeStart($event, comp, 'n')" />
              <div class="resize-handle resize-s" @mousedown.stop="onResizeStart($event, comp, 's')" />
              <div class="resize-handle resize-e" @mousedown.stop="onResizeStart($event, comp, 'e')" />
              <div class="resize-handle resize-w" @mousedown.stop="onResizeStart($event, comp, 'w')" />
              <div class="resize-handle resize-nw" @mousedown.stop="onResizeStart($event, comp, 'nw')" />
              <div class="resize-handle resize-ne" @mousedown.stop="onResizeStart($event, comp, 'ne')" />
              <div class="resize-handle resize-sw" @mousedown.stop="onResizeStart($event, comp, 'sw')" />
              <div class="resize-handle resize-se" @mousedown.stop="onResizeStart($event, comp, 'se')" />
            </template>

            <!-- ���件内容 -->
            <div class="component-content" :ref="el => setComponentRef(comp.id, el)">
              <component
                :is="getComponentRenderer(comp)"
                v-bind="comp.props"
                :style="comp.style"
              />
            </div>

            <!-- 删除按钮 -->
            <a-button
              v-if="selectedComponentId === comp.id"
              type="text"
              danger
              size="small"
              class="delete-btn"
              @click.stop="deleteComponent(comp.id)"
            >
              <CloseOutlined />
            </a-button>
          </div>

          <!-- 空状态提示 -->
          <a-empty v-if="components.length === 0" description="从左侧拖入组件开始设计" />
        </div>
      </div>

      <!-- 分割线 -->
      <div class="resizer-h" @mousedown="startResizeH"></div>

      <!-- 右侧属性面板 -->
      <div class="property-panel" :style="{ width: propertyPanelWidth + 'px' }">
        <div class="panel-header">
          <span>属性面板</span>
          <a-button type="text" size="small" @click="togglePropertyPanel">
            <MenuFoldOutlined v-if="!propertyPanelCollapsed" />
            <MenuUnfoldOutlined v-else />
          </a-button>
        </div>
        <div class="panel-body" v-show="!propertyPanelCollapsed">
          <!-- 未选中组件 -->
          <a-empty v-if="!selectedComponent" description="选择一个组件查看属性" />

          <!-- 选中组件属性 -->
          <template v-else>
            <!-- 基本属性 -->
            <a-collapse :defaultActiveKey="['basic', 'data', 'style']" ghost>
              <a-collapse-panel key="basic" header="基本属性">
                <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }" size="small">
                  <a-form-item label="标题">
                    <a-input v-model:value="selectedComponent.props.title" @change="updateComponent" />
                  </a-form-item>
                  <a-form-item label="显示标题">
                    <a-switch v-model:value="selectedComponent.props.showTitle" @change="updateComponent" />
                  </a-form-item>
                  <a-form-item label="透明度">
                    <a-slider v-model:value="selectedComponent.props.opacity" :min="0" :max="100" @change="updateComponent" />
                  </a-form-item>
                </a-form>
              </a-collapse-panel>

              <a-collapse-panel key="data" header="数据配置">
                <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }" size="small">
                  <!-- 字段绑定 -->
                  <a-form-item label="X轴/维度">
                    <a-select
                      v-model:value="selectedComponent.props.xField"
                      placeholder="选择字段"
                      allow-clear
                      @change="updateComponent"
                    >
                      <a-select-option v-for="field in dataFields" :key="field" :value="field">
                        {{ field }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="Y轴/度量">
                    <a-select
                      v-model:value="selectedComponent.props.yField"
                      placeholder="选择字段"
                      allow-clear
                      @change="updateComponent"
                    >
                      <a-select-option v-for="field in dataFields" :key="field" :value="field">
                        {{ field }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="聚合方式">
                    <a-select
                      v-model:value="selectedComponent.props.aggregation"
                      @change="updateComponent"
                    >
                      <a-select-option value="sum">求和</a-select-option>
                      <a-select-option value="avg">平均值</a-select-option>
                      <a-select-option value="count">计数</a-select-option>
                      <a-select-option value="max">最大值</a-select-option>
                      <a-select-option value="min">最小值</a-select-option>
                    </a-select>
                  </a-form-item>
                  <!-- 数据集选择 -->
                  <a-form-item label="数据集">
                    <a-select
                      v-model:value="selectedComponent.props.datasetId"
                      @change="updateComponent"
                    >
                      <a-select-option v-for="ds in datasets" :key="ds.id" :value="ds.id">
                        {{ ds.name }}
                      </a-select-option>
                    </a-select>
                  </a-form-item>
                </a-form>
              </a-collapse-panel>

              <a-collapse-panel key="style" header="样式配置">
                <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }" size="small">
                  <a-form-item label="主色调">
                    <div style="display:flex;align-items:center;gap:8px">
                      <input type="color" :value="selectedComponent.props.color" @input="e => { selectedComponent.props.color = e.target.value; updateComponent(); }" style="width:32px;height:32px;border:1px solid #555;border-radius:4px;cursor:pointer;padding:0" />
                      <span style="font-size:12px;color:#999">{{ selectedComponent.props.color }}</span>
                    </div>
                  </a-form-item>
                  <a-form-item label="背景色">
                    <div style="display:flex;align-items:center;gap:8px">
                      <input type="color" :value="selectedComponent.props.bgColor === 'transparent' ? '#000000' : selectedComponent.props.bgColor" @input="e => { selectedComponent.props.bgColor = e.target.value; updateComponent(); }" style="width:32px;height:32px;border:1px solid #555;border-radius:4px;cursor:pointer;padding:0" />
                      <span style="font-size:12px;color:#999">{{ selectedComponent.props.bgColor }}</span>
                    </div>
                  </a-form-item>
                  <a-form-item label="边框色">
                    <div style="display:flex;align-items:center;gap:8px">
                      <input type="color" :value="selectedComponent.props.borderColor" @input="e => { selectedComponent.props.borderColor = e.target.value; updateComponent(); }" style="width:32px;height:32px;border:1px solid #555;border-radius:4px;cursor:pointer;padding:0" />
                      <span style="font-size:12px;color:#999">{{ selectedComponent.props.borderColor }}</span>
                    </div>
                  </a-form-item>
                  <a-form-item label="边框宽度">
                    <a-slider v-model:value="selectedComponent.props.borderWidth" :min="0" :max="10" @change="updateComponent" />
                  </a-form-item>
                  <a-form-item label="圆角">
                    <a-slider v-model:value="selectedComponent.props.borderRadius" :min="0" :max="50" @change="updateComponent" />
                  </a-form-item>
                  <a-form-item label="字体">
                    <a-select v-model:value="selectedComponent.props.fontFamily" @change="updateComponent">
                      <a-select-option value="inherit">默认字体</a-select-option>
                      <a-select-option value="SimHei">黑体</a-select-option>
                      <a-select-option value="Microsoft YaHei">微软雅黑</a-select-option>
                      <a-select-option value="SimSun">宋体</a-select-option>
                    </a-select>
                  </a-form-item>
                  <a-form-item label="字体大小">
                    <a-input-number v-model:value="selectedComponent.props.fontSize" :min="12" :max="72" @change="updateComponent" />
                  </a-form-item>
                </a-form>
              </a-collapse-panel>
            </a-collapse>
          </template>
        </div>
      </div>
    </div>

    <!-- 实训手册悬浮窗按钮 -->
    <div
      class="handbook-float-btn"
      :class="{ expanded: handbookVisible }"
      @click="toggleHandbook"
    >
      <BookOutlined />
      <span v-if="!handbookCollapsed">实训手册</span>
    </div>

    <!-- 实训手册弹窗 -->
    <a-drawer
      v-model:open="handbookVisible"
      title="实训手册"
      placement="right"
      :width="handbookWidth"
      :mask-closable="true"
      class="handbook-drawer"
    >
      <div class="handbook-content">
        <a-spin :spinning="handbookLoading">
          <template v-if="handbookContent">
            <!-- 目录 -->
            <div class="handbook-toc" v-if="handbookToc.length > 0">
              <h4>目录</h4>
              <ul>
                <li v-for="item in handbookToc" :key="item.id">
                  <a @click="scrollToSection(item.id)">{{ item.title }}</a>
                </li>
              </ul>
            </div>
            <!-- 内容 -->
            <div class="handbook-body" v-html="handbookContent"></div>
          </template>
          <a-empty v-else description="暂无手册内容" />
        </a-spin>
      </div>
    </a-drawer>

    <!-- 预览弹窗 -->
    <a-modal
      v-model:open="previewVisible"
      title="预览"
      :width="previewWidth"
      :footer="null"
      class="preview-modal"
    >
      <div class="preview-container" ref="previewContainerRef">
        <!-- 预览内容 -->
      </div>
    </a-modal>

    <!-- 保存成功提示 -->
    <a-modal
      v-model:open="saveSuccessVisible"
      title="提示"
      :mask="false"
      :footer="null"
      :closable="false"
      :width="300"
    >
      <a-result status="success" title="保存成功" sub-title="您的设计已保存" />
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import * as echarts from 'echarts';
import { message, type SelectProps } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  SaveOutlined,
  EyeOutlined,
  CameraOutlined,
  DeleteOutlined,
  BgColorsOutlined,
  DownOutlined,
  UserOutlined,
  QuestionCircleOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  CloseOutlined,
  BookOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  DotChartOutlined,
  RadarChartOutlined,
  HeatMapOutlined,
  BoxPlotOutlined,
  StockOutlined,
  TableOutlined,
  CreditCardOutlined,
  FileTextOutlined,
  FileImageOutlined,
  NumberOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue';
import { v4 as uuidv4 } from 'uuid';

// Props
const props = defineProps({
  trainingId: {
    type: [String, Number],
    required: true
  },
  classroomId: {
    type: [String, Number],
    required: true
  },
  initialData: {
    type: Array,
    default: () => []
  },
  snapshot: {
    type: [Object, Array],
    default: null
  },
  readOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits<{
  (e: 'save', data: any): void
  (e: 'spec-change', spec: any): void
}>();

// Router
const route = useRoute();
const router = useRouter();

// Refs
const canvasAreaRef = ref<HTMLElement | null>(null);
const previewContainerRef = ref<HTMLElement | null>(null);
const componentRefs = ref<Record<string, any>>({});

// State
const projectTitle = ref('可视化分析大屏');
const saving = ref(false);
const currentTheme = ref('dark');
const componentsPanelWidth = ref(220);
const componentsPanelCollapsed = ref(false);
const propertyPanelWidth = ref(280);
const propertyPanelCollapsed = ref(false);
const componentTab = ref('charts');
const componentSearch = ref('');
const components = ref<any[]>([]);
const selectedComponentId = ref<string | null>(null);
const datasets = ref<any[]>([]);
const dataFields = ref<string[]>([]);
const handbookVisible = ref(false);
const handbookCollapsed = ref(false);
const handbookWidth = ref(480);
const handbookLoading = ref(false);
const handbookContent = ref('');
const handbookToc = ref<any[]>([]);
const previewVisible = ref(false);
const previewWidth = ref(1200);
const saveSuccessVisible = ref(false);

// 拖拽状态
let draggingComponent: any = null;
let draggingCompId: string | null = null;
let resizing = ref(false);
let resizingDirection = '';
let resizingComp: any = null;
let resizeStartX = 0;
let resizeStartY = 0;
let resizeStartWidth = 0;
let resizeStartHeight = 0;
let resizeStartLeft = 0;
let resizeStartTop = 0;

// 组件类型定义
interface ComponentType {
  type: string;
  name: string;
  icon: any;
  defaultProps: Record<string, any>;
  defaultSize: { width: number; height: number };
}

const chartComponents: ComponentType[] = [
  { type: 'bar', name: '柱状图', icon: BarChartOutlined, defaultProps: { title: '柱状图', showTitle: true, xField: '', yField: '', aggregation: 'sum', datasetId: 'default', color: '#5470c6', bgColor: 'transparent', borderColor: '#5470c6', borderWidth: 1, borderRadius: 4, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'line', name: '折线图', icon: LineChartOutlined, defaultProps: { title: '折线图', showTitle: true, xField: '', yField: '', datasetId: 'default', aggregation: 'sum', color: '#91cc75', bgColor: 'transparent', borderColor: '#91cc75', borderWidth: 2, borderRadius: 4, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'pie', name: '饼图', icon: PieChartOutlined, defaultProps: { title: '饼图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#fac858', bgColor: 'transparent', borderColor: '#fac858', borderWidth: 1, borderRadius: 4, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 300, height: 300 } },
  { type: 'area', name: '面积图', icon: AreaChartOutlined, defaultProps: { title: '面积图', showTitle: true, xField: '', yField: '', datasetId: 'default', aggregation: 'sum', color: '#ee6666', bgColor: 'transparent', borderColor: '#ee6666', borderWidth: 2, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'scatter', name: '散点图', icon: DotChartOutlined, defaultProps: { title: '散点图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#73c0de', bgColor: 'transparent', borderColor: '#73c0de', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'radar', name: '雷达图', icon: RadarChartOutlined, defaultProps: { title: '雷达图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#3ba272', bgColor: 'transparent', borderColor: '#3ba272', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 300, height: 300 } },
  { type: 'heatmap', name: '热力图', icon: HeatMapOutlined, defaultProps: { title: '热力图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#fc8452', bgColor: 'transparent', borderColor: '#fc8452', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'treemap', name: '矩形树图', icon: StockOutlined, defaultProps: { title: '矩形树图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#9a60b4', bgColor: 'transparent', borderColor: '#9a60b4', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
  { type: 'boxplot', name: '箱线图', icon: BoxPlotOutlined, defaultProps: { title: '箱线图', showTitle: true, xField: '', yField: '', datasetId: 'default', color: '#ea7ccc', bgColor: 'transparent', borderColor: '#ea7ccc', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 400, height: 300 } },
];

const widgetComponents: ComponentType[] = [
  { type: 'card', name: '指标卡片', icon: CreditCardOutlined, defaultProps: { title: '指标', showTitle: true, value: '100', unit: '', color: '#1890ff', bgColor: 'rgba(24,144,255,0.1)', borderColor: '#1890ff', borderWidth: 1, borderRadius: 8, opacity: 100, fontFamily: 'inherit', fontSize: 24 }, defaultSize: { width: 200, height: 120 } },
  { type: 'table', name: '数据表格', icon: TableOutlined, defaultProps: { title: '数据表格', showTitle: true, columns: [], datasetId: '', color: '#333', bgColor: 'transparent', borderColor: '#e8e8e8', borderWidth: 1, opacity: 100, fontFamily: 'inherit', fontSize: 12 }, defaultSize: { width: 400, height: 200 } },
  { type: 'progress', name: '进度条', icon: LoadingOutlined, defaultProps: { title: '进度', showTitle: true, value: 50, max: 100, color: '#52c41a', bgColor: '#f0f0f0', opacity: 100, fontFamily: 'inherit', fontSize: 14 }, defaultSize: { width: 300, height: 40 } },
  { type: 'number', name: '数字翻牌', icon: NumberOutlined, defaultProps: { title: '数值', showTitle: false, value: '1,234', color: '#fff', bgColor: 'transparent', fontFamily: 'inherit', fontSize: 48 }, defaultSize: { width: 150, height: 80 } },
];

const mediaComponents: ComponentType[] = [
  { type: 'text', name: '文本', icon: FileTextOutlined, defaultProps: { title: '文本', showTitle: false, content: '请输入文本', color: '#fff', bgColor: 'transparent', fontFamily: 'Microsoft YaHei', fontSize: 16, opacity: 100 }, defaultSize: { width: 200, height: 40 } },
  { type: 'image', name: '图片', icon: FileImageOutlined, defaultProps: { title: '图片', showTitle: false, src: '', opacity: 100 }, defaultSize: { width: 200, height: 150 } },
];

// Computed
const filteredChartComponents = computed(() => {
  if (!componentSearch.value) return chartComponents;
  return chartComponents.filter(c => c.name.includes(componentSearch.value));
});

const filteredWidgetComponents = computed(() => {
  if (!componentSearch.value) return widgetComponents;
  return widgetComponents.filter(c => c.name.includes(componentSearch.value));
});

const filteredMediaComponents = computed(() => {
  if (!componentSearch.value) return mediaComponents;
  return mediaComponents.filter(c => c.name.includes(componentSearch.value));
});

const selectedComponent = computed(() => {
  if (!selectedComponentId.value) return null;
  return components.value.find(c => c.id === selectedComponentId.value);
});

const canvasStyle = computed(() => ({
  width: '100%',
  height: '100%',
  background: currentTheme.value === 'dark'
    ? 'linear-gradient(90deg, rgba(30,40,60,0.3) 1px, transparent 1px), linear-gradient(rgba(30,40,60,0.3) 1px, transparent 1px)'
    : 'linear-gradient(90deg, rgba(200,200,200,0.3) 1px, transparent 1px), linear-gradient(rgba(200,200,200,0.3) 1px, transparent 1px)',
  backgroundSize: '20px 20px'
}));

const saveStatusClass = computed(() => 'saved');

// Methods
const goBack = () => {
  router.back();
};

const toggleComponentsPanel = () => {
  componentsPanelCollapsed.value = !componentsPanelCollapsed.value;
};

const togglePropertyPanel = () => {
  propertyPanelCollapsed.value = !propertyPanelCollapsed.value;
};

const startResizeH = (e: MouseEvent) => {
  const startX = e.clientX;
  const startWidth = componentsPanelWidth.value;

  const onMouseMove = (e: MouseEvent) => {
    const diff = startX - e.clientX;
    componentsPanelWidth.value = Math.max(150, Math.min(400, startWidth + diff));
  };

  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  };

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
};

const onDragStart = (e: DragEvent, comp: ComponentType) => {
  draggingComponent = comp;
  e.dataTransfer?.setData('application/json', JSON.stringify(comp));
};

const onCanvasDragOver = (e: DragEvent) => {
  e.preventDefault();
};

const onCanvasDrop = (e: DragEvent) => {
  e.preventDefault();
  if (!draggingComponent) return;

  const rect = canvasAreaRef.value?.getBoundingClientRect();
  if (!rect) return;

  addComponentAt(draggingComponent, e.clientX - rect.left, e.clientY - rect.top);
  draggingComponent = null;
};

const addComponent = (comp: ComponentType) => {
  const newComp = createComponent(comp);
  components.value.push(newComp);
  selectedComponentId.value = newComp.id;
  renderComponent(newComp.id);
};

const addComponentAt = (comp: ComponentType, x: number, y: number) => {
  const newComp = createComponent(comp);
  newComp.x = Math.max(0, x - comp.defaultSize.width / 2);
  newComp.y = Math.max(0, y - comp.defaultSize.height / 2);
  components.value.push(newComp);
  selectedComponentId.value = newComp.id;
  renderComponent(newComp.id);
};

const createComponent = (compTemplate: ComponentType) => {
  const id = uuidv4();
  return {
    id,
    type: compTemplate.type,
    name: compTemplate.name,
    x: 100,
    y: 100,
    width: compTemplate.defaultSize.width,
    height: compTemplate.defaultSize.height,
    props: { ...compTemplate.defaultProps },
    style: {}
  };
};

const getComponentStyle = (comp: any) => ({
  left: `${comp.x}px`,
  top: `${comp.y}px`,
  width: `${comp.width}px`,
  height: `${comp.height}px`,
  opacity: comp.props.opacity / 100
});

const selectComponent = (id: string | null) => {
  selectedComponentId.value = id;
};

const deleteComponent = (id: string) => {
  const index = components.value.findIndex(c => c.id === id);
  if (index > -1) {
    components.value.splice(index, 1);
  }
  if (selectedComponentId.value === id) {
    selectedComponentId.value = null;
  }
};

const updateComponent = () => {
  if (selectedComponentId.value) {
    renderComponent(selectedComponentId.value);
    emit('spec-change', getSpec());
  }
};

const setComponentRef = (id: string, el: any) => {
  if (el) componentRefs.value[id] = el;
};

const getComponentRenderer = (comp: any) => {
  return {
    template: `<div class="chart-container" style="width:100%;height:100%"></div>`,
    setup() {
      return {};
    }
  };
};

// 组件拖拽移动
let movingComp: any = null;
let moveStartX = 0;
let moveStartY = 0;
let moveStartLeft = 0;
let moveStartTop = 0;

const onComponentMouseDown = (e: MouseEvent, comp: any) => {
  if (resizing.value) return;

  movingComp = comp;
  moveStartX = e.clientX;
  moveStartY = e.clientY;
  moveStartLeft = comp.x;
  moveStartTop = comp.y;

  const onMouseMove = (e: MouseEvent) => {
    const dx = e.clientX - moveStartX;
    const dy = e.clientY - moveStartY;
    comp.x = Math.max(0, moveStartLeft + dx);
    comp.y = Math.max(0, moveStartTop + dy);
  };

  const onMouseUp = () => {
    movingComp = null;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    emit('spec-change', getSpec());
  };

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
};

// 组件缩放
const onResizeStart = (e: MouseEvent, comp: any, direction: string) => {
  e.preventDefault();
  e.stopPropagation();

  resizing.value = true;
  resizingDirection = direction;
  resizingComp = comp;
  resizeStartX = e.clientX;
  resizeStartY = e.clientY;
  resizeStartWidth = comp.width;
  resizeStartHeight = comp.height;
  resizeStartLeft = comp.x;
  resizeStartTop = comp.y;

  const onMouseMove = (e: MouseEvent) => {
    const dx = e.clientX - resizeStartX;
    const dy = e.clientY - resizeStartY;

    if (direction.includes('e')) {
      comp.width = Math.max(100, resizeStartWidth + dx);
    }
    if (direction.includes('w')) {
      const newWidth = Math.max(100, resizeStartWidth - dx);
      comp.x = resizeStartLeft + resizeStartWidth - newWidth;
      comp.width = newWidth;
    }
    if (direction.includes('s')) {
      comp.height = Math.max(60, resizeStartHeight + dy);
    }
    if (direction.includes('n')) {
      const newHeight = Math.max(60, resizeStartHeight - dy);
      comp.y = resizeStartTop + resizeStartHeight - newHeight;
      comp.height = newHeight;
    }

    renderComponent(comp.id);
  };

  const onMouseUp = () => {
    resizing.value = false;
    resizingComp = null;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
    emit('spec-change', getSpec());
  };

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
};

const renderComponent = (id: string) => {
  nextTick(() => {
    const comp = components.value.find(c => c.id === id);
    if (!comp) return;

    const container = componentRefs.value[id]?.querySelector('.chart-container');
    if (!container) return;

    // 根据组件类型渲染
    if (['bar', 'line', 'pie', 'area', 'scatter', 'radar', 'heatmap', 'treemap', 'boxplot'].includes(comp.type)) {
      renderChart(container, comp);
    } else if (comp.type === 'card') {
      renderCard(container, comp);
    } else if (comp.type === 'table') {
      renderTable(container, comp);
    } else if (comp.type === 'progress') {
      renderProgress(container, comp);
    } else if (comp.type === 'number') {
      renderNumber(container, comp);
    } else if (comp.type === 'text') {
      renderText(container, comp);
    } else if (comp.type === 'image') {
      renderImage(container, comp);
    }
  });
};

const renderChart = (container: HTMLElement, comp: any) => {
  let chart = echarts.getInstanceByDom(container);
  if (!chart) {
    chart = echarts.init(container);
  }

  // 获取数据
  let data: any[] = [];
  if (comp.props.datasetId && props.initialData.length > 0) {
    data = props.initialData;
  } else {
    // 生成示例数据
    data = generateSampleData(comp);
  }

  // 根据字段聚合数据
  const aggregatedData = aggregateData(data, comp.props.xField, comp.props.yField, comp.props.aggregation);

  // 构建图表配置
  const option = buildChartOption(comp, aggregatedData);
  chart.setOption(option, true);

  // 响应式
  const resizeObserver = new ResizeObserver(() => {
    chart?.resize();
  });
  resizeObserver.observe(container);
};

const generateSampleData = (comp: any) => {
  const categories = ['北京', '上海', '广州', '深圳', '杭州', '成都'];
  return categories.map(cat => ({
    [comp.props.xField || '城市']: cat,
    [comp.props.yField || '销售额']: Math.floor(Math.random() * 10000) + 1000
  }));
};

const aggregateData = (data: any[], xField: string, yField: string, aggregation: string) => {
  if (!xField || !yField || data.length === 0) {
    return data.slice(0, 10);
  }

  const grouped: Record<string, number> = {};
  data.forEach(row => {
    const key = String(row[xField] || '未知');
    const value = Number(row[yField]) || 0;
    if (!grouped[key]) grouped[key] = 0;

    switch (aggregation) {
      case 'sum': grouped[key] += value; break;
      case 'avg': grouped[key] = ((grouped[key] || 0) + value) / 2; break;
      case 'count': grouped[key] = (grouped[key] || 0) + 1; break;
      case 'max': grouped[key] = Math.max(grouped[key] || 0, value); break;
      case 'min': grouped[key] = grouped[key] ? Math.min(grouped[key], value) : value; break;
      default: grouped[key] += value;
    }
  });

  return Object.entries(grouped).map(([name, value]) => ({ [xField]: name, [yField]: value }));
};

const buildChartOption = (comp: any, data: any[]) => {
  const xField = comp.props.xField || 'category';
  const yField = comp.props.yField || 'value';

  // 根据当前主题动态设置颜色
  const isDark = ['dark', 'tech-blue'].includes(currentTheme.value);
  const axisLabelColor = isDark ? '#ccc' : '#555';
  const splitLineColor = isDark ? '#333' : '#e0e0e0';
  const titleColor = isDark ? (comp.props.color || '#fff') : (comp.props.color || '#333');
  const radarAxisNameColor = isDark ? '#ccc' : '#555';
  const radarSplitAreaColors = isDark
    ? ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.05)']
    : ['rgba(0,0,0,0.02)', 'rgba(0,0,0,0.05)'];

  const commonOption = {
    title: {
      show: comp.props.showTitle,
      text: comp.props.title,
      left: 'center',
      textStyle: { color: titleColor, fontSize: 14 }
    },
    grid: { top: comp.props.showTitle ? 40 : 20, right: 20, bottom: 30, left: 50, containLabel: true },
    tooltip: { trigger: 'item' },
    textStyle: { fontFamily: comp.props.fontFamily }
  };

  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'];

  switch (comp.type) {
    case 'bar':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor } },
        yAxis: { type: 'value', axisLabel: { color: axisLabelColor }, splitLine: { lineStyle: { color: splitLineColor } } },
        series: [{ type: 'bar', data: data.map(d => d[yField]), itemStyle: { color: comp.props.color, borderRadius: [comp.props.borderRadius, comp.props.borderRadius, 0, 0] } }]
      };
    case 'line':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor } },
        yAxis: { type: 'value', axisLabel: { color: axisLabelColor }, splitLine: { lineStyle: { color: splitLineColor } } },
        series: [{ type: 'line', data: data.map(d => d[yField]), smooth: true, itemStyle: { color: comp.props.color }, areaStyle: { color: comp.props.color, opacity: 0.3 } }]
      };
    case 'pie':
      return {
        ...commonOption,
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        series: [{ type: 'pie', radius: '60%', data: data.map((d, i) => ({ name: d[xField], value: d[yField], itemStyle: { color: colors[i % colors.length] } })), center: ['50%', '55%'] }]
      };
    case 'area':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor } },
        yAxis: { type: 'value', axisLabel: { color: axisLabelColor }, splitLine: { lineStyle: { color: splitLineColor } } },
        series: [{ type: 'line', data: data.map(d => d[yField]), smooth: true, itemStyle: { color: comp.props.color }, areaStyle: { color: comp.props.color, opacity: 0.3 } }]
      };
    case 'scatter':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor } },
        yAxis: { type: 'value', axisLabel: { color: axisLabelColor }, splitLine: { lineStyle: { color: splitLineColor } } },
        series: [{ type: 'scatter', data: data.map(d => ({ value: [d[xField], d[yField]] })), itemStyle: { color: comp.props.color } }]
      };
    case 'radar':
      return {
        ...commonOption,
        radar: { indicator: data.map(d => ({ name: d[xField], max: d[yField] * 1.2 })), axisName: { color: radarAxisNameColor }, splitArea: { areaStyle: { color: radarSplitAreaColors } } },
        series: [{ type: 'radar', data: [{ name: comp.props.title, value: data.map(d => d[yField]), areaStyle: { color: comp.props.color, opacity: 0.3 } }] }]
      };
    case 'heatmap':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor, rotate: 30 } },
        yAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor }, splitLine: { show: false } },
        visualMap: { min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: 0, inRange: { color: ['#f6efa6', '#d88273', '#bf444c'] } },
        series: [{ type: 'heatmap', data: data.map((d, i) => [i % 5, Math.floor(i / 5), d[yField]]), emphasis: { itemStyle: { borderColor: comp.props.color, borderWidth: 1 } } }]
      };
    case 'treemap':
      return {
        ...commonOption,
        series: [{ type: 'treemap', data: data.map(d => ({ name: d[xField], value: d[yField] })), roam: false }]
      };
    case 'boxplot':
      return {
        ...commonOption,
        xAxis: { type: 'category', data: data.map(d => d[xField]), axisLabel: { color: axisLabelColor } },
        yAxis: { type: 'value', axisLabel: { color: axisLabelColor }, splitLine: { lineStyle: { color: splitLineColor } } },
        series: [{ type: 'boxplot', data: data.map(d => [d[yField], d[yField] * 0.8, d[yField] * 1.2, d[yField] * 0.9, d[yField] * 1.1]) }]
      };
    default:
      return {};
  }
};

const renderCard = (container: HTMLElement, comp: any) => {
  container.innerHTML = `
    <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100%; background: ${comp.props.bgColor}; border: ${comp.props.borderWidth}px solid ${comp.props.borderColor}; border-radius: ${comp.props.borderRadius}px; padding: 10px; box-sizing: border-box;">
      ${comp.props.showTitle ? `<div style="font-size: 14px; color: ${comp.props.color}; margin-bottom: 8px;">${comp.props.title}</div>` : ''}
      <div style="font-size: ${comp.props.fontSize}px; font-weight: bold; color: ${comp.props.color};">${comp.props.value}</div>
      ${comp.props.unit ? `<div style="font-size: 12px; color: #888; margin-top: 4px;">${comp.props.unit}</div>` : ''}
    </div>
  `;
};

const renderTable = (container: HTMLElement, comp: any) => {
  const columns = dataFields.value.slice(0, 5);
  const sampleData = props.initialData.slice(0, 5);

  container.innerHTML = `
    <div style="height: 100%; overflow: auto; background: ${comp.props.bgColor}; border-radius: 4px;">
      ${comp.props.showTitle ? `<div style="padding: 8px 12px; font-weight: bold; border-bottom: 1px solid ${comp.props.borderColor};">${comp.props.title}</div>` : ''}
      <table style="width: 100%; border-collapse: collapse; font-size: ${comp.props.fontSize}px;">
        <thead>
          <tr style="background: rgba(0,0,0,0.2);">
            ${columns.map(c => `<th style="padding: 8px; text-align: left; border-bottom: 1px solid ${comp.props.borderColor};">${c}</th>`).join('')}
          </tr>
        </thead>
        <tbody>
          ${sampleData.map(row => `
            <tr>
              ${columns.map(c => `<td style="padding: 8px; border-bottom: 1px solid ${comp.props.borderColor};">${row[c] || '-'}</td>`).join('')}
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
};

const renderProgress = (container: HTMLElement, comp: any) => {
  container.innerHTML = `
    <div style="height: 100%; display: flex; flex-direction: column; justify-content: center; padding: 0 10px;">
      ${comp.props.showTitle ? `<div style="font-size: 14px; margin-bottom: 8px;">${comp.props.title}</div>` : ''}
      <div style="flex: 1; background: ${comp.props.bgColor}; border-radius: ${comp.props.borderRadius}px; overflow: hidden; position: relative;">
        <div style="width: ${comp.props.value}%; height: 100%; background: linear-gradient(90deg, ${comp.props.color}, ${comp.props.color}dd); border-radius: ${comp.props.borderRadius}px;"></div>
      </div>
      <div style="text-align: right; font-size: 12px; margin-top: 4px; color: #888;">${comp.props.value}%</div>
    </div>
  `;
};

const renderNumber = (container: HTMLElement, comp: any) => {
  container.innerHTML = `
    <div style="height: 100%; display: flex; justify-content: center; align-items: center; background: ${comp.props.bgColor};">
      <span style="font-size: ${comp.props.fontSize}px; font-weight: bold; color: ${comp.props.color}; font-family: monospace;">${comp.props.value}</span>
    </div>
  `;
};

const renderText = (container: HTMLElement, comp: any) => {
  container.innerHTML = `
    <div style="height: 100%; display: flex; align-items: center; padding: 0 10px; background: ${comp.props.bgColor}; border-radius: 4px;">
      <span style="font-size: ${comp.props.fontSize}px; color: ${comp.props.color}; font-family: ${comp.props.fontFamily};">${comp.props.content}</span>
    </div>
  `;
};

const renderImage = (container: HTMLElement, comp: any) => {
  container.innerHTML = `
    <div style="height: 100%; display: flex; justify-content: center; align-items: center; background: ${comp.props.bgColor}; border-radius: 4px; overflow: hidden;">
      ${comp.props.src ? `<img src="${comp.props.src}" style="max-width: 100%; max-height: 100%; object-fit: contain;" />` : '<span style="color: #666;">点击设置图片</span>'}
    </div>
  `;
};

// 工具栏操作
const handleSave = async () => {
  saving.value = true;
  try {
    const spec = getSpec();
    emit('save', spec);
    saveSuccessVisible.value = true;
    setTimeout(() => { saveSuccessVisible.value = false; }, 2000);
  } finally {
    saving.value = false;
  }
};

const handlePreview = () => {
  previewVisible.value = true;
  nextTick(() => {
    // 渲染预览内容
    if (previewContainerRef.value) {
      previewContainerRef.value.innerHTML = `<div style="height: 100%; display: flex; justify-content: center; align-items: center; color: #666;">预览功能开发中...</div>`;
    }
  });
};

const handleSnapshot = (key: string) => {
  if (key === 'png') {
    message.info('截图功能需要 html2canvas 库支持');
  } else if (key === 'json') {
    const spec = getSpec();
    const blob = new Blob([JSON.stringify(spec, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'bi-design.json';
    a.click();
    URL.revokeObjectURL(url);
    message.success('已导出为 JSON');
  }
};

const handleClear = () => {
  components.value = [];
  selectedComponentId.value = null;
  message.success('画布已清空');
};

const changeTheme = (key: string) => {
  currentTheme.value = key;
  message.success(`已切换为${key === 'dark' ? '深色' : key === 'light' ? '浅色' : '商务蓝'}主题`);
  // 主题切换后重新渲染所有图表（更新轴线/标签颜色）
  nextTick(() => {
    components.value.forEach(c => {
      if (['bar','line','pie','area','scatter','radar','heatmap','treemap','boxplot'].includes(c.type)) {
        renderComponent(c.id);
      }
    });
  });
};

// 实训手册
const toggleHandbook = () => {
  if (!handbookVisible.value) {
    handbookVisible.value = true;
    handbookCollapsed.value = false;
    loadHandbook();
  } else {
    handbookVisible.value = false;
  }
};

const loadHandbook = async () => {
  handbookLoading.value = true;
  try {
    // 模拟加载手册内容
    await new Promise(resolve => setTimeout(resolve, 500));
    handbookContent.value = `
      <h2>实训任务说明</h2>
      <p>本实训旨在帮助您掌握可视化分析的基本技能。</p>

      <h3>任务一：创建柱状图</h3>
      <p>1. 从左侧组件库拖入一个"柱状图"组件到画布上</p>
      <p>2. 在右侧属性面板中配置数据字段</p>
      <p>3. 设置X轴为"城市"，Y轴为"销售额"</p>
      <p>4. 选择合适的颜色和样式</p>

      <h3>任务二：添加指标卡片</h3>
      <p>1. 拖入一个"指标卡片"组件</p>
      <p>2. 设置卡片显示总销售额</p>

      <h3>评分标准</h3>
      <ul>
        <li>完成柱状图绘制 (40分)</li>
        <li>正确绑定数据字段 (30分)</li>
        <li>样式美观合理 (20分)</li>
        <li>按时提交作业 (10分)</li>
      </ul>
    `;
    handbookToc.value = [
      { id: 'task1', title: '任务一：创建柱状图' },
      { id: 'task2', title: '任务二：添加指标卡片' },
      { id: 'score', title: '评分标准' }
    ];
  } finally {
    handbookLoading.value = false;
  }
};

const scrollToSection = (id: string) => {
  message.info(`跳转到章节: ${id}`);
};

// 获取设计规范
const getSpec = () => {
  return {
    theme: currentTheme.value,
    components: components.value.map(c => ({
      id: c.id,
      type: c.type,
      x: c.x,
      y: c.y,
      width: c.width,
      height: c.height,
      props: c.props
    })),
    canvas: {
      width: canvasAreaRef.value?.clientWidth || 1200,
      height: canvasAreaRef.value?.clientHeight || 800
    }
  };
};

// 生命周期
onMounted(async () => {
  // 初始化数据集
  if (props.initialData.length > 0) {
    datasets.value = [{ id: 'default', name: props.trainingId ? `实训数据集 (${props.initialData.length}行)` : '数据集' }];
    dataFields.value = Object.keys(props.initialData[0]);
  }

  // 恢复快照
  if (props.snapshot) {
    try {
      const spec = typeof props.snapshot === 'string' ? JSON.parse(props.snapshot) : props.snapshot;
      if (spec.theme) currentTheme.value = spec.theme;
      if (spec.components) {
        components.value = spec.components;
        components.value.forEach(c => renderComponent(c.id));
      }
    } catch (e) {
      console.warn('恢复快照失败:', e);
    }
  }
});

// 监听 initialData 变化 — 数据通过 postMessage 异步到达时重新渲染所有图表
watch(() => props.initialData, (newData) => {
  if (newData && newData.length > 0) {
    datasets.value = [{ id: 'default', name: props.trainingId ? `实训数据集 (${newData.length}行)` : '数据集' }];
    dataFields.value = Object.keys(newData[0]);
    // 重新渲染所有已有的图表组件
    nextTick(() => {
      components.value.forEach(c => {
        if (['bar','line','pie','area','scatter','radar','heatmap','treemap','boxplot'].includes(c.type)) {
          // 如果组件没有选择字段，自动分配
          if (!c.props.xField && dataFields.value.length > 0) {
            // 优先选择文本字段作为 X 轴
            const textFields = dataFields.value.filter(f => {
              const val = newData[0][f];
              return typeof val === 'string' && isNaN(Number(val));
            });
            c.props.xField = textFields[0] || dataFields.value[0];
          }
          if (!c.props.yField && dataFields.value.length > 1) {
            // 优先选择数值字段作为 Y 轴
            const numFields = dataFields.value.filter(f => {
              const val = newData[0][f];
              return typeof val === 'number' || (!isNaN(Number(val)) && val !== '');
            });
            c.props.yField = numFields[0] || dataFields.value[1];
          }
          renderComponent(c.id);
        }
      });
    });
  }
}, { deep: false });

onUnmounted(() => {
  // 清理图表实例
  Object.values(componentRefs.value).forEach((container: any) => {
    const chartEl = container?.querySelector('.chart-container');
    if (chartEl) {
      const chart = echarts.getInstanceByDom(chartEl);
      chart?.dispose();
    }
  });
});

// 暴露方法
defineExpose({
  getSpec: () => getSpec(),
  save: handleSave
});
</script>

<style scoped>
.tempo-bi-designer {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #1a1a2e;
  color: #fff;
}

/* 工具栏 */
.bi-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 16px;
  background: linear-gradient(180deg, #252540 0%, #1a1a2e 100%);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.toolbar-center {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

/* 内容区域 */
.bi-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.bi-content.theme-dark {
  background: #1a1a2e;
}

.bi-content.theme-light {
  background: #f5f5f5;
  color: #333;
}

.bi-content.theme-blue {
  background: #0d1b2a;
}

/* 组件面板 */
.components-panel {
  display: flex;
  flex-direction: column;
  background: #252540;
  border-right: 1px solid rgba(255,255,255,0.1);
  transition: width 0.2s;
}

.theme-light .components-panel {
  background: #fff;
  border-color: #e8e8e8;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  font-weight: 600;
}

.theme-light .panel-header {
  border-color: #e8e8e8;
}

.panel-body {
  flex: 1;
  overflow: auto;
  padding: 12px;
}

.component-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.component-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  cursor: grab;
  transition: all 0.2s;
}

.component-item:hover {
  background: rgba(84, 112, 198, 0.2);
  border-color: #5470c6;
  transform: translateY(-2px);
}

.component-item:active {
  cursor: grabbing;
}

.component-item span {
  margin-top: 8px;
  font-size: 12px;
  color: #ccc;
}

.theme-light .component-item span {
  color: #333;
}

/* 画布区域 */
.canvas-area {
  flex: 1;
  overflow: auto;
  position: relative;
}

.canvas-wrapper {
  position: relative;
  min-width: 100%;
  min-height: 100%;
}

.grid-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.canvas-component {
  position: absolute;
  cursor: move;
  background: rgba(255,255,255,0.02);
  border: 2px solid transparent;
  border-radius: 8px;
  transition: border-color 0.2s;
}

.canvas-component:hover {
  border-color: rgba(84, 112, 198, 0.5);
}

.canvas-component.selected {
  border-color: #5470c6;
  box-shadow: 0 0 0 2px rgba(84, 112, 198, 0.2);
}

.component-content {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.delete-btn {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 24px;
  height: 24px;
  padding: 0;
  background: #ff4d4f;
  border: none;
  border-radius: 50%;
  color: #fff;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.canvas-component.selected .delete-btn {
  opacity: 1;
}

/* 缩放控制点 */
.resize-handle {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #5470c6;
  border: 2px solid #fff;
  border-radius: 2px;
}

.resize-n { top: -6px; left: 50%; transform: translateX(-50%); cursor: n-resize; }
.resize-s { bottom: -6px; left: 50%; transform: translateX(-50%); cursor: s-resize; }
.resize-e { right: -6px; top: 50%; transform: translateY(-50%); cursor: e-resize; }
.resize-w { left: -6px; top: 50%; transform: translateY(-50%); cursor: w-resize; }
.resize-nw { top: -6px; left: -6px; cursor: nw-resize; }
.resize-ne { top: -6px; right: -6px; cursor: ne-resize; }
.resize-sw { bottom: -6px; left: -6px; cursor: sw-resize; }
.resize-se { bottom: -6px; right: -6px; cursor: se-resize; }

/* 属性面板 */
.property-panel {
  display: flex;
  flex-direction: column;
  background: #252540;
  border-left: 1px solid rgba(255,255,255,0.1);
  transition: width 0.2s;
}

.theme-light .property-panel {
  background: #fff;
  border-color: #e8e8e8;
}

/* 分割线 */
.resizer-h {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s;
}

.resizer-h:hover {
  background: #5470c6;
}

/* 实训手册悬浮按钮 */
.handbook-float-btn {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px 12px 12px;
  background: linear-gradient(90deg, #faad14, #fa8c16);
  border-radius: 20px 0 0 20px;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  z-index: 1000;
  box-shadow: -2px 0 8px rgba(250, 173, 20, 0.3);
  transition: all 0.3s;
}

.handbook-float-btn:hover {
  padding-right: 20px;
}

.handbook-float-btn.expanded {
  background: linear-gradient(90deg, #52c41a, #73d13d);
}

/* 实训手册内容 */
.handbook-content {
  height: 100%;
}

.handbook-toc {
  padding: 16px;
  background: rgba(0,0,0,0.05);
  border-radius: 8px;
  margin-bottom: 16px;
}

.handbook-toc h4 {
  margin-bottom: 12px;
  color: #1890ff;
}

.handbook-toc ul {
  list-style: none;
  padding: 0;
}

.handbook-toc li {
  padding: 8px 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.handbook-toc a {
  color: #1890ff;
  cursor: pointer;
}

.handbook-toc a:hover {
  text-decoration: underline;
}

.handbook-body {
  line-height: 1.8;
}

.handbook-body h2 {
  font-size: 20px;
  margin: 24px 0 16px;
  color: #1890ff;
}

.handbook-body h3 {
  font-size: 16px;
  margin: 20px 0 12px;
}

.handbook-body ul {
  padding-left: 24px;
}

.handbook-body li {
  margin-bottom: 8px;
}

/* 预览弹窗 */
.preview-modal :deep(.ant-modal-content) {
  background: #1a1a2e;
}

.preview-modal :deep(.ant-modal-header) {
  background: #252540;
  border-color: rgba(255,255,255,0.1);
}

.preview-modal :deep(.ant-modal-title) {
  color: #fff;
}

.preview-container {
  height: 600px;
  background: #000;
  border-radius: 8px;
}

/* Ant Design 覆盖 */
:deep(.ant-tabs-tab) {
  color: #999;
}

:deep(.ant-tabs-tab-active) {
  color: #fff !important;
}

.theme-light :deep(.ant-tabs-tab) {
  color: #666;
}

:deep(.ant-collapse-ghost > .ant-collapse-item > .ant-collapse-content > .ant-collapse-content-box) {
  padding: 0 16px;
}

:deep(.ant-form-item-label > label) {
  color: #ccc;
}

.theme-light :deep(.ant-form-item-label > label) {
  color: #333;
}

:deep(.ant-input),
:deep(.ant-select-selector),
:deep(.ant-input-number) {
  background: rgba(255,255,255,0.05) !important;
  border-color: rgba(255,255,255,0.2) !important;
  color: #fff !important;
}

.theme-light :deep(.ant-input),
.theme-light :deep(.ant-select-selector),
.theme-light :deep(.ant-input-number) {
  background: #f5f5f5 !important;
  border-color: #d9d9d9 !important;
  color: #333 !important;
}

:deep(.ant-input-search .ant-input) {
  background: transparent !important;
}
</style>
