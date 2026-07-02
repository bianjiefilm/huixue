import { request } from '@/utils/request';

// 仪表盘基础数据类型
export interface DashboardStats {
  totalUsers: number;
  userIncrease: number;
  totalCourses: number;
  courseIncrease: number;
  totalProjects: number;
  projectIncrease: number;
  totalExams: number;
  examIncrease: number;
}

/**
 * 获取系统总仪表盘统计数据
 */
export async function getSystemDashboardStats(): Promise<any> {
  return request.get('/api/v1/system/dashboard/statistics');
}

// 学校信息
export interface SchoolInfo {
  id?: number;
  name?: string;
  short_name?: string;
  motto?: string;
  logo_url?: string;
}

export function getSchoolInfo(id: number | string) {
  return request.get(`/api/v1/system/school/${id}`);
}

export function updateSchoolInfo(id: number | string, data: any) {
  return request.put(`/api/v1/system/school/${id}`, data);
}

export function uploadSchoolLogo(id: number | string, data: any) {
  return request.post(`/api/v1/system/school/${id}/logo`, data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

// 教师管理
export interface Teacher {
  id: number;
  job_number: string;
  name: string;
  gender: string;
  phone: string;
  email: string;
  title: string;
  department: string;
  is_active?: boolean;
  is_admin?: boolean;
}

export function getTeachers(params: any) {
  return request.get('/api/v1/system/teachers', { params });
}

export function createTeacher(data: any) {
  return request.post('/api/v1/system/teachers', data);
}

export function updateTeacher(id: number, data: any) {
  return request.put(`/api/v1/system/teachers/${id}`, data);
}

export function deleteTeacher(id: number) {
  return request.delete(`/api/v1/system/teachers/${id}`);
}

export function batchUpdateTeacherStatus(data: { ids: number[], is_active: boolean }) {
  return request.put('/api/v1/system/teachers/batch/status', data);
}

export function batchDeleteTeachers(ids: number[]) {
  return request.post('/api/v1/system/teachers/batch/delete', { ids });
}

export function importTeachers(file: File, schoolId: number) {
  const formData = new FormData();
  formData.append('file', file);
  return request.post(`/api/v1/system/teachers/import?school_id=${schoolId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

export function downloadTeacherTemplate() {
  return request.get('/api/v1/system/teachers/template/download', { responseType: 'blob' });
}