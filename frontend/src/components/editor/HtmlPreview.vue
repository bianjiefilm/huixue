<template>
  <div
    ref="previewContainer"
    class="html-preview-container"
    :class="{ 'is-dragging': isDragging }"
    :style="{
      left: `${position.x}px`,
      top: `${position.y}px`,
      width: `${size.width}px`,
      height: `${size.height}px`,
      zIndex: isActive ? 10 : 5
    }"
    @mousedown="activatePreview"
  >
    <div class="preview-header" @mousedown="startDrag">
      <span class="preview-title">HTML 预览</span>
      <div class="preview-actions">
        <a-button-group size="small">
          <a-button @click="resizePreview('small')">小</a-button>
          <a-button @click="resizePreview('medium')">中</a-button>
          <a-button @click="resizePreview('large')">大</a-button>
        </a-button-group>
        <a-button type="primary" danger size="small" @click="closePreview">
          <template #icon><CloseOutlined /></template>
        </a-button>
      </div>
    </div>
    <div class="preview-content">
      <iframe ref="previewFrame" :srcdoc="htmlContent" sandbox="allow-scripts" frameborder="0"></iframe>
    </div>
    <div class="resize-handle bottom-right" @mousedown="startResize"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, watch } from 'vue';
import { CloseOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  htmlContent: {
    type: String,
    default: ''
  },
  isOpen: {
    type: Boolean,
    default: true
  },
  defaultPosition: {
    type: Object,
    default: () => ({ x: 20, y: 100 })
  },
  defaultSize: {
    type: Object,
    default: () => ({ width: 400, height: 300 })
  }
});

const emit = (['close', 'update:isOpen']);

// 引用
const previewContainer = ref<HTMLElement | null>(null);
const previewFrame = ref<HTMLIFrameElement | null>(null);

// 状态
const isDragging = ref(false);
const isResizing = ref(false);
const isActive = ref(false);
const position = reactive({ ...props.defaultPosition });
const size = reactive({ ...props.defaultSize });
const dragOffset = reactive({ x: 0, y: 0 });
const initialSize = reactive({ width: 0, height: 0 });
const initialPosition = reactive({ x: 0, y: 0 });

// 预定义大小
const sizePresets = {
  small: { width: 320, height: 240 },
  medium: { width: 480, height: 360 },
  large: { width: 640, height: 480 }
};

// 监听可见性
watch(() => props.isOpen, (value) => {
  if (previewContainer.value) {
    previewContainer.value.style.display = value ? 'flex' : 'none';
  }
});

// 激活预览
function activatePreview() {
  isActive.value = true;
}

// 开始拖动
function startDrag(event: MouseEvent) {
  if (event.target !== event.currentTarget) return;
  
  isDragging.value = true;
  isActive.value = true;
  
  const rect = previewContainer.value!.getBoundingClientRect();
  dragOffset.x = event.clientX - rect.left;
  dragOffset.y = event.clientY - rect.top;
  
  document.addEventListener('mousemove', handleDrag);
  document.addEventListener('mouseup', stopDrag);
  
  event.preventDefault();
}

// 处理拖动
function handleDrag(event: MouseEvent) {
  if (!isDragging.value) return;
  
  position.x = event.clientX - dragOffset.x;
  position.y = event.clientY - dragOffset.y;
  
  // 确保不会被拖出视口
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  
  if (position.x < 0) position.x = 0;
  if (position.y < 0) position.y = 0;
  if (position.x + size.width > viewportWidth) position.x = viewportWidth - size.width;
  if (position.y + size.height > viewportHeight) position.y = viewportHeight - size.height;
}

// 停止拖动
function stopDrag() {
  isDragging.value = false;
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
}

// 开始调整大小
function startResize(event: MouseEvent) {
  isResizing.value = true;
  isActive.value = true;
  
  initialSize.width = size.width;
  initialSize.height = size.height;
  initialPosition.x = event.clientX;
  initialPosition.y = event.clientY;
  
  document.addEventListener('mousemove', handleResize);
  document.addEventListener('mouseup', stopResize);
  
  event.stopPropagation();
  event.preventDefault();
}

// 处理大小调整
function handleResize(event: MouseEvent) {
  if (!isResizing.value) return;
  
  const deltaX = event.clientX - initialPosition.x;
  const deltaY = event.clientY - initialPosition.y;
  
  // 计算新尺寸，设置最小尺寸限制
  size.width = Math.max(200, initialSize.width + deltaX);
  size.height = Math.max(150, initialSize.height + deltaY);
}

// 停止调整大小
function stopResize() {
  isResizing.value = false;
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
}

// 调整预览窗口到预设大小
function resizePreview(preset: 'small' | 'medium' | 'large') {
  size.width = sizePresets[preset].width;
  size.height = sizePresets[preset].height;
}

// 关闭预览
function closePreview() {
  emit('close');
  emit('update:isOpen', false);
}

// 生命周期
onMounted(() => {
  // 确保组件初始状态正确
  if (previewContainer.value) {
    previewContainer.value.style.display = props.isOpen ? 'flex' : 'none';
  }
  
  // 点击外部区域取消活动状态
  document.addEventListener('mousedown', (event) => {
    if (previewContainer.value && !previewContainer.value.contains(event.target as Node)) {
      isActive.value = false;
    }
  });
});

onBeforeUnmount(() => {
  document.removeEventListener('mousemove', handleDrag);
  document.removeEventListener('mouseup', stopDrag);
  document.removeEventListener('mousemove', handleResize);
  document.removeEventListener('mouseup', stopResize);
});

// 公开方法 - 只暴露必要的方法
defineExpose({});
</script>

<style scoped>
.html-preview-container {
  position: fixed;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  resize: both;
  transition: box-shadow 0.2s;
  min-width: 200px;
  min-height: 150px;
}

.html-preview-container.is-dragging {
  opacity: 0.8;
  cursor: move;
}

.html-preview-container:hover,
.html-preview-container.is-active {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  cursor: move;
  user-select: none;
  border-bottom: 1px solid #e8e8e8;
}

.preview-title {
  font-weight: 500;
  font-size: 14px;
}

.preview-actions {
  display: flex;
  gap: 8px;
}

.preview-content {
  flex: 1;
  overflow: hidden;
  background-color: #fff;
}

.preview-content iframe {
  width: 100%;
  height: 100%;
  border: none;
  background-color: #fff;
}

.resize-handle {
  position: absolute;
  width: 16px;
  height: 16px;
  background-color: transparent;
  cursor: nwse-resize;
}

.bottom-right {
  right: 0;
  bottom: 0;
}
</style> 