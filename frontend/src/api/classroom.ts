import { get, post, put, del } from '../utils/request';
import type { 
  ClassroomDetail, 
  CourseItem, 
  CourseStatus, 
  CourseType,
  Student,
  StudentProgress,
  ApiResponse,
  CreateClassroomRequest,
  UpdateClassroomRequest,
  AddStudentsRequest,
  PublishCourseRequest
} from '../types/classroom';
import { useUserStore } from '@/stores/user';

/**
 * 获取当前教师ID
 */
function getTeacherId(): number | undefined {
  const userStore = useUserStore();
  return userStore.userId;
}

/**
 * 获取课堂列表
 * @param status 课堂状态：ongoing-进行中，upcoming-即将开始，past-已结束
 * @param role 用户角色：student-学生，teacher-教师，admin-管理员
 * @returns 课堂列表
 */
export async function getClassrooms(
  status: 'ongoing' | 'upcoming' | 'past' = 'ongoing',
  role: string = 'teacher',
  studentId?: string
): Promise<ClassroomDetail[]> {
  try {
    if (role === 'student') {
      // 学生API返回分组数据，一次性获取所有状态
      const endpoint = '/api/v1/user/classrooms';
      const params: any = {};
      if (studentId) {
        params.student_id = studentId;
      }
      const response = await get(endpoint, params);

      // 返回请求的状态对应的数据
      return response.data[status] || [];
    } else {
      // 教师API按状态分别调用
      const endpoint = '/api/v1/my-classrooms';
      const teacherId = getTeacherId();
      const params: any = {};
      if (teacherId) {
        params.teacher_id = teacherId;
      }
      const response = await get(endpoint, params);

      // 根据状态返回对应的课堂列表
      return response.data[status] || [];
    }
  } catch (error) {
    console.error('获取课堂列表失败:', error);
    return [];
  }
}

/**
 * 获取我的课堂列表（教师用于实训资源库）
 * @returns 我的课堂列表
 */
export async function getMyClassrooms(): Promise<{ data: ClassroomDetail[] }> {
  try {
    const teacherId = getTeacherId();
    const params: any = {};
    if (teacherId) {
      params.teacher_id = teacherId;
    }
    const response = await get('/api/v1/my-classrooms', params);
    return response;
  } catch (error) {
    console.error('获取我的课堂列表失败:', error);
    return { data: [] };
  }
}

/**
 * 获取课堂详情
 * @param id 课堂ID
 * @returns 课堂详情
 */
export async function getClassroomDetail(id: string): Promise<ClassroomDetail | null> {
  try {
    const response = await get(`/api/v1/classrooms/${id}`, {
      enhanced: true
    });
    return response.data;
  } catch (error) {
    console.error('获取课堂详情失败:', error);
    return null;
  }
}

/**
 * 创建新课堂
 * @param classroom 课堂信息
 * @returns 创建后的课堂信息
 */
export async function createClassroom(classroom: Partial<ClassroomDetail>): Promise<ClassroomDetail> {
  if (!classroom.teacherId) {
    throw new Error('教师ID不能为空');
  }
  try {
    const response = await post('/api/v1/classrooms', {
      name: classroom.name,
      credits: classroom.credits,
      start_date: classroom.startDate,
      end_date: classroom.endDate,
      teacher_id: classroom.teacherId
    });
    return response.data;
  } catch (error) {
    console.error('创建课堂失败:', error);
    throw error;
  }
}

/**
 * 更新课堂信息
 * @param id 课堂ID
 * @param data 要更新的课堂信息
 * @returns 更新后的课堂信息
 */
export async function updateClassroom(id: string, data: Partial<ClassroomDetail>): Promise<ClassroomDetail | null> {
  try {
    const response = await put(`/api/v1/classrooms/${id}`, {
      name: data.name,
      credits: data.credits,
      start_date: data.startDate,
      end_date: data.endDate
    });
    return response.data;
  } catch (error) {
    console.error('更新课堂失败:', error);
    return null;
  }
}

/**
 * 删除课堂
 * @param id 课堂ID
 * @returns 操作结果
 */
export async function deleteClassroom(id: string): Promise<{ success: boolean; message?: string }> {
  try {
    await del(`/api/v1/classrooms/${id}`);
    return { success: true };
  } catch (error: any) {
    console.error('删除课堂失败:', error);
    return { 
      success: false, 
      message: error.response?.data?.message || '删除课堂失败，请重试' 
    };
  }
}

/**
 * 获取课堂中的课程列表
 * @param classroomId 课堂ID
 * @returns 课程列表
 */
export async function getCourses(classroomId: string): Promise<CourseItem[]> {
  try {
    const response = await get(`/api/v1/classrooms/${classroomId}/courses`);
    return response.data.list || [];
  } catch (error) {
    console.error('获取课程列表失败:', error);
    return [];
  }
}

/**
 * 发布课程
 * @param classroomId 课堂ID
 * @param courseIds 课程ID数组
 * @param settings 发布设置
 * @returns 发布结果
 */
export async function publishCourse(
  classroomId: string,
  courseIds: string[],
  settings?: any
): Promise<boolean> {
  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/courses/publish`, {
      course_ids: courseIds,
      ...settings
    });
    return response.code === '0000';
  } catch (error) {
    console.error('发布课程失败:', error);
    return false;
  }
}

/**
 * 删除课程
 * @param classroomId 课堂ID
 * @param courseIds 课程ID数组
 * @returns 操作结果
 */
export async function removeCourse(classroomId: string, courseIds: string[]): Promise<boolean> {
  try {
    const response = await del(`/api/v1/classrooms/${classroomId}/courses`, {
      data: { course_ids: courseIds }
    });
    return response.code === '0000';
  } catch (error) {
    console.error('删除课程失败:', error);
    return false;
  }
}

/**
 * 获取课堂学生列表
 * @param classroomId 课堂ID
 * @returns 学生列表
 */
export async function getClassroomStudents(classroomId: string): Promise<Student[]> {
  try {
    const response = await get(`/api/v1/classrooms/${classroomId}/students`);
    return response.data.list || [];
  } catch (error) {
    console.error('获取课堂学生列表失败:', error);
    return [];
  }
}

/**
 * 添加学生到课堂
 * @param classroomId 课堂ID
 * @param studentIds 学生ID数组
 * @returns 操作结果
 */
export async function addStudentsToClassroom(
  classroomId: string, 
  studentIds: string[]
): Promise<boolean> {
  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/students`, {
      student_ids: studentIds
    });
    return response.code === '0000';
  } catch (error) {
    console.error('添加学生失败:', error);
    return false;
  }
}

/**
 * 从课堂移除学生
 * @param classroomId 课堂ID
 * @param studentIds 学生ID数组
 * @returns 操作结果
 */
export async function removeStudentsFromClassroom(
  classroomId: string, 
  studentIds: string[]
): Promise<boolean> {
  try {
    const response = await del(`/api/v1/classrooms/${classroomId}/students`, {
      data: { student_ids: studentIds }
    });
    return response.code === '0000';
  } catch (error) {
    console.error('移除学生失败:', error);
    return false;
  }
}

/**
 * 获取可添加到课堂的学生列表
 * @param classroomId 课堂ID
 * @returns 可添加的学生列表
 */
export async function getAvailableStudents(classroomId: string): Promise<Student[]> {
  try {
    const response = await get(`/api/v1/classrooms/${classroomId}/available-students`);
    return response.data.list || [];
  } catch (error) {
    console.error('获取可添加学生列表失败:', error);
    return [];
  }
}

/**
 * 搜索学生
 * @param keyword 搜索关键词
 * @returns 符合条件的学生列表
 */
export async function searchStudentsByKeyword(keyword: string): Promise<Student[]> {
  try {
    const response = await get('/api/v1/students/search', {
      keyword,
      limit: 50
    });
    return response.data.list || [];
  } catch (error) {
    console.error('搜索学生失败:', error);
    return [];
  }
}

/**
 * 向课堂添加课程
 * @param classroomId 课堂ID
 * @param course 课程信息
 * @returns 添加后的课程信息
 */
export async function addCourseToClassroom(
  classroomId: string, 
  course: Partial<CourseItem>,
  teacherId: number
): Promise<CourseItem | null> {
  if (!teacherId) {
    throw new Error('教师ID不能为空');
  }
  try {
    const response = await post(`/api/v1/classrooms/${classroomId}/courses`, {
      course_id: course.id,
      classroom_chapter_title: course.chapter,
      teacher_id: teacherId
    });
    return response.data;
  } catch (error) {
    console.error('添加课程失败:', error);
    return null;
  }
} 