/**
 * 轮询工具函数
 * 用于轮询容器状态直到就绪
 */

import { getToken } from '@/utils/auth';

export interface PollStatus {
  status: 'starting' | 'running' | 'stopped' | 'error' | 'not_found';
  url?: string;
  host_port?: number;
  error?: string;
}

export interface PollOptions {
  maxAttempts?: number;
  interval?: number;
  onProgress?: (status: PollStatus) => void;
}

/**
 * 轮询容器状态直到就绪
 * @param containerId 容器ID或查询参数
 * @param options 轮询选项
 * @returns Promise<PollStatus>
 */
export async function pollUntilReady(
  containerIdOrQuery: string | { training_id: number; user_id: number },
  options: PollOptions = {}
): Promise<PollStatus> {
  const {
    maxAttempts = 30,
    interval = 2000,
    onProgress
  } = options;

  let attempt = 0;

  while (attempt < maxAttempts) {
    try {
      let url: string;
      let response: Response;

      // 如果containerIdOrQuery是对象，使用查询API
      if (typeof containerIdOrQuery === 'object') {
        const params = new URLSearchParams({
          training_id: containerIdOrQuery.training_id.toString(),
          user_id: containerIdOrQuery.user_id.toString()
        });
        url = `/api/v1/environments/query?${params.toString()}`;
      } else {
        url = `/api/v1/environments/${containerIdOrQuery}/status`;
      }

      response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${getToken() || ''}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const result = await response.json();
      
      if (result.code === '0000' && result.data) {
        const status: PollStatus = {
          status: result.data.status,
          url: result.data.url,
          host_port: result.data.host_port,
          error: result.data.error
        };

        // 调用进度回调
        if (onProgress) {
          onProgress(status);
        }

        // 如果状态是running，返回成功
        if (status.status === 'running' && status.url) {
          return status;
        }

        // 如果状态是error或stopped，抛出错误
        if (status.status === 'error' || status.status === 'stopped') {
          throw new Error(status.error || `容器状态: ${status.status}`);
        }

        // 如果状态是not_found且已达到最大尝试次数
        if (status.status === 'not_found' && attempt >= maxAttempts - 1) {
          throw new Error('容器未找到，请重试');
        }
      }

      attempt++;
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, interval));
      }
    } catch (error) {
      attempt++;
      if (attempt >= maxAttempts) {
        throw error;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
  }

  throw new Error('轮询超时，请重试');
}

/**
 * 启动环境并轮询直到就绪
 * @param trainingId 实训ID
 * @param userId 用户ID
 * @param options 轮询选项
 * @returns Promise<PollStatus>
 */
export async function launchAndPoll(
  trainingId: number,
  userId: number,
  options: PollOptions = {}
): Promise<PollStatus> {
  // 启动环境
  const launchResponse = await fetch('/api/v1/environments/launch', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken() || ''}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      training_id: trainingId,
      user_id: userId
    })
  });

  if (!launchResponse.ok) {
    throw new Error(`启动环境失败: ${launchResponse.status}`);
  }

  const launchResult = await launchResponse.json();
  
  if (launchResult.code !== '0000') {
    throw new Error(launchResult.message || '启动环境失败');
  }

  // 如果已有运行中的容器，直接返回
  if (launchResult.data.container_id && launchResult.data.status === 'running') {
    return {
      status: 'running',
      url: launchResult.data.url,
      host_port: launchResult.data.host_port
    };
  }

  // 轮询状态
  return pollUntilReady(
    { training_id: trainingId, user_id: userId },
    options
  );
}

