<template>
  <div class="statistics-container">
    <div class="page-header">
      <h2 class="page-title">
        {{ practiceName }} <span v-if="timeRangeLabel">({{ timeRangeLabel }})</span>
        <a-button type="link" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回
        </a-button>
      </h2>
    </div>

    <!-- 用户类型选择 -->
    <div class="user-type-selector">
      <a-radio-group v-model:value="userType" button-style="solid" @change="handleUserTypeChange">
        <a-radio-button value="teacher">教师视图</a-radio-button>
        <a-radio-button value="student">学生视图</a-radio-button>
      </a-radio-group>
    </div>

    <!-- 筛选条件 -->
    <a-form layout="inline" class="filter-form">
      <a-form-item label="姓名">
        <a-input v-model:value="filters.name" placeholder="请输入姓名" />
      </a-form-item>
      <a-form-item label="工号">
        <a-input v-model:value="filters.workerId" placeholder="请输入工号" />
      </a-form-item>
      <a-form-item label="学院">
        <a-select
          v-model:value="filters.department"
          placeholder="请选择学院"
          style="width: 180px"
          allowClear
          @change="handleDepartmentChange"
        >
          <a-select-option v-for="dept in departmentOptions" :key="dept.value" :value="dept.value">
            {{ dept.label }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="专业">
        <a-select
          v-model:value="filters.major"
          placeholder="请选择专业"
          style="width: 180px"
          allowClear
          :disabled="!filters.department"
        >
          <a-select-option v-for="major in majorOptions" :key="major.value" :value="major.value">
            {{ major.label }}
          </a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item>
        <a-space>
          <a-button type="primary" @click="fetchData">查询</a-button>
          <a-button @click="resetFilters">重置</a-button>
        </a-space>
      </a-form-item>
    </a-form>

    <!-- 表格数据 -->
    <a-table
      :columns="userType === 'teacher' ? teacherColumns : studentColumns"
      :data-source="tableData"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="id"
      class="data-table"
    />

    <!-- 导出按钮 -->
    <div class="action-bar">
      <a-button type="primary" @click="exportData">
        <template #icon><export-outlined /></template>
        导出
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import { ExportOutlined, ArrowLeftOutlined } from '@ant-design/icons-vue';

// 路由
const router = useRouter();
const route = useRoute();

// 教师列定义
const teacherColumns = [
  {
    title: '序号',
    dataIndex: 'id',
    width: 80,
  },
  {
    title: '姓名',
    dataIndex: 'name',
  },
  {
    title: '工号',
    dataIndex: 'workerId',
  },
  {
    title: '学院',
    dataIndex: 'department',
  },
  {
    title: '专业',
    dataIndex: 'major',
  },
  {
    title: '访问次数',
    dataIndex: 'visitCount',
    sorter: true,
    defaultSortOrder: 'descend'
  },
  {
    title: '添加到课堂次数',
    dataIndex: 'addToClassCount',
    sorter: true,
  }
];

// 学生列定义
const studentColumns = [
  {
    title: '序号',
    dataIndex: 'id',
    width: 80,
  },
  {
    title: '姓名',
    dataIndex: 'name',
  },
  {
    title: '学号',
    dataIndex: 'workerId',
  },
  {
    title: '学院',
    dataIndex: 'department',
  },
  {
    title: '专业',
    dataIndex: 'major',
  },
  {
    title: '访问次数',
    dataIndex: 'visitCount',
    sorter: true,
    defaultSortOrder: 'descend'
  },
  {
    title: '学习次数',
    dataIndex: 'learnCount',
    sorter: true,
  },
  {
    title: '学习时长(分钟)',
    dataIndex: 'learnDuration',
    sorter: true,
    customRender: ({ text }: { text: number }) => (text / 60).toFixed(1),
  }
];

// 实践名称和ID
const practiceId = computed(() => route.params.id as string);
const practiceName = ref('实践访问统计');

// 用户类型
const userType = ref(route.query.userType as string || 'teacher');

// 表格数据
const loading = ref(false);
const tableData = ref<any[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
});

// 筛选条件
const filters = reactive({
  name: '',
  workerId: '',
  department: undefined,
  major: undefined
});

// 时间范围
const timeRange = computed(() => route.query.timeRange as string || 'today');
const customStartDate = computed(() => route.query.startDate as string);
const customEndDate = computed(() => route.query.endDate as string);

// 院系专业数据
const departmentOptions = [
  { value: '计算机学院', label: '计算机学院' },
  { value: '数学学院', label: '数学学院' },
  { value: '物理学院', label: '物理学院' },
  { value: '经济学院', label: '经济学院' }
];

const majorMap = {
  '计算机学院': [
    { value: '计算机科学与技术', label: '计算机科学与技术' },
    { value: '软件工程', label: '软件工程' },
    { value: '人工智能', label: '人工智能' }
  ],
  '数学学院': [
    { value: '应用数学', label: '应用数学' },
    { value: '统计学', label: '统计学' }
  ],
  '物理学院': [
    { value: '理论物理', label: '理论物理' },
    { value: '应用物理', label: '应用物理' }
  ],
  '经济学院': [
    { value: '金融学', label: '金融学' },
    { value: '国际经济与贸易', label: '国际经济与贸易' }
  ]
};

const majorOptions = computed(() => {
  if (!filters.department) return [];
  return majorMap[filters.department as keyof typeof majorMap] || [];
});

// 时间范围标签
const timeRangeLabel = computed(() => {
  switch (timeRange.value) {
    case 'today':
      return dayjs().format('YYYY.MM.DD');
    case 'yesterday':
      return dayjs().subtract(1, 'day').format('YYYY.MM.DD');
    case 'week':
      return `${dayjs().subtract(6, 'day').format('YYYY.MM.DD')}~${dayjs().format('YYYY.MM.DD')}`;
    case 'month':
      return `${dayjs().subtract(29, 'day').format('YYYY.MM.DD')}~${dayjs().format('YYYY.MM.DD')}`;
    case 'custom':
      if (customStartDate.value && customEndDate.value) {
        return `${dayjs(customStartDate.value).format('YYYY.MM.DD')}~${dayjs(customEndDate.value).format('YYYY.MM.DD')}`;
      }
      return '';
    default:
      return '';
  }
});

// 处理学院变更，级联清空专业
const handleDepartmentChange = () => {
  filters.major = undefined;
};

// 处理用户类型变化
const handleUserTypeChange = () => {
  pagination.current = 1;
  fetchData();
};

// 处理表格变化（排序、分页）
const handleTableChange = (pag: any, filters: any, sorter: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  
  fetchData(sorter);
};

// 重置筛选
const resetFilters = () => {
  Object.assign(filters, {
    name: '',
    workerId: '',
    department: undefined,
    major: undefined
  });
  
  pagination.current = 1;
  fetchData();
};

// 返回实践列表页
const goBack = () => {
  router.push('/admin/logs/practice');
};

// 获取数据
const fetchData = async (sorter?: any) => {
  loading.value = true;
  try {
    // 构建查询参数
    const params: Record<string, any> = {
      page: pagination.current,
      pageSize: pagination.pageSize,
      timeRange: timeRange.value,
      userType: userType.value,
      ...filters
    };

    // 处理自定义时间范围
    if (timeRange.value === 'custom') {
      params.startDate = customStartDate.value;
      params.endDate = customEndDate.value;
    }

    // 处理排序
    if (sorter && sorter.field) {
      params.sortField = sorter.field;
      params.sortOrder = sorter.order;
    }

    // 请求数据
    const response = await fetch(`/v1/admin/logs/practice/detail/${practiceId.value}?${new URLSearchParams(params)}`);
    const result = await response.json();

    if (result.code === 200) {
      tableData.value = result.data.list;
      pagination.total = result.data.total;
      
      // 更新实践名称
      if (result.data.practiceName) {
        practiceName.value = result.data.practiceName;
      }
    } else {
      message.error('获取数据失败');
    }
  } catch (error) {
    console.error('获取数据失败', error);
    message.error('获取数据失败');
  } finally {
    loading.value = false;
  }
};

// 导出数据
const exportData = () => {
  message.success(`已导出${practiceName.value}${timeRangeLabel.value ? '（' + timeRangeLabel.value + '）' : ''}的统计数据`);
};

// 监听用户类型变化，重置分页
watch(userType, () => {
  pagination.current = 1;
});

// 初始加载
onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.statistics-container {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100%;
}

.page-header {
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  display: flex;
  align-items: center;
}

.user-type-selector {
  margin-bottom: 16px;
}

.filter-form {
  background-color: #fff;
  padding: 24px;
  margin-bottom: 24px;
  border-radius: 4px;
}

.data-table {
  background-color: #fff;
  border-radius: 4px;
}

.action-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style> 