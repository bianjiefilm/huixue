import { defineStore } from 'pinia';
import type { MessageInstance } from 'ant-design-vue/es/message/interface';
import type { ModalStaticFunctions } from 'ant-design-vue/es/modal/confirm';
import type { NotificationInstance } from 'ant-design-vue/es/notification/interface';

interface FeedbackInstances {
  messageApi: MessageInstance | null;
  modalApi: Omit<ModalStaticFunctions, 'warn'> | null;
  notificationApi: NotificationInstance | null;
}

// 使用any类型暂时绕过类型错误
type MessageContent = any;

export const useGlobalFeedbackStore = defineStore('globalFeedback', {
  state: (): FeedbackInstances => ({
    messageApi: null,
    modalApi: null,
    notificationApi: null,
  }),
  actions: {
    // --- 初始化API实例 (从App.vue调用) ---
    setMessageApi(api: MessageInstance) {
      this.messageApi = api;
    },
    setModalApi(api: Omit<ModalStaticFunctions, 'warn'>) {
      this.modalApi = api;
    },
    setNotificationApi(api: NotificationInstance) {
      this.notificationApi = api;
    },

    // --- 消息便捷方法 ---
    showMessage(type: 'success' | 'error' | 'info' | 'warning' | 'loading', content: MessageContent, duration?: number) {
      console.log('[GlobalFeedback] showMessage called:', type, content, 'messageApi:', !!this.messageApi);
      if (this.messageApi) {
        console.log('[GlobalFeedback] 调用 messageApi.' + type);
        this.messageApi[type](content, duration);
      } else {
        console.warn('[GlobalFeedback] messageApi未初始化。使用全局 message 对象作为 fallback:', content);
        import('ant-design-vue').then(({ message: antdMessage }) => {
          antdMessage[type](content, duration);
        });
      }
    },
    success(content: MessageContent, duration?: number) {
      this.showMessage('success', content, duration);
    },
    error(content: MessageContent, duration?: number) {
      this.showMessage('error', content, duration);
    },
    info(content: MessageContent, duration?: number) {
      this.showMessage('info', content, duration);
    },
    warning(content: MessageContent, duration?: number) {
      this.showMessage('warning', content, duration);
    },
    loading(content: MessageContent, duration?: number) {
      this.showMessage('loading', content, duration);
    },
    open(args: any) {
      if (this.messageApi) {
        this.messageApi.open(args);
      } else {
        console.warn('messageApi未初始化。消息未显示:', args.content);
      }
    },
    destroy(key?: string | number) {
      if (this.messageApi) {
        this.messageApi.destroy(key);
      }
    },

    // --- Modal方法 ---
    confirm(config: any) {
      if (this.modalApi) {
        this.modalApi.confirm(config);
      } else {
        console.warn('modalApi未初始化。');
      }
    },
    info_modal(config: any) {
      if (this.modalApi) {
        this.modalApi.info(config);
      } else {
        console.warn('modalApi未初始化。');
      }
    },
    success_modal(config: any) {
      if (this.modalApi) {
        this.modalApi.success(config);
      } else {
        console.warn('modalApi未初始化。');
      }
    },
    error_modal(config: any) {
      if (this.modalApi) {
        this.modalApi.error(config);
      } else {
        console.warn('modalApi未初始化。');
      }
    },
    warning_modal(config: any) {
      if (this.modalApi) {
        this.modalApi.warning(config);
      } else {
        console.warn('modalApi未初始化。');
      }
    },

    // --- Notification方法 ---
    notify(type: 'success' | 'error' | 'info' | 'warning', config: any) {
      if (this.notificationApi) {
        this.notificationApi[type](config);
      } else {
        console.warn('notificationApi未初始化。');
      }
    },
    notify_success(config: any) {
      this.notify('success', config);
    },
    notify_error(config: any) {
      this.notify('error', config);
    },
    notify_info(config: any) {
      this.notify('info', config);
    },
    notify_warning(config: any) {
      this.notify('warning', config);
    },
    notify_open(config: any) {
      if (this.notificationApi) {
        this.notificationApi.open(config);
      } else {
        console.warn('notificationApi未初始化。');
      }
    },
  },
}); 