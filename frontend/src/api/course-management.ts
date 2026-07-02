import request from '@/utils/http'

// ==================== 枚举类型 ====================

export enum CourseTypeEnum {
  PRACTICE = 'PRACTICE',
  TRAINING = 'TRAINING'
}

export enum RequestTypeEnum {
  PUBLISH = 'PUBLISH',
  UNPUBLISH = 'UNPUBLISH'
}

export enum RequestStatusEnum {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  CANCELLED = 'CANCELLED'
}

export enum SortOrderEnum {
  ASC = 'asc',
  DESC = 'desc'
}

// ==================== 类型定义 ====================

export interface CategoryNode {
  key: string
  title: string
  children?: CategoryNode[]
}

export interface CategoryTreeResponse {
  categories: CategoryNode[]
}

// 实践课程类型
export interface PracticeCourseBase {
  id: number
  title: string
  description?: string
  cover_url?: string
  direction?: string
  category?: string
  difficulty?: string
  task_count: number
  coin: number
  created_at: string
  updated_at: string
}

export interface PracticeCourseCreator {
  id: number
  full_name?: string
  username: string
}

export interface PracticeCourseItem extends PracticeCourseBase {
  creator?: PracticeCourseCreator
  publish_status: string
  visibility: string
  can_unpublish: boolean
  can_publish: boolean
}

export interface PracticeCourseDetail extends PracticeCourseBase {
  intro?: string
  summary?: string
  practice_type?: string
  environment_id?: string
  storage_limit?: string
  memory_limit?: string
  cpu_limit?: string
  creator?: PracticeCourseCreator
  can_unpublish: boolean
}

export interface PracticeCourseListResponse {
  items: PracticeCourseItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface PracticeCourseQuery {
  category?: string
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: SortOrderEnum
}

// 实训课程类型
export interface TrainingCourseBase {
  id: number
  title: string
  intro?: string
  industry?: string
  difficulty?: string
  course_hours: number
  training_type?: string
  created_at: string
  updated_at: string
}

export interface TrainingCourseCreator {
  id: number
  full_name?: string
  username: string
}

export interface TrainingCourseItem extends TrainingCourseBase {
  creator?: TrainingCourseCreator
  publish_status: string
  visibility: string
  can_unpublish: boolean
  can_publish: boolean
}

export interface TrainingCourseDetail extends TrainingCourseBase {
  handbook_content?: string
  assignment_nodes?: string
  require_design_files: boolean
  require_experiment_report: boolean
  environment_id?: string
  storage_limit?: string
  memory_limit?: string
  cpu_limit?: string
  creator?: TrainingCourseCreator
  can_unpublish: boolean
}

export interface TrainingCourseListResponse {
  items: TrainingCourseItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface TrainingCourseQuery {
  category?: string
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: SortOrderEnum
}

// 课程操作
export interface CourseActionRequest {
  course_id: number
  action: 'unpublish' | 'publish'
  reason?: string
}

export interface CourseActionResponse {
  success: boolean
  message: string
}

// 课程审批
export interface CourseRequestCourse {
  id: number
  title: string
}

export interface CourseRequestUser {
  id: number
  full_name?: string
  username: string
}

export interface CourseRequestBase {
  id: number
  course_id: number
  course_type: CourseTypeEnum
  request_type: RequestTypeEnum
  status: RequestStatusEnum
  application_reason?: string
  applied_at: string
  review_comments?: string
  reviewed_at?: string
}

export interface CourseRequestItem extends CourseRequestBase {
  course: CourseRequestCourse
  applicant: CourseRequestUser
  reviewer?: CourseRequestUser
  course_type_text: string
  request_type_text: string
  status_text: string
  can_approve: boolean
  can_reject: boolean
  can_view_detail: boolean
}

export interface CourseRequestDetail extends CourseRequestBase {
  course: CourseRequestCourse
  applicant: CourseRequestUser
  reviewer?: CourseRequestUser
  course_type_text: string
  request_type_text: string
  status_text: string
  cancelled_reason?: string
  cancelled_at?: string
  can_approve: boolean
  can_reject: boolean
}

export interface CourseRequestListResponse {
  items: CourseRequestItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface CourseRequestQuery {
  status?: RequestStatusEnum
  course_type?: CourseTypeEnum
  request_type?: RequestTypeEnum
  course_name?: string
  applicant_name?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
  sort_field?: string
  sort_order?: SortOrderEnum
}

export interface CourseRequestApprovalRequest {
  action: 'approve' | 'reject'
  review_comments?: string
}

export interface CourseRequestSubmitRequest {
  course_id: number
  course_type: CourseTypeEnum
  request_type: RequestTypeEnum
  application_reason?: string
}

export interface CourseRequestCancelRequest {
  cancel_reason?: string
}

// ==================== API方法 ====================

export class CourseManagementAPI {
  // 实践课程管理
  static async getPracticeCourseCategories(): Promise<CategoryTreeResponse> {
    return request.get('/api/v1/course-management/practice-courses/categories')
  }

  static async getPracticeCourses(params: PracticeCourseQuery): Promise<PracticeCourseListResponse> {
    return request.get('/api/v1/course-management/practice-courses', { params })
  }

  static async getPracticeCourseDetail(courseId: number): Promise<PracticeCourseDetail> {
    return request.get(`/api/v1/course-management/practice-courses/${courseId}`)
  }

  static async practiceCourseAction(data: CourseActionRequest): Promise<CourseActionResponse> {
    return request.post('/api/v1/course-management/practice-courses/action', data)
  }

  // 实训课程管理
  static async getTrainingCourseCategories(): Promise<CategoryTreeResponse> {
    return request.get('/api/v1/course-management/training-courses/categories')
  }

  static async getTrainingCourses(params: TrainingCourseQuery): Promise<TrainingCourseListResponse> {
    return request.get('/api/v1/course-management/training-courses', { params })
  }

  static async getTrainingCourseDetail(courseId: number): Promise<TrainingCourseDetail> {
    return request.get(`/api/v1/course-management/training-courses/${courseId}`)
  }

  static async trainingCourseAction(data: CourseActionRequest): Promise<CourseActionResponse> {
    return request.post('/api/v1/course-management/training-courses/action', data)
  }

  // 课程审批
  static async getCourseRequests(params: CourseRequestQuery): Promise<CourseRequestListResponse> {
    return request.get('/api/v1/course-management/course-requests', { params })
  }

  static async getCourseRequestDetail(requestId: number): Promise<CourseRequestDetail> {
    return request.get(`/api/v1/course-management/course-requests/${requestId}`)
  }

  static async approveCourseRequest(
    requestId: number, 
    data: CourseRequestApprovalRequest
  ): Promise<CourseActionResponse> {
    return request.post(`/api/v1/course-management/course-requests/${requestId}/approve`, data)
  }

  static async submitCourseRequest(data: CourseRequestSubmitRequest): Promise<CourseActionResponse> {
    return request.post('/api/v1/course-management/course-requests', data)
  }

  static async cancelCourseRequest(
    requestId: number, 
    data: CourseRequestCancelRequest
  ): Promise<CourseActionResponse> {
    return request.post(`/api/v1/course-management/course-requests/${requestId}/cancel`, data)
  }

  // 工具方法
  static getStatusText(status: RequestStatusEnum): string {
    const statusMap = {
      [RequestStatusEnum.PENDING]: '待审批',
      [RequestStatusEnum.APPROVED]: '已同意',
      [RequestStatusEnum.REJECTED]: '已驳回',
      [RequestStatusEnum.CANCELLED]: '已撤销'
    }
    return statusMap[status] || '未知'
  }

  static getRequestTypeText(type: RequestTypeEnum): string {
    const typeMap = {
      [RequestTypeEnum.PUBLISH]: '申请公开发布',
      [RequestTypeEnum.UNPUBLISH]: '申请撤销公开'
    }
    return typeMap[type] || '未知'
  }

  static getCourseTypeText(type: CourseTypeEnum): string {
    const typeMap = {
      [CourseTypeEnum.PRACTICE]: '实践课程',
      [CourseTypeEnum.TRAINING]: '实训课程'
    }
    return typeMap[type] || '未知'
  }

  static getDifficultyText(difficulty?: string): string {
    const difficultyMap: Record<string, string> = {
      'BEGINNER': '初级',
      'INTERMEDIATE': '中级',
      'ADVANCED': '高级'
    }
    return difficulty ? difficultyMap[difficulty] || difficulty : '-'
  }

  static getStatusColor(status: RequestStatusEnum): string {
    const colorMap = {
      [RequestStatusEnum.PENDING]: 'orange',
      [RequestStatusEnum.APPROVED]: 'green',
      [RequestStatusEnum.REJECTED]: 'red',
      [RequestStatusEnum.CANCELLED]: 'gray'
    }
    return colorMap[status] || 'default'
  }
} 