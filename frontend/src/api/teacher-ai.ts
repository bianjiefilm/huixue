// 教师端 AI 生成实践闯关任务 - API 调用契约
//
// 对齐《慧学AI升级方案-v2.md》第十六章「接口设计」-「教师端生成流程」。
// 后端接口由并行 agent 在 backend/doc_parser/、backend/ai_orch/ 等目录开发,
// 本文件只定义前端调用契约(URL、方法、请求/响应类型),不保证当前能真正联调成功。
//
// request 封装风格与 @/api/ai-generation.ts 保持一致,复用 @/utils/request。

import { request } from '@/utils/request'

// ==================== 通用类型 ====================

/** 学生水平四档,对齐方案第五章表格用词 */
export type StudentLevel =
  | 'zero_basis' // 零基础
  | 'learned_but_cannot_apply' // 学过但不会用
  | 'can_complete_basic_task' // 能独立完成基础任务
  | 'can_do_project' // 能做项目

export const STUDENT_LEVEL_OPTIONS: Array<{ value: StudentLevel; label: string; desc: string }> = [
  { value: 'zero_basis', label: '零基础', desc: '任务拆得更细，步骤更明确，测试集简单' },
  { value: 'learned_but_cannot_apply', label: '学过但不会用', desc: '多给操作型任务，少给概念解释' },
  { value: 'can_complete_basic_task', label: '能独立完成基础任务', desc: '增加综合步骤，减少提示' },
  { value: 'can_do_project', label: '能做项目', desc: '允许开放式任务、综合评测、人工验收' }
]

/** 评测方式 */
export type EvaluationMode = 'auto' | 'manual'

/** 生成任务状态 */
export type GenerationJobStatus =
  | 'pending'
  | 'parsing'
  | 'knowledge_ready'
  | 'drafting'
  | 'draft_ready'
  | 'committed'
  | 'failed'

// ==================== 1. 创建生成任务 POST /api/ai/generation-jobs ====================

export interface CreateGenerationJobRequest {
  /** 已有教学资源的资料 ID 列表(第一版仅支持"从已有教学资源选择") */
  source_document_ids: string[]
  /** 教学目标 */
  objective: string
  /** 学生水平 */
  student_level: StudentLevel
  /** 建议关卡数，留空则由 AI 自动建议 */
  suggested_level_count?: number
}

export interface CreateGenerationJobResponse {
  job_id: string
  status: GenerationJobStatus
  created_at: string
}

export function createGenerationJob(payload: CreateGenerationJobRequest) {
  return request<CreateGenerationJobResponse>({
    url: '/api/ai/generation-jobs',
    method: 'post',
    data: payload
  })
}

// ==================== 2. 获取知识点拆解结果 GET .../knowledge-points ====================

export interface KnowledgePointSource {
  document_id: string
  document_title: string
  /** 第几页 / 章节位置描述，如 "第 3 页" */
  location: string
}

export interface KnowledgePoint {
  knowledge_point_id: string
  /** 知识点名称 */
  name: string
  /** 简要说明 */
  summary: string
  /** 来源位置 */
  source: KnowledgePointSource
  /** 建议难度 */
  suggested_difficulty: string
  /** 是否建议转为实践任务 */
  suggested_for_challenge: boolean
  /** 老师是否保留，默认 true，前端本地态，PATCH 时提交 */
  confirmed: boolean
}

export interface GetKnowledgePointsResponse {
  job_id: string
  status: GenerationJobStatus
  knowledge_points: KnowledgePoint[]
}

export function getKnowledgePoints(jobId: string) {
  return request<GetKnowledgePointsResponse>({
    url: `/api/ai/generation-jobs/${jobId}/knowledge-points`,
    method: 'get'
  })
}

// ==================== 3. 确认/删除知识点 PATCH .../knowledge-points ====================

export interface ConfirmKnowledgePointsRequest {
  /** 保留的知识点 ID 列表 */
  confirmed_ids: string[]
  /** 删除的知识点 ID 列表 */
  removed_ids: string[]
}

export interface ConfirmKnowledgePointsResponse {
  job_id: string
  confirmed_count: number
  removed_count: number
}

export function confirmKnowledgePoints(
  jobId: string,
  payload: ConfirmKnowledgePointsRequest
) {
  return request<ConfirmKnowledgePointsResponse>({
    url: `/api/ai/generation-jobs/${jobId}/knowledge-points`,
    method: 'patch',
    data: payload
  })
}

// ==================== 4. 生成关卡草稿 POST .../challenge-drafts ====================

export interface GenerateChallengeDraftsRequest {
  /** 生成关卡数，留空则由 AI 按知识点密度自动建议 */
  level_count?: number
}

export interface GenerateChallengeDraftsResponse {
  job_id: string
  status: GenerationJobStatus
  draft_count: number
}

export function generateChallengeDrafts(
  jobId: string,
  payload: GenerateChallengeDraftsRequest = {}
) {
  return request<GenerateChallengeDraftsResponse>({
    url: `/api/ai/generation-jobs/${jobId}/challenge-drafts`,
    method: 'post',
    data: payload
  })
}

// ==================== 5. 获取草稿列表 GET .../challenge-drafts ====================

export interface ChallengeDraftTestCaseSummary {
  visible_count: number
  hidden_count: number
}

export interface ChallengeDraft {
  draft_id: string
  order: number
  /** 关卡名称 */
  title: string
  /** 难度：零基础 / 入门 / 中等 / 综合 */
  difficulty: string
  /** 技能标签 */
  skill_tags: string[]
  /** 过关任务，Markdown */
  task_handbook: string
  /** 评测方式 */
  evaluation_mode: EvaluationMode
  student_template?: string
  judge_script?: string
  test_case_summary?: ChallengeDraftTestCaseSummary
  /** 来源知识点 ID */
  source_knowledge_point_ids: string[]
  /** 校验状态：未校验 / 校验中 / 通过 / 失败 */
  validation_status: 'not_validated' | 'validating' | 'passed' | 'failed'
}

export interface GetChallengeDraftsResponse {
  job_id: string
  drafts: ChallengeDraft[]
}

export function getChallengeDrafts(jobId: string) {
  return request<GetChallengeDraftsResponse>({
    url: `/api/ai/generation-jobs/${jobId}/challenge-drafts`,
    method: 'get'
  })
}

// ==================== 6. 编辑单个草稿 PATCH /api/ai/challenge-drafts/{draft_id} ====================

export function updateChallengeDraft(draftId: string, payload: Partial<ChallengeDraft>) {
  return request<ChallengeDraft>({
    url: `/api/ai/challenge-drafts/${draftId}`,
    method: 'patch',
    data: payload
  })
}

// ==================== 7. 批量重新生成 POST /api/ai/challenge-drafts/batch-regenerate ====================

export interface BatchRegenerateRequest {
  draft_ids: string[]
  instruction: string
}

export function batchRegenerateDrafts(payload: BatchRegenerateRequest) {
  return request<{ regenerated: string[] }>({
    url: '/api/ai/challenge-drafts/batch-regenerate',
    method: 'post',
    data: payload
  })
}

// ==================== 8. 校验草稿(含攻击验证) POST .../{draft_id}/validate ====================

export interface AttackMatrixRow {
  attack_type: 'stub' | 'hardcode' | 'shape_only' | 'identity'
  fail_rate: number
  threshold: number
  passed: boolean
}

export interface RedlineRow {
  function_name: string
  independent_inputs: boolean
  boundary_case: boolean
  negative_type_assert: boolean
  tolerance_assert: boolean
  full_key_assert: boolean
}

export interface ValidateDraftResponse {
  draft_id: string
  passed: boolean
  json_schema_valid: boolean
  command_whitelist_valid: boolean
  reference_answer_runs: boolean
  attack_matrix: AttackMatrixRow[]
  redline_table: RedlineRow[]
  warnings: string[]
}

export function validateChallengeDraft(draftId: string) {
  return request<ValidateDraftResponse>({
    url: `/api/ai/challenge-drafts/${draftId}/validate`,
    method: 'post'
  })
}

// ==================== 9. 保存为实践课程 POST .../commit-to-practice ====================

export interface CommitToPracticeRequest {
  practice_name: string
  visibility: 'private_draft' | 'published'
}

export interface CommitToPracticeResponse {
  practice_id: number
  challenge_count: number
}

export function commitToPractice(jobId: string, payload: CommitToPracticeRequest) {
  return request<CommitToPracticeResponse>({
    url: `/api/ai/generation-jobs/${jobId}/commit-to-practice`,
    method: 'post',
    data: payload
  })
}

// ==================== 辅助:已有教学资源列表(资料选择用) ====================
// TODO: 后端资料选择接口路径待确认，暂时复用可能已存在的教学资源查询接口占位。
// 若后端最终路径不同，仅需修改本函数内 url，不影响上层组件调用签名。

export interface TeachingResourceItem {
  document_id: string
  title: string
  file_type: string
  pages?: number
  uploaded_at: string
}

export function listTeachingResources(keyword?: string) {
  return request<{ items: TeachingResourceItem[] }>({
    url: '/api/ai/source-documents',
    method: 'get',
    params: { keyword }
  })
}
