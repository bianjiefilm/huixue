<template>
  <div class="text-explainer">
    <!-- 选中文本的上下文菜单 -->
    <div 
      v-if="showContextMenu"
      :style="menuPosition"
      class="context-menu"
      ref="contextMenu"
    >
      <div class="menu-item" @click="copyText">
        <i class="icon-copy"></i>
        复制
      </div>
      <div class="menu-item" @click="highlightText">
        <i class="icon-highlight"></i>
        高亮
      </div>
      <div class="menu-item primary" @click="explainText">
        <i class="icon-explain"></i>
        帮我讲讲这段
      </div>
    </div>

    <!-- 解释结果弹窗 -->
    <div v-if="showExplanationModal" class="modal-overlay" @click="closeModal">
      <div class="explanation-modal" @click.stop>
        <div class="modal-header">
          <h3>文本解释</h3>
          <button class="close-btn" @click="closeModal">×</button>
        </div>
        
        <div class="modal-content">
          <!-- 原文显示 -->
          <div class="original-text">
            <h4>原文</h4>
            <div class="text-content">{{ selectedText }}</div>
          </div>

          <!-- 难度选择 -->
          <div class="difficulty-selector">
            <label>解释难度：</label>
            <select v-model="explainLevel" @change="requestExplanation">
              <option value="beginner">初学者</option>
              <option value="intermediate">中等水平</option>
              <option value="advanced">高级</option>
            </select>
          </div>

          <!-- 解释内容 -->
          <div v-if="explanation" class="explanation-content">
            <div class="explanation-section">
              <h4>核心解释</h4>
              <div class="explanation-text">{{ explanation.explanation }}</div>
            </div>

            <div class="explanation-section">
              <h4>关键要点</h4>
              <ul class="key-points">
                <li v-for="point in explanation.key_points" :key="point">
                  {{ point }}
                </li>
              </ul>
            </div>

            <div class="explanation-section" v-if="explanation.examples.length > 0">
              <h4>实例说明</h4>
              <div class="examples">
                <div v-for="example in explanation.examples" :key="example" class="example">
                  {{ example }}
                </div>
              </div>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-else-if="loading" class="loading">
            <div class="spinner"></div>
            正在生成解释...
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn secondary" @click="closeModal">关闭</button>
          <button class="btn primary" @click="copyExplanation">复制解释</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'

export default {
  name: 'TextExplainer',
  setup() {
    const showContextMenu = ref(false)
    const showExplanationModal = ref(false)
    const menuPosition = ref({ top: '0px', left: '0px' })
    const selectedText = ref('')
    const explainLevel = ref('beginner')
    const explanation = ref(null)
    const loading = ref(false)

    // 处理文本选择
    const handleTextSelection = (event) => {
      const selection = window.getSelection()
      const text = selection.toString().trim()

      if (text.length > 0) {
        selectedText.value = text
        showContextMenu.value = true
        
        // 设置菜单位置
        const rect = selection.getRangeAt(0).getBoundingClientRect()
        menuPosition.value = {
          position: 'fixed',
          top: `${rect.bottom + 5}px`,
          left: `${rect.left}px`,
          zIndex: 1000
        }
      } else {
        showContextMenu.value = false
      }
    }

    // 点击其他地方关闭菜单
    const handleClickOutside = (event) => {
      if (showContextMenu.value) {
        showContextMenu.value = false
      }
    }

    // 复制文本
    const copyText = () => {
      navigator.clipboard.writeText(selectedText.value)
      showContextMenu.value = false
      // 可以添加提示消息
    }

    // 高亮文本
    const highlightText = () => {
      // 实现文本高亮逻辑
      const selection = window.getSelection()
      if (selection.rangeCount > 0) {
        const range = selection.getRangeAt(0)
        const span = document.createElement('span')
        span.className = 'highlighted-text'
        span.style.backgroundColor = '#ffeb3b'
        span.style.padding = '2px'
        
        try {
          range.surroundContents(span)
        } catch (e) {
          // 如果选择跨越多个元素，使用不同方法
          const contents = range.extractContents()
          span.appendChild(contents)
          range.insertNode(span)
        }
      }
      showContextMenu.value = false
    }

    // 解释文本
    const explainText = () => {
      showContextMenu.value = false
      showExplanationModal.value = true
      requestExplanation()
    }

    // 请求解释
    const requestExplanation = async () => {
      if (!selectedText.value.trim()) return

      loading.value = true
      explanation.value = null

      try {
        const response = await api.post('/v1/text-explain/explain', {
          text: selectedText.value,
          level: explainLevel.value,
          context: getTextContext() // 获取上下文
        })

        if (response.data.code === '0000') {
          explanation.value = response.data.data
        }
      } catch (error) {
        console.error('解释请求失败:', error)
        explanation.value = {
          explanation: '抱歉，解释生成失败。请稍后再试。',
          key_points: [],
          examples: []
        }
      } finally {
        loading.value = false
      }
    }

    // 获取文本上下文
    const getTextContext = () => {
      const selection = window.getSelection()
      if (selection.rangeCount === 0) return ''

      const range = selection.getRangeAt(0)
      const container = range.commonAncestorContainer
      const parentElement = container.nodeType === Node.TEXT_NODE 
        ? container.parentElement 
        : container

      // 获取父级元素的文本作为上下文
      return parentElement.textContent || ''
    }

    // 关闭弹窗
    const closeModal = () => {
      showExplanationModal.value = false
      explanation.value = null
    }

    // 复制解释内容
    const copyExplanation = () => {
      if (!explanation.value) return

      const content = `
原文：${selectedText.value}

解释：${explanation.value.explanation}

关键要点：
${explanation.value.key_points.map(point => `• ${point}`).join('\n')}

${explanation.value.examples.length > 0 ? '实例：\n' + explanation.value.examples.map(ex => `• ${ex}`).join('\n') : ''}
      `.trim()

      navigator.clipboard.writeText(content)
      // 可以添加提示消息
    }

    onMounted(() => {
      document.addEventListener('mouseup', handleTextSelection)
      document.addEventListener('click', handleClickOutside)
    })

    onUnmounted(() => {
      document.removeEventListener('mouseup', handleTextSelection)
      document.removeEventListener('click', handleClickOutside)
    })

    return {
      showContextMenu,
      showExplanationModal,
      menuPosition,
      selectedText,
      explainLevel,
      explanation,
      loading,
      copyText,
      highlightText,
      explainText,
      requestExplanation,
      closeModal,
      copyExplanation
    }
  }
}
</script>

<style scoped>
/* 上下文菜单样式 */
.context-menu {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid #e1e5e9;
  padding: 4px 0;
  min-width: 140px;
}

.menu-item {
  padding: 8px 16px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background-color: #f5f5f5;
}

.menu-item.primary {
  color: #1976d2;
  font-weight: 500;
}

.menu-item.primary:hover {
  background-color: #e3f2fd;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.explanation-modal {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e1e5e9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.close-btn:hover {
  background-color: #f5f5f5;
}

.modal-content {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.original-text {
  margin-bottom: 20px;
}

.original-text h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.text-content {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid #1976d2;
  font-style: italic;
}

.difficulty-selector {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.difficulty-selector label {
  font-size: 14px;
  color: #666;
}

.difficulty-selector select {
  padding: 6px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.explanation-section {
  margin-bottom: 20px;
}

.explanation-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
  font-weight: 600;
}

.explanation-text {
  font-size: 15px;
  line-height: 1.6;
  color: #444;
}

.key-points {
  margin: 0;
  padding-left: 20px;
}

.key-points li {
  margin-bottom: 6px;
  font-size: 14px;
  line-height: 1.5;
}

.examples .example {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  font-size: 14px;
  border-left: 3px solid #28a745;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: #666;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e0e0e0;
  border-top: 2px solid #1976d2;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.modal-footer {
  padding: 16px 24px;
  border-top: 1px solid #e1e5e9;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn.secondary {
  background: #f5f5f5;
  color: #666;
}

.btn.secondary:hover {
  background: #e0e0e0;
}

.btn.primary {
  background: #1976d2;
  color: white;
}

.btn.primary:hover {
  background: #1565c0;
}

/* 高亮文本样式 */
:deep(.highlighted-text) {
  background-color: #ffeb3b !important;
  padding: 2px !important;
  border-radius: 2px !important;
}

/* 图标样式 - 如果没有图标字体，可以用emoji或删除 */
.icon-copy::before { content: "📋"; }
.icon-highlight::before { content: "🌟"; }
.icon-explain::before { content: "💡"; }
</style>