<template>
  <div class="monaco-editor-container" ref="editorContainer"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import { monaco } from '../../plugins/monaco';

// 定义组件的属性
const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'python'
  },
  theme: {
    type: String,
    default: 'vs'
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  options: {
    type: Object,
    default: () => ({})
  }
});

// 定义组件的事件
const emit = defineEmits(['update:value', 'change', 'mounted', 'error']);

// 编辑器容器和实例引用
const editorContainer = ref<HTMLElement | null>(null);
let editor: monaco.editor.IStandaloneCodeEditor | null = null;

// 初始化编辑器
const initEditor = () => {
  if (!editorContainer.value) {
    console.error('[Monaco] 容器不存在，无法初始化');
    emit('error', '编辑器容器不存在');
    return;
  }

  try {
    // 默认选项
    const defaultOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
      value: props.value,
      language: props.language,
      theme: props.theme,
      automaticLayout: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      readOnly: props.readOnly,
      fontSize: 14,
      wordWrap: 'on',
      lineNumbers: 'on',
      tabSize: 4,
      insertSpaces: true
    };

    // 合并自定义选项
    const options = {
      ...defaultOptions,
      ...props.options
    };

    console.log('[Monaco] 开始创建编辑器实例，选项:', options);
    
    // 创建编辑器实例
    editor = monaco.editor.create(editorContainer.value, options);
    
    console.log('[Monaco] 编辑器创建成功');

    // 监听内容变化事件
    editor.onDidChangeModelContent(() => {
      const value = editor?.getValue() || '';
      emit('update:value', value);
      emit('change', value);
    });
    
    // 触发mounted事件
    emit('mounted', editor);
    
  } catch (error) {
    console.error('[Monaco] 初始化编辑器失败:', error);
    emit('error', error);
  }
};

// 销毁编辑器
const destroyEditor = () => {
  if (editor) {
    editor.dispose();
    editor = null;
  }
};

// 组件挂载时初始化编辑器
onMounted(() => {
  // 确保容器存在且有尺寸
  if (!editorContainer.value) {
    console.error('[Monaco] 编辑器容器不存在');
    return;
  }
  
  // 检查容器尺寸
  const rect = editorContainer.value.getBoundingClientRect();
  console.log('[Monaco] 容器尺寸:', rect.width, 'x', rect.height);
  
  if (rect.width === 0 || rect.height === 0) {
    console.warn('[Monaco] 容器尺寸为0，延迟初始化');
    // 使用requestAnimationFrame确保在下一帧渲染后初始化
    requestAnimationFrame(() => {
      const newRect = editorContainer.value?.getBoundingClientRect();
      if (newRect && newRect.width > 0 && newRect.height > 0) {
        console.log('[Monaco] 延迟初始化，新尺寸:', newRect.width, 'x', newRect.height);
        initEditor();
      } else {
        // 如果还是没有尺寸，再延迟一次
        setTimeout(() => {
          console.log('[Monaco] 第二次延迟初始化');
          initEditor();
        }, 200);
      }
    });
  } else {
    initEditor();
  }
});

// 组件卸载前销毁编辑器
onBeforeUnmount(() => {
  destroyEditor();
});

// 监听值变化
watch(
  () => props.value,
  (newValue) => {
    if (editor && editor.getValue() !== newValue) {
      editor.setValue(newValue);
    }
  }
);

// 监听语言变化
watch(
  () => props.language,
  (newLang) => {
    if (editor) {
      monaco.editor.setModelLanguage(editor.getModel()!, newLang);
    }
  }
);

// 监听主题变化 
watch(
  () => props.theme,
  (newTheme) => {
    if (editor) {
      monaco.editor.setTheme(newTheme);
    }
  }
);

// 暴露一些方法给父组件
defineExpose({
  focus: () => editor?.focus(),
  getEditor: () => editor,
  setValue: (value: string) => editor?.setValue(value),
  getValue: () => editor?.getValue() || ''
});
</script>

<style scoped>
.monaco-editor-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}
</style> 