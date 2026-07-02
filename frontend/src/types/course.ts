// 课程相关类型定义

// 教材课程类型
export interface CourseResource {
  id: string;
  title: string;
  cover: string;
  teacher: string;
  university: string;
  description: string;
  tags: string[];
  views?: number;
  rating?: number;
  students?: number;
  chapters?: number;
  practices?: number;
}

// 微型实验课程类型
export interface MicroCourse {
  id: string;
  title: string;
  cover: string;
  type: string;
  level: string;
  popularity: number;
  views: number;
  direction?: string; // 实践方向
  category?: string; // 实践分类
  introduction?: string; // 实践介绍
  coins?: number; // 金币数量
  skills?: string[]; // 技能标签
  tasks?: Task[]; // 任务列表
}

// 标签类型
export interface Tag {
  id: string;
  name: string;
}

// 任务类型
export interface Task {
  id: string;
  title: string;
  type: 'judge' | 'choice' | 'practice'; // 判断题、选择题、实践题
  difficulty: number; // 难度 1-5
  coins: number; // 奖励金币
  skills: string[]; // 相关技能
  completed?: boolean; // 是否已完成
  description?: string; // 任务描述
}

// 课堂类型
export interface Classroom {
  id: string;
  name: string;
  teacherName?: string;
  teacher_name?: string; // API返回的教师名称字段
  teacher?: string; // 兼容旧字段
  studentCount?: number;
  student_count?: number; // API返回的学生数字段
  students?: number; // 兼容旧字段
  createdAt: string;
  credits?: number; // 学分
  startDate?: string; // 开始时间
  start_date?: string; // API返回的开始日期字段
  endDate?: string; // 结束时间
  end_date?: string; // API返回的结束日期字段
  experiment_count?: number; // 实验数量
  progress?: number; // 学习进度百分比
  semester?: string; // 学期
  description?: string; // 课堂描述
  status?: 'learning' | 'upcoming' | 'completed'; // 课堂状态
}

// 作业状态类型
export type HomeworkStatus = 'not_submitted' | 'pending' | 'passed' | 'failed';

// 作业项类型
export interface Homework {
  id: string;
  title: string;
  description: string;
  deadline: string; // 截止日期
  status: HomeworkStatus;
  score?: number; // 得分
  feedback?: string; // 教师反馈
  submittedAt?: string; // 提交时间
  attachments?: HomeworkAttachment[]; // 作业附件
}

// 作业附件类型
export interface HomeworkAttachment {
  id: string;
  name: string;
  url: string;
  size: number;
  type: string;
  createdAt: string;
}

// 课堂中的课程详情类型
export interface ClassroomCourseDetail {
  id: string;
  name: string;
  status: 'unpublished' | 'learning' | 'makeup' | 'completed'; // 未发布、学习中、补交中、已完成
  courseType: 'practice' | 'training'; // 实践课程或实训课程
  learningCount: number; // 学习中人数
  completedCount: number; // 已完成人数
  notStartedCount: number; // 未开始人数
  startDate?: string; // 开始日期
  endDate?: string; // 结束日期
  remainingTime?: string; // 剩余时间
  createTime?: string; // 创建时间
  coins: number; // 金币数
  difficulty: number; // 难度系数 1-5
  classroom: { // 所属课堂信息
    id: string;
    name: string;
  };
  tasks: ClassroomCourseTask[]; // 课程任务
  skills: ClassroomCourseSkill[]; // 技能标签
  studentProgress?: { // 学生学习进度（学生视图专用）
    completedTaskCount: number; // 已完成任务数
    totalTaskCount: number; // 总任务数
    completionRate: number; // 完成率（百分比）
    earnedCoins: number; // 获得的金币
  };
  isStudentView?: boolean; // 是否为学生视图
  // 实训项目新增字段
  trainingType?: 'ai' | 'bi' | 'jupyter'; // 实训类型
  industry?: string; // 行业分类
  chapters?: TrainingChapter[]; // 实训目录章节
  introduction?: string; // 实训介绍
  // 学生端实训详情新增字段
  homeworks?: Homework[]; // 学生作业列表，仅学生视图显示
}

// 课堂中的课程任务
export interface ClassroomCourseTask {
  id: string;
  title: string;
  type: 'judge' | 'choice' | 'practice'; // 判断题、选择题、实践题
  difficulty: number; // 难度 1-5
  coins: number; // 奖励金币
  description: string; // 任务描述
  completed: boolean; // 是否已完成
  score?: number; // 学生得分
  timeCost?: string; // 挑战用时
  skills: string[]; // 相关技能
}

// 课堂中的课程技能标签
export interface ClassroomCourseSkill {
  id: string;
  name: string;
  isLighted: boolean; // 是否已点亮
}

// 实训章节
export interface TrainingChapter {
  id: string;
  title: string;
  tasks: TrainingTask[];
}

// 实训任务
export interface TrainingTask {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  coins: number;
  type: 'theory' | 'practice'; // 理论学习或实践操作
  completed?: boolean; // 是否已完成
} 
