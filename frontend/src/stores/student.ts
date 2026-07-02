import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  getStudents,
  getStudentById,
  addStudent as apiAddStudent,
  updateStudent as apiUpdateStudent,
  deleteStudent as apiDeleteStudent,
  batchUpdateStatus as apiBatchUpdateStatus,
  batchDeleteStudents as apiBatchDeleteStudents,
  batchTransferStudents as apiBatchTransferStudents,
  importStudents as apiImportStudents
} from '@/api/student'

// 学生接口
export interface Student {
  id: string;
  name: string;
  studentId: string;
  gender: 'male' | 'female';
  avatar?: string;
  major: string;
  class: string;
  enrollYear: number;
  phone: string;
  email: string;
  department?: string;
  grade?: string;
  className?: string;
  status?: boolean;
  organizationId?: string;
}

// 分页结果
export interface PageResult<T> {
  items: T[];
  total: number;
}

// 查询参数
export interface QueryParams {
  organizationId: string;
  page: number;
  pageSize: number;
  keyword?: string;
}

export const useStudentStore = defineStore('student', {
  state: () => ({
    students: [] as Student[],
    currentStudent: null as Student | null,
    loading: false,
    keyword: ''
  }),
  
  getters: {
    totalStudents: (state) => state.students.length,
    
    // 获取男女学生数量
    genderStats: (state) => {
      const male = state.students.filter(student => student.gender === 'male').length;
      const female = state.students.filter(student => student.gender === 'female').length;
      return { male, female };
    },
    
    // 按专业分组的学生数量
    majorStats: (state) => {
      const stats: Record<string, number> = {};
      state.students.forEach(student => {
        if (student.major) {
          stats[student.major] = (stats[student.major] || 0) + 1;
        }
      });
      return stats;
    }
  },
  
  actions: {
    // 获取学生列表
    async fetchStudents(keyword?: string) {
      this.loading = true;
      try {
        this.students = await getStudents(keyword);
      } catch (error) {
        console.error('获取学生列表失败:', error);
        message.error('获取学生列表失败');
      } finally {
        this.loading = false;
      }
    },
    
    // 获取学生列表（别名方法，与fetchStudents功能相同）
    async getStudentList(params: QueryParams) {
      this.loading = true;
      try {
        this.keyword = params.keyword || '';
        this.students = await getStudents(params.keyword);
        return {
          items: this.students,
          total: this.students.length
        };
      } catch (error) {
        console.error('获取学生列表失败:', error);
        message.error('获取学生列表失败');
        return { items: [], total: 0 };
      } finally {
        this.loading = false;
      }
    },
    
    // 获取单个学生信息
    async fetchStudentById(id: string) {
      this.loading = true;
      try {
        this.currentStudent = await getStudentById(id);
        return this.currentStudent;
      } catch (error) {
        console.error('获取学生信息失败:', error);
        message.error('获取学生信息失败');
        return null;
      } finally {
        this.loading = false;
      }
    },
    
    // 获取学生详情（别名方法，与fetchStudentById功能相同）
    async getStudentDetail(id: string) {
      return this.fetchStudentById(id);
    },
    
    // 添加学生
    async addStudent(student: Partial<Student>) {
      this.loading = true;
      try {
        // 假设后端API会返回添加的学生信息
        const result = await apiAddStudent(student as Student);
        if (result) {
          message.success('添加学生成功');
          // 重新获取学生列表
          await this.fetchStudents(this.keyword);
          return true;
        }
        return false;
      } catch (error) {
        console.error('添加学生失败:', error);
        message.error('添加学生失败');
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    // 创建学生（别名方法，与addStudent功能相同）
    async createStudent(student: Partial<Student>) {
      return this.addStudent(student);
    },
    
    // 更新学生信息
    async updateStudent(id: string, student: Partial<Student>) {
      this.loading = true;
      try {
        const result = await apiUpdateStudent(id, student);
        if (result) {
          message.success('更新学生信息成功');
          // 重新获取学生列表
          await this.fetchStudents(this.keyword);
          return true;
        }
        return false;
      } catch (error) {
        console.error('更新学生信息失败:', error);
        message.error('更新学生信息失败');
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    // 删除学生
    async deleteStudent(id: string) {
      this.loading = true;
      try {
        const result = await apiDeleteStudent(id);
        if (result) {
          message.success('删除学生成功');
          // 重新获取学生列表
          await this.fetchStudents(this.keyword);
          return true;
        }
        return false;
      } catch (error) {
        console.error('删除学生失败:', error);
        message.error('删除学生失败');
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    // 批量删除学生
    async batchDeleteStudents(ids: string[]) {
      this.loading = true;
      try {
        const result = await apiBatchDeleteStudents(ids);
        if (result) {
          message.success(`成功删除${ids.length}个学生`);
          await this.fetchStudents(this.keyword);
          return true;
        } else {
          message.warning('部分学生删除失败');
          await this.fetchStudents(this.keyword);
          return false;
        }
      } catch (error) {
        console.error('批量删除学生失败:', error);
        message.error('批量删除学生失败');
        return false;
      } finally {
        this.loading = false;
      }
    },

    // 批量更新学生状态
    async batchUpdateStudentStatus(ids: string[], status: boolean) {
      this.loading = true;
      try {
        const result = await apiBatchUpdateStatus(ids, status);
        if (result) {
          message.success(`成功更新${ids.length}个学生状态`);
          await this.fetchStudents(this.keyword);
          return true;
        } else {
          message.warning('部分学生状态更新失败');
          await this.fetchStudents(this.keyword);
          return false;
        }
      } catch (error) {
        console.error('批量更新学生状态失败:', error);
        message.error('批量更新学生状态失败');
        return false;
      } finally {
        this.loading = false;
      }
    },

    // 转移学生到其他组织
    async transferStudents(ids: string[], targetClassId: string) {
      this.loading = true;
      try {
        const result = await apiBatchTransferStudents(ids, parseInt(targetClassId));
        if (result) {
          message.success(`成功转移${ids.length}个学生`);
          await this.fetchStudents(this.keyword);
          return true;
        } else {
          message.warning('部分学生转移失败');
          await this.fetchStudents(this.keyword);
          return false;
        }
      } catch (error) {
        console.error('转移学生失败:', error);
        message.error('转移学生失败');
        return false;
      } finally {
        this.loading = false;
      }
    },

    // 导入学生（文件上传）
    async importStudentsFromFile(file: File) {
      this.loading = true;
      try {
        const result = await apiImportStudents(file);
        if (result.success_count > 0) {
          message.success(`成功导入${result.success_count}个学生`);
        }
        if (result.error_count > 0) {
          message.warning(`${result.error_count}个学生导入失败`);
        }
        await this.fetchStudents(this.keyword);
        return result;
      } catch (error) {
        console.error('导入学生失败:', error);
        message.error('导入学生失败');
        return null;
      } finally {
        this.loading = false;
      }
    },

    // 导入学生（兼容旧接口）
    async importStudents(students: Partial<Student>[]) {
      this.loading = true;
      try {
        let success = true;
        let importedCount = 0;

        for (const student of students) {
          const result = await apiAddStudent(student as Student);
          if (result) {
            importedCount++;
          } else {
            success = false;
          }
        }

        if (success) {
          message.success(`成功导入${importedCount}个学生`);
        } else if (importedCount > 0) {
          message.warning(`部分导入成功: ${importedCount}/${students.length}`);
        } else {
          message.error('导入失败');
        }

        await this.fetchStudents(this.keyword);
        return importedCount > 0;
      } catch (error) {
        console.error('导入学生失败:', error);
        message.error('导入学生失败');
        return false;
      } finally {
        this.loading = false;
      }
    }
  }
}) 