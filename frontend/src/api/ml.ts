import { request } from '@/utils/request';

// 类型定义
export interface NodeType {
  type: string;
  name: string;
  category: string;
  description: string;
}

export interface NodeCategory {
  key: string;
  name: string;
}

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  config?: any;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface Workflow {
  id: string;
  userId: string;
  projectId: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowRunResult {
  runId: string;
  status: 'running' | 'completed' | 'failed';
  startTime: string;
  endTime?: string;
  results?: any;
  logs?: string[];
  error?: string;
}

/**
 * 获取节点类型列表
 */
export function getNodeTypes() {
  return request<{
    nodeTypes: NodeType[];
    categories: NodeCategory[];
  }>({
    url: '/api/ml/node-types',
    method: 'get',
  });
}

/**
 * 获取工作流模板
 */
export function getWorkflowTemplates() {
  return request<WorkflowTemplate[]>({
    url: '/api/ml/workflow-templates',
    method: 'get',
  });
}

/**
 * 获取用户工作流列表
 */
export function getUserWorkflows(params: {
  userId: string;
  projectId?: string;
}) {
  return request<Workflow[]>({
    url: '/api/ml/workflows',
    method: 'get',
    params,
  });
}

/**
 * 获取工作流详情
 */
export function getWorkflowDetail(id: string) {
  return request<Workflow>({
    url: `/api/ml/workflows/${id}`,
    method: 'get',
  });
}

/**
 * 保存或更新工作流
 */
export function saveWorkflow(data: Partial<Workflow>) {
  return request<{
    message: string;
    data: Workflow;
  }>({
    url: '/api/ml/workflows',
    method: 'post',
    data,
  });
}

/**
 * 删除工作流
 */
export function deleteWorkflow(id: string) {
  return request<{
    message: string;
  }>({
    url: `/api/ml/workflows/${id}`,
    method: 'delete',
  });
}

/**
 * 运行工作流
 */
export function runWorkflow(data: {
  workflowId: string;
  userId: string;
  config?: any;
}) {
  return request<{
    message: string;
    runId: string;
  }>({
    url: '/api/ml/workflows/run',
    method: 'post',
    data,
  });
}

/**
 * 获取工作流运行状态
 */
export function getWorkflowRunStatus(runId: string) {
  return request<WorkflowRunResult>({
    url: `/api/ml/workflows/runs/${runId}`,
    method: 'get',
  });
}

/**
 * 停止工作流运行
 */
export function stopWorkflowRun(runId: string) {
  return request<{
    message: string;
  }>({
    url: `/api/ml/workflows/runs/${runId}/stop`,
    method: 'post',
  });
}

/**
 * 导出模型
 */
export function exportModel(params: {
  workflowId: string;
  format: 'onnx' | 'pmml' | 'pickle';
}) {
  return request<{
    url: string;
    filename: string;
  }>({
    url: '/api/ml/models/export',
    method: 'post',
    data: params,
  });
}

/**
 * 获取数据集列表
 */
export function getMLDatasets(projectId?: string) {
  return request<Array<{
    id: string;
    name: string;
    path: string;
    size: number;
    format: string;
    description?: string;
  }>>({
    url: '/api/ml/datasets',
    method: 'get',
    params: { projectId },
  });
}

/**
 * 上传数据集
 */
export function uploadDataset(formData: FormData) {
  return request<{
    message: string;
    datasetId: string;
  }>({
    url: '/api/ml/datasets/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

// 获取 DAG 编排数据
export interface DagNode {
  id: string;
  name: string;
  type: string;
  left?: number;
  top?: number;
  ico?: string;
  state?: string;
  label?: string;
  config?: Record<string, any>;
  [key: string]: any;
}

export interface DagEdge {
  id: string;
  startId: string;
  endId: string;
  source?: string;
  target?: string;
  sourceAnchor?: number;
  targetAnchor?: number;
  type?: string;
  label?: string;
  [key: string]: any;
}

export interface DagGraph {
  nodes: DagNode[];
  edges: DagEdge[];
  GlobalConfig?: Record<string, any>;
}

export async function fetchDagGraph(projectId: string): Promise<DagGraph> {
  const response = await request<DagGraph>({
    url: `/api/v1/ml/projects/${projectId}/dag`,
    method: 'get',
  });
  return response;
}