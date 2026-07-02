import { message } from 'ant-design-vue';
import { get, post, put, del } from '../utils/request';

// 教师数据结构
export interface Teacher {
  id: string;
  name: string;
  code: string;
  gender: 'male' | 'female' | 'other';
  avatar: string;
  department: string;
  phone: string;
  email: string;
}

// 组织部门结构
export interface Department {
  id: string;
  name: string;
  children?: Department[];
}

// 分页结果
export interface PageResult<T> {
  items: T[];
  total: number;
}

// 查询参数
export interface QueryParams {
  page: number;
  pageSize: number;
  keyword?: string;
  departmentId?: string;
}

// 获取部门列表
export async function getDepartments(): Promise<Department[]> {
  try {
    const response = await get('/api/v1/departments');
    return response.data.list || [];
  } catch (error) {
    console.error('获取部门列表失败:', error);
    return [];
  }
}

// 获取教师列表（带分页和筛选）
export async function getTeacherList(params: QueryParams): Promise<PageResult<Teacher>> {
  try {
    const response = await get('/api/v1/system/teachers', {
      page: params.page,
      page_size: params.pageSize,
      keyword: params.keyword,
      department_id: params.departmentId
    });
    
    return {
      items: response.data.items || response.data.list || [],
      total: response.data.total || 0
    };
  } catch (error) {
    message.error('获取教师列表失败');
    console.error('获取教师列表失败:', error);
    return { items: [], total: 0 };
  }
}

// 根据ID获取教师信息
export async function getTeacherById(id: string): Promise<Teacher | null> {
  try {
    const response = await get(`/api/v1/system/teachers/${id}`);
    return response.data;
  } catch (error) {
    message.error('获取教师信息失败');
    console.error('获取教师信息失败:', error);
    return null;
  }
}

// 根据ID列表批量获取教师信息
export async function getTeachersByIds(ids: string[]): Promise<Teacher[]> {
  try {
    const response = await post('/api/v1/teachers/batch', { ids });
    return response.data.list || [];
  } catch (error) {
    message.error('批量获取教师信息失败');
    console.error('批量获取教师信息失败:', error);
    return [];
  }
}

// 创建新教师
export async function createTeacher(teacher: Omit<Teacher, 'id'>): Promise<Teacher | null> {
  try {
    const response = await post('/api/v1/system/teachers', teacher);
    return response.data;
  } catch (error) {
    message.error('创建教师失败');
    console.error('创建教师失败:', error);
    return null;
  }
}

// 更新教师信息
export async function updateTeacher(id: string, teacher: Partial<Teacher>): Promise<Teacher | null> {
  try {
    const response = await put(`/api/v1/system/teachers/${id}`, teacher);
    return response.data;
  } catch (error) {
    message.error('更新教师信息失败');
    console.error('更新教师信息失败:', error);
    return null;
  }
}

// 删除教师
export async function deleteTeacher(id: string): Promise<boolean> {
  try {
    const response = await del(`/api/v1/system/teachers/${id}`);
    return response.code === '0000';
  } catch (error) {
    message.error('删除教师失败');
    console.error('删除教师失败:', error);
    return false;
  }
}