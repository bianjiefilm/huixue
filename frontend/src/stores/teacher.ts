import { defineStore } from 'pinia'
import { ref } from 'vue'
import { message } from 'ant-design-vue'
import {
  getTeacherList as apiGetTeacherList,
  getTeacherById as apiGetTeacherById,
  createTeacher as apiCreateTeacher,
  updateTeacher as apiUpdateTeacher,
  deleteTeacher as apiDeleteTeacher,
  getTeachersByIds as apiGetTeachersByIds,
  type Teacher,
  type PageResult,
  type QueryParams
} from '@/api/teacher'

export const useTeacherStore = defineStore('teacher', () => {
  const loading = ref(false)

  async function getTeacherList(params: QueryParams): Promise<PageResult<Teacher>> {
    loading.value = true
    try {
      return await apiGetTeacherList(params)
    } catch (error) {
      message.error('获取教师列表失败')
      return { items: [], total: 0 }
    } finally {
      loading.value = false
    }
  }

  async function getTeacherDetail(id: string): Promise<Teacher | null> {
    try {
      return await apiGetTeacherById(id)
    } catch (error) {
      message.error('获取教师详情失败')
      return null
    }
  }

  async function getTeachersByIds(ids: string[]): Promise<Teacher[]> {
    try {
      return await apiGetTeachersByIds(ids)
    } catch (error) {
      message.error('获取教师失败')
      return []
    }
  }

  async function createTeacher(data: Omit<Teacher, 'id'>): Promise<Teacher | null> {
    try {
      return await apiCreateTeacher(data)
    } catch (error) {
      message.error('创建教师失败')
      return null
    }
  }

  async function updateTeacher(id: string, data: Partial<Teacher>): Promise<Teacher | null> {
    try {
      return await apiUpdateTeacher(id, data)
    } catch (error) {
      message.error('更新教师失败')
      return null
    }
  }

  async function deleteTeacher(id: string): Promise<boolean> {
    try {
      return await apiDeleteTeacher(id)
    } catch (error) {
      message.error('删除教师失败')
      return false
    }
  }

  return {
    loading,
    getTeacherList,
    getTeacherDetail,
    getTeachersByIds,
    createTeacher,
    updateTeacher,
    deleteTeacher
  }
})