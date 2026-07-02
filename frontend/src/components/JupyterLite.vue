<template>
  <div class="jupyter-container">
    <!-- Loading 覆盖层 -->
    <div v-if="loading" class="loading-overlay">
      <a-spin size="large" tip="正在启动 Jupyter 环境..." />
    </div>

    <!-- Error 显示 -->
    <div v-if="error" class="error-container">
      <a-alert
        :message="error"
        type="error"
        show-icon
        :closable="false"
      />
    </div>

    <!-- Iframe 始终渲染，但在加载时被覆盖 -->
    <iframe
      v-if="jupyterUrl"
      ref="jupyterFrame"
      :src="jupyterUrl"
      width="100%"
      height="100%"
      frameborder="0"
      @load="handleLoad"
      @error="handleError"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';

interface Props {
  url?: string;
  notebookId?: string;
  token?: string;
  environmentId?: string;
}

const props = withDefaults(defineProps<Props>(), {
  url: '',
  notebookId: '',
  token: '',
  environmentId: ''
});

const emit = defineEmits<{
  loaded: [];
  error: [error: string];
}>();

const jupyterUrl = ref('');
const jupyterFrame = ref();
const loading = ref(true);
const error = ref('');

// 构建 Jupyter URL
const buildJupyterUrl = () => {
  if (props.url) {
    // 如果提供了完整的 URL，直接使用
    return props.url;
  } else if (props.notebookId && props.token) {
    // 如果提供了 notebook ID 和 token，构建 URL
    // 动态获取服务器地址
    const hostname = window.location.hostname;
    const baseUrl = import.meta.env.VITE_JUPYTER_BASE_URL || (hostname === 'localhost' || hostname === '127.0.0.1'
      ? 'http://localhost:8888'
      : `http://${hostname}:8888`);
    return `${baseUrl}/notebooks/${props.notebookId}.ipynb?token=${props.token}`;
  }
  return '';
};

// 处理加载完成
const handleLoad = () => {
  console.log('Jupyter iframe loaded');
  loading.value = false;
  error.value = '';
  emit('loaded');
};

// 处理加载错误
const handleError = () => {
  console.log('Jupyter iframe error');
  loading.value = false;
  error.value = '无法加载 Jupyter 环境，请检查网络连接或联系管理员';
  emit('error', error.value);
};

watch(
  () => [props.url, props.notebookId, props.token],
  () => {
    const newUrl = buildJupyterUrl();
    console.log('JupyterLite URL:', newUrl);
    if (newUrl && newUrl !== jupyterUrl.value) {
      loading.value = true;
      error.value = '';
      jupyterUrl.value = newUrl;
    }
  },
  { immediate: true }
);

onMounted(() => {
  console.log('JupyterLite mounted, props:', props);
});
</script>

<style scoped>
.jupyter-container {
  width: 100%;
  height: calc(100vh - 64px); /* 减去头部导航的高度 */
  position: relative;
  background-color: #f5f5f5;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.9);
  z-index: 100;
}

.error-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80%;
  max-width: 500px;
  z-index: 101;
}
</style>
