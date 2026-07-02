/**
 * 优秀作业相关API
 */
import request from '@/utils/http';

// API响应类型
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
}

// 优秀作业接口类型定义
export interface ExcellentWork {
  id: number;
  student_id: number;
  student_name: string;
  student_number: string;
  avatar_url: string | null;
  submission_time: string | null;
  score: number;
  final_score: number;
  teacher_feedback: string | null;
  graded_at: string | null;
  graded_by_teacher_name: string | null;
  view_count: number;
  like_count: number;
  is_liked: boolean;
  is_favorited: boolean;
  // 额外字段
  course_name?: string;
  course_type?: string;
  classroom_name?: string;
  design_files?: any[];
  experiment_reports?: any[];
}

export interface NavigationNode {
  id: number;
  name: string;
  type: 'classroom' | 'course';
  course_count?: number;
  excellent_count?: number;
  course_type?: string;
  semester?: string;
  children: NavigationNode[];
}

export interface LikeResponse {
  success: boolean;
  action: 'like' | 'unlike';
  current_count: number;
  is_active: boolean;
}

export interface FavoriteResponse {
  success: boolean;
  action: 'favorite' | 'unfavorite';
  current_count: number;
  is_active: boolean;
}

// 获取优秀作业导航树
export async function getNavigationTree(params: {
  user_id: number;
  user_role: string;
}): Promise<ApiResponse<{ tree: NavigationNode[] }>> {
  return request.get('/api/v1/excellent-works/navigation-tree', { params });
}

// 获取优秀作业列表
export async function getExcellentWorksList(params: {
  user_id: number;
  user_role: string;
  classroom_id?: number;
  course_id?: number;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<{
  list: ExcellentWork[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}> {
  const response = await request.get('/api/v1/excellent-works/list', { params });
  return response;
}

// 获取优秀作业详情
export async function getExcellentWorkDetail(workId: number, params: {
  user_id: number;
  user_role: string;
}): Promise<ApiResponse<ExcellentWork>> {
  return request.get(`/api/v1/excellent-works/${workId}/detail`, { params });
}

// 点赞/取消点赞
export async function toggleLike(workId: number, action: 'like' | 'unlike', userId: number): Promise<ApiResponse<LikeResponse>> {
  return request.post(`/api/v1/excellent-works/${workId}/like`, {
    action
  }, {
    params: { user_id: userId }
  });
}

// 收藏/取消收藏
export async function toggleFavorite(workId: number, action: 'favorite' | 'unfavorite', userId: number): Promise<ApiResponse<FavoriteResponse>> {
  return request.post(`/api/v1/excellent-works/${workId}/favorite`, {
    action
  }, {
    params: { user_id: userId }
  });
}

// 获取我收藏的作业
export async function getMyFavorites(params: {
  user_id: number;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: ExcellentWork[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get('/api/v1/excellent-works/my-favorites', { params });
}

// 获取统计信息
export async function getStatistics(params: {
  user_id: number;
  user_role: string;
}): Promise<ApiResponse<{
  total_works: number;
  total_views: number;
  total_likes: number;
  total_favorites: number;
  my_favorites_count: number;
}>> {
  return request.get('/api/v1/excellent-works/statistics', { params });
} 