<template>
  <a-drawer
    :open="visible"
    title="可视化分析操作手册"
    width="500"
    :mask="false"
    @close="handleClose"
    placement="right"
    class="manual-drawer"
  >
    <a-menu
      :selected-keys="[selectedKey]"
      mode="inline"
      class="manual-menu"
      @select="handleMenuSelect"
    >
      <a-menu-item v-for="section in manualSections" :key="section.id">
        {{ section.title }}
      </a-menu-item>
    </a-menu>
    
    <div class="manual-content">
      <div v-if="selectedSection" class="section-content">
        <h2 class="section-title">{{ selectedSection.title }}</h2>
        <div class="section-text" v-html="formattedContent"></div>
      </div>
      <a-empty v-else description="请选择左侧章节" />
    </div>
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:visible']);

// 手册章节
const manualSections = ref([
  {
    id: 'introduction',
    title: '1. 介绍',
    content: `
# 可视化分析介绍

可视化分析是一种借助于图形化手段，对数据进行分析和展示的方法。通过可视化，可以更直观地理解数据中的模式、趋势和关系。

## 主要特点

- **直观展示**：将复杂数据转化为易于理解的图形
- **交互分析**：通过交互方式探索数据
- **多维比较**：支持多维度数据的比较分析
- **异常检测**：快速发现数据中的异常点
- **趋势识别**：帮助识别数据中的趋势和模式

## 应用场景

可视化分析广泛应用于商业智能、科学研究、金融分析、教育评估等多个领域。通过合理的可视化设计，可以将复杂的数据转化为有价值的决策信息。
    `
  },
  {
    id: 'interface',
    title: '2. 界面说明',
    content: `
# 界面说明

可视化分析工具的界面主要分为以下几个部分：

## 工具栏

位于页面顶部，提供保存、预览、主题切换等功能。

## 组件面板

位于左侧，提供各种图表组件，可以通过拖拽的方式添加到画布中。组件分为基础图表和高级图表两类。

## 画布区域

位于中间，是放置和编辑图表的主要区域。您可以在此拖拽、调整大小和定位各种图表组件。

## 属性面板

位于右侧，用于配置选中图表的各种属性，包括数据源、样式、交互等设置。

## 操作手册

通过右下角的"？"按钮可以随时打开本操作手册，获取使用帮助。
    `
  },
  {
    id: 'basic-operations',
    title: '3. 基本操作',
    content: `
# 基本操作

## 添加图表

1. 从左侧组件面板中选择需要的图表类型
2. 拖拽到中间画布区域
3. 图表会自动显示默认数据

## 调整图表位置和大小

- **移动图表**：选中图表后，按住鼠标左键拖动
- **调整大小**：选中图表后，通过右下角的调整手柄拖动改变大小

## 配置图表属性

1. 点击选中要配置的图表
2. 在右侧属性面板中进行设置：
   - 数据：选择数据源、设置数据刷新频率
   - 样式：设置标题、背景、边框等样式
   - 高级：设置层级顺序、透明度等

## 保存和预览

- 点击顶部工具栏的"保存"按钮保存当前设计
- 点击"预览"按钮可以查看全屏效果
    `
  },
  {
    id: 'chart-types',
    title: '4. 图表类型',
    content: `
# 图表类型说明

## 基础图表

### 折线图
适用于展示数据随时间变化的趋势。

### 柱状图
适用于比较不同类别的数据大小。

### 饼图
适用于展示整体中各部分的占比关系。

### 散点图
适用于探索两个变量之间的相关性。

## 高级图表

### 雷达图
适用于多维度评估和比较。

### 热力图
适用于展示二维矩阵数据的密度或频率。

### 树图
适用于展示层次结构数据。

### 关系图
适用于展示实体之间的关系网络。
    `
  },
  {
    id: 'data-sources',
    title: '5. 数据源',
    content: `
# 数据源管理

可视化分析工具支持多种数据源，您可以选择最适合您需求的数据源。

## 预设数据集

系统预置了几组示例数据集，适用于快速创建演示图表：

- **示例数据1**：基础销售数据
- **示例数据2**：用户行为数据
- **示例数据3**：区域分布数据

## 自定义数据

您也可以通过以下方式使用自定义数据：

1. 在属性面板中选择"自定义数据"
2. 在文本框中输入JSON格式的数据
3. 系统会自动验证JSON格式是否正确
4. 确认后图表会使用您提供的数据进行渲染

## 数据刷新

您可以设置数据自动刷新的时间间隔，使图表始终显示最新数据：

1. 在属性面板的"数据刷新间隔"中设置秒数
2. 设置为0表示不自动刷新
3. 建议根据数据更新频率设置合理的刷新间隔
    `
  }
]);

// 选中的章节ID
const selectedKey = ref('introduction');

// 获取选中的章节
const selectedSection = computed(() => {
  return manualSections.value.find(section => section.id === selectedKey.value);
});

// 格式化内容（将Markdown转为HTML）
const formattedContent = computed(() => {
  if (!selectedSection.value) return '';
  return marked(selectedSection.value.content);
});

// 关闭抽屉
const handleClose = () => {
  emit('update:visible', false);
};

// 处理菜单选择
const handleMenuSelect = (e: { key: string }) => {
  selectedKey.value = e.key;
};

// 初始化
onMounted(() => {
  // 默认选中第一个章节
  if (manualSections.value.length > 0) {
    selectedKey.value = manualSections.value[0].id;
  }
});
</script>

<style scoped>
.manual-drawer {
  display: flex;
  flex-direction: column;
}

.manual-drawer :deep(.ant-drawer-body) {
  padding: 0;
  display: flex;
  overflow: hidden;
  height: 100%;
}

.manual-menu {
  width: 200px;
  border-right: 1px solid #f0f0f0;
  height: 100%;
  overflow-y: auto;
}

.manual-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.section-title {
  font-size: 20px;
  font-weight: 500;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.section-text {
  font-size: 14px;
  line-height: 1.8;
}

.section-text :deep(h1) {
  font-size: 24px;
  margin-bottom: 16px;
}

.section-text :deep(h2) {
  font-size: 18px;
  margin-top: 24px;
  margin-bottom: 12px;
}

.section-text :deep(ul), .section-text :deep(ol) {
  padding-left: 24px;
  margin-bottom: 16px;
}

.section-text :deep(li) {
  margin-bottom: 8px;
}

.section-text :deep(p) {
  margin-bottom: 16px;
}

.section-text :deep(code) {
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 3px;
}
</style> 