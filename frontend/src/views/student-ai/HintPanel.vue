<template>
  <div class="hint-panel">
    <div class="hint-panel__header">
      <span class="hint-panel__title">AI 闯关助教</span>
      <span class="hint-panel__level-badge">第 {{ hintLevel }} 层提示</span>
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">当前任务</div>
      <div class="hint-panel__task">{{ challengeName }}</div>
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

    <div class="hint-panel__section" v-if="evalError">
      <div class="hint-panel__label">评测报错</div>
      <pre class="hint-panel__eval-error">{{ evalError }}</pre>
    </div>

    <div class="hint-panel__section">
      <div class="hint-panel__label">AI 提示</div>
      <div class="hint-panel__reply" v-if="!loading && replyMessage">
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
 * 当前先用假数据展示 UI（props 均有默认值），真实联调需要接入：
 * - POST /api/ai/student-hints（见 frontend/src/api/student-tutor.ts）
 * - 该 endpoint 尚未在 backend router 注册，路由接入需由负责 router 的
 *   agent 处理，本组件不改 router。
 */
import { ref } from 'vue'
import { requestStudentHint, type HintLevel } from '@/api/student-tutor'

interface Props {
  challengeId?: string
  challengeName?: string
  evalError?: string | null
  initialHintLevel?: HintLevel
  maxHintsPerChallenge?: number
}

const props = withDefaults(defineProps<Props>(), {
  challengeId: 'demo_challenge_001',
  challengeName: '示例关卡：数据清洗与聚合',
  evalError: null,
  initialHintLevel: 1,
  maxHintsPerChallenge: 5,
})

const question = ref('')
const hintLevel = ref<HintLevel>(props.initialHintLevel)
const replyMessage = ref('')
const loading = ref(false)
const usedHints = ref(0)

const remainingHints = ref(props.maxHintsPerChallenge)

async function handleAskAI() {
  if (loading.value || remainingHints.value <= 0) return
  loading.value = true
  replyMessage.value = ''
  try {
    const res = await requestStudentHint({
      challenge_id: props.challengeId,
      question: question.value || '为什么我的评测失败？',
      eval_error: props.evalError,
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
  } catch (err) {
    replyMessage.value = 'AI 助教暂时无法响应，请稍后再试。'
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
