<template>
  <div class="statistics-container">
    <div class="page-header">
      <h2 class="page-title">教师使用统计</h2>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <!-- 搜索框 -->
      <div class="search-filter">
        <a-input
          v-model:value="searchKeyword"
          placeholder="搜索教师姓名或工号"
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
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="教师总数" :value="statisticsData.totalTeachers" :valueStyle="{ color: '#3f8600' }">
          <template #prefix>
            <user-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总课堂数" :value="statisticsData.totalClassrooms" :valueStyle="{ color: '#0096FF' }">
          <template #prefix>
            <home-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总实践数" :value="statisticsData.totalPractices" :valueStyle="{ color: '#722ED1' }">
          <template #prefix>
            <experiment-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="总实训数" :value="statisticsData.totalTrainings" :valueStyle="{ color: '#F5A623' }">
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
      row-key="teacher_id"
      class="data-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'real_name'">
          <span class="teacher-name">{{ record.real_name }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'employee_id'">
          <span class="employee-id">{{ record.employee_id || '-' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'organization_name'">
          <a-tag color="blue">{{ record.organization_name || '-' }}</a-tag>
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
import { message } from 'ant-design-vue';
import { 
  UserOutlined,
  HomeOutlined,
  ExperimentOutlined,
  LaptopOutlined,
  ExportOutlined,
  SearchOutlined
} from '@ant-design/icons-vue';
import { 
  getTeacherUsageStatistics, 
  exportStatisticsData,
  type TeacherUsageParams,
  type TeacherUsageItem
} from '@/api/usage-statistics';

// 列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'teacher_id',
    width: 80,
  },
  {
    title: '教师姓名',
    dataIndex: 'real_name',
  },
  {
    title: '工号',
    dataIndex: 'employee_id',
    width: 120,
  },
  {
    title: '学院',
    dataIndex: 'organization_name',
    width: 120,
  },
  {
    title: '创建课堂数',
    dataIndex: 'classroom_count',
    sorter: true,
    defaultSortOrder: 'descend',
    width: 120,
  },
  {
    title: '创建实践数',
    dataIndex: 'practice_count',
    sorter: true,
    width: 120,
  },
  {
    title: '个人发布实践数',
    dataIndex: 'personal_practice_count',
    sorter: true,
    width: 140,
  },
  {
    title: '公开发布实践数',
    dataIndex: 'public_practice_count',
    sorter: true,
    width: 140,
  },
  {
    title: '创建实训数',
    dataIndex: 'training_count',
    sorter: true,
    width: 120,
  },
  {
    title: '个人发布实训数',
    dataIndex: 'personal_training_count',
    sorter: true,
    width: 140,
  },
  {
    title: '公开发布实训数',
    dataIndex: 'public_training_count',
    sorter: true,
    width: 140,
  }
];

// 表格数据
const loading = ref(false);
const exportLoading = ref(false);
const tableData = ref<TeacherUsageItem[]>([]);
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
  totalTeachers: 0,
  totalClassrooms: 0,
  totalPractices: 0,
  totalTrainings: 0,
});

// 筛选条件
const searchKeyword = ref<string>('');
const collegeFilter = ref<string>('');

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
    const params: TeacherUsageParams = {
      page: pagination.current,
      page_size: pagination.pageSize,
      name: searchKeyword.value || undefined,
      college: collegeFilter.value || undefined
    };

    // 请求数据
    const response = await getTeacherUsageStatistics(params);

    if (response.code === '0000' && response.data) {
      tableData.value = response.data.data;
      pagination.total = response.data.meta.total;
      
      // 更新统计数据
      statisticsData.totalTeachers = response.data.meta.total;
      statisticsData.totalClassrooms = response.data.data.reduce((sum, item) => sum + item.classroom_count, 0);
      statisticsData.totalPractices = response.data.data.reduce((sum, item) => sum + item.practice_count, 0);
      statisticsData.totalTrainings = response.data.data.reduce((sum, item) => sum + item.training_count, 0);
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
      export_type: 'teacher' as const,
      export_format: 'xlsx' as const,
      name: searchKeyword.value || undefined,
      college: collegeFilter.value || undefined
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

.search-filter,
.college-filter {
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

.teacher-name {
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