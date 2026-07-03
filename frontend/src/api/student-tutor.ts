/**
 * 学生端 AI 闯关辅导助手 API
 *
 * 对齐《慧学AI升级方案-v2.md》第十六章「学生端 AI 辅导」接口设计。
 *
 * 真实挂载路径是 POST /api/v1/ai/student-hints（不是方案文档字面的
 * /api/ai/student-hints）—— 后端 backend/app/api/v1/endpoints/ai_generation.py
 * 里的 student_hints_router 通过 app.main.py 以 prefix="/api/v1" 注册，
 * 且 frontend/vite.config.ts 的 '/api' 代理规则不做路径重写，
 * 所以前端必须直接打 /api/v1/ai/student-hints 才能被真实代理到后端同名路径，
 * 否则会打到后端一个不存在的 /api/ai/student-hints 路径上收到 404。
 *
 * 后端实现见 backend/app/services/tutor/（context_builder 物理隔离参考答案，
 * output_filter 落地前相似度过滤），端点本身见
 * backend/app/api/v1/endpoints/ai_generation.py 的 create_student_hint。
 */

import { post } from '@/utils/request'

// ==================== Types ====================

/** 三层提示机制层级，对齐方案第十二章：1=思路提示 2=错误解释 3=局部修正建议 */
export type HintLevel = 1 | 2 | 3

export interface StudentHintRequest {
  challenge_id: string
  question: string
  eval_error?: string | null
  hint_level: HintLevel
}

export interface StudentHintResponse {
  hint_level: HintLevel
  message: string
}

// ==================== API ====================

const STUDENT_HINTS_ENDPOINT = '/api/v1/ai/student-hints'

/**
 * 向 AI 闯关助教请求一次提示。
 *
 * 注意：本函数不缓存、不重试；调用方（HintPanel.vue）负责展示 loading /
 * 错误状态，以及按提示次数限额（由后端管理员配置项控制,见方案第二十一章）
 * 禁用按钮。
 */
export function requestStudentHint(payload: StudentHintRequest): Promise<StudentHintResponse> {
  return post<StudentHintResponse>(STUDENT_HINTS_ENDPOINT, payload)
}
