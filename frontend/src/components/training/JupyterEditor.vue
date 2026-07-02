<template>
  <div class="jupyter-editor">
    <!-- 工具栏 -->
    <div class="jupyter-toolbar">
      <a-space>
        <a-upload
          :show-upload-list="false"
          accept=".ipynb"
          :before-upload="handleImport"
        >
          <a-button type="primary">
            <UploadOutlined /> 导入 ipynb 文件
          </a-button>
        </a-upload>
        
        <a-button @click="handleExport">
          <DownloadOutlined /> 导出文件
        </a-button>
        
        <a-button @click="handleReset">
          <ReloadOutlined /> 重置环境
        </a-button>
        
        <a-button @click="toggleFullscreen">
          <FullscreenOutlined v-if="!isFullscreen" />
          <FullscreenExitOutlined v-else />
          {{ isFullscreen ? '退出全屏' : '全屏显示' }}
        </a-button>
        
        <a-button type="primary" ghost @click="handleRun">
          <PlayCircleOutlined /> 运行全部
        </a-button>
      </a-space>
    </div>
    
    <!-- 编辑区域 -->
    <div class="jupyter-container" ref="containerRef">
      <!-- 单元格列表 -->
      <div class="cells-container">
        <div
          v-for="(cell, index) in cells"
          :key="cell.id"
          class="cell"
          :class="{ active: activeCell === index }"
          @click="setActiveCell(index)"
        >
          <!-- 单元格工具栏 -->
          <div class="cell-toolbar">
            <a-space size="small">
              <a-select
                v-model:value="cell.type"
                size="small"
                style="width: 100px"
              >
                <a-select-option value="code">Code</a-select-option>
                <a-select-option value="markdown">Markdown</a-select-option>
              </a-select>
              
              <a-button size="small" @click="runCell(index)">
                <PlayCircleOutlined />
              </a-button>
              
              <a-button size="small" @click="addCellAfter(index)">
                <PlusOutlined />
              </a-button>
              
              <a-button size="small" danger @click="deleteCell(index)">
                <DeleteOutlined />
              </a-button>
              
              <a-button size="small" @click="moveCellUp(index)" :disabled="index === 0">
                <ArrowUpOutlined />
              </a-button>
              
              <a-button size="small" @click="moveCellDown(index)" :disabled="index === cells.length - 1">
                <ArrowDownOutlined />
              </a-button>
            </a-space>
          </div>
          
          <!-- 单元格内容 -->
          <div class="cell-content">
            <!-- 代码单元格 -->
            <div v-if="cell.type === 'code'" class="code-cell">
              <div class="cell-input">
                <div class="cell-prompt">In [{{ cell.execution_count || ' ' }}]:</div>
                <MonacoEditor
                  v-model:value="cell.source"
                  language="python"
                  :height="getEditorHeight(cell.source)"
                  :options="{
                    minimap: { enabled: false },
                    lineNumbers: 'on',
                    fontSize: 14,
                    automaticLayout: true
                  }"
                />
              </div>
              
              <!-- 输出区域 -->
              <div v-if="cell.outputs && cell.outputs.length > 0" class="cell-output">
                <div class="cell-prompt">Out[{{ cell.execution_count }}]:</div>
                <div class="output-content">
                  <div v-for="(output, oIndex) in cell.outputs" :key="oIndex">
                    <!-- 文本输出 -->
                    <pre v-if="output.type === 'stream'">{{ output.text }}</pre>
                    
                    <!-- 执行结果 -->
                    <pre v-else-if="output.type === 'execute_result'">{{ output.data['text/plain'] }}</pre>
                    
                    <!-- 错误输出 -->
                    <pre v-else-if="output.type === 'error'" class="error-output">
{{ output.ename }}: {{ output.evalue }}
{{ output.traceback.join('\n') }}
                    </pre>
                    
                    <!-- 图片输出 -->
                    <img
                      v-else-if="output.type === 'display_data' && output.data['image/png']"
                      :src="`data:image/png;base64,${output.data['image/png']}`"
                      alt="Output image"
                    />
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Markdown单元格 -->
            <div v-else-if="cell.type === 'markdown'" class="markdown-cell">
              <div v-if="editingCell !== index" class="markdown-preview" @dblclick="editCell(index)">
                <div v-html="renderMarkdown(cell.source)"></div>
              </div>
              <div v-else class="markdown-edit">
                <a-textarea
                  v-model:value="cell.source"
                  :auto-size="{ minRows: 3 }"
                  @blur="finishEdit(index)"
                  @keydown.esc="finishEdit(index)"
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- 添加新单元格按钮 -->
        <div class="add-cell-button" @click="addCell">
          <PlusOutlined /> 添加单元格
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { message } from 'ant-design-vue';
import {
  UploadOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons-vue';
import { marked } from 'marked';
import MonacoEditor from '@/components/editor/MonacoEditor.vue';

interface Cell {
  id: string;
  type: 'code' | 'markdown';
  source: string;
  outputs?: any[];
  execution_count?: number;
}

const props = defineProps<{
  trainingId: string;
}>();

const emit = defineEmits<{
  (e: 'save', cells: Cell[]): void;
}>();

const containerRef = ref<HTMLDivElement>();
const cells = ref<Cell[]>([
  {
    id: generateId(),
    type: 'markdown',
    source: '# Jupyter Notebook\n\n欢迎使用Jupyter编辑器，双击此处编辑Markdown内容。'
  },
  {
    id: generateId(),
    type: 'code',
    source: '# 导入必要的库\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\n# 你的代码从这里开始',
    outputs: []
  }
]);

const activeCell = ref(0);
const editingCell = ref<number | null>(null);
const isFullscreen = ref(false);

// 生成唯一ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// 获取编辑器高度
function getEditorHeight(content: string) {
  const lines = content.split('\n').length;
  return Math.max(100, Math.min(400, lines * 20 + 40));
}

// 渲染Markdown
function renderMarkdown(content: string) {
  return marked(content);
}

// 设置活动单元格
function setActiveCell(index: number) {
  activeCell.value = index;
}

// 编辑单元格
function editCell(index: number) {
  editingCell.value = index;
}

// 完成编辑
function finishEdit(index: number) {
  editingCell.value = null;
}

// 运行单元格
async function runCell(index: number) {
  const cell = cells.value[index];
  if (cell.type !== 'code') return;
  
  // 模拟运行
  message.info('正在运行单元格...');
  
  // 更新执行计数
  cell.execution_count = (cell.execution_count || 0) + 1;
  
  // 模拟输出
  setTimeout(() => {
    cell.outputs = [
      {
        type: 'stream',
        text: '运行成功！\n这是模拟的输出结果。'
      }
    ];
    message.success('单元格运行完成');
  }, 1000);
}

// 运行全部单元格
async function handleRun() {
  message.info('正在运行所有代码单元格...');
  
  for (let i = 0; i < cells.value.length; i++) {
    if (cells.value[i].type === 'code') {
      await runCell(i);
    }
  }
}

// 添加单元格
function addCell() {
  cells.value.push({
    id: generateId(),
    type: 'code',
    source: '',
    outputs: []
  });
}

// 在指定位置后添加单元格
function addCellAfter(index: number) {
  cells.value.splice(index + 1, 0, {
    id: generateId(),
    type: 'code',
    source: '',
    outputs: []
  });
  activeCell.value = index + 1;
}

// 删除单元格
function deleteCell(index: number) {
  if (cells.value.length === 1) {
    message.warning('至少需要保留一个单元格');
    return;
  }
  
  cells.value.splice(index, 1);
  if (activeCell.value >= cells.value.length) {
    activeCell.value = cells.value.length - 1;
  }
}

// 上移单元格
function moveCellUp(index: number) {
  if (index === 0) return;
  
  const temp = cells.value[index];
  cells.value[index] = cells.value[index - 1];
  cells.value[index - 1] = temp;
  activeCell.value = index - 1;
}

// 下移单元格
function moveCellDown(index: number) {
  if (index === cells.value.length - 1) return;
  
  const temp = cells.value[index];
  cells.value[index] = cells.value[index + 1];
  cells.value[index + 1] = temp;
  activeCell.value = index + 1;
}

// 导入ipynb文件
function handleImport(file: File) {
  const reader = new FileReader();
  
  reader.onload = (e) => {
    try {
      const notebook = JSON.parse(e.target?.result as string);
      
      // 转换notebook格式到我们的格式
      cells.value = notebook.cells.map((cell: any) => ({
        id: generateId(),
        type: cell.cell_type,
        source: Array.isArray(cell.source) ? cell.source.join('') : cell.source,
        outputs: cell.outputs || [],
        execution_count: cell.execution_count
      }));
      
      message.success('导入成功');
    } catch (error) {
      message.error('文件格式错误，请选择有效的.ipynb文件');
    }
  };
  
  reader.readAsText(file);
  return false; // 阻止默认上传
}

// 导出文件
function handleExport() {
  // 转换为Jupyter Notebook格式
  const notebook = {
    cells: cells.value.map(cell => ({
      cell_type: cell.type,
      source: cell.source.split('\n').map(line => line + '\n'),
      outputs: cell.outputs || [],
      execution_count: cell.execution_count,
      metadata: {}
    })),
    metadata: {
      kernelspec: {
        display_name: 'Python 3',
        language: 'python',
        name: 'python3'
      },
      language_info: {
        name: 'python',
        version: '3.8.0'
      }
    },
    nbformat: 4,
    nbformat_minor: 4
  };
  
  // 下载文件
  const blob = new Blob([JSON.stringify(notebook, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `training_${props.trainingId}.ipynb`;
  a.click();
  URL.revokeObjectURL(url);
  
  message.success('导出成功');
}

// 重置环境
function handleReset() {
  cells.value = [
    {
      id: generateId(),
      type: 'code',
      source: '',
      outputs: []
    }
  ];
  activeCell.value = 0;
  message.success('环境已重置');
}

// 切换全屏
function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value;
  
  if (isFullscreen.value) {
    containerRef.value?.requestFullscreen();
  } else {
    document.exitFullscreen();
  }
}

// 监听全屏变化
function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement;
}

// 自动保存
function autoSave() {
  emit('save', cells.value);
}

// 生命周期
onMounted(() => {
  document.addEventListener('fullscreenchange', handleFullscreenChange);
  
  // 每30秒自动保存
  const saveInterval = setInterval(autoSave, 30000);
  
  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
    clearInterval(saveInterval);
  });
});
</script>

<style scoped>
.jupyter-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.jupyter-toolbar {
  padding: 12px;
  background: #f5f5f5;
  border-bottom: 1px solid #d9d9d9;
}

.jupyter-container {
  flex: 1;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 20px;
}

.cells-container {
  max-width: 1000px;
  margin: 0 auto;
}

.cell {
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  margin-bottom: 10px;
  transition: all 0.2s;
}

.cell.active {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.cell-toolbar {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #d9d9d9;
  border-radius: 4px 4px 0 0;
}

.cell-content {
  padding: 0;
}

.code-cell .cell-input {
  display: flex;
  align-items: flex-start;
}

.cell-prompt {
  width: 80px;
  padding: 12px 8px;
  color: #999;
  font-family: monospace;
  font-size: 13px;
  text-align: right;
  flex-shrink: 0;
}

.code-cell .cell-input :deep(.monaco-editor) {
  flex: 1;
}

.cell-output {
  display: flex;
  align-items: flex-start;
  background: #fafafa;
  border-top: 1px solid #e8e8e8;
}

.output-content {
  flex: 1;
  padding: 12px;
}

.output-content pre {
  margin: 0;
  font-family: monospace;
  font-size: 13px;
  white-space: pre-wrap;
}

.error-output {
  color: #ff4d4f;
}

.output-content img {
  max-width: 100%;
  height: auto;
}

.markdown-cell {
  padding: 16px;
}

.markdown-preview {
  cursor: text;
  min-height: 50px;
}

.markdown-preview:hover {
  background: #fafafa;
}

.markdown-edit :deep(textarea) {
  font-family: monospace;
  font-size: 14px;
}

.add-cell-button {
  text-align: center;
  padding: 20px;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
}

.add-cell-button:hover {
  color: #1890ff;
}

/* Markdown样式 */
.markdown-preview h1 {
  font-size: 28px;
  font-weight: 500;
  margin: 16px 0;
}

.markdown-preview h2 {
  font-size: 24px;
  font-weight: 500;
  margin: 14px 0;
}

.markdown-preview h3 {
  font-size: 20px;
  font-weight: 500;
  margin: 12px 0;
}

.markdown-preview p {
  margin: 8px 0;
}

.markdown-preview code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-family: monospace;
}

.markdown-preview pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-preview ul,
.markdown-preview ol {
  margin: 8px 0;
  padding-left: 24px;
}
</style> 