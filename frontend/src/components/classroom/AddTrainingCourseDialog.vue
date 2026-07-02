<template>
  <a-modal
    v-model:open="visible"
    title="添加实训项目"
    width="900px"
    :confirmLoading="loading"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <!-- 搜索区域 -->
    <div class="search-area">
      <a-row :gutter="16">
        <a-col :span="12">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="请输入实训项目名称"
            @search="handleSearch"
          />
        </a-col>
        <a-col :span="12">
          <a-select
            v-model:value="selectedDifficulty"
            placeholder="选择难度"
            style="width: 100%"
            @change="handleSearch"
            allowClear
          >
            <a-select-option value="beginner">初级</a-select-option>
            <a-select-option value="intermediate">中级</a-select-option>
            <a-select-option value="advanced">高级</a-select-option>
          </a-select>
        </a-col>
      </a-row>
    </div>

    <!-- 实训项目列表 -->
    <div class="training-list">
      <a-table
        :columns="columns"
        :data-source="trainingList"
        :row-selection="rowSelection"
        :pagination="pagination"
        :loading="tableLoading"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'title'">
            <div class="training-title">{{ record.title }}</div>
          </template>
          <template v-else-if="column.key === 'difficulty'">
            <a-tag :color="getDifficultyColor(record.difficulty)">
              {{ getDifficultyText(record.difficulty) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'training_type'">
            <a-tag :color="['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(record.training_type) ? 'green' : 'blue'">
              {{ ['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(record.training_type) ? '拖拽式' : '编码式' }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 已选择的实训项目 -->
    <div class="selected-info" v-if="selectedRowKeys.length > 0">
      <a-alert
        :message="`已选择 ${selectedRowKeys.length} 个实训项目`"
        type="info"
        show-icon
      />
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue';
import { message } from 'ant-design-vue';
import { getTrainingLibrary } from '@/api/training';
import { addClassRoomTraining } from '@/api/classrooms';
import type { TableProps } from 'ant-design-vue';

interface Props {
  classroomId: string;
  existingTrainingIds?: number[];
}

const props = defineProps<Props>();
const emit = defineEmits(['success', 'cancel']);

// 状态管理
const visible = ref(false);
const loading = ref(false);
const tableLoading = ref(false);
const searchKeyword = ref('');
const selectedDifficulty = ref<string>();
const selectedRowKeys = ref<number[]>([]);
const trainingList = ref<any[]>([]);

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total: number) => `共 ${total} 条`
});

// 表格列配置
const columns = [
  {
    title: '实训名称',
    dataIndex: 'title',
    key: 'title',
    width: '30%'
  },
  {
    title: '所属行业',
    dataIndex: 'industry',
    key: 'industry',
    width: '15%'
  },
  {
    title: '实训类型',
    dataIndex: 'training_type',
    key: 'training_type',
    width: '15%'
  },
  {
    title: '难易度',
    dataIndex: 'difficulty',
    key: 'difficulty',
    width: '10%'
  },
  {
    title: '实验课时',
    dataIndex: 'course_hours',
    key: 'course_hours',
    width: '10%'
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    key: 'created_at',
    width: '20%'
  }
];

// 行选择配置
const rowSelection = computed(() => ({
  selectedRowKeys: selectedRowKeys.value,
  onChange: (keys: number[]) => {
    selectedRowKeys.value = keys;
  },
  getCheckboxProps: (record: any) => ({
    disabled: props.existingTrainingIds?.includes(record.id)
  })
}));

// 获取难度颜色
const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'beginner':
      return 'green';
    case 'intermediate':
      return 'orange';
    case 'advanced':
      return 'red';
    default:
      return 'default';
  }
};

// 获取难度文本
const getDifficultyText = (difficulty: string) => {
  switch (difficulty) {
    case 'beginner':
      return '初级';
    case 'intermediate':
      return '中级';
    case 'advanced':
      return '高级';
    default:
      return difficulty;
  }
};

// 加载实训项目列表
const loadTrainingList = async () => {
  tableLoading.value = true;
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      keyword: searchKeyword.value || undefined,
      difficulty: selectedDifficulty.value || undefined,
      status: 'published' // 只显示已发布的实训
    };
    
    const res = await getTrainingLibrary(params);
    trainingList.value = res.list || [];
    pagination.total = res.meta?.total || 0;
  } catch (error) {
    console.error('加载实训项目失败:', error);
    message.error('加载实训项目失败');
  } finally {
    tableLoading.value = false;
  }
};

// 处理搜索
const handleSearch = () => {
  pagination.current = 1;
  loadTrainingList();
};

// 处理表格变化
const handleTableChange: TableProps['onChange'] = (paginationConfig) => {
  pagination.current = paginationConfig?.current || 1;
  pagination.pageSize = paginationConfig?.pageSize || 10;
  loadTrainingList();
};

// 提交选择
const handleSubmit = async () => {
  if (selectedRowKeys.value.length === 0) {
    message.warning('请至少选择一个实训项目');
    return;
  }
  
  loading.value = true;
  try {
    await addClassRoomTraining({
      classroom_id: parseInt(props.classroomId),
      course_ids: selectedRowKeys.value  // 后端使用course_ids作为参数名
    });
    
    message.success(`成功添加 ${selectedRowKeys.value.length} 个实训项目`);
    emit('success');
    handleCancel();
  } catch (error) {
    console.error('添加实训项目失败:', error);
    message.error('添加实训项目失败');
  } finally {
    loading.value = false;
  }
};

// 取消
const handleCancel = () => {
  visible.value = false;
  selectedRowKeys.value = [];
  searchKeyword.value = '';
  selectedDifficulty.value = undefined;
  emit('cancel');
};

// 打开对话框
const open = () => {
  visible.value = true;
  loadTrainingList();
};

// 暴露方法
defineExpose({
  open
});
</script>

<style scoped>
.search-area {
  margin-bottom: 16px;
}

.training-list {
  margin-bottom: 16px;
}

.training-title {
  font-weight: 500;
}

.selected-info {
  margin-top: 16px;
}
</style>