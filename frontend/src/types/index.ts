/**
 * 导出所有类型定义
 */

export * from './classroom';
export * from './course';
export * from './user';

// 通用响应类型
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
  status?: string;
}

// 分页参数
export interface PaginationParams {
  page?: number;
  page_size?: number;
  total?: number;
}

// 分页响应
export interface PaginatedResponse<T> {
  list: T[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}