<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar title="院系设置" subtitle="管理学校组织架构">
      <template #actions>
        <a-button
          type="primary"
          @click="showCreateModal"
          v-if="!selectedNode || selectedNode.nodeType !== 'class'"
        >
          {{ getCreateButtonText() }}
        </a-button>
        <a-button
          v-if="selectedNode && selectedNode.nodeType === 'school'"
          @click="showImportModal"
        >
          组织导入
        </a-button>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
          <a-input-search
            v-model:value="searchValue"
            placeholder="搜索名称或编码"
            style="width: 250px"
            @search="onSearch"
          />
        </Stack>
      </template>
    </PageHeaderBar>

    <div class="department-content">
      <a-row :gutter="16">
        <!-- 左侧组织树 -->
        <a-col :span="6">
          <a-card title="组织架构" :bordered="false" :loading="loading">
            <a-tree
              v-model:expandedKeys="expandedKeys"
              v-model:selectedKeys="selectedKeys"
              :tree-data="treeData"
              :show-line="true"
              @select="onSelect"
            >
              <template #title="{ title, nodeType }">
                <span>{{ title }}</span>
              </template>
            </a-tree>
            <EmptyStateBlock
              v-if="treeData.length === 0 && !loading"
              description="暂无组织架构数据"
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
                <EmptyStateBlock description="暂无院系数据" />
              </template>
              <!-- 操作列 -->
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'action'">
                  <a-space>
                    <a @click="editItem(record)">编辑</a>
                    <a-divider type="vertical" />
                    <a-popconfirm
                      title="确定要删除该组织吗？"
                      ok-text="确定"
                      cancel-text="取消"
                      @confirm="deleteItem(record)"
                    >
                      <a class="danger-text">删除</a>
                    </a-popconfirm>
                  </a-space>
                </template>
                <!-- 状态显示 -->
                <template v-else-if="column.key === 'status'">
                  <a-tag :color="record.status ? 'success' : 'default'">
                    {{ record.status ? '已启用' : '已停用' }}
                  </a-tag>
                </template>
              </template>
            </a-table>
            
            <!-- 批量操作按钮 -->
            <div class="batch-operations" v-if="selectedRowKeys.length > 0">
              <a-button 
                type="primary" 
                danger 
                @click="showDeleteConfirm"
                :disabled="!hasOperationPermission"
              >
                批量删除
              </a-button>
              <a-button 
                @click="batchOperation('enable')"
                :disabled="!hasOperationPermission"
              >
                批量启用
              </a-button>
              <a-button 
                @click="batchOperation('disable')"
                :disabled="!hasOperationPermission"
              >
                批量停用
              </a-button>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
    
    <!-- 新建/编辑模态框 -->
    <a-modal
      v-model:open="modalVisible"
      :title="modalTitle"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="modalLoading"
    >
      <a-form 
        :model="formState" 
        :rules="formRules"
        ref="formRef"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item name="name" label="名称">
          <a-input v-model:value="formState.name" placeholder="请输入名称" />
        </a-form-item>
        <a-form-item name="code" label="编码">
          <a-input v-model:value="formState.code" placeholder="请输入编码" />
        </a-form-item>
        <a-form-item name="description" label="描述">
          <a-textarea 
            v-model:value="formState.description" 
            placeholder="请输入描述" 
            :rows="3" 
          />
        </a-form-item>
        <!-- 专业特有字段 -->
        <template v-if="currentNodeType === 'major'">
          <a-form-item name="degreeType" label="学位类型">
            <a-select v-model:value="formState.degreeType" placeholder="请选择学位类型">
              <a-select-option value="bachelor">本科</a-select-option>
              <a-select-option value="master">硕士</a-select-option>
              <a-select-option value="doctor">博士</a-select-option>
            </a-select>
          </a-form-item>
        </template>
        <!-- 班级特有字段 -->
        <template v-if="currentNodeType === 'class'">
          <a-form-item name="year" label="入学年份">
            <a-date-picker 
              v-model:value="formState.year" 
              picker="year" 
              :disabled="!!editingRecord"
            />
          </a-form-item>
          <a-form-item name="headTeacher" label="班主任">
            <a-input v-model:value="formState.headTeacher" placeholder="请输入班主任姓名" />
          </a-form-item>
        </template>
      </a-form>
    </a-modal>
    
    <!-- 导入组织模态框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="组织导入"
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
      <p>删除后将清除该组织下所有人员，是否确定删除所选组织？</p>
    </a-modal>
    
    <!-- 批量启用/停用确认 -->
    <a-modal
      v-model:open="statusConfirmVisible"
      :title="statusOperation === 'enable' ? '确认启用' : '确认停用'"
      @ok="confirmStatusChange"
      @cancel="cancelStatusChange"
    >
      <p v-if="statusOperation === 'enable'">是否确定启用所选组织？</p>
      <p v-else>停用后该组织下所有组织机构和人员用户都将被停用，是否确定停用所选组织？</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import type { TablePaginationConfig } from 'ant-design-vue';
import { useDepartmentStore } from '@/stores/department';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

// 树形数据
const treeData = ref<any[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const selectedNode = ref<any>(null);

// 表格数据
const columns = ref<any[]>([]);
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

// 模态框数据
const modalVisible = ref(false);
const modalTitle = ref('');
const modalLoading = ref(false);
const formRef = ref();
const formState = reactive<any>({
  name: '',
  code: '',
  description: '',
  degreeType: '',
  year: null,
  headTeacher: ''
});
const formRules = {
  name: [{ required: true, message: '请输入名称' }],
  code: [{ required: true, message: '请输入编码' }]
};
const currentNodeType = ref('');
const editingRecord = ref<any>(null);

// 导入相关
const importModalVisible = ref(false);
const importLoading = ref(false);
const importFileList = ref<any[]>([]);

// 批量删除确认
const deleteConfirmVisible = ref(false);

// 批量启用/停用确认
const statusConfirmVisible = ref(false);
const statusOperation = ref<'enable' | 'disable'>('enable');

// 获取部门Store
const departmentStore = useDepartmentStore();

// 是否有操作权限
const hasOperationPermission = computed(() => {
  return selectedRowKeys.value.length > 0;
});

// 根据当前选中节点类型获取创建按钮文字
const getCreateButtonText = () => {
  if (!selectedNode.value) return '新建学院';
  
  switch (selectedNode.value.nodeType) {
    case 'school':
      return '新建学院';
    case 'college':
      return '新建专业';
    case 'major':
    case 'grade':
      return '新建班级';
    default:
      return '新建';
  }
};

// 根据当前选中节点更新表格列
const updateColumns = () => {
  const baseColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
      width: 200
    },
    {
      title: '编码',
      dataIndex: 'code',
      key: 'code',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100
    },
    {
      title: '创建时间',
      dataIndex: 'createTime',
      key: 'createTime',
      width: 180
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right'
    }
  ];
  
  if (!selectedNode.value || selectedNode.value.nodeType === 'school') {
    // 学院列表额外显示院系数量
    columns.value = [
      ...baseColumns.slice(0, 2),
      {
        title: '专业数量',
        dataIndex: 'majorCount',
        key: 'majorCount',
        width: 120
      },
      ...baseColumns.slice(2)
    ];
  } else if (selectedNode.value.nodeType === 'college') {
    // 专业列表额外显示学位类型
    columns.value = [
      ...baseColumns.slice(0, 2),
      {
        title: '学位类型',
        dataIndex: 'degreeType',
        key: 'degreeType',
        width: 120,
        customRender: ({ text }: { text: string }) => {
          const degreeMap: Record<string, string> = {
            bachelor: '本科',
            master: '硕士',
            doctor: '博士'
          };
          return degreeMap[text] || text;
        }
      },
      ...baseColumns.slice(2)
    ];
  } else if (selectedNode.value.nodeType === 'major' || selectedNode.value.nodeType === 'grade') {
    // 班级列表额外显示班主任、人数
    columns.value = [
      ...baseColumns.slice(0, 2),
      {
        title: '班主任',
        dataIndex: 'headTeacher',
        key: 'headTeacher',
        width: 120
      },
      {
        title: '学生人数',
        dataIndex: 'studentCount',
        key: 'studentCount',
        width: 120
      },
      ...baseColumns.slice(2)
    ];
  } else {
    columns.value = baseColumns;
  }
};

// 加载组织树数据
const loadTreeData = async () => {
  try {
    loading.value = true;
    console.log('[Department] 开始加载组织树数据...');
    console.log('[Department] departmentStore:', departmentStore);
    
    const result = await departmentStore.getOrganizationTree();
    console.log('[Department] 组织树数据加载结果:', result);
    console.log('[Department] 结果类型:', typeof result, '是否为数组:', Array.isArray(result));
    console.log('[Department] 结果长度:', Array.isArray(result) ? result.length : 0);
    
    if (!Array.isArray(result)) {
      console.error('[Department] 组织树数据不是数组:', result);
      message.error('组织树数据格式错误');
      return;
    }
    
    treeData.value = result;
    console.log('[Department] treeData已设置:', treeData.value);
    console.log('[Department] treeData长度:', treeData.value.length);
    
    // 默认展开和选中学校节点
    if (treeData.value.length > 0) {
      const schoolNode = treeData.value[0];
      const schoolKey = schoolNode.key;
      console.log('[Department] 学校节点:', schoolNode);
      console.log('[Department] 学校key:', schoolKey);
      
      expandedKeys.value = [schoolKey];
      selectedKeys.value = [schoolKey];
      selectedNode.value = {
        key: schoolKey,
        nodeType: 'school',
        title: schoolNode.title
      };
      console.log('[Department] 已选中学校节点:', selectedNode.value);
      console.log('[Department] expandedKeys:', expandedKeys.value);
      console.log('[Department] selectedKeys:', selectedKeys.value);
      
      // 加载学校下的学院列表
      await loadTableData();
    } else {
      console.warn('[Department] 组织树数据为空');
      message.warning('暂无组织架构数据');
    }
  } catch (error: any) {
    message.error('加载组织架构失败');
    console.error('[Department] 加载组织架构失败:', error);
    console.error('[Department] 错误详情:', error.message, error.stack);
    if (error.response) {
      console.error('[Department] 错误响应:', error.response.data);
    }
  } finally {
    loading.value = false;
    console.log('[Department] 组织树数据加载完成');
  }
};

// 加载表格数据
const loadTableData = async () => {
  if (!selectedNode.value) {
    console.warn('[Department] 未选中节点，无法加载表格数据');
    return;
  }
  
  try {
    loading.value = true;
    console.log('[Department] 开始加载表格数据，选中节点:', selectedNode.value);
    
    // 更新表格列
    updateColumns();
    
    const { nodeType, key } = selectedNode.value;
    
    // 从key中提取ID（格式：nodeType-id）
    let parentId: string | null = null;
    if (nodeType !== 'school') {
      const match = key.match(/-(\d+)$/);
      if (match) {
        parentId = match[1];
      }
    }
    // 如果是学校节点，parentId应该是null（表示获取顶级组织）
    
    const childType = getChildNodeType(nodeType);
    const params = {
      parentId: parentId,
      type: childType,
      page: pagination.current,
      pageSize: pagination.pageSize,
      keyword: searchValue.value
    };
    
    console.log('[Department] 组织列表查询参数:', params);
    
    const result = await departmentStore.getOrganizationList(params);
    console.log('[Department] 组织列表查询结果:', result);
    
    tableData.value = result.items;
    pagination.total = result.total;
    
    console.log('[Department] 表格数据已更新，条数:', result.items.length);
  } catch (error: any) {
    message.error('加载数据失败');
    console.error('[Department] 加载表格数据失败:', error);
    console.error('[Department] 错误详情:', error.message, error.stack);
    if (error.response) {
      console.error('[Department] 错误响应:', error.response.data);
    }
  } finally {
    loading.value = false;
  }
};

// 获取子节点类型
const getChildNodeType = (nodeType: string) => {
  switch (nodeType) {
    case 'school':
      return 'college';
    case 'college':
      return 'major';
    case 'major':
      return 'grade';
    case 'grade':
      return 'class';
    default:
      return '';
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

// 显示创建模态框
const showCreateModal = () => {
  if (!selectedNode.value) return;
  
  const nodeType = selectedNode.value.nodeType;
  currentNodeType.value = getChildNodeType(nodeType);
  editingRecord.value = null;
  
  // 重置表单
  formState.name = '';
  formState.code = '';
  formState.description = '';
  formState.degreeType = 'bachelor';
  formState.year = null;
  formState.headTeacher = '';
  
  modalTitle.value = getCreateButtonText();
  modalVisible.value = true;
};

// 编辑项目
const editItem = (record: any) => {
  editingRecord.value = record;
  currentNodeType.value = selectedNode.value.nodeType === 'school' ? 'college' :
                           selectedNode.value.nodeType === 'college' ? 'major' :
                           'class';
  
  // 填充表单数据
  formState.name = record.name;
  formState.code = record.code;
  formState.description = record.description || '';
  formState.degreeType = record.degreeType || 'bachelor';
  formState.year = record.year ? new Date(record.year) : null;
  formState.headTeacher = record.headTeacher || '';
  
  modalTitle.value = '编辑信息';
  modalVisible.value = true;
};

// 处理模态框确认
const handleModalOk = async () => {
  try {
    await formRef.value.validate();
    
    modalLoading.value = true;
    
    // 从 key 中提取数字 ID（格式：nodeType-id）
    const key = selectedNode.value.key;
    const nodeType = selectedNode.value.nodeType;
    let parentId: string | null = null;
    if (nodeType !== 'school') {
      const match = key.match(/-(\d+)$/);
      if (match) {
        parentId = match[1];
      }
    }
    
    // 获取子组织的类型（创建的是子组织，不是当前选中的组织类型）
    const childType = getChildNodeType(nodeType);
    // 转换为大写形式（后端期望大写枚举）
    const typeMap: Record<string, string> = {
      'college': 'COLLEGE',
      'major': 'MAJOR',
      'grade': 'GRADE',
      'class': 'CLASS'
    };
    
    const formData: any = {
      name: formState.name,
      code: formState.code,
      description: formState.description,
      parentId: parentId,
      type: typeMap[childType] || childType.toUpperCase()
    };
    
    // 添加类型特定字段
    if (currentNodeType.value === 'major') {
      formData.degreeType = formState.degreeType;
    } else if (currentNodeType.value === 'class') {
      formData.year = formState.year ? formState.year.getFullYear() : null;
      formData.headTeacher = formState.headTeacher;
    }
    
    // 创建或更新
    if (editingRecord.value) {
      await departmentStore.updateOrganization({
        ...formData,
        id: editingRecord.value.id
      });
      message.success('更新成功');
    } else {
      await departmentStore.createOrganization(formData);
      message.success('创建成功');
    }
    
    // 关闭模态框
    modalVisible.value = false;
    
    // 重新加载数据
    await loadTableData();
    
    // 如果是创建新组织，可能需要刷新树结构
    if (!editingRecord.value) {
      await loadTreeData();
    }
  } catch (error) {
    console.error('表单验证错误或提交失败:', error);
  } finally {
    modalLoading.value = false;
  }
};

// 处理模态框取消
const handleModalCancel = () => {
  modalVisible.value = false;
  formRef.value.resetFields();
};

// 删除单个项目
const deleteItem = async (record: any) => {
  try {
    await departmentStore.deleteOrganization(record.id);
    message.success('删除成功');
    await loadTableData();
    await loadTreeData();
  } catch (error) {
    if (error.response && error.response.data && error.response.data.message) {
      message.error(error.response.data.message);
    } else {
      message.error('删除失败');
    }
    console.error(error);
  }
};

// 显示批量删除确认
const showDeleteConfirm = () => {
  deleteConfirmVisible.value = true;
};

// 确认批量删除
const confirmBatchDelete = async () => {
  try {
    await departmentStore.batchDeleteOrganization(selectedRowKeys.value);
    message.success('批量删除成功');
    selectedRowKeys.value = [];
    selectedRows.value = [];
    deleteConfirmVisible.value = false;
    await loadTableData();
    await loadTreeData();
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
    await departmentStore.batchUpdateOrganizationStatus(selectedRowKeys.value, status);
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

// 显示导入模态框
const showImportModal = () => {
  importModalVisible.value = true;
  importFileList.value = [];
};

// 下载导入模板
const downloadTemplate = () => {
  // 实际项目中，这里应该提供一个下载模板的链接
  message.info('正在下载模板...');
  // window.open('/api/organization/template', '_blank');
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
    // await departmentStore.importOrganization(formData);
    
    // 模拟上传成功
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    message.success('组织导入成功');
    importModalVisible.value = false;
    importFileList.value = [];
    
    // 重新加载数据
    await loadTreeData();
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

// 组件挂载时加载数据
onMounted(async () => {
  await loadTreeData();
});
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.department-content {
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
</style> 