<template>
  <a-modal
    v-model:open="visible"
    title="添加学生"
    width="1200px"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
  >
    <div class="add-student-container">
      <!-- 左侧组织架构树 -->
      <div class="organization-section">
        <div class="section-header">
          <span>组织架构</span>
          <a-input-search
            v-model:value="orgSearchKeyword"
            placeholder="搜索院系/专业/年级"
            style="width: 200px; margin-left: 10px;"
            size="small"
            @search="handleOrgSearch"
          />
        </div>
        <div class="organization-tree-wrapper">
          <a-spin :spinning="treeLoading">
            <a-tree
              v-if="organizationTree.length > 0"
              :tree-data="organizationTree"
              :expanded-keys="expandedKeys"
              :selected-keys="selectedKeys"
              :load-data="onLoadData"
              @expand="onExpand"
              @select="onSelect"
            >
              <template #title="{ title, nodeType }">
                <span class="tree-node-title">
                  <template v-if="nodeType === 'school'">
                    <HomeOutlined style="margin-right: 4px;" />
                  </template>
                  <template v-else-if="nodeType === 'college'">
                    <BankOutlined style="margin-right: 4px;" />
                  </template>
                  <template v-else-if="nodeType === 'major'">
                    <BookOutlined style="margin-right: 4px;" />
                  </template>
                  <template v-else-if="nodeType === 'grade'">
                    <CalendarOutlined style="margin-right: 4px;" />
                  </template>
                  <template v-else-if="nodeType === 'class'">
                    <TeamOutlined style="margin-right: 4px;" />
                  </template>
                  {{ title }}
                </span>
              </template>
            </a-tree>
          </a-spin>
        </div>
      </div>

      <!-- 中间待选学生列表 -->
      <div class="candidate-section">
        <div class="section-header">
          <span>待选学生 ({{ candidateStudents.length }})</span>
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索姓名或学号"
            style="width: 200px; margin-left: 10px;"
            size="small"
            @search="handleSearch"
          />
        </div>
        <div class="student-list-wrapper">
          <a-spin :spinning="studentsLoading">
            <a-checkbox-group v-model:value="selectedIds" style="width: 100%;">
              <div class="student-list">
                <div
                  v-for="student in candidateStudents"
                  :key="student.id"
                  class="student-item"
                >
                  <a-checkbox :value="student.id">
                    <div class="student-info">
                      <a-avatar :src="student.avatar" size="small">
                        {{ student.name.charAt(0) }}
                      </a-avatar>
                      <div class="student-details">
                        <div class="student-name">{{ student.name }}</div>
                        <div class="student-meta">
                          <span>{{ student.studentId }}</span>
                          <span class="separator">|</span>
                          <span>{{ student.major }}</span>
                          <span class="separator">|</span>
                          <span>{{ student.class }}</span>
                        </div>
                      </div>
                    </div>
                  </a-checkbox>
                </div>
                <a-empty v-if="candidateStudents.length === 0 && !studentsLoading" description="暂无可添加的学生" />
              </div>
            </a-checkbox-group>
          </a-spin>
        </div>
      </div>

      <!-- 右侧已选学生列表 -->
      <div class="selected-section">
        <div class="section-header">
          <span>已选学生 ({{ selectedStudents.length }})</span>
          <a-button
            v-if="selectedStudents.length > 0"
            type="link"
            size="small"
            danger
            @click="clearAll"
          >
            清空
          </a-button>
        </div>
        <div class="selected-list-wrapper">
          <div class="selected-list">
            <div
              v-for="student in selectedStudents"
              :key="student.id"
              class="selected-item"
            >
              <div class="student-info">
                <a-avatar :src="student.avatar" size="small">
                  {{ student.name.charAt(0) }}
                </a-avatar>
                <div class="student-details">
                  <div class="student-name">{{ student.name }}</div>
                  <div class="student-meta">{{ student.studentId }}</div>
                </div>
              </div>
              <a-button
                type="link"
                size="small"
                danger
                @click="removeStudent(student.id)"
              >
                移除
              </a-button>
            </div>
            <a-empty v-if="selectedStudents.length === 0" description="暂未选择学生" />
          </div>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import {
  HomeOutlined,
  BankOutlined,
  BookOutlined,
  CalendarOutlined,
  TeamOutlined
} from '@ant-design/icons-vue';
import type { TreeProps } from 'ant-design-vue';
import { getAvailableStudentsForClassroom, addStudentsToClassroom } from '@/api/student';
import { useDepartmentStore } from '@/stores/department';
import type { Student } from '@/types/classroom';
import type { OrganizationNode } from '@/stores/department';

interface Props {
  open: boolean;
  classroomId: string;
}

const props = defineProps<Props>();
const emit = defineEmits(['update:open', 'success']);

const departmentStore = useDepartmentStore();

const visible = ref(props.open);
const loading = ref(false);
const treeLoading = ref(false);
const studentsLoading = ref(false);

// 组织架构相关
const organizationTree = ref<OrganizationNode[]>([]);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const orgSearchKeyword = ref('');
const selectedOrganizationId = ref<string | null>(null);

// 学生列表相关
const allAvailableStudents = ref<Student[]>([]);
const candidateStudents = ref<Student[]>([]);
const selectedIds = ref<string[]>([]);
const searchKeyword = ref('');

// 计算已选学生列表
const selectedStudents = computed(() => {
  return allAvailableStudents.value.filter(student => 
    selectedIds.value.includes(student.id)
  );
});

// 监听属性变化
watch(() => props.open, (newVal) => {
  visible.value = newVal;
  if (newVal) {
    loadOrganizationTree();
    loadAvailableStudents();
  }
});

watch(visible, (newVal) => {
  emit('update:open', newVal);
});

// 加载组织架构树
const loadOrganizationTree = async () => {
  treeLoading.value = true;
  try {
    const treeData = await departmentStore.getOrganizationTree();
    organizationTree.value = treeData;
    // 默认展开第一层
    expandedKeys.value = treeData.map(node => node.key);
  } catch (error) {
    console.error('加载组织架构失败:', error);
    message.error('加载组织架构失败');
  } finally {
    treeLoading.value = false;
  }
};

// 加载可添加的学生
const loadAvailableStudents = async (organizationId?: string) => {
  studentsLoading.value = true;
  try {
    const params: any = {};
    
    // 添加搜索关键词
    if (searchKeyword.value) {
      params.keyword = searchKeyword.value;
    }
    
    // 添加组织ID筛选
    if (organizationId) {
      params.organization_id = organizationId;
    }
    
    const students = await getAvailableStudentsForClassroom(
      props.classroomId,
      params
    );
    
    allAvailableStudents.value = students;
    candidateStudents.value = students;
  } catch (error) {
    console.error('加载学生列表失败:', error);
    message.error('加载学生列表失败');
  } finally {
    studentsLoading.value = false;
  }
};

// 树节点展开
const onExpand = (keys: string[]) => {
  expandedKeys.value = keys;
};

// 树节点选择
const onSelect = (keys: string[], info: any) => {
  selectedKeys.value = keys;
  if (keys.length > 0) {
    selectedOrganizationId.value = keys[0];
    // 根据选择的组织筛选学生
    loadAvailableStudents(keys[0]);
  } else {
    selectedOrganizationId.value = null;
    loadAvailableStudents();
  }
};

// 动态加载子节点（如果需要）
const onLoadData: TreeProps['loadData'] = (treeNode) => {
  return new Promise((resolve) => {
    // 如果已经有子节点，直接返回
    if (treeNode.children && treeNode.children.length > 0) {
      resolve();
      return;
    }
    // 这里可以实现动态加载子节点的逻辑
    resolve();
  });
};

// 组织架构搜索
const handleOrgSearch = () => {
  // 实现组织架构搜索逻辑
  console.log('搜索组织:', orgSearchKeyword.value);
};

// 学生搜索
const handleSearch = () => {
  loadAvailableStudents(selectedOrganizationId.value || undefined);
};

// 移除单个学生
const removeStudent = (studentId: string) => {
  selectedIds.value = selectedIds.value.filter(id => id !== studentId);
};

// 清空所有选择
const clearAll = () => {
  selectedIds.value = [];
};

// 确认添加
const handleOk = async () => {
  if (selectedIds.value.length === 0) {
    message.warning('请至少选择一个学生');
    return;
  }

  loading.value = true;
  try {
    await addStudentsToClassroom(props.classroomId, selectedIds.value);
    message.success(`成功添加 ${selectedIds.value.length} 名学生`);
    visible.value = false;
    emit('success');
  } catch (error) {
    console.error('添加学生失败:', error);
    message.error('添加学生失败');
  } finally {
    loading.value = false;
  }
};

// 取消
const handleCancel = () => {
  visible.value = false;
  // 重置状态
  selectedIds.value = [];
  searchKeyword.value = '';
  orgSearchKeyword.value = '';
  selectedKeys.value = [];
  selectedOrganizationId.value = null;
};

onMounted(() => {
  if (props.open) {
    loadOrganizationTree();
    loadAvailableStudents();
  }
});
</script>

<style scoped lang="less">
.add-student-container {
  display: flex;
  height: 600px;
  gap: 16px;

  .organization-section {
    width: 280px;
    display: flex;
    flex-direction: column;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
  }

  .candidate-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
  }

  .selected-section {
    width: 320px;
    display: flex;
    flex-direction: column;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
  }

  .section-header {
    padding: 12px 16px;
    border-bottom: 1px solid #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: 500;
  }

  .organization-tree-wrapper {
    flex: 1;
    overflow-y: auto;
    padding: 12px;

    .tree-node-title {
      display: flex;
      align-items: center;
    }
  }

  .student-list-wrapper {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }

  .student-list {
    .student-item {
      padding: 8px 12px;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background-color: #fafafa;
      }

      .ant-checkbox-wrapper {
        width: 100%;
      }
    }
  }

  .selected-list-wrapper {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
  }

  .selected-list {
    .selected-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-bottom: 1px solid #f0f0f0;
      
      &:last-child {
        border-bottom: none;
      }

      &:hover {
        background-color: #fafafa;
      }
    }
  }

  .student-info {
    display: flex;
    align-items: center;
    gap: 12px;

    .student-details {
      .student-name {
        font-weight: 500;
        margin-bottom: 2px;
      }

      .student-meta {
        font-size: 12px;
        color: #999;

        .separator {
          margin: 0 4px;
        }
      }
    }
  }
}
</style>