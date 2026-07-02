<template>
  <div v-if="hasAccess">
    <slot />
  </div>
  <div v-else-if="fallback">
    <slot name="fallback" />
  </div>
  <div v-else-if="showError" class="permission-error">
    <a-result
      status="403"
      title="权限不足"
      :sub-title="errorMessage"
    >
      <template #extra>
        <a-button type="primary" @click="handleRetry">
          重试
        </a-button>
      </template>
    </a-result>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { hasPermission, PermissionCode } from '../../utils/permissions'

interface Props {
  permission?: PermissionCode
  permissions?: PermissionCode[]
  userId?: string
  context?: Record<string, any>
  requireAll?: boolean // 是否需要所有权限都满足（默认false，即任一权限满足即可）
  fallback?: boolean // 是否显示fallback插槽
  showError?: boolean // 是否显示错误信息
  errorMessage?: string // 自定义错误信息
}

const props = withDefaults(defineProps<Props>(), {
  requireAll: false,
  fallback: false,
  showError: true,
  errorMessage: '您没有权限访问此内容'
})

const hasAccess = ref(false)
const loading = ref(true)

const checkAccess = async () => {
  loading.value = true
  try {
    if (props.permission) {
      hasAccess.value = await hasPermission(props.permission, props.userId, props.context)
    } else if (props.permissions && props.permissions.length > 0) {
      if (props.requireAll) {
        // 需要所有权限都满足
        const results = await Promise.all(
          props.permissions.map(p => hasPermission(p, props.userId, props.context))
        )
        hasAccess.value = results.every(result => result)
      } else {
        // 任一权限满足即可
        const results = await Promise.all(
          props.permissions.map(p => hasPermission(p, props.userId, props.context))
        )
        hasAccess.value = results.some(result => result)
      }
    } else {
      // 没有指定权限，默认允许访问
      hasAccess.value = true
    }
  } catch (error) {
    console.error('权限检查失败:', error)
    hasAccess.value = false
    if (props.showError) {
      message.error('权限检查失败，请重试')
    }
  } finally {
    loading.value = false
  }
}

const handleRetry = () => {
  checkAccess()
}

// 监听权限或上下文变化时重新检查
watch(
  () => [props.permission, props.permissions, props.userId, props.context],
  () => {
    checkAccess()
  },
  { deep: true }
)

onMounted(() => {
  checkAccess()
})
</script>

<style scoped>
.permission-error {
  padding: 20px;
  text-align: center;
}
</style>



