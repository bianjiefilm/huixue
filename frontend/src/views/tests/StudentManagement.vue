<template>
  <div class="container">
    <div class="header">
      <h1>学生管理系统</h1>
    </div>
    
    <a-row :gutter="16" style="margin-bottom: 16px;">
      <a-col :span="6">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索学生姓名或学号"
          allow-clear
          @search="searchStudents"
        />
      </a-col>
      <a-col :span="18" style="text-align: right;">
        <a-button type="primary" @click="showAddModal">添加学生</a-button>
      </a-col>
    </a-row>
    
    <a-card class="card">
      <a-table
        :dataSource="students"
        :columns="columns"
        :loading="loading"
        :pagination="{ pageSize: 10 }"
        rowKey="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'avatar'">
            <a-avatar :src="record.avatar">
              {{ record.name.charAt(0) }}
            </a-avatar>
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" @click="showEditModal(record)">编辑</a-button>
              <a-popconfirm
                title="确定要删除此学生吗?"
                ok-text="确定"
                cancel-text="取消"
                @confirm="removeStudent(record.id)"
              >
                <a-button type="link" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 添加/编辑学生对话框 -->
    <a-modal
      :title="isEdit ? '编辑学生信息' : '添加新学生'"
      v-model:open="modalVisible"
      :confirm-loading="confirmLoading"
      @ok="handleModalOk"
      @cancel="handleModalCancel"
    >
      <a-form
        :model="formState"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="姓名" name="name">
          <a-input v-model:value="formState.name" />
        </a-form-item>
        <a-form-item label="学号" name="studentId">
          <a-input v-model:value="formState.studentId" />
        </a-form-item>
        <a-form-item label="性别" name="gender">
          <a-radio-group v-model:value="formState.gender">
            <a-radio value="male">男</a-radio>
            <a-radio value="female">女</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="专业" name="major">
          <a-input v-model:value="formState.major" />
        </a-form-item>
        <a-form-item label="班级" name="class">
          <a-input v-model:value="formState.class" />
        </a-form-item>
        <a-form-item label="入学年份" name="enrollYear">
          <a-input v-model:value="formState.enrollYear" />
        </a-form-item>
        <a-form-item label="手机号" name="phone">
          <a-input v-model:value="formState.phone" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formState.email" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted, computed } from 'vue';
import { useStudentStore } from '@/stores/student';
import { message } from 'ant-design-vue';

export default defineComponent({
  name: 'StudentManagement',
  
  setup() {
    const studentStore = useStudentStore();
    
    const searchKeyword = ref('');
    const modalVisible = ref(false);
    const confirmLoading = ref(false);
    const isEdit = ref(false);
    const currentId = ref('');
    
    const formState = reactive({
      name: '',
      studentId: '',
      gender: 'male',
      major: '',
      class: '',
      enrollYear: '2023',
      phone: '',
      email: ''
    });
    
    const columns = [
      {
        title: '头像',
        key: 'avatar',
        width: 80,
      },
      {
        title: '姓名',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: '学号',
        dataIndex: 'studentId',
        key: 'studentId',
      },
      {
        title: '性别',
        dataIndex: 'gender',
        key: 'gender',
        width: 80,
        customRender: ({ text }: { text: string }) => {
          return text === 'male' ? '男' : text === 'female' ? '女' : '其他';
        }
      },
      {
        title: '专业',
        dataIndex: 'major',
        key: 'major',
      },
      {
        title: '班级',
        dataIndex: 'class',
        key: 'class',
      },
      {
        title: '入学年份',
        dataIndex: 'enrollYear',
        key: 'enrollYear',
        width: 100,
      },
      {
        title: '联系方式',
        key: 'contact',
        customRender: ({ record }: { record: any }) => {
          return `${record.phone} / ${record.email}`;
        },
      },
      {
        title: '操作',
        key: 'action',
        width: 150,
      }
    ];
    
    // 计算属性：从 store 获取学生列表和加载状态
    const students = computed(() => studentStore.students);
    const loading = computed(() => studentStore.loading);
    
    onMounted(() => {
      studentStore.fetchStudents();
    });
    
    // 搜索学生
    const searchStudents = () => {
      studentStore.keyword = searchKeyword.value;
      studentStore.fetchStudents(searchKeyword.value);
    };
    
    // 显示添加学生对话框
    const showAddModal = () => {
      isEdit.value = false;
      resetForm();
      modalVisible.value = true;
    };
    
    // 显示编辑学生对话框
    const showEditModal = (record: any) => {
      isEdit.value = true;
      currentId.value = record.id;
      
      // 填充表单
      Object.keys(formState).forEach(key => {
        formState[key as keyof typeof formState] = record[key];
      });
      
      modalVisible.value = true;
    };
    
    // 处理对话框确认
    const handleModalOk = async () => {
      confirmLoading.value = true;
      
      try {
        let success;
        const studentData = {
          ...formState,
          gender: formState.gender as 'male' | 'female',
          enrollYear: parseInt(formState.enrollYear)
        };

        if (isEdit.value) {
          success = await studentStore.updateStudent(currentId.value, studentData);
        } else {
          success = await studentStore.addStudent(studentData);
        }
        
        if (success) {
          modalVisible.value = false;
          resetForm();
        }
      } finally {
        confirmLoading.value = false;
      }
    };
    
    // 处理对话框取消
    const handleModalCancel = () => {
      modalVisible.value = false;
      resetForm();
    };
    
    // 重置表单
    const resetForm = () => {
      Object.keys(formState).forEach(key => {
        formState[key as keyof typeof formState] = key === 'gender' ? 'male' : key === 'enrollYear' ? '2023' : '';
      });
      currentId.value = '';
    };
    
    // 删除学生
    const removeStudent = (id: string) => {
      studentStore.deleteStudent(id);
    };
    
    return {
      searchKeyword,
      students,
      loading,
      columns,
      modalVisible,
      confirmLoading,
      formState,
      isEdit,
      
      searchStudents,
      showAddModal,
      showEditModal,
      handleModalOk,
      handleModalCancel,
      removeStudent,
      resetForm
    };
  }
});
</script>

<style scoped>
:root {
  --background-color: #f5f5f5;
  --text-color: rgba(0, 0, 0, 0.85);
  --card-background: #fff;
  --border-color: #f0f0f0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.card {
  background-color: #fff;
  border-radius: 2px;
  transition: all 0.3s;
}
</style> 