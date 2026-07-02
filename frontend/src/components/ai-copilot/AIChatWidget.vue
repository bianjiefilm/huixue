<template>
  <div class="ai-chat-widget" :class="{ 'ai-chat-widget--open': isOpen }">
    <!-- 切换按钮 -->
    <button 
      class="chat-toggle"
      :class="{ 'chat-toggle--open': isOpen }"
      @click="toggleChat"
    >
      <RobotOutlined v-if="!isOpen" class="toggle-icon" />
      <CloseOutlined v-else class="toggle-icon" />
      <span v-if="!isOpen" class="toggle-label">AI 助手</span>
    </button>

    <!-- 聊天窗口 -->
    <Transition name="chat-slide">
      <div v-if="isOpen" class="chat-window">
        <!-- 头部 -->
        <div class="chat-header">
          <div class="header-info">
            <div class="ai-avatar">
              <RobotOutlined />
            </div>
            <div class="header-text">
              <span class="ai-name">慧慧</span>
              <span class="ai-status" :class="{ 'ai-status--online': isAvailable }">
                {{ isAvailable ? '在线' : '离线' }}
              </span>
            </div>
          </div>
          <button class="header-action" @click="handleClear" title="清空聊天">
            <DeleteOutlined />
          </button>
        </div>

        <!-- 消息区域 -->
        <div class="chat-messages" ref="messagesRef">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-icon">
              <BulbOutlined />
            </div>
            <h4>你好！我是慧慧，您的AI学习助手</h4>
            <p>您可以问我关于平台功能、课程内容或学习建议的任何问题！</p>
            
            <div class="quick-actions">
              <button 
                v-for="action in quickActions" 
                :key="action"
                class="quick-action"
                @click="sendQuickAction(action)"
              >
                {{ action }}
              </button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div 
            v-for="message in messages" 
            :key="message.id"
            class="message"
            :class="[`message--${message.role}`]"
          >
            <div v-if="message.role === 'assistant'" class="message-avatar">
              <RobotOutlined />
            </div>
            <div class="message-content">
              <div class="message-text">{{ message.content }}</div>
              <div class="message-time">{{ formatTime(message.timestamp) }}</div>
            </div>
          </div>

          <!-- 输入中指示器 -->
          <div v-if="loading" class="message message--assistant">
            <div class="message-avatar">
              <RobotOutlined />
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <!-- 输入区域 -->
        <div class="chat-input">
          <input
            ref="inputRef"
            v-model="inputMessage"
            type="text"
            placeholder="输入消息..."
            :disabled="!isAvailable || loading"
            @keydown.enter="handleSend"
          />
          <button 
            class="send-button" 
            :disabled="!inputMessage.trim() || !isAvailable || loading"
            @click="handleSend"
          >
            <SendOutlined />
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { 
  RobotOutlined, 
  CloseOutlined, 
  DeleteOutlined, 
  BulbOutlined,
  SendOutlined 
} from '@ant-design/icons-vue'
import type { ChatMessage } from '@/stores/aiCopilot'

interface Props {
  messages: ChatMessage[]
  loading?: boolean
  isAvailable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  isAvailable: true
})

const emit = defineEmits<{
  (e: 'send', message: string): void
  (e: 'clear'): void
}>()

// 状态
const isOpen = ref(false)
const inputMessage = ref('')
const messagesRef = ref<HTMLDivElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)

// 快捷操作
const quickActions = [
  '如何查看学习进度？',
  '推荐我接下来学什么',
  '技能图谱怎么看？'
]

// 切换聊天窗口
const toggleChat = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  }
}

// 发送消息
const handleSend = () => {
  const message = inputMessage.value.trim()
  if (!message || props.loading) return
  
  emit('send', message)
  inputMessage.value = ''
}

// 快捷操作
const sendQuickAction = (action: string) => {
  emit('send', action)
}

// 清空聊天
const handleClear = () => {
  emit('clear')
}

// 格式化时间
const formatTime = (date: Date) => {
  return new Date(date).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 自动滚动到底部
watch(() => props.messages.length, () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
})
</script>

<style scoped>
.ai-chat-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: var(--copilot-z-chat);
}

/* 切换按钮 */
.chat-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: var(--copilot-gradient-primary);
  border: none;
  border-radius: var(--copilot-radius-full);
  color: white;
  font-size: var(--copilot-font-size-sm);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--copilot-shadow-lg), 0 0 30px rgba(0, 217, 255, 0.4);
  transition: all var(--copilot-transition-normal);
}

.chat-toggle:hover {
  transform: scale(1.05);
  box-shadow: var(--copilot-shadow-lg), 0 0 40px rgba(0, 217, 255, 0.6);
}

.chat-toggle--open {
  padding: 12px;
  border-radius: 50%;
}

.toggle-icon {
  font-size: 20px;
}

/* 聊天窗口 */
.chat-window {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 380px;
  height: 500px;
  background: var(--copilot-bg-secondary);
  border: 1px solid var(--copilot-border-accent);
  border-radius: var(--copilot-radius-xl);
  box-shadow: var(--copilot-shadow-lg), var(--copilot-shadow-glow-cyan);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 动画 */
.chat-slide-enter-active,
.chat-slide-leave-active {
  transition: all 0.3s ease;
}

.chat-slide-enter-from,
.chat-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 头部 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: var(--copilot-bg-primary);
  border-bottom: 1px solid var(--copilot-border-muted);
}

.header-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar {
  width: 40px;
  height: 40px;
  background: var(--copilot-gradient-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.ai-name {
  font-weight: 600;
  color: var(--copilot-text-primary);
}

.ai-status {
  font-size: var(--copilot-font-size-xs);
  color: var(--copilot-text-tertiary);
}

.ai-status--online {
  color: var(--copilot-accent-green);
}

.ai-status--online::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--copilot-accent-green);
  border-radius: 50%;
  margin-right: 4px;
}

.header-action {
  background: transparent;
  border: none;
  color: var(--copilot-text-tertiary);
  cursor: pointer;
  padding: 8px;
  border-radius: var(--copilot-radius-sm);
  transition: all var(--copilot-transition-fast);
}

.header-action:hover {
  background: var(--copilot-bg-tertiary);
  color: var(--copilot-text-primary);
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-message {
  text-align: center;
  padding: 24px 16px;
}

.welcome-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  background: var(--copilot-accent-cyan-dim);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--copilot-accent-cyan);
  font-size: 24px;
}

.welcome-message h4 {
  font-size: var(--copilot-font-size-md);
  color: var(--copilot-text-primary);
  margin: 0 0 8px;
}

.welcome-message p {
  font-size: var(--copilot-font-size-sm);
  color: var(--copilot-text-secondary);
  margin: 0 0 16px;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quick-action {
  padding: 10px 16px;
  background: var(--copilot-bg-tertiary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-sm);
  cursor: pointer;
  transition: all var(--copilot-transition-fast);
}

.quick-action:hover {
  border-color: var(--copilot-accent-cyan);
  background: var(--copilot-accent-cyan-dim);
}

/* 消息气泡 */
.message {
  display: flex;
  gap: 8px;
  max-width: 85%;
}

.message--user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message--assistant {
  align-self: flex-start;
}

.message-avatar {
  width: 28px;
  height: 28px;
  background: var(--copilot-gradient-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  flex-shrink: 0;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-text {
  padding: 10px 14px;
  border-radius: var(--copilot-radius-lg);
  font-size: var(--copilot-font-size-sm);
  line-height: 1.5;
}

.message--user .message-text {
  background: var(--copilot-accent-cyan);
  color: white;
  border-bottom-right-radius: 4px;
}

.message--assistant .message-text {
  background: var(--copilot-bg-tertiary);
  color: var(--copilot-text-primary);
  border-bottom-left-radius: 4px;
}

.message-time {
  font-size: 10px;
  color: var(--copilot-text-tertiary);
}

.message--user .message-time {
  text-align: right;
}

/* 输入中指示器 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: var(--copilot-bg-tertiary);
  border-radius: var(--copilot-radius-lg);
  border-bottom-left-radius: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--copilot-text-tertiary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.4;
  }
  30% {
    transform: translateY(-8px);
    opacity: 1;
  }
}

/* 输入区域 */
.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: var(--copilot-bg-primary);
  border-top: 1px solid var(--copilot-border-muted);
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  background: var(--copilot-bg-tertiary);
  border: 1px solid var(--copilot-border-default);
  border-radius: var(--copilot-radius-md);
  color: var(--copilot-text-primary);
  font-size: var(--copilot-font-size-sm);
  outline: none;
  transition: border-color var(--copilot-transition-fast);
}

.chat-input input::placeholder {
  color: var(--copilot-text-tertiary);
}

.chat-input input:focus {
  border-color: var(--copilot-accent-cyan);
}

.chat-input input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-button {
  width: 40px;
  height: 40px;
  background: var(--copilot-accent-cyan);
  border: none;
  border-radius: var(--copilot-radius-md);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--copilot-transition-fast);
}

.send-button:hover:not(:disabled) {
  background: var(--copilot-accent-cyan);
  box-shadow: var(--copilot-shadow-glow-cyan);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 响应式 */
@media (max-width: 480px) {
  .chat-window {
    width: calc(100vw - 48px);
    height: calc(100vh - 120px);
    bottom: 60px;
    right: 0;
  }
}
</style>
