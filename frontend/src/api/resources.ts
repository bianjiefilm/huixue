import { request } from '@/utils/request';

export interface ApiResponse<T = any> {
  code: string | number;
  message: string;
  data: T;
}

// 教学资源相关的类型定义

// 资源模块
export interface ResourceModule {
  id: number;
  name: string;
  description?: string;
  order_index: number;
  file_count: number;
  created_at: string;
  updated_at: string;
  files?: ResourceFile[]; // 动态添加的文件列表
}

// 资源文件
export interface ResourceFile {
  id: number;
  module_id: number;
  name: string;
  url: string;
  file_type: 'pdf' | 'doc' | 'docx' | 'ppt' | 'pptx' | 'mp4';
  file_size: number;
  duration_seconds?: number;
  view_count: number;
  download_count: number;
  created_at: string;
  uploader_name: string;
}

// 课堂资源（旧版本兼容）
export interface ClassroomResource {
  id: number;
  title: string;
  url: string;
  resource_type: string;
  file_size?: number;
  upload_time: string;
  uploader_name: string;
  view_count: number;
  download_count: number;
}

// 学习记录
export interface LearningRecord {
  id: number;
  resource_file_id: number;
  learning_duration_seconds: number;
  last_position: number;
  is_completed: boolean;
  first_access_at: string;
  last_access_at: string;
}

// 云盘文件
export interface CloudFile {
  id: number;
  name: string;
  file_type: string;
  file_size: number;
  folder_path: string;
  url: string;
  upload_time: string;
  uploader_name: string;
  download_count: number;
  is_shared: boolean;
}

// 请求类型
export interface CreateModuleRequest {
  name: string;
  description?: string;
}

export interface UpdateModuleRequest {
  name?: string;
  description?: string;
  order_index?: number;
}

export interface UploadFileRequest {
  name: string;
  url: string;
  file_type: string;
  file_size: number;
  duration_seconds?: number;
}

export interface LearningRecordRequest {
  learning_duration_seconds: number;
  last_position?: number;
  is_completed?: boolean;
}

export interface CloudFilesBatchRequest {
  action: 'delete' | 'download';
  file_ids: number[];
}

// 响应类型
export interface ResourceModulesResponse {
  modules: ResourceModule[];
}

export interface ModuleFilesResponse {
  files: ResourceFile[];
}

export interface ClassroomResourcesResponse {
  list: ClassroomResource[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}

export interface CloudFilesResponse {
  list: CloudFile[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  current_path: string;
}

export interface StudentLearningRecordsResponse {
  records: LearningRecord[];
}

// API 函数

// ==================== 教学资源模块管理 ====================

/**
 * 获取课堂教学资源模块列表
 */
export async function getResourceModules(params: {
  classroom_id: number;
  teacher_id?: number;
  student_id?: number;
}): Promise<ApiResponse<ResourceModulesResponse>> {
  const { classroom_id, teacher_id, student_id } = params;
  
  // Use the new multi-tenant endpoint
  const queryParams = {} as any;
  if (teacher_id) queryParams.teacher_id = teacher_id;
  if (student_id) queryParams.student_id = student_id;
  
  return request.get(`/api/v1/teaching-resources/classrooms/${classroom_id}/modules`, {
    params: queryParams
  });
}

/**
 * 创建教学资源模块
 */
export async function createResourceModule(params: {
  classroom_id: number;
  teacher_id: number;
  data: CreateModuleRequest;
}): Promise<ApiResponse<ResourceModule>> {
  const { classroom_id, teacher_id, data } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/resource-modules`, null, {
    params: { teacher_id, ...data }
  });
}

/**
 * 更新教学资源模块
 */
export async function updateResourceModule(params: {
  module_id: number;
  teacher_id: number;
  data: UpdateModuleRequest;
}): Promise<ApiResponse<ResourceModule>> {
  const { module_id, teacher_id, data } = params;
  return request.put(`/api/v1/resource-modules/${module_id}`, null, {
    params: { teacher_id, ...data }
  });
}

/**
 * 删除教学资源模块
 */
export async function deleteResourceModule(params: {
  module_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{ message: string }>> {
  const { module_id, teacher_id } = params;
  return request.delete(`/api/v1/resource-modules/${module_id}`, {
    params: { teacher_id }
  });
}

// ==================== 教学资源文件管理 ====================

/**
 * 获取模块内的文件列表
 */
export async function getModuleFiles(params: {
  module_id: number;
  teacher_id: number;
}): Promise<ApiResponse<ModuleFilesResponse>> {
  const { module_id, teacher_id } = params;
  return request.get(`/api/v1/resource-modules/${module_id}/files`, {
    params: { teacher_id }
  });
}

/**
 * 上传文件到教学资源模块
 */
export async function uploadResourceFile(params: {
  module_id: number;
  teacher_id: number;
  data: UploadFileRequest;
}): Promise<ApiResponse<ResourceFile>> {
  const { module_id, teacher_id, data } = params;
  return request.post(`/api/v1/resource-modules/${module_id}/files`, null, {
    params: { teacher_id, ...data }
  });
}

/**
 * 删除教学资源文件
 */
export async function deleteResourceFile(params: {
  file_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{ message: string }>> {
  const { file_id, teacher_id } = params;
  return request.delete(`/api/v1/resource-files/${file_id}`, {
    params: { teacher_id }
  });
}

/**
 * 更新文件查看次数（用于预览时调用）
 */
export async function updateFileViewCount(params: {
  file_id: number;
}): Promise<ApiResponse<{ message: string }>> {
  const { file_id } = params;
  return request.post(`/api/v1/resource-files/${file_id}/view`);
}

// ==================== 课堂资源管理（兼容旧版本） ====================

/**
 * 获取课堂教学资源列表
 */
export async function getClassroomResources(params: {
  classroom_id: number;
  teacher_id: number;
  resource_type?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<ClassroomResourcesResponse>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/resources`, {
    params: queryParams
  });
}

/**
 * 上传教学资源（旧版本）
 */
export async function uploadClassroomResource(params: {
  classroom_id: number;
  teacher_id: number;
  title: string;
  resource_type: string;
  url: string;
}): Promise<ApiResponse<ClassroomResource>> {
  const { classroom_id, ...queryParams } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/resources`, null, {
    params: queryParams
  });
}

/**
 * 删除教学资源（旧版本）
 */
export async function deleteClassroomResource(params: {
  classroom_id: number;
  resource_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{ message: string }>> {
  const { classroom_id, resource_id, teacher_id } = params;
  return request.delete(`/api/v1/classrooms/${classroom_id}/resources/${resource_id}`, {
    params: { teacher_id }
  });
}

// ==================== 学习记录管理 ====================

/**
 * 记录学生学习时长
 */
export async function recordStudentLearning(params: {
  file_id: number;
  student_id: number;
  data: LearningRecordRequest;
}): Promise<ApiResponse<LearningRecord>> {
  const { file_id, student_id, data } = params;
  return request.post(`/api/v1/resource-files/${file_id}/learning-record`, null, {
    params: { student_id, ...data }
  });
}

/**
 * 获取学生在某个课堂的学习记录
 */
export async function getStudentLearningRecords(params: {
  classroom_id: number;
  student_id: number;
}): Promise<ApiResponse<StudentLearningRecordsResponse>> {
  const { classroom_id, student_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/student-learning-records`, {
    params: { student_id }
  });
}

// ==================== 课堂云盘管理 ====================

/**
 * 获取课堂云盘文件列表
 */
export async function getCloudDiskFiles(params: {
  classroom_id: number;
  teacher_id: number;
  user_role?: string;
  folder_path?: string;
  keyword?: string;
  file_type?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<CloudFilesResponse>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/cloud-disk`, {
    params: queryParams
  });
}

/**
 * 上传文件到课堂云盘
 */
export async function uploadCloudDiskFile(params: {
  classroom_id: number;
  teacher_id: number;
  file_name: string;
  file_type: string;
  file_size: number;
  folder_path?: string;
  url: string;
  is_shared?: boolean;
}): Promise<ApiResponse<CloudFile>> {
  const { classroom_id, ...queryParams } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/cloud-disk/upload`, null, {
    params: queryParams
  });
}

/**
 * 预览云盘文件
 */
export async function previewCloudDiskFile(params: {
  classroom_id: number;
  file_id: number;
  teacher_id: number;
}): Promise<ApiResponse<any>> {
  const { classroom_id, file_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/cloud-disk/${file_id}/preview`, {
    params: { teacher_id }
  });
}

/**
 * 下载云盘文件（更新下载次数）
 */
export async function downloadCloudDiskFile(params: {
  classroom_id: number;
  file_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{
  file_id: number;
  file_name: string;
  download_url: string;
  download_count: number;
}>> {
  const { classroom_id, file_id, teacher_id } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/cloud-disk/${file_id}/download`, null, {
    params: { teacher_id }
  });
}

/**
 * 批量操作云盘文件
 */
export async function batchCloudDiskOperation(params: {
  classroom_id: number;
  teacher_id: number;
  data: CloudFilesBatchRequest;
}): Promise<ApiResponse<any>> {
  const { classroom_id, teacher_id, data } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/cloud-disk/batch`, data, {
    params: { teacher_id }
  });
}

/**
 * 删除单个云盘文件
 */
export async function deleteCloudDiskFile(params: {
  classroom_id: number;
  file_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{ message: string }>> {
  const { classroom_id, file_id, teacher_id } = params;
  return request.delete(`/api/v1/classrooms/${classroom_id}/cloud-disk/${file_id}`, {
    params: { teacher_id }
  });
}

// 辅助函数

/**
 * 获取文件类型图标
 */
export function getFileTypeIcon(fileType: string): string {
  const iconMap: Record<string, string> = {
    'pdf': 'file-pdf',
    'doc': 'file-word',
    'docx': 'file-word',
    'ppt': 'file-ppt',
    'pptx': 'file-ppt',
    'mp4': 'play-circle',
    'video': 'play-circle'
  };
  return iconMap[fileType.toLowerCase()] || 'file';
}

/**
 * 获取文件类型名称
 */
export function getFileTypeName(fileType: string): string {
  const nameMap: Record<string, string> = {
    'pdf': 'PDF文档',
    'doc': 'Word文档',
    'docx': 'Word文档',
    'ppt': 'PPT演示文稿',
    'pptx': 'PPT演示文稿',
    'mp4': '视频文件',
    'video': '视频文件'
  };
  return nameMap[fileType.toLowerCase()] || '未知文件';
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * 格式化视频时长
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  } else {
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
}

/**
 * 检查文件类型是否支持
 */
export function isSupportedFileType(fileType: string): boolean {
  const supportedTypes = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4'];
  return supportedTypes.includes(fileType.toLowerCase());
}

/**
 * 检查文件大小是否超过限制（2GB）
 */
export function isFileSizeValid(fileSize: number): boolean {
  const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
  return fileSize <= maxSize;
}