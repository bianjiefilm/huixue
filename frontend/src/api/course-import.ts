import { request } from '@/utils/request';
import type { ApiResponse } from '@/utils/request';

// 扫描到的课程资源
export interface ScannedCourse {
  title: string;
  path: string;
  description?: string;
  difficulty?: string;
  direction?: string;
  category?: string;
  cover_url?: string;
  chapters?: number;
  tasks?: number;
}

// 扫描到的实训资源
export interface ScannedTraining {
  title: string;
  path: string;
  description?: string;
  difficulty?: string;
  datasets?: string[];
  workflow?: string[];
  jupyter?: string[];
}

// 扫描结果
export interface ScanResult {
  trainings: ScannedTraining[];
  courses: ScannedCourse[];
  total: number;
}

// 扫描响应
export interface ScanResponse {
  code: string;
  msg: string;
  data: {
    trainings: number;
    courses: number;
    total: number;
    resources: ScanResult;
  };
}

// 导入结果
export interface ImportResult {
  code: string;
  msg: string;
  data?: {
    title: string;
    action: 'created' | 'updated';
  };
}

/**
 * 扫描可导入的资源
 */
export async function scanResources(): Promise<ScanResponse> {
  return request.post('/api/v1/resource-import/scan/trainings');
}

/**
 * 导入单个课程资源
 */
export async function importCourse(params: {
  resource_path: string;
  force_update?: boolean;
}): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('resource_path', params.resource_path);
  if (params.force_update) {
    formData.append('force_update', 'true');
  }
  return request.post('/api/v1/resource-import/import/course', formData);
}

/**
 * 导入单个实训资源
 */
export async function importTraining(params: {
  resource_path: string;
  force_update?: boolean;
}): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('resource_path', params.resource_path);
  if (params.force_update) {
    formData.append('force_update', 'true');
  }
  return request.post('/api/v1/resource-import/import/training', formData);
}

/**
 * 批量导入课程资源
 */
export async function batchImportCourses(params: {
  resource_paths: string[];
  force_update?: boolean;
}): Promise<{
  success: number;
  failed: number;
  results: ImportResult[];
}> {
  const results: ImportResult[] = [];
  let success = 0;
  let failed = 0;

  for (const path of params.resource_paths) {
    try {
      const result = await importCourse({
        resource_path: path,
        force_update: params.force_update
      });
      results.push(result);
      if (result.code === '0000') {
        success++;
      } else {
        failed++;
      }
    } catch (error) {
      failed++;
      results.push({
        code: '2000',
        msg: `导入失败: ${error}`
      });
    }
  }

  return { success, failed, results };
}
