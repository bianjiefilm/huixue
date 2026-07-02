import request from '@/utils/http';

// 考试相关的类型定义
export interface ExamInfo {
  id: number;
  classroom_id: number;
  exam_name?: string;  // 可选，因为API返回title
  title?: string;      // API实际返回的字段
  exam_type: 'online' | 'offline';
  test_paper_id: number;
  test_paper_name?: string;
  test_paper_title?: string;  // API实际返回的字段
  paper_total_score?: number;
  test_paper_total_score?: number;  // API实际返回的字段
  passing_score?: number;
  pass_mark?: number;  // API实际返回的字段
  start_time: string | null;
  end_time: string | null;
  exam_start_time?: string | null;  // API返回的实际字段名
  exam_end_time?: string | null;    // API返回的实际字段名
  time_limit_minutes?: number;
  duration_minutes?: number;  // API实际返回的字段
  is_published: boolean;
  is_deleted?: boolean;
  created_at: string;
  updated_at: string;
  status?: 'not_started' | 'in_progress' | 'ended' | 'COMPLETED';
  status_cn?: string;  // API返回的中文状态
  student_count?: number;
  total_students?: number;  // API实际返回的字段
  submitted_count?: number;
  graded_count?: number;
}

// 考试列表项目类型（用于我的考试页面）
export interface ExamItem {
  id: number;
  title: string;
  classroom_id: number;
  classroom_name: string;
  status: 'unpublished' | 'upcoming' | 'ongoing' | 'finished';
  participant_count: number;
  total_count: number;
  start_time: string | null;
  end_time: string | null;
  duration: number;
  created_at: string;
  can_edit: boolean;
  can_delete: boolean;
  can_publish: boolean;
}

export interface StudentPaper {
  student_id: number;
  student_name: string;
  student_number: string;
  attempt_id?: number;
  submission_status: 'not_started' | 'in_progress' | 'submitted';
  submission_time: string | null;
  obtained_score: number | null;
  total_score: number;
  grading_status: 'not_graded' | 'auto_graded' | 'partially_graded' | 'fully_graded';
  objective_score?: number;
  subjective_score?: number;
  graded_by?: string;
  graded_at?: string;
}

export interface ExamStatistics {
  total_students: number;
  submitted_count: number;
  graded_count: number;
  passed_count: number;
  average_score: number;
  highest_score: number;
  lowest_score: number;
  pass_rate: number;
  score_distribution: {
    range: string;
    count: number;
    percentage: number;
  }[];
}

export interface ExamPaperDetail {
  exam_id: number;
  student_id: number;
  student_name: string;
  questions: {
    question_id: number;
    question_type: string;
    question_content: string;
    question_score: number;
    student_answer: string | null;
    is_correct?: boolean;
    obtained_score: number;
    teacher_comment?: string;
  }[];
  total_score: number;
  obtained_score: number;
  submission_time: string;
}

export interface GradingRequest {
  question_scores: {
    question_id: number;
    score: number;
    comment?: string;
  }[];
  total_score?: number;
}

// 考试管理相关的类型定义
export interface TestPaper {
  id: number;
  paper_name: string;
  paper_description?: string;
  total_score: number;
  pass_score: number;
  question_count: number;
  difficulty_level?: string;
  created_at: string;
  updated_at: string;
}

export interface ExamCreateRequest {
  title: string;
  test_paper_id: number;
}

export interface ExamPublishRequest {
  exam_start_time: string;
  exam_end_time: string;
  duration_minutes: number;
  pass_mark: number;
  shuffle_questions?: boolean;
  shuffle_options?: boolean;
}

export interface ExamUpdateRequest {
  exam_start_time?: string;
  exam_end_time?: string;
  duration_minutes?: number;
  pass_mark?: number;
  shuffle_questions?: boolean;
  shuffle_options?: boolean;
}

export interface ExamRenameRequest {
  title: string;
}

// API 函数

/**
 * 获取可用的试卷列表（用于创建考试）
 */
export async function getTestPapers(params: {
  classroom_id: number;
  teacher_id: number;
  keyword?: string;
  difficulty?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: TestPaper[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/test-papers`, {
    params: queryParams
  });
}

/**
 * 创建考试
 */
export async function createExam(params: {
  classroom_id: number;
  teacher_id: number;
  data: ExamCreateRequest;
}): Promise<ApiResponse<{
  exam_id: number;
  title: string;
  status: string;
  test_paper_id: number;
}>> {
  const { classroom_id, teacher_id, data } = params;
  return request.post(`/api/v1/classrooms/${classroom_id}/exams`, data, {
    params: { teacher_id }
  });
}

/**
 * 发布考试（简化版本，用于我的考试页面）
 */
export async function publishExamSimple(
  examId: number,
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.patch(`/api/v1/exams/${examId}/publish`, {}, {
    params: { teacher_id: teacherId }
  });
}

/**
 * 发布考试（完整版本，用于课程考核页面）
 */
export async function publishExam(params: {
  exam_id: number;
  teacher_id: number;
  data: ExamPublishRequest;
}): Promise<ApiResponse<{ message: string }>> {
  const { exam_id, teacher_id, data } = params;
  return request.patch(`/api/v1/exams/${exam_id}/publish`, data, {
    params: { teacher_id }
  });
}

/**
 * 更新考试设置
 */
export async function updateExam(params: {
  exam_id: number;
  teacher_id: number;
  data: ExamUpdateRequest;
}): Promise<ApiResponse<ExamInfo>> {
  const { exam_id, teacher_id, data } = params;
  return request.patch(`/api/v1/exams/${exam_id}`, data, {
    params: { teacher_id }
  });
}

/**
 * 重命名考试
 */
export async function renameExam(params: {
  exam_id: number;
  teacher_id: number;
  data: ExamRenameRequest;
}): Promise<ApiResponse<{
  exam_id: number;
  title: string;
  message: string;
}>> {
  const { exam_id, teacher_id, data } = params;
  return request.patch(`/api/v1/exams/${exam_id}/rename`, data, {
    params: { teacher_id }
  });
}

/**
 * 删除考试
 */
export async function deleteExam(params: {
  exam_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{
  message: string;
}>> {
  const { exam_id, teacher_id } = params;
  return request.delete(`/api/v1/exams/${exam_id}`, {
    params: { teacher_id }
  });
}

/**
 * 获取课堂的考试列表
 */
export async function getClassroomExams(params: {
  classroom_id: number;
  teacher_id: number;
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: ExamInfo[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  const { classroom_id, ...queryParams } = params;
  return request.get(`/api/v1/classrooms/${classroom_id}/exams`, {
    params: queryParams
  });
}

/**
 * 获取教师所有考试列表
 */
export async function getExamList(params: {
  teacher_id: number;
  keyword?: string;
  status?: string;
  classroom_id?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: ExamItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  return request.get('/api/v1/exams', {
    params
  });
}

/**
 * 获取考试详情
 */
export async function getExamDetail(params: {
  exam_id: number;
  teacher_id: number;
}): Promise<ApiResponse<ExamInfo>> {
  const { exam_id, teacher_id } = params;
  return request.get(`/api/v1/exams/${exam_id}/detail`, {
    params: { teacher_id }
  });
}

/**
 * 获取考试的学生试卷列表
 */
export async function getExamPapers(params: {
  exam_id: number;
  teacher_id: number;
  status?: string;
  keyword?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: StudentPaper[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
}>> {
  const { exam_id, ...queryParams } = params;
  return request.get(`/api/v1/exams/${exam_id}/papers`, {
    params: queryParams
  });
}

/**
 * 获取学生试卷详情（用于批阅）
 */
export async function getStudentPaper(params: {
  exam_id: number;
  student_id: number;
  teacher_id: number;
}): Promise<ApiResponse<ExamPaperDetail>> {
  const { exam_id, student_id, teacher_id } = params;
  return request.get(`/api/v1/exams/${exam_id}/papers/${student_id}`, {
    params: { teacher_id }
  });
}

/**
 * 提交学生试卷批阅结果
 */
export async function submitGrading(params: {
  exam_id: number;
  student_id: number;
  teacher_id: number;
  data: GradingRequest;
}): Promise<ApiResponse<{
  success: boolean;
  total_score: number;
  message: string;
}>> {
  const { exam_id, student_id, teacher_id, data } = params;
  return request.post(
    `/api/v1/exams/${exam_id}/papers/${student_id}/marks`,
    data,
    { params: { teacher_id } }
  );
}

/**
 * 获取考试统计信息
 */
export async function getExamStatistics(params: {
  exam_id: number;
  teacher_id: number;
}): Promise<ApiResponse<ExamStatistics>> {
  const { exam_id, teacher_id } = params;
  return request.get(`/api/v1/exams/${exam_id}/statistics`, {
    params: { teacher_id }
  });
}

/**
 * 获取考试成绩列表
 */
export async function getExamScores(params: {
  exam_id: number;
  teacher_id: number;
  sort_by?: 'score' | 'submission_time' | 'student_name';
  order?: 'asc' | 'desc';
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: StudentPaper[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  statistics: ExamStatistics;
}>> {
  const { exam_id, ...queryParams } = params;
  return request.get(`/api/v1/exams/${exam_id}/scores`, {
    params: queryParams
  });
}

/**
 * 自动批阅客观题
 */
export async function autoGradeExam(params: {
  exam_id: number;
  teacher_id: number;
  student_ids?: number[];
}): Promise<ApiResponse<{
  success: boolean;
  graded_count: number;
  message: string;
}>> {
  const { exam_id, teacher_id, student_ids } = params;
  return request.post(
    `/api/v1/exams/${exam_id}/auto-grade`,
    { student_ids },
    { params: { teacher_id } }
  );
}

/**
 * 批量自动批阅所有客观题
 */
export async function batchAutoGrade(params: {
  exam_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{
  success: boolean;
  graded_count: number;
  message: string;
}>> {
  const { exam_id, teacher_id } = params;
  return request.post(
    `/api/v1/exams/${exam_id}/batch-auto-grade`,
    {},
    { params: { teacher_id } }
  );
}

/**
 * 导出考试成绩
 */
export async function exportExamScores(params: {
  exam_id: number;
  teacher_id: number;
  sort_field?: string;
  sort_order?: string;
  keyword?: string;
  status_filter?: string;
  export_format?: string;
}): Promise<Blob> {
  const { exam_id, ...queryParams } = params;
  return request.get(`/api/v1/exams/${exam_id}/scores/export`, {
    params: {
      export_format: 'xlsx',
      ...queryParams
    },
    responseType: 'blob'
  });
}

/**
 * 更新考试分数段设置
 */
export async function updateExamScoreRanges(params: {
  exam_id: number;
  teacher_id: number;
  ranges: ScoreSegment[];
  enable_custom_labels: boolean;
}): Promise<ApiResponse<{ success: boolean }>> {
  const { exam_id, teacher_id, ranges, enable_custom_labels } = params;
  
  // 转换数据格式以匹配后端API
  const formattedRanges = ranges.map(range => ({
    min_score: range.min,
    max_score: range.max,
    label: range.name
  }));
  
  return request.patch(`/api/v1/exams/${exam_id}/distribution`, {
    ranges: formattedRanges,
    enable_custom_labels
  }, {
    params: { teacher_id }
  });
}

// 辅助函数

/**
 * 获取考试状态文本
 */
export function getExamStatusText(exam: ExamInfo): string {
  // 如果API直接返回了status_cn，使用它
  if (exam.status_cn) return exam.status_cn;

  const now = new Date();
  const startTime = exam.exam_start_time ? new Date(exam.exam_start_time) : null;
  const endTime = exam.exam_end_time ? new Date(exam.exam_end_time) : null;

  if (!exam.is_published) return '未发布';
  if (!startTime) return '未开始';
  if (startTime > now) return '未开始';
  if (endTime && endTime < now) return '已结束';
  return '进行中';
}

/**
 * 获取考试状态颜色
 */
export function getExamStatusColor(exam: ExamInfo): string {
  const status = getExamStatusText(exam);
  const colorMap: Record<string, string> = {
    '未发布': 'default',
    '未开始': 'orange',
    '进行中': 'green',
    '已结束': 'default'
  };
  return colorMap[status] || 'default';
}

/**
 * 获取批阅状态文本
 */
export function getGradingStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'not_graded': '未批阅',
    'auto_graded': '已自动批阅',
    'partially_graded': '部分批阅',
    'fully_graded': '已批阅'
  };
  return statusMap[status] || status;
}

/**
 * 获取批阅状态颜色
 */
export function getGradingStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    'not_graded': 'default',
    'auto_graded': 'blue',
    'partially_graded': 'orange',
    'fully_graded': 'green'
  };
  return colorMap[status] || 'default';
}

/**
 * 判断学生是否通过考试
 */
export function isStudentPassed(paper: StudentPaper, passingScore: number): boolean {
  return (paper.obtained_score || 0) >= passingScore;
}

// 成绩分布和试题分析相关类型
export interface ScoreSegment {
  min: number;
  max: number;
  name: string;
  count?: number;
  percentage?: number;
}

export interface ScoreDistribution {
  segments: ScoreSegment[];
  total_count: number;
}

export interface QuestionAnalysis {
  question_id: number;
  question_type: string;
  question_content: string;
  question_score: number;
  total_students: number;
  answered_students: number;
  correct_count: number;
  correct_rate: number;
  average_score: number;
  options?: {
    option_id: string;
    option_content: string;
    is_correct: boolean;
    selected_count: number;
    selected_rate: number;
  }[];
}

/**
 * 获取考试成绩分布
 */
export async function getExamScoreDistribution(params: {
  exam_id: number;
  teacher_id: number;
  segments?: ScoreSegment[];
}): Promise<ApiResponse<ScoreDistribution>> {
  const { exam_id, teacher_id } = params;
  return request.get(`/api/v1/exams/${exam_id}/distribution`, {
    params: { teacher_id }
  });
}

/**
 * 获取考试试题分析
 */
export async function getExamQuestionAnalysis(params: {
  exam_id: number;
  teacher_id: number;
}): Promise<ApiResponse<{
  questions: QuestionAnalysis[];
  total_questions: number;
}>> {
  const { exam_id, teacher_id } = params;
  return request.get(`/api/v1/exams/${exam_id}/questions/stats`, {
    params: { teacher_id }
      });
  }

// API响应类型
export interface ApiResponse<T = any> {
  code: string;
  message: string;
  data: T;
}

// ==================== 试卷库相关接口 ====================

// 试卷列表项
export interface PaperItem {
  id: number;
  title: string;
  direction?: string;
  difficulty?: string;
  difficulty_cn?: string;
  source: string;
  question_count: number;
  total_score: number;
  created_at: string;
  creator_name?: string;
  can_create_exam: boolean;
  can_copy: boolean;
  can_export: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

// 试卷详情
export interface PaperDetail extends PaperItem {
  description?: string;
  questions: PaperQuestion[];
  composition_method?: string;
}

// 试卷中的题目
export interface PaperQuestion {
  id: number;
  question_id: number;
  content: string;
  question_type: string;
  question_type_cn: string;
  options?: any[];
  correct_answers?: any;
  explanation?: string;
  difficulty: string;
  difficulty_cn: string;
  score_for_question: number;
  order_in_paper: number;
}

// 创建试卷请求
export interface CreatePaperRequest {
  title: string;
  description?: string;
  direction: string;
  difficulty: string;
  composition_method: 'MANUAL_SELECTION' | 'TEMPLATE_BASED';
}

// 从试卷创建考试请求
export interface CreateExamFromPaperRequest {
  exam_title: string;
  classroom_id: number;
}

// 获取试卷库列表
export async function getPaperList(params: {
  teacher_id: number;
  keyword?: string;
  direction?: string;
  difficulty?: string;
  source?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: PaperItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  filter_tags: any;
}>> {
  return request.get('/api/v1/paper-library/papers', { params });
}

// 获取试卷详情
export async function getPaperDetail(paperId: number, teacherId: number): Promise<ApiResponse<PaperDetail>> {
  return request.get(`/api/v1/paper-library/${paperId}`, {
    params: { teacher_id: teacherId }
  });
}

// 创建试卷
export async function createPaper(data: CreatePaperRequest, teacherId: number): Promise<ApiResponse<{ paper_id: number }>> {
  return request.post('/api/v1/paper-library/create', data, {
    params: { teacher_id: teacherId }
  });
}

// 复制试卷
export async function copyPaper(paperId: number, teacherId: number): Promise<ApiResponse<{ new_paper_id: number }>> {
  return request.post(`/api/v1/paper-library/${paperId}/copy`, {}, {
    params: { teacher_id: teacherId }
  });
}

// 删除试卷
export async function deletePaper(paperId: number, teacherId: number): Promise<ApiResponse<any>> {
  return request.delete(`/api/v1/paper-library/${paperId}?teacher_id=${teacherId}`);
}

// 导出试卷
export async function exportPaper(paperId: number, teacherId: number): Promise<Blob> {
  return request.get(`/api/v1/paper-library/${paperId}/export`, {
    params: { teacher_id: teacherId },
    responseType: 'blob'
  });
}

// 从试卷创建考试
export async function createExamFromPaper(
  paperId: number,
  data: CreateExamFromPaperRequest,
  teacherId: number
): Promise<ApiResponse<{ exam_id: number; exam_title: string }>> {
  return request.post(`/api/v1/paper-library/${paperId}/create-exam`, data, {
    params: { teacher_id: teacherId }
  });
}

// ==================== 试题库相关接口 ====================

// 题目类型枚举
export type QuestionType = 'SINGLE_CHOICE' | 'MULTIPLE_CHOICE' | 'TRUE_FALSE' | 'SHORT_ANSWER';

// 试题列表项
export interface QuestionItem {
  id: string | number;
  content: string;
  question_type: QuestionType;
  question_type_cn: string;
  difficulty: string;
  difficulty_cn: string;
  direction?: string;
  category?: string;
  source: string;
  creator_name?: string;
  created_at: string;
  updated_at?: string;
  can_copy: boolean;
  can_edit: boolean;
  can_delete: boolean;
}

// 试题详情
export interface QuestionDetail extends QuestionItem {
  options?: Array<{
    key: string;
    content: string;
  }>;
  correct_answers?: string[];
  explanation?: string;
}

// 创建试题请求
export interface CreateQuestionRequest {
  content: string;
  question_type: QuestionType;
  options?: Array<{
    key: string;
    content: string;
  }>;
  correct_answers: string[];
  explanation?: string;
  difficulty: string;
  direction?: string;
  category?: string;
}

// 获取试题库列表
export async function getQuestionList(params: {
  teacher_id: number;
  keyword?: string;
  question_type?: string;
  direction?: string;
  category?: string;
  difficulty?: string;
  source?: string;
  page?: number;
  page_size?: number;
}): Promise<ApiResponse<{
  list: QuestionItem[];
  meta: {
    total: number;
    page: number;
    page_size: number;
  };
  filter_tags: any;
}>> {
  return request.get('/api/v1/question-library/questions', { params });
}

// 获取试题详情
export async function getQuestionDetail(questionId: string | number, teacherId: number): Promise<ApiResponse<QuestionDetail>> {
  return request.get(`/api/v1/question-library/questions/${questionId}`, {
    params: { teacher_id: teacherId }
  });
}

// 创建试题
export async function createQuestion(data: CreateQuestionRequest, teacherId: number): Promise<ApiResponse<{ question_id: string }>> {
  return request.post('/api/v1/question-library/questions', data, {
    params: { teacher_id: teacherId }
  });
}

// 更新试题
export async function updateQuestion(
  questionId: string | number,
  data: Partial<CreateQuestionRequest>,
  teacherId: number
): Promise<ApiResponse<any>> {
  return request.put(`/api/v1/question-library/questions/${questionId}?teacher_id=${teacherId}`, data);
}

// 复制试题
export async function copyQuestion(questionId: string | number, teacherId: number): Promise<ApiResponse<{ new_question_id: string }>> {
  return request.post(`/api/v1/question-library/questions/${questionId}/copy?teacher_id=${teacherId}`, {});
}

// 删除试题
export async function deleteQuestion(questionId: string | number, teacherId: number): Promise<ApiResponse<any>> {
  return request.delete(`/api/v1/question-library/questions/${questionId}?teacher_id=${teacherId}`);
}

/**
 * 批量删除试题
 */
export async function deleteQuestions(questionIds: number[], teacherId: number): Promise<ApiResponse<any>> {
  return request.post('/api/v1/question-library/questions/batch-delete', {
    question_ids: questionIds,
    teacher_id: teacherId
  });
}

// 导入试题
export async function importQuestions(file: File, teacherId: number): Promise<ApiResponse<{
  success_count: number;
  error_count: number;
  total_count: number;
  error_details: any[];
}>> {
  const formData = new FormData();
  formData.append('file', file);
  
  return request.post('/api/v1/question-library/questions/import', formData, {
    params: { teacher_id: teacherId }
  });
}

// 下载试题导入模板
export async function downloadQuestionTemplate(): Promise<Blob> {
  return request.get('/api/v1/question-library/questions/template', {
    responseType: 'blob'
  });
}

// ==================== 试卷编辑相关接口 ====================

// 向试卷添加题目
export async function addQuestionsToPaper(
  paperId: number,
  questionIds: number[],
  scores?: number[],
  teacherId?: number
): Promise<ApiResponse<{ added_count: number }>> {
  return request.post(`/api/v1/paper-library/${paperId}/questions?teacher_id=${teacherId}`, {
    question_ids: questionIds,
    scores: scores
  });
}

// 从试卷中移除试题
export async function removeQuestionsFromPaper(
  paperId: number,
  questionIds: number[],
  teacherId: number
): Promise<ApiResponse<{ removed_count: number }>> {
  return request.post(`/api/v1/paper-library/${paperId}/questions/remove`, {
    question_ids: questionIds,
    teacher_id: teacherId
  });
}

// 更新试卷中的题目信息
export async function updatePaperQuestion(
  paperId: number,
  questionId: number,
  updateData: { score?: number; order_index?: number },
  teacherId: number
): Promise<ApiResponse<any>> {
  return request.put(`/api/v1/paper-library/${paperId}/questions/${questionId}?teacher_id=${teacherId}`, updateData);
}

// ==================== 试卷分值和排序相关接口 ====================

// 更新试题分值
export async function updateQuestionScore(
  paperId: number,
  questionId: number,
  score: number,
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.patch(`/api/v1/paper-library/${paperId}/questions/${questionId}/score?teacher_id=${teacherId}`, {
    score: score
  });
}

// 批量更新题型分值
export async function batchUpdateQuestionsScore(
  paperId: number,
  questionType: string,
  scorePerQuestion: number,
  teacherId: number
): Promise<ApiResponse<{ updated_count: number }>> {
  return request.patch(`/api/v1/paper-library/${paperId}/questions/batch-score?teacher_id=${teacherId}`, {
    question_type: questionType,
    score_per_question: scorePerQuestion
  });
}

// 更新题目排序
export async function updateQuestionsOrder(
  paperId: number,
  questionOrders: Array<{ question_id: number; order_index: number }>,
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.patch(`/api/v1/paper-library/${paperId}/questions/order?teacher_id=${teacherId}`, {
    question_orders: questionOrders
  });
}

// 更新大题排序
export async function updateSectionsOrder(
  paperId: number,
  sectionOrders: Array<{ question_type: string; order_index: number }>,
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.patch(`/api/v1/paper-library/${paperId}/sections/order?teacher_id=${teacherId}`, {
    section_orders: sectionOrders
  });
}

// 更新试卷基本信息
export async function updatePaperBasicInfo(
  paperId: number,
  basicInfo: {
    title: string;
    direction: string;
    difficulty: string;
    description: string;
  },
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.put(`/api/v1/paper-library/${paperId}/basic-info?teacher_id=${teacherId}`, basicInfo);
}

// 完成试卷编辑
export async function completePaperEditing(
  paperId: number,
  teacherId: number
): Promise<ApiResponse<{ message: string }>> {
  return request.post(`/api/v1/paper-library/${paperId}/complete?teacher_id=${teacherId}`, {});
}

// ==================== 试卷管理相关接口 ====================

// ==================== 试卷详情和信息接口 ====================

// 获取增强的试卷详情
export async function getPaperEnhancedDetail(
  paperId: number,
  teacherId: number
): Promise<ApiResponse<any>> {
  return request.get(`/api/v1/paper-library/${paperId}/enhanced-detail`, {
    params: { teacher_id: teacherId }
  });
}

// 获取试卷统计信息
export async function getPaperStatistics(
  paperId: number,
  teacherId: number
): Promise<ApiResponse<any>> {
  return request.get(`/api/v1/paper-library/${paperId}/statistics`, {
    params: { teacher_id: teacherId }
  });
}

// ==================== 试卷导出和完成接口 ====================

// 增强的试卷导出
export async function exportPaperEnhanced(
  paperId: number,
  teacherId: number,
  format: string = 'word',
  includeAnswers: boolean = false
): Promise<ApiResponse<any>> {
  return request.post(`/api/v1/paper-library/${paperId}/export-enhanced`, {
    format: format,
    include_answers: includeAnswers
  }, {
    params: { teacher_id: teacherId }
  });
}

// ==================== 试卷管理接口 ====================

// 检查试卷编辑权限
export async function checkPaperEditPermission(
  paperId: number,
  teacherId: number
): Promise<ApiResponse<{
  can_edit: boolean;
  edit_mode: string;
  paper_source: string;
  is_owner: boolean;
}>> {
  return request.get(`/api/v1/paper-library/${paperId}/edit-permission`, {
    params: { teacher_id: teacherId }
  });
}