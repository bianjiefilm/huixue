<template>
  <Teleport to="body">
    <div
      v-show="isVisible"
      ref="previewContainer"
      class="preview-window"
      :class="{ 'is-dragging': isDragging, 'is-resizing': isResizing }"
      :style="{
        left: `${position.x}px`,
        top: `${position.y}px`,
        width: `${size.width}px`,
        height: `${size.height}px`,
        zIndex: isActive ? 1000 : 999
      }"
      @mousedown="activateWindow"
    >
      <!-- 窗口标题栏 -->
      <div class="preview-header" @mousedown="startDrag">
        <div class="preview-title">
          <EyeOutlined />
          <span>页面预览</span>
        </div>
        <div class="preview-actions">
          <a-button-group size="small">
            <a-button @click="resizeToPreset('small')">小</a-button>
            <a-button @click="resizeToPreset('medium')">中</a-button>
            <a-button @click="resizeToPreset('large')">大</a-button>
            <a-button @click="toggleMaximize" :type="isMaximized ? 'primary' : 'default'">
              <template #icon>
                <ExpandOutlined v-if="!isMaximized" />
                <CompressOutlined v-else />
              </template>
            </a-button>
          </a-button-group>
          <a-button type="text" size="small" @click="closeWindow">
            <template #icon><CloseOutlined /></template>
          </a-button>
        </div>
      </div>

      <!-- 预览内容区域 -->
      <div class="preview-content">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="preview-loading">
          <a-spin size="small" />
          <span>加载中...</span>
        </div>
        <!-- 设备模拟容器 -->
        <div 
          class="device-simulator"
          :style="{
            width: deviceWidth,
            maxWidth: '100%',
            margin: deviceWidth !== '100%' ? '0 auto' : '0',
            height: '100%',
            background: deviceWidth !== '100%' ? '#f0f0f0' : 'transparent',
            borderRadius: deviceWidth !== '100%' ? '8px' : '0',
            boxShadow: deviceWidth !== '100%' ? '0 4px 12px rgba(0,0,0,0.15)' : 'none',
            overflow: 'hidden'
          }"
        >
          <div v-if="deviceWidth !== '100%'" class="device-label">
            {{ deviceLabel }} ({{ deviceWidth }})
          </div>
          <iframe
            v-if="!isLoading"
            ref="previewFrame"
            :srcdoc="combinedHtml"
            sandbox="allow-scripts allow-forms allow-same-origin"
            frameborder="0"
            @load="onIframeLoad"
            :style="{ height: deviceWidth !== '100%' ? 'calc(100% - 24px)' : '100%' }"
          ></iframe>
        </div>
      </div>

      <!-- 调整大小手柄 -->
      <div class="resize-handles">
        <div class="resize-handle top" @mousedown="startResize('top')"></div>
        <div class="resize-handle right" @mousedown="startResize('right')"></div>
        <div class="resize-handle bottom" @mousedown="startResize('bottom')"></div>
        <div class="resize-handle left" @mousedown="startResize('left')"></div>
        <div class="resize-handle top-right" @mousedown="startResize('top-right')"></div>
        <div class="resize-handle bottom-right" @mousedown="startResize('bottom-right')"></div>
        <div class="resize-handle bottom-left" @mousedown="startResize('bottom-left')"></div>
        <div class="resize-handle top-left" @mousedown="startResize('top-left')"></div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { EyeOutlined, CloseOutlined, ExpandOutlined, CompressOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  htmlContent: {
    type: String,
    default: ''
  },
  cssContent: {
    type: String,
    default: ''
  },
  jsContent: {
    type: String,
    default: ''
  },
  isVisible: {
    type: Boolean,
    default: false
  },
  taskId: {
    type: String,
    default: ''
  },
  deviceWidth: {
    type: String,
    default: '100%'
  },
  deviceLabel: {
    type: String,
    default: '桌面'
  }
})

// Emits
const emit = defineEmits(['close', 'update:isVisible'])

// Refs
const previewContainer = ref<HTMLElement | null>(null)
const previewFrame = ref<HTMLIFrameElement | null>(null)

// 状态
const isDragging = ref(false)
const isResizing = ref(false)
const isActive = ref(false)
const isLoading = ref(false)
const isMaximized = ref(false)

// 位置和大小 - 默认位置在右侧代码编辑器区域
const position = reactive({ x: Math.max(100, window.innerWidth - 500), y: 100 })
const size = reactive({ width: 400, height: 500 })
const previousState = reactive({ position: { x: 0, y: 0 }, size: { width: 0, height: 0 } })

// 拖拽相关
const dragOffset = reactive({ x: 0, y: 0 })

// 调整大小相关
const resizeType = ref('')
const initialSize = reactive({ width: 0, height: 0 })
const initialPosition = reactive({ x: 0, y: 0 })

// 预设大小
const sizePresets = {
  small: { width: 480, height: 320 },
  medium: { width: 800, height: 600 },
  large: { width: 1200, height: 800 }
}

// 本地存储键
const getStorageKey = (key: string) => `preview_window_${props.taskId}_${key}`

// 组合HTML内容
const combinedHtml = computed(() => {
  const html = props.htmlContent || '<html><head><title>预览</title></head><body><h1>页面预览</h1><p>请在编辑器中输入HTML代码</p></body></html>'

  // 注入CSS
  let processedHtml = html
  if (props.cssContent) {
    // 如果HTML中已经有<style>标签，替换内容；否则添加
    if (processedHtml.includes('<style>')) {
      const styleRegex = /(<style[^>]*>)([\s\S]*?)(<\/style>)/;
      processedHtml = processedHtml.replace(styleRegex, '$1' + props.cssContent + '$3');
    } else {
      const styleTag = '<style>' + props.cssContent + '</' + 'style>';
      processedHtml = processedHtml.replace('</head>', styleTag + '</head>');
    }
  }

  // 注入JavaScript
  if (props.jsContent) {
    // 如果HTML中已经有<script>标签，替换内容；否则添加
    if (processedHtml.includes('<script>') && !processedHtml.includes('<script src=')) {
      const scriptRegex = /(<script[^>]*>)([\s\S]*?)(<\/script>)/;
      processedHtml = processedHtml.replace(scriptRegex, '$1' + props.jsContent + '$3');
    } else {
      const scriptTag = '<script>' + props.jsContent + '</' + 'script>';
      processedHtml = processedHtml.replace('</body>', scriptTag + '</body>');
    }
  }

  return processedHtml
})

// 监听可见性变化
watch(() => props.isVisible, (visible) => {
  if (visible) {
    loadWindowState()
    nextTick(() => {
      updatePreview()
    })
  } else {
    saveWindowState()
  }
})

// 监听内容变化，实时更新预览
watch([() => props.htmlContent, () => props.cssContent, () => props.jsContent], () => {
  if (props.isVisible) {
    updatePreview()
  }
}, { debounce: 300 }) // 防抖300ms

// 激活窗口
function activateWindow() {
  isActive.value = true
}

// 开始拖拽
function startDrag(event: MouseEvent) {
  if (isMaximized.value) return

  isDragging.value = true
  isActive.value = true

  const rect = previewContainer.value!.getBoundingClientRect()
  dragOffset.x = event.clientX - rect.left
  dragOffset.y = event.clientY - rect.top

  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', stopDrag)

  event.preventDefault()
}

// 处理拖拽
function handleDrag(event: MouseEvent) {
  if (!isDragging.value || isMaximized.value) return

  const newX = event.clientX - dragOffset.x
  const newY = event.clientY - dragOffset.y

  // 边界检查
  const maxX = window.innerWidth - size.width
  const maxY = window.innerHeight - size.height

  position.x = Math.max(0, Math.min(newX, maxX))
  position.y = Math.max(0, Math.min(newY, maxY))
}

// 停止拖拽
function stopDrag() {
  isDragging.value = false
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// 开始调整大小
function startResize(type: string, event: MouseEvent) {
  if (isMaximized.value) return

  isResizing.value = true
  isActive.value = true
  resizeType.value = type

  initialSize.width = size.width
  initialSize.height = size.height
  initialPosition.x = event.clientX
  initialPosition.y = event.clientY

  document.addEventListener('mousemove', handleResize)
  document.addEventListener('mouseup', stopResize)

  event.stopPropagation()
  event.preventDefault()
}

// 处理调整大小
function handleResize(event: MouseEvent) {
  if (!isResizing.value || isMaximized.value) return

  const deltaX = event.clientX - initialPosition.x
  const deltaY = event.clientY - initialPosition.y

  switch (resizeType.value) {
    case 'right':
      size.width = Math.max(400, initialSize.width + deltaX)
      break
    case 'bottom':
      size.height = Math.max(300, initialSize.height + deltaY)
      break
    case 'bottom-right':
      size.width = Math.max(400, initialSize.width + deltaX)
      size.height = Math.max(300, initialSize.height + deltaY)
      break
    case 'left':
      const newWidth = Math.max(400, initialSize.width - deltaX)
      if (newWidth !== size.width) {
        size.width = newWidth
        position.x = Math.max(0, initialPosition.x - (newWidth - initialSize.width))
      }
      break
    case 'top':
      const newHeight = Math.max(300, initialSize.height - deltaY)
      if (newHeight !== size.height) {
        size.height = newHeight
        position.y = Math.max(0, initialPosition.y - (newHeight - initialSize.height))
      }
      break
    case 'top-right':
      size.width = Math.max(400, initialSize.width + deltaX)
      const newHeightTR = Math.max(300, initialSize.height - deltaY)
      if (newHeightTR !== size.height) {
        size.height = newHeightTR
        position.y = Math.max(0, initialPosition.y - (newHeightTR - initialSize.height))
      }
      break
    case 'bottom-left':
      const newWidthBL = Math.max(400, initialSize.width - deltaX)
      if (newWidthBL !== size.width) {
        size.width = newWidthBL
        position.x = Math.max(0, initialPosition.x - (newWidthBL - initialSize.width))
      }
      size.height = Math.max(300, initialSize.height + deltaY)
      break
    case 'top-left':
      const newWidthTL = Math.max(400, initialSize.width - deltaX)
      const newHeightTL = Math.max(300, initialSize.height - deltaY)
      if (newWidthTL !== size.width) {
        size.width = newWidthTL
        position.x = Math.max(0, initialPosition.x - (newWidthTL - initialSize.width))
      }
      if (newHeightTL !== size.height) {
        size.height = newHeightTL
        position.y = Math.max(0, initialPosition.y - (newHeightTL - initialSize.height))
      }
      break
  }
}

// 停止调整大小
function stopResize() {
  isResizing.value = false
  resizeType.value = ''
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
}

// 调整到预设大小
function resizeToPreset(preset: 'small' | 'medium' | 'large') {
  size.width = sizePresets[preset].width
  size.height = sizePresets[preset].height
  isMaximized.value = false
}

// 切换最大化
function toggleMaximize() {
  if (isMaximized.value) {
    // 恢复到之前的大小
    position.x = previousState.position.x
    position.y = previousState.position.y
    size.width = previousState.size.width
    size.height = previousState.size.height
    isMaximized.value = false
  } else {
    // 保存当前状态并最大化
    previousState.position.x = position.x
    previousState.position.y = position.y
    previousState.size.width = size.width
    previousState.size.height = size.height

    position.x = 0
    position.y = 0
    size.width = window.innerWidth
    size.height = window.innerHeight
    isMaximized.value = true
  }
}

// 更新预览内容
function updatePreview() {
  if (!previewFrame.value) return

  isLoading.value = true

  try {
    // 更新iframe的srcdoc
    previewFrame.value.srcdoc = combinedHtml.value
  } catch (error) {
    console.error('更新预览失败:', error)
    message.error('预览更新失败')
  } finally {
    // 延迟隐藏加载状态
    setTimeout(() => {
      isLoading.value = false
    }, 300)
  }
}

// iframe加载完成
function onIframeLoad() {
  isLoading.value = false
}

// 关闭窗口
function closeWindow() {
  emit('close')
  emit('update:isVisible', false)
}

// 加载窗口状态
function loadWindowState() {
  try {
    const savedPosition = localStorage.getItem(getStorageKey('position'))
    const savedSize = localStorage.getItem(getStorageKey('size'))
    const savedMaximized = localStorage.getItem(getStorageKey('maximized'))

    if (savedPosition) {
      const pos = JSON.parse(savedPosition)
      position.x = pos.x
      position.y = pos.y
    }

    if (savedSize) {
      const sz = JSON.parse(savedSize)
      size.width = sz.width
      size.height = sz.height
    }

    if (savedMaximized) {
      isMaximized.value = JSON.parse(savedMaximized)
    }
  } catch (error) {
    console.warn('加载预览窗口状态失败:', error)
  }
}

// 保存窗口状态
function saveWindowState() {
  try {
    localStorage.setItem(getStorageKey('position'), JSON.stringify(position))
    localStorage.setItem(getStorageKey('size'), JSON.stringify(size))
    localStorage.setItem(getStorageKey('maximized'), JSON.stringify(isMaximized.value))
  } catch (error) {
    console.warn('保存预览窗口状态失败:', error)
  }
}

// 生命周期
onMounted(() => {
  loadWindowState()

  // 全局点击事件，用于取消活动状态
  document.addEventListener('mousedown', (event) => {
    if (previewContainer.value && !previewContainer.value.contains(event.target as Node)) {
      isActive.value = false
    }
  })

  // 窗口大小改变时调整最大化状态
  window.addEventListener('resize', () => {
    if (isMaximized.value) {
      size.width = window.innerWidth
      size.height = window.innerHeight
    }
  })
})

onBeforeUnmount(() => {
  saveWindowState()

  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.removeEventListener('mousemove', handleResize)
  document.removeEventListener('mouseup', stopResize)
})

// 暴露方法
defineExpose({
  updatePreview
})
</script>

<style scoped>
.preview-window {
  position: fixed;
  display: flex;
  flex-direction: column;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  min-width: 400px;
  min-height: 300px;
  z-index: 999;
}

.preview-window.is-dragging {
  opacity: 0.9;
  cursor: move;
  user-select: none;
}

.preview-window.is-resizing {
  cursor: nw-resize;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f5f5f5;
  border-bottom: 1px solid #e8e8e8;
  cursor: move;
  user-select: none;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #262626;
}

.preview-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.preview-content {
  flex: 1;
  position: relative;
  background: #fff;
  overflow: hidden;
}

.preview-content iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}

.device-simulator {
  transition: all 0.3s ease;
}

.device-label {
  text-align: center;
  padding: 4px 0;
  background: #e8e8e8;
  font-size: 12px;
  color: #666;
  border-bottom: 1px solid #d9d9d9;
}

.preview-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #666;
  font-size: 14px;
}

.resize-handles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  pointer-events: auto;
  background: transparent;
}

.resize-handle.top {
  top: -2px;
  left: 0;
  right: 0;
  height: 6px;
  cursor: n-resize;
}

.resize-handle.right {
  top: 0;
  right: -2px;
  bottom: 0;
  width: 6px;
  cursor: e-resize;
}

.resize-handle.bottom {
  bottom: -2px;
  left: 0;
  right: 0;
  height: 6px;
  cursor: s-resize;
}

.resize-handle.left {
  top: 0;
  left: -2px;
  bottom: 0;
  width: 6px;
  cursor: w-resize;
}

.resize-handle.top-right {
  top: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  cursor: ne-resize;
}

.resize-handle.bottom-right {
  bottom: -2px;
  right: -2px;
  width: 12px;
  height: 12px;
  cursor: se-resize;
}

.resize-handle.bottom-left {
  bottom: -2px;
  left: -2px;
  width: 12px;
  height: 12px;
  cursor: sw-resize;
}

.resize-handle.top-left {
  top: -2px;
  left: -2px;
  width: 12px;
  height: 12px;
  cursor: nw-resize;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preview-window {
    min-width: 300px;
    min-height: 200px;
  }

  .preview-header {
    padding: 6px 12px;
  }

  .preview-actions {
    gap: 4px;
  }
}
</style>
