import { get, post, del, put } from '@/utils/request';

// Student interface
export interface Student {
  id: string;
  name: string;
  studentId: string;
  student_number?: string;
  gender: 'male' | 'female' | 'other';
  avatar: string;
  department: string;
  major: string;
  grade: string;
  phone: string;
  email: string;
  organization_id?: string;
  class_id?: number;
  is_active?: boolean;
}

// API基础路径
const API_BASE = '/api/v1/system';

/**
 * 获取所有学生列表
 * @param keyword 搜索关键词（可选）
 * @returns 学生列表
 */
export async function getStudents(keyword?: string): Promise<Student[]> {
  try {
    const params: any = { school_id: 1 };
    if (keyword && keyword.trim()) {
      params.search = keyword;
    }
    const response = await get(`${API_BASE}/students`, params);
    return response.data.items || [];
  } catch (error) {
    console.error('获取学生列表失败:', error);
    return [];
  }
}

/**
 * 根据ID获取学生信息
 * @param id 学生ID
 * @returns 学生信息
 */
export async function getStudentById(id: string): Promise<Student | null> {
  try {
    const response = await get(`${API_BASE}/students/${id}`);
    return response.data;
  } catch (error) {
    console.error('获取学生信息失败:', error);
    return null;
  }
}

/**
 * 批量获取学生信息
 * @param ids 学生ID数组
 * @returns 学生列表
 */
export async function getStudentsByIds(ids: string[]): Promise<Student[]> {
  try {
    const response = await post(`${API_BASE}/students/batch`, { ids });
    return response.data.list || [];
  } catch (error) {
    console.error('批量获取学生信息失败:', error);
    return [];
  }
}

/**
 * 获取教室中的学生列表
 * @param classroomId 教室ID
 * @returns 学生列表
 */
export async function getClassroomStudents(classroomId: string): Promise<Student[]> {
  try {
    const response = await get(`/api/v1/classrooms/${classroomId}/students`);
    return response.data.list || [];
  } catch (error) {
    console.error('获取教室学生列表失败:', error);
    return [];
  }
}

/**
 * 向教室添加学生
 * @param classroomId 教室ID
 * @param studentIds 学生ID数组
 * @param teacherId 教师ID（可选，用于权限验证）
 * @returns 成功消息
 */
export async function addStudentsToClassroom(
  classroomId: string,
  studentIds: string[],
  teacherId?: number
): Promise<{ success: boolean; message: string }> {
  try {
    // 从localStorage获取当前用户信息（应用使用userInfo键）
    const userStr = localStorage.getItem('userInfo');
    const user = userStr ? JSON.parse(userStr) : null;
    const currentTeacherId = teacherId || user?.id;

    // 后端需要teacher_id作为查询参数
    const url = currentTeacherId
      ? `/api/v1/classrooms/${classroomId}/students?teacher_id=${currentTeacherId}`
      : `/api/v1/classrooms/${classroomId}/students`;

    const response = await post(url, {
      student_ids: studentIds.map(id => parseInt(id))
    });
    return {
      success: response.code === '0000',
      message: response.message || '添加学生成功'
    };
  } catch (error: any) {
    console.error('添加学生失败:', error);
    return {
      success: false,
      message: error.response?.data?.message || '添加学生失败'
    };
  }
}

/**
 * 从教室移除学生
 * @param classroomId 教室ID
 * @param studentIds 学生ID数组
 * @returns 成功消息
 */
export async function removeStudentsFromClassroom(
  classroomId: string,
  studentIds: string[]
): Promise<{ success: boolean; message: string }> {
  try {
    const response = await del(`/api/v1/classrooms/${classroomId}/students`, {
      data: { student_ids: studentIds }
    });
    return {
      success: response.code === '0000',
      message: response.message || '移除学生成功'
    };
  } catch (error: any) {
    console.error('移除学生失败:', error);
    return {
      success: false,
      message: error.response?.data?.message || '移除学生失败'
    };
  }
}

/**
 * 获取可添加到教室的学生列表（未在该教室中的学生）
 * @param classroomId 教室ID
 * @param params 查询参数
 * @returns 学生列表
 */
export async function getAvailableStudentsForClassroom(
  classroomId: string,
  params?: {
    keyword?: string;
    organization_id?: string;
    department?: string;
    major?: string;
    grade?: string;
  }
): Promise<Student[]> {
  try {
    // 修复：后端API路径是 /students/available，不是 /available-students
    const response = await get(`/api/v1/classrooms/${classroomId}/students/available`, params);
    // 后端返回格式: { available_students: { list: [...] } }
    return response.data?.available_students?.list || response.data?.list || [];
  } catch (error) {
    console.error('获取可添加学生列表失败:', error);
    return [];
  }
}

// 添加新学生
export async function addStudent(student: Partial<Student>): Promise<Student | null> {
  try {
    // 转换前端字段到后端字段
    const studentData = {
      student_number: student.studentId || student.student_number,
      name: student.name,
      gender: student.gender,
      phone: student.phone,
      email: student.email,
      school_id: 1,
      class_id: student.class_id
    };
    const response = await post(`${API_BASE}/students`, studentData);
    return response.data;
  } catch (error) {
    console.error('添加学生失败:', error);
    return null;
  }
}

// 更新学生信息
export async function updateStudent(id: string, student: Partial<Student>): Promise<Student | null> {
  try {
    const response = await put(`${API_BASE}/students/${id}`, student);
    return response.data;
  } catch (error) {
    console.error('更新学生信息失败:', error);
    return null;
  }
}

// 删除学生
export async function deleteStudent(id: string): Promise<boolean> {
  try {
    const response = await del(`${API_BASE}/students/${id}`);
    return response.code === '0000';
  } catch (error) {
    console.error('删除学生失败:', error);
    return false;
  }
}

// 批量更新学生状态
export async function batchUpdateStatus(ids: string[], isActive: boolean): Promise<boolean> {
  try {
    const response = await post(`${API_BASE}/students/batch-status`, {
      ids: ids.map(id => parseInt(id)),
      is_active: isActive
    });
    return response.code === '0000';
  } catch (error) {
    console.error('批量更新学生状态失败:', error);
    return false;
  }
}

// 批量删除学生
export async function batchDeleteStudents(ids: string[]): Promise<boolean> {
  try {
    const response = await post(`${API_BASE}/students/batch-delete`, {
      ids: ids.map(id => parseInt(id)),
      is_active: false  // 复用BatchStatusUpdate schema
    });
    return response.code === '0000';
  } catch (error) {
    console.error('批量删除学生失败:', error);
    return false;
  }
}

// 批量调动学生
export async function batchTransferStudents(ids: string[], targetClassId: number): Promise<boolean> {
  try {
    const response = await post(`${API_BASE}/students/batch-transfer`, {
      student_ids: ids.map(id => parseInt(id)),
      target_class_id: targetClassId
    });
    return response.code === '0000';
  } catch (error) {
    console.error('批量调动学生失败:', error);
    return false;
  }
}

// 导入学生
export async function importStudents(file: File, schoolId: number = 1): Promise<any> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('school_id', schoolId.toString());
    const response = await post(`${API_BASE}/students/import`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response;
  } catch (error) {
    console.error('导入学生失败:', error);
    throw error;
  }
}

// 下载导入模板
export function getImportTemplateUrl(): string {
  return `${API_BASE}/students/export/template`;
} 