/**
 * AI Co-pilot Store
 * 
 * 学生 AI 仪表板状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from './user'
import {
  getStudentDashboard,
  getAISkillSummary,
  getAIRecommendation,
  getAIStatus,
  aiChat,
  type DashboardLearningPath,
  type DashboardSkillNode,
  type DashboardDeadline,
  type DashboardRecommendation,
  type ChatResponse
} from '@/api/ai-features'

// ==================== Types ====================

export interface LearningPath extends DashboardLearningPath {}

export interface UpcomingDeadline extends DashboardDeadline {}

export interface SkillNode extends DashboardSkillNode {}

export interface PathRecommendation extends DashboardRecommendation {}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

// ==================== Store ====================

export const useAICopilotStore = defineStore('aiCopilot', () => {
  // State
  const learningPaths = ref<LearningPath[]>([])
  const upcomingDeadlines = ref<UpcomingDeadline[]>([])
  const skillNodes = ref<SkillNode[]>([])
  const skillLinks = ref<{source: string, target: string, weight: number}[]>([])
  const topSkills = ref<string[]>([])
  const aiSkillSummary = ref<string>('')
  const pathRecommendations = ref<PathRecommendation[]>([])
  const chatMessages = ref<ChatMessage[]>([])
  const criticalCount = ref(0)
  
  const loading = ref({
    dashboard: false,
    paths: false,
    skills: false,
    recommendations: false,
    chat: false
  })
  
  const error = ref<string | null>(null)
  const isAIAvailable = ref(true)

  // Getters
  const activePaths = computed(() => 
    learningPaths.value.filter(p => p.progress < 100)
  )
  
  const highPriorityPaths = computed(() => 
    learningPaths.value.filter(p => 
      p.priority === 'deadline' || p.priority === 'skill_gap'
    )
  )
  
  const criticalDeadlines = computed(() => 
    upcomingDeadlines.value.filter(d => d.isCritical)
  )
  
  const masteredSkills = computed(() => 
    skillNodes.value.filter(s => s.mastery >= 80)
  )

  // Actions
  
  /**
   * 加载仪表板完整数据
   */
  async function loadDashboard() {
    loading.value.dashboard = true
    error.value = null
    
    try {
      const response = await getStudentDashboard()
      
      if (response.success) {
        // 活跃学习路径
        learningPaths.value = response.activePaths || []
        
        // 技能星座
        skillNodes.value = response.skillConstellation?.nodes || []
        skillLinks.value = response.skillConstellation?.links || []
        topSkills.value = response.skillConstellation?.topSkills || []
        aiSkillSummary.value = response.skillConstellation?.aiSummary || ''
        
        // 优先情报
        upcomingDeadlines.value = response.priorityIntel?.deadlines || []
        pathRecommendations.value = response.priorityIntel?.recommendations || []
        criticalCount.value = response.priorityIntel?.criticalCount || 0
      }
      
    } catch (e: any) {
      console.error('加载仪表板数据失败:', e)
      error.value = '加载数据失败，请稍后重试'
      // 使用默认数据
      loadDefaultData()
    } finally {
      loading.value.dashboard = false
    }
  }

  /**
   * 加载默认数据（用于演示或 API 不可用时）
   */
  function loadDefaultData() {
    skillNodes.value = [
      { id: 'python', name: 'Python', category: '编程', mastery: 85, connections: ['data-analysis', 'ml'] },
      { id: 'data-analysis', name: '数据分析', category: '数据分析', mastery: 70, connections: ['python', 'statistics'] },
      { id: 'statistics', name: '统计学', category: '数学统计', mastery: 60, connections: ['data-analysis', 'ml'] },
      { id: 'ml', name: '机器学习', category: '人工智能', mastery: 45, connections: ['python', 'statistics'] },
      { id: 'sql', name: 'SQL', category: '编程', mastery: 75, connections: ['data-analysis'] },
      { id: 'visualization', name: '数据可视化', category: '数据分析', mastery: 65, connections: ['data-analysis', 'python'] },
      { id: 'spark', name: 'Spark', category: '大数据', mastery: 30, connections: ['python', 'sql'] },
      { id: 'deep-learning', name: '深度学习', category: '人工智能', mastery: 20, connections: ['ml', 'python'] }
    ]
    
    pathRecommendations.value = [
      {
        courseId: 'rec-1',
        title: '人工智能伦理入门',
        reason: '基于您的技能图谱，这门拓展课程与您的学习路径高度匹配',
        matchScore: 85,
        tags: ['AI', '伦理', '拓展']
      }
    ]
  }

  /**
   * 获取 AI 技能评语
   */
  async function fetchAISkillSummary() {
    try {
      const response = await getAISkillSummary()
      if (response.success) {
        aiSkillSummary.value = response.summary
      }
    } catch (e) {
      console.error('获取 AI 评语失败:', e)
    }
  }

  /**
   * 获取 AI 课程推荐
   */
  async function fetchAIRecommendation() {
    loading.value.recommendations = true
    try {
      const response = await getAIRecommendation()
      if (response.success && response.recommendation) {
        pathRecommendations.value = [response.recommendation]
      }
    } catch (e) {
      console.error('获取 AI 推荐失败:', e)
    } finally {
      loading.value.recommendations = false
    }
  }

  /**
   * 发送聊天消息
   */
  async function sendChatMessage(message: string) {
    loading.value.chat = true
    const userStore = useUserStore()
    
    // 添加用户消息
    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: message,
      timestamp: new Date()
    }
    chatMessages.value.push(userMessage)
    
    try {
      // 构建上下文
      const context = buildChatContext()
      
      // 获取用户ID，传递给后端以获取学生学习上下文
      const userId = userStore.userId
      
      const response = await aiChat({
        user_message: message,
        context,
        user_id: userId ? Number(userId) : undefined,
        user_role: 'student'
      })
      
      // 添加助手回复
      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-reply`,
        role: 'assistant',
        content: response.success ? response.reply : 'AI助手暂时不可用，请稍后再试。',
        timestamp: new Date()
      }
      chatMessages.value.push(assistantMessage)
      
      return response
      
    } catch (e) {
      console.error('聊天失败:', e)
      
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: 'AI助手暂时不可用，请稍后再试。',
        timestamp: new Date()
      }
      chatMessages.value.push(errorMessage)
      
      throw e
    } finally {
      loading.value.chat = false
    }
  }

  /**
   * 构建聊天上下文
   */
  function buildChatContext(): string {
    const contextParts: string[] = [
      '您是慧学的AI学习助手Tempo，帮助学生解答学习问题。'
    ]
    
    if (highPriorityPaths.value.length > 0) {
      contextParts.push(`学生当前有${highPriorityPaths.value.length}门高优先级课程需要关注。`)
    }
    
    if (criticalDeadlines.value.length > 0) {
      contextParts.push(`有${criticalDeadlines.value.length}个紧急截止日期即将到来。`)
    }
    
    const skills = masteredSkills.value.slice(0, 3).map(s => s.name).join('、')
    if (skills) {
      contextParts.push(`学生擅长的技能包括：${skills}。`)
    }
    
    return contextParts.join(' ')
  }

  /**
   * 清空聊天记录
   */
  function clearChat() {
    chatMessages.value = []
  }

  /**
   * 初始化仪表板
   */
  async function initializeDashboard(studentId: string, userName: string) {
    await loadDashboard()

    // 先探测 AI 总开关状态,关闭时跳过 AI 增强内容,避免无谓的 403 请求
    try {
      const status = await getAIStatus()
      isAIAvailable.value = !!status.available
    } catch (e) {
      isAIAvailable.value = false
    }
    if (!isAIAvailable.value) return

    // 异步获取 AI 增强内容
    fetchAISkillSummary()
    fetchAIRecommendation()
  }

  return {
    // State
    learningPaths,
    upcomingDeadlines,
    skillNodes,
    skillLinks,
    topSkills,
    aiSkillSummary,
    pathRecommendations,
    chatMessages,
    criticalCount,
    loading,
    error,
    isAIAvailable,
    
    // Getters
    activePaths,
    highPriorityPaths,
    criticalDeadlines,
    masteredSkills,
    
    // Actions
    loadDashboard,
    fetchAISkillSummary,
    fetchAIRecommendation,
    sendChatMessage,
    clearChat,
    initializeDashboard
  }
})
