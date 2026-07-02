/**
 * AI学习助手相关API
 */

import request from '@/utils/request'

// AI对话
export interface ChatRequest {
  message: string
  context?: string
  user_id?: number
}

export interface ChatResponse {
  reply: string
  quota_info: any
  success: boolean
  error?: string
}

export function chatWithAI(data: ChatRequest) {
  return request.post('/ai/chat', data)
}

// 概念解释
export interface ExplainConceptRequest {
  concept: string
  context?: string
  user_id?: number
}

export interface ExplainConceptResponse {
  explanation: string
  quota_info: any
  success: boolean
  error?: string
}

export function explainConcept(data: ExplainConceptRequest) {
  return request.post('/ai/explain-concept', data)
}

// 试题生成
export interface GenerateQuestionsRequest {
  knowledge_point: string
  question_type: string
  count?: number
  difficulty?: string
  user_id?: number
}

export interface QuestionData {
  type: string
  content: string
  options?: any[]
  correct_answers?: any[]
  raw_response?: string
}

export interface GenerateQuestionsResponse {
  questions: QuestionData[]
  count: number
  quota_info: any
  success: boolean
  error?: string
}

export function generateQuestions(data: GenerateQuestionsRequest) {
  return request.post('/ai/generate-questions', data)
}

// 试题质量检查
export interface CheckQualityRequest {
  question_data: any
  user_id?: number
}

export interface CheckQualityResponse {
  quality_score: number
  suggestions: string[]
  detailed_analysis: string
  quota_info: any
  success: boolean
  error?: string
}

export function checkQuestionQuality(data: CheckQualityRequest) {
  return request.post('/ai/check-quality', data)
}

// 获取用户额度信息
export interface QuotaInfo {
  user_role: string
  monthly_quota: number
  used_this_month: number
  remaining: number
  reset_date?: string
  usage_by_type: Record<string, number>
  estimated_cost: number
}

export function getUserQuota(userId: number) {
  return request.get(`/ai/quota/${userId}`)
}
