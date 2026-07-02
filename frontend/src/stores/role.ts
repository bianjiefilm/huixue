import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import type { Teacher } from '../api/teacher'
import { getTeachersByIds, getTeacherList as fetchTeacherList } from '../api/teacher'
import { post, get } from '../utils/request'
import request from '../utils/request'

// 定义系统管理员结构（复用教师结构）
export type Admin = Teacher;

// 分页结果
export interface PageResult<T> {
  items: T[];
  total: number;
}

// 查询参数
export interface QueryParams {
  page: number;
  pageSize: number;
  keyword?: string;
  departmentId?: string;
}

export const useRoleStore = defineStore('role', () => {
  // 管理员ID列表（从后端获取）
  const adminIds = ref<string[]>([]);
  
  // 加载状态
  const loading = ref(false);
  const submitting = ref(false);

  // 获取管理员列表
  async function getAdminList(params: QueryParams): Promise<PageResult<Admin>> {
    loading.value = true;
    try {
      // 直接从后端获取管理员列表
      const response = await get('/api/v1/system/admins', {
        page: params.page,
        page_size: params.pageSize,
        keyword: params.keyword
      });
      
      // 解析响应
      const data = response.data || response;
      
      // 如果是数组，转换成分页格式
      if (Array.isArray(data)) {
        const admins = data.map((admin: any) => ({
          id: String(admin.id),
          name: admin.name || '',
          code: admin.job_number || '',
          jobNumber: admin.job_number || '',
          gender: admin.gender || '',
          phone: admin.phone || '',
          email: admin.email || '',
          title: admin.title || '',
          department: admin.department || '',
          isActive: admin.is_active ?? true
        }));
        
        // 更新本地缓存
        adminIds.value = admins.map((a: any) => a.id);
        
        // 前端分页
        const startIndex = (params.page - 1) * params.pageSize;
        const endIndex = Math.min(startIndex + params.pageSize, admins.length);
        
        return {
          items: admins.slice(startIndex, endIndex),
          total: admins.length
        };
      }
      
      // 如果后端已分页
      return {
        items: data.items || [],
        total: data.total || 0
      };
    } catch (error) {
      console.error('获取管理员列表失败:', error);
      message.error('获取管理员列表失败');
      return { items: [], total: 0 };
    } finally {
      loading.value = false;
    }
  }

  // 获取所有管理员ID
  async function getAdminIds(): Promise<string[]> {
    try {
      // 从后端获取管理员列表
      const response = await get('/api/v1/system/admins');
      // response 可能是 { data: [...], code: '0000' } 或直接是数组
      const adminList = response.data || response;
      if (Array.isArray(adminList)) {
        const ids = adminList.map((admin: any) => String(admin.id));
        adminIds.value = ids;
        return ids;
      }
      return adminIds.value;
    } catch (error) {
      console.error('获取管理员ID列表失败:', error);
      // 如果失败，返回本地缓存的
      return adminIds.value;
    }
  }

  // 添加管理员
  async function addAdmin(ids: string[]): Promise<boolean> {
    submitting.value = true;
    try {
      // 调用后端 API 设置管理员
      const teacherIds = ids.map(id => parseInt(id));
      await post('/api/v1/system/admins', { teacher_ids: teacherIds });
      
      // 同步更新本地存储
      adminIds.value = [...new Set([...adminIds.value, ...ids])];
      message.success('授权成功');
      return true;
    } catch (error) {
      console.error('添加管理员失败:', error);
      message.error('添加管理员失败');
      return false;
    } finally {
      submitting.value = false;
    }
  }

  // 移除管理员授权
  async function removeAdmin(id: string): Promise<boolean> {
    submitting.value = true;
    try {
      // 调用后端 API 移除管理员 - 使用 POST 发送到特定端点来移除
      const teacherId = parseInt(id);
      // FastAPI DELETE 请求体需要通过 axios 的 data 配置发送
      await request.delete('/api/v1/system/admins', { data: [teacherId] });
      
      // 从本地存储中移除
      adminIds.value = adminIds.value.filter(itemId => itemId !== id);
      message.success('移除管理员成功');
      return true;
    } catch (error) {
      console.error('移除管理员失败:', error);
      message.error('移除管理员失败');
      return false;
    } finally {
      submitting.value = false;
    }
  }

  // 批量移除管理员授权
  async function batchRemoveAdmin(ids: string[]): Promise<boolean> {
    submitting.value = true;
    try {
      // 从本地存储中批量移除
      adminIds.value = adminIds.value.filter(itemId => !ids.includes(itemId));
      message.success('批量移除管理员成功');
      return true;
    } catch (error) {
      console.error('批量移除管理员失败:', error);
      message.error('批量移除管理员失败');
      return false;
    } finally {
      submitting.value = false;
    }
  }

  // 获取未授权的教师列表（用于选择添加管理员）
  async function getUnauthorizedTeachers(params: QueryParams): Promise<PageResult<Teacher>> {
    loading.value = true;
    try {
      // 获取当前已授权的管理员ID列表
      const existingIds = await getAdminIds();
      
      // 获取所有教师列表
      const result = await fetchTeacherList(params);
      
      // 过滤掉已经是管理员的教师
      const filteredItems = result.items.filter(teacher => !existingIds.includes(teacher.id));
      
      return {
        items: filteredItems,
        total: result.total - (result.items.length - filteredItems.length)
      };
    } catch (error) {
      console.error('获取未授权教师列表失败:', error);
      message.error('获取未授权教师列表失败');
      return { items: [], total: 0 };
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    submitting,
    getAdminList,
    getAdminIds,
    addAdmin,
    removeAdmin,
    batchRemoveAdmin,
    getUnauthorizedTeachers
  }
}) 