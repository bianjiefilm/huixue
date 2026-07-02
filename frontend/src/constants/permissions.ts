// 角色定义
export enum Role {
  ADMIN = 'admin',        // 系统管理员
  TEACHER = 'teacher',    // 教师
  STUDENT = 'student'     // 学生
}

// 权限点定义
export enum Permission {
  // 课堂管理
  CLASSROOM_CREATE = 'classroom:create',
  CLASSROOM_EDIT = 'classroom:edit',
  CLASSROOM_DELETE = 'classroom:delete',
  CLASSROOM_VIEW = 'classroom:view',
  
  // 学生管理
  STUDENT_ADD = 'student:add',
  STUDENT_REMOVE = 'student:remove',
  STUDENT_VIEW = 'student:view',
  
  // 课程管理
  COURSE_CREATE = 'course:create',
  COURSE_EDIT = 'course:edit',
  COURSE_DELETE = 'course:delete',
  COURSE_PUBLISH = 'course:publish',
  COURSE_VIEW = 'course:view',
  
  // 作业评分
  HOMEWORK_GRADE = 'homework:grade',
  HOMEWORK_VIEW = 'homework:view',
  HOMEWORK_SUBMIT = 'homework:submit',
  
  // 学情分析
  ANALYTICS_VIEW = 'analytics:view',
  
  // 优秀作业
  EXCELLENT_WORKS_VIEW = 'excellent_works:view',
  EXCELLENT_WORKS_COLLECT = 'excellent_works:collect',
  
  // 数据游乐场
  PLAYGROUND_ACCESS = 'playground:access',
  
  // 系统管理
  SYSTEM_MANAGE = 'system:manage',
  USER_MANAGE = 'user:manage'
}

// 角色权限映射
export const rolePermissions: Record<Role, Permission[]> = {
  [Role.ADMIN]: [
    // 管理员拥有所有权限
    ...Object.values(Permission)
  ],
  [Role.TEACHER]: [
    Permission.CLASSROOM_CREATE,
    Permission.CLASSROOM_EDIT,
    Permission.CLASSROOM_DELETE,
    Permission.CLASSROOM_VIEW,
    Permission.STUDENT_ADD,
    Permission.STUDENT_REMOVE,
    Permission.STUDENT_VIEW,
    Permission.COURSE_CREATE,
    Permission.COURSE_EDIT,
    Permission.COURSE_DELETE,
    Permission.COURSE_PUBLISH,
    Permission.COURSE_VIEW,
    Permission.HOMEWORK_GRADE,
    Permission.HOMEWORK_VIEW,
    Permission.ANALYTICS_VIEW,
    Permission.EXCELLENT_WORKS_VIEW,
    Permission.EXCELLENT_WORKS_COLLECT
  ],
  [Role.STUDENT]: [
    Permission.CLASSROOM_VIEW,
    Permission.COURSE_VIEW,
    Permission.HOMEWORK_SUBMIT,
    Permission.HOMEWORK_VIEW,
    Permission.EXCELLENT_WORKS_VIEW,
    Permission.PLAYGROUND_ACCESS
  ]
}

// 路由权限映射
export const routePermissions: Record<string, Permission[]> = {
  // 课堂相关
  '/classroom': [Permission.CLASSROOM_VIEW],
  '/classroom/create': [Permission.CLASSROOM_CREATE],
  '/classroom/:id/edit': [Permission.CLASSROOM_EDIT],
  
  // 课程相关
  '/course': [Permission.COURSE_VIEW],
  '/course/training/create': [Permission.COURSE_CREATE],
  '/course/training/:id/edit': [Permission.COURSE_EDIT],
  
  // 作业评分
  '/classroom/:id/homework': [Permission.HOMEWORK_VIEW],
  '/classroom/:id/homework/grade': [Permission.HOMEWORK_GRADE],
  
  // 学情分析
  '/classroom/:id/analytics': [Permission.ANALYTICS_VIEW],
  
  // 数据游乐场
  '/playground': [Permission.PLAYGROUND_ACCESS],
  
  // 系统管理
  '/admin': [Permission.SYSTEM_MANAGE],
  '/admin/users': [Permission.USER_MANAGE]
}

// 功能权限映射
export const featurePermissions = {
  // 课堂操作
  createClassroom: [Permission.CLASSROOM_CREATE],
  editClassroom: [Permission.CLASSROOM_EDIT],
  deleteClassroom: [Permission.CLASSROOM_DELETE],
  
  // 学生管理
  addStudent: [Permission.STUDENT_ADD],
  removeStudent: [Permission.STUDENT_REMOVE],
  
  // 课程操作
  createCourse: [Permission.COURSE_CREATE],
  editCourse: [Permission.COURSE_EDIT],
  deleteCourse: [Permission.COURSE_DELETE],
  publishCourse: [Permission.COURSE_PUBLISH],
  
  // 作业操作
  submitHomework: [Permission.HOMEWORK_SUBMIT],
  gradeHomework: [Permission.HOMEWORK_GRADE],
  
  // 优秀作业
  collectWork: [Permission.EXCELLENT_WORKS_COLLECT]
}