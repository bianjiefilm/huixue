<template>
  <div class="role-manager">
    <a-card title="角色管理" class="main-card">
      <!-- 用户搜索和筛选 -->
      <div class="filters-section">
        <a-form layout="inline" class="filter-form">
          <a-form-item label="用户角色">
            <a-select
              v-model:value="filters.role"
              placeholder="选择角色"
              style="width: 120px"
              allow-clear
            >
              <a-select-option value="student">学生</a-select-option>
              <a-select-option value="teacher">教师</a-select-option>
              <a-select-option value="admin">管理员</a-select-option>
              <a-select-option value="assistant">助教</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item label="搜索用户">
            <a-input
              v-model:value="filters.search"
              placeholder="用户名或邮箱"
              style="width: 200px"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>
          <a-form-item>
            <a-button type="primary" @click="loadUsers">
              <template #icon>
                <ReloadOutlined />
              </template>
              搜索
            </a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 用户列表 -->
      <a-table
        :columns="columns"
        :data-source="users"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'role'">
            <a-tag :color="getRoleColor(record.role)">
              {{ getRoleDisplayName(record.role) }}
            </a-tag>
          </template>
          <template v-if="column.key === 'permissions'">
            <a-tooltip title="查看权限详情">
              <a-button
                type="link"
                size="small"
                @click="showPermissionsModal(record)"
              >
                查看权限 ({{ record.permissions?.length || 0 }})
              </a-button>
            </a-tooltip>
          </template>
          <template v-if="column.key === 'actions'">
            <a-space>
              <a-button
                type="primary"
                size="small"
                @click="showRoleModal(record)"
              >
                修改角色
              </a-button>
              <a-button
                type="default"
                size="small"
                @click="showPermissionsModal(record)"
              >
                权限管理
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>

      <!-- 角色修改模态框 -->
      <a-modal
        v-model:open="roleModalVisible"
        title="修改用户角色"
        @ok="handleRoleChange"
        :confirm-loading="roleChanging"
      >
        <a-form :model="roleForm" layout="vertical">
          <a-form-item
            label="新角色"
            name="role"
            :rules="[{ required: true, message: '请选择角色' }]"
          >
            <a-select v-model:value="roleForm.role" placeholder="选择角色">
              <a-select-option value="student">学生</a-select-option>
              <a-select-option value="teacher">教师</a-select-option>
              <a-select-option value="admin">管理员</a-select-option>
              <a-select-option value="assistant">助教</a-select-option>
            </a-select>
          </a-form-item>
          <a-form-item v-if="roleForm.role === 'admin'">
            <a-alert
              message="管理员权限说明"
              description="管理员拥有系统最高权限，包括用户管理、系统配置、课程审批等。"
              type="warning"
              show-icon
            />
          </a-form-item>
        </a-form>
      </a-modal>

      <!-- 权限详情模态框 -->
      <a-modal
        v-model:open="permissionsModalVisible"
        title="用户权限详情"
        width="800px"
        :footer="null"
      >
        <div v-if="selectedUser">
          <div class="user-info">
            <h3>{{ selectedUser.displayName || selectedUser.username }}</h3>
            <p>角色: <a-tag :color="getRoleColor(selectedUser.role)">{{ getRoleDisplayName(selectedUser.role) }}</a-tag></p>
          </div>

          <a-divider />

          <div class="permissions-list">
            <h4>权限列表</h4>
            <div class="permission-categories">
              <div
                v-for="category in permissionCategories"
                :key="category.key"
                class="category-section"
              >
                <h5>{{ category.name }}</h5>
                <div class="permission-items">
                  <a-tag
                    v-for="perm in getCategoryPermissions(category.key)"
                    :key="perm"
                    color="blue"
                  >
                    {{ getPermissionDisplayName(perm) }}
                  </a-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-modal>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  UserOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'
import {
  UserRole,
  PermissionCode,
  getRoleDisplayName,
  getPermissionDisplayName,
  getRolePermissions
} from '../../utils/permissions'

interface User {
  id: string
  username: string
  email: string
  displayName?: string
  role: string
  permissions: string[]
  createdAt: string
  lastLoginAt?: string
}

const filters = reactive({
  role: '',
  search: ''
})

const users = ref<User[]>([])
const loading = ref(false)
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
})

// 模态框状态
const roleModalVisible = ref(false)
const permissionsModalVisible = ref(false)
const roleChanging = ref(false)

// 表单数据
const roleForm = reactive({
  role: ''
})

// 选中的用户
const selectedUser = ref<User | null>(null)

// 权限分类
const permissionCategories = [
  { key: 'course', name: '课程管理' },
  { key: 'task', name: '任务管理' },
  { key: 'classroom', name: '课堂管理' },
  { key: 'student', name: '学生管理' },
  { key: 'teacher', name: '教师权限' },
  { key: 'admin', name: '管理员权限' },
  { key: 'file', name: '文件管理' },
  { key: 'statistics', name: '统计查看' },
  { key: 'coin', name: '金币管理' }
]

// 表格列配置
const columns = [
  {
    title: '用户名',
    dataIndex: 'username',
    key: 'username',
    ellipsis: true
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    ellipsis: true
  },
  {
    title: '显示名称',
    dataIndex: 'displayName',
    key: 'displayName',
    ellipsis: true
  },
  {
    title: '角色',
    key: 'role',
    width: 100
  },
  {
    title: '权限数量',
    key: 'permissions',
    width: 120
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    width: 150,
    sorter: true
  },
  {
    title: '最后登录',
    dataIndex: 'lastLoginAt',
    key: 'lastLoginAt',
    width: 150,
    sorter: true
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
]

// 加载用户列表
const loadUsers = async () => {
  loading.value = true
  try {
    // 这里应该调用用户管理API，暂时使用模拟数据
    const mockUsers: User[] = [
      {
        id: '1',
        username: 'student1',
        email: 'student1@example.com',
        displayName: '学生1',
        role: 'student',
        permissions: ['course:read', 'task:read', 'statistics:view'],
        createdAt: '2024-01-01',
        lastLoginAt: '2024-01-15'
      },
      {
        id: '2',
        username: 'teacher1',
        email: 'teacher1@example.com',
        displayName: '教师1',
        role: 'teacher',
        permissions: getRolePermissions(UserRole.TEACHER).map(p => p.toString()),
        createdAt: '2024-01-01',
        lastLoginAt: '2024-01-15'
      }
    ]

    // 应用筛选
    let filteredUsers = mockUsers
    if (filters.role) {
      filteredUsers = filteredUsers.filter(u => u.role === filters.role)
    }
    if (filters.search) {
      const search = filters.search.toLowerCase()
      filteredUsers = filteredUsers.filter(u =>
        u.username.toLowerCase().includes(search) ||
        u.email.toLowerCase().includes(search) ||
        (u.displayName && u.displayName.toLowerCase().includes(search))
      )
    }

    users.value = filteredUsers
    pagination.total = filteredUsers.length
  } catch (error) {
    console.error('加载用户列表失败:', error)
    message.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

// 获取角色颜色
const getRoleColor = (role: string) => {
  const colors: Record<string, string> = {
    student: 'blue',
    teacher: 'green',
    admin: 'red',
    assistant: 'orange'
  }
  return colors[role] || 'default'
}

// 显示角色修改模态框
const showRoleModal = (user: User) => {
  selectedUser.value = user
  roleForm.role = user.role
  roleModalVisible.value = true
}

// 处理角色修改
const handleRoleChange = async () => {
  if (!selectedUser.value) return

  roleChanging.value = true
  try {
    // 这里应该调用API修改用户角色
    // await permissionService.assignUserRole(selectedUser.value.id, [roleForm.role])

    // 模拟修改
    selectedUser.value.role = roleForm.role
    selectedUser.value.permissions = getRolePermissions(roleForm.role as UserRole).map(p => p.toString())

    message.success('角色修改成功')
    roleModalVisible.value = false
    loadUsers() // 重新加载列表
  } catch (error) {
    console.error('修改角色失败:', error)
    message.error('修改角色失败')
  } finally {
    roleChanging.value = false
  }
}

// 显示权限详情模态框
const showPermissionsModal = (user: User) => {
  selectedUser.value = user
  permissionsModalVisible.value = true
}

// 获取分类权限
const getCategoryPermissions = (category: string) => {
  if (!selectedUser.value?.permissions) return []

  const categoryPrefix = `${category}:`
  return selectedUser.value.permissions
    .filter(p => p.startsWith(categoryPrefix))
    .map(p => p as PermissionCode)
}

// 处理表格变化
const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadUsers()
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.role-manager {
  padding: 20px;
}

.filters-section {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 16px;
}

.main-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-info {
  text-align: center;
  margin-bottom: 16px;
}

.user-info h3 {
  margin: 0 0 8px 0;
  color: #1890ff;
}

.permissions-list h4 {
  margin-bottom: 16px;
  color: #262626;
}

.permission-categories {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-section h5 {
  margin: 0 0 8px 0;
  color: #595959;
  font-weight: 500;
}

.permission-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
