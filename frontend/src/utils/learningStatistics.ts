import dayjs from 'dayjs'

// 学习统计数据类型
export interface LearningStatistics {
  // 基本统计
  totalStudyTime: number // 总学习时长（分钟）
  completedTasks: number // 已完成任务数
  totalTasks: number // 总任务数
  completionRate: number // 完成率（百分比）

  // 时间统计
  todayStudyTime: number // 今日学习时长（分钟）
  weekStudyTime: number // 本周学习时长（分钟）
  monthStudyTime: number // 本月学习时长（分钟）
  averageSessionTime: number // 平均会话时长（分钟）

  // 任务统计
  taskCompletionByType: Record<string, { completed: number; total: number }> // 按任务类型统计
  taskCompletionByDifficulty: Record<string, { completed: number; total: number }> // 按难度统计

  // 学习行为统计
  totalSessions: number // 总学习会话数
  longestSession: number // 最长学习会话（分钟）
  consistencyScore: number // 学习一致性得分（0-100）
  currentStreak: number // 当前连续学习天数

  // 成就统计
  totalCoins: number // 总获得金币
  perfectTaskCount: number // 满分任务数
  firstTimeCompletions: number // 首次完成任务数

  // 时间分布
  studyTimeByHour: number[] // 24小时学习时长分布
  studyTimeByWeekday: number[] // 每周学习时长分布

  // 最近活动
  recentActivities: LearningActivity[]
}

// 学习活动记录
export interface LearningActivity {
  id: string
  type: 'task_completion' | 'session_start' | 'session_end' | 'coin_earned' | 'skill_unlocked'
  description: string
  timestamp: string
  metadata?: Record<string, any>
}

// 学习会话记录
export interface LearningSession {
  id: string
  startTime: string
  endTime?: string
  duration?: number // 分钟
  taskId?: string
  courseId: string
  classroomId: string
}

// 统计数据更新频率
export enum StatisticsUpdateFrequency {
  REALTIME = 'realtime', // 实时更新（如进度、当前会话时长）
  HOURLY = 'hourly',    // 每小时更新（如今日统计）
  DAILY = 'daily',      // 每日更新（如周统计、月统计）
  WEEKLY = 'weekly',    // 每周更新（如学习一致性）
  MONTHLY = 'monthly'   // 每月更新（如长期趋势）
}

// 计算学习统计数据（基于真实课程详情数据）
export function calculateLearningStatistics(
  userId: string,
  courseId?: string,
  classroomId?: string,
  courseDetail?: any  // 传入课程详情数据以获取真实统计
): LearningStatistics {
  // 从课程详情中提取真实数据
  const tasks = courseDetail?.tasks || [];
  const studentProgress = courseDetail?.studentProgress || {};
  const skills = courseDetail?.skills || [];

  const completedTasks = tasks.filter((t: any) => t.completed).length;
  const totalTasks = tasks.length;
  const completionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 1000) / 10 : 0;

  // 计算已获得金币（累加已通关任务的 coins）
  const totalCoins = studentProgress.earnedCoins || tasks
    .filter((t: any) => t.completed)
    .reduce((sum: number, t: any) => sum + (t.coins || t.coin || 0), 0);

  // 按类型统计
  const taskCompletionByType: Record<string, { completed: number; total: number }> = {};
  tasks.forEach((t: any) => {
    const type = t.type || 'practice';
    if (!taskCompletionByType[type]) taskCompletionByType[type] = { completed: 0, total: 0 };
    taskCompletionByType[type].total++;
    if (t.completed) taskCompletionByType[type].completed++;
  });

  // 按难度统计
  const taskCompletionByDifficulty: Record<string, { completed: number; total: number }> = {};
  tasks.forEach((t: any) => {
    const diff = (t.difficulty || 'beginner').toLowerCase();
    if (!taskCompletionByDifficulty[diff]) taskCompletionByDifficulty[diff] = { completed: 0, total: 0 };
    taskCompletionByDifficulty[diff].total++;
    if (t.completed) taskCompletionByDifficulty[diff].completed++;
  });

  // 满分任务数
  const perfectTaskCount = tasks.filter((t: any) => t.completed && t.score === 100).length;

  // 从 localStorage 获取会话数据（真实行为数据）
  const sessions = courseId && classroomId
    ? getLearningSessions(courseId, classroomId)
    : [];
  const totalStudyTime = sessions.reduce((sum, s) => sum + (s.duration || 0), 0);
  const todayStart = dayjs().startOf('day');
  const todayStudyTime = sessions
    .filter(s => dayjs(s.startTime).isAfter(todayStart))
    .reduce((sum, s) => sum + (s.duration || 0), 0);
  const weekStart = dayjs().startOf('week');
  const weekStudyTime = sessions
    .filter(s => dayjs(s.startTime).isAfter(weekStart))
    .reduce((sum, s) => sum + (s.duration || 0), 0);
  const avgSession = sessions.length > 0
    ? Math.round(totalStudyTime / sessions.length)
    : 0;

  // 生成最近活动（基于已完成的任务）
  const recentActivities: LearningActivity[] = tasks
    .filter((t: any) => t.completed && t.completion_time)
    .sort((a: any, b: any) => new Date(b.completion_time).getTime() - new Date(a.completion_time).getTime())
    .slice(0, 5)
    .map((t: any, i: number) => ({
      id: `act_${i}`,
      type: 'task_completion' as const,
      description: `完成了任务：${t.title}`,
      timestamp: t.completion_time || dayjs().subtract(i * 30, 'minute').format(),
      metadata: { taskId: t.id, score: t.score }
    }));

  // 如果没有真实活动数据，生成通关相关活动
  if (recentActivities.length === 0 && completedTasks > 0) {
    tasks.filter((t: any) => t.completed).slice(0, 3).forEach((t: any, i: number) => {
      recentActivities.push({
        id: `act_${i}`,
        type: 'task_completion',
        description: `完成了关卡：${t.title}`,
        timestamp: dayjs().subtract(i * 30 + 10, 'minute').format(),
        metadata: { taskId: t.id }
      });
    });
  }

  return {
    totalStudyTime,
    completedTasks,
    totalTasks,
    completionRate,
    todayStudyTime,
    weekStudyTime,
    monthStudyTime: totalStudyTime,
    averageSessionTime: avgSession,
    taskCompletionByType,
    taskCompletionByDifficulty,
    totalSessions: sessions.length,
    longestSession: sessions.reduce((max, s) => Math.max(max, s.duration || 0), 0),
    consistencyScore: 0,
    currentStreak: 0,
    totalCoins,
    perfectTaskCount,
    firstTimeCompletions: completedTasks,
    studyTimeByHour: new Array(24).fill(0),
    studyTimeByWeekday: new Array(7).fill(0),
    recentActivities
  };
}

// 计算学习一致性得分
export function calculateConsistencyScore(studyDays: number[], totalDays: number): number {
  if (totalDays === 0) return 0;

  const studyDayCount = studyDays.filter(day => day > 0).length;
  const averageStudyTime = studyDays.reduce((sum, time) => sum + time, 0) / totalDays;

  // 一致性得分 = (学习天数占比 * 40) + (平均学习时长 * 0.1) + (连续学习奖励)
  let consistencyScore = (studyDayCount / totalDays) * 40;

  // 平均学习时长奖励（最高30分）
  consistencyScore += Math.min(averageStudyTime * 0.1, 30);

  // 连续学习奖励（最高30分）
  const currentStreak = calculateCurrentStreak(studyDays);
  consistencyScore += Math.min(currentStreak * 2, 30);

  return Math.min(Math.round(consistencyScore), 100);
}

// 计算当前连续学习天数
export function calculateCurrentStreak(studyDays: number[]): number {
  let streak = 0;
  for (let i = studyDays.length - 1; i >= 0; i--) {
    if (studyDays[i] > 0) {
      streak++;
    } else {
      break;
    }
  }
  return streak;
}

// 格式化学习时长显示
export function formatStudyTime(minutes: number): string {
  if (minutes < 60) {
    return `${minutes}分钟`;
  } else if (minutes < 1440) { // 24小时
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}小时${remainingMinutes}分钟` : `${hours}小时`;
  } else {
    const days = Math.floor(minutes / 1440);
    const remainingHours = Math.floor((minutes % 1440) / 60);
    return remainingHours > 0 ? `${days}天${remainingHours}小时` : `${days}天`;
  }
}

// 格式化统计数值显示
export function formatStatisticValue(value: number, type: 'time' | 'count' | 'rate' | 'score'): string {
  switch (type) {
    case 'time':
      return formatStudyTime(value);
    case 'rate':
      return `${value.toFixed(1)}%`;
    case 'score':
      return value.toString();
    case 'count':
    default:
      return value.toLocaleString();
  }
}

// 获取统计数据的更新频率
export function getStatisticsUpdateFrequency(statisticType: keyof LearningStatistics): StatisticsUpdateFrequency {
  // 实时更新的统计
  const realtimeStats: (keyof LearningStatistics)[] = [
    'completedTasks',
    'completionRate',
    'todayStudyTime',
    'recentActivities'
  ];

  // 每小时更新的统计
  const hourlyStats: (keyof LearningStatistics)[] = [
    'weekStudyTime'
  ];

  // 每日更新的统计
  const dailyStats: (keyof LearningStatistics)[] = [
    'monthStudyTime',
    'totalSessions',
    'studyTimeByHour',
    'consistencyScore',
    'currentStreak'
  ];

  // 每周更新的统计
  const weeklyStats: (keyof LearningStatistics)[] = [
    'studyTimeByWeekday'
  ];

  if (realtimeStats.includes(statisticType)) {
    return StatisticsUpdateFrequency.REALTIME;
  } else if (hourlyStats.includes(statisticType)) {
    return StatisticsUpdateFrequency.HOURLY;
  } else if (dailyStats.includes(statisticType)) {
    return StatisticsUpdateFrequency.DAILY;
  } else if (weeklyStats.includes(statisticType)) {
    return StatisticsUpdateFrequency.WEEKLY;
  } else {
    return StatisticsUpdateFrequency.MONTHLY;
  }
}

// 记录学习会话
export function recordLearningSession(session: Omit<LearningSession, 'id'>): string {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // 这里应该保存到后端或本地存储
  const sessions = getLearningSessions(session.courseId, session.classroomId);
  sessions.push({ ...session, id: sessionId });

  localStorage.setItem(`learning_sessions_${session.courseId}_${session.classroomId}`,
    JSON.stringify(sessions));

  return sessionId;
}

// 获取学习会话记录
export function getLearningSessions(courseId: string, classroomId: string): LearningSession[] {
  const key = `learning_sessions_${courseId}_${classroomId}`;
  return JSON.parse(localStorage.getItem(key) || '[]');
}

// 更新学习会话结束时间
export function endLearningSession(sessionId: string, courseId: string, classroomId: string): void {
  const sessions = getLearningSessions(courseId, classroomId);
  const session = sessions.find(s => s.id === sessionId);

  if (session && !session.endTime) {
    session.endTime = new Date().toISOString();
    session.duration = dayjs(session.endTime).diff(dayjs(session.startTime), 'minute');

    localStorage.setItem(`learning_sessions_${courseId}_${classroomId}`, JSON.stringify(sessions));
  }
}

// 计算课程的学习时长
export function calculateCourseStudyTime(courseId: string, classroomId: string): number {
  const sessions = getLearningSessions(courseId, classroomId);
  return sessions.reduce((total, session) => total + (session.duration || 0), 0);
}

// 获取今日学习时长
export function getTodayStudyTime(courseId?: string, classroomId?: string): number {
  const today = dayjs().startOf('day');
  const sessions = courseId && classroomId ?
    getLearningSessions(courseId, classroomId) :
    getAllLearningSessions();

  return sessions
    .filter(session => dayjs(session.startTime).isAfter(today))
    .reduce((total, session) => total + (session.duration || 0), 0);
}

// 获取所有学习会话（跨课程）
export function getAllLearningSessions(): LearningSession[] {
  // 这里应该从所有课程的会话中汇总
  // 暂时返回空数组
  return [];
}

// 生成学习报告
export function generateLearningReport(
  userId: string,
  courseId?: string,
  classroomId?: string,
  period: 'week' | 'month' | 'all' = 'all'
): {
  summary: string
  highlights: string[]
  recommendations: string[]
  statistics: Partial<LearningStatistics>
} {
  const stats = calculateLearningStatistics(userId, courseId, classroomId);

  let summary = '';
  const highlights: string[] = [];
  const recommendations: string[] = [];

  // 生成摘要
  if (period === 'all') {
    summary = `总共学习了${formatStudyTime(stats.totalStudyTime)}，完成了${stats.completedTasks}个任务，获得${stats.totalCoins}金币。`;
  } else {
    const periodTime = period === 'week' ? stats.weekStudyTime : stats.monthStudyTime;
    summary = `本${period === 'week' ? '周' : '月'}学习了${formatStudyTime(periodTime)}，保持了${stats.consistencyScore}分的学习一致性。`;
  }

  // 生成亮点
  if (stats.perfectTaskCount > 0) {
    highlights.push(`完成了${stats.perfectTaskCount}个满分任务，表现出色！`);
  }
  if (stats.currentStreak >= 7) {
    highlights.push(`连续学习${stats.currentStreak}天，学习习惯优秀！`);
  }
  if (stats.completionRate >= 80) {
    highlights.push(`任务完成率达到${stats.completionRate.toFixed(1)}%，学习进度良好！`);
  }

  // 生成建议
  if (stats.consistencyScore < 60) {
    recommendations.push('建议增加学习频率，建立更好的学习习惯。');
  }
  if (stats.averageSessionTime < 20) {
    recommendations.push('建议延长每次学习时长，深入理解知识内容。');
  }
  if (stats.completionRate < 70) {
    recommendations.push('建议加强薄弱环节的学习，提高任务完成质量。');
  }

  return {
    summary,
    highlights,
    recommendations,
    statistics: stats
  };
}

