import type { Directive, DirectiveBinding } from 'vue'
import { usePermission } from '@/composables/usePermission'
import { Permission } from '@/constants/permissions'

interface PermissionElement extends HTMLElement {
  _permissionHandler?: () => void
}

// v-permission 指令
export const permission: Directive = {
  mounted(el: PermissionElement, binding: DirectiveBinding) {
    const { value } = binding
    if (!value) return
    
    const { hasPermission, hasAnyPermission } = usePermission()
    
    // 支持单个权限或权限数组
    const permissions = Array.isArray(value) ? value : [value]
    const hasAccess = permissions.length === 1 
      ? hasPermission(permissions[0] as Permission)
      : hasAnyPermission(permissions as Permission[])
    
    if (!hasAccess) {
      // 没有权限时隐藏元素
      el.style.display = 'none'
    }
    
    // 保存处理函数以便在更新时使用
    el._permissionHandler = () => {
      const currentHasAccess = permissions.length === 1 
        ? hasPermission(permissions[0] as Permission)
        : hasAnyPermission(permissions as Permission[])
      
      el.style.display = currentHasAccess ? '' : 'none'
    }
  },
  
  updated(el: PermissionElement, binding: DirectiveBinding) {
    const { value, oldValue } = binding
    if (value === oldValue) return
    
    // 权限变化时重新检查
    if (el._permissionHandler) {
      el._permissionHandler()
    }
  },
  
  unmounted(el: PermissionElement) {
    delete el._permissionHandler
  }
}

// v-role 指令
export const role: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const { value } = binding
    if (!value) return
    
    const { hasRole, hasAnyRole } = usePermission()
    
    // 支持单个角色或角色数组
    const roles = Array.isArray(value) ? value : [value]
    const hasAccess = roles.length === 1 
      ? hasRole(roles[0])
      : hasAnyRole(roles)
    
    if (!hasAccess) {
      el.style.display = 'none'
    }
  },
  
  updated(el: HTMLElement, binding: DirectiveBinding) {
    const { value, oldValue } = binding
    if (value === oldValue) return
    
    const { hasRole, hasAnyRole } = usePermission()
    const roles = Array.isArray(value) ? value : [value]
    const hasAccess = roles.length === 1 
      ? hasRole(roles[0])
      : hasAnyRole(roles)
    
    el.style.display = hasAccess ? '' : 'none'
  }
}