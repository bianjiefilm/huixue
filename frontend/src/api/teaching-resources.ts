import request from '@/utils/http';
import type { ApiResponse } from '@/utils/http';

// 教学资源管理相关的类型定义

// 环境类型枚举
export enum EnvironmentType {
  NORMAL = '普通实践',
  JUPYTER = 'jupyter', 
  DESKTOP = '云桌面'
}

// 实践环境配置
export interface EnvironmentConfig {
  id: string;
  name: string;
  type: EnvironmentType;
  storage: {
    min: number;
    max: number;
    default: number;
  };
  memory: {
    min: number;
    max: number;
    default: number;
  };
  cpu: {
    min: number;
    max: number;
    default: number;
  };
  docker_image?: string;
  docker_port?: number;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 服务器资源
export interface ServerResource {
  id: string;
  name: string;
  type: 'application' | 'compute';
  cpu: {
    used: number;
    total: number;
    usageRate: number;
  };
  memory: {
    used: number;
    total: number;
    usageRate: number;
  };
  storage: {
    used: number;
    total: number;
    usageRate: number;
  };
  status: 'online' | 'offline';
  last_updated: string;
}

// 容器进程
export interface ContainerProcess {
  id: string;
  container_id: string;
  container_name: string;
  user_name: string;
  user_id: string;
  course_name?: string;
  course_id?: number;
  environment_type: EnvironmentType;
  cpu_usage: number;
  memory_usage: number;
  memory_limit: number;
  start_time: string;
  running_time: number; // 运行时长（秒）
  last_activity: string;
  status: 'running' | 'stopped';
  ip_address: string;
  port: number;
}

// 并发实验设置
export interface ConcurrentExperimentSetting {
  enabled: boolean;
  updated_at: string;
  updated_by?: string;
}

// 统计信息
export interface ResourceStats {
  total_environments: number;
  normal_practice_count: number;
  jupyter_count: number;
  cloud_desktop_count: number;
  total_containers: number;
  running_containers: number;
  stopped_containers: number;
  total_nodes: number;
  online_nodes: number;
  offline_nodes: number;
  avg_cpu_usage: number;
  avg_memory_usage: number;
  avg_storage_usage: number;
}

// 分页响应类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

// API 函数

// ==================== 实践环境管理 ====================

/**
 * 获取实践环境列表
 */
export async function getEnvironmentConfigs(params: {
  environment_type?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PaginatedResponse<EnvironmentConfig>>> {
  return request.get('/api/v1/teaching-resources/practice-environments', { params });
}

/**
 * 获取实践环境详情
 */
export async function getEnvironmentDetail(environmentId: string): Promise<ApiResponse<EnvironmentConfig>> {
  return request.get(`/api/v1/teaching-resources/practice-environments/${environmentId}`);
}

/**
 * 更新实践环境配置
 */
export async function updateEnvironmentConfig(
  environmentId: string | number,
  config: {
    storage?: { min: number; max: number; default: number };
    memory?: { min: number; max: number; default: number };
    cpu?: { min: number; max: number; default: number };
    docker_image?: string;
    docker_port?: number;
    description?: string;
    is_active?: boolean;
  }
): Promise<ApiResponse<EnvironmentConfig>> {
  return request.put(`/api/v1/teaching-resources/practice-environments/${environmentId}`, config);
}

/**
 * 获取环境类型列表
 */
export async function getEnvironmentTypes(): Promise<ApiResponse<{ value: string; label: string }[]>> {
  return request.get('/api/v1/teaching-resources/environment-types');
}

// ==================== 实验资源监控 ====================

/**
 * 获取服务器节点概览
 */
export async function getServerNodesOverview(): Promise<ApiResponse<{
  application_servers: ServerResource[];
  compute_servers: ServerResource[];
}>> {
  return request.get('/api/v1/teaching-resources/server-nodes/overview');
}

/**
 * 刷新服务器资源监控
 */
export async function refreshServerNodes(): Promise<ApiResponse<{
  application_servers: ServerResource[];
  compute_servers: ServerResource[];
}>> {
  return request.get('/api/v1/teaching-resources/server-nodes/refresh');
}

/**
 * 获取资源使用趋势
 */
export async function getResourceUsageTrend(hours: number = 24): Promise<ApiResponse<any>> {
  return request.get('/api/v1/teaching-resources/resource-usage/trend', { 
    params: { hours } 
  });
}

// ==================== 容器进程管理 ====================

/**
 * 获取容器进程列表
 */
export async function getContainerProcesses(params: {
  keyword?: string;
  environment_type?: string;
  start_time_begin?: string;
  start_time_end?: string;
  duration_min?: number;
  duration_max?: number;
  cpu_min?: number;
  cpu_max?: number;
  memory_min?: number;
  memory_max?: number;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PaginatedResponse<ContainerProcess>>> {
  return request.get('/api/v1/teaching-resources/container-processes', { params });
}

/**
 * 刷新容器进程列表
 */
export async function refreshContainerProcesses(params: {
  keyword?: string;
  environment_type?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<PaginatedResponse<ContainerProcess>>> {
  return request.get('/api/v1/teaching-resources/container-processes/refresh', { params });
}

/**
 * 停止单个容器
 */
export async function stopContainer(
  containerId: string, 
  data: {
    reason?: string;
    operator_id?: number;
  }
): Promise<ApiResponse<{ container_id: string }>> {
  return request.post(`/api/v1/teaching-resources/containers/${containerId}/stop`, data);
}

/**
 * 批量停止容器
 */
export async function batchStopContainers(data: {
  container_ids: string[];
  reason?: string;
  operator_id?: number;
}): Promise<ApiResponse<{
  success_count: number;
  failed_count: number;
  results: Array<{ container_id: string; success: boolean; error?: string }>;
}>> {
  return request.post('/api/v1/teaching-resources/containers/batch-stop', data);
}

// ==================== 并发实验设置 ====================

/**
 * 获取并发实验设置
 */
export async function getConcurrentExperimentSetting(): Promise<ApiResponse<ConcurrentExperimentSetting>> {
  return request.get('/api/v1/teaching-resources/concurrent-experiment-setting');
}

/**
 * 更新并发实验设置
 */
export async function updateConcurrentExperimentSetting(data: {
  enable: boolean;
  operator_id?: number;
}): Promise<ApiResponse<ConcurrentExperimentSetting>> {
  return request.put('/api/v1/teaching-resources/concurrent-experiment-setting', data);
}

// ==================== 统计信息 ====================

/**
 * 获取教学资源管理统计信息
 */
export async function getResourceStats(): Promise<ApiResponse<ResourceStats>> {
  return request.get('/api/v1/teaching-resources/stats');
}

// 已移除模拟数据接口，保持文件末尾无导出