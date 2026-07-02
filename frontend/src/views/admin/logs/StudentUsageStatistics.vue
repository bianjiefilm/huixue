<template>
  <div class="statistics-container">
    <div class="page-header">
      <h2 class="page-title">学生使用统计 <span v-if="timeRangeLabel">({{ timeRangeLabel }})</span></h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <!-- 时间筛选 -->
      <a-radio-group v-model:value="timeRange" button-style="solid" @change="handleTimeRangeChange">
        <a-radio-button value="today">今天</a-radio-button>
        <a-radio-button value="yesterday">昨天</a-radio-button>
        <a-radio-button value="last_7_days">最近7天</a-radio-button>
        <a-radio-button value="last_30_days">最近30天</a-radio-button>
        <a-radio-button value="custom">自定义</a-radio-button>
      </a-radio-group>

      <a-range-picker
        v-model:value="customDateRange"
        v-show="timeRange === 'custom'"
        :disabledDate="disabledDate"
        @change="handleDateRangeChange"
        format="YYYY-MM-DD"
        :allowClear="false"
        class="custom-date-picker"
      />

      <!-- 搜索框 -->
      <div class="search-filter">
        <a-input
          v-model:value="searchKeyword"
          placeholder="搜索学生姓名或学号"
          style="width: 200px"
          @pressEnter="handleSearch"
          allowClear
        >
          <template #suffix>
            <search-outlined @click="handleSearch" />
          </template>
        </a-input>
      </div>

      <!-- 学院筛选 -->
      <div class="college-filter">
        <span class="filter-label">学院：</span>
        <a-select
          v-model:value="collegeFilter"
          style="width: 150px"
          @change="handleCollegeChange"
          allowClear
          placeholder="全部"
        >
          <a-select-option value="计算机学院">计算机学院</a-select-option>
          <a-select-option value="软件学院">软件学院</a-select-option>
          <a-select-option value="信息学院">信息学院</a-select-option>
          <a-select-option value="数学学院">数学学院</a-select-option>
        </a-select>
      </div>

      <!-- 专业筛选 -->
      <div class="major-filter">
        <span class="filter-label">专业：</span>
        <a-select
          v-model:value="majorFilter"
          style="width: 150px"
          @change="handleMajorChange"
          allowClear
          placeholder="全部"
        >
          <a-select-option value="计算机科学与技术">计算机科学与技术</a-select-option>
          <a-select-option value="软件工程">软件工程</a-select-option>
          <a-select-option value="人工智能">人工智能</a-select-option>
          <a-select-option value="数据科学与大数据技术">数据科学与大数据技术</a-select-option>
        </a-select>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="学生总数" :value="statisticsData.totalStudents" :valueStyle="{ color: '#3f8600' }">
          <template #prefix>
            <user-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总登录次数" :value="statisticsData.totalLogins" :valueStyle="{ color: '#0096FF' }">
          <template #prefix>
            <login-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总实践次数" :value="statisticsData.totalPractices" :valueStyle="{ color: '#722ED1' }">
          <template #prefix>
            <experiment-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总实训次数" :value="statisticsData.totalTrainings" :valueStyle="{ color: '#F5A623' }">
          <template #prefix>
            <laptop-outlined />
          </template>
        </a-statistic>
      </a-card>
    </div>

    <!-- 表格数据 -->
    <a-table
      :columns="columns"
      :data-source="tableData"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="student_id"
      class="data-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'real_name'">
          <span class="student-name">{{ record.real_name }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'employee_id'">
          <span class="employee-id">{{ record.employee_id || '-' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'organization_name'">
          <a-tag color="blue">{{ record.organization_name || '-' }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'practice_learning_duration'">
          {{ formatDuration(record.practice_learning_duration * 60) }}
        </template>
        <!--
        <template v-else-if="column.dataIndex === 'resource_learning_duration'">
          {{ formatDuration(record.resource_learning_duration * 60) }}
        </template>
        -->
        <template v-else-if="column.dataIndex === 'training_learning_duration'">
          {{ formatDuration(record.training_learning_duration * 60) }}
        </template>
      </template>
    </a-table>

    <!-- 导出按钮 -->
    <div class="action-bar">
      <a-button type="primary" @click="exportData" :loading="exportLoading">
        <template #icon><export-outlined /></template>
        导出
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import dayjs, { Dayjs } from 'dayjs';
import { 
  UserOutlined,
  LoginOutlined,
  ExperimentOutlined,
  LaptopOutlined,
  ExportOutlined,
  SearchOutlined
} from '@ant-design/icons-vue';
import { 
  getStudentUsageStatistics, 
  exportStatisticsData,
  TimeRange,
  formatTimeRangeText,
  formatDuration,
  type StudentUsageParams,
  type StudentUsageItem
} from '@/api/usage-statistics';

// 列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'student_id',
    width: 80,
  },
  {
    title: '学生姓名',
    dataIndex: 'real_name',
  },
  {
    title: '学号',
    dataIndex: 'employee_id',
    width: 120,
  },
  {
    title: '学院',
    dataIndex: 'organization_name',
    width: 120,
  },
  {
    title: '登录次数',
    dataIndex: 'login_count',
    sorter: true,
    defaultSortOrder: 'descend',
    width: 100,
  },
  {
    title: '开始实践次数',
    dataIndex: 'practice_start_count',
    sorter: true,
    width: 120,
  },
  {
    title: '实践学习时长',
    dataIndex: 'practice_learning_duration',
    sorter: true,
    width: 120,
  },
  // {
  //   title: '教学资源学习时长',
  //   dataIndex: 'resource_learning_duration',
  //   sorter: true,
  //   width: 140,
  // },
  {
    title: '开始实训次数',
    dataIndex: 'training_start_count',
    sorter: true,
    width: 120,
  },
  {
    title: '实训学习时长',
    dataIndex: 'training_learning_duration',
    sorter: true,
    width: 120,
  },
  // {
  //   title: '数据游乐场项目数',
  //   dataIndex: 'playground_project_count',
  //   sorter: true,
  //   width: 140,
  // }
];

// 表格数据
const loading = ref(false);
const exportLoading = ref(false);
const tableData = ref<StudentUsageItem[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
});

// 统计数据
const statisticsData = reactive({
  totalStudents: 0,
  totalLogins: 0,
  totalPractices: 0,
  totalTrainings: 0,
});

// 筛选条件
const timeRange = ref<TimeRange>(TimeRange.TODAY);
const customDateRange = ref<[Dayjs, Dayjs]>([dayjs().subtract(7, 'day'), dayjs()]);
const platformCreatedDate = dayjs('2018-10-06'); // 平台创建日期
const searchKeyword = ref<string>('');
const collegeFilter = ref<string>('');
const majorFilter = ref<string>('');

// 禁用日期范围
const disabledDate = (current: Dayjs) => {
  return current.isBefore(platformCreatedDate, 'day') || current.isAfter(dayjs(), 'day');
};

// 时间范围标签
const timeRangeLabel = computed(() => {
  let startDate: string | undefined;
  let endDate: string | undefined;
  
  if (timeRange.value === TimeRange.CUSTOM && customDateRange.value) {
    startDate = customDateRange.value[0].format('YYYY-MM-DD');
    endDate = customDateRange.value[1].format('YYYY-MM-DD');
  }
  
  return formatTimeRangeText(timeRange.value, startDate, endDate);
});

// 处理时间范围变化
const handleTimeRangeChange = () => {
  pagination.current = 1; // 重置到第一页
  fetchData();
};

// 处理自定义日期范围变化
const handleDateRangeChange = () => {
  if (timeRange.value === TimeRange.CUSTOM) {
    pagination.current = 1; // 重置到第一页
    fetchData();
  }
};

// 处理搜索
const handleSearch = () => {
  pagination.current = 1; // 重置到第一页
  fetchData();
};

// 处理学院筛选变化
const handleCollegeChange = () => {
  pagination.current = 1; // 重置到第一页
  fetchData();
};

// 处理专业筛选变化
const handleMajorChange = () => {
  pagination.current = 1; // 重置到第一页
  fetchData();
};

// 处理表格变化（排序、分页）
const handleTableChange = (pag: any, filters: any, sorter: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  
  // 处理排序逻辑如果需要的话
  fetchData();
};

// 获取数据
const fetchData = async () => {
  loading.value = true;
  try {
    // 构建查询参数
    const params: StudentUsageParams = {
      page: pagination.current,
      page_size: pagination.pageSize,
      time_range: timeRange.value,
      name: searchKeyword.value || undefined,
      college: collegeFilter.value || undefined,
      major: majorFilter.value || undefined
    };

    // 处理自定义时间范围
    if (timeRange.value === TimeRange.CUSTOM && customDateRange.value) {
      params.start_date = customDateRange.value[0].format('YYYY-MM-DD');
      params.end_date = customDateRange.value[1].format('YYYY-MM-DD');
    }

    // 请求数据
    const response = await getStudentUsageStatistics(params);

    if (response.code === '0000' && response.data) {
      tableData.value = response.data.data;
      pagination.total = response.data.meta.total;
      
      // 更新统计数据
      statisticsData.totalStudents = response.data.meta.total;
      statisticsData.totalLogins = response.data.data.reduce((sum, item) => sum + item.login_count, 0);
      statisticsData.totalPractices = response.data.data.reduce((sum, item) => sum + item.practice_start_count, 0);
      statisticsData.totalTrainings = response.data.data.reduce((sum, item) => sum + item.training_start_count, 0);
    } else {
      message.error(response.message || '获取数据失败');
    }
  } catch (error) {
    console.error('获取数据失败', error);
    message.error('获取数据失败');
  } finally {
    loading.value = false;
  }
};

// 导出数据
const exportData = async () => {
  exportLoading.value = true;
  try {
    const params = {
      export_type: 'student' as const,
      export_format: 'xlsx' as const,
      time_range: timeRange.value,
      name: searchKeyword.value || undefined,
      college: collegeFilter.value || undefined,
      major: majorFilter.value || undefined,
      ...(timeRange.value === TimeRange.CUSTOM && customDateRange.value ? {
        start_date: customDateRange.value[0].format('YYYY-MM-DD'),
        end_date: customDateRange.value[1].format('YYYY-MM-DD')
      } : {})
    };

    const response = await exportStatisticsData(params);
    
    if (response.code === '0000' && response.data) {
      // 触发下载
      const link = document.createElement('a');
      link.href = response.data.export_url;
      link.download = response.data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success(`成功导出 ${response.data.record_count} 条记录`);
    } else {
      message.error(response.message || '导出失败');
    }
  } catch (error) {
    console.error('导出失败', error);
    message.error('导出失败');
  } finally {
    exportLoading.value = false;
  }
};

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
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.filter-bar {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.custom-date-picker {
  margin-left: 16px;
}

.search-filter,
.college-filter,
.major-filter {
  display: flex;
  align-items: center;
}

.filter-label {
  margin-right: 8px;
  font-weight: 500;
}

.statistics-cards {
  display: flex;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.statistic-card {
  flex: 1;
  min-width: 220px;
}

.data-table {
  background-color: #fff;
  border-radius: 4px;
}

.student-name {
  font-weight: 500;
  color: #1890ff;
}

.employee-id {
  font-family: monospace;
  color: #666;
}

.action-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style> 