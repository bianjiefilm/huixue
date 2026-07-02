// 课程管理相关类型定义

// 课程类别枚举
export enum CourseType {
  PRACTICE = 'practice',  // 实践课程
  TRAINING = 'training'   // 实训课程
}

// 课程发布状态枚举
export enum CourseStatus {
  PUBLISHED = 'published',      // 已发布
  UNPUBLISHED = 'unpublished',  // 未发布
  PENDING = 'pending',          // 待审批
  REJECTED = 'rejected'         // 已驳回
}

// 审批状态枚举（与后端一致使用大写）
export enum ApprovalStatus {
  PENDING = 'PENDING',     // 待审批
  APPROVED = 'APPROVED',   // 已同意
  REJECTED = 'REJECTED',   // 已驳回
  CANCELLED = 'CANCELLED'  // 用户撤销
}

// 审批类型枚举（与后端一致使用大写）
export enum ApprovalType {
  PUBLISH = 'PUBLISH',     // 发布申请
  UNPUBLISH = 'UNPUBLISH'  // 撤销发布申请
}

// 课程分类节点
export interface CourseCategory {
  key: string;           // 分类键值
  title: string;         // 分类名称
  children?: CourseCategory[];  // 子分类
}

// 基础课程信息
export interface BaseCourse {
  id: string;
  title: string;
  cover: string;
  teacher: string;
  university: string;
  description: string;
  status: CourseStatus;
  createdAt: string;
  updatedAt: string;
}

// 实践课程信息
export interface PracticeCourse extends BaseCourse {
  type: CourseType.PRACTICE;
  direction: string;     // 所属方向
  category: string;      // 所属分类
}

// 实训课程信息
export interface TrainingCourse extends BaseCourse {
  type: CourseType.TRAINING;
  industry: string;      // 所属行业
}

// 课程审批记录
export interface CourseApproval {
  id: string;
  courseId: string;      // 关联课程ID
  courseTitle: string;   // 课程标题
  applicant: string;     // 申请人
  applicantId: string;   // 申请人ID
  type: ApprovalType;    // 申请类型
  status: ApprovalStatus;// 审批状态
  reason?: string;       // 申请理由
  feedback?: string;     // 审批意见
  appliedAt: string;     // 申请时间
  approvedAt?: string;   // 审批时间
}

// 实验环境类型
export enum EnvironmentType {
  NORMAL = 'normal',    // 普通实践
  JUPYTER = 'jupyter',  // Jupyter环境
  DESKTOP = 'desktop'   // 云桌面
}

// 实验环境配置
export interface EnvironmentConfig {
  id: string;
  name: string;         // 环境名称
  type: EnvironmentType;// 环境类型
  storage: {
    min: number;        // 最小存储空间(MB)
    max: number;        // 最大存储空间(MB)
    default: number;    // 默认存储空间(MB)
  };
  memory: {
    min: number;        // 最小内存(MB)
    max: number;        // 最大内存(MB)
    default: number;    // 默认内存(MB)
  };
  cpu: {
    min: number;        // 最小CPU核心数
    max: number;        // 最大CPU核心数
    default: number;    // 默认CPU核心数
  };
}

// 服务器资源使用情况
export interface ServerResource {
  id: string;
  name: string;           // 服务器名称
  type: 'application' | 'compute'; // 服务器类型：应用服务器或计算节点
  cpu: {
    total: number;        // 总核心数
    used: number;         // 已用核心数
    usageRate: number;    // 使用率
  };
  memory: {
    total: number;        // 总内存(MB)
    used: number;         // 已用内存(MB)
    usageRate: number;    // 使用率
  };
  storage: {
    total: number;        // 总存储空间(MB)
    used: number;         // 已用存储空间(MB)
    usageRate: number;    // 使用率
  };
}

// 容器进程信息
export interface ContainerProcess {
  id: string;
  userName: string;       // 用户姓名
  userId: string;         // 用户账号
  courseName: string;     // 课程名称
  experimentType: EnvironmentType; // 实验类型
  startTime: string;      // 开始时间
  runningTime: number;    // 运行时长(秒)
  cpu: number;            // CPU使用率
  memory: number;         // 内存使用(MB)
  selected?: boolean;     // 是否选中(用于批量操作)
} 