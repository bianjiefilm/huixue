<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar title="教师管理" :subtitle="`共 ${totalCount} 位教师`">
      <template #actions>
        <a-button type="primary" @click="showAddModal = true">
          <UserAddOutlined />
          添加教师
        </a-button>
        <a-button @click="handleImport">
          <ImportOutlined />
          人员导入
        </a-button>
        <a-dropdown>
          <a-button>
            更多操作
            <DownOutlined />
          </a-button>
          <template #overlay>
            <a-menu @click="handleMenuClick">
              <a-menu-item key="template">下载导入模板</a-menu-item>
              <a-menu-item key="export">导出数据</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="请输入姓名或工号"
            style="width: 220px"
            @search="handleSearch"
            allow-clear
          />
          <a-select
            v-model:value="filterCollege"
            placeholder="选择学院"
            allow-clear
            style="width: 160px"
          >
            <a-select-option value="">全部学院</a-select-option>
          </a-select>
          <a-select
            v-model:value="filterStatus"
            placeholder="选择状态"
            style="width: 120px"
          >
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="true">启用</a-select-option>
            <a-select-option value="false">停用</a-select-option>
          </a-select>
          <a-button type="primary" @click="handleSearch">搜索</a-button>
        </Stack>
      </template>
    </PageHeaderBar>

    <a-card :bordered="false">
      <!-- 批量操作区域 -->
      <div v-if="selectedRowKeys.length > 0" class="batch-actions">
        <a-space>
          <span>已选择 {{ selectedRowKeys.length }} 项</span>
          <a-button type="primary" @click="handleBatchEnable">批量启用</a-button>
          <a-button @click="handleBatchDisable">批量停用</a-button>
          <a-button danger @click="handleBatchDelete">批量删除</a-button>
        </a-space>
      </div>

      <!-- 教师列表表格 -->
      <a-table
        :columns="columns"
        :data-source="teacherList"
        :row-selection="rowSelection"
        :loading="loading"
        :pagination="paginationConfig"
        @change="handleTableChange"
        row-key="id"
      >
        <template #emptyText>
          <EmptyStateBlock description="暂无教师数据" />
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'red'">
              {{ record.is_active ? '启用' : '停用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'is_admin'">
            <a-tag v-if="record.is_admin" color="blue">管理员</a-tag>
            <span v-else>-</span>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">
                编辑
              </a-button>
              <a-button 
                type="link" 
                size="small" 
                :disabled="record.job_number === 'ttadmin' || record.job_number === 'admin'"
                @click="handleDelete(record)"
              >
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 添加/编辑教师弹窗 -->
    <a-modal
      v-model:open="showAddModal"
      :title="editingTeacher ? '编辑教师' : '添加教师'"
      width="600px"
      @ok="handleSaveTeacher"
      @cancel="handleCancelEdit"
    >
      <a-form
        ref="teacherForm"
        :model="teacherFormData"
        :rules="teacherFormRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="工号" name="job_number">
          <a-input 
            v-model:value="teacherFormData.job_number" 
            :disabled="!!editingTeacher"
            placeholder="请输入工号"
          />
        </a-form-item>
        <a-form-item label="姓名" name="name">
          <a-input v-model:value="teacherFormData.name" placeholder="请输入姓名" />
        </a-form-item>
        <a-form-item label="性别" name="gender">
          <a-select v-model:value="teacherFormData.gender" placeholder="请选择性别">
            <a-select-option value="男">男</a-select-option>
            <a-select-option value="女">女</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="联系电话" name="phone">
          <a-input v-model:value="teacherFormData.phone" placeholder="请输入联系电话" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="teacherFormData.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="职称" name="title">
          <a-input v-model:value="teacherFormData.title" placeholder="请输入职称" />
        </a-form-item>
        <a-form-item label="部门" name="department">
          <a-input v-model:value="teacherFormData.department" placeholder="请输入部门" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 导入弹窗 -->
    <a-modal
      v-model:open="showImportModal"
      title="批量导入教师"
      @ok="handleConfirmImport"
      @cancel="handleCancelImport"
    >
      <a-upload
        v-model:file-list="fileList"
        :before-upload="handleBeforeUpload"
        accept=".xlsx,.xls"
      >
        <a-button>
          <UploadOutlined />
          选择Excel文件
        </a-button>
      </a-upload>
      <p style="margin-top: 16px; color: #666;">
        请先下载模板，按照模板格式填写数据后上传
      </p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { 
  UserAddOutlined, 
  ImportOutlined, 
  DownOutlined,
  UploadOutlined 
} from '@ant-design/icons-vue';
import { 
  getTeachers, 
  createTeacher, 
  updateTeacher, 
  deleteTeacher,
  batchUpdateTeacherStatus,
  batchDeleteTeachers,
  importTeachers,
  downloadTeacherTemplate,
  type Teacher 
} from '@/api/system';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

// 响应式数据
const loading = ref(false);
const showAddModal = ref(false);
const showImportModal = ref(false);
const editingTeacher = ref<Teacher | null>(null);
const teacherList = ref<Teacher[]>([]);
const selectedRowKeys = ref<number[]>([]);
const totalCount = ref(0);
const fileList = ref([]);

// 搜索筛选
const searchKeyword = ref('');
const filterCollege = ref('');
const filterStatus = ref('');

// 分页配置
const currentPage = ref(1);
const pageSize = ref(20);

// 表单数据
const teacherFormData = reactive({
  job_number: '',
  name: '',
  gender: '',
  phone: '',
  email: '',
  title: '',
  department: '',
  school_id: 1 // 假设学校ID为1
});

// 表单验证规则
const teacherFormRules = {
  job_number: [{ required: true, message: '请输入工号' }],
  name: [{ required: true, message: '请输入姓名' }],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
};

// 表格列配置
const columns = [
  { title: '工号', dataIndex: 'job_number', key: 'job_number' },
  { title: '姓名', dataIndex: 'name', key: 'name' },
  { title: '性别', dataIndex: 'gender', key: 'gender' },
  { title: '联系电话', dataIndex: 'phone', key: 'phone' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '职称', dataIndex: 'title', key: 'title' },
  { title: '部门', dataIndex: 'department', key: 'department' },
  { title: '状态', dataIndex: 'is_active', key: 'is_active' },
  { title: '角色', dataIndex: 'is_admin', key: 'is_admin' },
  { title: '操作', key: 'action', width: 150 }
];

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys;
  },
  getCheckboxProps: (record: Teacher) => ({
    disabled: record.job_number === 'ttadmin' || record.job_number === 'admin'
  })
};

// 分页配置
const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: totalCount.value,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条记录`
}));

// 加载教师列表
const loadTeachers = async () => {
  loading.value = true;
  try {
    const params = {
      school_id: 1,
      search: searchKeyword.value || undefined,
      page: currentPage.value,
      page_size: pageSize.value
    };
    
    const response = await getTeachers(params);
    if (response.code === '0000') {
      teacherList.value = response.data.items;
      totalCount.value = response.data.total;
    } else {
      message.error(response.message || '加载教师列表失败');
    }
  } catch (error) {
    console.error('加载教师列表失败:', error);
    message.error('加载教师列表失败');
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadTeachers();
};

// 表格变化处理
const handleTableChange = (pagination: any) => {
  currentPage.value = pagination.current;
  pageSize.value = pagination.pageSize;
  loadTeachers();
};

// 编辑教师
const handleEdit = (record: Teacher) => {
  editingTeacher.value = record;
  Object.assign(teacherFormData, record);
  showAddModal.value = true;
};

// 删除教师
const handleDelete = (record: Teacher) => {
  Modal.confirm({
    title: '确认删除',
    content: '删除后将清除该用户创建的课堂及优秀作业等数据，是否确定删除该用户？',
    onOk: async () => {
      try {
        const response = await deleteTeacher(record.id);
        if (response.code === '0000') {
          message.success('删除成功');
          loadTeachers();
        } else {
          message.error(response.message || '删除失败');
        }
      } catch (error) {
        message.error('删除失败');
      }
    }
  });
};

// 保存教师
const handleSaveTeacher = async () => {
  try {
    if (editingTeacher.value) {
      // 编辑
      const response = await updateTeacher(editingTeacher.value.id, teacherFormData);
      if (response.code === '0000') {
        message.success('编辑成功');
        showAddModal.value = false;
        loadTeachers();
      } else {
        message.error(response.message || '编辑失败');
      }
    } else {
      // 新增
      const response = await createTeacher(teacherFormData);
      if (response.code === '0000') {
        message.success('添加成功');
        showAddModal.value = false;
        loadTeachers();
      } else {
        message.error(response.message || '添加失败');
      }
    }
  } catch (error) {
    message.error('保存失败');
  }
};

// 取消编辑
const handleCancelEdit = () => {
  showAddModal.value = false;
  editingTeacher.value = null;
  Object.keys(teacherFormData).forEach(key => {
    teacherFormData[key] = '';
  });
  teacherFormData.school_id = 1;
};

// 批量启用
const handleBatchEnable = async () => {
  try {
    const response = await batchUpdateTeacherStatus({
      ids: selectedRowKeys.value,
      is_active: true
    });
    if (response.code === '0000') {
      message.success('批量启用成功');
      selectedRowKeys.value = [];
      loadTeachers();
    }
  } catch (error) {
    message.error('批量启用失败');
  }
};

// 批量停用
const handleBatchDisable = async () => {
  try {
    const response = await batchUpdateTeacherStatus({
      ids: selectedRowKeys.value,
      is_active: false
    });
    if (response.code === '0000') {
      message.success('批量停用成功');
      selectedRowKeys.value = [];
      loadTeachers();
    }
  } catch (error) {
    message.error('批量停用失败');
  }
};

// 批量删除
const handleBatchDelete = () => {
  Modal.confirm({
    title: '确认删除',
    content: '删除后将清除所选用户创建的课堂及优秀作业等数据，是否确定删除所选用户？',
    onOk: async () => {
      try {
        const response = await batchDeleteTeachers(selectedRowKeys.value);
        if (response.code === '0000') {
          message.success('批量删除成功');
          selectedRowKeys.value = [];
          loadTeachers();
        }
      } catch (error) {
        message.error('批量删除失败');
      }
    }
  });
};

// 导入
const handleImport = () => {
  showImportModal.value = true;
};

// 确认导入
const handleConfirmImport = async () => {
  if (fileList.value.length === 0) {
    message.error('请选择要导入的文件');
    return;
  }

  try {
    const file = fileList.value[0].originFileObj;
    const response = await importTeachers(file, 1);
    
    if (response.code === '0000') {
      message.success(`导入成功：${response.data.success_count} 条，失败：${response.data.error_count} 条`);
      showImportModal.value = false;
      loadTeachers();
    }
  } catch (error) {
    message.error('导入失败');
  }
};

// 取消导入
const handleCancelImport = () => {
  showImportModal.value = false;
  fileList.value = [];
};

// 文件上传前处理
const handleBeforeUpload = () => {
  return false; // 阻止自动上传
};

// 菜单点击处理
const handleMenuClick = async ({ key }) => {
  if (key === 'template') {
    try {
      const blob = await downloadTeacherTemplate();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = '教师导入模板.xlsx';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      message.error('下载模板失败');
    }
  }
};

// 页面初始化
onMounted(() => {
  loadTeachers();
});
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.batch-actions {
  margin-bottom: var(--hx-space-4);
  padding: var(--hx-space-3) var(--hx-space-4);
  background: var(--hx-color-bg-hover);
  border-radius: var(--hx-radius-sm);
}
</style> 