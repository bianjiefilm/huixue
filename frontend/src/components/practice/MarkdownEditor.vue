<template>
  <div class="markdown-editor-container">
    <div class="editor-toolbar">
      <a-space>
        <a-tooltip title="加粗">
          <a-button size="small" type="text" @click="insertBold">
            <template #icon><BoldOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-tooltip title="斜体">
          <a-button size="small" type="text" @click="insertItalic">
            <template #icon><ItalicOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-tooltip title="标题">
          <a-button size="small" type="text" @click="insertHeading">
            <template #icon><FontSizeOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-divider type="vertical" />
        
        <a-tooltip title="无序列表">
          <a-button size="small" type="text" @click="insertUnorderedList">
            <template #icon><UnorderedListOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-tooltip title="有序列表">
          <a-button size="small" type="text" @click="insertOrderedList">
            <template #icon><OrderedListOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-divider type="vertical" />
        
        <a-tooltip title="代码块">
          <a-button size="small" type="text" @click="insertCodeBlock">
            <template #icon><CodeOutlined /></template>
          </a-button>
        </a-tooltip>
        
        <a-tooltip title="链接">
          <a-button size="small" type="text" @click="insertLink">
            <template #icon><LinkOutlined /></template>
          </a-button>
        </a-tooltip>

        <a-divider type="vertical" />

        <a-tooltip title="图片（点击或粘贴）">
          <a-button size="small" type="text" @click="triggerImageUpload">
            <template #icon><FileImageOutlined /></template>
          </a-button>
        </a-tooltip>
        <input
          ref="imageInputRef"
          type="file"
          accept="image/*"
          style="display: none"
          @change="handleImageSelect"
        />
        
        <a-divider type="vertical" />
        
        <a-radio-group v-model:value="viewMode" size="small">
          <a-radio-button value="edit">编辑</a-radio-button>
          <a-radio-button value="preview">预览</a-radio-button>
          <a-radio-button value="split">分屏</a-radio-button>
        </a-radio-group>
      </a-space>
    </div>
    
    <div class="editor-content" :class="viewMode">
      <div v-if="viewMode !== 'preview'" class="editor-input">
        <a-textarea
          ref="textareaRef"
          v-model:value="content"
          :placeholder="placeholder"
          :auto-size="false"
          :style="{ height: height + 'px' }"
          @change="handleChange"
          @paste="handlePaste"
        />
      </div>
      
      <div v-if="viewMode !== 'edit'" class="editor-preview">
        <div
          class="markdown-body"
          v-html="renderedContent"
          :style="{ height: height + 'px' }"
        ></div>
      </div>
    </div>
    
    <!-- 模板提示 -->
    <div v-if="showTemplate" class="editor-template">
      <a-alert
        message="过关任务模板"
        type="info"
        closable
        @close="showTemplate = false"
      >
        <template #description>
          <pre>## 任务目标
本关的学习目标是...

## 相关知识
本关涉及的知识点包括：
- 知识点1
- 知识点2

## 编程要求
请按照以下要求完成代码：
1. 要求1
2. 要求2

## 测试说明
本关的测试将验证...

## 提示
- 提示1
- 提示2</pre>
        </template>
      </a-alert>
    </div>

    <!-- 图片上传提示 -->
    <div class="image-upload-tip">
      <a-alert
        v-if="showImageTip"
        message="图片粘贴提示"
        description="可以直接Ctrl+V粘贴图片到编辑器中，或点击工具栏图片按钮选择文件。支持 JPG、PNG、GIF 格式，单张最大 2MB。"
        type="info"
        show-icon
        closable
        @close="showImageTip = false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import {
  BoldOutlined,
  ItalicOutlined,
  FontSizeOutlined,
  UnorderedListOutlined,
  OrderedListOutlined,
  CodeOutlined,
  LinkOutlined,
  FileImageOutlined
} from '@ant-design/icons-vue';

const props = withDefaults(defineProps<{
  value?: string;
  placeholder?: string;
  height?: number;
  showTemplate?: boolean;
}>(), {
  placeholder: '请输入内容，支持Markdown格式',
  height: 400,
  showTemplate: false
});

const emit = defineEmits<{
  (e: 'update:value', value: string): void;
  (e: 'change', value: string): void;
}>();

const textareaRef = ref();
const imageInputRef = ref();
const viewMode = ref<'edit' | 'preview' | 'split'>('edit');
const showTemplate = ref(props.showTemplate);
const showImageTip = ref(true);

// 内容
const content = computed({
  get: () => props.value || '',
  set: (value) => {
    emit('update:value', value);
    emit('change', value);
  }
});

// 渲染后的内容（简单的Markdown渲染）
const renderedContent = computed(() => {
  let html = content.value;
  
  // 转义HTML
  html = html.replace(/&/g, '&amp;')
             .replace(/</g, '&lt;')
             .replace(/>/g, '&gt;');
  
  // 标题
  html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');
  
  // 加粗和斜体
  html = html.replace(/\*\*\*(.*?)\*\*\*/g, '<strong><em>$1</em></strong>');
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  
  // 代码块
  html = html.replace(/```(.*?)```/gs, '<pre><code>$1</code></pre>');
  html = html.replace(/`(.*?)`/g, '<code>$1</code>');
  
  // 列表
  html = html.replace(/^\* (.*)$/gm, '<li>$1</li>');
  html = html.replace(/^\d+\. (.*)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
  
  // 换行
  html = html.replace(/\n/g, '<br>');
  
  return html;
});

// 插入文本
const insertText = (text: string, cursorOffset = 0) => {
  const textarea = textareaRef.value?.$el?.querySelector('textarea');
  if (!textarea) return;
  
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const value = content.value;
  
  content.value = value.substring(0, start) + text + value.substring(end);
  
  // 恢复光标位置
  setTimeout(() => {
    textarea.focus();
    textarea.setSelectionRange(start + cursorOffset, start + cursorOffset);
  }, 0);
};

// 工具栏操作
const insertBold = () => insertText('**粗体文本**', 2);
const insertItalic = () => insertText('*斜体文本*', 1);
const insertHeading = () => insertText('\n## 标题\n', 4);
const insertUnorderedList = () => insertText('\n* 列表项1\n* 列表项2\n* 列表项3\n', 3);
const insertOrderedList = () => insertText('\n1. 列表项1\n2. 列表项2\n3. 列表项3\n', 3);
const insertCodeBlock = () => insertText('\n```\n代码块\n```\n', 5);
const insertLink = () => insertText('[链接文本](https://example.com)', 1);

// 图片上传相关
const triggerImageUpload = () => {
  imageInputRef.value?.click();
};

const handleImageSelect = (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (file) {
    processImageFile(file);
  }
  // 清空input以便重复选择同一文件
  (event.target as HTMLInputElement).value = '';
};

const processImageFile = (file: File) => {
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    message.warning('请选择图片文件');
    return;
  }

  // 检查文件大小（限制为2MB）
  const maxSize = 2 * 1024 * 1024;
  if (file.size > maxSize) {
    message.warning('图片大小不能超过2MB');
    return;
  }

  // 使用FileReader读取图片并转换为base64
  const reader = new FileReader();
  reader.onload = (e) => {
    const base64 = e.target?.result as string;
    // 插入图片Markdown
    insertText(`\n![${file.name}](${base64})\n`, 0);
    message.success('图片已插入');
  };
  reader.onerror = () => {
    message.error('图片读取失败');
  };
  reader.readAsDataURL(file);
};

// 处理粘贴事件（支持图片粘贴）
const handlePaste = (event: ClipboardEvent) => {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      event.preventDefault();
      const file = item.getAsFile();
      if (file) {
        processImageFile(file);
      }
      return;
    }
  }
};

// 处理变化
const handleChange = () => {
  // 已通过v-model处理
};

// 初始化时设置默认模板
onMounted(() => {
  if (props.showTemplate && !content.value) {
    content.value = `## 任务目标
本关的学习目标是...

## 相关知识
本关涉及的知识点包括：
- 知识点1
- 知识点2

## 编程要求
请按照以下要求完成代码：
1. 要求1
2. 要求2

## 测试说明
本关的测试将验证...

## 提示
- 提示1
- 提示2`;
  }
});
</script>

<style scoped>
.markdown-editor-container {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  padding: 8px 12px;
  background: #fafafa;
  border-bottom: 1px solid #d9d9d9;
}

.editor-content {
  display: flex;
  background: #fff;
}

.editor-content.edit .editor-input {
  width: 100%;
}

.editor-content.preview .editor-preview {
  width: 100%;
}

.editor-content.split .editor-input,
.editor-content.split .editor-preview {
  width: 50%;
}

.editor-input {
  border-right: 1px solid #d9d9d9;
}

.editor-input :deep(textarea) {
  border: none;
  resize: none;
  padding: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
}

.editor-input :deep(.ant-input-textarea) {
  height: 100%;
}

.editor-preview {
  padding: 12px;
  overflow-y: auto;
  background: #fff;
}

.markdown-body {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin: 16px 0 8px;
  font-weight: 600;
}

.markdown-body h1 { font-size: 24px; }
.markdown-body h2 { font-size: 20px; }
.markdown-body h3 { font-size: 16px; }

.markdown-body p {
  margin: 8px 0;
}

.markdown-body ul,
.markdown-body ol {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-body li {
  margin: 4px 0;
}

.markdown-body code {
  padding: 2px 4px;
  background: #f5f5f5;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
}

.markdown-body pre {
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-body pre code {
  padding: 0;
  background: none;
}

.markdown-body a {
  color: #1890ff;
  text-decoration: none;
}

.markdown-body a:hover {
  text-decoration: underline;
}

.editor-template {
  margin-top: 16px;
}

.editor-template pre {
  margin: 0;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.65);
}

.image-upload-tip {
  margin-top: 8px;
}

.image-upload-tip :deep(.ant-alert) {
  padding: 8px 12px;
}
</style>