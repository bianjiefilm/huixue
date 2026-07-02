// 任务类型定义
export enum TaskType {
  JUDGE = 'judge',           // 判断题
  CHOICE = 'choice',         // 选择题
  PRACTICE = 'practice',     // 实践题
  FILL_BLANK = 'fill_blank', // 填空题
  ESSAY = 'essay',          // 简答题
  FILE_UPLOAD = 'file_upload' // 文件上传题
}

// 任务难度级别
export enum TaskDifficulty {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced'
}

// 任务状态
export enum TaskStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

// 基础任务接口
export interface BaseTask {
  id: string
  title: string
  description: string
  type: TaskType
  difficulty: TaskDifficulty
  points: number // 分值
  timeLimit?: number // 时间限制（分钟）
  skills: string[] // 相关技能标签
  createdAt: string
  updatedAt: string
}

// 判断题
export interface JudgeTask extends BaseTask {
  type: TaskType.JUDGE
  question: string
  correctAnswer: boolean // true/false
  explanation?: string // 答案解析
}

// 选择题
export interface ChoiceTask extends BaseTask {
  type: TaskType.CHOICE
  question: string
  options: string[] // 选项数组
  correctAnswer: number[] // 正确答案索引数组（支持多选）
  allowMultiple: boolean // 是否支持多选
  explanation?: string // 答案解析
}

// 实践题
export interface PracticeTask extends BaseTask {
  type: TaskType.PRACTICE
  instructions: string
  environment: {
    type: 'code' | 'html' | 'shell' | 'jupyter'
    template?: string // 初始代码模板
    testCases?: TestCase[]
  }
  evaluationCriteria: string[] // 评价标准
}

// 填空题
export interface FillBlankTask extends BaseTask {
  type: TaskType.FILL_BLANK
  content: string // 包含占位符的内容，如：中国首都位于__，简称__。
  blanks: {
    id: string
    placeholder: string
    correctAnswers: string[] // 支持多个正确答案
    caseSensitive: boolean // 是否区分大小写
    partialMatch: boolean // 是否支持部分匹配
  }[]
  explanation?: string // 答案解析
}

// 简答题
export interface EssayTask extends BaseTask {
  type: TaskType.ESSAY
  question: string
  wordLimit?: {
    min?: number
    max?: number
  }
  gradingCriteria: string[] // 评分标准
  sampleAnswer?: string // 参考答案（教师可见）
}

// 文件上传题
export interface FileUploadTask extends BaseTask {
  type: TaskType.FILE_UPLOAD
  instructions: string
  fileRequirements: {
    allowedTypes: string[] // 允许的文件类型，如 ['.pdf', '.docx', '.zip']
    maxSize: number // 最大文件大小（字节）
    maxFiles: number // 最大文件数量
  }
  gradingCriteria: string[] // 评分标准
}

// 任务联合类型
export type Task = JudgeTask | ChoiceTask | PracticeTask | FillBlankTask | EssayTask | FileUploadTask

// 测试用例
export interface TestCase {
  id: string
  input: string
  expectedOutput: string
  hidden: boolean // 是否为隐藏测试用例
  timeout?: number // 超时时间（毫秒）
}

// 任务提交记录
export interface TaskSubmission {
  id: string
  taskId: string
  userId: string
  classroomId: string
  courseId: string
  submittedAt: string
  status: TaskStatus
  score?: number
  maxScore: number
  timeSpent?: number // 耗时（分钟）
  attempts: number // 尝试次数
}

// 判断题提交
export interface JudgeSubmission extends TaskSubmission {
  answer: boolean
}

// 选择题提交
export interface ChoiceSubmission extends TaskSubmission {
  answer: number[]
}

// 实践题提交
export interface PracticeSubmission extends TaskSubmission {
  code?: string
  testResults?: {
    testCaseId: string
    passed: boolean
    output?: string
    error?: string
    executionTime?: number
  }[]
}

// 填空题提交
export interface FillBlankSubmission extends TaskSubmission {
  answers: {
    blankId: string
    answer: string
    isCorrect?: boolean
    score?: number
  }[]
}

// 简答题提交
export interface EssaySubmission extends TaskSubmission {
  answer: string // 富文本内容
  wordCount?: number
  teacherComments?: string
  teacherScore?: number
}

// 文件上传题提交
export interface FileUploadSubmission extends TaskSubmission {
  files: {
    id: string
    name: string
    url: string
    size: number
    uploadedAt: string
  }[]
  teacherComments?: string
  teacherScore?: number
}

// 提交联合类型
export type Submission = JudgeSubmission | ChoiceSubmission | PracticeSubmission | FillBlankSubmission | EssaySubmission | FileUploadSubmission

// 任务评价结果
export interface TaskEvaluation {
  submissionId: string
  score: number
  maxScore: number
  percentage: number
  feedback?: string
  breakdown?: {
    criteria: string
    score: number
    maxScore: number
    comment?: string
  }[]
  evaluatedBy?: string // 评价人ID
  evaluatedAt: string
}

// 任务组件Props类型
export interface TaskComponentProps<T extends Task = Task> {
  task: T
  submission?: Submission
  isPreview?: boolean // 是否为预览模式
  isTeacher?: boolean // 是否为教师视图
  onSubmit?: (submission: Partial<Submission>) => void
  onSave?: (draft: Partial<Submission>) => void
}

// 任务配置
export interface TaskConfig {
  type: TaskType
  name: string
  description: string
  icon: string
  color: string
  hasAutoGrading: boolean // 是否支持自动评分
  supportsPartialCredit: boolean // 是否支持部分分数
  requiresEnvironment: boolean // 是否需要运行环境
}

// 任务类型配置映射
export const TASK_TYPE_CONFIGS: Record<TaskType, TaskConfig> = {
  [TaskType.JUDGE]: {
    type: TaskType.JUDGE,
    name: '判断题',
    description: '判断题，要求学生选择正确或错误',
    icon: 'check-circle',
    color: 'blue',
    hasAutoGrading: true,
    supportsPartialCredit: false,
    requiresEnvironment: false
  },
  [TaskType.CHOICE]: {
    type: TaskType.CHOICE,
    name: '选择题',
    description: '选择题，支持单选和多选',
    icon: 'unordered-list',
    color: 'green',
    hasAutoGrading: true,
    supportsPartialCredit: true,
    requiresEnvironment: false
  },
  [TaskType.PRACTICE]: {
    type: TaskType.PRACTICE,
    name: '实践题',
    description: '编程实践题，需要编写代码解决实际问题',
    icon: 'code',
    color: 'purple',
    hasAutoGrading: true,
    supportsPartialCredit: true,
    requiresEnvironment: true
  },
  [TaskType.FILL_BLANK]: {
    type: TaskType.FILL_BLANK,
    name: '填空题',
    description: '填空题，支持多个空位和部分匹配',
    icon: 'form',
    color: 'orange',
    hasAutoGrading: true,
    supportsPartialCredit: true,
    requiresEnvironment: false
  },
  [TaskType.ESSAY]: {
    type: TaskType.ESSAY,
    name: '简答题',
    description: '主观题，需要教师手动评分',
    icon: 'file-text',
    color: 'red',
    hasAutoGrading: false,
    supportsPartialCredit: true,
    requiresEnvironment: false
  },
  [TaskType.FILE_UPLOAD]: {
    type: TaskType.FILE_UPLOAD,
    name: '文件上传题',
    description: '要求学生上传文件作品',
    icon: 'upload',
    color: 'cyan',
    hasAutoGrading: false,
    supportsPartialCredit: true,
    requiresEnvironment: false
  }
}

// 任务难度配置
export const TASK_DIFFICULTY_CONFIGS: Record<TaskDifficulty, { name: string; color: string; multiplier: number }> = {
  [TaskDifficulty.BEGINNER]: {
    name: '初级',
    color: 'green',
    multiplier: 1.0
  },
  [TaskDifficulty.INTERMEDIATE]: {
    name: '中级',
    color: 'orange',
    multiplier: 1.2
  },
  [TaskDifficulty.ADVANCED]: {
    name: '高级',
    color: 'red',
    multiplier: 1.5
  }
}

// 工具函数
export function getTaskTypeConfig(type: TaskType): TaskConfig {
  return TASK_TYPE_CONFIGS[type]
}

export function getTaskDifficultyConfig(difficulty: TaskDifficulty) {
  return TASK_DIFFICULTY_CONFIGS[difficulty]
}

export function calculateTaskScore(task: Task, submission: Submission): number {
  if (!submission.score) return 0
  return Math.min(submission.score, task.points)
}

export function isTaskCompleted(submission?: Submission): boolean {
  return submission?.status === TaskStatus.COMPLETED
}

export function getTaskProgress(task: Task, submission?: Submission): number {
  if (!submission) return 0
  if (submission.status === TaskStatus.COMPLETED) return 100

  // 根据任务类型计算进度
  switch (task.type) {
    case TaskType.PRACTICE:
      const practiceSubmission = submission as PracticeSubmission
      if (practiceSubmission.testResults) {
        const passed = practiceSubmission.testResults.filter(r => r.passed).length
        const total = practiceSubmission.testResults.length
        return total > 0 ? (passed / total) * 100 : 0
      }
      return 0

    case TaskType.FILL_BLANK:
      const fillBlankSubmission = submission as FillBlankSubmission
      if (fillBlankSubmission.answers) {
        const answered = fillBlankSubmission.answers.filter(a => a.answer.trim()).length
        return (answered / fillBlankSubmission.answers.length) * 100
      }
      return 0

    default:
      return submission.status === TaskStatus.IN_PROGRESS ? 50 : 0
  }
}

