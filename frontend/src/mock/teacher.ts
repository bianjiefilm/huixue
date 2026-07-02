import Mock from 'mockjs';
import type { MockMethod } from 'vite-plugin-mock';
import { getRandomId } from './utils';

// 教师接口定义
export interface Teacher {
  id: string;
  name: string;
  teacherId: string;
  gender: '男' | '女';
  avatar: string;
  department?: string;
  title?: string;  // 职称
  phone?: string;
  email?: string;
  status?: 'active' | 'inactive';
}

// 教师和课堂关系类型
export interface TeacherClassroomRelation {
  teacherId: string;
  classroomId: string;
  role: 'owner' | 'assistant';  // 主讲教师或助教
  joinTime: string;
}

// 生成随机头像URL
const generateAvatarUrl = () => {
  const avatarIds = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'];
  const id = Math.floor(Math.random() * avatarIds.length);
  return `/images/avatars/avatar${avatarIds[id]}.png`;
};

// 生成随机教师数据
const generateTeachers = (count: number = 30): Teacher[] => {
  const teachers: Teacher[] = [];
  
  const departments = [
    '计算机科学与技术学院',
    '软件学院',
    '信息科学与工程学院',
    '电子工程学院',
    '自动化学院',
    '数学学院',
    '物理学院'
  ];
  
  const titles = [
    '教授',
    '副教授',
    '讲师',
    '助教'
  ];
  
  for (let i = 0; i < count; i++) {
    const gender = Mock.Random.pick(['男', '女']);
    const firstName = gender === '男' 
      ? Mock.Random.pick(['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '郑', '孙', '马', '朱', '胡', '林', '郭', '何', '高', '罗']) 
      : Mock.Random.pick(['张', '王', '李', '赵', '刘', '陈', '杨', '黄', '周', '吴', '郑', '孙', '林', '徐', '何', '马', '朱', '胡', '郭', '梁']);
    
    const lastName = gender === '男'
      ? Mock.Random.pick(['伟', '强', '磊', '军', '杰', '涛', '超', '明', '勇', '波', '斌', '辉', '宇', '浩', '凯', '鹏', '健', '俊', '帆', '文', '宁', '博', '新', '志', '剑', '飞'])
      : Mock.Random.pick(['娜', '芳', '玲', '静', '婷', '洁', '雯', '燕', '娟', '文', '敏', '琳', '丽', '雪', '倩', '颖', '琴', '欣', '露', '佳', '悦', '莉', '璐', '凤', '红', '英']);
    
    // 生成真实姓名
    const name = firstName + lastName;
    
    // 生成教师号（T开头加6位数字）
    const teacherId = 'T' + Mock.Random.string('number', 6);
    
    // 部门和职称
    const department = Mock.Random.pick(departments);
    const title = Mock.Random.pick(titles);
    
    teachers.push({
      id: Mock.Random.guid(),
      name,
      teacherId,
      gender,
      avatar: `https://xsgames.co/randomusers/avatar.php?g=${gender === '男' ? 'male' : 'female'}&${Mock.Random.integer(1, 1000)}`,
      department,
      title,
      phone: `1${Mock.Random.pick(['3', '5', '7', '8', '9'])}${Mock.Random.string('number', 9)}`,
      email: Mock.Random.email(),
      status: Mock.Random.pick(['active', 'inactive']),
    });
  }
  
  return teachers;
};

// 预生成一批教师数据
const teacherPool = generateTeachers(50);

// 获取所有教师
export const getAllTeachers = (): Teacher[] => {
  return teacherPool;
};

// 根据ID获取教师
export const getTeacherById = (id: string): Teacher | undefined => {
  return teacherPool.find(teacher => teacher.id === id);
};

// 根据多个ID获取教师
export const getTeachersByIds = (ids: string[]): Teacher[] => {
  return teacherPool.filter(teacher => ids.includes(teacher.id));
};

// 搜索教师
export const searchTeachers = (keyword: string): Teacher[] => {
  if (!keyword) return teacherPool;
  
  const lowerKeyword = keyword.toLowerCase();
  return teacherPool.filter(teacher => 
    teacher.name.toLowerCase().includes(lowerKeyword) ||
    teacher.teacherId.toLowerCase().includes(lowerKeyword) ||
    (teacher.department && teacher.department.toLowerCase().includes(lowerKeyword)) ||
    (teacher.email && teacher.email.toLowerCase().includes(lowerKeyword))
  );
};

// 教师和课堂的关系数据
export const teacherClassroomRelations: TeacherClassroomRelation[] = [];

// 根据课堂ID获取相关教师
export function getTeachersByClassroomId(classroomId: string): Teacher[] {
  // 查找与该课堂关联的所有教师ID
  const teacherIds = teacherClassroomRelations
    .filter(relation => relation.classroomId === classroomId)
    .map(relation => relation.teacherId);
  
  // 如果没有关联教师数据，随机分配一名主讲教师
  if (teacherIds.length === 0) {
    const randomTeacher = Mock.Random.pick(teacherPool);
    
    // 添加关联关系
    teacherClassroomRelations.push({
      teacherId: randomTeacher.id,
      classroomId,
      role: 'owner',
      joinTime: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss')
    });
    
    return [randomTeacher];
  }
  
  // 返回关联的教师数据
  return teacherPool.filter(teacher => teacherIds.includes(teacher.id));
}

// 获取课堂的主讲教师
export function getMainTeacherByClassroomId(classroomId: string): Teacher | undefined {
  const relation = teacherClassroomRelations.find(
    relation => relation.classroomId === classroomId && relation.role === 'owner'
  );
  
  if (!relation) {
    // 如果没有找到，随机分配一名教师并设置为主讲
    const randomTeacher = Mock.Random.pick(teacherPool);
    
    teacherClassroomRelations.push({
      teacherId: randomTeacher.id,
      classroomId,
      role: 'owner',
      joinTime: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss')
    });
    
    return randomTeacher;
  }
  
  return teacherPool.find(teacher => teacher.id === relation.teacherId);
}

// 向课堂添加助教
export function addAssistantToClassroom(classroomId: string, teacherId: string): boolean {
  try {
    // 检查是否已经存在关联
    const existingRelation = teacherClassroomRelations.find(
      relation => relation.teacherId === teacherId && relation.classroomId === classroomId
    );
    
    if (existingRelation) {
      // 如果已存在，则更新角色为助教
      existingRelation.role = 'assistant';
    } else {
      // 添加新的关联关系
      teacherClassroomRelations.push({
        teacherId,
        classroomId,
        role: 'assistant',
        joinTime: Mock.Random.datetime('yyyy-MM-dd HH:mm:ss')
      });
    }
    
    return true;
  } catch (error) {
    console.error('添加助教到课堂失败:', error);
    return false;
  }
}

// 从课堂移除教师
export function removeTeacherFromClassroom(classroomId: string, teacherId: string): boolean {
  try {
    const relationIndex = teacherClassroomRelations.findIndex(
      relation => relation.teacherId === teacherId && relation.classroomId === classroomId
    );
    
    if (relationIndex !== -1) {
      // 移除关联关系
      teacherClassroomRelations.splice(relationIndex, 1);
    }
    
    return true;
  } catch (error) {
    console.error('从课堂移除教师失败:', error);
    return false;
  }
}

// 模拟接口
export default [
  {
    url: '/api/teachers',
    method: 'get',
    response: (req: any) => {
      const { keyword } = req.query;
      const teachers = keyword ? searchTeachers(keyword) : getAllTeachers();
      
      return {
        code: 200,
        data: teachers
      };
    }
  },
  {
    url: '/api/teachers/:id',
    method: 'get',
    response: (req: any) => {
      const { id } = req.params;
      const teacher = getTeacherById(id);
      
      if (!teacher) {
        return {
          code: 404,
          message: '教师不存在'
        };
      }
      
      return {
        code: 200,
        data: teacher
      };
    }
  },
  {
    url: '/api/classroom/:id/teachers',
    method: 'get',
    response: (req: any) => {
      const { id } = req.params;
      const teachers = getTeachersByClassroomId(id);
      
      return {
        code: 200,
        data: teachers
      };
    }
  },
  {
    url: '/api/classroom/:id/main-teacher',
    method: 'get',
    response: (req: any) => {
      const { id } = req.params;
      const teacher = getMainTeacherByClassroomId(id);
      
      if (!teacher) {
        return {
          code: 404,
          message: '未找到主讲教师'
        };
      }
      
      return {
        code: 200,
        data: teacher
      };
    }
  },
  {
    url: '/api/classroom/:id/add-assistant',
    method: 'post',
    response: (req: any) => {
      const { id } = req.params;
      const { teacherId } = req.body;
      
      if (!teacherId) {
        return {
          code: 400,
          message: '缺少教师ID'
        };
      }
      
      const success = addAssistantToClassroom(id, teacherId);
      
      if (!success) {
        return {
          code: 500,
          message: '添加助教失败'
        };
      }
      
      return {
        code: 200,
        message: '添加助教成功'
      };
    }
  },
  {
    url: '/api/classroom/:id/remove-teacher',
    method: 'post',
    response: (req: any) => {
      const { id } = req.params;
      const { teacherId } = req.body;
      
      if (!teacherId) {
        return {
          code: 400,
          message: '缺少教师ID'
        };
      }
      
      const success = removeTeacherFromClassroom(id, teacherId);
      
      if (!success) {
        return {
          code: 500,
          message: '移除教师失败'
        };
      }
      
      return {
        code: 200,
        message: '移除教师成功'
      };
    }
  }
] as MockMethod[]; 