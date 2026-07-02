<template>
  <div class="ai-test-container">
    <div class="page-header">
      <h1>
        🤖 AI学习助手测试
      </h1>
      <p>测试豆包AI集成功能</p>
    </div>

    <div class="test-section">
      <h2>💬 AI对话测试</h2>
      <div class="chat-container">
        <div class="chat-messages">
          <div v-for="msg in chatMessages" :key="msg.id" class="message" :class="msg.role">
            <div class="message-content">{{ msg.content }}</div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
        <div class="chat-input">
          <a-input
            v-model:value="chatInput"
            placeholder="输入您的问题..."
            @pressEnter="sendChatMessage"
            :disabled="chatLoading"
          >
            <template #suffix>
              <a-button
                type="primary"
                :loading="chatLoading"
                @click="sendChatMessage"
                size="small"
              >
                发送
              </a-button>
            </template>
          </a-input>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>📚 概念解释测试</h2>
      <div class="concept-test">
        <a-input
          v-model:value="conceptInput"
          placeholder="输入要解释的概念..."
          style="margin-bottom: 10px"
        />
        <a-button
          type="primary"
          :loading="conceptLoading"
          @click="explainConcept"
        >
          解释概念
        </a-button>
        <div v-if="conceptResult" class="result-display">
          <h3>解释结果：</h3>
          <div class="result-content">{{ conceptResult }}</div>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>📊 额度信息</h2>
      <div class="quota-info">
        <a-button type="primary" @click="loadQuotaInfo" :loading="quotaLoading">
          查看额度
        </a-button>
        <div v-if="quotaData" class="quota-display">
          <p><strong>用户角色：</strong>{{ quotaData.user_role }}</p>
          <p><strong>月额度：</strong>{{ quotaData.monthly_quota }}</p>
          <p><strong>已使用：</strong>{{ quotaData.used_this_month }}</p>
          <p><strong>剩余：</strong>{{ quotaData.remaining }}</p>
          <p><strong>重置日期：</strong>{{ quotaData.reset_date }}</p>
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2>📝 试题生成测试</h2>
      <div class="question-test">
        <a-input
          v-model:value="knowledgePoint"
          placeholder="输入知识点..."
          style="margin-bottom: 10px"
        />
        <a-select v-model:value="questionType" placeholder="选择题型" style="margin-bottom: 10px">
          <a-select-option value="single_choice">单选题</a-select-option>
          <a-select-option value="multiple_choice">多选题</a-select-option>
          <a-select-option value="true_false">判断题</a-select-option>
        </a-select>
        <a-select v-model:value="difficulty" placeholder="选择难度" style="margin-bottom: 10px">
          <a-select-option value="easy">简单</a-select-option>
          <a-select-option value="medium">中等</a-select-option>
          <a-select-option value="hard">困难</a-select-option>
        </a-select>
        <a-button
          type="primary"
          :loading="questionLoading"
          @click="generateQuestions"
        >
          生成试题
        </a-button>
        <div v-if="questionResult" class="result-display">
          <h3>生成结果：</h3>
          <div class="result-content">{{ questionResult }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'

// API imports
import {
  chatWithAI,
  explainConcept as explainConceptApi,
  generateQuestions as generateQuestionsApi,
  getUserQuota
} from '@/api/ai'

const userStore = useUserStore()

const requireCurrentUserId = () => {
  const userId = userStore.userId
  if (!userId) {
    message.warning('请先登录后再使用 AI 功能')
    throw new Error('Missing current user id')
  }
  return userId
}

// Chat state
const chatMessages = ref([])
const chatInput = ref('')
const chatLoading = ref(false)

// Concept explanation state
const conceptInput = ref('')
const conceptResult = ref('')
const conceptLoading = ref(false)

// Quota state
const quotaData = ref(null)
const quotaLoading = ref(false)

// Question generation state
const knowledgePoint = ref('')
const questionType = ref('single_choice')
const difficulty = ref('medium')
const questionResult = ref('')
const questionLoading = ref(false)

// Chat functions
const sendChatMessage = async () => {
  if (!chatInput.value.trim()) return

  const messageText = chatInput.value.trim()
  chatInput.value = ''

  // Add user message
  chatMessages.value.push({
    id: Date.now(),
    role: 'user',
    content: messageText,
    time: new Date().toLocaleTimeString()
  })

  chatLoading.value = true

  try {
    const currentUserId = requireCurrentUserId()
    const response = await chatWithAI({
      message: messageText,
      user_id: currentUserId
    })

    if (response.code === '0000' && response.data) {
      chatMessages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: response.data.reply,
        time: new Date().toLocaleTimeString()
      })
    } else {
      throw new Error(response.message || '发送失败')
    }
  } catch (error) {
    console.error('Chat error:', error)
    message.error('发送消息失败：' + (error.message || '未知错误'))
    chatMessages.value.push({
      id: Date.now(),
      role: 'error',
      content: '消息发送失败，请重试',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    chatLoading.value = false
  }
}

// Concept explanation function
const explainConcept = async () => {
  if (!conceptInput.value.trim()) {
    message.warning('请输入要解释的概念')
    return
  }

  conceptLoading.value = true
  conceptResult.value = ''

  try {
    const currentUserId = requireCurrentUserId()
    const response = await explainConceptApi({
      concept: conceptInput.value.trim(),
      user_id: currentUserId
    })

    if (response.code === '0000' && response.data) {
      conceptResult.value = response.data.explanation
    } else {
      throw new Error(response.message || '解释失败')
    }
  } catch (error) {
    console.error('Concept explanation error:', error)
    message.error('概念解释失败：' + (error.message || '未知错误'))
    conceptResult.value = '解释失败，请重试'
  } finally {
    conceptLoading.value = false
  }
}

// Load quota info
const loadQuotaInfo = async () => {
  quotaLoading.value = true

  try {
    const response = await getUserQuota(requireCurrentUserId())

    if (response.code === '0000' && response.data) {
      quotaData.value = response.data
    } else {
      throw new Error(response.message || '获取额度失败')
    }
  } catch (error) {
    console.error('Quota load error:', error)
    message.error('获取额度信息失败：' + (error.message || '未知错误'))
  } finally {
    quotaLoading.value = false
  }
}

// Generate questions
const generateQuestions = async () => {
  if (!knowledgePoint.value.trim()) {
    message.warning('请输入知识点')
    return
  }

  questionLoading.value = true
  questionResult.value = ''

  try {
    const currentUserId = requireCurrentUserId()
    const response = await generateQuestionsApi({
      knowledge_point: knowledgePoint.value.trim(),
      question_type: questionType.value,
      difficulty: difficulty.value,
      count: 1,
      user_id: currentUserId
    })

    if (response.code === '0000' && response.data) {
      const questions = response.data.questions
      if (questions && questions.length > 0) {
        questionResult.value = `生成了 ${questions.length} 道试题\n\n${questions[0].content || '试题内容不可用'}`
      } else {
        questionResult.value = '没有生成试题，请检查权限或参数'
      }
    } else {
      throw new Error(response.message || '生成失败')
    }
  } catch (error) {
    console.error('Question generation error:', error)
    message.error('试题生成失败：' + (error.message || '未知错误'))
    questionResult.value = '生成失败，请重试'
  } finally {
    questionLoading.value = false
  }
}

onMounted(() => {
  loadQuotaInfo()
})
</script>

<style scoped>
.ai-test-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  color: #1890ff;
  margin-bottom: 10px;
}

.test-section {
  margin-bottom: 40px;
  padding: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
}

.test-section h2 {
  color: #333;
  margin-bottom: 20px;
  border-bottom: 2px solid #1890ff;
  padding-bottom: 5px;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 400px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.message {
  margin-bottom: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  max-width: 70%;
}

.message.user {
  background-color: #1890ff;
  color: white;
  align-self: flex-end;
  margin-left: auto;
}

.message.assistant {
  background-color: #f0f0f0;
  color: #333;
}

.message.error {
  background-color: #ff4d4f;
  color: white;
}

.message-time {
  font-size: 12px;
  opacity: 0.7;
  margin-top: 4px;
}

.chat-input {
  border-top: 1px solid #d9d9d9;
  padding: 10px;
}

.result-display {
  margin-top: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 4px;
  border-left: 4px solid #1890ff;
}

.result-display h3 {
  margin-top: 0;
  color: #1890ff;
}

.result-content {
  white-space: pre-wrap;
  line-height: 1.6;
}

.quota-display {
  margin-top: 15px;
  padding: 15px;
  background-color: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 4px;
}

.quota-display p {
  margin: 5px 0;
}
</style>
