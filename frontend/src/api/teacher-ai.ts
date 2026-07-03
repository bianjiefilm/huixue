// 教师端 AI 生成实践闯关任务 - API 调用契约
//
// 对齐后端真实端点 backend/app/api/v1/endpoints/ai_generation.py（4 个已联调可用）。
// 与《慧学AI升级方案-v2.md》第十六章设计稿路径不同：路径前缀是 /api/v1/ai/...
// （对齐仓库既有路由惯例），创建任务是直接文件上传（multipart）而不是从已有
// 资源库选择（后端暂无资源列表接口），字段名以后端 Pydantic 模型为准。
//
// request 封装风格与 @/api/ai-generation.ts 保持一致，复用 @/utils/request。

import { request } from '@/utils/request'

// ==================== 通用类型 ====================

/** 学生水平四档，对齐方案第五章表格用词 */
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

export type EvaluationMode = 'auto' | 'manual'

export type GenerationJobStatus =
  | 'uploaded'
  | 'parsed'
  | 'knowledge_extracted'
  | 'knowledge_confirmed'
  | 'draft_generated'
  | 'validated'
  | 'committed'
  | 'failed'

// ==================== ① 创建生成任务 POST /api/v1/ai/generation-jobs ====================
// 后端签名是 multipart/form-data：file + objective + student_level + teacher_id

export interface GenerationJob {
  id: string
  objective: string | null
  student_level: string | null
  status: GenerationJobStatus
  model_name: string | null
  suggested_challenge_count: number | null
  selected_challenge_count: number | null
}

export interface KnowledgePointSourceRef {
  chunk_id: string
  location: string
}

export interface KnowledgePoint {
  id: string
  title: string
  summary: string | null
  source_refs_json: KnowledgePointSourceRef[] | null
  suggested_difficulty: string | null
  suggested_challenge_type: 'auto' | 'manual' | null
  selected: boolean
}

export interface CreateGenerationJobResponse {
  job: GenerationJob
  knowledge_points: KnowledgePoint[]
}

// 真实调用发现的问题：这两个端点内部会真实调用 LLM（文档解析+知识点拆解，
// 或关卡草稿生成），实测耗时可达 55 秒以上（尤其是关卡生成，模型输出的复杂
// JSON 有时要重试）。全局 axios 默认 timeout 只有 10 秒（见 @/utils/request.ts），
// 会导致前端提前判定失败、弹错误提示，但后端其实还在正常处理并最终成功写库——
// 用户会看到"失败"但数据其实生成好了，这是比真失败更糟的体验。因此这两个调用
// 单独传更长的 timeout，不改全局默认值（其他快接口不该被拖慢超时判定）。
//
// 后续 E2E UAT 用真实较大文档（7个知识点）复现出更严重的情况：后端 doubao_client
// 单次调用超时+重试，最坏情况耗时可达 300 秒（已将后端超时从 30s 提到
// 90s/150s，但两次重试仍可能累计到这个量级）。前端超时必须留出比后端最坏情况
// 更宽的余量，否则同样的"后端在跑、前端先放弃"问题会在大文档场景下重现。
const LLM_CALL_TIMEOUT_MS = 330000

export function createGenerationJob(payload: {
  file: File
  objective: string
  studentLevel: StudentLevel
  teacherId?: number
}) {
  const formData = new FormData()
  formData.append('file', payload.file)
  formData.append('objective', payload.objective)
  formData.append('student_level', payload.studentLevel)
  formData.append('teacher_id', String(payload.teacherId ?? 1))

  return request<CreateGenerationJobResponse>({
    url: '/api/v1/ai/generation-jobs',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: LLM_CALL_TIMEOUT_MS
  })
}

// ==================== ② 获取知识点拆解结果 GET .../knowledge-points ====================

export function getKnowledgePoints(jobId: string) {
  return request<KnowledgePoint[]>({
    url: `/api/v1/ai/generation-jobs/${jobId}/knowledge-points`,
    method: 'get'
  })
}

// ==================== ③ 确认/删除知识点 PATCH .../knowledge-points ====================
// 后端语义是"传入要保留的完整 ID 列表"，不是 confirmed_ids/removed_ids 两个数组

export function confirmKnowledgePoints(jobId: string, selectedKnowledgePointIds: string[]) {
  return request<KnowledgePoint[]>({
    url: `/api/v1/ai/generation-jobs/${jobId}/knowledge-points`,
    method: 'patch',
    data: { selected_knowledge_point_ids: selectedKnowledgePointIds }
  })
}

// ==================== ④ 生成关卡草稿 POST .../challenge-drafts ====================

export interface ChallengeDraft {
  id: string
  title: string
  difficulty: string | null
  skill_tags_json: string[] | null
  task_markdown: string | null
  evaluation_mode: EvaluationMode
  student_files_json: Record<string, string> | null
  test_cases_json: Array<{ input: unknown; output: unknown }> | null
  hidden_test_cases_json: Array<{ input: unknown; output: unknown }> | null
  reference_answer: string | null
  status: string
}

export function generateChallengeDrafts(jobId: string, challengeCount = 3) {
  return request<ChallengeDraft[]>({
    url: `/api/v1/ai/generation-jobs/${jobId}/challenge-drafts`,
    method: 'post',
    data: { challenge_count: challengeCount },
    timeout: LLM_CALL_TIMEOUT_MS
  })
}

export function getChallengeDrafts(jobId: string) {
  return request<ChallengeDraft[]>({
    url: `/api/v1/ai/generation-jobs/${jobId}/challenge-drafts`,
    method: 'get'
  })
}

// ==================== 尚未实现的后端能力 ====================
// 「保存为实践课程」(commit-to-practice) 需要对接现有 practices 表体系，
// 「批量重新生成」「版本对比」「草稿校验」「已有资源库选择」在方案文档里有设计，
// 但后端还没有对应端点。不在这里定义会调用 404 的函数占位，等后端真正实现
// 时再加，避免留下调用即报错的死代码。
