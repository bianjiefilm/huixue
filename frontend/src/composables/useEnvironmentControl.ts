import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  checkActiveEnvironment, 
  launchEnvironment, 
  stopEnvironment,
  type ActiveEnvironment 
} from '@/api/practice';

// 扩展 ActiveEnvironment 类型以支持 accessUrl
declare module '@/api/practice' {
  interface ActiveEnvironment {
    accessUrl?: string;
  }
}

export function useEnvironmentControl() {
  const router = useRouter();
  
  // 状态管理
  const activeEnvironment = ref<ActiveEnvironment | null>(null);
  const showConflictDialog = ref(false);
  const showSwitchDialog = ref(false);
  const isLaunching = ref(false);
  const isStopping = ref(false);
  const isSwitching = ref(false);
  
  // 待启动的环境信息
  const pendingLaunch = ref<{
    practiceId: string;
    practiceName: string;
    environmentType: string;
    onSuccess?: (environment: ActiveEnvironment) => void;
    onError?: (error: any) => void;
  } | null>(null);

  // 计算属性
  const isProcessing = computed(() => 
    isLaunching.value || isStopping.value || isSwitching.value
  );

  /**
   * 检查并启动环境
   * @param practiceId 实践课程ID
   * @param practiceName 实践课程名称
   * @param environmentType 环境类型
   * @param options 选项
   */
  const checkAndLaunchEnvironment = async (
    practiceId: string,
    practiceName: string, 
    environmentType: string,
    options?: {
      onSuccess?: (environment: ActiveEnvironment) => void;
      onError?: (error: any) => void;
    }
  ) => {
    try {
      isLaunching.value = true;
      
      // 检查用户是否有活跃环境
      console.log('[DEBUG] 检查是否有活跃环境...');
      const existingEnv = await checkActiveEnvironment();
      
      if (existingEnv && existingEnv.practiceId !== practiceId) {
        // 有不同的活跃环境，显示冲突弹窗
        console.log('[DEBUG] 检测到活跃环境冲突:', existingEnv);
        activeEnvironment.value = existingEnv;
        pendingLaunch.value = {
          practiceId,
          practiceName,
          environmentType,
          onSuccess: options?.onSuccess,
          onError: options?.onError
        };
        showConflictDialog.value = true;
        return; // 不直接启动，等待用户选择
      }
      
      // 没有冲突或是同一个实践，直接启动环境
      console.log('[DEBUG] 没有环境冲突，直接启动环境');
      await directLaunchEnvironment(practiceId, environmentType, options);
      
    } catch (error: any) {
      // 如果检查活跃环境失败（如404），则直接启动
      if (error?.response?.status === 404 || error?.message?.includes('404')) {
        console.log('[DEBUG] 活跃环境检查返回404，直接启动环境');
        await directLaunchEnvironment(practiceId, environmentType, options);
      } else {
        console.error('启动环境失败:', error);
        message.error('启动环境失败');
        options?.onError?.(error);
      }
    } finally {
      isLaunching.value = false;
    }
  };

  /**
   * 直接启动环境（不检查冲突）
   */
  const directLaunchEnvironment = async (
    practiceId: string,
    environmentType: string,
    options?: {
      onSuccess?: (environment: ActiveEnvironment) => void;
      onError?: (error: any) => void;
    }
  ) => {
    try {
      isLaunching.value = true;
      
      const environment = await launchEnvironment(practiceId, environmentType);
      
      if (environment) {
        console.log('[DEBUG] Environment object received:', environment);
        console.log('[DEBUG] environment.url:', environment.url);
        console.log('[DEBUG] environment.accessUrl:', environment.accessUrl);
        console.log('[DEBUG] environmentType:', environmentType);
        
        message.success('环境启动成功');
        activeEnvironment.value = environment;
        
        // 对于云桌面环境，可能需要获取 Jupyter URL
        if (environmentType === 'desktop' && !environment.accessUrl) {
          try {
            const { launchJupyterEnvironment } = await import('@/api/training');
            const jupyterResponse = await launchJupyterEnvironment(practiceId);
            if (jupyterResponse.data?.url) {
              environment.accessUrl = jupyterResponse.data.url;
            } else if (jupyterResponse.data?.notebookId && jupyterResponse.data?.token) {
              const baseUrl = import.meta.env.VITE_JUPYTER_BASE_URL || 'http://localhost:8888';
              environment.accessUrl = `${baseUrl}/notebooks/${jupyterResponse.data.notebookId}.ipynb?token=${jupyterResponse.data.token}`;
            }
          } catch (error) {
            console.warn('获取 Jupyter URL 失败:', error);
          }
        }
        
        options?.onSuccess?.(environment);
        
        // 检查是否有URL需要打开
        const urlToOpen = environment.url || environment.accessUrl;
        console.log('[DEBUG] urlToOpen:', urlToOpen);
        
        if (urlToOpen && environmentType !== 'desktop') {
          console.log('[DEBUG] Opening new window with URL:', urlToOpen);
          message.info('环境已启动，正在打开...');
          const newWindow = window.open(urlToOpen, '_blank');
          console.log('[DEBUG] New window opened:', newWindow);
          if (!newWindow) {
            message.warning('请检查浏览器是否阻止了新窗口打开');
          }
        } else if (environmentType === 'desktop') {
          console.log('[DEBUG] Desktop environment, not opening new window');
          message.info('环境已启动，请在我的课堂查看');
        } else {
          console.log('[DEBUG] No URL provided, environment may be accessed from my classroom');
          message.info('环境已启动，请查看我的课堂');
        }
      } else {
        console.error('[DEBUG] launchEnvironment returned null');
        throw new Error('启动环境失败');
      }
      
    } catch (error) {
      console.error('[DEBUG] directLaunchEnvironment error:', error);
      console.error('启动环境失败:', error);
      message.error('启动环境失败');
      options?.onError?.(error);
    } finally {
      isLaunching.value = false;
    }
  };

  /**
   * 停止环境
   */
  const stopCurrentEnvironment = async (environmentId: string) => {
    try {
      isStopping.value = true;
      
      const success = await stopEnvironment(environmentId);
      
      if (success) {
        message.success('环境已停止');
        activeEnvironment.value = null;
        return true;
      } else {
        throw new Error('停止环境失败');
      }
      
    } catch (error) {
      console.error('停止环境失败:', error);
      message.error('停止环境失败');
      return false;
    } finally {
      isStopping.value = false;
    }
  };

  /**
   * 处理返回该实验
   */
  const handleGoBackToActiveEnvironment = async (environment: ActiveEnvironment) => {
    console.log('[环境控制] 返回活跃实验:', environment);

    // 根据环境类型跳转到对应页面
    if (environment.url) {
      // 如果有直接的URL，在新窗口打开
      window.open(environment.url, '_blank');
    } else {
      // 跳转到实践挑战页面
      const practiceId = environment.practiceId;

      try {
        // 获取该实践的第一个任务ID
        const response = await fetch(`/api/v1/practices/${practiceId}/tasks`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const result = await response.json();
          const tasks = result.data?.list || result.data || [];
          if (tasks.length > 0) {
            // 找到第一个任务的ID
            const firstTask = tasks[0];
            const taskId = firstTask.taskId || firstTask.id;
            console.log('[环境控制] 跳转到:', `/course/challenge/${practiceId}/${taskId}`);
            router.push(`/course/challenge/${practiceId}/${taskId}`);
          } else {
            console.log('[环境控制] 没有找到任务，跳转到实践详情页');
            router.push(`/course/practice/${practiceId}`);
          }
        } else {
          console.log('[环境控制] 获取任务列表失败，跳转到实践详情页');
          router.push(`/course/practice/${practiceId}`);
        }
      } catch (error) {
        console.error('[环境控制] 获取任务列表出错:', error);
        router.push(`/course/practice/${practiceId}`);
      }
    }

    showConflictDialog.value = false;
    resetPendingLaunch();
  };

  /**
   * 处理切换环境 - 打开二次确认弹窗
   */
  const handleSwitchToNewEnvironment = async () => {
    if (!activeEnvironment.value) {
      console.log('[环境控制] 没有活跃环境，直接启动新环境');
      showConflictDialog.value = false;
      return;
    }

    if (!pendingLaunch.value) {
      console.warn('[环境控制] 缺少待启动环境信息，无法切换');
      message.warning('缺少待启动环境信息，请重新点击启动按钮');
      return;
    }

    console.log('[环境控制] 打开切换环境二次确认:', activeEnvironment.value.id);
    showConflictDialog.value = false;
    showSwitchDialog.value = true;
  };

  /**
   * 确认切换环境（用于二次确认对话框）
   */
  const confirmSwitchEnvironment = async () => {
    if (!activeEnvironment.value || !pendingLaunch.value) return;
    
    try {
      isSwitching.value = true;
      
      // 停止当前环境
      const stopSuccess = await stopCurrentEnvironment(activeEnvironment.value.id);
      
      if (stopSuccess) {
        // 启动新环境
        await directLaunchEnvironment(
          pendingLaunch.value.practiceId,
          pendingLaunch.value.environmentType,
          {
            onSuccess: pendingLaunch.value.onSuccess,
            onError: pendingLaunch.value.onError
          }
        );
        
        showSwitchDialog.value = false;
        resetPendingLaunch();
      }
      
    } catch (error) {
      console.error('切换环境失败:', error);
      message.error('切换环境失败');
    } finally {
      isSwitching.value = false;
    }
  };

  /**
   * 取消切换环境
   */
  const cancelSwitchEnvironment = () => {
    showSwitchDialog.value = false;
    resetPendingLaunch();
  };

  /**
   * 重置待启动信息
   */
  const resetPendingLaunch = () => {
    pendingLaunch.value = null;
  };

  /**
   * 关闭冲突对话框
   */
  const closeConflictDialog = () => {
    showConflictDialog.value = false;
    resetPendingLaunch();
  };

  return {
    // 状态
    activeEnvironment,
    showConflictDialog,
    showSwitchDialog,
    isLaunching,
    isStopping,
    isSwitching,
    isProcessing,
    pendingLaunch,
    
    // 方法
    checkAndLaunchEnvironment,
    directLaunchEnvironment,
    stopCurrentEnvironment,
    handleGoBackToActiveEnvironment,
    handleSwitchToNewEnvironment,
    confirmSwitchEnvironment,
    cancelSwitchEnvironment,
    closeConflictDialog,
    resetPendingLaunch
  };
}
