<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell. Routed teacher list is system/teacher-management.vue -->
  <div class="admin-page">
    <PageHeaderBar title="教师管理" subtitle="管理学校教师用户信息">
      <template #actions>
        <a-button type="primary" @click="handleAdd">添加</a-button>
        <a-button @click="showImportModal">人员导入</a-button>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
          <a-input-search
            v-model:value="searchValue"
            placeholder="搜索姓名/工号"
            style="width: 250px"
            @search="onSearch"
          />
        </Stack>
      </template>
    </PageHeaderBar>

    <div class="teacher-content">
      <a-row :gutter="16">
        <!-- 左侧组织树 -->
        <a-col :span="6">
          <a-card title="组织架构" :bordered="false">
            <a-tree
              v-model:expandedKeys="expandedKeys"
              v-model:selectedKeys="selectedKeys"
              :tree-data="treeData"
              @select="onSelect"
            />
          </a-card>
        </a-col>
        
        <!-- 右侧列表和操作 -->
        <a-col :span="18">
          <a-card :bordered="false">
            <!-- 表格 -->
            <a-table
              :columns="columns"
              :data-source="tableData"
              :row-selection="rowSelection"
              :pagination="pagination"
              @change="handleTableChange"
              :loading="loading"
              row-key="id"
              :scroll="{ x: 1100 }"
            >
              <template #emptyText>
                <EmptyStateBlock description="暂无教师数据" />
              </template>
              <!-- 操作列 -->
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a @click="handleEdit(record)">编辑</a>
                    <a-divider type="vertical" />
                    <a-popconfirm
                      title="删除后将清除该用户创建的课堂及优秀作业等数据，是否确定删除该用户?"
                      ok-text="确定"
                      cancel-text="取消"
                      @confirm="handleDelete(record)"
                    >
                      <a class="danger-text">删除</a>
                    </a-popconfirm>
                  </a-space>
                </template>
                <!-- 状态显示 -->
                <template v-else-if="column.key === 'status'">
                  <a-badge :status="record.status ? 'success' : 'default'" />
                  <span>{{ record.status ? '在职' : '离职' }}</span>
                </template>
                <!-- 性别 -->
                <template v-else-if="column.key === 'gender'">
                  {{ record.gender === 'male' ? '男' : record.gender === 'female' ? '女' : '未知' }}
                </template>
                <!-- 头像 -->
                <template v-else-if="column.key === 'avatar'">
                  <a-avatar :src="record.avatar" :alt="record.name">
                    {{ record.name.substring(0, 1) }}
                  </a-avatar>
                </template>
              </template>
            </a-table>
            
            <!-- 批量操作按钮 -->
            <div class="batch-operations" v-if="selectedRowKeys.length > 0">
              <a-button 
                type="primary" 
                danger 
                @click="showDeleteConfirm"
              >
                批量删除
              </a-button>
              <a-button 
                @click="batchOperation('enable')"
              >
                批量启用
              </a-button>
              <a-button 
                @click="batchOperation('disable')"
              >
                批量停用
              </a-button>
              <a-button 
                @click="showTransferModal"
              >
                人员调动
              </a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
    
    <!-- 导入模态框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="人员导入"
      @ok="handleImportOk"
      @cancel="handleImportCancel"
      :confirm-loading="importLoading"
    >
      <div class="import-modal-content">
        <p>请下载模板，填写后上传</p>
        <a-button type="link" @click="downloadTemplate">下载模板</a-button>
        
        <a-upload
          name="file"
          :multiple="false"
          :file-list="importFileList"
          :before-upload="beforeImportUpload"
          @change="handleImportChange"
          accept=".xlsx,.xls"
        >
          <a-button>
            <upload-outlined /> 选择文件
          </a-button>
        </a-upload>
      </div>
    </a-modal>
    
    <!-- 批量删除确认 -->
    <a-modal
      v-model:open="deleteConfirmVisible"
      title="确认删除"
      @ok="confirmBatchDelete"
      @cancel="cancelBatchDelete"
      :ok-button-props="{ danger: true }"
      ok-text="删除"
      cancel-text="取消"
    >
      <p>删除后将清除所选用户创建的课堂及优秀作业等数据，是否确定删除所选用户?</p>
    </a-modal>
    
    <!-- 批量启用/停用确认 -->
    <a-modal
      v-model:open="statusConfirmVisible"
      :title="statusOperation === 'enable' ? '确认启用' : '确认停用'"
      @ok="confirmStatusChange"
      @cancel="cancelStatusChange"
    >
      <p v-if="statusOperation === 'enable'">是否确定启用所选用户？</p>
      <p v-else>是否确定停用所选用户？</p>
    </a-modal>
    
    <!-- 人员调动 -->
    <a-modal
      v-model:open="transferModalVisible"
      title="人员调动"
      @ok="handleTransferOk"
      @cancel="handleTransferCancel"
      :confirm-loading="transferLoading"
      width="600px"
    >
      <div class="transfer-modal-content">
        <p>请选择要调入的组织：</p>
        <a-tree
          v-model:expandedKeys="transferExpandedKeys"
          v-model:selectedKeys="transferSelectedKeys"
          :tree-data="treeData"
          @select="onTransferSelect"
        />
        <p style="margin-top: 16px;">
          已选择 <span style="color: #1890ff;">{{ selectedRowKeys.length }}</span> 人调入 
          <span style="color: #1890ff;">{{ transferTargetName || '请选择' }}</span>
        </p>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import { useRouter } from 'vue-router';
import type { TablePaginationConfig } from 'ant-design-vue';
import { useDepartmentStore } from '@/stores/department';
import { useTeacherStore } from '@/stores/teacher';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

const router = useRouter();
const departmentStore = useDepartmentStore();
const teacherStore = useTeacherStore();

// 树形数据
const treeData = ref<any[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const selectedNode = ref<any>(null);

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
    title: '状态',
    dataIndex: 'status',
    key: 'status',
    width: 100
  },
  {
    title: '操作',
    key: 'action',
    width: 120,
    fixed: 'right'
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

// 导入相关
const importModalVisible = ref(false);
const importLoading = ref(false);
const importFileList = ref<any[]>([]);

// 批量删除确认
const deleteConfirmVisible = ref(false);

// 批量启用/停用确认
const statusConfirmVisible = ref(false);
const statusOperation = ref<'enable' | 'disable'>('enable');

// 人员调动
const transferModalVisible = ref(false);
const transferLoading = ref(false);
const transferExpandedKeys = ref<string[]>([]);
const transferSelectedKeys = ref<string[]>([]);
const transferTargetId = ref<string | null>(null);
const transferTargetName = ref<string | null>(null);

// 加载组织树数据
const loadTreeData = async () => {
  try {
    loading.value = true;
    const result = await departmentStore.getOrganizationTree();
    treeData.value = result;
    
    // 默认展开和选中学校节点
    if (treeData.value.length > 0) {
      const schoolKey = treeData.value[0].key;
      expandedKeys.value = [schoolKey];
      selectedKeys.value = [schoolKey];
      selectedNode.value = {
        key: schoolKey,
        nodeType: 'school',
        title: treeData.value[0].title
      };
      
      // 加载学校下的教师列表
      await loadTableData();
    }
  } catch (error) {
    message.error('加载组织架构失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 加载表格数据
const loadTableData = async () => {
  if (!selectedNode.value) return;
  
  try {
    loading.value = true;
    
    const { nodeType, key } = selectedNode.value;
    const params = {
      organizationId: key,
      page: pagination.current,
      pageSize: pagination.pageSize,
      keyword: searchValue.value
    };
    
    const result = await teacherStore.getTeacherList(params);
    tableData.value = result.items;
    pagination.total = result.total;
  } catch (error) {
    message.error('加载数据失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 当选择树节点时
const onSelect = async (keys: string[], info: any) => {
  if (keys.length === 0) return;
  
  selectedNode.value = {
    key: keys[0],
    nodeType: info.node.nodeType,
    title: info.node.title
  };
  
  // 重置分页
  pagination.current = 1;
  // 清空搜索
  searchValue.value = '';
  // 清空选中行
  selectedRowKeys.value = [];
  selectedRows.value = [];
  
  // 加载表格数据
  await loadTableData();
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

// 添加教师
const handleAdd = () => {
  router.push('/admin/user/teacher/add');
};

// 编辑教师
const handleEdit = (record: any) => {
  router.push(`/admin/user/teacher/edit/${record.id}`);
};

// 删除教师
const handleDelete = async (record: any) => {
  try {
    await teacherStore.deleteTeacher(record.id);
    message.success('删除成功');
    await loadTableData();
  } catch (error) {
    message.error('删除失败');
    console.error(error);
  }
};

// 显示导入模态框
const showImportModal = () => {
  importModalVisible.value = true;
  importFileList.value = [];
};

// 下载导入模板
const downloadTemplate = () => {
  // 实际项目中，这里应该提供一个下载模板的链接
  message.info('正在下载模板...');
  // window.open('/api/teacher/template', '_blank');
};

// 上传前检查
const beforeImportUpload = (file: File) => {
  const isExcel = file.type === 'application/vnd.ms-excel' || 
                  file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  if (!isExcel) {
    message.error('只能上传Excel文件!');
    return false;
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    message.error('文件大小不能超过10MB!');
    return false;
  }
  
  return true;
};

// 处理导入文件变化
const handleImportChange = (info: any) => {
  importFileList.value = info.fileList.slice(-1);
};

// 处理导入确认
const handleImportOk = async () => {
  if (importFileList.value.length === 0) {
    message.warning('请选择要导入的文件');
    return;
  }
  
  try {
    importLoading.value = true;
    
    // 在实际项目中，这里应该调用上传API
    // const formData = new FormData();
    // formData.append('file', importFileList.value[0].originFileObj);
    // await teacherStore.importTeachers(formData);
    
    // 模拟上传成功
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    message.success('教师导入成功');
    importModalVisible.value = false;
    importFileList.value = [];
    
    // 重新加载数据
    await loadTableData();
  } catch (error) {
    message.error('导入失败');
    console.error(error);
  } finally {
    importLoading.value = false;
  }
};

// 处理导入取消
const handleImportCancel = () => {
  importModalVisible.value = false;
  importFileList.value = [];
};

// 显示批量删除确认
const showDeleteConfirm = () => {
  deleteConfirmVisible.value = true;
};

// 确认批量删除
const confirmBatchDelete = async () => {
  try {
    await teacherStore.batchDeleteTeachers(selectedRowKeys.value);
    message.success('批量删除成功');
    selectedRowKeys.value = [];
    selectedRows.value = [];
    deleteConfirmVisible.value = false;
    await loadTableData();
  } catch (error) {
    message.error('批量删除失败');
    console.error(error);
  }
};

// 取消批量删除
const cancelBatchDelete = () => {
  deleteConfirmVisible.value = false;
};

// 批量操作（启用/停用）
const batchOperation = (operation: 'enable' | 'disable') => {
  statusOperation.value = operation;
  statusConfirmVisible.value = true;
};

// 确认状态变更
const confirmStatusChange = async () => {
  try {
    const status = statusOperation.value === 'enable';
    await teacherStore.batchUpdateTeacherStatus(selectedRowKeys.value, status);
    message.success(`批量${status ? '启用' : '停用'}成功`);
    selectedRowKeys.value = [];
    selectedRows.value = [];
    statusConfirmVisible.value = false;
    await loadTableData();
  } catch (error) {
    message.error(`批量${statusOperation.value}失败`);
    console.error(error);
  }
};

// 取消状态变更
const cancelStatusChange = () => {
  statusConfirmVisible.value = false;
};

// 显示人员调动模态框
const showTransferModal = () => {
  transferModalVisible.value = true;
  transferExpandedKeys.value = expandedKeys.value;
  transferSelectedKeys.value = [];
  transferTargetId.value = null;
  transferTargetName.value = null;
};

// 当选择调动目标组织时
const onTransferSelect = (keys: string[], info: any) => {
  if (keys.length === 0) return;
  
  transferTargetId.value = keys[0];
  transferTargetName.value = info.node.title;
};

// 处理人员调动确认
const handleTransferOk = async () => {
  if (!transferTargetId.value) {
    message.warning('请选择要调入的组织');
    return;
  }
  
  try {
    transferLoading.value = true;
    
    await teacherStore.transferTeachers(selectedRowKeys.value, transferTargetId.value);
    
    message.success('人员调动成功');
    transferModalVisible.value = false;
    selectedRowKeys.value = [];
    selectedRows.value = [];
    
    // 重新加载数据
    await loadTableData();
  } catch (error) {
    message.error('人员调动失败');
    console.error(error);
  } finally {
    transferLoading.value = false;
  }
};

// 取消人员调动
const handleTransferCancel = () => {
  transferModalVisible.value = false;
};

// 组件挂载时加载数据
onMounted(async () => {
  await loadTreeData();
});
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.teacher-content {
  margin-top: 0;
}

.batch-operations {
  margin-top: var(--hx-space-4);
  display: flex;
  gap: var(--hx-space-2);
}

.danger-text {
  color: var(--hx-color-error);
}

.import-modal-content {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-4);
}

.transfer-modal-content {
  max-height: 400px;
  overflow-y: auto;
}
</style> 