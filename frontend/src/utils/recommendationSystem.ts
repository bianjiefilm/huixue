// 推荐实践系统

export interface CourseItem {
  id: string
  title: string
  type?: string
  difficulty?: string
  direction?: string
  tags?: string[]
  skills?: string[]
  industry?: string
  category?: string
}

export interface RecommendationResult {
  course: CourseItem
  score: number
  reasons: string[]
}

// 计算两门课程的相似度分数
function calculateSimilarityScore(courseA: CourseItem, courseB: CourseItem): { score: number, reasons: string[] } {
  let score = 0
  const reasons: string[] = []
  const maxScore = 100

  // 1. 方向匹配 (30分)
  if (courseA.direction && courseB.direction && courseA.direction === courseB.direction) {
    score += 30
    reasons.push(`相同方向: ${courseA.direction}`)
  }

  // 2. 难度匹配 (20分)
  if (courseA.difficulty && courseB.difficulty && courseA.difficulty === courseB.difficulty) {
    score += 20
    reasons.push(`相同难度: ${courseA.difficulty}`)
  }

  // 3. 标签匹配 (25分)
  if (courseA.tags && courseB.tags) {
    const commonTags = courseA.tags.filter(tag => courseB.tags!.includes(tag))
    if (commonTags.length > 0) {
      const tagScore = Math.min(commonTags.length * 5, 25)
      score += tagScore
      reasons.push(`共同标签: ${commonTags.slice(0, 3).join(', ')}`)
    }
  }

  // 4. 技能匹配 (15分)
  if (courseA.skills && courseB.skills) {
    const commonSkills = courseA.skills.filter(skill => courseB.skills!.includes(skill))
    if (commonSkills.length > 0) {
      const skillScore = Math.min(commonSkills.length * 3, 15)
      score += skillScore
      reasons.push(`共同技能: ${commonSkills.slice(0, 2).join(', ')}`)
    }
  }

  // 5. 类型匹配 (5分)
  if (courseA.type && courseB.type && courseA.type === courseB.type) {
    score += 5
    reasons.push(`相同类型: ${courseA.type}`)
  }

  // 6. 行业/分类匹配 (5分)
  if (courseA.industry && courseB.industry && courseA.industry === courseB.industry) {
    score += 5
    reasons.push(`相同行业: ${courseA.industry}`)
  }

  // 确保分数不超过最大值
  score = Math.min(score, maxScore)

  return { score, reasons }
}

// 获取推荐课程列表
export function getRecommendedCourses(
  currentCourse: CourseItem,
  allCourses: CourseItem[],
  options: {
    maxRecommendations?: number
    minScore?: number
    excludeCurrent?: boolean
  } = {}
): RecommendationResult[] {
  const {
    maxRecommendations = 5,
    minScore = 20,
    excludeCurrent = true
  } = options

  // 过滤掉当前课程
  let candidateCourses = allCourses
  if (excludeCurrent) {
    candidateCourses = allCourses.filter(course => course.id !== currentCourse.id)
  }

  // 计算相似度并排序
  const recommendations: RecommendationResult[] = candidateCourses
    .map(course => {
      const { score, reasons } = calculateSimilarityScore(currentCourse, course)
      return {
        course,
        score,
        reasons
      }
    })
    .filter(result => result.score >= minScore)
    .sort((a, b) => b.score - a.score)
    .slice(0, maxRecommendations)

  return recommendations
}

// 基于用户学习历史的推荐
export function getPersonalizedRecommendations(
  userHistory: CourseItem[],
  allCourses: CourseItem[],
  options: {
    maxRecommendations?: number
    weightRecent?: number
  } = {}
): RecommendationResult[] {
  const { maxRecommendations = 5, weightRecent = 0.7 } = options

  if (userHistory.length === 0) {
    // 如果没有历史记录，返回热门推荐
    return getPopularRecommendations(allCourses, maxRecommendations)
  }

  // 计算用户偏好向量
  const userPreferences = calculateUserPreferences(userHistory)

  // 计算每门课程的推荐分数
  const recommendations: RecommendationResult[] = allCourses
    .filter(course => !userHistory.some(history => history.id === course.id))
    .map(course => {
      const score = calculatePersonalizedScore(course, userPreferences, userHistory)
      return {
        course,
        score,
        reasons: generatePersonalizedReasons(course, userPreferences)
      }
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, maxRecommendations)

  return recommendations
}

// 计算用户偏好
function calculateUserPreferences(userHistory: CourseItem[]): {
  directions: Record<string, number>
  difficulties: Record<string, number>
  tags: Record<string, number>
  skills: Record<string, number>
  types: Record<string, number>
  industries: Record<string, number>
} {
  const preferences = {
    directions: {} as Record<string, number>,
    difficulties: {} as Record<string, number>,
    tags: {} as Record<string, number>,
    skills: {} as Record<string, number>,
    types: {} as Record<string, number>,
    industries: {} as Record<string, number>
  }

  userHistory.forEach(course => {
    // 方向偏好
    if (course.direction) {
      preferences.directions[course.direction] = (preferences.directions[course.direction] || 0) + 1
    }

    // 难度偏好
    if (course.difficulty) {
      preferences.difficulties[course.difficulty] = (preferences.difficulties[course.difficulty] || 0) + 1
    }

    // 类型偏好
    if (course.type) {
      preferences.types[course.type] = (preferences.types[course.type] || 0) + 1
    }

    // 行业偏好
    if (course.industry) {
      preferences.industries[course.industry] = (preferences.industries[course.industry] || 0) + 1
    }

    // 标签偏好
    if (course.tags) {
      course.tags.forEach(tag => {
        preferences.tags[tag] = (preferences.tags[tag] || 0) + 1
      })
    }

    // 技能偏好
    if (course.skills) {
      course.skills.forEach(skill => {
        preferences.skills[skill] = (preferences.skills[skill] || 0) + 1
      })
    }
  })

  return preferences
}

// 计算个性化推荐分数
function calculatePersonalizedScore(
  course: CourseItem,
  userPreferences: ReturnType<typeof calculateUserPreferences>,
  userHistory: CourseItem[]
): number {
  let score = 0

  // 方向匹配 (25分)
  if (course.direction && userPreferences.directions[course.direction]) {
    score += 25 * (userPreferences.directions[course.direction] / userHistory.length)
  }

  // 难度匹配 (20分)
  if (course.difficulty && userPreferences.difficulties[course.difficulty]) {
    score += 20 * (userPreferences.difficulties[course.difficulty] / userHistory.length)
  }

  // 类型匹配 (15分)
  if (course.type && userPreferences.types[course.type]) {
    score += 15 * (userPreferences.types[course.type] / userHistory.length)
  }

  // 行业匹配 (10分)
  if (course.industry && userPreferences.industries[course.industry]) {
    score += 10 * (userPreferences.industries[course.industry] / userHistory.length)
  }

  // 标签匹配 (20分)
  if (course.tags) {
    const tagMatches = course.tags.filter(tag => userPreferences.tags[tag]).length
    if (tagMatches > 0) {
      score += 20 * (tagMatches / course.tags.length)
    }
  }

  // 技能匹配 (10分)
  if (course.skills) {
    const skillMatches = course.skills.filter(skill => userPreferences.skills[skill]).length
    if (skillMatches > 0) {
      score += 10 * (skillMatches / course.skills.length)
    }
  }

  return Math.min(score, 100)
}

// 生成个性化推荐理由
function generatePersonalizedReasons(
  course: CourseItem,
  userPreferences: ReturnType<typeof calculateUserPreferences>
): string[] {
  const reasons: string[] = []

  if (course.direction && userPreferences.directions[course.direction]) {
    reasons.push(`你喜欢 ${course.direction} 方向的课程`)
  }

  if (course.difficulty && userPreferences.difficulties[course.difficulty]) {
    reasons.push(`符合你喜欢的 ${course.difficulty} 难度`)
  }

  if (course.type && userPreferences.types[course.type]) {
    reasons.push(`你经常学习的 ${course.type} 类型`)
  }

  if (course.tags) {
    const preferredTags = course.tags.filter(tag => userPreferences.tags[tag])
    if (preferredTags.length > 0) {
      reasons.push(`包含你感兴趣的标签: ${preferredTags.slice(0, 2).join(', ')}`)
    }
  }

  if (course.skills) {
    const preferredSkills = course.skills.filter(skill => userPreferences.skills[skill])
    if (preferredSkills.length > 0) {
      reasons.push(`涉及你擅长的技能: ${preferredSkills.slice(0, 2).join(', ')}`)
    }
  }

  return reasons.length > 0 ? reasons : ['基于你的学习偏好推荐']
}

// 获取热门推荐（当没有足够数据时使用）
function getPopularRecommendations(allCourses: CourseItem[], maxCount: number): RecommendationResult[] {
  // 简单地返回前N个课程作为热门推荐
  return allCourses.slice(0, maxCount).map(course => ({
    course,
    score: 80 + Math.random() * 20, // 随机80-100分
    reasons: ['热门推荐课程']
  }))
}

// 混合推荐算法（结合相似度和个性化）
export function getHybridRecommendations(
  currentCourse: CourseItem,
  userHistory: CourseItem[],
  allCourses: CourseItem[],
  options: {
    maxRecommendations?: number
    similarityWeight?: number
    personalizationWeight?: number
  } = {}
): RecommendationResult[] {
  const {
    maxRecommendations = 5,
    similarityWeight = 0.6,
    personalizationWeight = 0.4
  } = options

  // 获取相似度推荐
  const similarityRecommendations = getRecommendedCourses(currentCourse, allCourses, {
    maxRecommendations: maxRecommendations * 2,
    minScore: 10
  })

  // 获取个性化推荐
  const personalizedRecommendations = getPersonalizedRecommendations(userHistory, allCourses, {
    maxRecommendations: maxRecommendations * 2
  })

  // 合并推荐结果
  const allRecommendations = new Map<string, RecommendationResult>()

  // 添加相似度推荐
  similarityRecommendations.forEach(rec => {
    const weightedScore = rec.score * similarityWeight
    allRecommendations.set(rec.course.id, {
      ...rec,
      score: weightedScore
    })
  })

  // 添加个性化推荐，合并分数
  personalizedRecommendations.forEach(rec => {
    const existing = allRecommendations.get(rec.course.id)
    const newScore = rec.score * personalizationWeight

    if (existing) {
      // 合并理由和分数
      allRecommendations.set(rec.course.id, {
        course: rec.course,
        score: existing.score + newScore,
        reasons: [...new Set([...existing.reasons, ...rec.reasons])]
      })
    } else {
      allRecommendations.set(rec.course.id, {
        ...rec,
        score: newScore
      })
    }
  })

  // 排序并返回前N个
  return Array.from(allRecommendations.values())
    .sort((a, b) => b.score - a.score)
    .slice(0, maxRecommendations)
}

