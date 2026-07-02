<template>
  <a-modal
    :open="open"
    title="确认切换实验环境"
    :closable="false"
    :maskClosable="false"
    width="480px"
    class="switch-environment-dialog"
    @cancel="handleCancel"
  >
    <div class="switch-content">
      <div class="switch-icon">
        <QuestionCircleOutlined style="color: #faad14; font-size: 48px;" />
      </div>
      
      <div class="switch-message">
        <h3>确定要切换到新的实验环境吗？</h3>
        
        <div class="environment-info">
          <div class="current-env">
            <h4>当前环境</h4>
            <p><strong>{{ currentEnvironment?.practiceName }}</strong></p>
            <p class="env-detail">{{ getEnvironmentTypeName(currentEnvironment?.environmentType) }}</p>
          </div>
          
          <div class="arrow-divider">
            <ArrowRightOutlined style="color: #bfbfbf; font-size: 16px;" />
          </div>
          
          <div class="target-env">
            <h4>目标环境</h4>
            <p><strong>{{ targetPracticeName }}</strong></p>
            <p class="env-detail">{{ getEnvironmentTypeName(targetEnvironmentType) }}</p>
          </div>
        </div>
        
        <div class="switch-warning">
          <ExclamationCircleOutlined style="color: #ff4d4f; margin-right: 8px;" />
          <div>
            <p><strong>注意：</strong></p>
            <ul>
              <li>当前实验环境将被停止，所有未保存的数据将丢失</li>
              <li>停止过程可能需要几秒钟时间</li>
              <li>新环境启动后将自动打开</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <a-button @click="handleCancel" :disabled="processing">
          取消
        </a-button>
        <a-button 
          type="primary" 
          danger 
          @click="handleConfirm" 
          :loading="processing"
        >
          <SwapOutlined v-if="!processing" />
          {{ processing ? '正在切换...' : '确认切换' }}
        </a-button>
      </div>
    </template>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  QuestionCircleOutlined, 
  ArrowRightOutlined, 
  ExclamationCircleOutlined,
  SwapOutlined 
} from '@ant-design/icons-vue';
import type { ActiveEnvironment } from '@/api/practice';

interface Props {
  open: boolean;
  currentEnvironment: ActiveEnvironment | null;
  targetPracticeName: string;
  targetEnvironmentType: string;
  processing?: boolean;
}

interface Emits {
  (e: 'update:open', value: boolean): void;
  (e: 'confirm'): void;
  (e: 'cancel'): void;
}

const props = withDefaults(defineProps<Props>(), {
  processing: false
});

const emit = defineEmits<Emits>();

// 移除computed visible

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

const handleConfirm = () => {
  emit('confirm');
};

const handleCancel = () => {
  emit('cancel');
  emit('update:open', false);
};
</script>

<style scoped>
.switch-environment-dialog {
  .switch-content {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 16px 0;
  }

  .switch-icon {
    flex-shrink: 0;
  }

  .switch-message {
    flex: 1;

    h3 {
      margin: 0 0 20px 0;
      font-size: 18px;
      font-weight: 600;
      color: #262626;
    }

    .environment-info {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 20px 0;
      padding: 16px;
      border: 1px solid #e8e8e8;
      border-radius: 8px;
      background: #fafafa;

      .current-env,
      .target-env {
        flex: 1;
        text-align: center;

        h4 {
          margin: 0 0 8px 0;
          font-size: 14px;
          color: #8c8c8c;
          font-weight: normal;
        }

        p {
          margin: 4px 0;
          color: #262626;

          &.env-detail {
            font-size: 12px;
            color: #8c8c8c;
          }
        }
      }

      .arrow-divider {
        flex-shrink: 0;
        display: flex;
        align-items: center;
      }
    }

    .switch-warning {
      margin-top: 20px;
      padding: 12px;
      background: #fff2f0;
      border: 1px solid #ffccc7;
      border-radius: 6px;
      display: flex;
      align-items: flex-start;
      font-size: 14px;

      p {
        margin: 0 0 8px 0;
        color: #ff4d4f;
        font-weight: 600;
      }

      ul {
        margin: 0;
        padding-left: 16px;
        color: #595959;

        li {
          margin: 4px 0;
          line-height: 1.4;
        }
      }
    }
  }

  .dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;

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