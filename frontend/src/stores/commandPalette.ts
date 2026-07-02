/**
 * Command Palette State Store
 * 
 * Manages command palette visibility, search query, and results
 * Enhanced with AI NLU (Natural Language Understanding) support
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Component } from 'vue'
import { parseCommand } from '@/api/ai-features'

export interface CommandItem {
  id: string
  label: string
  description?: string
  icon?: Component
  shortcut?: string
  keywords?: string[]
  category?: 'navigation' | 'action' | 'recent' | 'search' | 'ai'
  action: () => void | Promise<void>
}

export interface AICommandResult {
  action: string
  entity: string
  filters?: Record<string, any>
  params?: Record<string, any>
}

export const useCommandPaletteStore = defineStore('commandPalette', () => {
  // Router will be set when initDefaultCommands is called
  let routerInstance: ReturnType<typeof useRouter> | null = null
  
  // State
  const isOpen = ref(false)
  const query = ref('')
  const selectedIndex = ref(0)
  const recentCommands = ref<string[]>([])  // IDs of recently used commands
  
  // AI NLU state
  const isAIProcessing = ref(false)
  const aiResult = ref<AICommandResult | null>(null)
  const aiError = ref<string | null>(null)
  
  // Registered commands
  const commands = ref<CommandItem[]>([])
  
  // Computed
  const filteredCommands = computed(() => {
    if (!query.value.trim()) {
      // Show recent commands first, then all commands
      const recent = commands.value.filter(c => recentCommands.value.includes(c.id))
      const others = commands.value.filter(c => !recentCommands.value.includes(c.id))
      return [...recent.slice(0, 3), ...others].slice(0, 10)
    }
    
    const q = query.value.toLowerCase()
    return commands.value.filter(cmd => {
      const matchLabel = cmd.label.toLowerCase().includes(q)
      const matchDesc = cmd.description?.toLowerCase().includes(q)
      const matchKeywords = cmd.keywords?.some(k => k.toLowerCase().includes(q))
      return matchLabel || matchDesc || matchKeywords
    }).slice(0, 10)
  })
  
  const selectedCommand = computed(() => {
    return filteredCommands.value[selectedIndex.value]
  })
  
  // Actions
  function open() {
    isOpen.value = true
    query.value = ''
    selectedIndex.value = 0
  }
  
  function close() {
    isOpen.value = false
    query.value = ''
    selectedIndex.value = 0
  }
  
  function toggle() {
    if (isOpen.value) {
      close()
    } else {
      open()
    }
  }
  
  function setQuery(value: string) {
    query.value = value
    selectedIndex.value = 0
  }
  
  function moveSelection(direction: 'up' | 'down') {
    const maxIndex = filteredCommands.value.length - 1
    if (direction === 'up') {
      selectedIndex.value = selectedIndex.value > 0 ? selectedIndex.value - 1 : maxIndex
    } else {
      selectedIndex.value = selectedIndex.value < maxIndex ? selectedIndex.value + 1 : 0
    }
  }
  
  function selectIndex(index: number) {
    selectedIndex.value = index
  }
  
  async function executeSelected() {
    const cmd = selectedCommand.value
    if (cmd) {
      // Track as recent
      addToRecent(cmd.id)
      
      // Execute and close
      close()
      await cmd.action()
    }
  }
  
  async function executeCommand(id: string) {
    const cmd = commands.value.find(c => c.id === id)
    if (cmd) {
      addToRecent(id)
      close()
      await cmd.action()
    }
  }
  
  function addToRecent(id: string) {
    const filtered = recentCommands.value.filter(i => i !== id)
    recentCommands.value = [id, ...filtered].slice(0, 5)
    localStorage.setItem('command-palette-recent', JSON.stringify(recentCommands.value))
  }
  
  function loadRecent() {
    try {
      const stored = localStorage.getItem('command-palette-recent')
      if (stored) {
        recentCommands.value = JSON.parse(stored)
      }
    } catch {
      recentCommands.value = []
    }
  }
  
  function registerCommand(command: CommandItem) {
    // Avoid duplicates
    const existing = commands.value.findIndex(c => c.id === command.id)
    if (existing > -1) {
      commands.value[existing] = command
    } else {
      commands.value.push(command)
    }
  }
  
  function registerCommands(newCommands: CommandItem[]) {
    newCommands.forEach(registerCommand)
  }
  
  function unregisterCommand(id: string) {
    commands.value = commands.value.filter(c => c.id !== id)
  }
  
  function clearCommands() {
    commands.value = []
  }
  
  // AI NLU: Parse natural language command
  async function parseNaturalLanguageCommand(rawQuery: string): Promise<AICommandResult | null> {
    if (!rawQuery.trim() || rawQuery.length < 4) return null
    
    isAIProcessing.value = true
    aiError.value = null
    aiResult.value = null
    
    try {
      const response = await parseCommand({
        user_raw_query: rawQuery
      })
      
      if (response.success && response.command) {
        aiResult.value = response.command
        
        // 根据 AI 解析结果执行操作
        await executeAICommand(response.command)
        
        return response.command
      } else {
        aiError.value = response.error || '无法理解您的命令'
        return null
      }
    } catch (e: any) {
      aiError.value = e.message || 'AI 命令解析失败'
      console.error('AI command parse error:', e)
      return null
    } finally {
      isAIProcessing.value = false
    }
  }
  
  // Execute AI parsed command
  async function executeAICommand(cmd: AICommandResult) {
    const { action, entity, filters, params } = cmd
    
    // 根据解析结果执行对应操作
    switch (action) {
      case 'navigate':
        // 导航到指定页面
        const navMap: Record<string, string> = {
          'dashboard': '/student-dashboard',
          'classroom': '/classroom',
          'course': '/course',
          'project': '/project',
          'visual': '/visual',
          'ml': '/ml',
          'admin': '/admin'
        }
        const path = navMap[entity] || `/${entity}`
        routerInstance?.push(path)
        break
        
      case 'search':
        // 搜索操作
        const searchMap: Record<string, string> = {
          'classroom': '/classroom',
          'classroom_course': '/classroom',
          'course': '/course',
          'students': '/admin/users'
        }
        const searchPath = searchMap[entity] || '/classroom'
        routerInstance?.push({
          path: searchPath,
          query: filters
        })
        break
        
      case 'create':
        // 创建操作
        const createMap: Record<string, string> = {
          'classroom': '/classroom/create',
          'course': '/course/create',
          'practice': '/course/practice/create',
          'training': '/training/create'
        }
        const createPath = createMap[entity]
        if (createPath) {
          routerInstance?.push(createPath)
        }
        break
        
      case 'list':
        // 列表操作
        const listMap: Record<string, string> = {
          'students': '/admin/users',
          'classrooms': '/classroom',
          'courses': '/course'
        }
        const listPath = listMap[entity] || `/${entity}`
        routerInstance?.push(listPath)
        break
        
      default:
        console.log('Unknown AI command action:', action)
    }
    
    close()
  }
  
  // Check if query looks like a natural language command
  function isNaturalLanguageQuery(q: string): boolean {
    // 如果查询包含中文动词或命令词，认为是自然语言
    const nlPatterns = [
      /搜索|查找|打开|创建|新建|删除|编辑|修改|查看|显示|列出|去到/,
      /帮我|请|给我|我想|我要/,
      /谁|什么|哪个|怎么/
    ]
    return nlPatterns.some(p => p.test(q))
  }
  
  // Initialize with default navigation commands
  function initDefaultCommands(router?: ReturnType<typeof useRouter>) {
    if (router) {
      routerInstance = router
    }
    
    const navigationCommands: CommandItem[] = [
      {
        id: 'nav-dashboard',
        label: '学习仪表板',
        description: '查看学习进度和推荐',
        category: 'navigation',
        keywords: ['dashboard', 'home', '首页', '仪表板'],
        action: () => routerInstance?.push('/student-dashboard')
      },
      {
        id: 'nav-classroom',
        label: '我的课堂',
        description: '查看所有课堂',
        category: 'navigation',
        keywords: ['classroom', '课堂', '班级'],
        action: () => routerInstance?.push('/classroom')
      },
      {
        id: 'nav-course',
        label: '课程实践',
        description: '浏览课程和练习',
        category: 'navigation',
        keywords: ['course', '课程', '实践'],
        action: () => routerInstance?.push('/course')
      },
      {
        id: 'nav-project',
        label: '项目实训',
        description: '查看项目画布',
        category: 'navigation',
        keywords: ['project', '项目', '实训'],
        action: () => routerInstance?.push('/project')
      },
      {
        id: 'nav-visual',
        label: '可视化分析',
        description: '数据可视化工具',
        category: 'navigation',
        keywords: ['visual', '可视化', '分析', '图表'],
        action: () => routerInstance?.push('/visual')
      },
      {
        id: 'nav-ml',
        label: '机器学习',
        description: '机器学习建模',
        category: 'navigation',
        keywords: ['ml', '机器学习', 'machine learning'],
        action: () => routerInstance?.push('/ml')
      }
    ]
    
    const actionCommands: CommandItem[] = [
      {
        id: 'action-create-classroom',
        label: '创建课堂',
        description: '新建一个课堂',
        category: 'action',
        keywords: ['create', '创建', '新建', 'new'],
        action: () => routerInstance?.push('/classroom/create')
      },
      {
        id: 'action-toggle-sidebar',
        label: '切换侧边栏',
        description: '展开/收起侧边栏',
        category: 'action',
        shortcut: '⌘B',
        keywords: ['sidebar', '侧边栏', 'toggle'],
        action: () => {
          // Will be handled by the component
        }
      }
    ]
    
    registerCommands([...navigationCommands, ...actionCommands])
  }
  
  return {
    // State
    isOpen,
    query,
    selectedIndex,
    commands,
    recentCommands,
    
    // AI State
    isAIProcessing,
    aiResult,
    aiError,
    
    // Computed
    filteredCommands,
    selectedCommand,
    
    // Actions
    open,
    close,
    toggle,
    setQuery,
    moveSelection,
    selectIndex,
    executeSelected,
    executeCommand,
    loadRecent,
    registerCommand,
    registerCommands,
    unregisterCommand,
    clearCommands,
    initDefaultCommands,
    
    // AI Actions
    parseNaturalLanguageCommand,
    executeAICommand,
    isNaturalLanguageQuery
  }
})

