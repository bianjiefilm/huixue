import dayjs from 'dayjs';
import type { Classroom } from '@/types/course';

/**
 * 计算课堂状态
 * @param startDate 开始日期
 * @param endDate 结束日期
 * @returns 课堂状态
 */
export function getClassroomStatus(startDate: string, endDate: string): 'learning' | 'upcoming' | 'completed' {
  const now = dayjs();
  const start = dayjs(startDate);
  const end = dayjs(endDate);
  
  if (now.isBefore(start)) {
    return 'upcoming'; // 未开始
  } else if (now.isAfter(end)) {
    return 'completed'; // 已结课
  } else {
    return 'learning'; // 正在上课
  }
}

/**
 * 计算学期
 * @param startDate 开始日期
 * @returns 学期字符串
 */
export function getSemester(startDate: string): string {
  const date = dayjs(startDate);
  const year = date.year();
  const month = date.month() + 1; // dayjs的month从0开始
  
  if (month >= 2 && month <= 7) {
    return `${year}年春季学期`;
  } else if (month >= 8 && month <= 12) {
    return `${year}年秋季学期`;
  } else {
    return `${year-1}年秋季学期`; // 1月份属于上一年的秋季学期
  }
}

/**
 * 处理课堂数据，添加计算字段
 * @param classroom 原始课堂数据
 * @returns 处理后的课堂数据
 */
export function processClassroom(classroom: Classroom): Classroom {
  const startDate = classroom.start_date || classroom.startDate || '';
  const endDate = classroom.end_date || classroom.endDate || '';
  
  // 计算状态
  const status = getClassroomStatus(startDate, endDate);
  
  // 计算学期
  const semester = classroom.semester || getSemester(startDate);
  
  // 统一字段名
  return {
    ...classroom,
    status,
    semester,
    teacherName: classroom.teacher_name || classroom.teacherName || classroom.teacher || '',
    studentCount: classroom.student_count || classroom.studentCount || classroom.students || 0,
    startDate: startDate,
    endDate: endDate,
    progress: classroom.progress || 0,
    experiment_count: classroom.experiment_count || 0
  };
}

/**
 * 对课堂列表进行分组
 * @param classrooms 课堂列表
 * @returns 分组后的课堂列表
 */
export function groupClassrooms(classrooms: Classroom[]): {
  learning: Classroom[];
  upcoming: Classroom[];
  completed: Classroom[];
} {
  const processed = classrooms.map(processClassroom);
  
  return {
    learning: processed.filter(c => c.status === 'learning'),
    upcoming: processed.filter(c => c.status === 'upcoming'),
    completed: processed.filter(c => c.status === 'completed')
  };
}