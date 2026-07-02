import { defineStore } from 'pinia';
import type { ClassroomDetail, Student } from '../types/classroom';
import { 
  getClassrooms, 
  getClassroomDetail, 
  deleteClassroom,
  updateClassroom,
  createClassroom,
  addStudentsToClassroom,
  removeStudentsFromClassroom,
  getClassroomStudents
} from '../api/classroom';

export const useClassroomStore = defineStore('classroom', {
  state: () => ({
    classrooms: {
      ongoing: [] as ClassroomDetail[],
      upcoming: [] as ClassroomDetail[],
      past: [] as ClassroomDetail[]
    },
    currentClassroom: null as ClassroomDetail | null,
    currentStudents: [] as Student[],
    loading: {
      ongoing: false,
      upcoming: false,
      past: false,
      detail: false,
      create: false,
      update: false,
      delete: false,
      students: false
    },
    error: null as Error | null
  }),
  
  getters: {
    // 获取进行中的课堂数量
    ongoingCount: (state) => state.classrooms.ongoing.length,

    // 获取即将开始的课堂数量
    upcomingCount: (state) => state.classrooms.upcoming.length,

    // 获取已结束的课堂数量
    pastCount: (state) => state.classrooms.past.length,

    // 获取当前课堂ID
    currentClassroomId: (state) => state.currentClassroom?.id
  },
  
  actions: {
    // 获取所有课堂
    async fetchClassrooms(status: 'ongoing' | 'upcoming' | 'past' = 'ongoing', role: string = 'teacher', studentId?: string) {
      const loadingKey = role === 'student' ? 'ongoing' : status;
      this.loading[loadingKey] = true;

      try {
        if (role === 'student') {
          // 对于学生，一次性获取所有状态的数据
          console.log('Student fetching classrooms for studentId:', studentId);
          const ongoingClassrooms = await getClassrooms('ongoing', role, studentId);
          const upcomingClassrooms = await getClassrooms('upcoming', role, studentId);
          const pastClassrooms = await getClassrooms('past', role, studentId);

          console.log('API responses:', {
            ongoing: ongoingClassrooms.length,
            upcoming: upcomingClassrooms.length,
            past: pastClassrooms.length
          });

          this.classrooms.ongoing = ongoingClassrooms;
          this.classrooms.upcoming = upcomingClassrooms;
          this.classrooms.past = pastClassrooms;

          console.log('Updated store classrooms:', {
            ongoing: this.classrooms.ongoing.length,
            upcoming: this.classrooms.upcoming.length,
            past: this.classrooms.past.length
          });
        } else {
          // 对于教师，按状态分别获取
          const classrooms = await getClassrooms(status, role, studentId);
          this.classrooms[status] = classrooms;
        }
        this.error = null;
      } catch (error) {
        console.error('获取课堂列表失败:', error);
        this.error = error as Error;
      } finally {
        this.loading[loadingKey] = false;
      }
    },
    
    // 获取课堂详情
    async fetchClassroomDetail(id: string) {
      this.loading.detail = true;
      try {
        const classroom = await getClassroomDetail(id);
        if (classroom) {
          this.currentClassroom = classroom;
        } else {
          throw new Error('课堂不存在');
        }
        this.error = null;
      } catch (error) {
        console.error('获取课堂详情失败:', error);
        this.error = error as Error;
      } finally {
        this.loading.detail = false;
      }
    },
    
    // 创建新课堂
    async createNewClassroom(classroom: Partial<ClassroomDetail>) {
      this.loading.create = true;
      try {
        const newClassroom = await createClassroom(classroom);
        this.classrooms.unshift(newClassroom);
        this.error = null;
        return newClassroom;
      } catch (error) {
        console.error('创建课堂失败:', error);
        this.error = error as Error;
        throw error;
      } finally {
        this.loading.create = false;
      }
    },
    
    // 更新课堂
    async updateClassroomInfo(id: string, data: Partial<ClassroomDetail>) {
      this.loading.update = true;
      try {
        const updatedClassroom = await updateClassroom(id, data);
        if (updatedClassroom) {
          // 更新列表中的数据
          const index = this.classrooms.findIndex(c => c.id === id);
          if (index !== -1) {
            this.classrooms[index] = updatedClassroom;
          }
          // 更新当前课堂数据
          if (this.currentClassroom?.id === id) {
            this.currentClassroom = updatedClassroom;
          }
        }
        this.error = null;
        return updatedClassroom;
      } catch (error) {
        console.error('更新课堂失败:', error);
        this.error = error as Error;
        return null;
      } finally {
        this.loading.update = false;
      }
    },
    
    // 删除课堂
    async deleteClassroom(id: string) {
      this.loading.delete = true;
      try {
        const result = await deleteClassroom(id);
        if (result.success) {
          // 从列表中删除
          this.classrooms = this.classrooms.filter(c => c.id !== id);
          // 清空当前课堂（如果是删除的当前课堂）
          if (this.currentClassroom?.id === id) {
            this.currentClassroom = null;
          }
        } else {
          throw new Error(result.message || '删除课堂失败');
        }
        this.error = null;
        return result;
      } catch (error) {
        console.error('删除课堂失败:', error);
        this.error = error as Error;
        throw error;
      } finally {
        this.loading.delete = false;
      }
    },
    
    // 获取课堂学生
    async fetchClassroomStudents(classroomId: string) {
      this.loading.students = true;
      try {
        this.currentStudents = await getClassroomStudents(classroomId);
        this.error = null;
      } catch (error) {
        console.error('获取课堂学生失败:', error);
        this.error = error as Error;
      } finally {
        this.loading.students = false;
      }
    },
    
    // 添加学生到课堂
    async addStudents(classroomId: string, studentIds: string[]) {
      try {
        const result = await addStudentsToClassroom(classroomId, studentIds);
        if (result) {
          // 重新获取课堂信息
          await this.fetchClassroomDetail(classroomId);
          // 重新获取学生列表
          await this.fetchClassroomStudents(classroomId);
        }
        return result;
      } catch (error) {
        console.error('添加学生失败:', error);
        this.error = error as Error;
        return false;
      }
    },
    
    // 从课堂移除学生
    async removeStudents(classroomId: string, studentIds: string[]) {
      try {
        const result = await removeStudentsFromClassroom(classroomId, studentIds);
        if (result) {
          // 重新获取课堂信息
          await this.fetchClassroomDetail(classroomId);
          // 重新获取学生列表
          await this.fetchClassroomStudents(classroomId);
        }
        return result;
      } catch (error) {
        console.error('移除学生失败:', error);
        this.error = error as Error;
        return false;
      }
    },
    
    // 清除当前课堂
    clearCurrentClassroom() {
      this.currentClassroom = null;
      this.currentStudents = [];
    },
    
    // 清除错误
    clearError() {
      this.error = null;
    }
  }
}); 