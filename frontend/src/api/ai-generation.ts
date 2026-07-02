import { request } from '@/utils/request'

export interface TextExtractResponse {
  filename: string
  text_content: string
  markdown_content: string
  content_length: number
}

export interface OutlineItem {
  title: string
  knowledge_points: string[]
  suggested_type: string
  difficulty: string
  estimated_time: number
}

export interface OutlineSuggestionResponse {
  outline: OutlineItem[]
  total_levels: number
  course_type: string
}

export interface CodeSnippetResponse {
  code: string
  target_type: string
  language: string
}

export interface PracticeOutlineItem {
  level_title: string
  core_knowledge: string
  practice_description: string
  suggested_type: string
  difficulty: string
  estimated_time: number
}

export interface PracticeOutlineResponse {
  filename: string
  outline: PracticeOutlineItem[]
  original_text: string
}

export interface PracticeLevelContent {
  task_handbook?: string
  student_template?: string
  judge_script?: string
  test_cases?: any[]
  reference_answer?: string
  questions?: any[]
}

export interface PracticeLevelResponse {
  level_title: string
  level_type: string
  content: PracticeLevelContent
}

// API 1: 文本提取
export function extractTextFromFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request<TextExtractResponse>({
    url: '/api/v1/generation/extract-text',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// API 2: 知识点大纲建议
export function suggestOutline(textContent: string, courseType: string = 'practice') {
  return request<OutlineSuggestionResponse>({
    url: '/api/v1/generation/suggest-outline',
    method: 'post',
    data: {
      text_content: textContent,
      course_type: courseType
    }
  })
}

// API 3: 代码片段生成
export function suggestCodeSnippet(
  instruction: string,
  targetType: string = 'student_template',
  context: string = '',
  language: string = 'python'
) {
  return request<CodeSnippetResponse>({
    url: '/api/v1/generation/suggest-code-snippet',
    method: 'post',
    data: {
      instruction,
      target_type: targetType,
      context,
      language
    }
  })
}

// 接口 1: 从文件生成实践大纲
export function generatePracticeOutlineFromFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  
  return request<PracticeOutlineResponse>({
    url: '/api/v1/generation/practice-outline-from-file',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 接口 2: 生成实践关卡内容
export function generatePracticeLevelContent(
  levelInfo: PracticeOutlineItem,
  originalText: string = ''
) {
  return request<PracticeLevelResponse>({
    url: '/api/v1/generation/practice-level-content',
    method: 'post',
    data: {
      level_info: levelInfo,
      original_text: originalText
    }
  })
}

// ==================== 试题生成相关API ====================

export interface Question {
  question_type: string
  question_stem: string
  options?: string[]
  correct_answer: string | string[] | boolean
  difficulty: string
  analysis: string
  subject?: string
  chapter?: string
}

export interface QuestionsGenerateResponse {
  filename: string
  questions: Question[]
  statistics: {
    single_choice: number
    multiple_choice: number
    true_false: number
    total: number
  }
}

export interface ExcelFormatData {
  序号: number
  题目类型: string
  题干: string
  科目: string
  章节: string
  难度: string
  答案解析: string
  正确答案: string
  [key: string]: any // 选项A-F
}

// 从文件生成试题
export function generateQuestionsFromFile(
  file: File,
  numSingleChoice: number = 10,
  numMultipleChoice: number = 5,
  numTrueFalse: number = 5
) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('num_single_choice', numSingleChoice.toString())
  formData.append('num_multiple_choice', numMultipleChoice.toString())
  formData.append('num_true_false', numTrueFalse.toString())
  
  return request<QuestionsGenerateResponse>({
    url: '/api/v1/generation/questions-from-file',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// 格式化试题为Excel格式
export function formatQuestionsForExcel(
  questions: Question[],
  subject: string = '通用',
  chapter: string = ''
) {
  return request<{ excel_format: ExcelFormatData[], total: number }>({
    url: '/api/v1/generation/format-questions-for-excel',
    method: 'post',
    data: {
      questions,
      subject,
      chapter
    }
  })
}

// 批量导入试题
export function batchImportQuestions(
  questions: Question[],
  categoryId?: number
) {
  return request<{
    imported: number
    failed: number
    errors: Array<{ question: string, error: string }>
  }>({
    url: '/api/v1/generation/batch-import-questions',
    method: 'post',
    data: {
      questions,
      category_id: categoryId
    }
  })
}

// ==================== 自动化课程生成流水线 API ====================

export interface CourseProject {
  project_name: string
  path: string
  file_count: number
  largest_file: string
  largest_file_size_mb: number
  status: '待处理' | '部分完成' | '已完成'
  missing_components: string[]
  has_practice: boolean
  has_stages: boolean
  has_questions: boolean
  practice_id?: number
}

export interface ResourceFile {
  filename: string
  full_path: string  // 包含子目录的完整相对路径
  project: string    // 所属项目/文件夹名称
  path: string       // 完整路径
  size: number
  size_mb: number
  modified_time: string
  extension: string
  is_processed: boolean
}

export interface CourseGenerationTask {
  task_id: string
  file_name: string
  status: 'pending' | 'processing' | 'success' | 'error'
  progress?: number
  message?: string
  result?: {
    practice_id: number
    stages_count: number
    questions_count: number
  }
  error?: string
}

// 获取课程项目列表
export function getCourseProjects() {
  return request({
    url: '/api/v1/generation/course-projects',
    method: 'get'
  })
}

// 获取课程资源文件列表（已废弃，保留兼容性）
export function getCourseResourceFiles() {
  return request({
    url: '/api/v1/generation/course-resource-files',
    method: 'get'
  })
}

// 智能补充课程项目
export function supplementCourseProject(projectName: string, categoryId?: number) {
  return request({
    url: '/api/v1/generation/supplement-course-project',
    method: 'post',
    data: {
      project_name: projectName,
      category_id: categoryId
    }
  })
}

// 创建完整课程生成任务（已废弃，保留兼容性）
export function createFullCourseFromFile(filePath: string, categoryId?: number) {
  return request({
    url: '/api/v1/generation/create-full-course-from-file',
    method: 'post',
    data: {
      file_path: filePath,
      category_id: categoryId
    }
  })
}

// 查询任务状态
export function getTaskStatus(taskId: string) {
  return request({
    url: `/api/v1/generation/tasks/${taskId}/status`,
    method: 'get'
  })
}

// ==================== 课程包生成 API (兼容旧组件) ====================

export interface CourseManifest {
  title: string
  description?: string
  category?: string
}

export interface FileManifestItem {
  name: string
  fileType: string
  uid: string
}

export interface TaskStatus {
  status:
    | 'pending'
    | 'processing'
    | 'success'
    | 'error'
    | 'PENDING'
    | 'PROCESSING'
    | 'SUCCESS'
    | 'ERROR'
  progress: number
  message?: string
  // 兼容不同实现的字段
  result?: any
  error_message?: string
}

// 创建课程包任务（存根函数）
export function createCoursePackageTask(manifest: CourseManifest, files: FileManifestItem[]) {
  console.warn('createCoursePackageTask is a stub function')
  return Promise.resolve({
    task_id: 'stub-task-id',
    status: 'pending'
  })
}

// 获取课程包任务状态（存根函数）
export function getCoursePackageTaskStatus(taskId: string) {
  console.warn('getCoursePackageTaskStatus is a stub function')
  return Promise.resolve({
    status: 'PROCESSING',
    progress: 0,
    message: 'Stub task status'
  })
}

// ==================== 实训资源增强 API ====================

export interface TrainingProject {
  project_name: string
  path: string
  file_count: number
  largest_file: string
  largest_file_size_mb: number
  status: '待处理' | '部分完成' | '已完成'
  missing_components: string[]
  has_training: boolean
  has_datasets: boolean
  has_notebooks: boolean
  training_id?: number
}

// 获取实训项目列表
export function getTrainingProjects() {
  return request({
    url: '/api/v1/generation/training-projects',
    method: 'get'
  })
}

// 智能增强实训项目
export function supplementTrainingProject(projectName: string) {
  return request({
    url: '/api/v1/generation/supplement-training-project',
    method: 'post',
    data: {
      project_name: projectName
    }
  })
}

// ==================== 实训包生成 API (供 TrainingGeneration 使用) ====================

export interface TrainingManifest {
  training_title: string
  analysis_goals: string[]
  training_type: string
  files: TrainingFileManifestItem[]
}

export interface TrainingFileManifestItem {
  form_field_name: string
  original_filename: string
  file_type:
    | 'sql_schema'
    | 'sql_data'
    | 'bi_template'
    | 'ai_template'
    | 'jupyter_notebook'
    | 'supporting_asset'
}

// 创建实训包任务（存根函数）
export function createTrainingPackageTask(files: File[], manifest: TrainingManifest) {
  console.warn('createTrainingPackageTask is a stub function')
  return Promise.resolve({
    task_id: 'stub-training-task-id',
    status: 'PENDING'
  })
}

// 获取实训包任务状态（存根函数）
export function getTrainingPackageTaskStatus(taskId: string) {
  console.warn('getTrainingPackageTaskStatus is a stub function')
  const status: TaskStatus = {
    status: 'PROCESSING',
    progress: 50,
    message: 'Stub training task status'
  }
  return Promise.resolve(status)
}