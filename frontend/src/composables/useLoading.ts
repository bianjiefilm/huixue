import { ref, type Ref } from 'vue';

/**
 * 创建loading状态管理
 * @param initialValue 初始值
 * @returns loading状态和包装函数
 */
export function useLoading(initialValue = false) {
  const loading = ref(initialValue);
  
  /**
   * 执行异步操作并自动管理loading状态
   * @param fn 异步函数
   * @returns 异步函数的返回值
   */
  async function withLoading<T>(fn: () => Promise<T>): Promise<T> {
    loading.value = true;
    try {
      return await fn();
    } finally {
      loading.value = false;
    }
  }
  
  return {
    loading: loading as Ref<boolean>,
    withLoading
  };
}

/**
 * 创建多个loading状态管理
 * @param keys loading状态的键名
 * @returns loading状态对象和包装函数
 */
export function useMultipleLoading<T extends string>(...keys: T[]) {
  const loadingStates = {} as Record<T, Ref<boolean>>;
  
  keys.forEach(key => {
    loadingStates[key] = ref(false);
  });
  
  /**
   * 执行异步操作并自动管理指定的loading状态
   * @param key loading状态键名
   * @param fn 异步函数
   * @returns 异步函数的返回值
   */
  async function withLoading<R>(key: T, fn: () => Promise<R>): Promise<R> {
    loadingStates[key].value = true;
    try {
      return await fn();
    } finally {
      loadingStates[key].value = false;
    }
  }
  
  /**
   * 检查是否有任意loading状态为true
   * @returns 是否有loading
   */
  function isAnyLoading(): boolean {
    return Object.values(loadingStates).some((state: any) => state.value);
  }
  
  /**
   * 检查指定的loading状态是否为true
   * @param keys 要检查的键名
   * @returns 是否有loading
   */
  function isSomeLoading(...checkKeys: T[]): boolean {
    return checkKeys.some(key => loadingStates[key].value);
  }
  
  return {
    loading: loadingStates,
    withLoading,
    isAnyLoading,
    isSomeLoading
  };
}

/**
 * 创建防抖loading状态管理
 * @param delay 延迟时间(ms)
 * @returns loading状态和包装函数
 */
export function useDebouncedLoading(delay = 200) {
  const loading = ref(false);
  let timer: NodeJS.Timeout | null = null;
  
  /**
   * 执行异步操作并自动管理loading状态（带防抖）
   * @param fn 异步函数
   * @returns 异步函数的返回值
   */
  async function withLoading<T>(fn: () => Promise<T>): Promise<T> {
    // 清除之前的定时器
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
    
    // 设置延迟显示loading
    timer = setTimeout(() => {
      loading.value = true;
      timer = null;
    }, delay);
    
    try {
      const result = await fn();
      
      // 如果操作很快完成，取消loading显示
      if (timer) {
        clearTimeout(timer);
        timer = null;
      } else {
        // 如果已经显示了loading，则关闭它
        loading.value = false;
      }
      
      return result;
    } catch (error) {
      // 错误时也要清理
      if (timer) {
        clearTimeout(timer);
        timer = null;
      } else {
        loading.value = false;
      }
      throw error;
    }
  }
  
  return {
    loading: loading as Ref<boolean>,
    withLoading
  };
}