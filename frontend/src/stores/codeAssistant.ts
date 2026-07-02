/**
 * Code Assistant Store
 * 
 * 管理代码助手相关的状态和 AI 功能
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getCodeSuggestion, 
  explainCode, 
  diagnoseError,
  type CodeSuggestionRequest,
  type CodeExplanationRequest,
  type ErrorDiagnosisRequest
} from '@/api/ai-features'

export interface CodeContext {
  code: string
  language: string
  taskObjective?: string
  taskAnswer?: string
  errorLog?: string
  testInput?: string
  expectedOutput?: string
}

export interface AssistantMessage {
  id: string
  type: 'suggestion' | 'explanation' | 'diagnosis' | 'error'
  content: string
  timestamp: Date
  codeSnippet?: string
  loading?: boolean
}

export const useCodeAssistantStore = defineStore('codeAssistant', () => {
  // State
  const isOpen = ref(false)
  const activeTab = ref<'suggestion' | 'explanation' | 'diagnosis'>('explanation')
  const messages = ref<AssistantMessage[]>([])
  const currentContext = ref<CodeContext | null>(null)
  const loading = ref({
    suggestion: false,
    explanation: false,
    diagnosis: false
  })
  const error = ref<string | null>(null)

  // Getters
  const hasMessages = computed(() => messages.value.length > 0)
  const isLoading = computed(() => 
    loading.value.suggestion || loading.value.explanation || loading.value.diagnosis
  )

  // Actions
  
  /**
   * 打开代码助手面板
   */
  function open(tab?: 'suggestion' | 'explanation' | 'diagnosis') {
    isOpen.value = true
    if (tab) {
      activeTab.value = tab
    }
  }

  /**
   * 关闭代码助手面板
   */
  function close() {
    isOpen.value = false
  }

  /**
   * 设置当前代码上下文
   */
  function setContext(context: CodeContext) {
    currentContext.value = context
  }

  /**
   * 获取代码建议
   */
  async function fetchSuggestion(code: string, taskObjective: string, taskAnswer?: string, language: string = 'Python') {
    loading.value.suggestion = true
    error.value = null

    const loadingMsg: AssistantMessage = {
      id: `msg-${Date.now()}-loading`,
      type: 'suggestion',
      content: '正在分析代码...',
      timestamp: new Date(),
      codeSnippet: code.slice(0, 100),
      loading: true
    }
    messages.value.push(loadingMsg)

    try {
      const response = await getCodeSuggestion({
        current_code_snippet: code,
        task_objective: taskObjective,
        task_answer: taskAnswer,
        language
      })

      // 移除 loading 消息
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

      if (response.success) {
        messages.value.push({
          id: `msg-${Date.now()}`,
          type: 'suggestion',
          content: response.suggestion || '暂无建议',
          timestamp: new Date(),
          codeSnippet: code.slice(0, 100)
        })
      } else {
        throw new Error(response.error || '获取建议失败')
      }

      return response
    } catch (e: any) {
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      error.value = e.message || '获取建议失败'
      messages.value.push({
        id: `msg-${Date.now()}-error`,
        type: 'error',
        content: `获取建议失败: ${e.message}`,
        timestamp: new Date()
      })
      throw e
    } finally {
      loading.value.suggestion = false
    }
  }

  /**
   * 获取代码解释
   */
  async function fetchExplanation(code: string, style: '简洁' | '详细' | 'ELI5' = '详细') {
    loading.value.explanation = true
    error.value = null

    const loadingMsg: AssistantMessage = {
      id: `msg-${Date.now()}-loading`,
      type: 'explanation',
      content: '正在解释代码...',
      timestamp: new Date(),
      codeSnippet: code.slice(0, 100),
      loading: true
    }
    messages.value.push(loadingMsg)

    try {
      const response = await explainCode({
        selected_code_snippet: code,
        explanation_style: style
      })

      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

      if (response.success) {
        messages.value.push({
          id: `msg-${Date.now()}`,
          type: 'explanation',
          content: response.explanation || '暂无解释',
          timestamp: new Date(),
          codeSnippet: code.slice(0, 100)
        })
      } else {
        throw new Error(response.error || '获取解释失败')
      }

      return response
    } catch (e: any) {
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      error.value = e.message || '获取解释失败'
      messages.value.push({
        id: `msg-${Date.now()}-error`,
        type: 'error',
        content: `获取解释失败: ${e.message}`,
        timestamp: new Date()
      })
      throw e
    } finally {
      loading.value.explanation = false
    }
  }

  /**
   * 获取错误诊断
   */
  async function fetchDiagnosis(
    code: string, 
    errorLog: string, 
    testInput: string, 
    expectedOutput: string,
    taskObjective: string
  ) {
    loading.value.diagnosis = true
    error.value = null

    const loadingMsg: AssistantMessage = {
      id: `msg-${Date.now()}-loading`,
      type: 'diagnosis',
      content: '正在诊断错误...',
      timestamp: new Date(),
      codeSnippet: code.slice(0, 100),
      loading: true
    }
    messages.value.push(loadingMsg)

    try {
      const response = await diagnoseError({
        failed_code_snippet: code,
        error_log: errorLog,
        failed_test_case_input: testInput,
        failed_test_case_expected_output: expectedOutput,
        task_objective: taskObjective
      })

      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)

      if (response.success) {
        messages.value.push({
          id: `msg-${Date.now()}`,
          type: 'diagnosis',
          content: response.diagnosis || '暂无诊断结果',
          timestamp: new Date(),
          codeSnippet: code.slice(0, 100)
        })
      } else {
        throw new Error(response.error || '错误诊断失败')
      }

      return response
    } catch (e: any) {
      messages.value = messages.value.filter(m => m.id !== loadingMsg.id)
      error.value = e.message || '错误诊断失败'
      messages.value.push({
        id: `msg-${Date.now()}-error`,
        type: 'error',
        content: `错误诊断失败: ${e.message}`,
        timestamp: new Date()
      })
      throw e
    } finally {
      loading.value.diagnosis = false
    }
  }

  /**
   * 清除消息
   */
  function clearMessages() {
    messages.value = []
    error.value = null
  }

  return {
    // State
    isOpen,
    activeTab,
    messages,
    currentContext,
    loading,
    error,
    
    // Getters
    hasMessages,
    isLoading,
    
    // Actions
    open,
    close,
    setContext,
    fetchSuggestion,
    fetchExplanation,
    fetchDiagnosis,
    clearMessages
  }
})

