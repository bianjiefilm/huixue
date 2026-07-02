import type { CourseResource, MicroCourse, Tag, Classroom, ClassroomCourseDetail, Homework, HomeworkAttachment } from '../types/course';
import { get, post } from '../utils/request';
import { materialList, microList } from './cmaterial';

// 获取课程教材列表 - 调用专门的courses API，只返回courses表记录（完整教学课程）
export async function getCourseResources(keyword?: string, selectedTags?: string[]): Promise<CourseResource[]> {
  try {
    // 调用专门的courses API，返回courses表记录（完整教学课程）
    const response = await get('/api/v1/courses', {
      limit: 100,
      page: 1,
      keyword: keyword || undefined
    });

    const courses = response.data?.list || [];

    // Convert API response to CourseResource format
    return courses.map((course: any) => ({
      id: course.id.toString(),
      title: course.title,
      description: course.description,
      cover: course.cover_url,
      teacher: course.author || '',
      university: course.publisher || '',
      tags: Array.isArray(course.categories) ? course.categories :
            (course.categories ? course.categories.split(',') : []),
      chapters: course.chapters || 0,
      experiments: course.experiments || 0,
      duration: course.duration || '0小时',
      level: course.difficulty || 'beginner',
      rating: course.rating || 4.5,
      students: course.students || 0
    }));
  } catch (error) {
    console.error('Error fetching course resources:', error);
    return [];
  }
}

// 获取微型实验课程列表 - 只返回practices表的数据
export async function getMicroCourses(keyword?: string, direction?: string, category?: string, level?: string): Promise<MicroCourse[]> {
  try {
    // 直接调用 /api/v1/practices API
    const params: any = {
      limit: 100,
      page: 1,
    };

    // Add filter parameters if provided
    if (keyword && keyword.trim() !== '') {
      params.keyword = keyword;
    }

    if (direction && direction.trim() !== '') {
      params.direction = direction;
    }

    if (category && category.trim() !== '') {
      params.category = category;
    }

    if (level && level.trim() !== '') {
      // 转换中文难度为英文
      const levelMap: { [key: string]: string } = {
        '初级': 'beginner',
        '中级': 'intermediate',
        '高级': 'advanced'
      };
      params.difficulty = levelMap[level] || level;
    }

    const response = await get('/api/v1/practices', params);

    const practices = response.data?.list || response?.list || [];

    // Convert API response to MicroCourse format
    return practices.map((practice: any) => ({
      id: practice.id.toString(),
      title: practice.title,
      description: practice.description,
      cover: practice.cover_url,
      direction: practice.direction,
      category: practice.category,
      level: practice.difficulty === 'beginner' ? '初级' :
             practice.difficulty === 'intermediate' ? '中级' :
             practice.difficulty === 'advanced' ? '高级' : '初级',
      type: practice.category || '实践',
      difficulty: practice.difficulty,
      coin: practice.coin || 0,
      tasks: practice.task_count || 0,
      stage_count: practice.stage_count || practice.task_count || 0,
      card_count: practice.task_count || 0,
      popularity: practice.popularity || 0,
      views: practice.views || 0,
      rating: practice.rating || 4.5,
      duration: practice.duration || '2小时'
    }));
  } catch (error) {
    console.error('Error fetching micro courses:', error);
    return [];
  }
}

// 获取实践的关卡列表
export async function getPracticeTasks(practiceId: string | number, userId?: number) {
  try {
    const url = userId 
      ? `/api/v1/practices/${practiceId}/tasks?user_id=${userId}`
      : `/api/v1/practices/${practiceId}/tasks`;
    const response = await get(url);
    return response;
  } catch (error) {
    console.error('Error fetching practice tasks:', error);
    return { data: { list: [] } };
  }
}

// 解析 categories 字段（可能是JSON字符串、数组或逗号分隔字符串）
function parseCategories(categories: any): string[] {
  if (!categories) return [];
  if (Array.isArray(categories)) return categories;
  if (typeof categories === 'string') {
    // 尝试解析JSON格式 (如 '["区块链"]')
    try {
      const parsed = JSON.parse(categories);
      return Array.isArray(parsed) ? parsed : [categories];
    } catch {
      // 不是JSON，尝试逗号分隔
      return categories.split(',').map((s: string) => s.trim()).filter(Boolean);
    }
  }
  return [];
}

// 获取标签列表
export async function getTags(): Promise<Tag[]> {
  try {
    const response = await materialList({ limit: 100, page: 1 });
    // 处理两种可能的响应格式
    const courses = response?.data?.list || response?.list || [];

    // Extract unique tags from categories and direction
    const allTags = new Set<string>();
    courses.forEach((course: any) => {
      // 从 categories 提取标签（正确解析JSON字符串）
      const categoryTags = parseCategories(course.categories);
      categoryTags.forEach((tag: string) => {
        const trimmed = tag.trim();
        if (trimmed) allTags.add(trimmed);
      });
      // 从 direction 提取标签
      if (course.direction) {
        allTags.add(course.direction.trim());
      }
    });

    // Convert to Tag format
    const tags: Tag[] = Array.from(allTags).map((name, index) => ({
      id: (index + 1).toString(),
      name: name
    }));

    return tags;
  } catch (error) {
    console.error('Error fetching tags:', error);
    return [];
  }
}

// 根据ID获取课程详情
export async function getCourseById(id: string): Promise<CourseResource | null> {
  try {
    const response = await get(`/api/v1/course-materials/${id}`);
    return response.data;
  } catch (error) {
    console.error('获取课程详情失败:', error);
    return null;
  }
}

// 根据ID获取微课详情
export async function getMicroCourseById(id: string): Promise<MicroCourse | null> {
  try {
    const response = await get(`/api/v1/practices/${id}`);
    return response.data;
  } catch (error) {
    console.error('获取微课详情失败:', error);
    return null;
  }
}

// 获取所有微型实验方向
export async function getMicroDirections(): Promise<string[]> {
  try {
    const response = await microList({ limit: 100, page: 1 });
    const practices = response.list || [];
    
    // Extract unique directions
    const directions = Array.from(new Set(
      practices.map((practice: any) => practice.direction).filter(Boolean)
    )) as string[];
    
    return directions;
  } catch (error) {
    console.error('Error fetching micro directions:', error);
    return [];
  }
}

// 获取所有微型实验分类
export async function getMicroCategories(): Promise<string[]> {
  try {
    const response = await microList({ limit: 100, page: 1 });
    const practices = response.list || [];
    
    // Extract unique categories
    const categories = Array.from(new Set(
      practices.map((practice: any) => practice.category).filter(Boolean)
    )) as string[];
    
    return categories;
  } catch (error) {
    console.error('Error fetching micro categories:', error);
    return [];
  }
}

// 获取课堂列表
export async function getClassrooms(): Promise<Classroom[]> {
  try {
    const response = await get('/api/v1/my-classrooms');
    return response.data.ongoing.concat(response.data.upcoming, response.data.ended);
  } catch (error) {
    console.error('获取课堂列表失败:', error);
    return [];
  }
}

/**
 * 创建新课堂
 * @param classroom 课堂信息
 * @returns 创建后的课堂信息
 */
export async function createClassroom(classroom: {
  name: string;
  credits: number;
  startDate: string;
  endDate: string;
  teacherId: string;
  teacherName: string;
}): Promise<Classroom> {
  try {
    const response = await post('/api/v1/classrooms', {
      name: classroom.name,
      credits: classroom.credits,
      start_date: classroom.startDate,
      end_date: classroom.endDate,
      teacher_id: classroom.teacherId
    });
    
    return response.data;
  } catch (error) {
    console.error('创建课堂失败:', error);
    throw error;
  }
}

// 获取推荐课程
export async function getRecommendedMicroCourses(currentId: string, count: number = 4): Promise<MicroCourse[]> {
  try {
    const response = await get('/api/v1/practices/recommended', {
      exclude_id: currentId,
      limit: count
    });
    
    return response.data.list || [];
  } catch (error) {
    console.error('获取推荐课程失败:', error);
    return [];
  }
}

// 获取课堂中的课程详情（教师视角）
export async function getClassroomCourseDetailById(classroomId: string, courseId: string, teacherId?: string | number): Promise<ClassroomCourseDetail> {
  try {
    const response = await get(`/api/v1/courses/${courseId}/detail`, {
      classroom_id: classroomId,
      user_id: teacherId || 0,
      user_role: 'teacher'
    });

    // 将 banner 中的属性展开到顶层，以匹配前端模板期望的结构
    const data = response.data;
    if (data && data.banner) {
      // 确保classroom对象有有效的id和name
      const classroomData = data.banner.classroom || {};
      const safeClassroom = {
        id: classroomData.id || classroomId ? parseInt(classroomId) : 0,
        name: classroomData.name || '未知课堂'
      };

      return {
        id: data.banner.id,
        name: data.banner.title,
        status: data.banner.status?.toLowerCase() || 'unpublished',
        coins: data.banner.coins || 0,
        classroom: safeClassroom,
        difficulty: data.banner.difficulty || 3,
        startDate: data.banner.start_date,
        endDate: data.banner.end_date,
        remainingTime: data.banner.remaining_time,
        learningCount: data.banner.learning_count || 0,
        completedCount: data.banner.completed_count || 0,
        notStartedCount: data.banner.not_started_count || 0,
        courseType: data.banner.course_type,
        tasks: data.tasks || [],
        skills: data.skills || [],
        isStudentView: false,
        ...data
      };
    }

    return data;
  } catch (error) {
    console.error('获取课程详情失败:', error);
    throw error;
  }
}

// 获取学生视图的课程详情（增加学生学习情况）
export async function getStudentClassroomCourseDetailById(classroomId: string, courseId: string, studentId: string): Promise<ClassroomCourseDetail> {
  try {
    const response = await get(`/api/v1/courses/${courseId}/detail`, {
      classroom_id: classroomId,
      user_id: studentId,
      user_role: 'student'
    });

    // 将 banner 中的属性展开到顶层，以匹配前端模板期望的结构
    const data = response.data;
    if (data && data.banner) {
      // 转换 tasks 字段名以匹配前端模板期望
      const transformedTasks = (data.tasks || []).map((task: any) => {
        // 解析 skills：后端返回 JSON 字符串或数组
        let parsedSkills = task.skills || [];
        if (typeof parsedSkills === 'string') {
          try { parsedSkills = JSON.parse(parsedSkills); } catch { parsedSkills = []; }
        }
        return {
          ...task,
          completed: task.is_completed,  // 映射 is_completed -> completed
          type: task.task_type?.toLowerCase() || 'practice',
          skills: parsedSkills,
          coins: task.coin || 0,  // 映射 coin -> coins
        };
      });

      // 转换 skills 字段名以匹配前端模板期望
      const transformedSkills = (data.skills || []).map((skill: any) => ({
        id: skill.id || skill.skill_name,
        name: skill.skill_name || skill.name,  // 映射 skill_name -> name
        isLighted: skill.is_unlocked || skill.isLighted || false,  // 映射 is_unlocked -> isLighted
        relatedTasks: skill.related_tasks || []
      }));

      // 计算学生进度
      const studentProgress = data.learning_stats ? {
        completedTaskCount: data.learning_stats.completed_tasks || 0,
        totalTaskCount: data.learning_stats.total_tasks || 0,
        completionRate: data.learning_stats.progress_rate || 0,
        earnedCoins: data.learning_stats.earned_coins || 0
      } : undefined;

      // 确保classroom对象有有效的id和name
      const classroomData = data.banner.classroom || {};
      const safeClassroom = {
        id: classroomData.id || classroomId ? parseInt(classroomId) : 0,
        name: classroomData.name || '未知课堂'
      };

      // 注意：...data放在前面，后面的属性会覆盖data中同名属性
      return {
        ...data,
        id: data.banner.id,
        name: data.banner.title,
        status: data.banner.status?.toLowerCase() || 'unpublished',
        coins: data.banner.coin || 0,
        classroom: safeClassroom,
        difficulty: data.banner.difficulty || 3,
        startDate: data.banner.start_date,
        endDate: data.banner.end_date,
        remainingTime: data.banner.remaining_time,
        learningCount: data.banner.student_stats?.learning || 0,
        completedCount: data.banner.student_stats?.completed || 0,
        notStartedCount: data.banner.student_stats?.not_started || 0,
        courseType: data.banner.course_type,
        tasks: transformedTasks,
        skills: transformedSkills,
        studentProgress: studentProgress,
        isStudentView: true
      };
    }

    return data;
  } catch (error) {
    console.error('获取学生课程详情失败:', error);
    throw error;
  }
}

/**
 * 获取学生视角的课程详情
 */
export async function fetchStudentClassroomCourseDetail(classroomId: string, courseId: string, studentId: string): Promise<ClassroomCourseDetail> {
  // 直接调用已经优化过的函数
  return getStudentClassroomCourseDetailById(classroomId, courseId, studentId);
}

/**
 * 获取课程详情
 */
export async function getCourseDetail(courseId: string): Promise<any> {
  try {
    const response = await get(`/api/v1/courses/${courseId}`);
    // request.ts的响应拦截器已经返回了data.data，所以这里直接返回response即可
    return response;
  } catch (error) {
    console.error('获取课程详情失败:', error);
    throw error;
  }
}

/**
 * 获取实训项目详情
 */
export async function fetchTrainingCourseDetail(classroomId: string, courseId: string, studentId?: string): Promise<ClassroomCourseDetail> {
  try {
    const params: any = {
      classroom_id: classroomId,
      user_role: studentId ? 'student' : 'teacher'
    };
    
    if (studentId) {
      params.user_id = studentId;
    }
    
    const response = await get(`/api/v1/courses/${courseId}/detail`, params);
    return response.data;
  } catch (error) {
    console.error('获取实训项目详情失败', error);
    throw error;
  }
}

/**
 * 获取学生作业列表
 * @param classroomId 课堂ID
 * @param courseId 课程ID
 * @param studentId 学生ID
 */
export async function getStudentHomeworks(classroomId: string, courseId: string, studentId: string): Promise<Homework[]> {
  try {
    // 先获取课堂课程ID
    const classroomCourseResponse = await get(`/api/v1/classrooms/${classroomId}/courses`, {
      status: 'all'
    });
    
    const course = classroomCourseResponse.data.list.find((c: any) => c.course_id.toString() === courseId);
    if (!course) {
      throw new Error('课程不存在');
    }
    
    const response = await get(`/api/v1/classroom-courses/${course.id}/my-assignment`, {
      student_id: studentId
    });
    
    return response.data;
  } catch (error) {
    console.error('获取学生作业列表失败', error);
    throw error;
  }
}

/**
 * 提交作业
 * @param classroomId 课堂ID
 * @param courseId 课程ID
 * @param homeworkId 作业ID
 * @param studentId 学生ID
 * @param attachments 附件列表
 */
export async function submitHomework(
  classroomId: string, 
  courseId: string, 
  homeworkId: string, 
  studentId: string, 
  attachments: HomeworkAttachment[]
): Promise<Homework> {
  try {
    // 先获取课堂课程ID
    const classroomCourseResponse = await get(`/api/v1/classrooms/${classroomId}/courses`, {
      status: 'all'
    });
    
    const course = classroomCourseResponse.data.list.find((c: any) => c.course_id.toString() === courseId);
    if (!course) {
      throw new Error('课程不存在');
    }
    
    const response = await post(`/api/v1/classroom-courses/${course.id}/submit-assignment`, {
      student_id: studentId,
      homework_id: homeworkId,
      attachments
    });
    
    return response.data;
  } catch (error) {
    console.error('提交作业失败', error);
    throw error;
  }
}

/**
 * 获取作业详情
 * @param classroomId 课堂ID
 * @param courseId 课程ID
 * @param homeworkId 作业ID
 * @param studentId 学生ID
 */
export async function getHomeworkDetail(
  classroomId: string, 
  courseId: string, 
  homeworkId: string, 
  studentId: string
): Promise<Homework> {
  try {
    // 先获取课堂课程ID
    const classroomCourseResponse = await get(`/api/v1/classrooms/${classroomId}/courses`, {
      status: 'all'
    });
    
    const course = classroomCourseResponse.data.list.find((c: any) => c.course_id.toString() === courseId);
    if (!course) {
      throw new Error('课程不存在');
    }
    
    const response = await get(`/api/v1/classroom-courses/${course.id}/my-assignment`, {
      student_id: studentId,
      homework_id: homeworkId
    });
    
    return response.data;
  } catch (error) {
    console.error('获取作业详情失败', error);
    throw error;
  }
}

/**
 * 获取实训项目列表
 */
export async function getTrainingProjects(params?: {
  page?: number;
  page_size?: number;
  keyword?: string;
  direction?: string;
  category?: string;
  difficulty?: string;
}): Promise<MicroCourse[]> {
  try {
    const response = await get('/api/v1/practices', params);

    const practices = response.data?.list || [];
    // 过滤出实训项目（根据实际情况，可能需要后端API支持）
    // 这里先返回所有practices，实际应用中可能需要根据practice_type或其他字段过滤
    return practices.map((practice: any) => ({
      id: practice.id.toString(),
      title: practice.title,
      description: practice.description,
      cover: practice.cover_url,
      direction: practice.direction,
      category: practice.category,
      level: practice.difficulty === 'beginner' ? '初级' :
             practice.difficulty === 'intermediate' ? '中级' :
             practice.difficulty === 'advanced' ? '高级' : '初级',
      type: practice.category || '实训项目',
      difficulty: practice.difficulty,
      coin: practice.coin || 0,
      tasks: practice.task_count || 0,
      popularity: practice.popularity || 0,
      views: practice.views || 0,
      rating: practice.rating || 4.5,
      duration: practice.duration || practice.estimated_duration + '小时' || '2小时'
    }));
  } catch (error) {
    console.error('获取实训项目列表失败', error);
    throw error;
  }
}

/**
 * 获取实训项目详情
 */
export async function getTrainingProjectDetail(id: string): Promise<MicroCourse> {
  try {
    const response = await get(`/api/v1/practices/${id}`);

    const practice = response.data?.data || response.data;
    if (!practice) {
      throw new Error('实训项目不存在');
    }

    return {
      id: practice.id.toString(),
      title: practice.title,
      description: practice.description,
      cover: practice.cover_url,
      direction: practice.direction,
      category: practice.category,
      level: practice.difficulty === 'beginner' ? '初级' :
             practice.difficulty === 'intermediate' ? '中级' :
             practice.difficulty === 'advanced' ? '高级' : '初级',
      type: practice.category || '实训项目',
      difficulty: practice.difficulty,
      coin: practice.coin || 0,
      tasks: practice.task_count || 0,
      popularity: practice.popularity || 0,
      views: practice.views || 0,
      rating: practice.rating || 4.5,
      duration: practice.duration || practice.estimated_duration + '小时' || '2小时'
    };
  } catch (error) {
    console.error('获取实训项目详情失败', error);
    throw error;
  }
} 