<template>
  <div class="student-management">
    <a-page-header title="学生管理测试页面" subtitle="使用Ant Design组件和Pinia状态管理" />
    
    <div class="content-container">
      <!-- 顶部操作栏 -->
      <a-card :bordered="false" class="action-card">
        <a-space>
          <a-button type="primary" @click="showAddModal">
            <template #icon><plus-outlined /></template>
            添加学生
          </a-button>
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索姓名或学号"
            style="width: 250px"
            @search="handleSearch"
          />
        </a-space>
      </a-card>
      
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-card>
              <template #title>
                <team-outlined /> 学生总数
              </template>
              <div class="stats-number">{{ studentStore.totalStudents }}</div>
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card>
              <template #title>
                <man-outlined /> 性别分布
              </template>
              <div class="stats-chart">
                <div>男生: {{ studentStore.genderStats.male }}</div>
                <div>女生: {{ studentStore.genderStats.female }}</div>
                <a-progress 
                  :percent="studentStore.totalStudents ? 
                    Math.round(studentStore.genderStats.male / studentStore.totalStudents * 100) : 0" 
                  :success="{ percent: studentStore.totalStudents ? 
                    Math.round(studentStore.genderStats.female / studentStore.totalStudents * 100) : 0 }"
                  size="small"
                />
              </div>
            </a-card>
          </a-col>
          <a-col :span="8">
            <a-card>
              <template #title>
                <read-outlined /> 专业分布
              </template>
              <a-spin v-if="studentStore.loading" />
              <div v-else class="major-stats">
                <div v-for="(count, major) in studentStore.majorStats" :key="major" class="major-item">
                  {{ major }}: {{ count }}
                </div>
              </div>
            </a-card>
          </a-col>
        </a-row>
      </div>
      
      <!-- 学生数据表格 -->
      <a-card :bordered="false" title="学生列表" class="table-card">
        <a-table
          :columns="columns"
          :data-source="studentStore.students"
          :pagination="pagination"
          :loading="studentStore.loading"
          row-key="id"
          @change="handleTableChange"
        >
          <!-- 操作列 -->
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-space>
                <a @click="handleEdit(record)">编辑</a>
                <a-divider type="vertical" />
                <a-popconfirm
                  title="确定要删除这个学生吗?"
                  ok-text="确定"
                  cancel-text="取消"
                  @confirm="handleDelete(record.id)"
                >
                  <a class="danger-link">删除</a>
                </a-popconfirm>
              </a-space>
            </template>
            
            <!-- 性别列 -->
            <template v-else-if="column.key === 'gender'">
              <a-tag :color="record.gender === 'male' ? 'blue' : 'pink'">
                {{ record.gender === 'male' ? '男' : '女' }}
              </a-tag>
            </template>
            
            <!-- 状态列 -->
            <template v-else-if="column.key === 'status'">
              <a-badge :status="record.status ? 'success' : 'error'" />
              <span>{{ record.status ? '在读' : '已毕业' }}</span>
            </template>
            
            <!-- 头像列 -->
            <template v-else-if="column.key === 'avatar'">
              <a-avatar :src="record.avatar">
                {{ record.name ? record.name.substring(0, 1) : 'U' }}
              </a-avatar>
            </template>
          </template>
        </a-table>
      </a-card>
    </div>
    
    <!-- 添加/编辑学生表单 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑学生信息' : '添加新学生'"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
      :confirm-loading="modalLoading"
    >
      <a-form
        ref="formRef"
        :model="studentForm"
        :rules="formRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="姓名" name="name">
          <a-input v-model:value="studentForm.name" placeholder="请输入姓名" />
        </a-form-item>
        
        <a-form-item label="学号" name="studentId">
          <a-input v-model:value="studentForm.studentId" placeholder="请输入学号" />
        </a-form-item>
        
        <a-form-item label="性别" name="gender">
          <a-radio-group v-model:value="studentForm.gender">
            <a-radio value="male">男</a-radio>
            <a-radio value="female">女</a-radio>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="专业" name="major">
          <a-input v-model:value="studentForm.major" placeholder="请输入专业" />
        </a-form-item>
        
        <a-form-item label="班级" name="class">
          <a-input v-model:value="studentForm.class" placeholder="请输入班级" />
        </a-form-item>
        
        <a-form-item label="入学年份" name="enrollYear">
          <a-date-picker 
            v-model:value="studentForm.enrollYearDate" 
            picker="year" 
            style="width: 100%"
            @change="handleEnrollYearChange"
          />
        </a-form-item>
        
        <a-form-item label="电话" name="phone">
          <a-input v-model:value="studentForm.phone" placeholder="请输入电话号码" />
        </a-form-item>
        
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="studentForm.email" placeholder="请输入邮箱地址" />
        </a-form-item>
        
        <a-form-item label="状态" name="status">
          <a-switch v-model:checked="studentForm.status" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue';
import { 
  PlusOutlined, 
  TeamOutlined, 
  ManOutlined, 
  ReadOutlined 
} from '@ant-design/icons-vue';
import { useStudentStore, type Student } from '@/stores/student';
import type { FormInstance } from 'ant-design-vue';
import dayjs from 'dayjs';
import { message } from 'ant-design-vue';

// 初始化学生仓库
const studentStore = useStudentStore();

// 搜索相关
const searchKeyword = ref('');
const handleSearch = (value: string) => {
  searchKeyword.value = value;
  studentStore.keyword = value;
  studentStore.fetchStudents(value);
};

// 表格相关
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
    width: 100,
    sorter: (a: Student, b: Student) => a.name.localeCompare(b.name)
  },
  {
    title: '学号',
    dataIndex: 'studentId',
    key: 'studentId',
    width: 120
  },
  {
    title: '性别',
    dataIndex: 'gender',
    key: 'gender',
    width: 80
  },
  {
    title: '专业',
    dataIndex: 'major',
    key: 'major',
    width: 150
  },
  {
    title: '班级',
    dataIndex: 'class',
    key: 'class',
    width: 100
  },
  {
    title: '入学年份',
    dataIndex: 'enrollYear',
    key: 'enrollYear',
    width: 100,
    sorter: (a: Student, b: Student) => a.enrollYear - b.enrollYear
  },
  {
    title: '电话',
    dataIndex: 'phone',
    key: 'phone',
    width: 120
  },
  {
    title: '邮箱',
    dataIndex: 'email',
    key: 'email',
    width: 180
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
    fixed: 'right',
    width: 120
  }
];

// 分页相关
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: computed(() => studentStore.students.length),
  showTotal: (total: number) => `共 ${total} 条数据`
});

const handleTableChange = (pag: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
};

// 添加/编辑学生相关
const modalVisible = ref(false);
const modalLoading = ref(false);
const isEdit = ref(false);
const formRef = ref<FormInstance>();

// 表单校验规则
const formRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  studentId: [{ required: true, message: '请输入学号', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  major: [{ required: true, message: '请输入专业', trigger: 'blur' }],
  class: [{ required: true, message: '请输入班级', trigger: 'blur' }],
  enrollYear: [{ required: true, message: '请选择入学年份', trigger: 'change' }],
  phone: [{ required: true, message: '请输入电话号码', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ]
};

// 学生表单
const initialStudentForm = {
  name: '',
  studentId: '',
  gender: 'male' as 'male' | 'female',
  avatar: '',
  major: '',
  class: '',
  enrollYear: new Date().getFullYear(),
  enrollYearDate: null as any,
  phone: '',
  email: '',
  status: true,
  id: ''
};

const studentForm = reactive({...initialStudentForm});

// 监听入学年份变化
const handleEnrollYearChange = (value: any) => {
  if (value) {
    studentForm.enrollYear = value.year();
  }
};

// 显示添加学生模态框
const showAddModal = () => {
  isEdit.value = false;
  Object.assign(studentForm, initialStudentForm);
  studentForm.enrollYearDate = dayjs();
  modalVisible.value = true;
};

// 处理编辑
const handleEdit = (record: Student) => {
  isEdit.value = true;
  // 将记录复制到表单
  Object.assign(studentForm, {
    ...record,
    enrollYearDate: dayjs().year(record.enrollYear)
  });
  modalVisible.value = true;
};

// 处理删除
const handleDelete = async (id: string) => {
  const success = await studentStore.deleteStudent(id);
  if (success) {
    message.success('删除成功');
  }
};

// 模态框确认
const handleModalOk = async () => {
  try {
    await formRef.value?.validate();
    
    modalLoading.value = true;
    
    // 准备提交的数据
    const studentData: Partial<Student> = {
      name: studentForm.name,
      studentId: studentForm.studentId,
      gender: studentForm.gender,
      major: studentForm.major,
      class: studentForm.class,
      enrollYear: studentForm.enrollYear,
      phone: studentForm.phone,
      email: studentForm.email,
      status: studentForm.status
    };
    
    let success;
    if (isEdit.value) {
      success = await studentStore.updateStudent(
        studentForm.id as string, 
        studentData
      );
    } else {
      success = await studentStore.addStudent(studentData);
    }
    
    if (success) {
      modalVisible.value = false;
      message.success(isEdit.value ? '更新成功' : '添加成功');
    }
  } catch (error) {
    console.error('表单验证失败:', error);
  } finally {
    modalLoading.value = false;
  }
};

// 模态框取消
const handleModalCancel = () => {
  modalVisible.value = false;
};

// 组件加载时获取学生列表
onMounted(() => {
  studentStore.fetchStudents();
});
</script>

<style scoped>
.student-management {
  padding: 20px;
}

.content-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-card {
  margin-bottom: 16px;
}

.stats-cards {
  margin-bottom: 16px;
}

.stats-number {
  font-size: 32px;
  font-weight: bold;
  color: #1890ff;
  text-align: center;
}

.stats-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.major-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 100px;
  overflow-y: auto;
}

.major-item {
  display: flex;
  justify-content: space-between;
}

.danger-link {
  color: #ff4d4f;
}
</style> 