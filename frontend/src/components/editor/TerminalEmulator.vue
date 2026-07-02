<template>
  <div class="terminal-container">
    <div class="terminal-header">
      <div class="terminal-title">
        <code-outlined />
        <span>命令行终端</span>
      </div>
      <div class="terminal-actions">
        <a-button type="text" size="small" @click="$emit('reset')">
          <template #icon><ReloadOutlined /></template>
          重置命令行
        </a-button>
      </div>
    </div>
    <div class="terminal-content" ref="terminalContent">
      <div class="terminal-output">
        <div v-for="(line, index) in outputLines" :key="index" class="terminal-line">
          <pre v-html="formatOutput(line)"></pre>
        </div>
      </div>
      <div class="terminal-input-line">
        <span class="prompt">{{ prompt }}</span>
        <input
          ref="commandInput"
          type="text"
          class="command-input"
          v-model="currentCommand"
          @keydown.enter="executeCommand"
          @keydown.up="navigateHistory(-1)"
          @keydown.down="navigateHistory(1)"
          :disabled="executing"
          autocomplete="off"
          spellcheck="false"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, defineEmits } from 'vue';
import { CodeOutlined, ReloadOutlined } from '@ant-design/icons-vue';

// 定义组件属性
const props = defineProps({
  initialCommands: {
    type: Array as () => string[],
    default: () => []
  },
  initialOutput: {
    type: Array as () => string[],
    default: () => ['欢迎使用命令行终端']
  },
  prompt: {
    type: String,
    default: '$ '
  }
});

// 定义事件
const emit = defineEmits<{
  execute: [command: string]
  reset: []
}>()

// 状态
const outputLines = ref<string[]>([...props.initialOutput]);
const commandHistory = ref<string[]>([]);
const historyIndex = ref(-1);
const currentCommand = ref('');
const executing = ref(false);
const terminalContent = ref<HTMLElement | null>(null);
const commandInput = ref<HTMLInputElement | null>(null);

// 格式化输出，处理特殊字符和颜色
const formatOutput = (line: string): string => {
  // 处理颜色代码等终端格式
  return line
    .replace(/\x1b\[31m(.*?)\x1b\[0m/g, '<span class="red">$1</span>')
    .replace(/\x1b\[32m(.*?)\x1b\[0m/g, '<span class="green">$1</span>')
    .replace(/\x1b\[33m(.*?)\x1b\[0m/g, '<span class="yellow">$1</span>')
    .replace(/\x1b\[34m(.*?)\x1b\[0m/g, '<span class="blue">$1</span>')
    .replace(/\x1b\[1m(.*?)\x1b\[0m/g, '<span class="bold">$1</span>');
};

// 执行命令
const executeCommand = async () => {
  const command = currentCommand.value.trim();
  if (!command) return;

  executing.value = true;
  
  // 将命令添加到输出
  outputLines.value.push(`${props.prompt}${command}`);
  
  // 将命令添加到历史记录
  commandHistory.value.push(command);
  historyIndex.value = -1;
  currentCommand.value = '';

  // 执行命令，触发事件让父组件处理
  emit('execute', command);
  
  // 模拟命令处理延迟
  await new Promise(resolve => setTimeout(resolve, 100));
  
  executing.value = false;

  // 滚动到底部并聚焦输入框
  nextTick(() => {
    scrollToBottom();
    focusInput();
  });
};

// 添加输出行
const addOutputLine = (line: string) => {
  outputLines.value.push(line);
  nextTick(() => {
    scrollToBottom();
  });
};

// 添加多行输出
const addOutputLines = (lines: string[]) => {
  outputLines.value.push(...lines);
  nextTick(() => {
    scrollToBottom();
  });
};

// 滚动终端到底部
const scrollToBottom = () => {
  if (terminalContent.value) {
    terminalContent.value.scrollTop = terminalContent.value.scrollHeight;
  }
};

// 聚焦输入框
const focusInput = () => {
  if (commandInput.value) {
    commandInput.value.focus();
  }
};

// 导航命令历史
const navigateHistory = (direction: number) => {
  if (commandHistory.value.length === 0) return;
  
  // 向上：获取较早的命令
  if (direction < 0) {
    historyIndex.value = historyIndex.value < 0 
      ? commandHistory.value.length - 1 
      : Math.max(0, historyIndex.value - 1);
  } 
  // 向下：获取较新的命令
  else {
    historyIndex.value = historyIndex.value >= commandHistory.value.length - 1
      ? -1
      : historyIndex.value + 1;
  }
  
  currentCommand.value = historyIndex.value >= 0 
    ? commandHistory.value[historyIndex.value] 
    : '';
};

// 重置终端
const resetTerminal = () => {
  outputLines.value = [...props.initialOutput];
  currentCommand.value = '';
  emit('reset');
  focusInput();
};

// 初始化终端内容
const initializeTerminal = () => {
  // 如果有初始命令，依次执行它们
  if (props.initialCommands && props.initialCommands.length > 0) {
    props.initialCommands.forEach(cmd => {
      outputLines.value.push(`${props.prompt}${cmd}`);
    });
  }
};

// 生命周期钩子
onMounted(() => {
  initializeTerminal();
  focusInput();
});

// 暴露方法给父组件
defineExpose({
  addOutputLine,
  addOutputLines,
  resetTerminal,
  focusInput
});
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #000000;
  color: #ffffff;
  border-radius: 4px;
  overflow: hidden;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-bottom: 1px solid #333333;
}

.terminal-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #ddd;
}

.terminal-actions {
  display: flex;
  gap: 8px;
}

.terminal-content {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  line-height: 1.5;
}

.terminal-output {
  margin-bottom: 12px;
}

.terminal-line {
  white-space: pre-wrap;
  word-break: break-all;
}

.terminal-line pre {
  margin: 0;
  font-family: inherit;
}

.terminal-input-line {
  display: flex;
  align-items: center;
}

.prompt {
  color: #7fff00;
  margin-right: 4px;
}

.command-input {
  flex: 1;
  background-color: transparent;
  border: none;
  color: #ffffff;
  font-family: inherit;
  font-size: inherit;
  padding: 0;
  outline: none;
}

/* 命令输出颜色样式 */
:deep(.red) {
  color: #ff6666;
}

:deep(.green) {
  color: #7fff00;
}

:deep(.yellow) {
  color: #ffff00;
}

:deep(.blue) {
  color: #5f9bff;
}

:deep(.bold) {
  font-weight: bold;
}
</style> 