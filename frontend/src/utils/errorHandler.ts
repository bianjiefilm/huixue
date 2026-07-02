import { message } from 'ant-design-vue';

interface ApiError {
  code?: string;
  message?: string;
  data?: any;
}

/**
 * 统一API错误处理
 * @param error 错误对象
 * @param customMessage 自定义错误消息
 * @returns 处理后的错误信息
 */
export function handleApiError(error: any, customMessage?: string): ApiError {
  console.error('API Error:', error);

  // 网络错误
  if (!error.response) {
    const errorMsg = '网络连接失败，请检查网络设置';
    message.error(customMessage || errorMsg);
    return { code: 'NETWORK_ERROR', message: errorMsg };
  }

  // HTTP错误
  const { status, data } = error.response;

  let errorMsg = customMessage || '操作失败';
  let errorCode = 'UNKNOWN_ERROR';

  switch (status) {
    case 400:
      errorMsg = data?.message || '请求参数错误';
      errorCode = 'BAD_REQUEST';
      break;
    case 401:
      errorMsg = '登录已过期，请重新登录';
      errorCode = 'UNAUTHORIZED';
      // TODO: 跳转到登录页
      break;
    case 403:
      errorMsg = '您没有权限执行此操作';
      errorCode = 'FORBIDDEN';
      break;
    case 404:
      errorMsg = data?.message || '请求的资源不存在';
      errorCode = 'NOT_FOUND';
      break;
    case 409:
      errorMsg = data?.message || '数据冲突';
      errorCode = 'CONFLICT';
      break;
    case 422:
      errorMsg = data?.message || '数据验证失败';
      errorCode = 'VALIDATION_ERROR';
      break;
    case 500:
      errorMsg = '服务器错误，请稍后重试';
      errorCode = 'SERVER_ERROR';
      break;
    default:
      errorMsg = data?.message || customMessage || `请求失败(${status})`;
      errorCode = `HTTP_${status}`;
  }

  message.error(errorMsg);
  return { code: errorCode, message: errorMsg, data };
}

/**
 * 创建带错误处理的API调用包装器
 * @param apiCall API调用函数
 * @param options 选项
 * @returns 包装后的函数
 */
export function withErrorHandler<T extends (...args: any[]) => Promise<any>>(
  apiCall: T,
  options?: {
    customMessage?: string;
    showError?: boolean;
    defaultValue?: any;
  }
): T {
  const { customMessage, showError = true, defaultValue } = options || {};

  return (async (...args: Parameters<T>) => {
    try {
      return await apiCall(...args);
    } catch (error) {
      if (showError) {
        handleApiError(error, customMessage);
      }
      return defaultValue !== undefined ? defaultValue : null;
    }
  }) as T;
}

/**
 * 批量操作错误处理
 * @param results 批量操作结果
 * @param successMessage 成功消息
 * @returns 处理结果
 */
export function handleBatchResults(
  results: Array<{ success: boolean; error?: any }>,
  successMessage?: string
): { successCount: number; failCount: number } {
  const successCount = results.filter(r => r.success).length;
  const failCount = results.length - successCount;

  if (successCount === results.length) {
    message.success(successMessage || `全部操作成功(${successCount}个)`);
  } else if (successCount > 0) {
    message.warning(`部分操作成功: ${successCount}个成功, ${failCount}个失败`);
  } else {
    message.error('操作全部失败');
  }

  return { successCount, failCount };
}