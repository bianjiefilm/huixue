<template>
  <div class="rich-text-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <a-space wrap>
        <!-- 文字格式 -->
        <a-button-group>
          <a-tooltip title="加粗">
            <a-button @click="execCommand('bold')" :type="isActive('bold') ? 'primary' : 'default'">
              <BoldOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="斜体">
            <a-button @click="execCommand('italic')" :type="isActive('italic') ? 'primary' : 'default'">
              <ItalicOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="下划线">
            <a-button @click="execCommand('underline')" :type="isActive('underline') ? 'primary' : 'default'">
              <UnderlineOutlined />
            </a-button>
          </a-tooltip>
        </a-button-group>

        <!-- 标题 -->
        <a-select v-model:value="headingLevel" @change="setHeading" style="width: 120px">
          <a-select-option value="p">正文</a-select-option>
          <a-select-option value="h1">标题 1</a-select-option>
          <a-select-option value="h2">标题 2</a-select-option>
          <a-select-option value="h3">标题 3</a-select-option>
          <a-select-option value="h4">标题 4</a-select-option>
        </a-select>

        <!-- 列表 -->
        <a-button-group>
          <a-tooltip title="无序列表">
            <a-button @click="execCommand('insertUnorderedList')">
              <UnorderedListOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="有序列表">
            <a-button @click="execCommand('insertOrderedList')">
              <OrderedListOutlined />
            </a-button>
          </a-tooltip>
        </a-button-group>

        <!-- 插入 -->
        <a-button-group>
          <a-tooltip title="插入链接">
            <a-button @click="showLinkDialog">
              <LinkOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="插入图片">
            <a-button @click="showImageDialog">
              <PictureOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="插入代码块">
            <a-button @click="insertCodeBlock">
              <CodeOutlined />
            </a-button>
          </a-tooltip>
          <a-tooltip title="插入表格">
            <a-button @click="showTableDialog">
              <TableOutlined />
            </a-button>
          </a-tooltip>
        </a-button-group>

        <!-- 视图切换 -->
        <a-radio-group v-model:value="viewMode" button-style="solid">
          <a-radio-button value="edit">编辑</a-radio-button>
          <a-radio-button value="preview">预览</a-radio-button>
          <a-radio-button value="split">分屏</a-radio-button>
        </a-radio-group>
      </a-space>
    </div>

    <!-- 编辑区域 -->
    <div class="editor-container" :class="viewMode">
      <div v-if="viewMode !== 'preview'" class="editor-pane">
        <div
          ref="editorRef"
          class="editor-content"
          contenteditable="true"
          @input="handleInput"
          @paste="handlePaste"
          v-html="content"
        ></div>
      </div>
      
      <div v-if="viewMode !== 'edit'" class="preview-pane">
        <div class="preview-content" v-html="previewHtml"></div>
      </div>
    </div>

    <!-- 链接对话框 -->
    <a-modal
      v-model:open="linkDialogVisible"
      title="插入链接"
      @ok="insertLink"
      @cancel="linkDialogVisible = false"
    >
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="链接文字">
          <a-input v-model:value="linkForm.text" placeholder="请输入链接文字" />
        </a-form-item>
        <a-form-item label="链接地址">
          <a-input v-model:value="linkForm.url" placeholder="请输入链接地址" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 图片对话框 -->
    <a-modal
      v-model:open="imageDialogVisible"
      title="插入图片"
      @ok="insertImage"
      @cancel="imageDialogVisible = false"
    >
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="图片地址">
          <a-input v-model:value="imageForm.url" placeholder="请输入图片URL" />
        </a-form-item>
        <a-form-item label="图片描述">
          <a-input v-model:value="imageForm.alt" placeholder="请输入图片描述（可选）" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 表格对话框 -->
    <a-modal
      v-model:open="tableDialogVisible"
      title="插入表格"
      @ok="insertTable"
      @cancel="tableDialogVisible = false"
    >
      <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="行数">
          <a-input-number v-model:value="tableForm.rows" :min="1" :max="20" />
        </a-form-item>
        <a-form-item label="列数">
          <a-input-number v-model:value="tableForm.cols" :min="1" :max="10" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import {
  BoldOutlined,
  ItalicOutlined,
  UnderlineOutlined,
  UnorderedListOutlined,
  OrderedListOutlined,
  LinkOutlined,
  PictureOutlined,
  CodeOutlined,
  TableOutlined
} from '@ant-design/icons-vue';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const props = defineProps<{
  value?: string;
  placeholder?: string;
  height?: number;
}>();

const emit = defineEmits<{
  (e: 'update:value', value: string): void;
  (e: 'change', value: string): void;
}>();

const editorRef = ref<HTMLDivElement>();
const content = ref(props.value || '');
const viewMode = ref<'edit' | 'preview' | 'split'>('edit');
const headingLevel = ref('p');

// 对话框
const linkDialogVisible = ref(false);
const imageDialogVisible = ref(false);
const tableDialogVisible = ref(false);

// 表单数据
const linkForm = ref({ text: '', url: '' });
const imageForm = ref({ url: '', alt: '' });
const tableForm = ref({ rows: 3, cols: 3 });

// 预览HTML
const previewHtml = computed(() => {
  if (!content.value) return '';
  
  // 使用marked解析Markdown
  const html = marked(content.value);
  
  // 使用DOMPurify清理HTML，防止XSS
  return DOMPurify.sanitize(html);
});

// 执行命令
const execCommand = (command: string, value?: string) => {
  document.execCommand(command, false, value);
  handleInput();
};

// 检查命令状态
const isActive = (command: string) => {
  return document.queryCommandState(command);
};

// 设置标题
const setHeading = (level: string) => {
  if (level === 'p') {
    execCommand('formatBlock', '<p>');
  } else {
    execCommand('formatBlock', `<${level}>`);
  }
};

// 处理输入
const handleInput = () => {
  if (editorRef.value) {
    content.value = editorRef.value.innerHTML;
    emit('update:value', content.value);
    emit('change', content.value);
  }
};

// 处理粘贴
const handlePaste = (e: ClipboardEvent) => {
  e.preventDefault();
  const text = e.clipboardData?.getData('text/plain');
  if (text) {
    document.execCommand('insertText', false, text);
  }
};

// 显示链接对话框
const showLinkDialog = () => {
  linkForm.value = { text: '', url: '' };
  linkDialogVisible.value = true;
};

// 插入链接
const insertLink = () => {
  if (linkForm.value.url) {
    const html = `<a href="${linkForm.value.url}" target="_blank">${linkForm.value.text || linkForm.value.url}</a>`;
    execCommand('insertHTML', html);
  }
  linkDialogVisible.value = false;
};

// 显示图片对话框
const showImageDialog = () => {
  imageForm.value = { url: '', alt: '' };
  imageDialogVisible.value = true;
};

// 插入图片
const insertImage = () => {
  if (imageForm.value.url) {
    const html = `<img src="${imageForm.value.url}" alt="${imageForm.value.alt || ''}" style="max-width: 100%;">`;
    execCommand('insertHTML', html);
  }
  imageDialogVisible.value = false;
};

// 插入代码块
const insertCodeBlock = () => {
  const html = '<pre><code>// 在此输入代码</code></pre><p><br></p>';
  execCommand('insertHTML', html);
};

// 显示表格对话框
const showTableDialog = () => {
  tableForm.value = { rows: 3, cols: 3 };
  tableDialogVisible.value = true;
};

// 插入表格
const insertTable = () => {
  let html = '<table border="1" style="border-collapse: collapse; width: 100%;">';
  
  // 表头
  html += '<thead><tr>';
  for (let j = 0; j < tableForm.value.cols; j++) {
    html += `<th style="border: 1px solid #ddd; padding: 8px;">标题${j + 1}</th>`;
  }
  html += '</tr></thead>';
  
  // 表体
  html += '<tbody>';
  for (let i = 0; i < tableForm.value.rows - 1; i++) {
    html += '<tr>';
    for (let j = 0; j < tableForm.value.cols; j++) {
      html += '<td style="border: 1px solid #ddd; padding: 8px;">内容</td>';
    }
    html += '</tr>';
  }
  html += '</tbody></table><p><br></p>';
  
  execCommand('insertHTML', html);
  tableDialogVisible.value = false;
};

// 监听value变化
watch(() => props.value, (newValue) => {
  if (newValue !== content.value) {
    content.value = newValue || '';
    if (editorRef.value && editorRef.value.innerHTML !== content.value) {
      editorRef.value.innerHTML = content.value;
    }
  }
});

// 初始化
onMounted(() => {
  if (editorRef.value && content.value) {
    editorRef.value.innerHTML = content.value;
  }
});
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #d9d9d9;
}

.editor-container {
  display: flex;
  min-height: 400px;
  background: #fff;
}

.editor-container.edit {
  .editor-pane {
    width: 100%;
  }
}

.editor-container.preview {
  .preview-pane {
    width: 100%;
  }
}

.editor-container.split {
  .editor-pane,
  .preview-pane {
    width: 50%;
  }
  
  .editor-pane {
    border-right: 1px solid #d9d9d9;
  }
}

.editor-pane,
.preview-pane {
  overflow-y: auto;
}

.editor-content {
  min-height: 400px;
  padding: 16px;
  outline: none;
  font-size: 14px;
  line-height: 1.6;
}

.editor-content:empty::before {
  content: attr(placeholder);
  color: #999;
}

.preview-content {
  padding: 16px;
  font-size: 14px;
  line-height: 1.6;
}

/* 编辑器内容样式 */
.editor-content h1,
.preview-content h1 {
  font-size: 28px;
  font-weight: 500;
  margin: 16px 0;
}

.editor-content h2,
.preview-content h2 {
  font-size: 24px;
  font-weight: 500;
  margin: 14px 0;
}

.editor-content h3,
.preview-content h3 {
  font-size: 20px;
  font-weight: 500;
  margin: 12px 0;
}

.editor-content h4,
.preview-content h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 10px 0;
}

.editor-content pre,
.preview-content pre {
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 12px;
  margin: 12px 0;
  overflow-x: auto;
}

.editor-content code,
.preview-content code {
  background: #f5f5f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.editor-content table,
.preview-content table {
  width: 100%;
  margin: 12px 0;
}

.editor-content img,
.preview-content img {
  max-width: 100%;
  height: auto;
}

.editor-content a,
.preview-content a {
  color: #1890ff;
  text-decoration: none;
}

.editor-content a:hover,
.preview-content a:hover {
  text-decoration: underline;
}

/* 移动端响应式样式 */
@media (max-width: 768px) {
  .editor-toolbar {
    padding: 6px 8px;
  }

  .editor-toolbar .ant-space {
    gap: 4px !important;
  }

  .editor-toolbar .ant-btn {
    min-width: 32px;
    height: 32px;
    padding: 0 8px;
  }

  .editor-toolbar .ant-btn-group .ant-btn {
    margin-right: -1px;
  }

  .editor-toolbar .ant-select {
    width: 100px !important;
  }

  .editor-toolbar .ant-tooltip {
    font-size: 12px;
  }

  .editor-container {
    min-height: 300px;
  }

  .editor-content,
  .preview-content {
    min-height: 300px;
    padding: 12px;
    font-size: 16px; /* 防止iOS缩放 */
  }

  .editor-container.split {
    flex-direction: column;

    .editor-pane,
    .preview-pane {
      width: 100%;
      min-height: 250px;
    }

    .editor-pane {
      border-right: none;
      border-bottom: 1px solid #d9d9d9;
    }
  }

  .mode-switch {
    flex-direction: column;
    gap: 8px;
  }

  .mode-switch .ant-radio-group {
    width: 100%;
  }
}
</style> 