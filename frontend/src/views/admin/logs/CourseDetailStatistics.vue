<template>
  <div class="statistics-container">
    <div class="page-header">
      <a-button type="text" @click="goBack" class="back-button">
        <template #icon><arrow-left-outlined /></template>
        返回
      </a-button>
      <h2 class="page-title">{{ courseTitle }} <span v-if="timeRangeLabel">({{ timeRangeLabel }})</span></h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <!-- 姓名搜索 -->
      <div class="search-filter">
        <a-input
          v-model:value="searchKeyword"
          placeholder="搜索姓名"
          style="width: 150px"
          @pressEnter="handleSearch"
          allowClear
        >
          <template #suffix>
            <search-outlined @click="handleSearch" />
          </template>
        </a-input>
      </div>

      <!-- 工号/学号搜索 -->
      <div class="employee-filter">
        <a-input
          v-model:value="employeeFilter"
          placeholder="搜索工号/学号"
          style="width: 150px"
          @pressEnter="handleSearch"
          allowClear
        />
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
        <a-statistic title="总用户数" :value="statisticsData.totalUsers" :valueStyle="{ color: '#3f8600' }">
          <template #prefix>
            <user-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总访问次数" :value="statisticsData.totalAccesses" :valueStyle="{ color: '#0096FF' }">
          <template #prefix>
            <eye-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总学习次数" :value="statisticsData.totalLearning" :valueStyle="{ color: '#722ED1' }">
          <template #prefix>
            <book-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总学习时长" :value="formatDuration(statisticsData.totalDuration)" :valueStyle="{ color: '#F5A623' }">
          <template #prefix>
            <clock-circle-outlined />
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
      row-key="user_id"
      class="data-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'real_name'">
          <span class="user-name">{{ record.real_name }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'employee_id'">
          <span class="employee-id">{{ record.employee_id || '-' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'organization_name'">
          <a-tag color="blue">{{ record.organization_name || '-' }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'major'">
          <a-tag color="green">{{ record.major || '-' }}</a-tag>
        </template>
        <template v-else-if="column.dataIndex === 'learning_duration'">
          {{ formatDuration(record.learning_duration * 60) }}
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
import { ref, reactive, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  ArrowLeftOutlined,
  UserOutlined,
  EyeOutlined,
  BookOutlined,
  ClockCircleOutlined,
  ExportOutlined,
  SearchOutlined
} from '@ant-design/icons-vue';
import { 
  getCourseDetailStatistics, 
  exportStatisticsData,
  formatDuration,
  type CourseDetailStatisticsParams,
  type CourseDetailStatisticsItem
} from '@/api/usage-statistics';

// 列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'user_id',
    width: 80,
  },
  {
    title: '姓名',
    dataIndex: 'real_name',
  },
  {
    title: '工号/学号',
    dataIndex: 'employee_id',
    width: 120,
  },
  {
    title: '学院',
    dataIndex: 'organization_name',
    width: 120,
  },
  {
    title: '专业',
    dataIndex: 'major',
    width: 150,
  },
  {
    title: '访问次数',
    dataIndex: 'access_count',
    sorter: true,
    defaultSortOrder: 'descend',
    width: 100,
  },
  {
    title: '学习次数',
    dataIndex: 'learning_count',
    sorter: true,
    width: 100,
  },
  {
    title: '学习时长',
    dataIndex: 'learning_duration',
    sorter: true,
    width: 120,
  },
  {
    title: '添加到课堂次数',
    dataIndex: 'add_to_classroom_count',
    sorter: true,
    width: 140,
  }
];

// 路由
const router = useRouter();
const route = useRoute();

// 表格数据
const loading = ref(false);
const exportLoading = ref(false);
const tableData = ref<CourseDetailStatisticsItem[]>([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
});

// 页面数据
const courseId = ref<number>(Number(route.params.id));
const courseTitle = ref<string>('');
const timeRangeLabel = ref<string>('');

// 统计数据
const statisticsData = reactive({
  totalUsers: 0,
  totalAccesses: 0,
  totalLearning: 0,
  totalDuration: 0,
});

// 筛选条件
const searchKeyword = ref<string>('');
const employeeFilter = ref<string>('');
const collegeFilter = ref<string>('');
const majorFilter = ref<string>('');

// 返回上一页
const goBack = () => {
  router.go(-1);
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
    const params: Omit<CourseDetailStatisticsParams, 'course_id'> = {
      page: pagination.current,
      page_size: pagination.pageSize,
      // 从路由query中获取时间参数
      time_range: route.query.timeRange as any,
      start_date: route.query.startDate as string,
      end_date: route.query.endDate as string
    };

    // 添加筛选条件
    if (searchKeyword.value) {
      (params as any).name = searchKeyword.value;
    }
    if (employeeFilter.value) {
      (params as any).employee_id = employeeFilter.value;
    }
    if (collegeFilter.value) {
      (params as any).college = collegeFilter.value;
    }
    if (majorFilter.value) {
      (params as any).major = majorFilter.value;
    }

    // 请求数据
    const response = await getCourseDetailStatistics(courseId.value, params);

    if (response.code === '0000' && response.data) {
      courseTitle.value = response.data.course_title;
      timeRangeLabel.value = response.data.time_range_text;
      tableData.value = response.data.data;
      pagination.total = response.data.meta.total;
      
      // 更新统计数据
      statisticsData.totalUsers = response.data.meta.total;
      statisticsData.totalAccesses = response.data.data.reduce((sum, item) => sum + item.access_count, 0);
      statisticsData.totalLearning = response.data.data.reduce((sum, item) => sum + item.learning_count, 0);
      statisticsData.totalDuration = response.data.data.reduce((sum, item) => sum + item.learning_duration * 60, 0);
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
      export_type: 'course_detail' as const,
      export_format: 'xlsx' as const,
      course_id: courseId.value,
      time_range: route.query.timeRange,
      start_date: route.query.startDate,
      end_date: route.query.endDate,
      name: searchKeyword.value || undefined,
      employee_id: employeeFilter.value || undefined,
      college: collegeFilter.value || undefined,
      major: majorFilter.value || undefined
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
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-button {
  padding: 4px 8px;
  font-size: 14px;
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

.search-filter,
.employee-filter,
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

.user-name {
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