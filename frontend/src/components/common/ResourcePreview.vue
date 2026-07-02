<template>
  <div class="resource-preview">
    <a-modal
      v-model:open="visible"
      :width="modalWidth"
      :height="modalHeight"
      :style="modalStyle"
      :footer="null"
      :destroyOnClose="true"
      :maskClosable="true"
      :wrapClassName="isMaximized ? 'maximized-modal' : ''"
    >
      <template #title>
        <div class="modal-title">
          <span>{{ resource?.title || '资源预览' }}</span>
          <a-button
            type="text"
            size="small"
            @click="toggleMaximize"
            class="maximize-btn"
          >
            <template #icon>
              <FullscreenOutlined v-if="!isMaximized" />
              <FullscreenExitOutlined v-else />
            </template>
          </a-button>
        </div>
      </template>
      <div class="preview-container">
        <!-- PDF 预览 - 使用embed标签直接显示PDF内容 -->
        <div v-if="resourceType === 'pdf'" class="pdf-preview">
          <embed
            :src="previewUrl"
            type="application/pdf"
            width="100%"
            :height="pdfHeight"
            style="border: none; border-radius: 8px;"
          />
          <div class="pdf-controls" style="margin-top: 10px; text-align: center;">
            <a-button @click="downloadResource">
              <template #icon><DownloadOutlined /></template>
              下载PDF
            </a-button>
          </div>
          <div class="pdf-fallback" v-if="!isPdfSupported">
            <p>您的浏览器不支持PDF预览，请<a :href="downloadUrl" target="_blank">下载查看</a></p>
          </div>
        </div>

        <!-- Office 文档预览 -->
        <div v-else-if="resourceType === 'office'" class="office-preview">
          <iframe
            :src="previewUrl"
            width="100%"
            height="600px"
            frameborder="0"
          />
        </div>

        <!-- Word 文档预览 -->
        <div v-else-if="resourceType === 'word'" class="word-preview">
          <!-- 加载中状态 (使用v-show保持容器始终存在) -->
          <div v-show="docxLoading" class="docx-loading">
            <LoadingOutlined style="font-size: 48px; color: #1890ff;" spin />
            <p>正在加载文档...</p>
          </div>
          <!-- 加载错误状态 -->
          <div v-show="docxError && !docxLoading" class="docx-error">
            <a-result
              status="error"
              title="文档加载失败"
              :sub-title="docxErrorMsg"
            />
          </div>
          <!-- docx 渲染容器 (始终存在，仅隐藏) -->
          <div ref="docxContainer" class="docx-container" v-show="!docxLoading && !docxError"></div>
        </div>

        <!-- 视频预览 -->
        <div v-else-if="resourceType === 'video'" class="video-preview">
          <video
            ref="videoPlayer"
            :src="previewUrl"
            controls
            preload="metadata"
            playsinline
            style="width: 100%; max-height: 600px; border-radius: 8px; background: #000;"
            @error="onVideoError"
            @loadedmetadata="onVideoLoadedMetadata"
          >
            您的浏览器不支持视频播放。
          </video>
          
          <!-- 视频控制栏 -->
          <div class="video-controls" style="margin-top: 15px; text-align: center;">
            <a-button @click="openInNewTab">
              <template #icon><FullscreenOutlined /></template>
              新窗口播放
            </a-button>
            <a-button style="margin-left: 8px;" @click="downloadResource">
              <template #icon><DownloadOutlined /></template>
              下载
            </a-button>
          </div>
        </div>

        <!-- 图片预览 -->
        <div v-else-if="resourceType === 'image'" class="image-preview">
          <img :src="previewUrl" alt="预览图片" class="preview-image" />
        </div>

        <!-- Markdown 预览 -->
        <div v-else-if="resourceType === 'markdown'" class="markdown-preview">
          <iframe
            :src="previewUrl + '?preview=true'"
            width="100%"
            height="600px"
            frameborder="0"
          />
        </div>

        <!-- JSON/配置文件预览 -->
        <div v-else-if="resourceType === 'json'" class="json-preview">
          <a-card title="配置文件内容" size="small">
            <pre>{{ resource?.content || '暂无内容' }}</pre>
          </a-card>
        </div>

        <!-- 试卷预览（教师专用） -->
        <div v-else-if="resourceType === 'exam'" class="exam-preview">
          <a-alert
            v-if="!hasExamPermission"
            message="权限不足"
            description="只有教师用户才能预览试卷内容"
            type="error"
            show-icon
          />
          <div v-else class="exam-content">
            <a-card title="试卷预览" size="small">
              <div class="exam-info">
                <p><strong>试卷标题：</strong>{{ resource?.title }}</p>
                <p><strong>考试类型：</strong>{{ resource?.examType }}</p>
                <p><strong>题目数量：</strong>{{ resource?.questionCount }}</p>
                <p><strong>总分：</strong>{{ resource?.totalScore }}</p>
              </div>
              <a-divider />
              <div class="exam-questions">
                <p>试卷内容将在考试开始时显示</p>
              </div>
            </a-card>
          </div>
        </div>

        <!-- 不支持的格式 -->
        <div v-else class="unsupported-preview">
          <a-result
            status="warning"
            title="不支持预览"
            :sub-title="`文件格式 ${resource?.fileType} 暂不支持在线预览`"
          >
            <template #extra>
              <a-button type="primary" @click="downloadResource">
                下载查看
              </a-button>
            </template>
          </a-result>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick, onBeforeMount } from 'vue'
import { message } from 'ant-design-vue'
import { FullscreenOutlined, FullscreenExitOutlined, DownloadOutlined, PlayCircleOutlined, FileTextOutlined, LoadingOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { renderAsync } from 'docx-preview'

interface ResourcePreviewProps {
  resource?: {
    id: string
    title: string
    url: string
    fileType: string
    content?: string
    examType?: string
    questionCount?: number
    totalScore?: number
  }
  visible: boolean
}

const props = withDefaults(defineProps<ResourcePreviewProps>(), {
  visible: false
})

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

// 视频播放器引用
const videoPlayer = ref<HTMLVideoElement>()

// docx预览相关
const docxContainer = ref<HTMLDivElement>()
const docxLoading = ref(false)
const docxError = ref(false)
const docxErrorMsg = ref('')

const userStore = useUserStore()

// 最大化状态
const isMaximized = ref(false)

// 视频解码错误状态
const videoDecodeError = ref(false)

// 标记modal是否正在关闭，避免关闭时触发错误提示
const isModalClosing = ref(false)


// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (value) => {
    // 当关闭modal时，先设置标志，避免视频销毁时触发错误提示
    if (!value) {
      isModalClosing.value = true
      // 延迟重置标志
      setTimeout(() => {
        isModalClosing.value = false
      }, 500)
    }
    emit('update:visible', value)
  }
})

const resourceType = computed(() => {
  // 优先使用fileType字段，如果不存在则从URL或resource_type推断
  let fileType = props.resource?.fileType || props.resource?.resource_type || 'unknown'
  fileType = fileType.toLowerCase()

  // 获取URL用于辅助判断
  const url = (props.resource?.url || '').toLowerCase()

  // PDF - 检查fileType或URL
  if (fileType.includes('pdf') || url.endsWith('.pdf')) return 'pdf'

  // Word 文档 - 单独处理，不走 Office Online
  // 检查fileType包含docx/doc/word，或者URL以.docx/.doc结尾
  if (fileType.includes('docx') || fileType.includes('doc') || fileType.includes('word') ||
      url.endsWith('.docx') || url.endsWith('.doc')) {
    return 'word'
  }

  // Office 文档 (PPT, Excel) - 需要 Office Online 预览
  if (['ppt', 'pptx', 'xls', 'xlsx'].some(ext => fileType.includes(ext)) ||
      ['.ppt', '.pptx', '.xls', '.xlsx'].some(ext => url.endsWith(ext))) {
    return 'office'
  }

  // 视频 - 检查fileType或URL
  if (fileType === 'video' || ['mp4', 'mov', 'avi', 'wmv', 'flv'].some(ext => fileType.includes(ext)) ||
      ['.mp4', '.mov', '.avi', '.wmv', '.flv'].some(ext => url.endsWith(ext))) {
    return 'video'
  }

  // 图片 - 支持 "image" 类型和具体扩展名，或URL检测
  if (fileType === 'image' || ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg'].some(ext => fileType.includes(ext)) ||
      ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'].some(ext => url.endsWith(ext))) {
    return 'image'
  }

  // Markdown - 检查fileType或URL
  if (fileType.includes('md') || fileType.includes('markdown') || url.endsWith('.md')) {
    return 'markdown'
  }

  // JSON - 检查fileType或URL
  if (fileType.includes('json') || url.endsWith('.json')) {
    return 'json'
  }

  // 考试试卷
  if (fileType.includes('exam') || props.resource.title?.includes('试卷')) {
    return 'exam'
  }

  return 'unknown'
})

const previewUrl = computed(() => {
  if (!props.resource?.url) return ''

  const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const resourceUrl = props.resource.url

  console.log('ResourcePreview - 原始URL:', resourceUrl, '类型:', resourceType.value)

  // 优先检查：如果是静态资源路径（/static/开头），直接使用后端URL
  if (resourceUrl.startsWith('/static/')) {
    const baseOrigin = backendBaseUrl.replace(/\/api\/v1\/?$/, '')
    const finalUrl = `${baseOrigin}${resourceUrl}`
    console.log('ResourcePreview - 静态资源URL:', finalUrl)
    return finalUrl
  }

  // 如果已经是完整的API路径，直接使用
  if (resourceUrl.startsWith('/api/')) {
    if (['office', 'pdf', 'video'].includes(resourceType.value)) {
      if (resourceType.value === 'video') {
        return `${backendBaseUrl}${resourceUrl}?preview=true`
      }
      return `${resourceUrl}?preview=true`
    }
    return resourceUrl
  }

  // 否则，构造完整的API路径
  const baseUrl = '/api/v1/files/teaching-resources'
  if (['office', 'pdf', 'video'].includes(resourceType.value)) {
    if (resourceType.value === 'video') {
      return `${backendBaseUrl}${baseUrl}/${resourceUrl}?preview=true`
    }
    return `${baseUrl}/${resourceUrl}?preview=true`
  }

  return `${baseUrl}/${resourceUrl}`
})

const downloadUrl = computed(() => {
  return previewUrl.value.replace('?preview=true', '').replace('&preview=true', '')
})

const pdfHeight = computed(() => {
  return '600px' // 可以根据需要调整
})

const isPdfSupported = computed(() => {
  // 检查浏览器是否支持PDF
  return true // 暂时假设支持，后续可以添加检测逻辑
})

// 模态框尺寸
const modalWidth = computed(() => {
  return isMaximized.value ? '100vw' : '90%'
})

const modalHeight = computed(() => {
  return isMaximized.value ? '100vh' : '80vh'
})

const modalStyle = computed(() => {
  if (isMaximized.value) {
    return {
      top: '0px',
      left: '0px',
      margin: '0px',
      maxWidth: '100vw',
      maxHeight: '100vh'
    }
  }
  return {}
})

// 切换最大化状态
const toggleMaximize = () => {
  isMaximized.value = !isMaximized.value
}

const hasExamPermission = computed(() => {
  return userStore.userInfo.role === 'teacher' || userStore.userInfo.role === 'admin'
})

// 在新标签页中打开文件
const openInNewTab = () => {
  if (!props.resource?.url) {
    message.error('资源链接不存在')
    return
  }

  const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
  let url = props.resource.url

  // 如果是静态资源路径，直接使用后端URL
  if (url.startsWith('/static/')) {
    url = `${backendBaseUrl}${url}`
  } else if (url.startsWith('/api/')) {
    // API路径需要加上后端前缀
    url = `${backendBaseUrl}${url}`
  }

  window.open(url, '_blank')
  message.success(`已在新标签页中打开：${props.resource.title}`)
}

// 加载并渲染docx文件
const loadDocx = async () => {
  if (!props.resource?.url || resourceType.value !== 'word') {
    return
  }

  docxLoading.value = true
  docxError.value = false
  docxErrorMsg.value = ''

  try {
    const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
    let url = props.resource.url

    // 如果是静态资源路径，使用后端URL
    if (url.startsWith('/static/')) {
      url = `${backendBaseUrl}${url}`
    } else if (url.startsWith('/api/')) {
      url = `${backendBaseUrl}${url}`
    }

    console.log('正在加载docx文件:', url)

    // 获取docx文件
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }

    const blob = await response.blob()
    console.log('docx文件大小:', blob.size, 'bytes')

    // 等待容器元素渲染
    await nextTick()

    if (docxContainer.value) {
      // 清空容器
      docxContainer.value.innerHTML = ''

      // 使用docx-preview渲染
      await renderAsync(blob, docxContainer.value, undefined, {
        className: 'docx-viewer',
        inWrapper: true,
        ignoreWidth: false,
        ignoreHeight: false,
        ignoreFonts: false,
        breakPages: true,
        ignoreLastRenderedPageBreak: true,
        experimental: false,
        trimXmlDeclaration: true,
        useBase64URL: true,
        renderHeaders: true,
        renderFooters: true,
        renderFootnotes: true,
        renderEndnotes: true,
      })

      console.log('docx文件渲染成功')
    } else {
      throw new Error('渲染容器未找到')
    }
  } catch (error) {
    console.error('docx加载失败:', error)
    docxError.value = true
    docxErrorMsg.value = error instanceof Error ? error.message : '未知错误'
  } finally {
    docxLoading.value = false
  }
}

// 方法
const downloadResource = () => {
  if (!props.resource?.url) {
    message.error('资源链接不存在')
    return
  }

  const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin
  let url = props.resource.url

  // 如果是静态资源路径，使用后端URL
  if (url.startsWith('/static/')) {
    url = `${backendBaseUrl}${url}`
  }

  // 创建下载链接
  const link = document.createElement('a')
  link.href = url
  link.download = props.resource.title || 'resource'
  link.target = '_blank'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  message.success('开始下载文件')
}

// 视频播放事件处理 (Chrome优化版)
const onVideoError = (event) => {
  // 如果modal正在关闭，忽略错误（避免关闭时触发误报）
  if (isModalClosing.value || !props.visible) {
    console.log('视频错误事件被忽略（modal正在关闭）')
    return
  }

  console.error('视频播放错误:', event.target.error)
  const error = event.target.error

  // 如果没有错误对象，忽略
  if (!error) {
    console.log('视频错误事件被忽略（无错误对象）')
    return
  }

  let errorMessage = '视频播放失败'

  switch (error.code) {
    case MediaError.MEDIA_ERR_ABORTED:
      // 用户中断通常是正常操作，不显示错误
      console.log('视频播放被用户中断')
      return
    case MediaError.MEDIA_ERR_NETWORK:
      errorMessage = '网络连接错误，请检查网络后重试'
      break
    case MediaError.MEDIA_ERR_DECODE:
      errorMessage = '视频文件可能损坏或编码格式不兼容，建议下载后使用其他播放器'
      videoDecodeError.value = true
      break
    case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
      errorMessage = 'Chrome不支持此视频格式，请下载后使用专业播放器'
      videoDecodeError.value = true
      break
    default:
      errorMessage = `视频播放错误 (错误代码: ${error.code})`
  }

  message.error(errorMessage)
}

const onVideoStalled = () => {
  console.warn('视频加载停滞，正在缓冲...')
  message.warning('视频加载中，请稍候...')
}

const onVideoWaiting = () => {
  console.log('视频缓冲中...')
}

const onVideoCanPlay = () => {
  console.log('视频可以开始播放')
}

const onVideoLoadedMetadata = () => {
  console.log('视频元数据已加载')
  // 确保视频可以正常播放
  if (videoPlayer.value) {
    videoPlayer.value.currentTime = 0
  }
}

const onVideoPlay = () => {
  console.log('视频开始播放')
}

const onVideoPause = () => {
  console.log('视频暂停')
}

const onVideoTimeUpdate = () => {
  if (videoPlayer.value) {
    console.log(`视频时间更新: ${videoPlayer.value.currentTime.toFixed(3)}秒`)
  }
}

// 测试兼容视频 (Chrome优化版本)
const testCompatibleVideo = () => {
  console.log('测试Chrome兼容视频...')

  // 使用Chrome原生支持的测试视频
  const testVideoUrl = 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4'

  // 隐藏错误提示
  videoDecodeError.value = false

  // 更新视频源
  if (videoPlayer.value) {
    videoPlayer.value.src = testVideoUrl
    videoPlayer.value.load() // 重新加载

    message.info('正在加载Chrome兼容测试视频...')

    // 监听加载完成
    videoPlayer.value.addEventListener('loadedmetadata', () => {
      console.log('✅ 测试视频加载成功，开始播放')
      message.success('Chrome兼容视频加载成功！')
    })

    videoPlayer.value.addEventListener('error', (e) => {
      console.error('❌ 测试视频播放失败:', e.target.error)
      message.error('测试视频播放失败，请检查网络连接')
    })

    // 自动播放测试
    videoPlayer.value.play().then(() => {
      console.log('✅ 测试视频开始播放')
    }).catch(err => {
      console.warn('自动播放被阻止，请手动点击播放:', err.message)
    })
  }
}

// 监听资源变化，自动处理预览
watch(() => props.resource, (newResource) => {
  if (newResource && visible.value) {
    // 可以在这里添加预览前的验证逻辑
    console.log('预览资源:', newResource.title, '类型:', resourceType.value)

    // 重置错误状态
    videoDecodeError.value = false

    // 如果是Word文档，加载docx预览
    if (resourceType.value === 'word') {
      nextTick(() => {
        loadDocx()
      })
    }

    // PDF现在直接在弹窗中显示，不在新标签页中打开
    // 其他类型的文件仍然可以选择在新标签页中打开
  }
}, { deep: true })

// 监听visible变化，打开时加载docx
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.resource && resourceType.value === 'word') {
    nextTick(() => {
      loadDocx()
    })
  }
})

// 组件挂载时，如果已经是visible状态且是word文档，则加载
// 这处理了destroyOnClose=true时组件重新创建的情况
onMounted(() => {
  if (props.visible && props.resource && resourceType.value === 'word') {
    nextTick(() => {
      loadDocx()
    })
  }
})

// 组件销毁时清理资源
onUnmounted(() => {
  // Chrome版本不需要特殊清理
})

// 确保所有计算属性都已定义后再暴露
defineExpose({
  openInNewTab,
  toggleMaximize
})
</script>

<style scoped>
.resource-preview {
  position: relative;
}

.preview-container {
  min-height: 400px;
}

.pdf-preview,
.office-preview,
.markdown-preview {
  width: 100%;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.pdf-preview iframe,
.office-preview iframe,
.markdown-preview iframe {
  display: block;
  width: 100%;
  border: none;
}

.video-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #000;
  border-radius: 12px;
  padding: 20px;
}

.video-preview video {
  max-width: 100%;
  border-radius: 8px;
}

.video-controls {
  width: 100%;
}

.pdf-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  width: 100%;
}

.pdf-preview embed {
  max-width: 100%;
  min-height: 500px;
}

.pdf-fallback {
  text-align: center;
  padding: 20px;
  color: #666;
}

.pdf-fallback a {
  color: #1890ff;
  text-decoration: none;
}

.pdf-fallback a:hover {
  text-decoration: underline;
}

.image-preview {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.json-preview {
  max-height: 600px;
  overflow-y: auto;
}

.json-preview pre {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.4;
  overflow-x: auto;
  margin: 0;
}

.exam-preview {
  min-height: 300px;
}

.exam-content .ant-card-body {
  padding: 16px;
}

.exam-info p {
  margin: 8px 0;
  color: #666;
}

.unsupported-preview {
  min-height: 300px;
}

/* 模态框标题样式 */
.modal-title {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px; /* 按钮之间的间距 */
}

.modal-title span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.maximize-btn {
  color: #666;
  flex-shrink: 0; /* 防止按钮被压缩 */
  margin-right: 48px; /* 为关闭按钮留出足够空间 */
}

.maximize-btn:hover {
  color: #1890ff;
  background-color: #f0f0f0;
}

/* Word 文档预览样式 */
.word-preview {
  min-height: 400px;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
}

/* docx加载中状态 */
.docx-loading {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  gap: 16px;
}

.docx-loading p {
  color: #666;
  margin: 0;
}

/* docx错误状态 */
.docx-error {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

/* docx渲染容器 */
.docx-container {
  width: 100%;
  max-height: 600px;
  overflow: auto;
  background: #fff;
  padding: 20px;
  box-sizing: border-box;
}

/* docx-preview库生成的样式覆盖 */
.docx-container :deep(.docx-wrapper) {
  background: #fff;
  padding: 0;
}

.docx-container :deep(.docx) {
  width: 100% !important;
  padding: 20px;
  box-shadow: none;
  margin-bottom: 0;
}

.docx-container :deep(section.docx) {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  border-radius: 4px;
}

/* 最大化模态框样式 */
.maximized-modal .ant-modal {
  max-width: 100vw !important;
  width: 100vw !important;
  height: 100vh !important;
  max-height: 100vh !important;
  margin: 0 !important;
  top: 0 !important;
  left: 0 !important;
  padding-bottom: 0 !important;
}

.maximized-modal .ant-modal-content {
  height: 100vh !important;
  border-radius: 0 !important;
}

.maximized-modal .ant-modal-body {
  height: calc(100vh - 110px) !important; /* 减去标题栏和边距的高度 */
  overflow: auto;
}

.maximized-modal .pdf-preview embed {
  height: calc(100vh - 150px) !important; /* 适应最大化时的容器高度 */
}

@media (max-width: 768px) {
  .preview-container {
    min-height: 300px;
  }

  .pdf-preview iframe,
  .office-preview iframe,
  .markdown-preview iframe {
    height: 400px;
  }

  .video-preview {
    padding: 15px;
  }
  
  .video-preview video {
    max-height: 400px;
  }

  .image-preview {
    min-height: 300px;
  }

  .preview-image {
    max-height: 400px;
  }
}
</style>

