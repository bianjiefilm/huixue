import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { userLogin } from '@/api/user';
import { getToken as getAuthToken, setAuth, clearAuth } from '@/utils/auth';
import {
  UserRole as PermissionUserRole,
  PermissionCode,
  hasPermission,
  getRolePermissions,
  initializeUserPermissions,
  clearPermissionCache
} from '../utils/permissions';

// 用户角色类型（兼容现有代码）
export type UserRole = 'student' | 'teacher' | 'admin';

// 用户状态存储
export const useUserStore = defineStore('user', () => {
  // 从本地存储恢复用户信息
  const storedUserInfo = localStorage.getItem('userInfo');
  let parsedUserInfo: any = null;

  if (storedUserInfo) {
    try {
      parsedUserInfo = JSON.parse(storedUserInfo);
      // 确保必要的字段存在
      if (!parsedUserInfo.id && parsedUserInfo.user_id) {
        parsedUserInfo.id = parsedUserInfo.user_id.toString();
      }
      if (!parsedUserInfo.role) {
        console.warn('用户信息中缺少role字段');
        parsedUserInfo.role = 'student'; // 默认设为学生
      }
    } catch (e) {
      console.error('解析用户信息失败:', e);
      parsedUserInfo = null;
    }
  }

  // 如果没有有效的用户信息，使用默认值
  const defaultUserInfo = parsedUserInfo || {
    id: '',
    username: '',
    role: 'student' as UserRole
  };

  // 状态
  const token = ref<string | null>(getAuthToken())
  const userInfo = ref<{
    id?: string
    user_id?: string | number
    username?: string
    avatar?: string
    email?: string
	realname?: string
	mobile?: string
    role?: UserRole
    permissions?: PermissionCode[]
  }>(defaultUserInfo)
  const isLoggedIn = computed(() => !!token.value)
  // 计算当前用户是否为管理员
  const isAdmin = computed(() => userInfo.value.role === 'admin')
  // 获取当前用户ID (转换为数字)
  const userId = computed(() => userInfo.value.id ? parseInt(userInfo.value.id) : undefined)
  // 获取用户角色，确保有默认值
  const userRole = computed(() => userInfo.value.role || 'student')
  // 获取用户权限列表
  const userPermissions = computed(() => userInfo.value.permissions || getRolePermissions(userRole.value as PermissionUserRole))

  // 监听userInfo变化，自动持久化到localStorage
  watch(() => userInfo.value, (newVal) => {
    localStorage.setItem('userInfo', JSON.stringify(newVal));
  }, { deep: true });

  // 操作方法
  function setToken(newToken: string) {
    token.value = newToken
    // 使用 auth.ts 中的 setAuth 方法来保存 token
    setAuth(newToken, userInfo.value)
  }

  function clearToken() {
    token.value = null
    // 使用 auth.ts 中的 clearAuth 方法
    clearAuth()
  }

  function setUserInfo(info: any) {
    // 确保所有必要字段都存在
    const processedInfo = {
      id: info.id?.toString() || info.user_id?.toString() || '',
      user_id: info.user_id || info.id, // 保留原字段以防其他地方依赖
      username: info.username || '',
      email: info.email || '',
      realname: info.realname || info.name || '',
      mobile: info.mobile || '',
      avatar: info.avatar || '',
      role: (info.role === 'teacher' || info.role === 'admin' || info.role === 'student')
        ? info.role
        : 'student'  // 默认角色
    };

    userInfo.value = processedInfo;
    localStorage.setItem('userInfo', JSON.stringify(processedInfo));
    console.log('User info updated:', processedInfo);
  }

  function logout() {
    clearToken()
    // 彻底清除用户信息，防止角色越权（修复上一用户的身份残留）
    userInfo.value = { role: 'student' };
    localStorage.removeItem('userInfo');
  }

  // 切换用户角色
  function switchRole(newRole: UserRole) {
    userInfo.value = {
      ...userInfo.value,
      role: newRole,
      permissions: getRolePermissions(newRole as PermissionUserRole)
    }
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value));
    clearPermissionCache() // 清除权限缓存
  }

  // 检查用户是否有指定权限
  async function checkPermission(permission: PermissionCode, context?: Record<string, any>): Promise<boolean> {
    return await hasPermission(permission, userInfo.value.id, context)
  }

  // 检查用户是否有多个权限中的任意一个
  async function checkPermissions(permissions: PermissionCode[], context?: Record<string, any>): Promise<boolean> {
    for (const permission of permissions) {
      if (await hasPermission(permission, userInfo.value.id, context)) {
        return true
      }
    }
    return false
  }

  // 初始化用户权限
  async function initPermissions(): Promise<void> {
    if (userInfo.value.id && userInfo.value.role) {
      try {
        await initializeUserPermissions(userInfo.value.id, userInfo.value.role as PermissionUserRole)
        // 更新本地权限信息
        userInfo.value.permissions = getRolePermissions(userInfo.value.role as PermissionUserRole)
      } catch (error) {
        console.error('初始化用户权限失败:', error)
      }
    }
  }

  async function login(credentials: { username: string; password: string }) {
	try {
	  const res = await userLogin(credentials) as any;

	  // Check if response has the expected structure
	  if (!res || !res.token || !res.user) {
	    console.error('Invalid response structure:', res);
	    throw new Error('Invalid response from server');
	  }

	  setToken(res.token.access_token || res.token);
	  setUserInfo(res.user);
	} catch (err) {
	  console.error('Login error:', err);
	  clearToken();
	  throw err;
	}
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isAdmin,
    userId,
    userRole,
    userPermissions,
    setToken,
    clearToken,
    setUserInfo,
    switchRole,
    checkPermission,
    checkPermissions,
    initPermissions,
    login,
    logout
  }
})
