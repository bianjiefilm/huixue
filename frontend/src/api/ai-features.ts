/**
 * AI Features API
 * 
 * Frontend wrapper for the AI Co-pilot features powered by PromptPilot
 */

import request from '@/utils/request'

// ==================== Types ====================

export interface AIServiceStatus {
  available: boolean
  message: string
  task_ids: Record<string, string>
}

// Recommendation
export interface RecommendationRequest {
  user_name: string
  course_title: string
  recommendation_reason: 'DEADLINE' | 'SKILL_GAP' | 'OPTIONAL_PATH' | 'MANDATORY'
  context_data: string
  user_id?: number
  user_role?: string
}

export interface RecommendationResponse {
  success: boolean
  reason_text: string
  run_id?: string
  tokens_used?: number
  error?: string
}

export interface BatchRecommendationItem {
  course_id: number
  course_title: string
  recommendation_reason: 'DEADLINE' | 'SKILL_GAP' | 'OPTIONAL_PATH' | 'MANDATORY'
  context_data: string
}

export interface BatchRecommendationRequest {
  user_id: number
  user_name: string
  courses: BatchRecommendationItem[]
  user_role?: string
}

export interface BatchRecommendationResponseItem {
  course_id: number
  priority: 'high' | 'medium' | 'low'
  reason_text: string
}

export interface BatchRecommendationResponse {
  success: boolean
  recommendations: BatchRecommendationResponseItem[]
  error?: string
}

// Brainstorm
export interface BrainstormRequest {
  user_prompt: string
  project_context?: string[]
  user_id?: number
  user_role?: string
}

export interface BrainstormResponse {
  success: boolean
  content?: string
  ideas: Array<{ idea: string }>
  run_id?: string
  tokens_used?: number
  error?: string
}

// Command Parse
export interface CommandParseRequest {
  user_raw_query: string
  user_id?: number
  user_role?: string
}

export interface CommandParseResponse {
  success: boolean
  command?: {
    action: string
    entity: string
    filters?: Record<string, any>
  }
  raw_response?: string
  run_id?: string
  tokens_used?: number
  error?: string
}

// Code Suggestion
export interface CodeSuggestionRequest {
  current_code_snippet: string
  task_objective: string
  task_answer?: string
  language?: string
  user_id?: number
  user_role?: string
}

export interface CodeSuggestionResponse {
  success: boolean
  suggestion: string
  run_id?: string
  tokens_used?: number
  error?: string
}

// Code Explanation
export interface CodeExplanationRequest {
  selected_code_snippet: string
  explanation_style?: '简洁' | '详细' | 'ELI5'
  user_id?: number
  user_role?: string
}

export interface CodeExplanationResponse {
  success: boolean
  explanation: string
  run_id?: string
  tokens_used?: number
  error?: string
}

// Error Diagnosis
export interface ErrorDiagnosisRequest {
  failed_code_snippet: string
  error_log: string
  failed_test_case_input: string
  failed_test_case_expected_output: string
  task_objective: string
  user_id?: number
  user_role?: string
}

export interface ErrorDiagnosisResponse {
  success: boolean
  diagnosis: string
  run_id?: string
  tokens_used?: number
  error?: string
}

// Chat
export interface ChatRequest {
  user_message: string
  context?: string
  user_id?: number
  user_role?: string
}

export interface ChatResponse {
  success: boolean
  reply: string
  run_id?: string
  tokens_used?: number
  error?: string
}

// ==================== API Functions ====================

const AI_FEATURES_BASE = '/api/v1/ai-features'

/**
 * Check if AI features service is available
 */
export async function getAIStatus(): Promise<AIServiceStatus> {
  const response = await request.get(`${AI_FEATURES_BASE}/status`)
  return response.data || response
}

/**
 * Generate a personalized recommendation reason for a course
 */
export async function generateRecommendation(data: RecommendationRequest): Promise<RecommendationResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/recommendation/explain`, data)
  return response.data || response
}

/**
 * Generate recommendation reasons for multiple courses at once
 */
export async function batchRecommendations(data: BatchRecommendationRequest): Promise<BatchRecommendationResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/recommendation/batch`, data)
  return response.data || response
}

/**
 * AI-powered brainstorming for project ideas
 */
export async function aiBrainstorm(data: BrainstormRequest): Promise<BrainstormResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/brainstorm`, data)
  return response.data || response
}

/**
 * Parse natural language command into structured action
 */
export async function parseCommand(data: CommandParseRequest): Promise<CommandParseResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/command/parse`, data)
  return response.data || response
}

/**
 * Get AI-powered code optimization suggestions
 */
export async function getCodeSuggestion(data: CodeSuggestionRequest): Promise<CodeSuggestionResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/code/suggest`, data)
  return response.data || response
}

/**
 * Get AI explanation for a code snippet
 */
export async function explainCode(data: CodeExplanationRequest): Promise<CodeExplanationResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/code/explain`, data)
  return response.data || response
}

/**
 * Get AI diagnosis for code evaluation errors
 */
export async function diagnoseError(data: ErrorDiagnosisRequest): Promise<ErrorDiagnosisResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/code/diagnose`, data)
  return response.data || response
}

/**
 * General AI chat
 * Note: AI chat requests may take longer than default timeout, so we use extended timeout
 */
export async function aiChat(data: ChatRequest): Promise<ChatResponse> {
  const response = await request.post(`${AI_FEATURES_BASE}/chat`, data, {
    timeout: 60000 // 60 seconds for AI requests
  })
  return response.data || response
}

// ==================== Student Dashboard API ====================

const STUDENT_DASHBOARD_BASE = '/api/v1/student'

export interface DashboardLearningPath {
  id: string
  courseId: string
  classroomCourseId: number
  title: string
  code: string
  coverImage?: string
  progress: number
  priority: 'deadline' | 'skill_gap' | 'optional' | 'mandatory' | 'completed'
  daysRemaining?: number
  dueDate?: string
  classroomId: string
  classroomName: string
  isMandatory: boolean
  totalTasks: number
  completedTasks: number
  attentionScore: number
  priorityReason?: string
}

export interface DashboardSkillNode {
  id: string
  name: string
  category: string
  mastery: number
  connections: string[]
}

export interface DashboardSkillLink {
  source: string
  target: string
  weight: number
}

export interface DashboardSkillConstellation {
  nodes: DashboardSkillNode[]
  links: DashboardSkillLink[]
  totalSkills: number
  topSkills: string[]
  aiSummary?: string
}

export interface DashboardDeadline {
  id: string
  title: string
  dueDate?: string
  daysRemaining: number
  type: string
  courseId: string
  classroomId: string
  isCritical: boolean
}

export interface DashboardRecommendation {
  courseId: string
  title: string
  reason: string
  matchScore: number
  tags?: string[]
}

export interface DashboardPriorityIntel {
  deadlines: DashboardDeadline[]
  recommendations: DashboardRecommendation[]
  criticalCount: number
}

export interface DashboardResponse {
  success: boolean
  activePaths: DashboardLearningPath[]
  skillConstellation: DashboardSkillConstellation
  priorityIntel: DashboardPriorityIntel
}

/**
 * 获取学生仪表板完整数据
 */
export async function getStudentDashboard(): Promise<DashboardResponse> {
  const response = await request.get(`${STUDENT_DASHBOARD_BASE}/dashboard`)
  return response.data || response
}

/**
 * 获取活跃学习路径
 */
export async function getLearningPaths(limit: number = 3): Promise<{success: boolean, data: DashboardLearningPath[]}> {
  const response = await request.get(`${STUDENT_DASHBOARD_BASE}/dashboard/learning-paths`, { params: { limit } })
  return response.data || response
}

/**
 * 获取技能星座数据
 */
export async function getSkillConstellation(): Promise<{success: boolean, data: DashboardSkillConstellation}> {
  const response = await request.get(`${STUDENT_DASHBOARD_BASE}/dashboard/skill-constellation`)
  return response.data || response
}

/**
 * 获取优先情报
 */
export async function getPriorityIntel(): Promise<{success: boolean, data: DashboardPriorityIntel}> {
  const response = await request.get(`${STUDENT_DASHBOARD_BASE}/dashboard/priority-intel`)
  return response.data || response
}

/**
 * 获取 AI 技能评语
 */
export async function getAISkillSummary(): Promise<{success: boolean, summary: string}> {
  const response = await request.post(`${STUDENT_DASHBOARD_BASE}/dashboard/ai-skill-summary`)
  return response.data || response
}

/**
 * 获取 AI 课程推荐
 */
export async function getAIRecommendation(): Promise<{success: boolean, recommendation?: DashboardRecommendation}> {
  const response = await request.post(`${STUDENT_DASHBOARD_BASE}/dashboard/ai-recommendation`)
  return response.data || response
}

