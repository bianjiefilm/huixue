/**
 * 学生端 AI 闯关辅导助手 API
 *
 * 对齐《慧学AI升级方案-v2.md》第十六章「学生端 AI 辅导」接口设计：
 * POST /api/ai/student-hints
 *
 * 后端实现见 backend/app/services/tutor/（本文件对应 endpoint 尚未在
 * backend router 中注册，需要另行由负责 router 的 agent 接入）。
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

const STUDENT_HINTS_ENDPOINT = '/api/ai/student-hints'

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
