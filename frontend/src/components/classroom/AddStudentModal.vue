<template>
  <a-modal
    :title="title"
    :open="open"
    :confirm-loading="confirmLoading"
    width="700px"
    @ok="handleOk"
    @cancel="handleCancel"
    :mask-closable="false"
  >
    <a-spin :spinning="loading">
      <div class="add-student-modal">
        <!-- 搜索栏 -->
        <div class="search-bar">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="请输入学生姓名或学号搜索"
            enter-button
            @search="handleSearch"
            style="width: 100%"
          />
        </div>

        <!-- 候选学生列表 -->
        <div class="student-container">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="search" :tab="`搜索结果${searchStudents.length ? ` (${searchStudents.length})` : ''}`">
              <a-empty v-if="searchStudents.length === 0 && searchKeyword" description="未找到匹配的学生" />
              <a-empty v-else-if="searchStudents.length === 0" description="请输入关键词搜索学生" />
              <div v-else class="student-list">
                <div 
                  v-for="student in searchStudents" 
                  :key="student.id"
                  class="student-item"
                  :class="{ 'selected': isSelected(student.id) }"
                  @click="toggleSelection(student)"
                >
                  <div class="student-avatar">
                    <a-avatar :src="student.avatar || ''" :alt="student.name">
                      {{ student.name.substring(0, 1) }}
                    </a-avatar>
                  </div>
                  <div class="student-info">
                    <div class="student-name">{{ student.name }}</div>
                    <div class="student-meta">
                      <span>学号: {{ student.studentId }}</span>
                      <span>{{ student.major || '未设置专业' }}</span>
                    </div>
                  </div>
                  <div class="student-action">
                    <a-checkbox :checked="isSelected(student.id)" @change="() => toggleSelection(student)" @click.stop />
                  </div>
                </div>
              </div>
            </a-tab-pane>
            <a-tab-pane key="available" :tab="`可添加学生 (${availableStudents.length})`">
              <a-empty v-if="availableStudents.length === 0" description="暂无可添加的学生" />
              <div v-else class="student-list">
                <div 
                  v-for="student in availableStudents" 
                  :key="student.id"
                  class="student-item"
                  :class="{ 'selected': isSelected(student.id) }"
                  @click="toggleSelection(student)"
                >
                  <div class="student-avatar">
                    <a-avatar :src="student.avatar || ''" :alt="student.name">
                      {{ student.name.substring(0, 1) }}
                    </a-avatar>
                  </div>
                  <div class="student-info">
                    <div class="student-name">{{ student.name }}</div>
                    <div class="student-meta">
                      <span>学号: {{ student.studentId }}</span>
                      <span>{{ student.major || '未设置专业' }}</span>
                    </div>
                  </div>
                  <div class="student-action">
                    <a-checkbox :checked="isSelected(student.id)" @change="() => toggleSelection(student)" @click.stop />
                  </div>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>
        </div>

        <!-- 选中学生统计 -->
        <div class="selected-summary">
          <template v-if="selectedStudents.length > 0">
            已选择 {{ selectedStudents.length }} 名学生
            <a-button type="link" @click="clearSelection">清空选择</a-button>
          </template>
          <template v-else>
            请选择要添加的学生
          </template>
        </div>
      </div>
    </a-spin>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useClassroomStore } from '../../stores/classroom';
import { searchStudentsByKeyword, getAvailableStudents } from '../../api/classroom';
import type { Student } from '@/types/classroom';
import { message } from 'ant-design-vue';

// 组件属性
const props = defineProps({
  classroomId: {
    type: String,
    required: true
  },
  open: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '添加学生'
  }
});

// 组件事件
const emit = defineEmits(['update:open', 'success', 'cancel']);

// 组件状态
const classroomStore = useClassroomStore();
const searchKeyword = ref('');
const searchStudents = ref<Student[]>([]);
const availableStudents = ref<Student[]>([]);
const selectedStudentIds = ref<string[]>([]);
const loading = ref(false);
const confirmLoading = ref(false);
const activeTab = ref('available');

// 计算属性
const selectedStudents = computed(() => {
  const allStudents = [...searchStudents.value, ...availableStudents.value];
  // 去重
  const uniqueStudents = allStudents.filter((student, index, self) => 
    index === self.findIndex(s => s.id === student.id)
  );
  return uniqueStudents.filter(student => selectedStudentIds.value.includes(student.id));
});

// 是否已选中
const isSelected = (studentId: string) => {
  return selectedStudentIds.value.includes(studentId);
};

// 切换选中状态
const toggleSelection = (student: Student) => {
  if (isSelected(student.id)) {
    // 取消选择
    selectedStudentIds.value = selectedStudentIds.value.filter(id => id !== student.id);
  } else {
    // 添加选择
    selectedStudentIds.value.push(student.id);
  }
};

// 清空选择
const clearSelection = () => {
  selectedStudentIds.value = [];
};

// 搜索学生
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchStudents.value = [];
    activeTab.value = 'available';
    return;
  }
  
  loading.value = true;
  try {
    const students = await searchStudentsByKeyword(searchKeyword.value);
    searchStudents.value = students;
    activeTab.value = 'search';
  } catch (error) {
    console.error('搜索学生失败:', error);
    message.error('搜索学生失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 获取可添加学生
const fetchAvailableStudents = async () => {
  loading.value = true;
  try {
    availableStudents.value = await getAvailableStudents(props.classroomId);
  } catch (error) {
    console.error('获取可添加学生失败:', error);
    message.error('获取可添加学生失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 确认添加
const handleOk = async () => {
  if (selectedStudentIds.value.length === 0) {
    message.warning('请至少选择一名学生');
    return;
  }
  
  confirmLoading.value = true;
  try {
    const result = await classroomStore.addStudents(props.classroomId, selectedStudentIds.value);
    if (result) {
      message.success(`成功添加 ${selectedStudentIds.value.length} 名学生`);
      emit('success');
      emit('update:open', false);
      resetState();
    } else {
      throw new Error('添加学生失败');
    }
  } catch (error) {
    console.error('添加学生失败:', error);
    message.error('添加学生失败，请重试');
  } finally {
    confirmLoading.value = false;
  }
};

// 取消添加
const handleCancel = () => {
  emit('update:open', false);
  emit('cancel');
  resetState();
};

// 重置状态
const resetState = () => {
  searchKeyword.value = '';
  searchStudents.value = [];
  selectedStudentIds.value = [];
  activeTab.value = 'available';
};

// 监听对话框开关状态
watch(() => props.open, (newVal) => {
  if (newVal) {
    fetchAvailableStudents();
  }
});

// 组件初始化
onMounted(() => {
  if (props.open) {
    fetchAvailableStudents();
  }
});
</script>

<style scoped>
.add-student-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-bar {
  margin-bottom: 16px;
}

.student-container {
  height: 400px;
  overflow: hidden;
}

.student-list {
  height: 330px;
  overflow-y: auto;
  padding: 8px 0;
}

.student-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.student-item:hover {
  background-color: #f5f5f5;
}

.student-item.selected {
  background-color: #e6f7ff;
}

.student-avatar {
  margin-right: 12px;
}

.student-info {
  flex: 1;
}

.student-name {
  font-weight: 500;
  font-size: 16px;
  margin-bottom: 4px;
}

.student-meta {
  font-size: 14px;
  color: #666;
  display: flex;
  gap: 16px;
}

.student-action {
  margin-left: 12px;
}

.selected-summary {
  padding: 12px 0;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style> 