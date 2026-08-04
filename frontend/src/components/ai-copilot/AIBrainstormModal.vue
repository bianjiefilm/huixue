<template>
  <Transition name="fade">
    <div v-if="visible" class="brainstorm-overlay" @click.self="handleClose">
      <div class="brainstorm-modal copilot-theme">
        <!-- 头部 -->
        <div class="modal-header">
          <div class="header-title">
            <BulbOutlined class="title-icon" />
            <span>AI 头脑风暴</span>
          </div>
          <button class="close-btn" @click="handleClose">
            <CloseOutlined />
          </button>
        </div>

        <!-- 内容区域 -->
        <div class="modal-content">
          <!-- 输入区 -->
          <div class="input-section">
            <label>💡 描述你的想法或问题</label>
            <textarea
              v-model="userPrompt"
              placeholder="例如：帮我规划一下数据分析项目的后续步骤..."
              rows="4"
              :disabled="loading"
            ></textarea>
          </div>

          <!-- 项目上下文 -->
          <div v-if="projectContext.length > 0" class="context-section">
            <label>📁 当前项目上下文</label>
            <div class="context-tags">
              <span 
                v-for="(project, index) in projectContext" 
                :key="index"
                class="context-tag"
              >
                {{ project }}
              </span>
            </div>
          </div>

          <!-- 生成按钮 -->
          <button 
            class="generate-btn" 
            :disabled="!userPrompt.trim() || loading"
            @click="handleGenerate"
          >
            <LoadingOutlined v-if="loading" spin />
            <ThunderboltOutlined v-else />
            <span>{{ loading ? '正在思考...' : '开始头脑风暴' }}</span>
          </button>

          <!-- 结果区域 -->
          <div v-if="result" class="result-section">
            <div class="result-header">
              <RocketOutlined />
              <span>AI 创意</span>
            </div>
            
            <!-- 原始内容 -->
            <div v-if="result.content" class="result-content">
              <div v-html="formatContent(result.content)"></div>
            </div>

            <!-- 结构化创意列表 -->
            <div v-if="result.ideas && result.ideas.length > 0" class="ideas-list">
              <div 
                v-for="(idea, index) in result.ideas" 
                :key="index"
                class="idea-card"
                @click="selectIdea(idea)"
              >
                <div class="idea-number">{{ index + 1 }}</div>
                <div class="idea-text">{{ idea.idea || idea }}</div>
                <PlusOutlined class="idea-add" />
              </div>
            </div>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="error-message">
            <WarningOutlined />
            <span>{{ error }}</span>
          </div>
        </div>

        <!-- 底部操作 -->
        <div class="modal-footer">
          <button class="secondary-btn" @click="handleClose">关闭</button>
          <button 
            v-if="result" 
            class="primary-btn"
            @click="applyAllIdeas"
          >
            <CheckOutlined />
            应用创意
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  BulbOutlined,
  CloseOutlined,
  LoadingOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  PlusOutlined,
  WarningOutlined,
  CheckOutlined
} from '@ant-design/icons-vue'
import { aiBrainstorm, type BrainstormResponse } from '@/api/ai-features'

interface Props {
  visible: boolean
  projectContext?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  visible: false,
  projectContext: () => []
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select-idea', idea: string): void
  (e: 'apply-ideas', ideas: string[]): void
}>()

// 状态
const userPrompt = ref('')
const loading = ref(false)
const result = ref<BrainstormResponse | null>(null)
const error = ref<string | null>(null)

// 处理关闭
function handleClose() {
  emit('close')
}

// 处理生成
async function handleGenerate() {
  if (!userPrompt.value.trim()) return
  
  loading.value = true
  error.value = null
  result.value = null
  
  try {
    const response = await aiBrainstorm({
      user_prompt: userPrompt.value,
      project_context: props.projectContext
    })
    
    if (response.success) {
      result.value = response
    } else {
      throw new Error(response.error || '生成失败')
    }
  } catch (e: any) {
    error.value = e.message || 'AI 头脑风暴失败，请稍后重试'
    console.error('Brainstorm error:', e)
  } finally {
    loading.value = false
  }
}

// 选择单个创意
function selectIdea(idea: any) {
  const ideaText = typeof idea === 'string' ? idea : idea.idea
  emit('select-idea', ideaText)
}

// 应用所有创意
function applyAllIdeas() {
  if (!result.value?.ideas) return
  const ideas = result.value.ideas.map(i => typeof i === 'string' ? i : i.idea)
  emit('apply-ideas', ideas)
  handleClose()
}

// 格式化内容
function formatContent(content: string): string {
  return content
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(\d+)\./g, '<span class="list-number">$1.</span>')
}

// 重置状态
watch(() => props.visible, (val) => {
  if (val) {
    // 打开时重置
    error.value = null
  }
})
</script>

<style scoped>
.brainstorm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--hx-z-modal);
  backdrop-filter: blur(4px);
}

.brainstorm-modal {
  width: 560px;
  max-width: 90vw;
  max-height: 85vh;
  background: var(--copilot-bg-secondary, #ffffff);
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

/* 头部 */
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid var(--copilot-border-default, #e8e8e8);
  background: linear-gradient(135deg, rgba(0, 198, 255, 0.1), transparent);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 600;
  color: var(--copilot-text-primary, #e0e0e0);
}

.title-icon {
  color: var(--copilot-accent-yellow, #facc15);
  font-size: 24px;
}

.close-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--copilot-text-secondary, #a0a0a0);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.1));
  color: var(--copilot-text-primary, #e0e0e0);
}

/* 内容区域 */
.modal-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

.input-section {
  margin-bottom: 20px;
}

.input-section label,
.context-section label {
  display: block;
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 500;
  color: var(--copilot-text-primary, #e0e0e0);
}

.input-section textarea {
  width: 100%;
  padding: 14px 16px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 10px;
  background: var(--copilot-bg-tertiary, #fafafa);
  color: var(--copilot-text-primary, #e0e0e0);
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  transition: border-color 0.2s;
}

.input-section textarea:focus {
  outline: none;
  border-color: var(--copilot-brand-primary, #00c6ff);
}

.input-section textarea:disabled {
  opacity: 0.6;
}

/* 项目上下文 */
.context-section {
  margin-bottom: 20px;
}

.context-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.context-tag {
  padding: 6px 12px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 20px;
  font-size: 13px;
  color: var(--copilot-text-secondary, #a0a0a0);
}

/* 生成按钮 */
.generate-btn {
  width: 100%;
  padding: 14px 24px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--copilot-brand-primary, #00c6ff), var(--copilot-accent-purple, #a855f7));
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 198, 255, 0.3);
}

.generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 结果区域 */
.result-section {
  margin-top: 24px;
  padding: 20px;
  background: var(--copilot-bg-tertiary, #fafafa);
  border-radius: 12px;
  border: 1px solid var(--copilot-border-highlight, rgba(0, 198, 255, 0.3));
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--copilot-brand-primary, #00c6ff);
}

.result-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--copilot-text-primary, #e0e0e0);
}

.result-content :deep(code) {
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.1));
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
}

.result-content :deep(strong) {
  color: var(--copilot-accent-yellow, #facc15);
}

.result-content :deep(.list-number) {
  color: var(--copilot-brand-primary, #00c6ff);
  font-weight: 600;
}

/* 创意列表 */
.ideas-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.idea-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--copilot-bg-secondary, #ffffff);
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.idea-card:hover {
  border-color: var(--copilot-brand-primary, #00c6ff);
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.05));
}

.idea-number {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--copilot-brand-primary, #00c6ff), var(--copilot-accent-purple, #a855f7));
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.idea-text {
  flex: 1;
  font-size: 14px;
  color: var(--copilot-text-primary, #e0e0e0);
}

.idea-add {
  color: var(--copilot-text-muted, #606060);
  transition: color 0.2s;
}

.idea-card:hover .idea-add {
  color: var(--copilot-brand-primary, #00c6ff);
}

/* 错误提示 */
.error-message {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--copilot-semantic-error, #ef4444);
  border-radius: 8px;
  color: var(--copilot-semantic-error, #ef4444);
  font-size: 14px;
}

/* 底部 */
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--copilot-border-default, #e8e8e8);
}

.secondary-btn {
  padding: 10px 20px;
  border: 1px solid var(--copilot-border-default, #e8e8e8);
  border-radius: 8px;
  background: transparent;
  color: var(--copilot-text-secondary, #a0a0a0);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.secondary-btn:hover {
  background: var(--copilot-bg-hover, rgba(255, 255, 255, 0.1));
  color: var(--copilot-text-primary, #e0e0e0);
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
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.primary-btn:hover {
  background: var(--copilot-brand-hover, #00e1ff);
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active .brainstorm-modal {
  animation: modal-in 0.3s ease;
}

.fade-leave-active .brainstorm-modal {
  animation: modal-out 0.3s ease;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes modal-out {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.95) translateY(20px);
  }
}
</style>

