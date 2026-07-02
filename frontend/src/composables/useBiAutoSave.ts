import { ref, onUnmounted } from 'vue';

export type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';

export interface BiDraft {
  snapshot: any;
  schemaVersion: string;
  updatedAt: string;
}

export interface UseBiAutoSaveOptions {
  trainingId: number;
  classroomId: string;
  studentId: number;
  getSpec: () => Promise<any>;
  autoSaveInterval?: number; // 自动保存间隔 (ms), 默认 60000
}

const SCHEMA_VERSION = 'gwalk-v0.4.77';
const PLATFORM_VERSION = '2.1.0';

/**
 * BI 可视化分析自动保存 composable
 *
 * 功能：
 * 1. localStorage 即时保存 (防意外丢失)
 * 2. 服务器保存 (防抖)
 * 3. 草稿恢复
 */
export function useBiAutoSave(options: UseBiAutoSaveOptions) {
  const {
    trainingId,
    classroomId,
    studentId,
    getSpec,
    autoSaveInterval = 60000 // 默认 60 秒
  } = options;

  const saveStatus = ref<SaveStatus>('idle');
  const lastSavedAt = ref<Date | null>(null);

  let saveTimer: ReturnType<typeof setTimeout> | null = null;
  let pendingSpec: any = null;

  // localStorage key
  const localStorageKey = `bi_draft_${classroomId}_${trainingId}`;

  /**
   * 保存到 localStorage (即时)
   */
  function saveToLocalStorage(spec: any) {
    try {
      const draft: BiDraft = {
        snapshot: spec,
        schemaVersion: SCHEMA_VERSION,
        updatedAt: new Date().toISOString()
      };
      localStorage.setItem(localStorageKey, JSON.stringify(draft));
      console.log('[BiAutoSave] Saved to localStorage');
    } catch (error) {
      console.error('[BiAutoSave] Failed to save to localStorage:', error);
    }
  }

  /**
   * 从 localStorage 加载
   */
  function loadFromLocalStorage(): BiDraft | null {
    try {
      const data = localStorage.getItem(localStorageKey);
      if (data) {
        return JSON.parse(data);
      }
    } catch (error) {
      console.error('[BiAutoSave] Failed to load from localStorage:', error);
    }
    return null;
  }

  /**
   * 清除 localStorage 草稿
   */
  function clearLocalStorage() {
    try {
      localStorage.removeItem(localStorageKey);
    } catch (error) {
      console.error('[BiAutoSave] Failed to clear localStorage:', error);
    }
  }

  /**
   * 保存到服务器
   */
  async function saveToServer(spec: any): Promise<boolean> {
    try {
      saveStatus.value = 'saving';

      const draftData = {
        snapshot: spec,
        schemaVersion: SCHEMA_VERSION,
        platformVersion: PLATFORM_VERSION
      };

      const response = await fetch(
        `/api/v1/trainings/${trainingId}/bi-draft?classroom_id=${classroomId}&student_id=${studentId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(draftData)
        }
      );

      const result = await response.json();

      if (result.code === '0000') {
        saveStatus.value = 'saved';
        lastSavedAt.value = new Date();
        console.log('[BiAutoSave] Saved to server');
        return true;
      } else {
        console.error('[BiAutoSave] Server save failed:', result.message);
        saveStatus.value = 'error';
        return false;
      }
    } catch (error) {
      console.error('[BiAutoSave] Failed to save to server:', error);
      saveStatus.value = 'error';
      return false;
    }
  }

  /**
   * 从服务器加载草稿
   */
  async function loadFromServer(): Promise<BiDraft | null> {
    try {
      const response = await fetch(
        `/api/v1/trainings/${trainingId}/bi-draft?classroom_id=${classroomId}&student_id=${studentId}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
            'Content-Type': 'application/json'
          }
        }
      );

      const result = await response.json();

      if (result.code === '0000' && result.data) {
        return {
          snapshot: result.data.snapshot,
          schemaVersion: result.data.schemaVersion || SCHEMA_VERSION,
          updatedAt: result.data.updatedAt
        };
      }
    } catch (error) {
      console.error('[BiAutoSave] Failed to load from server:', error);
    }
    return null;
  }

  /**
   * 防抖保存（用于自动保存）
   */
  function debouncedSave(spec: any) {
    pendingSpec = spec;

    // 立即保存到 localStorage
    saveToLocalStorage(spec);

    // 防抖保存到服务器
    if (saveTimer) {
      clearTimeout(saveTimer);
    }

    saveTimer = setTimeout(async () => {
      if (pendingSpec) {
        await saveToServer(pendingSpec);
        pendingSpec = null;
      }
    }, autoSaveInterval);
  }

  /**
   * 手动触发保存
   */
  async function saveDraft(spec?: any): Promise<boolean> {
    const specToSave = spec || (await getSpec());

    if (!specToSave) {
      console.warn('[BiAutoSave] No spec to save');
      return false;
    }

    // 保存到 localStorage
    saveToLocalStorage(specToSave);

    // 保存到服务器
    return await saveToServer(specToSave);
  }

  /**
   * 加载草稿（优先 localStorage，fallback 服务器）
   */
  async function loadDraft(): Promise<BiDraft | null> {
    // 先尝试从 localStorage 加载
    const localDraft = loadFromLocalStorage();

    // 再尝试从服务器加载
    const serverDraft = await loadFromServer();

    if (!localDraft && !serverDraft) {
      return null;
    }

    // 比较时间戳，返回较新的
    if (localDraft && serverDraft) {
      const localTime = new Date(localDraft.updatedAt).getTime();
      const serverTime = new Date(serverDraft.updatedAt).getTime();

      if (localTime > serverTime) {
        console.log('[BiAutoSave] Using local draft (newer)');
        return localDraft;
      } else {
        console.log('[BiAutoSave] Using server draft (newer)');
        return serverDraft;
      }
    }

    return localDraft || serverDraft;
  }

  /**
   * 处理 spec 变化（由外部调用）
   */
  function onSpecChange(spec: any) {
    debouncedSave(spec);
  }

  /**
   * 页面离开前保存
   */
  async function saveBeforeUnload() {
    if (pendingSpec) {
      // 使用同步方式保存到 localStorage（确保不丢失）
      saveToLocalStorage(pendingSpec);

      // 尝试保存到服务器（可能不会完成）
      try {
        await saveToServer(pendingSpec);
      } catch {
        // 忽略错误，localStorage 已保存
      }
    }
  }

  // 添加页面离开监听
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', saveBeforeUnload);
  }

  // 清理
  onUnmounted(() => {
    if (saveTimer) {
      clearTimeout(saveTimer);
    }
    if (typeof window !== 'undefined') {
      window.removeEventListener('beforeunload', saveBeforeUnload);
    }
  });

  return {
    saveStatus,
    lastSavedAt,
    saveDraft,
    loadDraft,
    onSpecChange,
    clearLocalStorage
  };
}
