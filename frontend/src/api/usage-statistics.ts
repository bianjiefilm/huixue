import request from '@/utils/http';

// 时间范围枚举
export enum TimeRange {
  TODAY = 'today',
  YESTERDAY = 'yesterday',
  LAST_7_DAYS = 'last_7_days',
  LAST_30_DAYS = 'last_30_days',
  CUSTOM = 'custom'
}

// 用户组枚举
export enum UserGroup {
  TEACHER = 'teacher',
  STUDENT = 'student'
}

// 基础分页参数
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// 时间筛选参数
export interface TimeFilterParams {
  time_range?: TimeRange;
  start_date?: string; // YYYY-MM-DD格式
  end_date?: string;   // YYYY-MM-DD格式
}

// 基础统计请求参数
export interface BaseStatisticsParams extends PaginationParams, TimeFilterParams {}

// 课程统计请求参数
export interface CourseStatisticsParams extends BaseStatisticsParams {
  course_name?: string; // 课程名称筛选
}

// 课程统计项
export interface CourseStatisticsItem {
  course_id: number;
  course_name: string;
  access_count: number;        // 访问次数
  access_users: number;        // 访问人数
  avg_access_per_user: number; // 人均访问次数
  classroom_creation_count: number; // 创建课堂次数
  course_type: string;         // 课程类型
  created_at: string;
}

// 课程统计响应
export interface CourseStatisticsResponse {
  data: CourseStatisticsItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 实践统计请求参数
export interface PracticeStatisticsParams extends BaseStatisticsParams {
  user_group?: UserGroup;      // 用户组筛选
  practice_name?: string;      // 实践名称筛选
}

// 实践统计项
export interface PracticeStatisticsItem {
  practice_id: number;
  practice_name: string;
  access_count: number;        // 访问次数
  access_users: number;        // 访问人数
  avg_access_per_user: number; // 人均访问次数
  learning_count: number;      // 学习次数
  learning_duration: number;   // 学习时长（分钟）
  add_to_classroom_count: number; // 添加到课堂次数
}

// 实践统计响应
export interface PracticeStatisticsResponse {
  data: PracticeStatisticsItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 实训统计请求参数
export interface TrainingStatisticsParams extends BaseStatisticsParams {
  user_group?: UserGroup;      // 用户组筛选
  training_name?: string;      // 实训名称筛选
}

// 实训统计项
export interface TrainingStatisticsItem {
  training_id: number;
  training_name: string;
  access_count: number;        // 访问次数
  access_users: number;        // 访问人数
  avg_access_per_user: number; // 人均访问次数
  learning_count: number;      // 学习次数
  learning_duration: number;   // 学习时长（分钟）
  add_to_classroom_count: number; // 添加到课堂次数
}

// 实训统计响应
export interface TrainingStatisticsResponse {
  data: TrainingStatisticsItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 教师使用统计请求参数
export interface TeacherUsageParams extends BaseStatisticsParams {
  name?: string;           // 教师姓名筛选
  employee_id?: string;    // 工号筛选
  college?: string;        // 学院筛选
}

// 教师使用统计项
export interface TeacherUsageItem {
  teacher_id: number;
  real_name: string;
  employee_id?: string;    // 工号
  organization_name?: string; // 学院
  classroom_count: number;           // 创建课堂数
  practice_count: number;            // 创建实践数
  personal_practice_count: number;   // 个人发布实践数
  public_practice_count: number;     // 公开发布实践数
  training_count: number;            // 创建实训数
  personal_training_count: number;   // 个人发布实训数
  public_training_count: number;     // 公开发布实训数
}

// 教师使用统计响应
export interface TeacherUsageResponse {
  data: TeacherUsageItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 学生使用统计请求参数
export interface StudentUsageParams extends BaseStatisticsParams {
  name?: string;           // 学生姓名筛选
  student_id?: string;     // 学号筛选
  college?: string;        // 学院筛选
  major?: string;          // 专业筛选
}

// 学生使用统计项
export interface StudentUsageItem {
  student_id: number;
  real_name: string;
  employee_id?: string;    // 学号
  organization_name?: string; // 学院
  login_count: number;               // 登录次数
  practice_start_count: number;      // 开始实践次数
  practice_learning_duration: number; // 实践学习时长（分钟）
  resource_learning_duration: number; // 教学资源学习时长（分钟）
  training_start_count: number;      // 开始实训次数
  training_learning_duration: number; // 实训学习时长（分钟）
  playground_project_count: number;  // 创建数据游乐场项目数
}

// 学生使用统计响应
export interface StudentUsageResponse {
  data: StudentUsageItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 课程详细统计请求参数
export interface CourseDetailStatisticsParams extends BaseStatisticsParams {
  course_id: number;
}

// 课程详细统计项
export interface CourseDetailStatisticsItem {
  user_id: number;
  real_name: string;
  employee_id?: string;    // 工号/学号
  organization_name?: string; // 学院
  college?: string;        // 学院
  major?: string;          // 专业
  access_count: number;              // 访问次数
  learning_count: number;            // 学习次数（学生端）
  learning_duration: number;         // 学习时长（学生端）
  add_to_classroom_count: number;    // 添加到课堂次数（教师端）
}

// 课程详细统计响应
export interface CourseDetailStatisticsResponse {
  course_id: number;
  course_title: string;
  time_range_text: string;
  data: CourseDetailStatisticsItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
  };
}

// 导出请求参数
export interface ExportStatisticsParams {
  export_type: 'course' | 'practice' | 'training' | 'teacher' | 'student' | 'course_detail' | 'practice_detail' | 'training_detail';
  export_format?: 'xlsx' | 'csv';
  time_range?: TimeRange;
  start_date?: string;
  end_date?: string;
  user_group?: UserGroup;
  course_id?: number;  // 课程详情导出用
  practice_id?: number; // 实践详情导出用
  training_id?: number; // 实训详情导出用
  [key: string]: any; // 其他筛选条件
}

// 导出响应
export interface ExportStatisticsResponse {
  export_url: string;
  filename: string;
  export_time: string;
  record_count: number;
}

// API响应基础结构
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
  trace_id?: string;
}

// ===== API函数 =====

// 获取课程统计分析
export async function getCourseStatistics(params: CourseStatisticsParams = {}): Promise<ApiResponse<CourseStatisticsResponse>> {
  return request.get('/api/v1/usage-statistics/courses', { params });
}

// 获取实践统计分析
export async function getPracticeStatistics(params: PracticeStatisticsParams = {}): Promise<ApiResponse<PracticeStatisticsResponse>> {
  return request.get('/api/v1/usage-statistics/practices', { params });
}

// 获取实训统计分析
export async function getTrainingStatistics(params: TrainingStatisticsParams = {}): Promise<ApiResponse<TrainingStatisticsResponse>> {
  return request.get('/api/v1/usage-statistics/trainings', { params });
}

// 获取教师使用统计
export async function getTeacherUsageStatistics(params: TeacherUsageParams = {}): Promise<ApiResponse<TeacherUsageResponse>> {
  return request.get('/api/v1/usage-statistics/teachers', { params });
}

// 获取学生使用统计
export async function getStudentUsageStatistics(params: StudentUsageParams = {}): Promise<ApiResponse<StudentUsageResponse>> {
  return request.get('/api/v1/usage-statistics/students', { params });
}

// 获取课程详细统计（下钻页面）
export async function getCourseDetailStatistics(courseId: number, params: Omit<CourseDetailStatisticsParams, 'course_id'> = {}): Promise<ApiResponse<CourseDetailStatisticsResponse>> {
  return request.get(`/api/v1/usage-statistics/courses/${courseId}/details`, { params });
}

// 导出统计数据
export async function exportStatisticsData(params: ExportStatisticsParams): Promise<ApiResponse<ExportStatisticsResponse>> {
  return request.post('/api/v1/usage-statistics/export', params);
}

// 时间范围选项
export const timeRangeOptions = [
  { label: '今天', value: TimeRange.TODAY },
  { label: '昨天', value: TimeRange.YESTERDAY },
  { label: '最近7天', value: TimeRange.LAST_7_DAYS },
  { label: '最近30天', value: TimeRange.LAST_30_DAYS },
  { label: '自定义', value: TimeRange.CUSTOM },
];

// 用户组选项
export const userGroupOptions = [
  { label: '教师', value: UserGroup.TEACHER },
  { label: '学生', value: UserGroup.STUDENT },
];

// 格式化时间范围显示文本
export function formatTimeRangeText(timeRange: TimeRange, startDate?: string, endDate?: string): string {
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  
  const formatDate = (date: Date) => {
    return date.getFullYear() + '.' + 
           String(date.getMonth() + 1).padStart(2, '0') + '.' + 
           String(date.getDate()).padStart(2, '0');
  };
  
  switch (timeRange) {
    case TimeRange.TODAY:
      return formatDate(today);
    case TimeRange.YESTERDAY:
      return formatDate(yesterday);
    case TimeRange.LAST_7_DAYS:
      const week = new Date(today);
      week.setDate(week.getDate() - 6);
      return `${formatDate(week)}~${formatDate(today)}`;
    case TimeRange.LAST_30_DAYS:
      const month = new Date(today);
      month.setDate(month.getDate() - 29);
      return `${formatDate(month)}~${formatDate(today)}`;
    case TimeRange.CUSTOM:
      if (startDate && endDate) {
        return `${startDate.replace(/-/g, '.')}~${endDate.replace(/-/g, '.')}`;
      }
      return '';
    default:
      return '';
  }
}

// 格式化学习时长（秒转换为友好格式）
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}秒`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return remainingSeconds > 0 ? `${minutes}分${remainingSeconds}秒` : `${minutes}分钟`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return minutes > 0 ? `${hours}小时${minutes}分钟` : `${hours}小时`;
  }
}

// 格式化百分比
export function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
} 