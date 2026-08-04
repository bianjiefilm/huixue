<template>
  <Transition name="slide-right">
    <div v-if="store.isOpen" class="code-assistant-panel copilot-theme">
      <!-- 头部 -->
      <div class="panel-header">
        <div class="header-title">
          <RobotOutlined class="title-icon" />
          <span>AI 代码助手</span>
        </div>
        <div class="header-actions">
          <button class="action-btn" @click="clearMessages" title="清空">
            <DeleteOutlined />
          </button>
          <button class="action-btn" @click="store.close" title="关闭">
            <CloseOutlined />
          </button>
        </div>
      </div>

      <!-- 选项卡 -->
      <div class="panel-tabs">
        <button 
          :class="['tab-btn', { active: store.activeTab === 'explanation' }]"
          @click="store.activeTab = 'explanation'"
        >
          <BookOutlined /> 代码解释
        </button>
        <button 
          :class="['tab-btn', { active: store.activeTab === 'suggestion' }]"
          @click="store.activeTab = 'suggestion'"
        >
          <BulbOutlined /> 优化建议
        </button>
        <button 
          :class="['tab-btn', { active: store.activeTab === 'diagnosis' }]"
          @click="store.activeTab = 'diagnosis'"
        >
          <BugOutlined /> 错误诊断
        </button>
      </div>

      <!-- 内容区域 -->
      <div class="panel-content">
        <!-- 解释模式 -->
        <div v-if="store.activeTab === 'explanation'" class="tab-content">
          <div class="input-section">
            <label>请输入要解释的代码：</label>
            <textarea 
              v-model="explanationCode" 
              placeholder="粘贴或输入代码..."
              rows="6"
            ></textarea>
            <div class="input-options">
              <select v-model="explanationStyle">
                <option value="详细">详细解释</option>
                <option value="简洁">简洁解释</option>
                <option value="ELI5">通俗易懂</option>
              </select>
              <button 
                class="primary-btn" 
                :disabled="!explanationCode.trim() || store.loading.explanation"
                @click="handleExplain"
              >
                <LoadingOutlined v-if="store.loading.explanation" spin />
                <span v-else>解释代码</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 建议模式 -->
        <div v-if="store.activeTab === 'suggestion'" class="tab-content">
          <div class="input-section">
            <label>当前代码：</label>
            <textarea 
              v-model="suggestionCode" 
              placeholder="粘贴你的代码..."
              rows="5"
            ></textarea>
            <label>任务目标：</label>
            <textarea 
              v-model="suggestionObjective" 
              placeholder="描述这段代码要完成的任务..."
              rows="2"
            ></textarea>
            <button 
              class="primary-btn" 
              :disabled="!suggestionCode.trim() || !suggestionObjective.trim() || store.loading.suggestion"
              @click="handleSuggest"
            >
              <LoadingOutlined v-if="store.loading.suggestion" spin />
              <span v-else>获取建议</span>
            </button>
          </div>
        </div>

        <!-- 诊断模式 -->
        <div v-if="store.activeTab === 'diagnosis'" class="tab-content">
          <div class="input-section">
            <label>失败的代码：</label>
            <textarea 
              v-model="diagnosisCode" 
              placeholder="粘贴失败的代码..."
              rows="4"
            ></textarea>
            <label>错误日志：</label>
            <textarea 
              v-model="diagnosisError" 
              placeholder="粘贴错误信息..."
              rows="2"
            ></textarea>
            <div class="input-row">
              <div class="input-col">
                <label>测试输入：</label>
                <input v-model="diagnosisInput" placeholder="测试用例输入" />
              </div>
              <div class="input-col">
                <label>期望输出：</label>
                <input v-model="diagnosisExpected" placeholder="期望的输出" />
              </div>
            </div>
            <label>任务目标：</label>
            <input v-model="diagnosisObjective" placeholder="任务描述" />
            <button 
              class="primary-btn" 
              :disabled="!diagnosisCode.trim() || !diagnosisError.trim() || store.loading.diagnosis"
              @click="handleDiagnose"
            >
              <LoadingOutlined v-if="store.loading.diagnosis" spin />
              <span v-else>诊断错误</span>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="messages-section" ref="messagesRef">
          <div v-if="store.messages.length === 0" class="empty-messages">
            <RobotOutlined class="empty-icon" />
            <p>选择上方的功能，开始使用 AI 代码助手</p>
          </div>
          <div 
            v-for="message in filteredMessages" 
            :key="message.id"
            :class="['message', `message--${message.type}`]"
          >
            <div class="message-header">
              <span class="message-type">
                <BookOutlined v-if="message.type === 'explanation'" />
                <BulbOutlined v-else-if="message.type === 'suggestion'" />
                <BugOutlined v-else-if="message.type === 'diagnosis'" />
                <WarningOutlined v-else />
                {{ getTypeLabel(message.type) }}
              </span>
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
            </div>
            <div v-if="message.loading" class="message-loading">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
            <div v-else class="message-content" v-html="formatContent(message.content)"></div>
            <div v-if="message.codeSnippet" class="message-code">
              <code>{{ message.codeSnippet }}...</code>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { 
  RobotOutlined, 
  CloseOutlined, 
  DeleteOutlined,
  BookOutlined,
  BulbOutlined,
  BugOutlined,
  WarningOutlined,
  LoadingOutlined
} from '@ant-design/icons-vue'
import { useCodeAssistantStore } from '@/stores/codeAssistant'

const store = useCodeAssistantStore()

// 解释模式
const explanationCode = ref('')
const explanationStyle = ref<'简洁' | '详细' | 'ELI5'>('详细')

// 建议模式
const suggestionCode = ref('')
const suggestionObjective = ref('')

// 诊断模式
const diagnosisCode = ref('')
const diagnosisError = ref('')
const diagnosisInput = ref('')
const diagnosisExpected = ref('')
const diagnosisObjective = ref('')

const messagesRef = ref<HTMLDivElement | null>(null)

// 过滤当前 tab 的消息
const filteredMessages = computed(() => {
  return store.messages.filter(m => 
    m.type === store.activeTab || m.type === 'error'
  ).slice(-10) // 只显示最近10条
})

// 处理代码解释
async function handleExplain() {
  if (!explanationCode.value.trim()) return
  await store.fetchExplanation(explanationCode.value, explanationStyle.value)
  scrollToBottom()
}

// 处理代码建议
async function handleSuggest() {
  if (!suggestionCode.value.trim() || !suggestionObjective.value.trim()) return
  await store.fetchSuggestion(suggestionCode.value, suggestionObjective.value)
  scrollToBottom()
}

// 处理错误诊断
async function handleDiagnose() {
  if (!diagnosisCode.value.trim() || !diagnosisError.value.trim()) return
  await store.fetchDiagnosis(
    diagnosisCode.value,
    diagnosisError.value,
    diagnosisInput.value || '无',
    diagnosisExpected.value || '无',
    diagnosisObjective.value || '完成任务'
  )
  scrollToBottom()
}

// 清空消息
function clearMessages() {
  store.clearMessages()
}

// 滚动到底部
function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

// 获取类型标签
function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    explanation: '代码解释',
    suggestion: '优化建议',
    diagnosis: '错误诊断',
    error: '错误'
  }
  return labels[type] || type
}

// 格式化时间
function formatTime(timestamp: Date): string {
  return new Date(timestamp).toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 格式化内容（支持简单的 Markdown）
function formatContent(content: string): string {
  return content
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
}

// 监听消息变化，自动滚动
watch(() => store.messages.length, () => {
  scrollToBottom()
})
</script>

<style scoped>
.code-assistant-panel {
  position: fixed;
  right: 0;
  top: 0;
  width: 420px;
  height: 100vh;
  background: var(--copilot-bg-secondary, #ffffff);
  border-left: 1px solid var(--copilot-border-default, #e8e8e8);
  display: flex;
  flex-direction: column;
  z-index: var(--hx-z-ai-float);
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
}

/* 头部 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--copilot-border-default, #e8e8e8);
  background: var(--copilot-bg-tertiary, #fafafa);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--copilot-text-primary, #e0e0e0);
}

.title-icon {
  color: var(--copilot-brand-primary, #00c6ff);
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--copilot-text-secondary, #a0a0a0);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.1));
  color: var(--copilot-text-primary, #e0e0e0);
}

/* 选项卡 */
.panel-tabs {
  display: flex;
  border-bottom: 1px solid var(--copilot-border-default, #e8e8e8);
  padding: 0 12px;
}

.tab-btn {
  flex: 1;
  padding: 12px 8px;
  border: none;
  background: transparent;
  color: var(--copilot-text-secondary, #a0a0a0);
  font-size: 13px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--copilot-text-primary, #e0e0e0);
}

.tab-btn.active {
  color: var(--copilot-brand-primary, #00c6ff);
  border-bottom-color: var(--copilot-brand-primary, #00c6ff);
}

/* 内容区域 */
.panel-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.tab-content {
  padding: 16px;
}

.input-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-section label {
  font-size: 13px;
  color: var(--copilot-text-secondary, #a0a0a0);
}

.input-section textarea,
.input-section input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 8px;
  background: var(--copilot-bg-tertiary, #fafafa);
  color: var(--copilot-text-primary, #e0e0e0);
  font-family: 'Fira Code', 'Monaco', monospace;
  font-size: 13px;
  resize: vertical;
}

.input-section textarea:focus,
.input-section input:focus {
  outline: none;
  border-color: var(--copilot-brand-primary, #00c6ff);
}

.input-options {
  display: flex;
  gap: 12px;
  align-items: center;
}

.input-options select {
  padding: 8px 12px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 6px;
  background: var(--copilot-bg-tertiary, #fafafa);
  color: var(--copilot-text-primary, #e0e0e0);
  font-size: 13px;
}

.input-row {
  display: flex;
  gap: 12px;
}

.input-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.primary-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: var(--copilot-brand-primary, #00c6ff);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.primary-btn:hover:not(:disabled) {
  background: var(--copilot-brand-hover, #00e1ff);
}

.primary-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 消息区域 */
.messages-section {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  border-top: 1px solid var(--copilot-border-default, #e8e8e8);
}

.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--copilot-text-muted, #606060);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.message {
  padding: 14px;
  border-radius: 10px;
  margin-bottom: 12px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border: 1px solid var(--copilot-border-default, #e8e8e8);
}

.message--error {
  border-color: var(--copilot-semantic-error, #ef4444);
  background: rgba(239, 68, 68, 0.1);
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
}

.message-type {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--copilot-brand-primary, #00c6ff);
  font-weight: 500;
}

.message-time {
  color: var(--copilot-text-muted, #606060);
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  color: var(--copilot-text-primary, #e0e0e0);
}

.message-content :deep(code) {
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.1));
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
}

.message-content :deep(strong) {
  color: var(--copilot-brand-primary, #00c6ff);
}

.message-code {
  margin-top: 10px;
  padding: 8px 10px;
  background: var(--copilot-bg-primary, #f5f5f5);
  border-radius: 6px;
  font-size: 12px;
  color: var(--copilot-text-muted, #606060);
}

.message-loading {
  padding: 10px 0;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--copilot-brand-primary, #00c6ff);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

/* 滑动动画 */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>

