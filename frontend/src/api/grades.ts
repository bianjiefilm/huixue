import { request } from '@/utils/request';
import type { ApiResponse } from '@/utils/request';

// 成绩相关的类型定义
export interface StudentGrade {
  id: string;
  student_id: number;
  student_name: string;
  student_number: string;
  assignment_status: string;
  submission_time: string | null;
  completed_levels?: number;
  total_levels?: number;
  total_duration?: number;
  level_score?: number;
  penalty_score?: number;
  final_score: number;
  grading_status?: string;
  teacher_feedback?: string;
  is_excellent?: boolean;
}

export interface CourseGradeStats {
  total_students: number;
  not_started: number;
  in_progress: number;
  completed: number;
  late_completed: number;
}

export interface TrainingAssignment {
  id: string;
  student_id: number;
  student_name: string;
  student_number: string;
  submission_status: string;
  grading_status: string;
  started_at: string | null;
  submitted_at: string | null;
  score: number | null;
  final_score: number | null;
  teacher_feedback: string | null;
  is_excellent: boolean;
  design_files?: string[];
  experiment_reports?: string[];
}

export interface GradeListResponse {
  list: StudentGrade[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  stats: CourseGradeStats;
}

export interface AssignmentListResponse {
  list: TrainingAssignment[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  stats: {
    total_students: number;
    not_started: number;
    not_submitted: number;
    submitted: number;
    late_submitted: number;
    graded: number;
    not_graded: number;
  };
}

export interface PenaltyUpdateRequest {
  penalty_score: number;
  reason?: string;
}

export interface BatchPenaltyUpdateRequest {
  student_ids: number[];
  penalty_score: number;
  reason?: string;
}

export interface TrainingGradingRequest {
  score: number;
  feedback: string;
  is_excellent?: boolean;
}

export interface AssignmentDetail {
  student_id: number;
  student_name: string;
  student_number: string;
  avatar_url: string | null;
  submission_status: string;
  submission_time: string | null;
  design_files: string[];
  experiment_reports: string[];
  grading_status: string;
  score: number | null;
  final_score: number | null;
  penalty_score: number;
  teacher_feedback: string | null;
  is_excellent: boolean;
  graded_at: string | null;
  graded_by_teacher_name: string | null;
  can_grade: boolean;
}

export interface ExcellentWork {
  id: number;
  classroom_course_id?: number;
  course_name?: string;
  course_type?: string;
  student_id: number;
  student_name: string;
  student_number: string;
  avatar_url: string | null;
  submission_time: string;
  score: number;
  final_score: number;
  teacher_feedback: string;
  graded_at: string;
  graded_by_teacher_name: string;
  design_files?: string[];
  experiment_reports?: string[];
  can_view_details: boolean;
}

export interface ExportGradeResponse {
  format: string;
  total_records: number;
  export_time: string;
  include_details: boolean;
  download_url: string;
}

// API 函数

/**
 * 获取待评分列表 (P3 新 API)
 */
export async function getSubmissions(params: {
  teacher_id: number;
  classroom_id: number;
  course_id: number;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<any>> {
  const { teacher_id, classroom_id, course_id, ...queryParams } = params;
  return request.get(`/api/v1/teachers/${teacher_id}/classrooms/${classroom_id}/courses/${course_id}/submissions`, {
    params: queryParams
  });
}

/**
 * 提交成绩 (P3 新 API)
 */
export async function submitGrade(params: {
  teacher_id: number;
  classroom_id: number;
  course_id: number;
  student_id: number;
  overall_score: number;
  teacher_penalties?: number;
  teacher_feedback?: string;
  is_excellent_work?: boolean;
}): Promise<ApiResponse<any>> {
  const { teacher_id, classroom_id, course_id, ...data } = params;
  return request.post(`/api/v1/teachers/${teacher_id}/classrooms/${classroom_id}/courses/${course_id}/grade`, data);
}

/**
 * 获取课程成绩列表 (兼容旧 API)
 */
export async function getCourseGrades(params: {
  classroom_id: number;
  classroom_course_id: number;
  teacher_id: number;
  status?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<GradeListResponse>> {
  const { classroom_id, classroom_course_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/courses/${classroom_course_id}/grades`, {
    params: queryParams
  });
}

/**
 * 获取课程成绩统计信息
 */
export async function getCourseGradeStatistics(params: {
  classroom_course_id: number;
  teacher_id: number;
}): Promise<ApiResponse<any>> {
  const { classroom_course_id, ...queryParams } = params;
  return request.get(`/api/v1/classroom-courses/${classroom_course_id}/statistics`, {
    params: queryParams
  });
}

/**
 * 更新学生奖惩扣分
 */
export async function updateStudentPenalty(params: {
  progress_id: number;
  teacher_id: number;
  data: PenaltyUpdateRequest;
}): Promise<ApiResponse<{
  id: number;
  penalty_score: number;
  final_score: number;
}>> {
  const { progress_id, teacher_id, data } = params;
  return request.patch(`/api/v1/student-progress/${progress_id}/penalty`, data, {
    params: { teacher_id }
  });
}

/**
 * 批量更新学生奖惩扣分
 */
export async function batchUpdateStudentPenalty(params: {
  classroom_course_id: number;
  teacher_id: number;
  data: BatchPenaltyUpdateRequest;
}): Promise<ApiResponse<{
  updated_count: number;
  penalty_score: number;
}>> {
  const { classroom_course_id, teacher_id, data } = params;
  return request.patch(`/api/v1/classroom-courses/${classroom_course_id}/batch-penalty`, data, {
    params: { teacher_id }
  });
}

/**
 * 获取实训作业列表
 */
export async function getTrainingAssignments(params: {
  classroom_course_id: number;
  teacher_id: number;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<AssignmentListResponse>> {
  const { classroom_course_id, ...queryParams } = params;
  return request.get(`/api/v1/classroom-courses/${classroom_course_id}/assignments`, {
    params: queryParams
  });
}

/**
 * 实训作业点评
 */
export async function gradeTrainingAssignment(params: {
  classroom_course_id: number;
  student_id: number;
  teacher_id: number;
  data: TrainingGradingRequest;
}): Promise<ApiResponse<{
  student_id: number;
  score: number;
  final_score: number;
  feedback: string;
  is_excellent: boolean;
  graded_at: string;
}>> {
  const { classroom_course_id, student_id, teacher_id, data } = params;
  return request.post(
    `/api/v1/classroom-courses/${classroom_course_id}/students/${student_id}/grade`, 
    data,
    { params: { teacher_id } }
  );
}

/**
 * 获取学生作业详情（实训课程）
 */
export async function getStudentAssignmentDetail(params: {
  classroom_course_id: number;
  student_id: number;
  teacher_id: number;
}): Promise<ApiResponse<AssignmentDetail>> {
  const { classroom_course_id, student_id, teacher_id } = params;
  return request.get(
    `/api/v1/classroom-courses/${classroom_course_id}/students/${student_id}/assignment`,
    { params: { teacher_id } }
  );
}

/**
 * 获取优秀作业列表（按课程）
 */
export async function getExcellentWorks(params: {
  classroom_course_id: number;
  page?: number;
  page_size?: number;
  teacher_id?: number;
  student_id?: number;
}): Promise<ApiResponse<{
  list: ExcellentWork[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  course_info: {
    course_name: string;
    course_type: string;
    classroom_name: string;
  };
}>> {
  const { classroom_course_id, ...queryParams } = params;
  return request.get(`/api/v1/classroom-courses/${classroom_course_id}/excellent-works`, {
    params: queryParams
  });
}

/**
 * 获取课堂所有优秀作业列表
 */
export async function getClassroomExcellentWorks(params: {
  classroom_id: number;
  course_type?: string;
  page?: number;
  page_size?: number;
  teacher_id?: number;
  student_id?: number;
}): Promise<ApiResponse<{
  list: ExcellentWork[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/excellent-works`, {
    params: queryParams
  });
}

/**
 * 导出课程成绩
 */
export async function exportCourseGrades(params: {
  classroom_course_id: number;
  teacher_id: number;
  format?: string;
  include_details?: boolean;
}): Promise<ApiResponse<ExportGradeResponse>> {
  const { classroom_course_id, ...queryParams } = params;
  return request.get(`/api/v1/classroom-courses/${classroom_course_id}/export-grades`, {
    params: {
      format: 'excel',
      include_details: true,
      ...queryParams
    }
  });
}

// 学生成绩单相关的类型定义
export interface StudentTranscript {
  student_id: number;
  student_name: string;
  student_number: string;
  avatar_url: string | null;
  class_name?: string;
  statistics: {
    average_score: number;
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
    score: number;
    status: string;
    level_progress?: number;
    study_time_minutes: number;
    complete_time: string | null;
    submitted_work_count?: number;
    is_excellent?: boolean;
  }[];
}

/**
 * 获取学生成绩单 (P3 新 API)
 */
export async function getStudentGrades(params: {
  student_id: number;
  classroom_id: number;
}): Promise<ApiResponse<any>> {
  const { student_id, classroom_id } = params;
  return request.get(`/api/v1/students/${student_id}/classrooms/${classroom_id}/grades`);
}

/**
 * 获取排名列表 (P3 新 API)
 */
export async function getGradeRankings(params: {
  classroom_id: number;
  course_id?: number;
  sort_by?: string;
  limit?: number;
}): Promise<ApiResponse<any>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/grade-rankings`, {
    params: queryParams
  });
}

/**
 * 获取班级学情总览 (P3 新 API)
 */
export async function getAnalyticsOverview(params: {
  teacher_id: number;
  classroom_id: number;
}): Promise<ApiResponse<any>> {
  const { teacher_id, classroom_id } = params;
  return request.get(`/api/v1/teachers/${teacher_id}/classrooms/${classroom_id}/analytics/overview`);
}

/**
 * 获取课程统计 (P3 新 API)
 */
export async function getCourseStats(params: {
  teacher_id: number;
  classroom_id: number;
}): Promise<ApiResponse<any>> {
  const { teacher_id, classroom_id } = params;
  return request.get(`/api/v1/teachers/${teacher_id}/classrooms/${classroom_id}/analytics/course-stats`);
}

/**
 * 获取学生成绩单 (兼容旧 API)
 */
export async function getStudentTranscript(params: {
  classroom_id: number;
  student_id: number;
}): Promise<ApiResponse<StudentTranscript>> {
  const { classroom_id, student_id } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/learning/transcript/${student_id}`);
}

// 辅助函数

/**
 * 获取作业状态文本
 */
export function getAssignmentStatusText(status: string, courseType: 'practice' | 'training'): string {
  if (courseType === 'practice') {
    const statusMap: Record<string, string> = {
      'not_started': '未开始',
      'not_completed': '未通关',
      'completed_on_time': '按时通关',
      'completed_late': '补交通关'
    };
    return statusMap[status] || status;
  } else {
    const statusMap: Record<string, string> = {
      'not_started': '未开始',
      'not_submitted': '未提交',
      'submitted': '已提交',
      'late_submitted': '已补交'
    };
    return statusMap[status] || status;
  }
}

/**
 * 获取作业状态颜色
 */
export function getAssignmentStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    'not_started': 'default',
    'not_completed': 'blue',
    'not_submitted': 'blue',
    'completed_on_time': 'green',
    'submitted': 'green',
    'completed_late': 'orange',
    'late_submitted': 'orange'
  };
  return colorMap[status] || 'default';
}

/**
 * 获取点评状态文本
 */
export function getGradingStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'NOT_GRADED': '未点评',
    'GRADED': '已点评'
  };
  return statusMap[status] || status;
}

/**
 * 获取点评状态颜色
 */
export function getGradingStatusColor(status: string): string {
  return status === 'GRADED' ? 'green' : 'orange';
}

/**
 * 格式化时长（分钟转为小时和分钟）
 */
export function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return hours > 0 ? `${hours}小时${mins}分钟` : `${mins}分钟`;
}