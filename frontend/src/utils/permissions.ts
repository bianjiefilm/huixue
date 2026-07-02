// 用户权限和角色管理工具
// 注意：这是本地权限检查工具，不依赖后端API

// 角色定义
export enum UserRole {
  STUDENT = 'student',
  TEACHER = 'teacher',
  ADMIN = 'admin',
  ASSISTANT = 'assistant' // 助教（如果需要）
}

// 权限代码定义
export enum PermissionCode {
  // 课程相关权限
  COURSE_CREATE = 'course:create',
  COURSE_READ = 'course:read',
  COURSE_UPDATE = 'course:update',
  COURSE_DELETE = 'course:delete',
  COURSE_PUBLISH = 'course:publish',
  COURSE_MANAGE = 'course:manage',

  // 任务相关权限
  TASK_CREATE = 'task:create',
  TASK_READ = 'task:read',
  TASK_UPDATE = 'task:update',
  TASK_DELETE = 'task:delete',
  TASK_GRADE = 'task:grade',

  // 课堂相关权限
  CLASSROOM_CREATE = 'classroom:create',
  CLASSROOM_READ = 'classroom:read',
  CLASSROOM_UPDATE = 'classroom:update',
  CLASSROOM_DELETE = 'classroom:delete',
  CLASSROOM_MANAGE = 'classroom:manage',
  CLASSROOM_INVITE = 'classroom:invite',

  // 学生管理权限
  STUDENT_VIEW_PROGRESS = 'student:view_progress',
  STUDENT_VIEW_GRADES = 'student:view_grades',
  STUDENT_MANAGE = 'student:manage',

  // 教师权限
  TEACHER_GRADE = 'teacher:grade',
  TEACHER_VIEW_ALL_PROGRESS = 'teacher:view_all_progress',
  TEACHER_MANAGE_SETTINGS = 'teacher:manage_settings',

  // 管理员权限
  ADMIN_USER_MANAGE = 'admin:user_manage',
  ADMIN_SYSTEM_CONFIG = 'admin:system_config',
  ADMIN_COURSE_APPROVE = 'admin:course_approve',
  ADMIN_STATISTICS_VIEW = 'admin:statistics_view',

  // 文件权限
  FILE_UPLOAD = 'file:upload',
  FILE_DOWNLOAD = 'file:download',
  FILE_MANAGE = 'file:manage',

  // 统计权限
  STATISTICS_VIEW = 'statistics:view',
  STATISTICS_EXPORT = 'statistics:export',

  // 金币权限
  COIN_VIEW = 'coin:view',
  COIN_MANAGE = 'coin:manage',
}

// 学生权限
const STUDENT_PERMISSIONS: PermissionCode[] = [
  PermissionCode.COURSE_READ,
  PermissionCode.TASK_READ,
  PermissionCode.CLASSROOM_READ,
  PermissionCode.FILE_DOWNLOAD,
  PermissionCode.STATISTICS_VIEW,
  PermissionCode.COIN_VIEW,
]

// 教师权限
const TEACHER_PERMISSIONS: PermissionCode[] = [
  PermissionCode.COURSE_CREATE,
  PermissionCode.COURSE_READ,
  PermissionCode.COURSE_UPDATE,
  PermissionCode.COURSE_PUBLISH,
  PermissionCode.TASK_CREATE,
  PermissionCode.TASK_READ,
  PermissionCode.TASK_UPDATE,
  PermissionCode.TASK_GRADE,
  PermissionCode.CLASSROOM_CREATE,
  PermissionCode.CLASSROOM_READ,
  PermissionCode.CLASSROOM_UPDATE,
  PermissionCode.CLASSROOM_MANAGE,
  PermissionCode.CLASSROOM_INVITE,
  PermissionCode.TEACHER_GRADE,
  PermissionCode.TEACHER_VIEW_ALL_PROGRESS,
  PermissionCode.TEACHER_MANAGE_SETTINGS,
  PermissionCode.STUDENT_VIEW_PROGRESS,
  PermissionCode.STUDENT_VIEW_GRADES,
  PermissionCode.FILE_UPLOAD,
  PermissionCode.FILE_DOWNLOAD,
  PermissionCode.FILE_MANAGE,
  PermissionCode.STATISTICS_VIEW,
  PermissionCode.STATISTICS_EXPORT,
  PermissionCode.COIN_VIEW,
  PermissionCode.COIN_MANAGE,
]

// 管理员权限（包含教师的所有权限）
const ADMIN_PERMISSIONS: PermissionCode[] = [
  ...TEACHER_PERMISSIONS,
  PermissionCode.COURSE_DELETE,
  PermissionCode.COURSE_MANAGE,
  PermissionCode.TASK_DELETE,
  PermissionCode.CLASSROOM_DELETE,
  PermissionCode.STUDENT_MANAGE,
  PermissionCode.ADMIN_USER_MANAGE,
  PermissionCode.ADMIN_SYSTEM_CONFIG,
  PermissionCode.ADMIN_COURSE_APPROVE,
  PermissionCode.ADMIN_STATISTICS_VIEW,
]

// 助教权限（教师权限的子集）
const ASSISTANT_PERMISSIONS: PermissionCode[] = [
  PermissionCode.COURSE_READ,
  PermissionCode.TASK_READ,
  PermissionCode.TASK_GRADE,
  PermissionCode.CLASSROOM_READ,
  PermissionCode.CLASSROOM_UPDATE,
  PermissionCode.TEACHER_GRADE,
  PermissionCode.TEACHER_VIEW_ALL_PROGRESS,
  PermissionCode.STUDENT_VIEW_PROGRESS,
  PermissionCode.STUDENT_VIEW_GRADES,
  PermissionCode.FILE_UPLOAD,
  PermissionCode.FILE_DOWNLOAD,
  PermissionCode.STATISTICS_VIEW,
  PermissionCode.COIN_VIEW,
]

// 角色权限映射
export const ROLE_PERMISSIONS: Record<UserRole, PermissionCode[]> = {
  [UserRole.STUDENT]: STUDENT_PERMISSIONS,
  [UserRole.TEACHER]: TEACHER_PERMISSIONS,
  [UserRole.ADMIN]: ADMIN_PERMISSIONS,
  [UserRole.ASSISTANT]: ASSISTANT_PERMISSIONS,
}

// 权限检查缓存
const permissionCache = new Map<string, { result: boolean; timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 检查用户是否有指定权限（本地实现，基于角色）
 */
export async function hasPermission(
  permissionCode: PermissionCode,
  userId?: string,
  context?: Record<string, any>
): Promise<boolean> {
  const cacheKey = `${userId || 'current'}:${permissionCode}:${JSON.stringify(context)}`
  const cached = permissionCache.get(cacheKey)

  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.result
  }

  try {
    // 从localStorage获取用户信息
    const userInfoStr = localStorage.getItem('userInfo')
    if (!userInfoStr) {
      return false
    }

    const userInfo = JSON.parse(userInfoStr)
    const userRole = userInfo.role as UserRole
    
    // 检查用户角色是否有该权限
    const rolePermissions = getRolePermissions(userRole)
    const result = rolePermissions.includes(permissionCode)

    permissionCache.set(cacheKey, { result, timestamp: Date.now() })
    return result
  } catch (error) {
    console.error('权限检查失败:', error)
    return false
  }
}

/**
 * 批量检查权限（本地实现）
 */
export async function hasPermissions(
  permissionCodes: PermissionCode[],
  userId?: string,
  context?: Record<string, any>
): Promise<Record<PermissionCode, boolean>> {
  try {
    const results: Record<PermissionCode, boolean> = {} as Record<PermissionCode, boolean>

    // 批量检查每个权限
    for (const code of permissionCodes) {
      results[code] = await hasPermission(code, userId, context)
    }

    return results
  } catch (error) {
    console.error('批量权限检查失败:', error)
    const results: Record<PermissionCode, boolean> = {} as Record<PermissionCode, boolean>
    permissionCodes.forEach(code => {
      results[code] = false
    })
    return results
  }
}

/**
 * 根据角色获取权限列表
 */
export function getRolePermissions(role: UserRole): PermissionCode[] {
  return ROLE_PERMISSIONS[role] || []
}

/**
 * 检查用户是否是指定角色
 */
export function isRole(userRole: string, targetRole: UserRole): boolean {
  return userRole === targetRole
}

/**
 * 检查用户是否是管理员或教师
 */
export function isAdminOrTeacher(userRole: string): boolean {
  return isRole(userRole, UserRole.ADMIN) || isRole(userRole, UserRole.TEACHER)
}

/**
 * 检查用户是否是管理员
 */
export function isAdmin(userRole: string): boolean {
  return isRole(userRole, UserRole.ADMIN)
}

/**
 * 检查用户是否是教师
 */
export function isTeacher(userRole: string): boolean {
  return isRole(userRole, UserRole.TEACHER)
}

/**
 * 检查用户是否是学生
 */
export function isStudent(userRole: string): boolean {
  return isRole(userRole, UserRole.STUDENT)
}

/**
 * 获取用户角色显示名称
 */
export function getRoleDisplayName(role: UserRole): string {
  const roleNames: Record<UserRole, string> = {
    [UserRole.STUDENT]: '学生',
    [UserRole.TEACHER]: '教师',
    [UserRole.ADMIN]: '管理员',
    [UserRole.ASSISTANT]: '助教',
  }
  return roleNames[role] || '未知角色'
}

/**
 * 获取权限显示名称
 */
export function getPermissionDisplayName(code: PermissionCode): string {
  const permissionNames: Record<PermissionCode, string> = {
    [PermissionCode.COURSE_CREATE]: '创建课程',
    [PermissionCode.COURSE_READ]: '查看课程',
    [PermissionCode.COURSE_UPDATE]: '编辑课程',
    [PermissionCode.COURSE_DELETE]: '删除课程',
    [PermissionCode.COURSE_PUBLISH]: '发布课程',
    [PermissionCode.COURSE_MANAGE]: '管理所有课程',
    [PermissionCode.TASK_CREATE]: '创建任务',
    [PermissionCode.TASK_READ]: '查看任务',
    [PermissionCode.TASK_UPDATE]: '编辑任务',
    [PermissionCode.TASK_DELETE]: '删除任务',
    [PermissionCode.TASK_GRADE]: '批改任务',
    [PermissionCode.CLASSROOM_CREATE]: '创建课堂',
    [PermissionCode.CLASSROOM_READ]: '查看课堂',
    [PermissionCode.CLASSROOM_UPDATE]: '编辑课堂',
    [PermissionCode.CLASSROOM_DELETE]: '删除课堂',
    [PermissionCode.CLASSROOM_MANAGE]: '管理课堂',
    [PermissionCode.CLASSROOM_INVITE]: '邀请学生',
    [PermissionCode.STUDENT_VIEW_PROGRESS]: '查看学生进度',
    [PermissionCode.STUDENT_VIEW_GRADES]: '查看学生成绩',
    [PermissionCode.STUDENT_MANAGE]: '管理学生',
    [PermissionCode.TEACHER_GRADE]: '教师批改',
    [PermissionCode.TEACHER_VIEW_ALL_PROGRESS]: '查看所有进度',
    [PermissionCode.TEACHER_MANAGE_SETTINGS]: '管理设置',
    [PermissionCode.ADMIN_USER_MANAGE]: '用户管理',
    [PermissionCode.ADMIN_SYSTEM_CONFIG]: '系统配置',
    [PermissionCode.ADMIN_COURSE_APPROVE]: '审批课程',
    [PermissionCode.ADMIN_STATISTICS_VIEW]: '查看系统统计',
    [PermissionCode.FILE_UPLOAD]: '上传文件',
    [PermissionCode.FILE_DOWNLOAD]: '下载文件',
    [PermissionCode.FILE_MANAGE]: '管理文件',
    [PermissionCode.STATISTICS_VIEW]: '查看统计',
    [PermissionCode.STATISTICS_EXPORT]: '导出统计',
    [PermissionCode.COIN_VIEW]: '查看金币',
    [PermissionCode.COIN_MANAGE]: '管理金币',
  }
  return permissionNames[code] || code
}

/**
 * 清除权限缓存
 */
export function clearPermissionCache(): void {
  permissionCache.clear()
}

/**
 * 检查是否可以公开成绩（教师权限）
 */
export async function canViewStudentProgress(teacherId: string, classroomId?: string): Promise<boolean> {
  return await hasPermission(PermissionCode.STUDENT_VIEW_PROGRESS, teacherId, { classroomId })
}

/**
 * 检查是否可以批改作业
 */
export async function canGradeSubmissions(userId: string, classroomId?: string): Promise<boolean> {
  return await hasPermission(PermissionCode.TASK_GRADE, userId, { classroomId })
}

/**
 * 检查是否可以管理课程
 */
export async function canManageCourse(userId: string, courseId?: string): Promise<boolean> {
  const hasCreate = await hasPermission(PermissionCode.COURSE_CREATE, userId)
  const hasUpdate = await hasPermission(PermissionCode.COURSE_UPDATE, userId, { courseId })
  const hasManage = await hasPermission(PermissionCode.COURSE_MANAGE, userId)

  return hasCreate || hasUpdate || hasManage
}

/**
 * 检查是否可以查看统计数据
 */
export async function canViewStatistics(userId: string, scope: 'personal' | 'classroom' | 'system' = 'personal'): Promise<boolean> {
  if (scope === 'personal') {
    return await hasPermission(PermissionCode.STATISTICS_VIEW, userId)
  } else if (scope === 'classroom') {
    return await hasPermission(PermissionCode.STATISTICS_VIEW, userId) ||
           await hasPermission(PermissionCode.TEACHER_VIEW_ALL_PROGRESS, userId)
  } else {
    return await hasPermission(PermissionCode.ADMIN_STATISTICS_VIEW, userId)
  }
}

/**
 * 初始化用户权限（本地实现）
 */
export async function initializeUserPermissions(userId: string, role: UserRole): Promise<void> {
  try {
    // 本地实现：只清除缓存，权限由角色决定
    clearPermissionCache()
    console.log(`用户 ${userId} 的权限已初始化为角色: ${role}`)
  } catch (error) {
    console.error('初始化用户权限失败:', error)
    throw error
  }
}
