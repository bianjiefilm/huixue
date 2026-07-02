import { defineStore } from 'pinia'
import { ref } from 'vue'

// 事件类型定义
export enum DataSyncEventType {
  COIN_UPDATED = 'coin-updated',
  TASK_COMPLETED = 'task-completed',
  CHALLENGE_STARTED = 'challenge-started',
  CHALLENGE_COMPLETED = 'challenge-completed',
  SKILL_UPDATED = 'skill-updated'
}

// 全局数据同步存储
export const useGlobalDataSyncStore = defineStore('globalDataSync', () => {
  // 事件监听器
  const listeners = ref<Record<string, Function[]>>({});

  // 添加事件监听器
  const addEventListener = (event: string, callback: Function) => {
    if (!listeners.value[event]) {
      listeners.value[event] = [];
    }
    listeners.value[event].push(callback);
  };

  // 监听事件（返回移除函数）
  const onEvent = (event: string, callback: Function) => {
    addEventListener(event, callback);
    // 返回移除函数
    return () => removeEventListener(event, callback);
  };

  // 移除事件监听器
  const removeEventListener = (event: string, callback: Function) => {
    if (listeners.value[event]) {
      const index = listeners.value[event].indexOf(callback);
      if (index > -1) {
        listeners.value[event].splice(index, 1);
      }
    }
  };

  // 触发事件
  const emit = (event: string, ...args: any[]) => {
    if (listeners.value[event]) {
      listeners.value[event].forEach(callback => {
        try {
          callback(...args);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  };

  // 硬币更新事件
  const emitCoinUpdated = (newBalance: number, reason: string) => {
    emit('coin-updated', { newBalance, reason, timestamp: Date.now() });
    console.log(`Coin updated: ${newBalance}, reason: ${reason}`);
  };

  // 任务完成事件
  const emitTaskCompleted = (task: any, submission: any) => {
    emit('task-completed', { task, submission, timestamp: Date.now() });
    console.log(`Task completed:`, task, submission);
  };

  // 挑战开始事件
  const emitChallengeStarted = (challenge: any) => {
    emit('challenge-started', { challenge, timestamp: Date.now() });
    console.log(`Challenge started:`, challenge);
  };

  // 挑战完成事件
  const emitChallengeCompleted = (challenge: any, result: any) => {
    emit('challenge-completed', { challenge, result, timestamp: Date.now() });
    console.log(`Challenge completed:`, challenge, result);
  };

  return {
    // 事件管理
    addEventListener,
    removeEventListener,
    onEvent,
    emit,

    // 具体事件
    emitCoinUpdated,
    emitTaskCompleted,
    emitChallengeStarted,
    emitChallengeCompleted
  };
});
