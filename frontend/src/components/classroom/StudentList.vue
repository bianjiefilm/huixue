<template>
  <div class="student-list-component">
    <!-- 搜索和工具栏 -->
    <div class="toolbar">
      <div class="search-area">
        <a-input-search
          v-model:value="searchKeyword"
          placeholder="搜索学生姓名或学号"
          style="width: 300px;"
          @search="handleSearch"
        />
      </div>
      <div class="actions">
        <a-button 
          v-if="!readOnly" 
          type="primary" 
          @click="$emit('add-student')"
          :disabled="loading"
        >
          <template #icon><plus-outlined /></template>
          添加学生
        </a-button>
        <a-button
          v-if="!readOnly && selectedRowKeys.length > 0"
          type="primary"
          danger
          @click="confirmRemoveSelected"
          :disabled="loading"
        >
          <template #icon><delete-outlined /></template>
          批量移除 ({{ selectedRowKeys.length }})
        </a-button>
      </div>
    </div>

    <!-- 学生表格 -->
    <a-table
      :dataSource="filteredStudents"
      :columns="columns"
      :rowKey="(record: Student) => record.id"
      :pagination="{ pageSize: 10, showSizeChanger: true, pageSizeOptions: ['10', '20', '50', '100'] }"
      :loading="loading"
      :rowSelection="!readOnly ? { selectedRowKeys, onChange: onSelectChange } : undefined"
      size="middle"
    >
      <!-- 学生头像 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'avatar'">
          <a-avatar :src="record.avatar" :alt="record.name">
            {{ record.name.substring(0, 1) }}
          </a-avatar>
        </template>
        
        <!-- 姓名展示 -->
        <template v-else-if="column.dataIndex === 'name'">
          <div class="student-name">
            {{ record.name }}
            <a-tag v-if="record.gender === '男'" color="blue">男</a-tag>
            <a-tag v-else-if="record.gender === '女'" color="pink">女</a-tag>
          </div>
        </template>
        
        <!-- 专业和班级 -->
        <template v-else-if="column.dataIndex === 'major'">
          <div>
            <div>{{ record.major || '未设置专业' }}</div>
            <div class="text-secondary">{{ record.class || '未设置班级' }}</div>
          </div>
        </template>
        
        <!-- 入学年份 -->
        <template v-else-if="column.dataIndex === 'enrollYear'">
          {{ record.enrollYear || '未知' }}级
        </template>
        
        <!-- 操作按钮 -->
        <template v-else-if="column.dataIndex === 'action'">
          <div class="action-buttons">
            <a-button type="link" size="small" @click="viewStudentDetail(record)">查看</a-button>
            <a-button v-if="!readOnly" type="link" size="small" danger @click="confirmRemoveStudent(record)">移除</a-button>
          </div>
        </template>
      </template>
      
      <!-- 空状态 -->
      <template #emptyText>
        <a-empty :description="searchKeyword ? '未找到匹配的学生' : '暂无学生数据'" />
      </template>
    </a-table>
    
    <!-- 移除确认对话框 -->
    <a-modal
      v-model:open="removeConfirmVisible"
      title="移除学生"
      :confirm-loading="confirmLoading"
      @ok="handleRemoveConfirm"
      @cancel="cancelRemove"
    >
      <p v-if="selectedRowKeys.length > 0 && batchRemove">
        确定要从课堂中移除选中的 <strong>{{ selectedRowKeys.length }}</strong> 名学生吗？
      </p>
      <p v-else-if="currentStudent">
        确定要从课堂中移除学生 <strong>{{ currentStudent.name }}</strong> 吗？
      </p>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import type { Student } from '@/types/classroom';
import type { TableColumnsType } from 'ant-design-vue';

// 组件属性
const props = defineProps({
  students: {
    type: Array as () => Student[],
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  readOnly: {
    type: Boolean,
    default: false
  }
});

// 组件事件
const emit = defineEmits(['add-student', 'remove-student', 'view-student', 'search']);

// 组件状态
const searchKeyword = ref('');
const selectedRowKeys = ref<string[]>([]);
const removeConfirmVisible = ref(false);
const confirmLoading = ref(false);
const currentStudent = ref<Student | null>(null);
const batchRemove = ref(false);

// 表格列定义
const columns = computed<TableColumnsType>(() => [
  {
    title: '头像',
    dataIndex: 'avatar',
    width: 80
  },
  {
    title: '姓名',
    dataIndex: 'name',
    width: 150
  },
  {
    title: '学号',
    dataIndex: 'studentId',
    width: 150
  },
  {
    title: '专业/班级',
    dataIndex: 'major',
    width: 200
  },
  {
    title: '入学年份',
    dataIndex: 'enrollYear',
    width: 100
  },
  {
    title: '联系方式',
    dataIndex: 'phone',
    width: 150
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 120,
    fixed: 'right'
  }
]);

// 过滤后的学生列表
const filteredStudents = computed(() => {
  if (!searchKeyword.value) {
    return props.students;
  }
  
  const keyword = searchKeyword.value.toLowerCase();
  return props.students.filter(student => 
    student.name.toLowerCase().includes(keyword) ||
    student.studentId.toLowerCase().includes(keyword) ||
    (student.major && student.major.toLowerCase().includes(keyword)) ||
    (student.class && student.class.toLowerCase().includes(keyword))
  );
});

// 选择变化
const onSelectChange = (keys: string[]) => {
  selectedRowKeys.value = keys;
};

// 搜索事件
const handleSearch = (value: string) => {
  searchKeyword.value = value;
  emit('search', value);
};

// 查看学生详情
const viewStudentDetail = (student: Student) => {
  emit('view-student', student);
};

// 确认移除学生 - 单个
const confirmRemoveStudent = (student: Student) => {
  currentStudent.value = student;
  batchRemove.value = false;
  removeConfirmVisible.value = true;
};

// 确认批量移除选中学生
const confirmRemoveSelected = () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请至少选择一名学生');
    return;
  }
  
  batchRemove.value = true;
  removeConfirmVisible.value = true;
};

// 确认移除
const handleRemoveConfirm = async () => {
  confirmLoading.value = true;
  
  try {
    if (batchRemove.value) {
      // 批量移除
      emit('remove-student', selectedRowKeys.value);
      message.success(`已移除 ${selectedRowKeys.value.length} 名学生`);
      selectedRowKeys.value = [];
    } else if (currentStudent.value) {
      // 移除单个学生
      emit('remove-student', [currentStudent.value.id]);
      message.success(`已移除学生 ${currentStudent.value.name}`);
    }
    
    removeConfirmVisible.value = false;
  } catch (error) {
    console.error('移除学生失败:', error);
    message.error('移除学生失败，请重试');
  } finally {
    confirmLoading.value = false;
  }
};

// 取消移除
const cancelRemove = () => {
  removeConfirmVisible.value = false;
  currentStudent.value = null;
  batchRemove.value = false;
};

// 当学生列表变化时，清空选择
watch(() => props.students, () => {
  selectedRowKeys.value = [];
}, { deep: true });
</script>

<style scoped>
.student-list-component {
  margin-bottom: 24px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.actions {
  display: flex;
  gap: 8px;
}

.student-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-secondary {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}
</style> 