<template>
  <div class="hint-panel">
    <div class="hint-panel__header">
      <span class="hint-panel__title">AI 闯关助教</span>
      <span class="hint-panel__level-badge">第 {{ hintLevel }} 层提示</span>
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">当前任务</div>
      <div class="hint-panel__task">{{ challengeName }}</div>
      <div class="hint-panel__task-id">关卡 ID：{{ effectiveChallengeId }}</div>
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">我的问题</div>
      <textarea
        v-model="question"
        class="hint-panel__question-input"
        placeholder="例如：为什么我的评测失败？"
        rows="2"
      />
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">评测报错（可选，联调测试用，正常场景由做题页自动传入）</div>
      <textarea
        v-model="evalErrorInput"
        class="hint-panel__question-input"
        placeholder="粘贴评测失败报错文本，留空则视为未评测过"
        rows="2"
      />
    </div>

    <div class="hint-panel__section" v-if="requestError">
      <div class="hint-panel__label">请求出错</div>
      <pre class="hint-panel__eval-error">{{ requestError }}</pre>
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">AI 提示</div>
      <div class="hint-panel__reply" v-if="!loading && replyMessage" data-testid="hint-reply">
        {{ replyMessage }}
      </div>
      <div class="hint-panel__reply hint-panel__reply--placeholder" v-else-if="!loading">
        点击下方按钮向 AI 助教求助，提示不会包含完整答案。
      </div>
      <div class="hint-panel__reply hint-panel__reply--loading" v-else>思考中...</div>
    </div>

    <div class="hint-panel__footer">
      <span class="hint-panel__quota">本关剩余提示次数：{{ remainingHints }}</span>
      <button
        class="hint-panel__ask-btn"
        :disabled="loading || remainingHints <= 0"
        @click="handleAskAI"
      >
        问 AI 助教
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 学生端 AI 辅导侧栏组件
 *
 * 对齐《慧学AI升级方案-v2.md》第二十章「学生端新增组件 - AI 辅导侧栏」：
 * 显示当前任务、学生问题、AI 提示、提示层级；不显示答案。
 *
 * 真实接入 POST /api/v1/ai/student-hints（见 frontend/src/api/student-tutor.ts，
 * 后端实现见 backend/app/api/v1/endpoints/ai_generation.py 的
 * create_student_hint + backend/app/services/tutor/）。
 *
 * 两种挂载方式：
 * 1. 作为侧栏组件嵌入 course/challenge/detail.vue：challengeId/challengeName/
 *    evalError 由父页面通过 props 传入（父页面拿到真实 taskId、真实评测报错）。
 * 2. 作为独立路由 /student/ai-hint-test/:challengeId 直接访问（联调测试用）：
 *    从 route.params.challengeId 兜底取值，evalError 通过页面内输入框手填
 *    （因为没有父页面提供真实评测上下文）。
 */
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { requestStudentHint, type HintLevel } from '@/api/student-tutor'

interface Props {
  challengeId?: string
  challengeName?: string
  evalError?: string | null
  initialHintLevel?: HintLevel
  maxHintsPerChallenge?: number
}

const props = withDefaults(defineProps<Props>(), {
  challengeId: '',
  challengeName: '示例关卡：数据清洗与聚合',
  evalError: null,
  initialHintLevel: 1,
  maxHintsPerChallenge: 5,
})

const route = useRoute()

// props.challengeId 优先（嵌入模式）；独立路由模式下从 route.params 兜底取值。
const effectiveChallengeId = computed(() => {
  if (props.challengeId) return props.challengeId
  const fromRoute = route.params.challengeId
  return Array.isArray(fromRoute) ? fromRoute[0] : fromRoute || ''
})

const question = ref('')
// 独立路由模式下评测报错没有页面上下文自动填充，允许学生/测试者手动输入；
// 嵌入模式下 props.evalError 优先。
const evalErrorInput = ref(props.evalError || '')
const effectiveEvalError = computed(() => props.evalError ?? (evalErrorInput.value || null))

const hintLevel = ref<HintLevel>(props.initialHintLevel)
const replyMessage = ref('')
const requestError = ref('')
const loading = ref(false)
const usedHints = ref(0)

const remainingHints = ref(props.maxHintsPerChallenge)

async function handleAskAI() {
  if (loading.value || remainingHints.value <= 0) return
  if (!effectiveChallengeId.value) {
    requestError.value = '缺少关卡 ID，无法请求 AI 辅导'
    return
  }
  loading.value = true
  replyMessage.value = ''
  requestError.value = ''
  try {
    const res = await requestStudentHint({
      challenge_id: effectiveChallengeId.value,
      question: question.value || '为什么我的评测失败？',
      eval_error: effectiveEvalError.value,
      hint_level: hintLevel.value,
    })
    replyMessage.value = res.message
    hintLevel.value = res.hint_level
    usedHints.value += 1
    remainingHints.value = Math.max(0, props.maxHintsPerChallenge - usedHints.value)
    // 连续失败多次后升级到第三层提示，具体升级策略由后端/教师端配置决定，
    // 这里仅做最简单的前端展示态推进，真实策略以后端返回的 hint_level 为准。
    if (hintLevel.value < 3) {
      hintLevel.value = (hintLevel.value + (usedHints.value > 1 ? 1 : 0)) as HintLevel
    }
  } catch (err: any) {
    const backendDetail = err?.response?.data?.detail
    requestError.value =
      (typeof backendDetail === 'string' ? backendDetail : backendDetail?.message) ||
      err?.message ||
      'AI 助教暂时无法响应，请稍后再试。'
    console.error('[HintPanel] requestStudentHint failed:', err)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.hint-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 320px;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.hint-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint-panel__title {
  font-weight: 600;
  font-size: 15px;
  color: #1f2937;
}

.hint-panel__level-badge {
  font-size: 12px;
  color: #2563eb;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 12px;
}

.hint-panel__section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hint-panel__label {
  font-size: 12px;
  color: #6b7280;
}

.hint-panel__task {
  font-size: 13px;
  color: #111827;
}

.hint-panel__task-id {
  font-size: 11px;
  color: #9ca3af;
}

.hint-panel__question-input {
  resize: none;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 8px;
  font-size: 13px;
}

.hint-panel__eval-error {
  background: #fef2f2;
  color: #b91c1c;
  padding: 8px;
  border-radius: 6px;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.hint-panel__reply {
  background: #f9fafb;
  border-radius: 6px;
  padding: 10px;
  font-size: 13px;
  color: #111827;
  min-height: 40px;
  line-height: 1.5;
}

.hint-panel__reply--placeholder {
  color: #9ca3af;
}

.hint-panel__reply--loading {
  color: #6b7280;
  font-style: italic;
}

.hint-panel__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint-panel__quota {
  font-size: 12px;
  color: #9ca3af;
}

.hint-panel__ask-btn {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
}

.hint-panel__ask-btn:disabled {
  background: #93c5fd;
  cursor: not-allowed;
}
</style>
