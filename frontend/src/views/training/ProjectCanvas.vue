<template>
  <div class="project-canvas copilot-theme">
    <!-- 头部 -->
    <header class="canvas-header">
      <div class="header-left">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h1 class="canvas-title">项目画布</h1>
      </div>
      <div class="header-right">
        <button class="notification-btn">
          <BellOutlined />
        </button>
        <div class="user-avatar">
          <img :src="userAvatar" alt="User" />
        </div>
      </div>
    </header>

    <!-- 画布区域 -->
    <div class="canvas-container" ref="canvasContainer">
      <canvas ref="starmapCanvas" class="starmap-canvas"></canvas>
      
      <!-- 项目节点覆盖层 -->
      <div class="nodes-overlay">
        <div
          v-for="node in projectNodes"
          :key="node.id"
          class="project-node"
          :class="[`node-${node.status}`, { 'node-selected': selectedNode?.id === node.id }]"
          :style="getNodeStyle(node)"
          @click="selectNode(node)"
          @dblclick="openProject(node)"
        >
          <div class="node-ring" :style="getNodeRingStyle(node)"></div>
          <div class="node-content">
            <span class="node-title">{{ node.title }}</span>
            <span v-if="node.subtitle" class="node-subtitle">{{ node.subtitle }}</span>
            <span v-if="node.progress !== undefined" class="node-progress">{{ node.progress }}%</span>
          </div>
          <div v-if="node.status === 'completed'" class="node-badge completed">
            <CheckOutlined />
          </div>
          <div v-else-if="node.status === 'warning'" class="node-badge warning">
            <ExclamationOutlined />
          </div>
        </div>
      </div>
    </div>

    <!-- 命令面板 -->
    <div class="command-palette" :class="{ 'palette-focused': isCommandFocused }">
      <div class="palette-icon">
        <CodeOutlined />
      </div>
      <input
        ref="commandInput"
        v-model="commandText"
        type="text"
        class="palette-input"
        :placeholder="commandPlaceholder"
        @focus="isCommandFocused = true"
        @blur="isCommandFocused = false"
        @keydown.enter="executeCommand"
        @keydown.escape="clearCommand"
      />
      <button class="palette-submit" @click="executeCommand">
        <ArrowRightOutlined />
      </button>
    </div>

    <!-- 底部工具栏 -->
    <div class="canvas-toolbar">
      <div class="toolbar-group zoom-controls">
        <button class="toolbar-btn" @click="zoomIn" title="放大">
          <ZoomInOutlined />
        </button>
        <button class="toolbar-btn" @click="zoomOut" title="缩小">
          <ZoomOutOutlined />
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group tools">
        <button 
          class="toolbar-btn tool-btn" 
          :class="{ active: activeTool === 'brainstorm' }"
          @click="openTool('brainstorm')"
        >
          <BulbOutlined />
          <span>AI 头脑风暴</span>
        </button>
        <button 
          class="toolbar-btn tool-btn" 
          :class="{ active: activeTool === 'whiteboard' }"
          @click="openTool('whiteboard')"
        >
          <EditOutlined />
          <span>白板</span>
        </button>
        <button 
          class="toolbar-btn tool-btn" 
          :class="{ active: activeTool === 'timeline' }"
          @click="openTool('timeline')"
        >
          <LineChartOutlined />
          <span>时间线</span>
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <button class="toolbar-btn add-btn" @click="showAddProject">
        <PlusOutlined />
      </button>
    </div>

    <!-- AI 头脑风暴面板 -->
    <Transition name="slide-up">
      <div v-if="activeTool === 'brainstorm'" class="tool-panel brainstorm-panel">
        <div class="panel-header">
          <h3><BulbOutlined /> AI 头脑风暴</h3>
          <button class="panel-close" @click="closeTool">
            <CloseOutlined />
          </button>
        </div>
        <div class="panel-content">
          <div class="brainstorm-input">
            <textarea 
              v-model="brainstormPrompt" 
              placeholder="描述您的项目想法或问题..."
              rows="3"
            ></textarea>
            <button class="brainstorm-submit" @click="generateBrainstorm" :disabled="brainstormLoading">
              <ThunderboltOutlined v-if="!brainstormLoading" />
              <LoadingOutlined v-else spin />
              生成创意
            </button>
          </div>
          <div v-if="brainstormResults.length > 0" class="brainstorm-results">
            <div v-for="(idea, index) in brainstormResults" :key="index" class="idea-card">
              <span class="idea-number">{{ index + 1 }}</span>
              <p>{{ idea }}</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 添加项目模态框 -->
    <a-modal
      v-model:open="showAddModal"
      title="添加新项目"
      :footer="null"
      class="dark-modal"
    >
      <div class="add-project-form">
        <div class="form-group">
          <label>项目名称</label>
          <a-input v-model:value="newProject.title" placeholder="输入项目名称" />
        </div>
        <div class="form-group">
          <label>项目描述</label>
          <a-textarea v-model:value="newProject.subtitle" placeholder="简短描述" :rows="2" />
        </div>
        <div class="form-group">
          <label>关联项目</label>
          <a-select
            v-model:value="newProject.relatedProjects"
            mode="multiple"
            placeholder="选择关联项目"
            style="width: 100%"
          >
            <a-select-option v-for="p in projectNodes" :key="p.id" :value="p.id">
              {{ p.title }}
            </a-select-option>
          </a-select>
        </div>
        <div class="form-actions">
          <a-button @click="showAddModal = false">取消</a-button>
          <a-button type="primary" @click="addProject">创建项目</a-button>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  BellOutlined,
  CheckOutlined,
  ExclamationOutlined,
  CodeOutlined,
  ArrowRightOutlined,
  ZoomInOutlined,
  ZoomOutOutlined,
  BulbOutlined,
  EditOutlined,
  LineChartOutlined,
  PlusOutlined,
  CloseOutlined,
  ThunderboltOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { aiBrainstorm } from '@/api/ai-features'
import request from '@/utils/request'

const router = useRouter()
const userStore = useUserStore()

const requireCurrentUserId = () => {
  const userId = userStore.userId
  if (!userId) {
    message.warning('请先登录后再使用项目画布')
    router.push('/login')
    throw new Error('Missing current user id')
  }
  return userId
}

// Refs
const canvasContainer = ref<HTMLDivElement | null>(null)
const starmapCanvas = ref<HTMLCanvasElement | null>(null)
const commandInput = ref<HTMLInputElement | null>(null)

// User info
const userAvatar = computed(() => userStore.userInfo?.avatar || '/default-avatar.png')

// State
const zoom = ref(1)
const selectedNode = ref<ProjectNode | null>(null)
const isCommandFocused = ref(false)
const commandText = ref('')
const activeTool = ref<string | null>(null)
const showAddModal = ref(false)
const brainstormPrompt = ref('')
const brainstormResults = ref<string[]>([])
const brainstormLoading = ref(false)

const commandPlaceholder = computed(() => {
  if (selectedNode.value) {
    return `> 命令: 聚焦项目 '${selectedNode.value.title}' 或输入 'help'`
  }
  return "> 命令: 搜索项目、输入 'help' 获取帮助"
})

// New project form
const newProject = ref({
  title: '',
  subtitle: '',
  relatedProjects: [] as string[]
})

// Project node types
interface ProjectNode {
  id: string
  title: string
  subtitle?: string
  progress?: number
  status: 'completed' | 'in_progress' | 'warning' | 'pending' | 'default'
  x: number
  y: number
  size: 'large' | 'medium' | 'small'
  color: string
  connections: string[]
}

// Project data from API
const projectNodes = ref<ProjectNode[]>([])
const loading = ref(true)
const totalProjects = ref(0)
const completedCount = ref(0)
const inProgressCount = ref(0)

// Load project data from backend API
const loadProjectData = async () => {
  loading.value = true
  console.log('[ProjectCanvas] 开始加载项目数据...')
  try {
    const response = await request.get('/api/v1/project-canvas/canvas')
    console.log('[ProjectCanvas] API 响应:', response)
    const data = response.data || response
    
    if (data.success && data.nodes && data.nodes.length > 0) {
      console.log('[ProjectCanvas] 加载到真实数据:', data.nodes.length, '个项目')
      projectNodes.value = data.nodes
      totalProjects.value = data.totalProjects || 0
      completedCount.value = data.completedCount || 0
      inProgressCount.value = data.inProgressCount || 0
    } else {
      console.log('[ProjectCanvas] 无真实数据，使用示例数据')
      // 如果没有数据，使用示例数据
      loadSampleData()
    }
  } catch (error) {
    console.error('[ProjectCanvas] 加载项目数据失败:', error)
    // 使用示例数据作为回退
    loadSampleData()
  } finally {
    loading.value = false
    nextTick(() => {
      initCanvas()
    })
  }
}

// 加载示例数据（当 API 无数据时）
const loadSampleData = () => {
  projectNodes.value = [
    {
      id: 'retail-analysis',
      title: '某零售企业经营分析',
      subtitle: '入门',
      progress: 100,
      status: 'completed',
      x: 50,
      y: 45,
      size: 'large',
      color: '#22c55e',
      connections: ['fund-marketing', 'stock-analysis']
    },
    {
      id: 'fund-marketing',
      title: '公募基金精准营销',
      subtitle: '中级',
      progress: 75,
      status: 'in_progress',
      x: 28,
      y: 25,
      size: 'medium',
      color: '#3b82f6',
      connections: ['retail-analysis', 'churn-prediction']
    },
    {
      id: 'stock-analysis',
      title: 'A股上市公司销售额分析',
      subtitle: '中级',
      progress: 50,
      status: 'in_progress',
      x: 72,
      y: 25,
      size: 'medium',
      color: '#3b82f6',
      connections: ['retail-analysis']
    },
    {
      id: 'churn-prediction',
      title: '客户流失模型预测',
      subtitle: '高级',
      progress: 25,
      status: 'pending',
      x: 35,
      y: 70,
      size: 'medium',
      color: '#f59e0b',
      connections: ['fund-marketing']
    },
    {
      id: 'python-course',
      title: 'Python程序设计',
      subtitle: '入门',
      status: 'completed',
      x: 65,
      y: 70,
      size: 'small',
      color: '#22c55e',
      connections: ['churn-prediction', 'spark-basics']
    },
    {
      id: 'spark-basics',
      title: 'Spark编程基础',
      subtitle: '中级',
      status: 'warning',
      x: 85,
      y: 55,
      size: 'small',
      color: '#ef4444',
      connections: ['python-course']
    }
  ]
  totalProjects.value = 6
  completedCount.value = 2
  inProgressCount.value = 2
}

// Canvas drawing
let ctx: CanvasRenderingContext2D | null = null
let animationId: number = 0

const initCanvas = () => {
  if (!starmapCanvas.value || !canvasContainer.value) return
  
  const canvas = starmapCanvas.value
  const container = canvasContainer.value
  
  canvas.width = container.clientWidth
  canvas.height = container.clientHeight
  
  ctx = canvas.getContext('2d')
  if (!ctx) return
  
  drawConnections()
}

const drawConnections = () => {
  if (!ctx || !starmapCanvas.value) return
  
  const canvas = starmapCanvas.value
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // Draw starfield background
  drawStarfield()
  
  // Draw connections
  projectNodes.value.forEach(node => {
    node.connections.forEach(targetId => {
      const target = projectNodes.value.find(n => n.id === targetId)
      if (target) {
        drawConnection(node, target)
      }
    })
  })
}

const drawStarfield = () => {
  if (!ctx || !starmapCanvas.value) return
  
  const canvas = starmapCanvas.value
  
  // Draw subtle stars
  for (let i = 0; i < 100; i++) {
    const x = Math.random() * canvas.width
    const y = Math.random() * canvas.height
    const size = Math.random() * 1.5
    const opacity = Math.random() * 0.3 + 0.1
    
    ctx.beginPath()
    ctx.arc(x, y, size, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(255, 255, 255, ${opacity})`
    ctx.fill()
  }
}

const drawConnection = (from: ProjectNode, to: ProjectNode) => {
  if (!ctx || !starmapCanvas.value) return
  
  const canvas = starmapCanvas.value
  const fromX = (from.x / 100) * canvas.width
  const fromY = (from.y / 100) * canvas.height
  const toX = (to.x / 100) * canvas.width
  const toY = (to.y / 100) * canvas.height
  
  // Create gradient line
  const gradient = ctx.createLinearGradient(fromX, fromY, toX, toY)
  gradient.addColorStop(0, from.color + '80')
  gradient.addColorStop(1, to.color + '40')
  
  ctx.beginPath()
  ctx.moveTo(fromX, fromY)
  ctx.lineTo(toX, toY)
  ctx.strokeStyle = gradient
  ctx.lineWidth = 1.5
  ctx.setLineDash([5, 5])
  ctx.stroke()
  ctx.setLineDash([])
}

const getNodeStyle = (node: ProjectNode) => {
  const sizeMap = {
    large: 140,
    medium: 100,
    small: 70
  }
  const size = sizeMap[node.size]
  
  return {
    left: `calc(${node.x}% - ${size / 2}px)`,
    top: `calc(${node.y}% - ${size / 2}px)`,
    width: `${size}px`,
    height: `${size}px`
  }
}

const getNodeRingStyle = (node: ProjectNode) => {
  return {
    borderColor: node.color,
    boxShadow: `0 0 20px ${node.color}40, inset 0 0 20px ${node.color}20`
  }
}

// Interactions
const selectNode = (node: ProjectNode) => {
  selectedNode.value = node
}

const openProject = (node: ProjectNode) => {
  router.push(`/project/${node.id}`)
}

const zoomIn = () => {
  zoom.value = Math.min(2, zoom.value + 0.1)
}

const zoomOut = () => {
  zoom.value = Math.max(0.5, zoom.value - 0.1)
}

const openTool = (tool: string) => {
  activeTool.value = activeTool.value === tool ? null : tool
}

const closeTool = () => {
  activeTool.value = null
}

const showAddProject = () => {
  showAddModal.value = true
}

const addProject = () => {
  if (!newProject.value.title) {
    message.warning('请输入项目名称')
    return
  }
  
  const newNode: ProjectNode = {
    id: `project-${Date.now()}`,
    title: newProject.value.title,
    subtitle: newProject.value.subtitle,
    status: 'pending',
    x: 30 + Math.random() * 40,
    y: 30 + Math.random() * 40,
    size: 'medium',
    color: '#6b7280',
    connections: newProject.value.relatedProjects
  }
  
  projectNodes.value.push(newNode)
  
  // Update connections for related projects
  newProject.value.relatedProjects.forEach(relatedId => {
    const related = projectNodes.value.find(n => n.id === relatedId)
    if (related && !related.connections.includes(newNode.id)) {
      related.connections.push(newNode.id)
    }
  })
  
  showAddModal.value = false
  newProject.value = { title: '', subtitle: '', relatedProjects: [] }
  
  nextTick(() => {
    drawConnections()
  })
  
  message.success('项目创建成功')
}

// Command palette
const executeCommand = () => {
  const cmd = commandText.value.trim().toLowerCase()
  
  if (cmd === 'help') {
    message.info('可用命令: zoom [项目名], focus [项目名], add, list, clear')
  } else if (cmd.startsWith('zoom ') || cmd.startsWith('focus ')) {
    const projectName = cmd.replace(/^(zoom|focus)\s+/, '').replace(/['"]/g, '')
    const node = projectNodes.value.find(n => 
      n.title.toLowerCase().includes(projectName)
    )
    if (node) {
      selectNode(node)
      message.success(`已聚焦到项目: ${node.title}`)
    } else {
      message.warning(`未找到项目: ${projectName}`)
    }
  } else if (cmd === 'add') {
    showAddProject()
  } else if (cmd === 'list') {
    message.info(`共 ${projectNodes.value.length} 个项目`)
  } else if (cmd === 'clear') {
    selectedNode.value = null
    message.success('已清除选择')
  } else if (cmd) {
    // Search projects
    const matches = projectNodes.value.filter(n => 
      n.title.toLowerCase().includes(cmd)
    )
    if (matches.length > 0) {
      selectNode(matches[0])
      message.success(`找到 ${matches.length} 个匹配项目`)
    } else {
      message.warning('未找到匹配项目')
    }
  }
  
  commandText.value = ''
}

const clearCommand = () => {
  commandText.value = ''
  commandInput.value?.blur()
}

// AI Brainstorm
const generateBrainstorm = async () => {
  if (!brainstormPrompt.value.trim()) {
    message.warning('请输入项目想法或问题')
    return
  }
  
  brainstormLoading.value = true
  
  try {
    // Get project context
    const projectContext = projectNodes.value.map(n => n.title)
    
    const response = await aiBrainstorm({
      user_id: requireCurrentUserId(),
      user_prompt: brainstormPrompt.value,
      project_context: projectContext
    })
    
    if (response.success && response.ideas) {
      brainstormResults.value = response.ideas
    } else {
      // Fallback ideas
      brainstormResults.value = [
        '考虑将机器学习模块与数据分析进行深度整合，实现自动化数据洞察',
        '引入实时协作功能，支持多人同时编辑项目',
        '添加项目依赖可视化，清晰展示项目间的关联关系',
        '实现智能项目推荐，基于用户历史和技能匹配合适的项目'
      ]
    }
  } catch (e) {
    console.error('Brainstorm failed:', e)
    brainstormResults.value = [
      '建议优化项目间的数据流转机制',
      '考虑添加自动化测试模块提高代码质量',
      '引入版本控制功能追踪项目变更历史'
    ]
  } finally {
    brainstormLoading.value = false
  }
}

// Keyboard shortcuts
const handleKeydown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    commandInput.value?.focus()
  }
}

// Lifecycle
onMounted(async () => {
  await loadProjectData()
  window.addEventListener('resize', initCanvas)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('resize', initCanvas)
  window.removeEventListener('keydown', handleKeydown)
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
})
</script>

<style scoped>
.project-canvas {
  position: relative;
  width: 100%;
  height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #f5f5f5 50%, #fafafa 100%);
  overflow: hidden;
}

/* Header */
.canvas-header {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  z-index: 100;
  background: transparent;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 40px;
  height: 40px;
  background: var(--copilot-gradient-primary);
  border-radius: var(--copilot-radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.canvas-title {
  font-size: var(--copilot-font-size-lg);
  font-weight: 600;
  color: var(--copilot-text-primary);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-btn {
  width: 40px;
  height: 40px;
  background: transparent;
  border: 1px solid var(--copilot-border-default);
  border-radius: 50%;
  color: var(--copilot-text-secondary);
  cursor: pointer;
  transition: all var(--copilot-transition-fast);
}

.notification-btn:hover {
  border-color: var(--copilot-border-accent);
  color: var(--copilot-text-primary);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid var(--copilot-accent-pink);
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Canvas */
.canvas-container {
  position: absolute;
  inset: 64px 0 160px 0;
}

.starmap-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.nodes-overlay {
  position: absolute;
  inset: 0;
}

/* Project Nodes */
.project-node {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all var(--copilot-transition-normal);
}

.node-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 2px solid;
  background: radial-gradient(circle at center, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.4) 100%);
  transition: all var(--copilot-transition-normal);
}

.project-node:hover .node-ring {
  transform: scale(1.05);
}

.project-node.node-selected .node-ring {
  transform: scale(1.1);
  border-width: 3px;
}

.node-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 8px;
}

.node-title {
  display: block;
  font-size: var(--copilot-font-size-sm);
  font-weight: 600;
  color: var(--copilot-text-primary);
  line-height: 1.3;
}

.node-subtitle {
  display: block;
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-secondary);
  margin-top: 2px;
}

.node-progress {
  display: block;
  font-size: var(--copilot-font-size-md);
  font-weight: 700;
  color: var(--copilot-accent-cyan);
  margin-top: 4px;
}

.node-badge {
  position: absolute;
  bottom: 15%;
  left: 50%;
  transform: translateX(-50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.node-badge.completed {
  background: var(--copilot-accent-green);
  color: white;
}

.node-badge.warning {
  background: var(--copilot-accent-pink);
  color: white;
}

/* Node status colors */
.node-completed .node-ring {
  border-color: var(--copilot-accent-green);
  box-shadow: 0 0 30px rgba(34, 197, 94, 0.4), inset 0 0 20px rgba(34, 197, 94, 0.1);
}

.node-in_progress .node-ring {
  border-color: var(--copilot-accent-cyan);
  box-shadow: 0 0 30px rgba(59, 130, 246, 0.4), inset 0 0 20px rgba(59, 130, 246, 0.1);
}

.node-warning .node-ring {
  border-color: var(--copilot-accent-pink);
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.4), inset 0 0 20px rgba(239, 68, 68, 0.1);
}

.node-pending .node-ring,
.node-default .node-ring {
  border-color: var(--copilot-border-default);
  box-shadow: 0 0 20px rgba(107, 114, 128, 0.3);
}

/* Command Palette */
.command-palette {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  width: 600px;
  max-width: calc(100% - 48px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-xl);
  box-shadow: var(--copilot-shadow-lg);
  transition: all var(--copilot-transition-normal);
  z-index: 50;
}

.command-palette.palette-focused {
  border-color: var(--copilot-accent-cyan);
  box-shadow: var(--copilot-shadow-lg), var(--copilot-shadow-glow-cyan);
}

.palette-icon {
  color: var(--copilot-text-tertiary);
  font-size: 18px;
}

.palette-input {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-base);
  font-family: 'JetBrains Mono', monospace;
  outline: none;
}

.palette-input::placeholder {
  color: var(--copilot-text-tertiary);
}

.palette-submit {
  width: 36px;
  height: 36px;
  background: var(--copilot-accent-cyan);
  border: none;
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--copilot-transition-fast);
}

.palette-submit:hover {
  transform: scale(1.1);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

/* Bottom Toolbar */
.canvas-toolbar {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-xl);
  box-shadow: var(--copilot-shadow-lg);
  z-index: 50;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background: var(--copilot-border-default);
  margin: 0 8px;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-secondary);
  cursor: pointer;
  transition: all var(--copilot-transition-fast);
}

.toolbar-btn:hover {
  background: var(--copilot-bg-tertiary);
  color: var(--copilot-text-primary);
}

.tool-btn {
  padding: 8px 16px;
}

.tool-btn span {
  font-size: var(--copilot-font-size-sm);
}

.tool-btn.active {
  background: var(--copilot-accent-cyan-dim);
  color: var(--copilot-accent-cyan);
}

.add-btn {
  width: 40px;
  height: 40px;
  background: var(--copilot-accent-cyan);
  color: white;
  border-radius: 50%;
}

.add-btn:hover {
  background: var(--copilot-accent-cyan);
  transform: scale(1.1);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

/* Tool Panel */
.tool-panel {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  max-width: calc(100% - 48px);
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-accent);
  border-radius: var(--copilot-radius-xl);
  box-shadow: var(--copilot-shadow-lg), var(--copilot-shadow-glow-cyan);
  z-index: 60;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--copilot-border-muted);
}

.panel-header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: var(--copilot-font-size-md);
  color: var(--copilot-text-primary);
}

.panel-close {
  background: transparent;
  border: none;
  color: var(--copilot-text-tertiary);
  cursor: pointer;
  padding: 4px;
}

.panel-close:hover {
  color: var(--copilot-text-primary);
}

.panel-content {
  padding: 20px;
  max-height: 400px;
  overflow-y: auto;
}

/* Brainstorm Panel */
.brainstorm-input {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brainstorm-input textarea {
  width: 100%;
  padding: 12px;
  background: var(--copilot-bg-primary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-sm);
  resize: none;
}

.brainstorm-input textarea:focus {
  outline: none;
  border-color: var(--copilot-accent-cyan);
}

.brainstorm-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  background: var(--copilot-gradient-primary);
  border: none;
  border-radius: var(--copilot-radius-md);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--copilot-transition-fast);
}

.brainstorm-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

.brainstorm-submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.brainstorm-results {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.idea-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--copilot-bg-primary);
  border: 1px solid var(--copilot-border-muted);
  border-radius: var(--copilot-radius-md);
}

.idea-number {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  background: var(--copilot-accent-cyan-dim);
  color: var(--copilot-accent-cyan);
  border-radius: 50%;
  font-size: var(--copilot-font-size-xs);
  font-weight: 600;
}

.idea-card p {
  margin: 0;
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-text-primary);
  line-height: 1.5;
}

/* Animations */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translate(-50%, 20px);
}

/* Add Project Modal */
.add-project-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-text-secondary);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 8px;
}

/* Responsive */
@media (max-width: 768px) {
  .command-palette {
    width: calc(100% - 48px);
    bottom: 80px;
  }
  
  .tool-btn span {
    display: none;
  }
  
  .tool-panel {
    width: calc(100% - 48px);
  }
}
</style>
