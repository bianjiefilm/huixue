import { request } from '@/utils/request';

export interface SceneJSON {
  nodes: any[];
  links: any[];
  props: object;
}

export interface PipelineDAG {
  nodes: any[];
  edges: any[];
}

export interface NotebookCheckpoint {
  path: string;
  content: string;
}

export interface DatasetFile {
  name: string;
  path: string;
  size: number;
  type?: string;
  description?: string;
}

// ==================== BI相关接口 ====================

/**
 * 保存BI场景配置
 */
export function saveBIScene(sceneId: string, sceneJson: SceneJSON) {
  return request({
    url: `/api/v1/bi/${sceneId}/save`,
    method: 'post',
    data: sceneJson
  });
}

/**
 * 获取BI场景预览URL
 */
export function getBIPreviewUrl(sceneId: string) {
  return request<{ url: string; expires_in: number }>({
    url: `/api/v1/bi/${sceneId}/preview-url`,
    method: 'get'
  });
}

// ==================== AI相关接口 ====================

/**
 * 运行AI Pipeline
 */
export function runAIPipeline(pipelineId: string, dag: PipelineDAG) {
  return request<{
    run_id: string;
    pipeline_id: string;
    status: string;
    started_at: string;
  }>({
    url: `/api/v1/ai/${pipelineId}/run`,
    method: 'post',
    data: dag
  });
}

/**
 * 获取AI运行日志
 */
export function getAIRunLogs(runId: string, offset: number = 0, limit: number = 100) {
  return request<{
    run_id: string;
    logs: Array<{
      timestamp: string;
      level: string;
      message: string;
    }>;
    total: number;
    has_more: boolean;
  }>({
    url: `/api/v1/ai/${runId}/logs`,
    method: 'get',
    params: { offset, limit }
  });
}

/**
 * 保存AI Pipeline配置
 */
export function saveAIPipeline(pipelineId: string, dag: PipelineDAG) {
  return request<{
    pipeline_id: string;
    saved_at: string;
    version: number;
  }>({
    url: `/api/v1/ai/${pipelineId}/save`,
    method: 'post',
    data: dag
  });
}

// ==================== Jupyter相关接口 ====================

/**
 * 启动Jupyter环境
 */
export function launchJupyter(trainingId: number) {
  return request<{
    env_id: string;
    url: string;
    token: string;
    expires_in: number;
    training_id: number;
  }>({
    url: `/api/v1/jupyter/${trainingId}/launch`,
    method: 'get'
  });
}

/**
 * 延长Jupyter环境时间
 */
export function extendJupyterTime(envId: string, minutes: number = 30) {
  return request<{
    env_id: string;
    extended_minutes: number;
    new_expires_in: number;
    extended_at: string;
  }>({
    url: `/api/v1/jupyter/${envId}/extend-time`,
    method: 'post',
    data: { minutes }
  });
}

/**
 * 重置Jupyter环境（恢复依赖）
 */
export function resetJupyterEnv(envId: string) {
  return request<{
    env_id: string;
    reset_type: string;
    reset_at: string;
  }>({
    url: `/api/v1/jupyter/${envId}/reset-env`,
    method: 'post'
  });
}

/**
 * 重置代码仓库（清空用户修改）
 */
export function resetJupyterRepo(envId: string) {
  return request<{
    env_id: string;
    reset_type: string;
    reset_at: string;
    warning: string;
  }>({
    url: `/api/v1/jupyter/${envId}/reset-repo`,
    method: 'post'
  });
}

// ==================== 通用接口 ====================

/**
 * 获取实训手册（Markdown格式）
 */
export function getTrainingHandbook(trainingId: number) {
  return request<{
    training_id: number;
    content: string;
    format: string;
  }>({
    url: `/api/v1/trainings/${trainingId}/handbook`,
    method: 'get'
  });
}

/**
 * 获取实训数据集列表
 */
export function getTrainingDatasets(trainingId: number) {
  return request<{
    training_id: number;
    datasets: DatasetFile[];
    total: number;
  }>({
    url: `/api/v1/trainings/${trainingId}/datasets`,
    method: 'get'
  });
}