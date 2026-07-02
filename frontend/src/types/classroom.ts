/**
 * 课堂相关类型定义
 */

// 课堂详情
export interface ClassroomDetail {
  id: string;
  name: string;
  credits: number;
  status: 'ongoing' | 'upcoming' | 'past';
  startDate: string;
  endDate: string;
  studentCount: number;
  teacherId?: number;
  teacherName?: string;
  teacherAvatar?: string;
  coverImage?: string;
  description?: string;
  courses?: CourseItem[];
  chapters?: ChapterItem[];
  students?: Student[];
  createdAt?: string;
  updatedAt?: string;
}

// 章节信息
export interface ChapterItem {
  id: string;
  name: string;
  order: number;
  courses: CourseItem[];
  status?: number;
}

// 课程项目
export interface CourseItem {
  id: string;
  classroom_course_id?: string | number;
  classroomCourseId?: string | number;
  course_id?: string | number;
  practice_id?: string | number;
  original_course_id?: string | number;
  source_type?: string;
  title?: string;
  course_name?: string;
  name: string;
  name_override: string;
  type: CourseType;
  status: CourseStatus;
  coins: number;
  difficulty: number;
  is_required: boolean;
  order: number;
  created_at: string;
  updated_at?: string;
  startDate?: string;
  endDate?: string;
  learningCount?: number;
  completedCount?: number;
  notStartedCount?: number;
  completionRate?: number;
}

// 课程类型
export type CourseType = 'practice' | 'training' | 'exam' | 'homework';

// 课程状态
export type CourseStatus = 'unpublished' | 'learning' | 'makeup' | 'completed';

// 学生信息
export interface Student {
  id: number;
  studentId: string;
  name: string;
  avatar?: string;
  gender?: 'male' | 'female';
  department?: string;
  major?: string;
  class?: string;
  grade?: string;
  email?: string;
  phone?: string;
  status?: 'active' | 'inactive';
  joinedAt?: string;
  lastActiveAt?: string;
  learningProgress?: number;
  completedCourses?: number;
  totalCourses?: number;
}

// 学生进度
export interface StudentProgress {
  studentId: string;
  courseId: string;
  status: 'not_started' | 'in_progress' | 'completed';
  progress: number;
  startedAt?: string;
  completedAt?: string;
  score?: number;
}

// API 响应格式
export interface ApiResponse<T> {
  code: string;
  message: string;
  data: T;
}

// 课堂创建请求
export interface CreateClassroomRequest {
  name: string;
  credits: number;
  start_date: string;
  end_date: string;
  teacher_id?: number;
  description?: string;
}

// 课堂更新请求
export interface UpdateClassroomRequest {
  name?: string;
  credits?: number;
  start_date?: string;
  end_date?: string;
  description?: string;
}

// 添加学生请求
export interface AddStudentsRequest {
  student_ids: string[];
  classroom_id: string;
}

// 课程发布请求
export interface PublishCourseRequest {
  course_id: string;
  start_date?: string;
  end_date?: string;
  is_makeup?: boolean;
}
