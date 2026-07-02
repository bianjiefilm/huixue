import dayjs from 'dayjs'
import type { ClassroomCourseDetail } from '@/types/course'

// 课程状态枚举
export enum CourseStatus {
  UNPUBLISHED = 'unpublished',
  LEARNING = 'learning',
  MAKEUP = 'makeup',
  COMPLETED = 'completed'
}

// 课程状态文本映射
export const COURSE_STATUS_TEXT = {
  [CourseStatus.UNPUBLISHED]: '未发布',
  [CourseStatus.LEARNING]: '学习中',
  [CourseStatus.MAKEUP]: '补交中',
  [CourseStatus.COMPLETED]: '已完成'
}

// 课程状态样式类映射
export const COURSE_STATUS_CLASS = {
  [CourseStatus.UNPUBLISHED]: 'status-unpublished',
  [CourseStatus.LEARNING]: 'status-learning',
  [CourseStatus.MAKEUP]: 'status-makeup',
  [CourseStatus.COMPLETED]: 'status-completed'
}

// 检查教师是否有权限修改课程状态
export function canTeacherChangeCourseStatus(userRole: string): boolean {
  return userRole === 'teacher' || userRole === 'admin'
}

// 检查是否可以发布课程（从未发布到学习中）
export function canPublishCourse(course: ClassroomCourseDetail): boolean {
  return course.status === CourseStatus.UNPUBLISHED
}

// 检查是否可以取消发布课程（从学习中到未发布）
export function canUnpublishCourse(course: ClassroomCourseDetail): boolean {
  return course.status === CourseStatus.LEARNING
}

// 计算课程的当前状态（基于时间和手动设置）
export function calculateCourseStatus(course: ClassroomCourseDetail): CourseStatus {
  const now = dayjs()
  const startDate = course.startDate ? dayjs(course.startDate) : null
  const endDate = course.endDate ? dayjs(course.endDate) : null

  // 如果课程还未开始，返回未发布状态
  if (startDate && now.isBefore(startDate)) {
    return CourseStatus.UNPUBLISHED
  }

  // 如果课程已结束
  if (endDate && now.isAfter(endDate)) {
    // 检查是否还有学生未完成
    const hasUnfinishedStudents = course.notStartedCount > 0 || course.learningCount > 0
    if (hasUnfinishedStudents) {
      // 如果在补交期内（结束时间后7天内），返回补交中状态
      const makeupEndDate = endDate.add(7, 'day')
      if (now.isBefore(makeupEndDate)) {
        return CourseStatus.MAKEUP
      }
    }
    // 补交期结束后，返回已完成状态
    return CourseStatus.COMPLETED
  }

  // 如果课程已发布且在进行中，返回学习中状态
  if (course.status === CourseStatus.LEARNING || course.status === CourseStatus.MAKEUP) {
    return course.status
  }

  // 默认返回未发布状态
  return CourseStatus.UNPUBLISHED
}

// 获取课程状态变更建议
export function getCourseStatusChangeSuggestions(course: ClassroomCourseDetail): {
  canPublish: boolean
  canUnpublish: boolean
  autoStatus: CourseStatus
  suggestions: string[]
} {
  const currentStatus = course.status
  const calculatedStatus = calculateCourseStatus(course)
  const suggestions: string[] = []

  const canPublish = canPublishCourse(course)
  const canUnpublish = canUnpublishCourse(course)

  // 如果计算出的状态与当前状态不一致，给出建议
  if (calculatedStatus !== currentStatus) {
    switch (calculatedStatus) {
      case CourseStatus.MAKEUP:
        suggestions.push('课程已过截止时间，建议进入补交阶段')
        break
      case CourseStatus.COMPLETED:
        suggestions.push('课程已结束，建议标记为已完成')
        break
    }
  }

  // 检查时间相关建议
  const now = dayjs()
  const endDate = course.endDate ? dayjs(course.endDate) : null

  if (endDate) {
    const daysUntilEnd = endDate.diff(now, 'day')
    if (daysUntilEnd === 0) {
      suggestions.push('课程今日截止，请提醒学生及时提交')
    } else if (daysUntilEnd === 1) {
      suggestions.push('课程明日截止，请提醒学生及时提交')
    } else if (daysUntilEnd < 0) {
      const daysOverdue = Math.abs(daysUntilEnd)
      if (daysOverdue <= 7) {
        suggestions.push(`课程已逾期${daysOverdue}天，建议开启补交`)
      } else {
        suggestions.push(`课程已逾期${daysOverdue}天，建议结束课程`)
      }
    }
  }

  return {
    canPublish,
    canUnpublish,
    autoStatus: calculatedStatus,
    suggestions
  }
}

// 批量更新课程状态（用于定时任务或管理员操作）
export function batchUpdateCourseStatuses(courses: ClassroomCourseDetail[]): {
  updated: ClassroomCourseDetail[]
  unchanged: ClassroomCourseDetail[]
} {
  const updated: ClassroomCourseDetail[] = []
  const unchanged: ClassroomCourseDetail[] = []

  courses.forEach(course => {
    const calculatedStatus = calculateCourseStatus(course)
    if (calculatedStatus !== course.status) {
      course.status = calculatedStatus
      updated.push(course)
    } else {
      unchanged.push(course)
    }
  })

  return { updated, unchanged }
}

// 获取课程状态的时间信息
export function getCourseTimeInfo(course: ClassroomCourseDetail): {
  isStarted: boolean
  isEnded: boolean
  isInMakeupPeriod: boolean
  daysUntilStart: number
  daysUntilEnd: number
  daysSinceEnd: number
} {
  const now = dayjs()
  const startDate = course.startDate ? dayjs(course.startDate) : null
  const endDate = course.endDate ? dayjs(course.endDate) : null

  const isStarted = !startDate || now.isAfter(startDate)
  const isEnded = endDate && now.isAfter(endDate)
  const isInMakeupPeriod = isEnded && endDate && now.isBefore(endDate.add(7, 'day'))

  const daysUntilStart = startDate ? startDate.diff(now, 'day') : 0
  const daysUntilEnd = endDate ? endDate.diff(now, 'day') : 0
  const daysSinceEnd = endDate ? now.diff(endDate, 'day') : 0

  return {
    isStarted,
    isEnded,
    isInMakeupPeriod,
    daysUntilStart,
    daysUntilEnd,
    daysSinceEnd
  }
}

// 格式化剩余时间显示
export function formatRemainingTime(course: ClassroomCourseDetail): string {
  const timeInfo = getCourseTimeInfo(course)

  if (!timeInfo.isStarted) {
    return `${Math.abs(timeInfo.daysUntilStart)}天后开始`
  }

  if (timeInfo.isInMakeupPeriod) {
    const makeupEndDate = course.endDate ? dayjs(course.endDate).add(7, 'day') : null
    if (makeupEndDate) {
      const daysLeft = makeupEndDate.diff(dayjs(), 'day')
      return `补交中，还剩${daysLeft}天`
    }
  }

  if (timeInfo.daysUntilEnd > 0) {
    if (timeInfo.daysUntilEnd === 1) {
      return '明天截止'
    }
    return `还剩${timeInfo.daysUntilEnd}天`
  }

  if (timeInfo.daysUntilEnd === 0) {
    return '今日截止'
  }

  if (timeInfo.daysSinceEnd > 0) {
    return `已逾期${timeInfo.daysSinceEnd}天`
  }

  return ''
}

