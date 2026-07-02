import { request } from '@/utils/request';
import type { ApiResponse } from '@/types';

// 学情分析相关的类型定义

// 学情总览
export interface LearningOverview {
  classroom_info: {
    classroom_id: number;
    classroom_name: string;
    start_date: string;
    end_date: string;
    practice_courses_total: number;
    practice_courses_published: number;
    training_courses_total: number;
    training_courses_published: number;
  };
  course_completion: {
    completed: number;
    learning: number;
    makeup: number;
    not_published: number;
  };
  online_status: {
    online_count: number;
    offline_count: number;
  };
  statistics: {
    average_score: number;
    top_students: {
      student_id: number;
      student_name: string;
      average_score: number;
    }[];
    study_time_stats: {
      student_id: number;
      student_name: string;
      student_number: string;
      total_study_hours: number;
    }[];
    course_avg_scores: {
      course_id: number;
      course_name: string;
      chapter?: string;
      average_score: number;
      completed_count: number;
    }[];
  };
}

// 学生学习统计（必修/拓展课程）
export interface StudentLearningStats {
  student_id: number;
  student_name: string;
  student_number: string;
  online_status: 'online' | 'offline';
  grade?: string;
  class_name?: string;
  practice_completed: number;
  practice_average_score: number;
  training_completed: number;
  training_average_score: number;
  course_average_score: number;
  total_study_hours: number;
}

export interface LearningStudentsResponse {
  list: StudentLearningStats[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  summary: {
    total_students: number;
    online_students: number;
    avg_practice_score: number;
    avg_training_score: number;
    avg_overall_score: number;
  };
}

// 学生成绩单
export interface StudentTranscript {
  student_id: number;
  student_name: string;
  student_number: string;
  avatar_url: string | null;
  class_name?: string;
  grade?: string;
  statistics: {
    course_average_score: number;
    ranking: number;
    total_study_hours: number;
    completed_courses: number;
    total_courses: number;
    excellent_assignments: number;
  };
  courses: {
    course_id: number;
    course_name: string;
    course_type: 'PRACTICE' | 'TRAINING';
    is_required: boolean;
    status: string;
    level_progress?: number;
    study_time_minutes: number;
    complete_time: string | null;
    course_score: number;
    submitted_work_count?: number;
    is_excellent?: boolean;
  }[];
}

// 导出请求
export interface ExportAnalyticsRequest {
  course_type: 'required' | 'optional';
  selected_student_ids?: number[];
  export_format: 'excel' | 'csv';
}

export interface ExportAnalyticsResponse {
  export_type: 'selected' | 'all';
  export_count: number;
  export_format: string;
  export_filename: string;
  export_url: string;
  created_at: string;
}

// API 函数

/**
 * 获取学情总览
 */
export async function getLearningOverview(params: {
  classroom_id: number;
  teacher_id: number;
}): Promise<ApiResponse<LearningOverview>> {
  const { classroom_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/learning/overview`, {
    params: { teacher_id }
  });
}

/**
 * 获取学生学习统计（必修课程统计/拓展课程统计）
 */
export async function getLearningStudents(params: {
  classroom_id: number;
  teacher_id: number;
  course_type: 'required' | 'optional';
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<LearningStudentsResponse>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/learning/students`, {
    params: queryParams
  });
}

/**
 * 获取学生个人成绩单
 */
export async function getStudentTranscript(params: {
  classroom_id: number;
  student_id: number;
  teacher_id: number;
}): Promise<ApiResponse<StudentTranscript>> {
  const { classroom_id, student_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/learning/transcript/${student_id}`, {
    params: { teacher_id }
  });
}

/**
 * 导出学情分析数据
 */
export async function exportLearningAnalytics(params: {
  classroom_id: number;
  teacher_id: number;
  course_type: 'required' | 'optional';
  student_ids?: number[];
}): Promise<Blob> {
  const { classroom_id, teacher_id, course_type, student_ids } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/learning/export`, {
    params: {
      teacher_id,
      course_type,
      student_ids: student_ids?.join(',') || ''
    },
    responseType: 'blob'
  });
}

// 兼容旧版本的API函数（如果需要）

/**
 * 获取课堂分析总览（兼容旧版本）
 */
export async function getClassroomAnalyticsOverview(params: {
  classroom_id: number;
  teacher_id: number;
}): Promise<ApiResponse<any>> {
  const { classroom_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/analytics/overview`, {
    params: { teacher_id }
  });
}

/**
 * 获取必修课程统计（兼容旧版本）
 */
export async function getMandatoryCoursesAnalytics(params: {
  classroom_id: number;
  teacher_id: number;
}): Promise<ApiResponse<any>> {
  const { classroom_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/analytics/mandatory-courses`, {
    params: { teacher_id }
  });
}

/**
 * 获取拓展课程统计（兼容旧版本）
 */
export async function getElectiveCoursesAnalytics(params: {
  classroom_id: number;
  teacher_id: number;
}): Promise<ApiResponse<any>> {
  const { classroom_id, teacher_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/analytics/elective-courses`, {
    params: { teacher_id }
  });
}

// 辅助函数

/**
 * 获取在线状态文本
 */
export function getOnlineStatusText(status: 'online' | 'offline'): string {
  return status === 'online' ? '在线' : '离线';
}

/**
 * 获取在线状态颜色
 */
export function getOnlineStatusColor(status: 'online' | 'offline'): string {
  return status === 'online' ? 'green' : 'default';
}

/**
 * 获取课程状态文本
 */
export function getCourseStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'not_started': '未开始',
    'learning': '学习中',
    'completed': '已完成',
    'makeup': '补交中',
    'not_published': '未发布'
  };
  return statusMap[status] || status;
}

/**
 * 获取课程状态颜色
 */
export function getCourseStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    'not_started': 'default',
    'learning': 'blue',
    'completed': 'green',
    'makeup': 'orange',
    'not_published': 'default'
  };
  return colorMap[status] || 'default';
}

/**
 * 格式化学习时长（小时）
 */
export function formatStudyHours(hours: number): string {
  if (hours < 1) {
    return `${Math.round(hours * 60)}分钟`;
  }
  return `${hours.toFixed(1)}小时`;
}

/**
 * 格式化分数
 */
export function formatScore(score: number): string {
  return score.toFixed(1);
}