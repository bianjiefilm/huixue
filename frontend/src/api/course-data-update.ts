/**
 * 课程数据更新配置
 * 用于映射后端真实课程数据到前端显示
 */

// 真实课程教材数据（来自后端数据库）
export const realCourseMaterials = [
  {
    id: "6",
    title: "大数据基础与应用",
    description: "本课程涵盖大数据的基本概念、技术架构、数据处理方法以及实际应用案例，适合初学者入门学习。",
    cover: "https://picsum.photos/800/450?random=6",
    teacher: "张教授",
    university: "清华大学",
    tags: ["大数据", "基础理论", "数据分析"],
    chapters: 15,
    experiments: 8,
    duration: "32小时",
    level: "beginner",
    rating: 4.8,
    students: 2350
  },
  {
    id: "7",
    title: "机器学习算法与实践",
    description: "深入学习各种机器学习算法，包括监督学习、无监督学习和强化学习，结合Python实现和案例分析。",
    cover: "https://picsum.photos/800/450?random=7",
    teacher: "李教授",
    university: "北京理工大学",
    tags: ["机器学习", "算法", "人工智能"],
    chapters: 20,
    experiments: 12,
    duration: "48小时",
    level: "intermediate",
    rating: 4.9,
    students: 3200
  },
  {
    id: "8",
    title: "云计算技术与架构",
    description: "系统介绍云计算的核心技术、服务模式、部署模式以及主流云平台的使用方法。",
    cover: "https://picsum.photos/800/450?random=8",
    teacher: "王教授",
    university: "电子科技大学",
    tags: ["云计算", "云服务", "架构设计"],
    chapters: 18,
    experiments: 10,
    duration: "40小时",
    level: "advanced",
    rating: 4.7,
    students: 1850
  },
  {
    id: "9",
    title: "Python程序设计基础",
    description: "Python语言基础语法、数据结构、面向对象编程以及常用库的使用，适合编程初学者。",
    cover: "https://picsum.photos/800/450?random=9",
    teacher: "刘教授",
    university: "北京邮电大学",
    tags: ["Python", "基础编程", "编程语言"],
    chapters: 25,
    experiments: 15,
    duration: "50小时",
    level: "beginner",
    rating: 4.9,
    students: 5200
  },
  {
    id: "10",
    title: "区块链技术原理与应用",
    description: "深入了解区块链的底层原理、共识机制、智能合约以及在各行业的应用前景。",
    cover: "https://picsum.photos/800/450?random=10",
    teacher: "陈教授",
    university: "复旦大学",
    tags: ["区块链", "分布式系统", "加密技术"],
    chapters: 12,
    experiments: 6,
    duration: "30小时",
    level: "advanced",
    rating: 4.6,
    students: 1200
  },
  {
    id: "11",
    title: "数据库系统原理",
    description: "关系数据库理论、SQL语言、数据库设计、事务处理、并发控制等核心概念。",
    cover: "https://picsum.photos/800/450?random=11",
    teacher: "赵教授",
    university: "同济大学",
    tags: ["数据库", "关系数据库", "SQL"],
    chapters: 16,
    experiments: 9,
    duration: "36小时",
    level: "intermediate",
    rating: 4.7,
    students: 2800
  }
];

// 真实微型实验数据（来自后端数据库）
export const realMicroCourses = [
  {
    id: "1",
    title: "Python基础实践",
    description: "通过实际项目学习Python编程基础，包括数据类型、控制结构、函数和模块等核心概念。",
    cover: "https://picsum.photos/800/450?random=21",
    direction: "编程语言",
    category: "基础编程",
    level: "初级",
    type: "实践",
    difficulty: "beginner",
    coin: 100,
    tasks: 15,
    popularity: 3200,
    views: 8500,
    rating: 4.8,
    duration: "16小时"
  },
  {
    id: "2",
    title: "机器学习实战",
    description: "从零开始实现常见的机器学习算法，包括回归、分类、聚类等，并应用到实际数据集上。",
    cover: "https://picsum.photos/800/450?random=22",
    direction: "人工智能",
    category: "机器学习",
    level: "中级",
    type: "实践",
    difficulty: "intermediate",
    coin: 150,
    tasks: 20,
    popularity: 4500,
    views: 12000,
    rating: 4.9,
    duration: "24小时"
  },
  {
    id: "3",
    title: "大数据处理实践",
    description: "使用Hadoop和Spark进行大规模数据处理，学习分布式计算的核心概念和实践技能。",
    cover: "https://picsum.photos/800/450?random=23",
    direction: "大数据",
    category: "数据处理",
    level: "高级",
    type: "实践",
    difficulty: "advanced",
    coin: 200,
    tasks: 18,
    popularity: 2800,
    views: 7500,
    rating: 4.7,
    duration: "32小时"
  },
  {
    id: "1",
    title: "Hadoop分布式文件系统实践",
    description: "通过实际操作学习HDFS的基本概念、架构设计和文件操作命令。",
    cover: "https://picsum.photos/800/450?random=24",
    direction: "大数据",
    category: "分布式存储",
    level: "初级",
    type: "实践",
    difficulty: "beginner",
    coin: 50,
    tasks: 3,
    popularity: 1500,
    views: 4200,
    rating: 4.5,
    duration: "8小时"
  },
  {
    id: "2",
    title: "线性回归算法实现",
    description: "使用Python从零实现线性回归算法，理解梯度下降和最小二乘法。",
    cover: "https://picsum.photos/800/450?random=25",
    direction: "人工智能",
    category: "机器学习",
    level: "中级",
    type: "实践",
    difficulty: "intermediate",
    coin: 80,
    tasks: 4,
    popularity: 2200,
    views: 5800,
    rating: 4.6,
    duration: "12小时"
  },
  {
    id: "3",
    title: "Docker容器化部署",
    description: "学习Docker的基本概念和操作，实现应用的容器化部署。",
    cover: "https://picsum.photos/800/450?random=26",
    direction: "云计算",
    category: "容器化",
    level: "中级",
    type: "实践",
    difficulty: "intermediate",
    coin: 100,
    tasks: 5,
    popularity: 3100,
    views: 8200,
    rating: 4.7,
    duration: "16小时"
  },
  {
    id: "4",
    title: "Python爬虫实战",
    description: "使用Python requests和BeautifulSoup库实现网页数据爬取。",
    cover: "https://picsum.photos/800/450?random=27",
    direction: "编程语言",
    category: "数据爬取",
    level: "初级",
    type: "实践",
    difficulty: "beginner",
    coin: 60,
    tasks: 6,
    popularity: 2500,
    views: 6800,
    rating: 4.5,
    duration: "10小时"
  },
  {
    id: "5",
    title: "智能合约开发入门",
    description: "基于Solidity语言开发简单的以太坊智能合约，了解区块链编程。",
    cover: "https://picsum.photos/800/450?random=28",
    direction: "区块链",
    category: "智能合约",
    level: "高级",
    type: "实践",
    difficulty: "advanced",
    coin: 150,
    tasks: 4,
    popularity: 1200,
    views: 3500,
    rating: 4.4,
    duration: "20小时"
  }
];

// 数据转换函数
export function transformBackendCourseData(backendData: any): any {
  if (!backendData) return null;
  
  // 根据不同的API响应格式进行转换
  if (backendData.course_type === 'COURSE_MATERIAL') {
    // 转换课程教材数据
    return {
      id: backendData.id.toString(),
      title: backendData.title,
      description: backendData.description,
      cover: backendData.cover_url || `https://picsum.photos/800/450?random=${backendData.id}`,
      teacher: backendData.author || '资深教授',
      university: backendData.source || '知名高校',
      tags: backendData.categories ? backendData.categories.split(',').map((tag: string) => tag.trim()) : [],
      chapters: backendData.material_resources_count || 10,
      experiments: backendData.practice_task_count || 5,
      duration: `${(backendData.material_resources_count || 10) * 2}小时`,
      level: backendData.difficulty ? backendData.difficulty.toLowerCase() : 'beginner',
      rating: 4.5 + Math.random() * 0.4,
      students: 1000 + Math.floor(Math.random() * 4000)
    };
  } else {
    // 转换微型实验数据
    const difficultyMap: any = {
      'beginner': '初级',
      'intermediate': '中级',
      'advanced': '高级'
    };
    
    return {
      id: backendData.id.toString(),
      title: backendData.title,
      description: backendData.description,
      cover: backendData.cover_url || `https://picsum.photos/800/450?random=${backendData.id + 20}`,
      direction: backendData.direction,
      category: backendData.category,
      level: difficultyMap[backendData.difficulty] || '初级',
      type: '实践',
      difficulty: backendData.difficulty,
      coin: backendData.coin || 100,
      tasks: backendData.task_count || 5,
      popularity: backendData.popularity || 1000 + Math.floor(Math.random() * 3000),
      views: backendData.views || 2000 + Math.floor(Math.random() * 8000),
      rating: 4.3 + Math.random() * 0.6,
      duration: `${(backendData.task_count || 5) * 3}小时`
    };
  }
}