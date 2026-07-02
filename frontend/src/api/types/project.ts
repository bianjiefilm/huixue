/**
 * 项目接口类型定义
 */

// 项目过滤参数
export interface ProjectFilter {
  keyword?: string;
  industry?: string;
  trainingType?: string;
  difficulty?: string;
  page?: number;
  pageSize?: number;
  isMLProject?: boolean;
  
  // 兼容原有字段
  direction?: string;
  category?: string;
  level?: string;
}

// 项目基本信息
export interface Project {
  id: string;
  title: string;
  description: string;
  // 支持两种类型的图片字段名
  coverImage?: string;
  cover?: string;
  
  // 支持组件类型和字符串类型
  industry: {
    id: string;
    name: string;
  } | string;
  
  // 支持组件类型和字符串类型
  trainingType: {
    id: string;
    name: string;
  } | string;
  
  // 支持组件类型和字符串类型
  difficulty: {
    id: string;
    name: string;
  } | string;
  
  // 流行度/参与度
  enrollCount?: number;
  participants?: number;
  popularity?: number;
  
  duration: string;
  tags: string[];
  createdAt: string;
  isPopular?: boolean;
  isNew?: boolean;
  
  // 原始项目还有这些额外字段
  category?: string;
  direction?: string;
  level?: string;
  author?: string;
  authorAvatar?: string;
}

// 项目详情
export interface ProjectDetail extends Project {
  goals: string[];
  requirements: string[];
  manualSections: ManualSection[];
  challenges: Challenge[];
  isMLProject: boolean;
  environment_type: 'jupyter' | 'visual' | 'ml' | 'code';
  designer_type?: 'BI' | 'AI' | 'JUPYTER' | null;
  content?: string;
  objectives?: string[];
  syllabus?: Array<{
    title: string;
    items: string[];
  }>;
  resources?: Array<{
    title: string;
    type: string;
    url: string;
  }>;
  steps?: Array<{
    title: string;
    description: string;
    tasks: string[];
  }>;
  comments?: Array<{
    id: string;
    user: string;
    avatar: string;
    content: string;
    createdAt: string;
    likes: number;
  }>;
}

// 操作手册章节
export interface ManualSection {
  id: string;
  title: string;
  content: string;
}

// 挑战
export interface Challenge {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  type: string;
  points: number;
  status?: 'not_started' | 'in_progress' | 'completed';
}

// 项目列表响应
export interface ProjectsResponse {
  projects: Project[];
  total: number;
  industries: Array<{ id: string; name: string }>;
  trainingTypes: Array<{ id: string; name: string }>;
  difficultyLevels: Array<{ id: string; name: string }>;
}

// 数据集
export interface Dataset {
  id: number;
  name: string;
  path: string;
  size: number; // 以字节为单位
  description: string;
}

// 工作流状态
export interface WorkflowState {
  nodes: Array<{
    id: string;
    type: string;
    position: { x: number; y: number };
    data: any;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
  }>;
  lastUpdated: string;
  [key: string]: any;
}

// 用户项目进度
export interface UserProjectProgress {
  userId: string;
  projectId: string;
  status: 'not_started' | 'in_progress' | 'completed';
  progress: number; // 0-100
  startTime: string;
  lastAccessTime: string;
  challengesCompleted: number;
  totalChallenges: number;
  currentStep: number;
}

// 将项目添加到课堂的请求
export interface AddProjectToClassroomRequest {
  id: string;
  title: string;
  description: string;
  industry: {
    id: string;
    name: string;
  };
  trainingType: {
    id: string;
    name: string;
  };
  startDate?: string;
  endDate?: string;
  isRequired?: boolean;
}

// 将项目添加到课堂的响应
export interface AddProjectToClassroomResponse {
  id: string;
  name: string;
  type: 'training';
  status: string;
  startDate: string;
  endDate: string;
  createTime: string;
  learningCount: number;
  completedCount: number;
  notStartedCount: number;
  industry: string;
  trainingType: string;
  introduction: string;
  order: number;
  isRequired: boolean;
}

// BI场景JSON
export interface SceneJSON {
  nodes: any[];
  links: any[];
  props: {
    title?: string;
    theme?: string;
    backgroundColor?: string;
  };
}

// AI管道DAG
export interface DagNode {
  id: string;
  type: string;
  label: string;
  config: Record<string, any>;
  position: { x: number; y: number };
}

export interface DagEdge {
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface PipelineDAG {
  nodes: DagNode[];
  edges: DagEdge[];
}

// Notebook检查点
export interface NotebookCheckpoint {
  path: string;
  content: string;
  timestamp?: string;
}

// 环境启动响应
export interface LaunchEnvironmentResponse {
  envId: string;
  url: string;
  remainingTime: number; // 分钟
}

// 延时请求
export interface ExtendTimeRequest {
  minutes: number;
}

// 数据集文件
export interface DatasetFile {
  name: string;
  path: string;
  size: number;
  type: string;
}

// 历史记录类型
export type HistoryActionType = 'add_node' | 'delete_node' | 'add_edge' | 'delete_edge' | 'move_node';

export interface HistoryEntry {
  id: string;
  action: HistoryActionType;
  timestamp: number;
  description: string;
  // 备份的数据
  nodes: DagNode[];
  edges: DagEdge[];
}

export interface HistoryState {
  undoStack: HistoryEntry[];
  redoStack: HistoryEntry[];
  maxHistorySize: number;
}

// AI模型
export interface AIModel {
  id: string;
  name: string;
  type: string;
  algorithm: string;
  description: string;
  created_at: string;
  thumbnail?: string;
}

// Pipeline洞察数据
export interface PipelineInsight {
  run_id: string;
  total_nodes: number;
  executed_nodes: number;
  failed_nodes: number;
  execution_time: number;
  node_insights: NodeInsight[];
  model_insights: ModelInsights;
}

export interface NodeInsight {
  node_id: string;
  node_type: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  execution_time: number;
  input_rows: number;
  output_rows: number;
  memory_usage: number;
  cpu_usage: number;
}

export interface ModelInsights {
  accuracy?: number;
  loss?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  auc?: number;
  training_samples: number;
  validation_samples: number;
  test_samples: number;
}

// AI模型详情
export interface AIModelDetail {
  id: string;
  name: string;
  model_type: string;
  description: string;
  tags: string[];
  config: Record<string, unknown>;
  version: number;
  is_published: boolean;
  user_id: number;
  created_at: string;
  updated_at: string;
}

// 单步执行结果
export interface SingleStepResult {
  execution_id?: string;
  run_id: string;
  pipeline_id: string;
  node_id: string;
  status: string;
  started_at: string;
  completed_at: string;
  duration_ms: number;
  output: {
    data: Record<string, unknown>;
    metrics: {
      execution_time: number;
      memory_usage: string;
      cpu_usage: string;
    };
  };
  logs: string[];
} 
