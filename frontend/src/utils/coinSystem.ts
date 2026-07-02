import type { ClassroomCourseTask } from '@/types/course'

// 金币奖励配置
export const COIN_REWARDS = {
  TASK_COMPLETION: {
    judge: 5,      // 判断题
    choice: 8,     // 选择题
    practice: 15   // 实践题
  },
  DIFFICULTY_MULTIPLIER: {
    beginner: 1.0,     // 初级
    intermediate: 1.2, // 中级
    advanced: 1.5      // 高级
  },
  FIRST_TIME_BONUS: 2, // 首次完成奖励
  PERFECT_SCORE_BONUS: 3 // 满分奖励
} as const

// 金币奖励计算结果
export interface CoinRewardResult {
  baseCoins: number
  difficultyMultiplier: number
  firstTimeBonus: number
  perfectScoreBonus: number
  totalCoins: number
  breakdown: string[]
}

// 计算任务完成的金币奖励
export function calculateTaskReward(
  task: ClassroomCourseTask,
  isFirstTime: boolean = true,
  score: number = 100
): CoinRewardResult {
  const breakdown: string[] = []

  // 基础金币奖励
  const baseCoins = COIN_REWARDS.TASK_COMPLETION[task.type] || 10
  breakdown.push(`基础奖励: ${baseCoins}金币 (${task.type})`)

  // 难度倍数
  const difficultyMultiplier = COIN_REWARDS.DIFFICULTY_MULTIPLIER[task.difficulty] || 1.0
  const difficultyBonus = Math.round(baseCoins * (difficultyMultiplier - 1.0))
  if (difficultyBonus > 0) {
    breakdown.push(`难度奖励: +${difficultyBonus}金币 (${task.difficulty})`)
  }

  // 首次完成奖励
  let firstTimeBonus = 0
  if (isFirstTime) {
    firstTimeBonus = COIN_REWARDS.FIRST_TIME_BONUS
    breakdown.push(`首次完成: +${firstTimeBonus}金币`)
  }

  // 满分奖励
  let perfectScoreBonus = 0
  if (score === 100) {
    perfectScoreBonus = COIN_REWARDS.PERFECT_SCORE_BONUS
    breakdown.push(`满分奖励: +${perfectScoreBonus}金币`)
  }

  // 总金币数
  const totalCoins = baseCoins + difficultyBonus + firstTimeBonus + perfectScoreBonus

  return {
    baseCoins,
    difficultyMultiplier,
    firstTimeBonus,
    perfectScoreBonus,
    totalCoins,
    breakdown
  }
}

// 计算课程总金币奖励
export function calculateCourseTotalCoins(tasks: ClassroomCourseTask[]): number {
  return tasks.reduce((total, task) => {
    const reward = calculateTaskReward(task, true, 100)
    return total + reward.totalCoins
  }, 0)
}

// 金币变动记录类型
export interface CoinTransaction {
  id: string
  userId: string
  type: 'earn' | 'spend'
  amount: number
  reason: string
  taskId?: string
  courseId?: string
  classroomId?: string
  createdAt: string
  details: CoinRewardResult
}

// 模拟金币发放（实际应该调用后端API）
export async function awardCoins(
  userId: string,
  rewardResult: CoinRewardResult,
  taskId: string,
  courseId: string,
  classroomId: string
): Promise<boolean> {
  try {
    // 模拟API调用延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    // 创建金币交易记录
    const transaction: CoinTransaction = {
      id: `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      userId,
      type: 'earn',
      amount: rewardResult.totalCoins,
      reason: `完成任务奖励`,
      taskId,
      courseId,
      classroomId,
      createdAt: new Date().toISOString(),
      details: rewardResult
    }

    // 这里应该调用后端API保存交易记录
    console.log('金币奖励发放:', transaction)

    // 模拟成功率95%
    if (Math.random() > 0.05) {
      return true
    } else {
      throw new Error('金币发放失败')
    }
  } catch (error) {
    console.error('金币奖励发放失败:', error)
    return false
  }
}

// 检查用户是否已完成过该任务（用于判断是否给予首次奖励）
export function hasUserCompletedTask(userId: string, taskId: string): boolean {
  // 这里应该查询用户的任务完成历史
  // 暂时使用localStorage模拟
  const completedTasks = JSON.parse(localStorage.getItem(`completed_tasks_${userId}`) || '[]')
  return completedTasks.includes(taskId)
}

// 记录用户完成的任务
export function recordTaskCompletion(userId: string, taskId: string): void {
  const completedTasks = JSON.parse(localStorage.getItem(`completed_tasks_${userId}`) || '[]')
  if (!completedTasks.includes(taskId)) {
    completedTasks.push(taskId)
    localStorage.setItem(`completed_tasks_${userId}`, JSON.stringify(completedTasks))
  }
}

// 获取用户的金币余额
export function getUserCoinBalance(userId: string): number {
  // 这里应该调用后端API获取用户的金币余额
  // 暂时使用localStorage模拟
  return parseInt(localStorage.getItem(`coin_balance_${userId}`) || '0')
}

// 更新用户的金币余额
export function updateUserCoinBalance(userId: string, amount: number): number {
  const currentBalance = getUserCoinBalance(userId)
  const newBalance = Math.max(0, currentBalance + amount)
  localStorage.setItem(`coin_balance_${userId}`, newBalance.toString())
  return newBalance
}

// 获取用户的金币交易历史
export function getUserCoinHistory(userId: string): CoinTransaction[] {
  // 这里应该调用后端API获取交易历史
  // 暂时使用localStorage模拟
  return JSON.parse(localStorage.getItem(`coin_history_${userId}`) || '[]')
}

// 添加金币交易记录
export function addCoinTransaction(transaction: CoinTransaction): void {
  const history = getUserCoinHistory(transaction.userId)
  history.unshift(transaction)
  // 只保留最近100条记录
  if (history.length > 100) {
    history.splice(100)
  }
  localStorage.setItem(`coin_history_${transaction.userId}`, JSON.stringify(history))
}

// 完整的金币奖励流程
export async function processTaskReward(
  userId: string,
  task: ClassroomCourseTask,
  score: number,
  courseId: string,
  classroomId: string
): Promise<{
  success: boolean
  rewardResult: CoinRewardResult
  newBalance: number
  error?: string
}> {
  try {
    // 检查是否首次完成
    const isFirstTime = !hasUserCompletedTask(userId, task.id)

    // 计算奖励
    const rewardResult = calculateTaskReward(task, isFirstTime, score)

    // 发放金币
    const success = await awardCoins(userId, rewardResult, task.id, courseId, classroomId)

    if (success) {
      // 更新余额
      const newBalance = updateUserCoinBalance(userId, rewardResult.totalCoins)

      // 记录完成的任务
      recordTaskCompletion(userId, task.id)

      // 添加交易记录
      const transaction: CoinTransaction = {
        id: `txn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        userId,
        type: 'earn',
        amount: rewardResult.totalCoins,
        reason: `完成任务: ${task.title}`,
        taskId: task.id,
        courseId,
        classroomId,
        createdAt: new Date().toISOString(),
        details: rewardResult
      }
      addCoinTransaction(transaction)

      return {
        success: true,
        rewardResult,
        newBalance
      }
    } else {
      return {
        success: false,
        rewardResult,
        newBalance: getUserCoinBalance(userId),
        error: '金币发放失败，请稍后重试'
      }
    }
  } catch (error) {
    console.error('处理任务奖励失败:', error)
    return {
      success: false,
      rewardResult: calculateTaskReward(task, true, score),
      newBalance: getUserCoinBalance(userId),
      error: '系统错误，请联系管理员'
    }
  }
}

