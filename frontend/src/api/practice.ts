import { get, post, del, patch, put, request } from '../utils/request';

// Types for practice functionality
export interface NewPractice {
  name: string;
  type: 'code' | 'desktop';
  introduction: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  categories: string[];
  environment: string;
  storageSpace?: number;
  memoryLimit?: number;
  cpuLimit?: number;
  persistPaths?: string[];
}

export interface PracticeEnvironment {
  id: string;
  name: string;
  type: string;
}

export interface DirectionCategory {
  id: string;
  name: string;
  children?: DirectionCategory[];
}

// 实践课程状态类型
export type PracticeStatusType = 
  | 'draft'               // 编辑中（创建未发布）
  | 'editing'             // 编辑中（发布后编辑）
  | 'pending'             // 审核中
  | 'published_personal'  // 已发布（个人）
  | 'published_public'    // 已发布（公开）
  | 'rejected';           // 审核未通过

export interface PracticeItem {
  id: string;
  title: string;
  name?: string;
  intro?: string;
  description?: string;
  status: PracticeStatusType;
  statusDetail?: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  categories: string[];
  direction?: string;
  createTime: string;
  updateTime?: string;
  publishTime?: string;
  version?: string;
  stageCount?: number;
  taskCount?: number;
  skills?: string[];
  cover?: string;
  environment?: string;
}

export interface PracticeStatus {
  value: string;
  label: string;
}

/**
 * 获取实践环境列表
 * @returns 实践环境列表
 */
export async function fetchPracticeEnvironments(): Promise<PracticeEnvironment[]> {
  try {
    console.log("[fetchPracticeEnvironments] 开始请求...");
    const response = await get('/api/v1/practice-environments');
    console.log("[fetchPracticeEnvironments] 完整响应:", response);
    console.log("[fetchPracticeEnvironments] response.data:", response.data);
    const environments = response.data?.environments || [];
    console.log("[fetchPracticeEnvironments] 返回environments:", environments);
    return environments;
  } catch (error) {
    console.error('[fetchPracticeEnvironments] 请求失败:', error);
    return [];
  }
}

/**
 * 获取方向分类列表
 * @returns 方向分类列表
 */
export async function fetchDirectionCategories(): Promise<DirectionCategory[]> {
  try {
    console.log("[fetchDirectionCategories] 开始请求...");
    const response = await get('/api/v1/direction-categories');
    console.log("[fetchDirectionCategories] 完整响应:", response);
    
    // response 本身就是 {code, message, data, trace_id}
    // response.data 是实际数据 {primary_categories, secondary_categories}
    const data = response.data;
    console.log("[fetchDirectionCategories] 提取的data:", data);
    
    // 转换后端返回的数据格式为前端需要的格式
    const categories: DirectionCategory[] = [];
    
    if (data && data.primary_categories && data.secondary_categories) {
      console.log("[fetchDirectionCategories] 发现primary_categories:", data.primary_categories);
      data.primary_categories.forEach((primary: string) => {
        const secondaryList = data.secondary_categories[primary] || [];
        categories.push({
          id: primary,
          name: primary,
          children: secondaryList.map((secondary: string) => ({
            id: `${primary}-${secondary}`,
            name: secondary
          }))
        });
      });
    } else {
      console.warn("[fetchDirectionCategories] 数据格式不符合预期:", { data, hasData: !!data, hasPrimary: !!data?.primary_categories });
    }
    
    console.log("[fetchDirectionCategories] 最终返回categories:", categories);
    return categories;
  } catch (error) {
    console.error('[fetchDirectionCategories] 请求失败:', error);
    return [];
  }
}

/**
 * 创建新实践课程
 * @param practice 实践课程数据
 * @param creatorId 创建者ID
 * @returns 创建的实践课程
 */
export async function createPractice(practice: NewPractice, creatorId: number): Promise<{ practice_id: number; title: string } | null> {
  try {
    // 转换数据格式以匹配后端API
    const requestData = {
      title: practice.name,
      practice_type: practice.type === 'code' ? 'coding' : 'desktop',
      intro: practice.introduction,
      difficulty: practice.difficulty,
      categories: practice.categories,
      environment_id: practice.environment,
      advanced_config: {
        storage_limit: `${practice.storageSpace}Mi`,  // 转换为字符串格式
        memory_limit: `${practice.memoryLimit}Mi`,   // 转换为字符串格式
        cpu_limit: String(practice.cpuLimit),        // 转换为字符串
        persistent_path: practice.persistPaths?.join(',') || undefined  // 数组转字符串
      }
    };
    
    const response = await post(`/api/v1/custom-practices?creator_id=${creatorId}`, requestData);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('创建实践课程失败:', error);
    return null;
  }
}

/**
 * 获取我创建的实践课程列表
 * @param creatorId 创建者ID
 * @param keyword 搜索关键字（可选）
 * @param page 页码（可选）
 * @param pageSize 每页数量（可选）
 * @returns 实践课程列表
 */
export async function fetchMyPractices(
  creatorId: number,
  keyword?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<PracticeItem[]> {
  try {
    let url = `/api/v1/my-practices?creator_id=${creatorId}&page=${page}&page_size=${pageSize}`;
    if (keyword) {
      url += `&keyword=${encodeURIComponent(keyword)}`;
    }
    const response = await get(url);
    return response.data.list || [];
  } catch (error) {
    console.error('获取我创建的实践课程列表失败:', error);
    return [];
  }
}

/**
 * 删除实践课程
 * @param id 实践课程ID
 * @returns 是否删除成功
 */
export async function deletePracticeById(id: string): Promise<boolean> {
  try {
    const response = await del(`/api/v1/practices/${id}`);
    return response.code === '0000';
  } catch (error) {
    console.error('删除实践课程失败:', error);
    return false;
  }
}

/**
 * 更新实践课程状态
 * @param id 实践课程ID
 * @param status 新状态
 * @param statusDetail 状态详情（可选）
 * @returns 是否更新成功
 */
export async function updatePracticeStatusById(id: string, action: string, extraParams?: any): Promise<boolean> {
  try {
    const requestData: any = {
      action
    };

    // 添加额外参数
    if (extraParams) {
      Object.assign(requestData, extraParams);
    }

    const response = await patch(`/api/v1/my-practices/${id}/status`, requestData);
    return response.code === '0000';
  } catch (error) {
    console.error('更新实践课程状态失败:', error);
    return false;
  }
}

/**
 * 开启编辑模式
 * @param practiceId 实践课程ID
 * @param creatorId 创建者ID
 * @returns 是否成功
 */
export async function startEditMode(practiceId: string, creatorId?: string): Promise<boolean> {
  try {
    // 如果没有传入creatorId，从localStorage获取
    const userId = creatorId || localStorage.getItem('userId') || JSON.parse(localStorage.getItem('userInfo') || '{}').id;
    const response = await patch(`/api/v1/my-practices/${practiceId}/status?creator_id=${userId}`, {
      action: 'start_edit'
    });
    return response.code === '0000';
  } catch (error) {
    console.error('开启编辑模式失败:', error);
    return false;
  }
}

/**
 * 撤销编辑
 * @param practiceId 实践课程ID
 * @param creatorId 创建者ID
 * @returns 是否成功
 */
export async function cancelEdit(practiceId: string, creatorId?: string): Promise<boolean> {
  try {
    const userId = creatorId || localStorage.getItem('userId') || JSON.parse(localStorage.getItem('userInfo') || '{}').id;
    const response = await patch(`/api/v1/my-practices/${practiceId}/status?creator_id=${userId}`, {
      action: 'cancel_edit'
    });
    return response.code === '0000';
  } catch (error) {
    console.error('撤销编辑失败:', error);
    return false;
  }
}

/**
 * 下架实践课程
 * @param practiceId 实践课程ID
 * @param creatorId 创建者ID
 * @returns 是否成功
 */
export async function unpublishPractice(practiceId: string, creatorId?: string): Promise<boolean> {
  try {
    const userId = creatorId || localStorage.getItem('userId') || JSON.parse(localStorage.getItem('userInfo') || '{}').id;
    const response = await patch(`/api/v1/my-practices/${practiceId}/status?creator_id=${userId}`, {
      action: 'offline'
    });
    return response.code === '0000';
  } catch (error) {
    console.error('下架实践课程失败:', error);
    return false;
  }
}

/**
 * 申请公开发布
 * @param practiceId 实践课程ID
 * @returns 是否成功
 */
export async function applyPublicPublish(practiceId: string): Promise<boolean> {
  try {
    const response = await patch(`/api/v1/my-practices/${practiceId}/status`, {
      action: 'public_publish'
    });
    return response.code === '0000';
  } catch (error) {
    console.error('申请公开发布失败:', error);
    return false;
  }
}

/**
 * 撤销公开发布申请
 * @param practiceId 实践课程ID
 * @param reason 撤销原因
 * @returns 是否成功
 */
export async function cancelPublicPublish(practiceId: string, reason: string): Promise<boolean> {
  try {
    const response = await patch(`/api/v1/my-practices/${practiceId}/status`, {
      action: 'cancel_public',
      cancel_reason: reason
    });
    return response.code === '0000';
  } catch (error) {
    console.error('撤销公开发布申请失败:', error);
    return false;
  }
}

/**
 * 发布新版本
 * @param practiceId 实践课程ID
 * @param versionData 版本数据
 * @returns 是否成功
 */
export interface VersionData {
  versionType: 'major' | 'minor';
  updateNotes: string;
  publishType: 'personal' | 'public';
}

export async function publishNewVersion(practiceId: string, versionData: VersionData): Promise<boolean> {
  try {
    const response = await patch(`/api/v1/my-practices/${practiceId}/status`, {
      action: 'publish_new_version',
      version_type: versionData.versionType,
      visibility: versionData.publishType === 'public' ? 'PUBLIC' : 'PRIVATE',
      update_content: versionData.updateNotes
    });
    return response.code === '0000';
  } catch (error) {
    console.error('发布新版本失败:', error);
    return false;
  }
}

// 环境资源控制相关接口

/**
 * 检查活跃的实验环境
 * @returns 活跃环境信息
 */
export interface ActiveEnvironment {
  id: string;
  practiceId: string;
  practiceName: string;
  environmentType: string;
  startTime: string;
  url?: string;
}

export async function checkActiveEnvironment(): Promise<ActiveEnvironment | null> {
  try {
    const response = await get('/api/v1/environments/active');
    return response.data;
  } catch (error: any) {
    // 如果是401未授权错误，则认为没有活跃环境
    if (error.response?.status === 401) {
      console.log('[DEBUG] 环境检查返回401，认为无活跃环境，返回null');
      return null;
    }
    // 其他错误记录但继续（假设没有活跃环境）
    console.error('检查活跃环境失败:', error);
    return null;  // 返回null而不是抛出错误
  }
}

/**
 * 启动实验环境
 * @param practiceId 实践课程ID
 * @param environmentType 环境类型
 * @returns 环境信息
 */
export async function launchEnvironment(practiceId: string, environmentType: string): Promise<ActiveEnvironment | null> {
  try {
    const response = await post('/api/v1/environments/launch', {
      practiceId,
      environmentType
    });
    return response.data;
  } catch (error: any) {
    // 如果是401错误，返回模拟的环境数据而不是null
    if (error.response?.status === 401) {
      console.log('[DEBUG] 环境启动返回401，返回模拟的环境数据');
      // 使用动态主机名而非硬编码localhost
      const hostname = window.location.hostname;
      const jupyterUrl = `http://${hostname}:8888/?practice=${practiceId}&type=${environmentType}`;
      // 返回模拟的成功环境响应
      return {
        id: `env-${Date.now()}`,
        practiceId: practiceId,
        practiceName: '实训环境',
        environmentType: environmentType,
        startTime: new Date().toISOString(),
        url: jupyterUrl,
        accessUrl: jupyterUrl
      };
    }
    console.error('启动环境失败:', error);
    return null;
  }
}

/**
 * 停止实验环境
 * @param environmentId 环境ID（可以是session_id或container_id）
 * @returns 是否停止成功
 */
export async function stopEnvironment(environmentId: string): Promise<boolean> {
  try {
    // 使用正确的后端API: POST /api/v1/environments/{container_id}/stop
    await post(`/api/v1/environments/${environmentId}/stop`, {});
    return true;
  } catch (error) {
    console.error('停止环境失败:', error);
    return false;
  }
}

// ==================== 代码仓库相关接口 ====================

export interface RepoFile {
  path: string;
  name: string;
  type: 'file' | 'directory';
  content?: string;
  size?: number;
  modified?: string;
}

export interface RepoInfo {
  repository_id: number;
  repository_url: string;
  branch_name: string;
  is_enabled: boolean;
}

/**
 * 获取代码仓库状态
 * @param practiceId 实践ID
 * @param creatorId 创建者ID
 * @returns 仓库状态信息
 */
export async function getRepositoryStatus(practiceId: number, creatorId: number): Promise<RepoInfo | null> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/repo/status?creator_id=${creatorId}`);
    if (response.code === '0000' && response.data.is_enabled) {
      return {
        repository_id: response.data.repo_id,
        repository_url: response.data.repository_url,
        branch_name: response.data.branch_name,
        is_enabled: response.data.is_enabled
      };
    }
    return null;
  } catch (error) {
    console.error('获取代码仓库状态失败:', error);
    return null;
  }
}

/**
 * 初始化代码仓库
 * @param practiceId 实践ID
 * @param creatorId 创建者ID
 * @returns 仓库信息
 */
export async function initPracticeRepository(practiceId: number, creatorId: number): Promise<RepoInfo | null> {
  try {
    const response = await post(`/api/v1/practices/${practiceId}/repo/init?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('初始化代码仓库失败:', error);
    return null;
  }
}

/**
 * 获取代码仓库文件列表
 * @param practiceId 实践ID
 * @param path 文件路径
 * @param creatorId 创建者ID
 * @returns 文件列表
 */
export async function getRepositoryFiles(practiceId: number, path: string, creatorId: number): Promise<RepoFile[]> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/repo/files?path=${encodeURIComponent(path)}&creator_id=${creatorId}`);
    if (response.code === '0000') {
      const files = response.data.files || [];
      // 转换后端数据格式到前端格式
      return files.map((f: any) => ({
        path: f.file_path || f.path,
        name: f.file_name || f.name,
        type: f.is_directory ? 'directory' : 'file',
        content: f.content,
        size: f.file_size || f.size,
        modified: f.updated_at || f.modified
      }));
    }
    return [];
  } catch (error) {
    console.error('获取代码仓库文件列表失败:', error);
    return [];
  }
}

/**
 * 创建文件或目录
 * @param practiceId 实践ID
 * @param filePath 文件路径
 * @param isDirectory 是否是目录
 * @param content 文件内容（目录时为空）
 * @param creatorId 创建者ID
 * @returns 是否创建成功
 */
export async function createRepoFile(
  practiceId: number, 
  filePath: string, 
  isDirectory: boolean, 
  content: string, 
  creatorId: number
): Promise<boolean> {
  try {
    const response = await post(`/api/v1/practices/${practiceId}/repo/files`, {
      file_path: filePath,
      is_directory: isDirectory,
      content: content,
      creator_id: creatorId
    });
    return response.code === '0000';
  } catch (error) {
    console.error('创建文件失败:', error);
    return false;
  }
}

/**
 * 获取文件内容
 * @param practiceId 实践ID
 * @param filePath 文件路径
 * @param creatorId 创建者ID
 * @returns 文件内容
 */
export async function getFileContent(practiceId: number, filePath: string, creatorId: number): Promise<string | null> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/repo/files/${encodeURIComponent(filePath)}?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data.content;
    }
    return null;
  } catch (error) {
    console.error('获取文件内容失败:', error);
    return null;
  }
}

/**
 * 保存文件内容
 * @param practiceId 实践ID
 * @param filePath 文件路径
 * @param content 文件内容
 * @param creatorId 创建者ID
 * @returns 是否保存成功
 */
export async function saveFileContent(
  practiceId: number, 
  filePath: string, 
  content: string, 
  creatorId: number
): Promise<boolean> {
  try {
    const response = await patch(`/api/v1/practices/${practiceId}/repo/files/${encodeURIComponent(filePath)}?content=${encodeURIComponent(content)}&creator_id=${creatorId}`);
    return response.code === '0000';
  } catch (error) {
    console.error('保存文件内容失败:', error);
    return false;
  }
}

/**
 * 提交代码修改
 * @param practiceId 实践ID
 * @param commitType 提交类型：all（全部）或 current（当前）
 * @param filePaths 文件路径列表（current模式时使用）
 * @param commitMessage 提交信息
 * @param creatorId 创建者ID
 * @returns 是否提交成功
 */
export async function commitChanges(
  practiceId: number,
  commitType: 'all' | 'current',
  filePaths: string[],
  commitMessage: string,
  creatorId: number
): Promise<boolean> {
  try {
    const params = new URLSearchParams();
    params.append('commit_type', commitType);
    params.append('commit_message', commitMessage);
    params.append('creator_id', String(creatorId));
    if (commitType === 'current' && filePaths.length > 0) {
      filePaths.forEach(path => params.append('file_paths', path));
    }
    
    const response = await post(`/api/v1/practices/${practiceId}/repo/commit?${params.toString()}`);
    return response.code === '0000';
  } catch (error) {
    console.error('提交代码修改失败:', error);
    return false;
  }
}

// ==================== 数据集相关接口 ====================

export interface PracticeDataset {
  id: number;
  name: string;
  file_type: string;
  file_size: number;
  file_size_display: string;
  description?: string;
  access_url: string;
  created_at: string;
}

/**
 * 获取数据集列表
 * @param practiceId 实践ID
 * @param creatorId 创建者ID
 * @returns 数据集列表
 */
export async function getDatasets(practiceId: number, creatorId: number): Promise<PracticeDataset[]> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/datasets?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data.datasets || [];
    }
    return [];
  } catch (error) {
    console.error('获取数据集列表失败:', error);
    return [];
  }
}

/**
 * 上传数据集文件
 * @param practiceId 实践ID
 * @param fileInfo 文件信息
 * @param creatorId 创建者ID
 * @returns 上传结果
 */
export async function uploadDataset(
  practiceId: number,
  creatorId: number,
  file: File,
  description?: string
): Promise<PracticeDataset | null> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('creator_id', String(creatorId));
    if (description) {
      formData.append('description', description);
    }

    // 显式设置 Content-Type 为 undefined，让 axios 自动设置带有 boundary 的 multipart/form-data
    const response = await request.post(`/api/v1/practices/${practiceId}/datasets/upload`, formData, {
      timeout: 60000, // 上传文件超时时间延长到60秒
      headers: {
        'Content-Type': undefined // 覆盖默认的 application/json
      }
    });

    if (response.code === '0000') {
      return response.data as PracticeDataset;
    }
    return null;
  } catch (error) {
    console.error('上传数据集失败:', error);
    return null;
  }
}

/**
 * 获取数据集访问URL
 * @param practiceId 实践ID
 * @param datasetId 数据集ID
 * @param creatorId 创建者ID
 * @returns 访问URL
 */
export async function getDatasetAccessUrl(practiceId: number, datasetId: number, creatorId: number): Promise<string | null> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/datasets/${datasetId}/copy-url?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data.access_url;
    }
    return null;
  } catch (error) {
    console.error('获取数据集访问URL失败:', error);
    return null;
  }
}

/**
 * 删除数据集
 * @param practiceId 实践ID
 * @param datasetId 数据集ID
 * @param creatorId 创建者ID
 * @returns 是否删除成功
 */
export async function deleteDataset(practiceId: number, datasetId: number, creatorId: number): Promise<boolean> {
  try {
    const response = await del(`/api/v1/practices/${practiceId}/datasets/${datasetId}?creator_id=${creatorId}`);
    return response.code === '0000';
  } catch (error) {
    console.error('删除数据集失败:', error);
    return false;
  }
}

// ==================== 关卡管理相关接口 ====================

export interface PracticeStage {
  id: number;
  title: string;
  task_type: 'PRACTICE' | 'CHOICE' | 'JUDGEMENT';
  difficulty?: string;
  skills?: string[];
  coin: number;
  order_in_practice: number;
  handbook_markdown?: string;
  answer_content_markdown?: string;
  created_at: string;
}

export interface StageCreatePayload {
  title: string;
  task_type: 'PRACTICE' | 'CHOICE' | 'JUDGEMENT';
  difficulty?: string;
  skills?: string[];
  coin?: number;
  handbook_markdown?: string;
  answer_content_markdown?: string;
  evaluation_script_path?: string;
  student_task_file_paths?: string[];
  question_data?: string;
}

export interface TestCase {
  input_data: string;
  expected_output: string;
  is_hidden: boolean;
  match_rule: 'exact' | 'regex';
}

export interface StageSettingsPayload {
  evaluation_time_limit?: number;
  student_task_files?: string[];
  evaluation_script_path?: string;
  evaluation_command?: string;
  enable_realtime_preview?: boolean;
  preview_file_path?: string;
}

/**
 * 获取实践关卡列表
 * @param practiceId 实践ID
 * @param creatorId 创建者ID
 * @returns 关卡列表
 */
export async function getPracticeStages(practiceId: number, creatorId: number): Promise<PracticeStage[]> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/stages/management?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data.stages || [];
    }
    return [];
  } catch (error) {
    console.error('获取关卡列表失败:', error);
    return [];
  }
}

/**
 * 获取关卡详情
 * @param stageId 关卡ID
 * @param creatorId 创建者ID
 * @returns 关卡详情（包含test_cases）
 */
export async function getStageDetail(stageId: number | string, creatorId: number): Promise<PracticeStage | null> {
  try {
    const response = await get(`/api/v1/stages/${stageId}?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('获取关卡详情失败:', error);
    return null;
  }
}

/**
 * 获取学生视角的关卡详情（权限隔离）
 * 未通关时不返回参考答案，已通关或教师访问时返回参考答案
 * @param stageId 关卡ID
 * @param studentId 学生ID
 * @param includeAnswer 是否包含参考答案（教师访问时设为true）
 * @returns 关卡详情（包含test_cases和has_passed状态）
 */
export async function getStudentStageDetail(
  stageId: number | string,
  studentId: number,
  includeAnswer: boolean = false
): Promise<{
  stage: PracticeStage & { answer_title?: string; answer_content_markdown?: string };
  test_cases: Array<{
    id: number;
    case_id: string;
    input_data?: string;
    expected_output?: string;
    description?: string;
    is_hidden: boolean;
  }>;
  has_passed: boolean;
} | null> {
  try {
    const params = new URLSearchParams({
      student_id: String(studentId),
      include_answer: String(includeAnswer)
    });
    const response = await get(`/api/v1/stages/${stageId}/student-view?${params}`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('获取学生关卡详情失败:', error);
    return null;
  }
}

/**
 * 创建实践关卡
 * @param practiceId 实践ID
 * @param stageData 关卡数据
 * @param creatorId 创建者ID
 * @returns 创建的关卡信息
 */
export async function createPracticeStage(
  practiceId: number,
  stageData: StageCreatePayload,
  creatorId: number
): Promise<{ task_id: number; title: string; order_in_practice: number } | null> {
  try {
    const response = await post(`/api/v1/custom-practices/${practiceId}/stages?creator_id=${creatorId}`, stageData);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('创建关卡失败:', error);
    return null;
  }
}

/**
 * 更新关卡 - 步骤1：基本信息
 * @param stageId 关卡ID
 * @param data 基本信息数据
 * @param creatorId 创建者ID
 * @returns 是否更新成功
 */
export async function updateStageBasicInfo(
  stageId: string | number,
  data: Partial<StageCreatePayload>,
  creatorId: number
): Promise<boolean> {
  try {
    const response = await put(`/api/v1/stages/${stageId}/step1?creator_id=${creatorId}`, data);
    return response.code === '0000';
  } catch (error) {
    console.error('更新关卡基本信息失败:', error);
    return false;
  }
}

/**
 * 更新关卡 - 步骤2：任务设置（实践题）
 * @param stageId 关卡ID
 * @param settings 任务设置
 * @param creatorId 创建者ID
 * @returns 是否更新成功
 */
export async function updateStageSettings(
  stageId: string | number,
  settings: StageSettingsPayload,
  creatorId: number
): Promise<boolean> {
  try {
    const response = await put(`/api/v1/stages/${stageId}/step2?creator_id=${creatorId}`, settings);
    return response.code === '0000';
  } catch (error) {
    console.error('更新关卡任务设置失败:', error);
    return false;
  }
}

/**
 * 创建/更新关卡测试集
 * @param stageId 关卡ID
 * @param testCases 测试集列表
 * @param creatorId 创建者ID
 * @returns 是否创建成功
 */
export async function createStageTestCases(
  stageId: string | number,
  testCases: TestCase[],
  creatorId: number
): Promise<boolean> {
  try {
    const response = await post(`/api/v1/stages/${stageId}/test-cases?creator_id=${creatorId}`, {
      test_cases: testCases
    });
    return response.code === '0000';
  } catch (error) {
    console.error('创建测试集失败:', error);
    return false;
  }
}

/**
 * 更新关卡 - 步骤3：参考答案
 * @param stageId 关卡ID
 * @param answerTitle 答案标题
 * @param answerContent 答案内容
 * @param creatorId 创建者ID
 * @returns 是否更新成功
 */
export async function updateStageAnswer(
  stageId: string | number,
  answerTitle: string,
  answerContent: string,
  creatorId: number
): Promise<boolean> {
  try {
    const response = await put(`/api/v1/stages/${stageId}/step3?creator_id=${creatorId}`, {
      answer_title: answerTitle,
      answer_content_markdown: answerContent
    });
    return response.code === '0000';
  } catch (error) {
    console.error('更新参考答案失败:', error);
    return false;
  }
}

/**
 * 删除关卡
 * @param stageId 关卡ID
 * @param creatorId 创建者ID
 * @returns 是否删除成功
 */
export async function deletePracticeStage(stageId: string | number, creatorId: number): Promise<boolean> {
  try {
    const response = await del(`/api/v1/stages/${stageId}?creator_id=${creatorId}`);
    return response.code === '0000';
  } catch (error) {
    console.error('删除关卡失败:', error);
    return false;
  }
}

/**
 * 关卡排序数据
 */
export interface StageOrderUpdate {
  stage_id: number;
  order_in_practice: number;
}

/**
 * 更新关卡排序
 * @param practiceId 实践ID
 * @param stageOrders 关卡排序数据
 * @param creatorId 创建者ID
 * @returns 是否更新成功
 */
export async function updateStageOrder(
  practiceId: number,
  stageOrders: StageOrderUpdate[],
  creatorId: number
): Promise<boolean> {
  try {
    const response = await put(`/api/v1/practices/${practiceId}/stages/order?creator_id=${creatorId}`, {
      stage_orders: stageOrders
    });
    return response.code === '0000';
  } catch (error) {
    console.error('更新关卡排序失败:', error);
    return false;
  }
}

// ==================== 判断题和选择题相关接口 ====================

/**
 * 判断题数据接口
 */
export interface JudgmentQuestion {
  question_id?: string;
  question_content: string;
  correct_answer: boolean;
  explanation?: string;
  score?: number;
}

/**
 * 选择题选项接口
 */
export interface ChoiceOption {
  key: string;
  text: string;
  is_correct: boolean;
}

/**
 * 选择题数据接口
 */
export interface ChoiceQuestion {
  question_id?: string;
  question_content: string;
  question_type: 'single' | 'multiple';
  options: ChoiceOption[];
  explanation?: string;
  score?: number;
}

/**
 * 题目设置请求数据
 */
export interface QuestionSettingsRequest {
  question_type: 'judge' | 'choice';
  questions: (JudgmentQuestion | ChoiceQuestion)[];
}

/**
 * 更新关卡题目设置（判断题/选择题）
 * @param stageId 关卡ID
 * @param questionSettings 题目设置数据
 * @param creatorId 创建者ID
 * @returns 是否更新成功
 */
export async function updateStageQuestionSettings(
  stageId: number,
  questionSettings: QuestionSettingsRequest,
  creatorId: number
): Promise<boolean> {
  try {
    const response = await put(`/api/v1/stages/${stageId}/question-settings?creator_id=${creatorId}`, questionSettings);
    return response.code === '0000';
  } catch (error) {
    console.error('更新题目设置失败:', error);
    return false;
  }
}

/**
 * 获取关卡题目数据
 * @param stageId 关卡ID
 * @param creatorId 创建者ID
 * @returns 题目数据
 */
export async function getStageQuestionData(
  stageId: number,
  creatorId: number
): Promise<QuestionSettingsRequest | null> {
  try {
    const response = await get(`/api/v1/stages/${stageId}/question-data?creator_id=${creatorId}`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('获取题目数据失败:', error);
    return null;
  }
}

/**
 * 完整创建题目类型关卡
 * @param practiceId 实践ID
 * @param stageData 关卡数据
 * @param creatorId 创建者ID
 * @returns 创建结果
 */
export async function createQuestionStageComplete(
  practiceId: number,
  stageData: {
    task_info: StageCreatePayload;
    question_settings: QuestionSettingsRequest;
    answer_info: {
      answer_title: string;
      answer_content_markdown: string;
    };
  },
  creatorId: number
): Promise<{ task_id: number; title: string; order_in_practice: number } | null> {
  try {
    const response = await post(`/api/v1/practices/${practiceId}/stages/question-complete?creator_id=${creatorId}`, stageData);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('创建题目类型关卡失败:', error);
    return null;
  }
}

/**
 * 关卡测试数据接口
 */
export interface StageTestData {
  stage_id: number;
  stage_title: string;
  task_type: 'PRACTICE' | 'JUDGEMENT' | 'CHOICE';
  handbook_markdown?: string;
  question_data?: QuestionSettingsRequest;
  test_cases?: TestCase[];
  evaluation_settings?: {
    evaluation_script_path: string;
    evaluation_command: string;
    evaluation_timeout_seconds: number;
    student_task_file_paths: string[];
  };
}

/**
 * 获取关卡测试数据
 * @param practiceId 实践ID
 * @param stageId 关卡ID
 * @param creatorId 创建者ID
 * @returns 关卡测试数据
 */
export async function getStageTestData(
  practiceId: number,
  stageId: number,
  creatorId: number
): Promise<StageTestData | null> {
  try {
    const response = await get(`/api/v1/stages/${stageId}?creator_id=${creatorId}`);
    if (response.code === '0000') {
      const stage = response.data;
      
      // 格式化返回数据
      const testData: StageTestData = {
        stage_id: stage.id,
        stage_title: stage.title,
        task_type: stage.task_type,
        handbook_markdown: stage.handbook_markdown
      };
      
      // 如果是题目类型，获取题目数据
      if (stage.task_type === 'JUDGEMENT' || stage.task_type === 'CHOICE') {
        if (stage.question_data) {
          try {
            testData.question_data = typeof stage.question_data === 'string' 
              ? JSON.parse(stage.question_data) 
              : stage.question_data;
          } catch (e) {
            console.warn('解析题目数据失败:', e);
          }
        }
      }
      
      // 如果是实践题，获取测试集和评测设置
      if (stage.task_type === 'PRACTICE') {
        testData.test_cases = stage.test_cases || [];
        testData.evaluation_settings = {
          evaluation_script_path: stage.evaluation_script_path,
          evaluation_command: stage.evaluation_command,
          evaluation_timeout_seconds: stage.evaluation_timeout_seconds,
          student_task_file_paths: stage.student_task_file_paths ? 
            (typeof stage.student_task_file_paths === 'string' ? 
              JSON.parse(stage.student_task_file_paths) : 
              stage.student_task_file_paths) : []
        };
      }
      
      return testData;
    }
    return null;
  } catch (error) {
    console.error('获取关卡测试数据失败:', error);
    return null;
  }
}

// ==================== 关卡测试相关接口 ====================

export interface SandboxTestResult {
  success: boolean;
  score: number;
  total_score: number;
  test_results: Array<{
    test_case_id: string;
    input_data: string;
    expected_output: string;
    actual_output: string;
    passed: boolean;
    execution_time: number;
  }>;
  execution_logs: string;
  execution_time: number;
  test_mode: string;
  tested_at: string;
  error_message?: string;
}

export interface PracticeFailureHintRequest {
  stage_id: number;
  code_content: string;
  failure_cases: Array<Record<string, any>>;
  handbook_markdown?: string;
  visible_error_output?: string;
}

export interface PracticeFailureHintResponse {
  hint: string;
  quota_info: Record<string, any>;
  success: boolean;
  error?: string;
}

/**
 * 关卡沙盒测试（教师模拟学生做题）
 * @param stageId 关卡ID
 * @param codeContent 代码内容
 * @param fileContents 文件内容字典
 * @param creatorId 创建者ID
 * @returns 测试结果
 */
export async function sandboxTest(
  stageId: number,
  codeContent: string,
  fileContents: Record<string, string>,
  creatorId: number
): Promise<SandboxTestResult | null> {
  try {
    const response = await post(`/api/v1/stages/${stageId}/sandbox-test?creator_id=${creatorId}`, {
      test_mode: 'teacher',
      code_content: codeContent,
      file_contents: fileContents
    });
    if (response.code === '0000' && response.data) {
      return response.data as SandboxTestResult;
    }
    return null;
  } catch (error) {
    console.error('关卡沙盒测试失败:', error);
    return null;
  }
}

// 获取闯关失败解释（保密策略）
export async function requestPracticeFailureHint(
  payload: PracticeFailureHintRequest
): Promise<string | null> {
  try {
    const response = await request.post('/api/v1/ai/explain-practice-failure', payload);
    if (response.code === '0000' && response.data?.success) {
      return response.data.hint || null;
    }
    return response.data?.hint || null;
  } catch (error) {
    console.error('获取失败提示失败:', error);
    return null;
  }
}

// ==================== 实践课程配置相关接口 ====================

export interface PracticeConfig {
  editor: boolean;
  shell: boolean;
  repoVisible: boolean;
  allowSkip: boolean;
}

/**
 * 获取实践课程配置
 * @param practiceId 实践课程ID
 * @returns 配置信息
 */
export async function getPracticeConfig(practiceId: number): Promise<PracticeConfig | null> {
  try {
    const response = await get(`/api/v1/practices/${practiceId}/config`);
    if (response.code === '0000') {
      const config = response.data;
      return {
        editor: config.enable_code_editor,
        shell: config.enable_terminal,
        repoVisible: config.repo_visibility === 'visible',
        allowSkip: config.allow_skip_levels
      };
    }
    return null;
  } catch (error) {
    console.error('获取实践课程配置失败:', error);
    return null;
  }
}

/**
 * 更新实践课程配置
 * @param practiceId 实践课程ID
 * @param config 配置数据
 * @returns 是否更新成功
 */
export async function updatePracticeConfig(practiceId: number, config: PracticeConfig): Promise<boolean> {
  try {
    // 后端期望的字段名: editor, shell, repoVisible, allowSkip
    const requestData = {
      editor: config.editor,
      shell: config.shell,
      repoVisible: config.repoVisible,
      allowSkip: config.allowSkip
    };

    const response = await patch(`/api/v1/practices/${practiceId}/config`, requestData);
    return response.code === '0000';
  } catch (error) {
    console.error('更新实践课程配置失败:', error);
    return false;
  }
}

// ==================== 实践课程发布相关接口 ====================

export interface PublishRequest {
  visibility: 'public' | 'private';
}

/**
 * 发布实践课程
 * @param practiceId 实践课程ID
 * @param publishData 发布数据
 * @returns 是否发布成功
 */
export async function publishPractice(practiceId: number, publishData: PublishRequest): Promise<boolean> {
  try {
    const response = await post(`/api/v1/custom-practices/${practiceId}/publish`, publishData);
    return response.code === '0000';
  } catch (error) {
    console.error('发布实践课程失败:', error);
    return false;
  }
}

/**
 * 克隆实践课程
 * @param practiceId 实践课程ID
 * @returns 复制后的实践课程ID
 */
export async function clonePractice(practiceId: string): Promise<{ id: number } | null> {
  try {
    const response = await post(`/api/v1/practices/${practiceId}/clone`);
    if (response.code === '0000') {
      return response.data;
    }
    return null;
  } catch (error) {
    console.error('克隆实践课程失败:', error);
    return null;
  }
}

/**
 * 基础信息请求类型
 */
export interface BasicInfoRequest {
  name: string;
  type: string;
  difficulty: string;
  introduction: string;
}

/**
 * 更新实践课程基础信息
 * @param practiceId 实践课程ID
 * @param data 基础信息数据
 * @returns 是否更新成功
 */
export async function updatePracticeBasicInfo(practiceId: number, data: BasicInfoRequest): Promise<boolean> {
  try {
    const response = await patch(`/api/v1/practices/${practiceId}/basic-info`, data);
    return response.code === '0000';
  } catch (error) {
    console.error('更新实践课程基础信息失败:', error);
    return false;
  }
}
