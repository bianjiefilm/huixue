import { request } from '@/utils/request';
import type { OrganizationNode } from '@/stores/department';

// API响应类型
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
}

// 组织节点类型
export type NodeType = 'school' | 'college' | 'major' | 'grade' | 'class';

// 组织表格项接口
export interface OrganizationItem {
  id: number;
  name: string;
  code: string;
  type: NodeType;
  parent_id?: number;
  description?: string;
  status: boolean;
  created_at: string;
  updated_at: string;
  // 统计字段
  student_count?: number;
  major_count?: number;
  class_count?: number;
  // 特殊字段
  degree_type?: 'bachelor' | 'master' | 'doctor';
  head_teacher?: string;
  year?: number;
}

// 查询参数
export interface QueryParams {
  parent_id?: number;
  type?: NodeType;
  page?: number;
  page_size?: number;
  keyword?: string;
  status?: boolean;
}

// 组织表单数据
export interface OrganizationForm {
  name: string;
  code: string;
  type: NodeType;
  parent_id?: number;
  description?: string;
  degree_type?: 'bachelor' | 'master' | 'doctor';
  head_teacher?: string;
  year?: number;
}

/**
 * 获取学校组织架构树
 * @param schoolId 学校ID
 * @returns 组织架构树
 */
export function getOrganizationTree(schoolId?: string) {
  return request<OrganizationNode[]>({
    url: schoolId ? `/api/v1/organization/schools/${schoolId}/organizations/tree` : '/api/v1/organizations/tree',
    method: 'get'
  });
}

// 获取组织列表
export async function getOrganizationList(params: QueryParams): Promise<ApiResponse<{
  list: OrganizationItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request({
    url: '/api/v1/organizations',
    method: 'get',
    params
  });
}

// 获取组织详情
export async function getOrganizationDetail(id: number): Promise<ApiResponse<OrganizationItem>> {
  return request({
    url: `/api/v1/organizations/${id}`,
    method: 'get'
  });
}

// 创建组织
export async function createOrganization(data: OrganizationForm): Promise<ApiResponse<OrganizationItem>> {
  return request({
    url: '/api/v1/organizations',
    method: 'post',
    data
  });
}

// 更新组织
export async function updateOrganization(id: number, data: Partial<OrganizationForm>): Promise<ApiResponse<OrganizationItem>> {
  return request({
    url: `/api/v1/organizations/${id}`,
    method: 'put',
    data
  });
}

// 删除组织
export async function deleteOrganization(id: number): Promise<ApiResponse<{ success: boolean }>> {
  return request({
    url: `/api/v1/organizations/${id}`,
    method: 'delete'
  });
}

// 批量删除组织
export async function batchDeleteOrganizations(ids: number[]): Promise<ApiResponse<{ 
  success: boolean;
  failed_ids?: number[];
  error_message?: string;
}>> {
  return request({
    url: '/api/v1/organizations/batch-delete',
    method: 'post',
    data: { ids }
  });
}

// 批量更新组织状态
export async function batchUpdateOrganizationStatus(ids: number[], status: boolean): Promise<ApiResponse<{ success: boolean }>> {
  return request({
    url: '/api/v1/organizations/batch-status',
    method: 'post',
    data: { ids, status }
  });
}

// 获取可选的父级组织列表
export async function getParentOrganizations(type: NodeType): Promise<ApiResponse<OrganizationNode[]>> {
  return request({
    url: '/api/v1/organizations/parents',
    method: 'get',
    params: { type }
  });
}

// 验证组织代码是否可用
export async function checkOrganizationCode(code: string, excludeId?: number): Promise<ApiResponse<{ available: boolean }>> {
  return request({
    url: '/api/v1/organizations/check-code',
    method: 'get',
    params: { code, exclude_id: excludeId }
  });
}

// 导入组织数据
export async function importOrganizations(file: File, options?: {
  skip_duplicates?: boolean;
  update_existing?: boolean;
}): Promise<ApiResponse<{
  success_count: number;
  failed_count: number;
  errors?: Array<{ row: number; message: string; }>;
}>> {
  const formData = new FormData();
  formData.append('file', file);
  if (options) {
    Object.entries(options).forEach(([key, value]) => {
      formData.append(key, String(value));
    });
  }
  
  return request({
    url: '/api/v1/organizations/import',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

/**
 * 获取组织下的学生列表
 * @param organizationId 组织ID
 * @param params 查询参数
 * @returns 学生列表
 */
export function getOrganizationStudents(organizationId: string, params?: {
  keyword?: string;
  page?: number;
  page_size?: number;
}) {
  return request({
    url: `/api/v1/organizations/${organizationId}/students`,
    method: 'get',
    params
  });
}

/**
 * 获取带真实API的可添加学生列表
 * @param classroomId 课堂ID
 * @param params 查询参数
 * @returns API响应
 */
export function getAvailableStudentsForClassroomAPI(classroomId: number, params: {
  keyword?: string;
  organization_id?: string;
  department?: string;
  major?: string;
  grade?: string;
  page?: number;
  page_size?: number;
  teacher_id: number;
}) {
  return request({
    url: `/api/v1/classrooms/${classroomId}/students/available`,
    method: 'get',
    params
  });
}

/**
 * 批量添加学生到课堂
 * @param classroomId 课堂ID
 * @param data 请求数据
 * @returns API响应
 */
export function addStudentsToClassroomAPI(classroomId: number, data: {
  student_ids: number[];
}, teacherId: number) {
  return request({
    url: `/api/v1/classrooms/${classroomId}/students`,
    method: 'post',
    data,
    params: {
      teacher_id: teacherId
    }
  });
}