/**
 * 用户管理相关API (后台管理)
 */
import request from '@/utils/http';

// API响应类型
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
}

// 用户角色类型
export type UserRole = 'student' | 'teacher' | 'admin';

// 用户状态类型
export type UserStatus = 'active' | 'inactive' | 'graduated' | 'suspended';

// 用户基础信息接口
export interface UserInfo {
  id: number;
  username: string;
  real_name: string;
  email: string;
  phone?: string;
  avatar?: string;
  role: UserRole;
  status: UserStatus;
  organization_id?: number;
  organization_name?: string;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

// 学生特有信息
export interface StudentInfo extends UserInfo {
  student_id: string;
  gender: 'male' | 'female' | 'other';
  major: string;
  grade: string;
  class_name: string;
  enrollment_year: number;
  graduation_year?: number;
}

// 教师特有信息
export interface TeacherInfo extends UserInfo {
  teacher_id: string;
  title: string; // 职称
  department: string;
  research_area?: string;
  bio?: string;
}

// 查询参数
export interface UserQueryParams {
  role?: UserRole;
  status?: UserStatus;
  organization_id?: number;
  keyword?: string;
  page?: number;
  page_size?: number;
  created_start?: string;
  created_end?: string;
}

// 用户表单数据
export interface UserFormData {
  username: string;
  real_name: string;
  email: string;
  phone?: string;
  role: UserRole;
  organization_id?: number;
  password?: string;
  // 学生特有字段
  student_id?: string;
  gender?: 'male' | 'female' | 'other';
  major?: string;
  grade?: string;
  class_name?: string;
  enrollment_year?: number;
  // 教师特有字段
  teacher_id?: string;
  title?: string;
  department?: string;
  research_area?: string;
  bio?: string;
}

// 批量操作结果
export interface BatchOperationResult {
  success_count: number;
  failed_count: number;
  failed_items?: Array<{ id: number; error: string; }>;
}

// 获取用户列表
export async function getUserList(params: UserQueryParams): Promise<ApiResponse<{
  list: UserInfo[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get('/api/v1/admin/users', { params });
}

// 获取学生列表
export async function getStudentList(params: UserQueryParams): Promise<ApiResponse<{
  list: StudentInfo[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get('/api/v1/admin/students', { params });
}

// 获取教师列表
export async function getTeacherList(params: UserQueryParams): Promise<ApiResponse<{
  list: TeacherInfo[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get('/api/v1/admin/teachers', { params });
}

// 获取用户详情
export async function getUserDetail(id: number): Promise<ApiResponse<UserInfo>> {
  return request.get(`/api/v1/admin/users/${id}`);
}

// 创建用户
export async function createUser(data: UserFormData): Promise<ApiResponse<UserInfo>> {
  return request.post('/api/v1/admin/users', data);
}

// 更新用户信息
export async function updateUser(id: number, data: Partial<UserFormData>): Promise<ApiResponse<UserInfo>> {
  return request.put(`/api/v1/admin/users/${id}`, data);
}

// 删除用户
export async function deleteUser(id: number): Promise<ApiResponse<{ success: boolean }>> {
  return request.delete(`/api/v1/admin/users/${id}`);
}

// 批量删除用户
export async function batchDeleteUsers(ids: number[]): Promise<ApiResponse<BatchOperationResult>> {
  return request.post('/api/v1/admin/users/batch-delete', { ids });
}

// 批量更新用户状态
export async function batchUpdateUserStatus(ids: number[], status: UserStatus): Promise<ApiResponse<BatchOperationResult>> {
  return request.post('/api/v1/admin/users/batch-status', { ids, status });
}

// 重置用户密码
export async function resetUserPassword(id: number, new_password?: string): Promise<ApiResponse<{ password: string }>> {
  return request.post(`/api/v1/admin/users/${id}/reset-password`, { new_password });
}

// 批量重置密码
export async function batchResetPasswords(ids: number[]): Promise<ApiResponse<{
  results: Array<{ id: number; password: string; success: boolean; }>;
}>> {
  return request.post('/api/v1/admin/users/batch-reset-password', { ids });
}

// 用户账号转移（更换组织）
export async function transferUser(id: number, new_organization_id: number): Promise<ApiResponse<UserInfo>> {
  return request.post(`/api/v1/admin/users/${id}/transfer`, { new_organization_id });
}

// 批量转移用户
export async function batchTransferUsers(ids: number[], new_organization_id: number): Promise<ApiResponse<BatchOperationResult>> {
  return request.post('/api/v1/admin/users/batch-transfer', { ids, new_organization_id });
}

// 导入用户数据
export async function importUsers(file: File, options?: {
  role?: UserRole;
  organization_id?: number;
  skip_duplicates?: boolean;
  update_existing?: boolean;
  send_welcome_email?: boolean;
}): Promise<ApiResponse<{
  success_count: number;
  failed_count: number;
  errors?: Array<{ row: number; message: string; }>;
  created_passwords?: Array<{ username: string; password: string; }>;
}>> {
  const formData = new FormData();
  formData.append('file', file);
  if (options) {
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, String(value));
    });
  }
  
  return request.post('/api/v1/admin/users/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 导出用户数据
export async function exportUsers(params?: UserQueryParams): Promise<Blob> {
  const response = await request.get('/api/v1/admin/users/export', {
    params,
    responseType: 'blob'
  });
  return response;
}

// 获取用户统计信息
export async function getUserStats(params?: {
  organization_id?: number;
  date_range?: { start: string; end: string; };
}): Promise<ApiResponse<{
  total_users: number;
  active_users: number;
  new_users_this_month: number;
  role_distribution: Record<UserRole, number>;
  status_distribution: Record<UserStatus, number>;
  organization_distribution: Array<{ organization_name: string; count: number; }>;
  login_stats: {
    daily_logins: Array<{ date: string; count: number; }>;
    weekly_active_users: number;
    monthly_active_users: number;
  };
}>> {
  return request.get('/api/v1/admin/users/stats', { params });
}

// 获取用户活动日志
export async function getUserActivityLogs(userId: number, params?: {
  action_type?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: Array<{
    id: number;
    action_type: string;
    action_description: string;
    ip_address: string;
    user_agent: string;
    created_at: string;
  }>;
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get(`/api/v1/admin/users/${userId}/activity-logs`, { params });
}

// 检查用户名是否可用
export async function checkUsername(username: string, excludeId?: number): Promise<ApiResponse<{ available: boolean }>> {
  return request.get('/api/v1/admin/users/check-username', {
    params: { username, exclude_id: excludeId }
  });
}

// 检查邮箱是否可用
export async function checkEmail(email: string, excludeId?: number): Promise<ApiResponse<{ available: boolean }>> {
  return request.get('/api/v1/admin/users/check-email', {
    params: { email, exclude_id: excludeId }
  });
}

// 发送欢迎邮件
export async function sendWelcomeEmail(userId: number): Promise<ApiResponse<{ success: boolean }>> {
  return request.post(`/api/v1/admin/users/${userId}/send-welcome-email`);
}

// 批量发送欢迎邮件
export async function batchSendWelcomeEmails(ids: number[]): Promise<ApiResponse<BatchOperationResult>> {
  return request.post('/api/v1/admin/users/batch-send-welcome-email', { ids });
}