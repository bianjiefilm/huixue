import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { Role, Permission, rolePermissions } from '@/constants/permissions'

export function usePermission() {
  const userStore = useUserStore()
  
  // 获取当前用户的所有权限
  const userPermissions = computed(() => {
    const role = userStore.user?.role as Role
    if (!role) return []
    return rolePermissions[role] || []
  })
  
  // 检查是否拥有单个权限
  const hasPermission = (permission: Permission): boolean => {
    return userPermissions.value.includes(permission)
  }
  
  // 检查是否拥有多个权限中的任意一个
  const hasAnyPermission = (permissions: Permission[]): boolean => {
    return permissions.some(permission => hasPermission(permission))
  }
  
  // 检查是否拥有所有权限
  const hasAllPermissions = (permissions: Permission[]): boolean => {
    return permissions.every(permission => hasPermission(permission))
  }
  
  // 检查是否是某个角色
  const hasRole = (role: Role): boolean => {
    return userStore.user?.role === role
  }
  
  // 检查是否是多个角色中的任意一个
  const hasAnyRole = (roles: Role[]): boolean => {
    return roles.includes(userStore.user?.role as Role)
  }
  
  // 检查是否可以操作某个资源（考虑所有权）
  const canOperate = (permission: Permission, resourceOwnerId?: string): boolean => {
    // 管理员可以操作所有资源
    if (hasRole(Role.ADMIN)) return true
    
    // 检查基础权限
    if (!hasPermission(permission)) return false
    
    // 如果提供了资源所有者ID，检查是否是资源所有者
    if (resourceOwnerId && userStore.user?.id) {
      return resourceOwnerId === userStore.user.id
    }
    
    return true
  }
  
  // 便捷方法
  const isAdmin = computed(() => hasRole(Role.ADMIN))
  const isTeacher = computed(() => hasRole(Role.TEACHER))
  const isStudent = computed(() => hasRole(Role.STUDENT))
  
  return {
    userPermissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    canOperate,
    isAdmin,
    isTeacher,
    isStudent
  }
}