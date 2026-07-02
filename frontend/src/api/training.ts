import { get, post, put, del } from '@/utils/request';
import type { 
  Project, 
  ProjectDetail, 
  ProjectFilter,
  Dataset,
  WorkflowState,
  AddProjectToClassroomRequest,
  AddProjectToClassroomResponse,
  SceneJSON,
  PipelineDAG,
  SingleStepResult,
  NotebookCheckpoint,
  ExtendTimeRequest,
  LaunchEnvironmentResponse
} from './types/project';

// Types for training functionality
export interface NewTraining {
  name: string;
  type: 'bi' | 'ai' | 'jupyter';
  intro: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  categories: string[];
  environment?: string;
  coverImage?: string;
  duration?: number;  // 预计时长（分钟）
}

export interface TrainingEnvironment {
  id: string;
  name: string;
  type: string;
  description?: string;
}

// 实训课程状态类型
export type TrainingStatusType = 
  | 'draft'               // 编辑中（创建未发布）
  | 'editing'             // 编辑中（发布后编辑）
  | 'pending'             // 审核中
  | 'published_personal'  // 已发布（个人）
  | 'published_public'    // 已发布（公开）
  | 'rejected';           // 审核未通过

export interface TrainingItem {
  id: string;
  title: string;
  name?: string;
  intro?: string;
  description?: string;
  status: TrainingStatusType;
  statusDetail?: string;
  type: 'bi' | 'ai' | 'jupyter';
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  categories: string[];
  direction?: string;
  createTime: string;
  updateTime?: string;
  publishTime?: string;
  version?: string;
  duration?: number;
  skills?: string[];
  cover?: string;
  environment?: string;
}

export interface TrainingStatus {
  value: string;
  label: string;
}

/**
 * 获取项目实训列表
 */
export async function getProjectList(filters?: ProjectFilter) {
  try {
    const response = await get('/api/v1/projects', { params: filters });
    return response.data;
  } catch (error) {
    console.error('获取项目列表失败:', error);
    throw error;
  }
}

/**
 * 获取项目详情
 */
export async function getProjectDetail(projectId: string): Promise<ProjectDetail> {
  try {
    const response = await get(`/api/v1/trainings/library/${projectId}`);
    return response.data;
  } catch (error) {
    console.error('获取项目详情失败:', error);
    throw error;
  }
}

/**
 * 获取实训数据集 - 使用简化的训练API端点
 */
export async function getProjectDatasets(projectId: string): Promise<Dataset[]> {
  try {
    console.log('[getProjectDatasets] Calling API with projectId:', projectId);
    // 调用简化的实训数据集端点 (不需要classroom_id)
    const response = await get(`/api/v1/trainings/${projectId}/datasets`);
    console.log('[getProjectDatasets] Raw response:', response);
    console.log('[getProjectDatasets] response.data:', response?.data);
    console.log('[getProjectDatasets] response.data.datasets:', response?.data?.datasets);
    // 返回datasets数组
    if (response && response.data && response.data.datasets) {
      return response.data.datasets;
    }
    // 尝试其他可能的响应结构
    if (response && response.datasets) {
      console.log('[getProjectDatasets] Using response.datasets directly');
      return response.datasets;
    }
    console.log('[getProjectDatasets] No datasets found, returning empty array');
    return [];
  } catch (error) {
    console.error('[getProjectDatasets] 获取实训数据集失败:', error);
    return [];
  }
}

/**
 * 获取实训手册
 */
export async function getTrainingManual(projectId: string): Promise<string> {
  try {
    const response = await get(`/api/v1/trainings/${projectId}/handbook`);
    // 返回content字段
    if (response.data && response.data.content) {
      return response.data.content;
    }
    return '';
  } catch (error) {
    console.error('获取实训手册失败:', error);
    return '';
  }
}

export interface TrainingCodeTask {
  id: number;
  training_id: number;
  title: string;
  order_in_training: number;
  task_type: string;
  env_type: string;
  difficulty?: string;
  handbook_markdown?: string;
  starter_code?: string;
  match_rule: string;
  tests?: number;
  visible_tests?: TrainingCodeTaskTest[];
}

export interface TrainingCodeTaskTest {
  id: number;
  case_id: string;
  input_data: string;
  expected_output: string;
  is_hidden: boolean;
  weight: number;
}

export interface TrainingCodeEvaluationResult {
  status: string;
  score: number;
  passed_tests: number;
  total_tests: number;
  test_results?: any[];
  error_message?: string;
}

export interface TrainingCodePassedSnapshot {
  has_passed_code: boolean;
  submitted_code?: string | null;
  evaluation_id?: number | null;
  passed_tests: number;
  total_tests: number;
  score: number;
  created_at?: string | null;
}

export interface TrainingCodeGradeRow {
  student_id: number;
  username: string;
  student_name: string;
  evaluation_id?: number;
  status?: string;
  grade_status: string;
  passed_tests: number;
  total_tests: number;
  score: number;
  created_at?: string;
}

export interface TrainingCodeGradesResponse {
  training_id: number;
  task_id: number;
  classroom_id: number;
  status: string;
  summary: Record<string, number>;
  grades: TrainingCodeGradeRow[];
  total: number;
}

export async function getTrainingCodeTasks(trainingId: string | number) {
  const response = await get(`/api/v1/trainings/${trainingId}/code-tasks`);
  return response.data as { training_id: number; tasks: TrainingCodeTask[]; total: number };
}

export async function getTrainingCodeTask(trainingId: string | number, taskId: string | number) {
  const response = await get(`/api/v1/trainings/${trainingId}/code-tasks/${taskId}`);
  return response.data as TrainingCodeTask;
}

export async function getTrainingCodeTaskTests(trainingId: string | number, taskId: string | number) {
  const response = await get(`/api/v1/trainings/${trainingId}/code-tasks/${taskId}/tests`);
  return response.data as { tests: TrainingCodeTaskTest[] };
}

export async function evaluateTrainingCodeTask(
  trainingId: string | number,
  taskId: string | number,
  code: string
) {
  const response = await post(`/api/v1/trainings/${trainingId}/code-tasks/${taskId}/evaluate`, { code });
  return response.data as TrainingCodeEvaluationResult;
}

export async function getTrainingCodeTaskPassedSnapshot(
  trainingId: string | number,
  taskId: string | number
) {
  const response = await get(`/api/v1/trainings/${trainingId}/code-tasks/${taskId}/passed-snapshot`);
  return response.data as TrainingCodePassedSnapshot;
}

export async function getTrainingCodeTaskGrades(
  trainingId: string | number,
  taskId: string | number,
  classroomId: string | number,
  status = 'all'
) {
  const response = await get(`/api/v1/trainings/${trainingId}/code-tasks/${taskId}/grades`, {
    classroom_id: classroomId,
    status
  });
  return response.data as TrainingCodeGradesResponse;
}

/**
 * 添加项目到课堂
 */
export async function addProjectToClassroom(
  classroomId: string,
  request: AddProjectToClassroomRequest
): Promise<AddProjectToClassroomResponse> {
  try {
    // 使用正确的API路径：trainingId在request中
    const trainingId = request.id;
    const response = await post(`/api/v1/trainings/library/${trainingId}/add-to-classroom/${classroomId}`, {
      training_id: parseInt(trainingId),
      start_time: request.startDate,
      end_time: request.endDate,
      allow_late_submission: !request.isRequired,
      late_submission_days: 7
    });
    return response.data;
  } catch (error) {
    console.error('添加项目到课堂失败:', error);
    throw error;
  }
}

// BI可视化分析实训相关API

/**
 * 保存BI场景
 */
export async function saveBIScene(sceneId: string, sceneData: SceneJSON) {
  try {
    const response = await post(`/api/v1/bi/${sceneId}/save`, sceneData);
    return response;
  } catch (error) {
    console.error('保存BI场景失败:', error);
    throw error;
  }
}

/**
 * 获取BI预览URL
 */
export async function getBIPreviewUrl(sceneId: string): Promise<string> {
  try {
    const response = await get(`/api/v1/bi/${sceneId}/preview-url`);
    // response已经是后端返回的完整对象 {"code": "0000", "data": {"url": ...}}
    return response.data.url;
  } catch (error) {
    console.error('获取BI预览URL失败:', error);
    throw error;
  }
}

/**
 * 导出BI场景快照
 */
export async function exportBISnapshot(sceneId: string, format: string = 'png') {
  try {
    const response = await post(`/api/v1/bi/${sceneId}/snapshot`, { format });
    // 拦截器已经返回了处理后的数据，不需要再取 .data
    return response;
  } catch (error) {
    console.error('导出BI快照失败:', error);
    throw error;
  }
}

/**
 * 下载BI场景快照
 */
export async function downloadBISnapshot(sceneId: string): Promise<void> {
  try {
    const response = await fetch(`/api/v1/bi/${sceneId}/snapshot/download`, {
      method: 'GET',
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('下载失败');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `bi_snapshot_${sceneId}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('下载BI快照失败:', error);
    throw error;
  }
}

/**
 * 获取数据集预览
 */
export async function getDatasetPreview(datasetId: string, limit: number = 100) {
  try {
    const response = await get(`/api/v1/bi/datasets/${datasetId}/preview`, { params: { limit } });
    return response.data;
  } catch (error) {
    console.error('获取数据集预览失败:', error);
    throw error;
  }
}

/**
 * 获取BI场景详情
 */
export async function getBISceneDetail(sceneId: string, params?: {
  training_id?: number;
  classroom_id?: number;
  student_id?: number;
}) {
  try {
    const response = await get(`/api/v1/bi/${sceneId}/detail`, params);
    return response.data;
  } catch (error) {
    console.error('获取BI场景详情失败:', error);
    throw error;
  }
}

// AI机器学习实训相关API

/**
 * 运行AI管道
 */
export async function runAIPipeline(pipelineId: string, pipelineData: PipelineDAG) {
  try {
    const response = await post(`/api/v1/ai/${pipelineId}/run`, pipelineData);
    return response.data;
  } catch (error) {
    console.error('运行AI管道失败:', error);
    throw error;
  }
}

/**
 * 获取AI运行日志
 */
export async function getAIRunLogs(runId: string) {
  try {
    const response = await get(`/api/v1/ai/${runId}/logs`);
    // response已经是后端返回的完整对象 {"code": "0000", "data": {"logs": [...]}}
    return response.data.logs;
  } catch (error) {
    console.error('获取AI运行日志失败:', error);
    return [];
  }
}

/**
 * 获取已保存的AI管道
 */
export async function getSavedAIPipeline(pipelineId: string): Promise<PipelineDAG | null> {
  try {
    const response = await get(`/api/v1/ai/${pipelineId}/pipeline`);
    const data = response.data || response;
    if (data && Array.isArray(data.nodes) && data.nodes.length > 0) {
      return {
        nodes: data.nodes,
        edges: Array.isArray(data.edges) ? data.edges : []
      };
    }
    return null;
  } catch (error) {
    console.error('获取已保存AI管道失败:', error);
    return null;
  }
}

/**
 * 保存AI管道
 */
export async function saveAIPipeline(pipelineId: string, pipelineData: PipelineDAG) {
  try {
    const response = await post(`/api/v1/ai/${pipelineId}/save`, pipelineData);
    return response.data;
  } catch (error) {
    console.error('保存AI管道失败:', error);
    throw error;
  }
}

/**
 * 停止AI管道运行
 */
export async function stopAIRun(runId: string) {
  try {
    const response = await post(`/api/v1/ai/${runId}/stop`);
    return response;
  } catch (error) {
    console.error('停止AI运行失败:', error);
    throw error;
  }
}

// ==================== AI模型库相关API ====================

/**
 * AI模型列表项
 */
export interface AIModelListItem {
  id: string;
  name: string;
  type: string;
  algorithm: string;
  description: string;
  created_at: string;
}

/**
 * 获取AI模型列表
 */
export async function getModelList(): Promise<AIModelListItem[]> {
  try {
    const response = await get('/api/v1/ai/models');
    if (response.code === '0000') {
      if (Array.isArray(response.data)) {
        return response.data;
      }
      return response.data?.models || [];
    }
    return [];
  } catch (error) {
    console.error('获取模型列表失败:', error);
    return [];
  }
}

/**
 * 保存AI模型
 */
export interface SaveModelRequest {
  name: string;
  type: string;
  algorithm: string;
  description: string;
  pipeline: PipelineDAG;
}

export async function saveModel(data: SaveModelRequest): Promise<boolean> {
  try {
    const response = await post('/api/v1/ai/models', data);
    return response.code === '0000';
  } catch (error) {
    console.error('保存模型失败:', error);
    return false;
  }
}

/**
 * 删除AI模型
 */
export async function deleteModel(modelId: string): Promise<boolean> {
  try {
    const response = await del(`/api/v1/ai/models/${modelId}`);
    return response.code === '0000';
  } catch (error) {
    console.error('删除模型失败:', error);
    return false;
  }
}

/**
 * 获取AI模型详情
 */
export async function getModelDetail(modelId: string): Promise<AIModelDetail | null> {
  try {
    const response = await get(`/api/v1/ai/models/${modelId}`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('获取模型详情失败:', error);
    return null;
  }
}

/**
 * 更新AI模型
 */
export async function updateModel(modelId: string, data: SaveModelRequest): Promise<boolean> {
  try {
    const response = await put(`/api/v1/ai/models/${modelId}`, data);
    return response.code === '0000';
  } catch (error) {
    console.error('更新模型失败:', error);
    return false;
  }
}

/**
 * 单步执行Pipeline节点
 */
export async function executeSingleStep(
  pipelineId: string,
  nodeId: string,
  inputData?: Record<string, unknown>,
  parameters?: Record<string, unknown>
): Promise<SingleStepResult | null> {
  try {
    const response = await post(`/api/v1/ai/${pipelineId}/single-step`, {
      node_id: nodeId,
      input_data: inputData || {},
      parameters: parameters || {}
    });
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('单步执行失败:', error);
    return null;
  }
}

/**
 * 获取Pipeline执行洞察
 */
export async function getPipelineInsights(runId: string): Promise<PipelineInsight | null> {
  try {
    const response = await get(`/api/v1/ai/${runId}/insights`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('获取洞察数据失败:', error);
    return null;
  }
}

// Jupyter编码式实训相关API

/**
 * 启动Jupyter环境
 */
export async function launchJupyterEnvironment(trainingId: string): Promise<LaunchEnvironmentResponse> {
  try {
    const response = await get(`/api/v1/jupyter/${trainingId}/launch`);
    return response.data;
  } catch (error) {
    console.error('启动Jupyter环境失败:', error);
    throw error;
  }
}

/**
 * 启动或恢复课堂实训环境 (支持 CODING/JUPYTER 和 BI/DATA_ANALYSIS 多态)
 */
export async function launchClassroomTraining(
  trainingId: string | number,
  classroomId: string | number,
  trainingType: string,
  studentId: string | number
): Promise<any> {
  try {
    if (trainingType === 'CODING' || trainingType === 'JUPYTER') {
      const response = await get(
        `/api/v1/jupyter/${trainingId}/launch?student_id=${studentId}&classroom_id=${classroomId}`
      );
      return response;
    }
    
    const response = await post(
      `/api/v1/trainings/${trainingId}/launch?classroom_id=${classroomId}&training_type=${trainingType}&student_id=${studentId}`,
      null,
      { timeout: 60000 }
    );
    // request.ts loader will handle JSON and standard code='0000' logic
    return response;
  } catch (error) {
    console.error('启动课堂实训失败:', error);
    throw error;
  }
}

/**
 * 提交课堂实训作业/进度
 */
export async function submitClassroomTraining(
  classroomId: number | string,
  trainingId: number | string,
  studentId: number | string,
  data: any
): Promise<any> {
  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/trainings/${trainingId}/submission`, {
      student_id: studentId,
      ...data
    });
    return response;
  } catch (error) {
    console.error('提交课堂实训失败:', error);
    throw error;
  }
}

/**
 * 查询环境状态 (支持轮询 Cloud SDK 异步创建结果)
 */
export async function queryEnvironmentStatus(
  trainingId: string | number,
  studentId: string | number
): Promise<any> {
  try {
    return await get(`/api/v1/environments/query?training_id=${trainingId}&user_id=${studentId}`);
  } catch (error) {
    console.error('查询环境状态失败:', error);
    throw error;
  }
}

/**
 * 延长环境时间
 */
export async function extendEnvironmentTime(envId: string, request: ExtendTimeRequest) {
  try {
    const response = await post(`/api/v1/jupyter/${envId}/extend-time`, request);
    return response;
  } catch (error) {
    console.error('延长环境时间失败:', error);
    throw error;
  }
}

/**
 * 重置环境
 */
export async function resetEnvironment(envId: string) {
  try {
    const response = await post(`/api/v1/jupyter/${envId}/reset-env`);
    return response;
  } catch (error) {
    console.error('重置环境失败:', error);
    throw error;
  }
}

/**
 * 重置代码仓库
 */
export async function resetCodeRepository(envId: string) {
  try {
    const response = await post(`/api/v1/jupyter/${envId}/reset-repo`);
    return response.data;
  } catch (error) {
    console.error('重置代码仓库失败:', error);
    throw error;
  }
}

/**
 * 保存Notebook
 */
export async function saveNotebook(envId: string, checkpoint: NotebookCheckpoint) {
  try {
    const response = await post(`/api/v1/jupyter/${envId}/save`, checkpoint);
    return response.data;
  } catch (error) {
    console.error('保存Notebook失败:', error);
    throw error;
  }
}

// 通用功能

/**
 * 获取用户项目进度
 */
export async function getUserProjectProgress(projectId: string, userId: string) {
  try {
    const response = await get(`/api/v1/projects/${projectId}/users/${userId}/progress`);
    return response.data;
  } catch (error) {
    console.error('获取用户项目进度失败:', error);
    return null;
  }
}

/**
 * 更新用户项目进度
 */
export async function updateUserProjectProgress(
  projectId: string, 
  userId: string, 
  progress: Partial<WorkflowState>
) {
  try {
    const response = await put(`/api/v1/projects/${projectId}/users/${userId}/progress`, progress);
    return response.data;
  } catch (error) {
    console.error('更新用户项目进度失败:', error);
    throw error;
  }
}

// ==================== 实训课程管理相关接口 ====================

/**
 * 获取实训环境列表
 * @returns 实训环境列表
 */
export async function fetchTrainingEnvironments(): Promise<TrainingEnvironment[]> {
  try {
    const response = await get('/api/v1/trainings/environments');
    return response.data.list || [];
  } catch (error) {
    console.error('获取实训环境列表失败:', error);
    return [];
  }
}

/**
 * 创建新实训课程
 * @param training 实训课程数据
 * @param creatorId 创建者ID
 * @returns 创建的实训课程
 */
export async function createTraining(training: NewTraining, creatorId: number): Promise<{ training_id: number; title: string } | null> {
  try {
    // 转换实训类型
    const typeMap: Record<string, string> = {
      'bi': 'DRAG_DROP',
      'ai': 'DRAG_DROP',  // AI也使用拖拽式
      'jupyter': 'CODING'
    };
    
    // 转换数据格式以匹配后端API
    const requestData = {
      title: training.name,
      intro: training.intro,
      training_type: typeMap[training.type] || 'DRAG_DROP',
      industry: training.categories?.[0] || '',  // 使用第一个分类作为行业
      difficulty: training.difficulty,
      course_hours: Math.ceil((training.duration || 60) / 45),  // 分钟转课时
      handbook_content: '',  // 初始为空，后续在编辑页面填写
      assignment_nodes: training.type === 'jupyter' ? [] : [
        {
          node_id: 1,
          node_name: '作业节点1',
          use_drag_ai: training.type === 'ai',
          use_drag_bi: training.type === 'bi',
          require_submission: true
        }
      ],
      require_design_files: training.type !== 'jupyter',
      require_experiment_report: true,
      environment_id: training.environment,
      environment_config: training.type === 'jupyter' ? {
        storage_limit: '1Gi',
        memory_limit: '2Gi',
        cpu_limit: '1'
      } : undefined
    };
    
    console.log('createTraining requestData:', requestData);
    const response = await post(`/api/v1/trainings/custom-trainings?creator_id=${creatorId}`, requestData);
    console.log('createTraining raw response:', response);
    console.log('createTraining response.training_id:', response.training_id);

    if (response && response.training_id) {
      return response;
    }
    return null;
  } catch (error) {
    console.error('创建实训课程失败:', error);
    return null;
  }
}

/**
 * 获取我创建的实训课程列表
 * @returns 实训课程列表
 */
export async function fetchMyTrainings(): Promise<TrainingItem[]> {
  try {
    const response = await get('/api/v1/trainings/my-trainings');
    console.log('fetchMyTrainings raw response:', response);
    console.log('fetchMyTrainings response.list:', response.list);
    return response.list || [];
  } catch (error) {
    console.error('获取我创建的实训课程列表失败:', error);
    return [];
  }
}

/**
 * 删除实训课程
 * @param id 实训课程ID
 * @returns 是否删除成功
 */
export async function deleteTrainingById(id: string): Promise<boolean> {
  try {
    const response = await del(`/api/v1/trainings/detail/${id}`);
    // 响应拦截器已经处理了code检查，这里只需要检查响应是否存在
    return response !== undefined;
  } catch (error) {
    console.error('删除实训课程失败:', error);
    return false;
  }
}

/**
 * 更新实训课程状态
 * @param id 实训课程ID
 * @param status 新状态
 * @param statusDetail 状态详情（可选）
 * @returns 是否更新成功
 */
export async function updateTrainingStatusById(id: string, status: TrainingStatusType, statusDetail?: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/${id}/status`, {
      status,
      status_detail: statusDetail
    });
    return response.code === '0000';
  } catch (error) {
    console.error('更新实训课程状态失败:', error);
    return false;
  }
}

/**
 * 开启编辑模式
 * @param trainingId 实训课程ID
 * @returns 是否成功
 */
export async function startEditModeTraining(trainingId: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/edit`);
    return response.code === '0000';
  } catch (error) {
    console.error('开启编辑模式失败:', error);
    return false;
  }
}

/**
 * 撤销编辑
 * @param trainingId 实训课程ID
 * @returns 是否成功
 */
export async function cancelEditTraining(trainingId: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/cancel-edit`);
    return response.code === '0000';
  } catch (error) {
    console.error('撤销编辑失败:', error);
    return false;
  }
}

/**
 * 下架实训课程
 * @param trainingId 实训课程ID
 * @returns 是否成功
 */
export async function unpublishTraining(trainingId: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/detail/${trainingId}/unpublish`);
    // 响应拦截器已经处理了code检查，这里只需要检查响应是否存在
    return response !== undefined;
  } catch (error) {
    console.error('下架实训课程失败:', error);
    return false;
  }
}

/**
 * 申请公开发布
 * @param trainingId 实训课程ID
 * @returns 是否成功
 */
export async function applyPublicPublishTraining(trainingId: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/apply-public`);
    return response.code === '0000';
  } catch (error) {
    console.error('申请公开发布失败:', error);
    return false;
  }
}

/**
 * 撤销公开发布申请
 * @param trainingId 实训课程ID
 * @param reason 撤销原因
 * @returns 是否成功
 */
export async function cancelPublicPublishTraining(trainingId: string, reason: string): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/cancel-public`, {
      reason
    });
    return response.code === '0000';
  } catch (error) {
    console.error('撤销公开发布申请失败:', error);
    return false;
  }
}

/**
 * 发布新版本
 * @param trainingId 实训课程ID
 * @param versionData 版本数据
 * @returns 是否成功
 */
export interface TrainingVersionData {
  versionType: 'major' | 'minor';
  updateNotes: string;
  publishType: 'personal' | 'public';
}

export async function publishNewTrainingVersion(trainingId: string, versionData: TrainingVersionData): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/custom-trainings/${trainingId}/publish-version`, versionData);
    // 响应拦截器已经处理了code检查，这里只需要检查是否有id返回
    return response && response.id;
  } catch (error) {
    console.error('发布新版本失败:', error);
    return false;
  }
}

/**
 * 发布实训课程
 * @param trainingId 实训课程ID
 * @param publishData 发布数据
 * @returns 是否发布成功
 */
export interface TrainingPublishRequest {
  visibility: 'public' | 'private';
}

export async function publishTraining(trainingId: number, publishData: TrainingPublishRequest): Promise<boolean> {
  try {
    const response = await post(`/api/v1/trainings/custom-trainings/${trainingId}/publish`, publishData);
    console.log('publishTraining response:', response);
    // 响应拦截器已经处理了code检查，这里只需要检查是否有id返回
    return response && response.id;
  } catch (error) {
    console.error('发布实训课程失败:', error);
    return false;
  }
}

// ==================== 实训资源库相关接口 ====================

export interface TrainingLibraryQueryParams {
  keyword?: string;
  training_type?: 'CODING' | 'DRAG_DROP';
  difficulty?: string;
  tags?: string[];
  is_preset?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface TrainingLibraryItem {
  id: number;
  title: string;
  intro: string;
  training_type: 'CODING' | 'DRAG_DROP';
  difficulty: string;
  industry: string;
  course_hours: number;
  dataset_count: number;
  tags: string[];
  is_preset: boolean;
  creator_name?: string;
  created_at: string;
  updated_at: string;
}

export interface TrainingLibraryResponse {
  list: TrainingLibraryItem[];
  total: number;
  page: number;
  page_size: number;
}

/**
 * 获取实训资源库列表
 * @param params 查询参数
 * @returns 实训资源库列表
 */
export async function getTrainingLibrary(params: TrainingLibraryQueryParams = {}): Promise<TrainingLibraryResponse> {
  try {
    console.log('[FRONTEND] getTrainingLibrary called with params:', params);
    // 直接传递 params，因为 get 函数已经会将其作为 axios 的 params 配置
    const response = await get('/api/v1/trainings/library', params);
    console.log('[FRONTEND] getTrainingLibrary raw response:', response);
    console.log('[FRONTEND] getTrainingLibrary response.data:', response.data);
    return response.data;
  } catch (error) {
    console.error('[FRONTEND] 获取实训资源库失败:', error);
    throw error;
  }
}

/**
 * 获取实训资源库详情
 * @param trainingId 实训ID
 * @returns 实训详情
 */
export async function getTrainingLibraryDetail(trainingId: number) {
  try {
    const response = await get(`/api/v1/trainings/library/${trainingId}`);
    return response.data;
  } catch (error) {
    console.error('获取实训资源库详情失败:', error);
    throw error;
  }
}

/**
 * 添加实训到课堂
 * @param trainingId 实训ID
 * @param classroomId 课堂ID
 * @param params 添加参数
 * @returns 添加结果
 */
export interface AddTrainingToClassroomParams {
  start_time: string;
  end_time: string;
  allow_late_submission?: boolean;
  late_submission_days?: number;
  source_type?: 'training' | 'practice';  // R3 P0 #6: practice (XQ01) 走 classroom_courses
}

export async function addTrainingToClassroomFromLibrary(
  trainingId: number,
  classroomId: number,
  params: AddTrainingToClassroomParams
) {
  try {
    const response = await post(
      `/api/v1/trainings/library/${trainingId}/add-to-classroom/${classroomId}`,
      params
    );
    return response.data;
  } catch (error) {
    console.error('添加实训到课堂失败:', error);
    throw error;
  }
}

/**
 * 获取课堂实训列表
 * @param classroomId 课堂ID
 * @param params 查询参数
 * @returns 课堂实训列表
 */
export async function getClassroomTrainings(classroomId: number, params: { teacher_id?: number; student_id?: number } = {}) {
  try {
    const response = await get(`/api/v1/classrooms/${classroomId}/trainings`, { params });
    return response.data;
  } catch (error) {
    console.error('获取课堂实训列表失败:', error);
    throw error;
  }
}

// ==================== 实训会话管理相关接口 ====================

export interface TrainingSessionCreateParams {
  classroom_training_id: number;
  student_id: number;
}

export interface TrainingSessionResponse {
  id: number;
  session_id: string;
  jupyter_url: string;
  container_name: string;
  status: string;
  created_at: string;
  expires_at: string;
}

/**
 * 创建实训会话
 * @param params 创建参数
 * @returns 会话信息
 */
export async function createTrainingSession(params: TrainingSessionCreateParams): Promise<TrainingSessionResponse> {
  try {
    const response = await post('/api/v1/training-sessions', params);
    return response.data;
  } catch (error) {
    console.error('创建实训会话失败:', error);
    throw error;
  }
}

/**
 * 获取实训会话详情
 * @param sessionId 会话ID
 * @param studentId 学生ID
 * @returns 会话详情
 */
export async function getTrainingSession(sessionId: number, studentId: number) {
  try {
    const response = await get(`/api/v1/training-sessions/${sessionId}`, {
      params: { student_id: studentId }
    });
    return response.data;
  } catch (error) {
    console.error('获取实训会话详情失败:', error);
    throw error;
  }
}

/**
 * 实训会话心跳
 * @param sessionId 会话ID
 * @param studentId 学生ID
 * @returns 心跳结果
 */
export async function trainingSessionHeartbeat(sessionId: number, studentId: number) {
  try {
    const response = await post(`/api/v1/training-sessions/${sessionId}/heartbeat`, {}, {
      params: { student_id: studentId }
    });
    return response.data;
  } catch (error) {
    console.error('实训会话心跳失败:', error);
    throw error;
  }
}

/**
 * 更新实训进度
 * @param sessionId 会话ID
 * @param studentId 学生ID
 * @param progress 进度信息
 * @returns 更新结果
 */
export interface TrainingProgressParams {
  progress_percentage: number;
  current_step: string;
  completed_tasks: string[];
}

export async function updateTrainingProgress(
  sessionId: number,
  studentId: number,
  progress: TrainingProgressParams
) {
  try {
    const response = await put(`/api/v1/training-sessions/${sessionId}/progress`, progress, {
      params: { student_id: studentId }
    });
    return response.data;
  } catch (error) {
    console.error('更新实训进度失败:', error);
    throw error;
  }
}

/**
 * 提交实训结果
 * @param sessionId 会话ID
 * @param studentId 学生ID
 * @param submission 提交内容
 * @returns 提交结果
 */
export interface TrainingSubmissionParams {
  submission_type: 'notebook' | 'file' | 'text';
  notebook_content?: string;
  file_urls?: string[];
  text_content?: string;
  summary: string;
}

export async function submitTraining(
  sessionId: number,
  studentId: number,
  submission: TrainingSubmissionParams
) {
  try {
    const response = await post(`/api/v1/training-sessions/${sessionId}/submit`, submission, {
      params: { student_id: studentId }
    });
    return response.data;
  } catch (error) {
    console.error('提交实训结果失败:', error);
    throw error;
  }
}

/**
 * 关闭实训会话
 * @param sessionId 会话ID
 * @param studentId 学生ID
 * @returns 关闭结果
 */
export async function closeTrainingSession(sessionId: number, studentId: number) {
  try {
    const response = await post(`/api/v1/training-sessions/${sessionId}/close`, {}, {
      params: { student_id: studentId }
    });
    return response.data;
  } catch (error) {
    console.error('关闭实训会话失败:', error);
    throw error;
  }
}

/**
 * 初始化实训资源（管理员功能）
 * @returns 初始化结果
 */
export async function seedTrainingResources() {
  try {
    const response = await post('/api/v1/trainings/seed');
    return response.data;
  } catch (error) {
    console.error('初始化实训资源失败:', error);
    throw error;
  }
}

// ==================== 数据转换工具函数 ====================

/**
 * 转换后端训练类型到前端格式
 * @param backendType 后端类型
 * @returns 前端类型
 */
export function convertTrainingTypeFromBackend(backendType: 'CODING' | 'DRAG_DROP'): 'bi' | 'ai' | 'jupyter' {
  const typeMap = {
    'DRAG_DROP': 'bi' as const,
    'CODING': 'jupyter' as const
  };
  return typeMap[backendType] || 'bi';
}

/**
 * 转换前端训练类型到后端格式
 * @param frontendType 前端类型
 * @returns 后端类型
 */
export function convertTrainingTypeToBackend(frontendType: 'bi' | 'ai' | 'jupyter'): 'CODING' | 'DRAG_DROP' {
  const typeMap = {
    'bi': 'DRAG_DROP' as const,
    'ai': 'DRAG_DROP' as const,
    'jupyter': 'CODING' as const
  };
  return typeMap[frontendType] || 'DRAG_DROP';
}

// ==================== P2 实训详情页面 API ====================

/**
 * 获取课堂内实训详情（包括学生进度）
 * @param classroomId 课堂ID
 * @param trainingId 实训ID
 * @param userId 用户ID
 * @param userRole 用户角色
 */
export async function getClassroomTrainingDetails(
  classroomId: number,
  trainingId: number,
  userId: number,
  userRole: 'teacher' | 'student'
) {
  try {
    const params = userRole === 'teacher' 
      ? { teacher_id: userId }
      : { student_id: userId };
    
    const response = await get(
      `/api/v1/classrooms/${classroomId}/trainings/${trainingId}/details`,
      params
    );
    return response.data;
  } catch (error) {
    console.error('获取实训详情失败:', error);
    throw error;
  }
}

/**
 * 启动实训编辑器环境
 * @param trainingId 实训ID
 * @param classroomId 课堂ID
 * @param trainingType 实训类型
 */
export async function launchTrainingEnvironment(
  trainingId: number,
  classroomId: number,
  trainingType: string
) {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/launch`, {
      classroom_id: classroomId,
      training_type: trainingType
    });
    return response.data;
  } catch (error) {
    console.error('启动实训环境失败:', error);
    throw error;
  }
}

/**
 * 提交实训作业
 * @param trainingId 实训ID
 * @param classroomTrainingId 课堂实训关联ID
 * @param notes 提交说明
 * @param files 上传的文件
 */
export async function submitTrainingAssignment(
  trainingId: number,
  classroomTrainingId: number,
  notes: string = '',
  files: any[] = []
) {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/submit`, {
      classroom_training_id: classroomTrainingId,
      notes,
      files
    });
    return response.data;
  } catch (error) {
    console.error('提交实训作业失败:', error);
    throw error;
  }
}

/**
 * 克隆实训课程
 * @param trainingId 实训课程ID
 * @returns 复制后的实训课程ID
 */
export async function cloneTraining(trainingId: string): Promise<{ id: number } | null> {
  try {
    const response = await post(`/api/v1/trainings/${trainingId}/clone`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('克隆实训课程失败:', error);
    return null;
  }
}
