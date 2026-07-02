<template>
  <a-modal
    :open="open"
    title="检测到活跃的实验环境"
    :closable="false"
    :maskClosable="false"
    width="520px"
    class="environment-conflict-dialog"
    @cancel="handleCancel"
  >
    <div class="conflict-content">
      <div class="conflict-icon">
        <ExclamationCircleOutlined style="color: #faad14; font-size: 48px;" />
      </div>
      
      <div class="conflict-message">
        <h3>您有一个正在运行的实验环境</h3>
        <p class="current-env-info">
          <strong>当前运行环境：</strong>{{ activeEnvironment?.practiceName }}
        </p>
        <p class="env-type">
          <strong>环境类型：</strong>{{ getEnvironmentTypeName(activeEnvironment?.environmentType) }}
        </p>
        <p class="start-time">
          <strong>启动时间：</strong>{{ formatTime(activeEnvironment?.startTime) }}
        </p>
        
        <div class="conflict-warning">
          <InfoCircleOutlined style="color: #1890ff; margin-right: 8px;" />
          系统限制每个用户只能同时运行一个实验环境
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <a-button @click="handleGoBack" class="go-back-btn">
          <ArrowLeftOutlined />
          返回该实验
        </a-button>
        <a-button type="primary" @click="handleSwitchEnvironment" :loading="switching">
          <SwapOutlined />
          进入本实验
        </a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  ExclamationCircleOutlined, 
  InfoCircleOutlined, 
  ArrowLeftOutlined, 
  SwapOutlined 
} from '@ant-design/icons-vue';
import type { ActiveEnvironment } from '@/api/practice';
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Props {
  open: boolean;
  activeEnvironment: ActiveEnvironment | null;
}

interface Emits {
  (e: 'update:open', value: boolean): void;
  (e: 'go-back', environment: ActiveEnvironment): void;
  (e: 'switch-environment', environment: ActiveEnvironment): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const switching = ref(false);

// 获取环境类型名称
const getEnvironmentTypeName = (type?: string) => {
  const typeMap: Record<string, string> = {
    'code': '编程环境',
    'desktop': '桌面环境',
    'terminal': '命令行环境',
    'python': 'Python环境',
    'java': 'Java环境',
    'nodejs': 'Node.js环境',
    'cpp': 'C++环境'
  };
  return typeMap[type || ''] || type || '未知类型';
};

// 格式化时间
const formatTime = (timeStr?: string) => {
  if (!timeStr) return '';
  try {
    const date = new Date(timeStr);
    return formatDistanceToNow(date, { 
      addSuffix: true, 
      locale: zhCN 
    });
  } catch (error) {
    return timeStr;
  }
};

// 处理取消
const handleCancel = () => {
  emit('update:open', false);
};

// 返回该实验
const handleGoBack = () => {
  if (props.activeEnvironment) {
    emit('go-back', props.activeEnvironment);
  }
  emit('update:open', false);
};

// 切换到本实验
const handleSwitchEnvironment = () => {
  if (props.activeEnvironment) {
    emit('switch-environment', props.activeEnvironment);
  }
};

// 重置切换状态
const resetSwitching = () => {
  switching.value = false;
};

defineExpose({
  resetSwitching
});
</script>

<style scoped>
.environment-conflict-dialog {
  .conflict-content {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px 0;
  }

  .conflict-icon {
    flex-shrink: 0;
  }

  .conflict-message {
    flex: 1;

    h3 {
      margin: 0 0 16px 0;
      font-size: 18px;
      font-weight: 600;
      color: #262626;
    }

    p {
      margin: 8px 0;
      color: #595959;
      line-height: 1.6;

      strong {
        color: #262626;
      }
    }

    .conflict-warning {
      margin-top: 16px;
      padding: 12px;
      background: #f6ffed;
      border: 1px solid #b7eb8f;
      border-radius: 6px;
      display: flex;
      align-items: center;
      font-size: 14px;
      color: #52c41a;
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: space-between;
    gap: 12px;

    .go-back-btn {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .ant-btn {
      display: flex;
      align-items: center;
      gap: 6px;
    }
  }
}

:deep(.ant-modal-header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
}

:deep(.ant-modal-body) {
  padding: 24px;
}

:deep(.ant-modal-footer) {
  border-top: 1px solid #f0f0f0;
  padding: 16px 24px;
}
</style>
