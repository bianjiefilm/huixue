<template>
  <div class="role-container">
    <a-page-header title="角色授权" subtitle="授予教师用户管理员角色" />
    
    <div class="role-content">
      <a-card :bordered="false">
        <!-- 操作按钮区域 -->
        <div class="operation-area">
          <div class="left-operations">
            <a-button 
              type="primary" 
              @click="showAddModal"
            >
              添加
            </a-button>
          </div>
          <div class="right-operations">
            <a-input-search
              v-model:value="searchValue"
              placeholder="搜索姓名/工号"
              style="width: 250px"
              @search="onSearch"
            />
          </div>
        </div>
        
        <!-- 表格 -->
        <a-table
          :columns="columns"
          :data-source="tableData"
          :row-selection="rowSelection"
          :pagination="pagination"
          @change="handleTableChange"
          :loading="loading"
          row-key="id"
        >
          <!-- 操作列 -->
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-space>
                <a-popconfirm
                  title="确定要删除该用户的管理员授权吗?"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record)"
                >
                  <a class="danger-text">移除</a>
                </a-popconfirm>
              </a-space>
            </template>
            <!-- 头像 -->
            <template v-else-if="column.key === 'avatar'">
              <a-avatar :src="record.avatar" :alt="record.name">
                {{ record.name.substring(0, 1) }}
              </a-avatar>
            </template>
            <!-- 性别 -->
            <template v-else-if="column.key === 'gender'">
              {{ record.gender === 'male' ? '男' : record.gender === 'female' ? '女' : '未知' }}
            </template>
          </template>
        </a-table>
        
        <!-- 批量操作按钮 -->
        <div class="batch-operations" v-if="selectedRowKeys.length > 0">
          <a-popconfirm
            title="确定要移除选中用户的管理员授权吗?"
            ok-text="确定"
            cancel-text="取消"
            @confirm="confirmBatchDelete"
          >
            <a-button 
              type="primary" 
              danger
            >
              批量移除
            </a-button>
          </a-popconfirm>
        </div>
      </a-card>
    </div>
    
    <!-- 添加管理员模态框 -->
    <a-modal
      v-model:open="addModalVisible"
      title="添加管理员"
      @ok="handleAddOk"
      @cancel="handleAddCancel"
      :confirm-loading="addLoading"
      width="800px"
    >
      <div class="add-modal-content">
        <a-row :gutter="16">
          <!-- 左侧组织树 -->
          <a-col :span="8">
            <div class="org-tree-container">
              <h4>选择组织</h4>
              <a-tree
                v-model:expandedKeys="addExpandedKeys"
                v-model:selectedKeys="addSelectedKeys"
                :tree-data="treeData"
                @select="onAddTreeSelect"
              />
            </div>
          </a-col>
          
          <!-- 右侧教师列表 -->
          <a-col :span="16">
            <div class="teacher-list-container">
              <h4>选择教师</h4>
              
              <!-- 搜索 -->
              <a-input-search
                v-model:value="addSearchValue"
                placeholder="搜索姓名/工号"
                style="width: 100%; margin-bottom: 16px;"
                @search="onAddSearch"
              />
              
              <!-- 教师列表 -->
              <a-table
                :columns="addColumns"
                :data-source="addTableData"
                :row-selection="addRowSelection"
                :pagination="addPagination"
                @change="handleAddTableChange"
                :loading="addLoading"
                row-key="id"
                size="small"
              >
                <!-- 头像 -->
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'avatar'">
                    <a-avatar :src="record.avatar" :alt="record.name" size="small">
                      {{ record.name.substring(0, 1) }}
                    </a-avatar>
                  </template>
                </template>
              </a-table>
            </div>
          </a-col>
        </a-row>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import type { TablePaginationConfig } from 'ant-design-vue';
import { useDepartmentStore } from '@/stores/department';
import { useTeacherStore } from '@/stores/teacher';
import { useRoleStore } from '@/stores/role';

const departmentStore = useDepartmentStore();
const teacherStore = useTeacherStore();
const roleStore = useRoleStore();

// 表格数据
const columns = [
  {
    title: '头像',
    dataIndex: 'avatar',
    key: 'avatar',
    width: 80
  },
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    width: 120
  },
  {
    title: '工号',
    dataIndex: 'code',
    key: 'code',
    width: 120
  },
  {
    title: '性别',
    dataIndex: 'gender',
    key: 'gender',
    width: 80
  },
  {
    title: '所属部门',
    dataIndex: 'department',
    key: 'department',
    width: 200
  },
  {
    title: '手机号',
    dataIndex: 'phone',
    key: 'phone',
    width: 150
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    width: 200
  },
  {
    title: '操作',
    key: 'action',
    width: 100
  }
];

const tableData = ref<any[]>([]);
const loading = ref(false);
const searchValue = ref('');
const pagination = reactive<TablePaginationConfig>({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
});

// 选择行数据
const selectedRowKeys = ref<string[]>([]);
const selectedRows = ref<any[]>([]);
const rowSelection = {
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: string[], rows: any[]) => {
    selectedRowKeys.value = keys;
    selectedRows.value = rows;
  }
};

// 添加模态框相关
const addModalVisible = ref(false);
const addLoading = ref(false);
const treeData = ref<any[]>([]);
const addExpandedKeys = ref<string[]>([]);
const addSelectedKeys = ref<string[]>([]);
const addSelectedNode = ref<any>(null);
const addSearchValue = ref('');

// 添加模态框表格数据
const addColumns = [
  {
    title: '头像',
    dataIndex: 'avatar',
    key: 'avatar',
    width: 60
  },
  {
    title: '姓名',
    dataIndex: 'name',
    key: 'name',
    width: 100
  },
  {
    title: '工号',
    dataIndex: 'code',
    key: 'code',
    width: 100
  },
  {
    title: '部门',
    dataIndex: 'department',
    key: 'department'
  }
];

const addTableData = ref<any[]>([]);
const addPagination = reactive<TablePaginationConfig>({
  current: 1,
  pageSize: 5,
  total: 0,
  showSizeChanger: true,
  size: 'small',
  showTotal: (total) => `共 ${total} 条`
});

// 添加模态框选择行数据
const addSelectedRowKeys = ref<string[]>([]);
const addSelectedRows = ref<any[]>([]);
const addRowSelection = {
  selectedRowKeys: addSelectedRowKeys.value,
  onChange: (keys: string[], rows: any[]) => {
    addSelectedRowKeys.value = keys;
    addSelectedRows.value = rows;
  }
};

// 加载系统管理员列表
const loadTableData = async () => {
  try {
    loading.value = true;
    
    const params = {
      page: pagination.current || 1,
      pageSize: pagination.pageSize || 10,
      keyword: searchValue.value
    };
    
    const result = await roleStore.getAdminList(params);
    tableData.value = result.items;
    pagination.total = result.total;
  } catch (error) {
    message.error('加载数据失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 表格变化处理
const handleTableChange = async (pag: TablePaginationConfig) => {
  pagination.current = pag.current || 1;
  pagination.pageSize = pag.pageSize || 10;
  await loadTableData();
};

// 搜索处理
const onSearch = async () => {
  pagination.current = 1;
  await loadTableData();
};

// 删除管理员授权
const handleDelete = async (record: any) => {
  try {
    await roleStore.removeAdmin(record.id);
    message.success('移除管理员授权成功');
    await loadTableData();
  } catch (error) {
    message.error('操作失败');
    console.error(error);
  }
};

// 批量删除管理员授权
const confirmBatchDelete = async () => {
  try {
    await roleStore.batchRemoveAdmin(selectedRowKeys.value);
    message.success('批量移除管理员授权成功');
    selectedRowKeys.value = [];
    selectedRows.value = [];
    await loadTableData();
  } catch (error) {
    message.error('操作失败');
    console.error(error);
  }
};

// 显示添加模态框
const showAddModal = async () => {
  addModalVisible.value = true;
  addSearchValue.value = '';
  addSelectedRowKeys.value = [];
  addSelectedRows.value = [];
  
  // 加载组织树
  await loadTreeData();
  
  // 默认选中学校节点
  if (treeData.value.length > 0) {
    const schoolKey = treeData.value[0].key;
    addExpandedKeys.value = [schoolKey];
    addSelectedKeys.value = [schoolKey];
    addSelectedNode.value = {
      key: schoolKey,
      nodeType: 'school',
      title: treeData.value[0].title
    };
    
    // 加载教师列表
    await loadAddTableData();
  }
};

// 加载组织树数据
const loadTreeData = async () => {
  try {
    const result = await departmentStore.getOrganizationTree();
    treeData.value = result;
  } catch (error) {
    message.error('加载组织架构失败');
    console.error(error);
  }
};

// 当选择组织树节点时
const onAddTreeSelect = async (keys: string[], info: any) => {
  if (keys.length === 0) return;
  
  addSelectedNode.value = {
    key: keys[0],
    nodeType: info.node.nodeType,
    title: info.node.title
  };
  
  // 重置分页
  addPagination.current = 1;
  // 清空选中行
  addSelectedRowKeys.value = [];
  addSelectedRows.value = [];
  
  // 加载教师列表
  await loadAddTableData();
};

// 添加模态框搜索
const onAddSearch = async () => {
  addPagination.current = 1;
  await loadAddTableData();
};

// 添加模态框表格变化
const handleAddTableChange = async (pag: TablePaginationConfig) => {
  addPagination.current = pag.current || 1;
  addPagination.pageSize = pag.pageSize || 5;
  await loadAddTableData();
};

// 加载添加模态框教师列表
const loadAddTableData = async () => {
  if (!addSelectedNode.value) return;
  
  try {
    addLoading.value = true;
    
    const { key } = addSelectedNode.value;
    const params = {
      organizationId: key,
      page: addPagination.current || 1,
      pageSize: addPagination.pageSize || 5,
      keyword: addSearchValue.value
    };
    
    const result = await teacherStore.getTeacherList(params);
    
    // 从结果中过滤掉已经是管理员的教师
    const adminIds = await roleStore.getAdminIds();
    addTableData.value = result.items.filter(item => !adminIds.includes(item.id));
    addPagination.total = addTableData.value.length;
  } catch (error) {
    message.error('加载数据失败');
    console.error(error);
  } finally {
    addLoading.value = false;
  }
};

// 处理添加确认
const handleAddOk = async () => {
  if (addSelectedRowKeys.value.length === 0) {
    message.warning('请选择要授权的教师');
    return;
  }
  
  try {
    addLoading.value = true;
    
    await roleStore.addAdmin(addSelectedRowKeys.value);
    
    message.success('授权成功');
    addModalVisible.value = false;
    
    // 重新加载管理员列表
    await loadTableData();
  } catch (error) {
    message.error('授权失败');
    console.error(error);
  } finally {
    addLoading.value = false;
  }
};

// 处理添加取消
const handleAddCancel = () => {
  addModalVisible.value = false;
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadTableData();
});
</script>

<style scoped>
.role-container {
  background-color: #f0f2f5;
  padding: 0;
}

.role-content {
  margin-top: 24px;
}

.operation-area {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.left-operations {
  display: flex;
  gap: 8px;
}

.right-operations {
  display: flex;
  gap: 8px;
}

.batch-operations {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.danger-text {
  color: #ff4d4f;
}

.add-modal-content {
  max-height: 600px;
}

.org-tree-container {
  border-right: 1px solid #f0f0f0;
  padding-right: 16px;
  height: 400px;
  overflow: auto;
}

.teacher-list-container {
  padding-left: 8px;
  height: 400px;
  display: flex;
  flex-direction: column;
}
</style> 