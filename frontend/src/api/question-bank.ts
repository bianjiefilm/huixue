import request from '@/utils/http';

// 类型定义
export type QuestionType = 'single' | 'multiple' | 'judge' | 'essay';
export type QuestionDifficulty = 'easy' | 'medium' | 'hard';
export type QuestionSource = 'system' | 'personal';

export interface QuestionSummary {
  id: string;
  type: QuestionType;
  content: string;
  category: string[];
  difficulty: QuestionDifficulty;
  source: QuestionSource;
  score: number;
}

export interface QuestionDetail extends QuestionSummary {
  options?: {
    content: string;
  }[];
  answer: number[] | boolean;
  referenceAnswer?: string;
  explanation?: string;
  creatorId?: string;
}

export interface QuestionInput {
  type: QuestionType;
  content: string;
  options?: string[];
  answer: number[] | boolean;
  referenceAnswer?: string;
  score: number;
  difficulty: QuestionDifficulty;
  category: string[];
  explanation?: string;
}

export interface PaperSummary {
  id: string;
  title: string;
  category: string;
  difficulty: QuestionDifficulty;
  source: QuestionSource;
  questionCount: number;
  totalScore: number;
  createdAt: string;
  updatedAt: string;
  creatorId?: string;
  createdBy?: string;
}

export interface PaperDetail extends PaperSummary {
  description?: string;
  duration: number;
  passingScore: number;
  questions: QuestionDetail[];
}

export interface TemplateRule {
  type: QuestionType;
  count: number;
  scorePerQuestion: number;
  difficulty?: QuestionDifficulty;
  category?: string[];
}

export interface QuestionTemplate {
  id: string;
  name: string;
  description: string;
  rules: TemplateRule[];
  isSystem: boolean;
}

// API 函数

/**
 * 获取题库列表
 */
export async function getQuestions(params: {
  keyword?: string;
  type?: QuestionType;
  difficulty?: QuestionDifficulty;
  category?: string;
  source?: QuestionSource;
  page?: number;
  pageSize?: number;
}): Promise<ApiResponse<{
  list: QuestionSummary[];
  total: number;
  page: number;
  pageSize: number;
}>> {
  return request.get('/api/exam/questions', { params });
}

/**
 * 创建试题
 */
export async function createQuestion(data: QuestionInput): Promise<ApiResponse<QuestionDetail>> {
  return request.post('/api/exam/questions', data);
}

/**
 * 获取试题详情
 */
export async function getQuestionDetail(id: string): Promise<ApiResponse<QuestionDetail>> {
  return request.get(`/api/exam/questions/${id}`);
}

/**
 * 更新试题
 */
export async function updateQuestion(id: string, data: QuestionInput): Promise<ApiResponse<QuestionDetail>> {
  return request.put(`/api/exam/questions/${id}`, data);
}

/**
 * 复制试题
 */
export async function copyQuestion(id: string): Promise<ApiResponse<QuestionDetail>> {
  return request.post(`/api/exam/questions/${id}/copy`);
}

/**
 * 删除试题
 */
export async function deleteQuestion(id: string): Promise<ApiResponse<{ message: string }>> {
  return request.delete(`/api/exam/questions/${id}`);
}

/**
 * 批量删除试题
 */
export async function batchDeleteQuestions(ids: string[]): Promise<ApiResponse<{ message: string }>> {
  return request.post('/api/exam/questions/batch-delete', { ids });
}

/**
 * 导入试题
 */
export async function importQuestions(file: File): Promise<ApiResponse<{
  successCount: number;
  failCount: number;
  errors?: string[];
}>> {
  const formData = new FormData();
  formData.append('file', file);
  return request.post('/api/exam/questions/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * 获取试卷列表
 */
export async function getPapers(params: {
  keyword?: string;
  category?: string;
  difficulty?: QuestionDifficulty;
  source?: QuestionSource;
  page?: number;
  pageSize?: number;
}): Promise<ApiResponse<{
  list: PaperSummary[];
  total: number;
  page: number;
  pageSize: number;
}>> {
  return request.get('/api/exam/papers', { params });
}

/**
 * 创建试卷
 */
export async function createPaper(data: {
  title: string;
  description?: string;
  category: string;
  difficulty: QuestionDifficulty;
  duration: number;
  passingScore: number;
  questions: Array<{
    questionId: string;
    score: number;
  }>;
}): Promise<ApiResponse<PaperDetail>> {
  return request.post('/api/exam/papers', data);
}

/**
 * 获取试卷详情
 */
export async function getPaperDetail(id: string): Promise<ApiResponse<PaperDetail>> {
  return request.get(`/api/exam/papers/${id}`);
}

/**
 * 更新试卷
 */
export async function updatePaper(id: string, data: {
  title?: string;
  description?: string;
  category?: string;
  difficulty?: QuestionDifficulty;
  duration?: number;
  passingScore?: number;
  questions?: Array<{
    questionId: string;
    score: number;
  }>;
}): Promise<ApiResponse<PaperDetail>> {
  return request.put(`/api/exam/papers/${id}`, data);
}

/**
 * 复制试卷
 */
export async function copyPaper(id: string): Promise<ApiResponse<PaperDetail>> {
  return request.post(`/api/exam/papers/${id}/copy`);
}

/**
 * 导出试卷
 */
export async function exportPaper(id: string): Promise<ApiResponse<{
  downloadUrl: string;
  filename: string;
}>> {
  return request.get(`/api/exam/papers/${id}/export`);
}

/**
 * 删除试卷
 */
export async function deletePaper(id: string): Promise<ApiResponse<{ message: string }>> {
  return request.delete(`/api/exam/papers/${id}`);
}

/**
 * 获取试卷模板
 */
export async function getPaperTemplates(): Promise<ApiResponse<QuestionTemplate[]>> {
  return request.get('/api/exam/paper-templates');
}

/**
 * 根据模板生成试卷
 */
export async function generatePaperFromTemplate(data: {
  templateId: string;
  title: string;
  category: string;
  duration: number;
  passingScore: number;
}): Promise<ApiResponse<PaperDetail>> {
  return request.post('/api/exam/papers/generate-from-template', data);
}

/**
 * 创建考试（从试卷）
 */
export async function createExamFromPaper(data: {
  paperId: string;
  examTitle: string;
  classroomId: string;
  startTime?: string;
  endTime?: string;
}): Promise<ApiResponse<{
  examId: string;
  message: string;
}>> {
  return request.post('/api/exam/papers/create-exam', data);
}