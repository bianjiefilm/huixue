<template>
    <a-card class="students-card">
      <template #title>
        
        <a-button v-if="classroomStatus !== 'past'" type="primary" size="small" @click="openAddStudentModal">
          <template #icon><plus-outlined /></template>
          添加学生
        </a-button>
      </template>
  
      <div>
        <div class="student-search-bar">
          <a-input-search
            v-model:value="studentSearchText"
            placeholder="请输入学生姓名或学号"
            style="width: 300px"
            @search="handleSearchStudent"
            allow-clear
          />
			<a-button type="primary" @click="loadStudentList">
			    <template #icon><ReloadOutlined /></template>
			  </a-button>
          <div class="student-actions">
            <a-button type="primary" danger :disabled="selectedStudentKeys.length === 0" @click="showBatchRemoveConfirm">
                批量移除 ({{ selectedStudentKeys.length }})
            </a-button>
          </div>
        </div>
  
        <a-table
          :dataSource="localStudents"
          :columns="studentColumns"
          :pagination="{ pageSize: 10 }"
          rowKey="id"
          :rowSelection="{
            selectedRowKeys: selectedStudentKeys,
            onChange: onStudentSelectionChange
          }"
          :scroll="{ x: true }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'action'">
              <a-button type="link" danger @click="showRemoveStudentConfirm(record)">移除</a-button>
            </template>
          </template>
        </a-table>
      </div>
      
      <!-- Remove Student Confirm Modal -->
      <a-modal
        v-model:open="showRemoveStudentModal"
        title="确认移除"
        @ok="confirmRemoveStudent"
        @cancel="cancelRemoveStudent"
        :confirmLoading="removingStudent"
      >
        <p>确定要将学生 "{{ studentToRemove?.name }}" 从课堂中移除吗？</p>
      </a-modal>
  
       <!-- Batch Remove Confirm Modal -->
      <a-modal
        v-model:open="showBatchRemoveModal"
        title="确认批量移除"
        @ok="confirmBatchRemove"
        @cancel="showBatchRemoveModal = false"
        :confirmLoading="removingStudent"
      >
        <p>确定要将选中的 {{ selectedStudentKeys.length }} 名学生从课堂中移除吗？
  </p>
        <p style="color: red;">此操作不可恢复。
  </p>
      </a-modal>
  
    </a-card>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch, onMounted} from 'vue';
  import { message, Modal } from 'ant-design-vue';
  import { TeamOutlined, PlusOutlined,ReloadOutlined } from '@ant-design/icons-vue';
  import { departTreeList,classStuList } from '@/api/classes';
  import { getRoomStuList,addRoomStudents,delRoomStudents } from '@/api/classrooms';
  // import { useClassroomStore } from '../../stores/classroom'; // If needed
  
  // Mock data structure - replace with your actual type
  interface Student {
    id: string;
    name: string;
    studentId: string;
    major?: string;
    className?: string;
  }
  interface OrgNode {
      title: string;
      key: string;
      children?: OrgNode[];
  }
  
  interface Props {
    students: Student[];
    classroomId: string;
    classroomStatus: string;
  }
  // Ant Design Vue 4.x 使用 fieldNames 替代 replaceFields
  const fieldNames = {
    children: 'children',
    title: 'name',
    key: 'id'
  };
  const props = defineProps<Props>();
  const emit = defineEmits(['update-students', 'add-student', 'remove-student']); // Notify parent of changes
  
  // const classroomStore = useClassroomStore(); // Uncomment if store actions are used
  
  // --- Local State ---
  const localStudents = ref<Student[]>([]);
  const studentSearchText = ref('');
  const selectedStudentKeys = ref<string[]>([]); // For main list selection
  
  // Remove Student Modal State
  const showRemoveStudentModal = ref(false);
  const showBatchRemoveModal = ref(false);
  const studentToRemove = ref<Student | null>(null);
  const removingStudent = ref(false);
  

  // --- Table Columns ---
  const studentColumns = [
    { title: '姓名', dataIndex: 'realname', key: 'realname', width: 120 },
    { title: '学号', dataIndex: 'xuehao', key: 'xuehao', width: 150 },
    { title: '班级', dataIndex: 'class_name', key: 'class_name', width: 150 },
    { title: '操作', key: 'action', fixed: 'right', width: 80 },
  ];

  // --- Methods ---
  
  // Student List Management
  const handleSearchStudent = () => {
    loadStudentList();
  };
  
  const onStudentSelectionChange = (keys: string[]) => {
    selectedStudentKeys.value = keys;
  };
  
  const showRemoveStudentConfirm = (student: Student) => {
    studentToRemove.value = student;
    showRemoveStudentModal.value = true;
  };
  
  const confirmRemoveStudent = async () => {
    if (!studentToRemove.value) return;
    removingStudent.value = true;
    const studentId = studentToRemove.value.id;
    try {
      emit('remove-student', [studentId]); // emit to detail.vue
    } catch (error) {
      //message.error('移除学生失败');
      console.error(error);
    } finally {
      removingStudent.value = false;
      studentToRemove.value = null;
    }
  };
  
  const cancelRemoveStudent = () => {
    showRemoveStudentModal.value = false;
    studentToRemove.value = null;
  };
  
  const showBatchRemoveConfirm = () => {
      if (selectedStudentKeys.value.length === 0) return;
      showBatchRemoveModal.value = true;
  };
  
  const confirmBatchRemove = async () => {
      if (selectedStudentKeys.value.length === 0) return;
      removingStudent.value = true;
      const studentIdsToRemove = [...selectedStudentKeys.value];
	  let stuids=studentIdsToRemove.join(',');
      try {
          emit('remove-student', studentIdsToRemove); // emit to detail.vue
          showBatchRemoveModal.value = false;
      } catch (error) {
          message.error('批量移除学生失败');
          console.error(error);
      } finally {
          removingStudent.value = false;
      }
  };
  


  const loadStudentList = async () => {
    localStudents.value = []; // Clear previous
    try {
      const res = await getRoomStuList({classroom_id: Number(props.classroomId), keyword: studentSearchText.value});
      // 从响应中提取data数组，兼容多种响应格式
      localStudents.value = Array.isArray(res) ? res : (res?.data || []);
      console.log('[StudentList] 加载学生列表成功:', localStudents.value.length, '个学生');
    } catch (error) {
      message.error('加载学生列表失败');
      console.error('[StudentList] 加载学生列表失败:', error);
      localStudents.value = [];
    }
  };

  // 打开添加学生弹窗
  const openAddStudentModal = () => {
    console.log('准备打开外层添加学生弹窗...');
    emit('add-student');
  };

  // --- Lifecycle ---
  onMounted(() => {
    loadStudentList(); 
  });

  // 兼容旧的open方法
  const open = () => {
    loadStudentList();
  };

  // 暴露方法给父组件
  defineExpose({
    open,
    openAddStudentModal
  });
  </script>
  
  <style scoped>
  /* Add all relevant styles from the original file here */
  .students-card {
    margin-bottom: 24px;
  }
  
  .card-title {
    display: flex;
    align-items: center;
  }
  
  .card-title :deep(svg) {
    margin-right: 8px;
    font-size: 16px;
  }
  
  .student-search-bar {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    flex-wrap: wrap; /* Allow wrapping */
    gap: 16px; /* Space between search and actions */
  }
  
  .student-actions {
    display: flex;
    gap: 8px;
  }
</style>