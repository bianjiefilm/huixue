<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar :title="`实践统计分析${timeRangeLabel ? ' (' + timeRangeLabel + ')' : ''}`">
      <template #actions>
        <a-button type="primary" @click="exportData" :loading="exportLoading">
          <template #icon><export-outlined /></template>
          导出
        </a-button>
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3" align="center">
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
          <a-select
            v-model:value="userGroup"
            style="width: 120px"
            @change="handleUserGroupChange"
            allowClear
            placeholder="用户组"
          >
            <a-select-option value="teacher">教师</a-select-option>
            <a-select-option value="student">学生</a-select-option>
          </a-select>
          <a-input
            v-model:value="searchKeyword"
            placeholder="搜索实践名称"
            style="width: 200px"
            @pressEnter="handleSearch"
            allowClear
          >
            <template #suffix>
              <search-outlined @click="handleSearch" />
            </template>
          </a-input>
        </Stack>
      </template>
    </PageHeaderBar>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="statistics-cards">
      <a-col :span="8">
        <a-card class="statistic-card" :bordered="false">
          <a-statistic title="实践总数" :value="statisticsData.totalPractices" :valueStyle="{ color: 'var(--hx-color-success)' }">
            <template #prefix>
              <experiment-outlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="statistic-card" :bordered="false">
          <a-statistic title="总访问次数" :value="statisticsData.totalAccesses" :valueStyle="{ color: 'var(--hx-color-primary)' }">
            <template #prefix>
              <eye-outlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card class="statistic-card" :bordered="false">
          <a-statistic title="总学习次数" :value="statisticsData.totalLearning" :valueStyle="{ color: 'var(--hx-color-accent-purple)' }">
            <template #prefix>
              <book-outlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 表格数据 -->
    <a-table
      :columns="currentColumns"
      :data-source="tableData"
      :loading="loading"
      :pagination="pagination"
      @change="handleTableChange"
      row-key="practice_id"
      class="data-table"
    >
      <template #emptyText>
        <EmptyStateBlock description="暂无实践统计数据" />
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'practice_name'">
          <a @click="showPracticeDetail(record)">{{ record.practice_name }}</a>
        </template>
        <template v-else-if="column.dataIndex === 'learning_duration'">
          {{ formatDuration(record.learning_duration * 60) }}
        </template>
      </template>
    </a-table>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs, { Dayjs } from 'dayjs';
import { 
  ExperimentOutlined,
  EyeOutlined,
  BookOutlined,
  ExportOutlined,
  SearchOutlined
} from '@ant-design/icons-vue';
import { 
  getPracticeStatistics, 
  exportStatisticsData,
  TimeRange,
  UserGroup,
  formatTimeRangeText,
  formatDuration,
  type PracticeStatisticsParams,
  type PracticeStatisticsItem
} from '@/api/usage-statistics';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import Stack from '@/components/common/Stack.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

// 基础列定义
const baseColumns = [
  {
    title: '序号',
    dataIndex: 'practice_id',
    width: 80,
  },
  {
    title: '实践名称',
    dataIndex: 'practice_name',
  },
  {
    title: '访问次数',
    dataIndex: 'access_count',
    sorter: true,
    defaultSortOrder: 'descend'
  },
  {
    title: '访问人数',
    dataIndex: 'access_users',
    sorter: true,
  },
  {
    title: '人均访问次数',
    dataIndex: 'avg_access_per_user',
    sorter: true,
  }
];

// 教师端列
const teacherColumns = [
  ...baseColumns,
  {
    title: '添加到课堂次数',
    dataIndex: 'add_to_classroom_count',
    sorter: true,
  }
];

// 学生端列
const studentColumns = [
  ...baseColumns,
  {
    title: '学习次数',
    dataIndex: 'learning_count',
    sorter: true,
  },
  {
    title: '学习时长',
    dataIndex: 'learning_duration',
    sorter: true,
  }
];

// 路由
const router = useRouter();

// 表格数据
const loading = ref(false);
const exportLoading = ref(false);
const tableData = ref<PracticeStatisticsItem[]>([]);
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
  totalPractices: 0,
  totalAccesses: 0,
  totalLearning: 0,
});

// 筛选条件
const timeRange = ref<TimeRange>(TimeRange.TODAY);
const userGroup = ref<UserGroup | undefined>(undefined);
const searchKeyword = ref<string>('');
const customDateRange = ref<[Dayjs, Dayjs]>([dayjs().subtract(7, 'day'), dayjs()]);
const platformCreatedDate = dayjs('2018-10-06'); // 平台创建日期

// 当前使用的列配置
const currentColumns = computed(() => {
  if (userGroup.value === UserGroup.TEACHER) {
    return teacherColumns;
  } else if (userGroup.value === UserGroup.STUDENT) {
    return studentColumns;
  } else {
    // 全部用户组时，显示完整列
    return [
      ...baseColumns,
      {
        title: '学习次数',
        dataIndex: 'learning_count',
        sorter: true,
      },
      {
        title: '学习时长',
        dataIndex: 'learning_duration',
        sorter: true,
      },
      {
        title: '添加到课堂次数',
        dataIndex: 'add_to_classroom_count',
        sorter: true,
      }
    ];
  }
});

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

// 处理用户组变化
const handleUserGroupChange = () => {
  pagination.current = 1; // 重置到第一页
  fetchData();
};

// 处理搜索
const handleSearch = () => {
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

// 实践详情页
const showPracticeDetail = (record: PracticeStatisticsItem) => {
  router.push({
    path: `/admin/logs/practice/${record.practice_id}`,
    query: { 
      timeRange: timeRange.value,
      userGroup: userGroup.value,
      ...(timeRange.value === TimeRange.CUSTOM && customDateRange.value ? {
        startDate: customDateRange.value[0].format('YYYY-MM-DD'),
        endDate: customDateRange.value[1].format('YYYY-MM-DD')
      } : {})
    }
  });
};

// 获取数据
const fetchData = async () => {
  loading.value = true;
  try {
    // 构建查询参数
    const params: PracticeStatisticsParams = {
      page: pagination.current,
      page_size: pagination.pageSize,
      time_range: timeRange.value,
      user_group: userGroup.value,
      practice_name: searchKeyword.value || undefined
    };

    // 处理自定义时间范围
    if (timeRange.value === TimeRange.CUSTOM && customDateRange.value) {
      params.start_date = customDateRange.value[0].format('YYYY-MM-DD');
      params.end_date = customDateRange.value[1].format('YYYY-MM-DD');
    }

    // 请求数据
    const response = await getPracticeStatistics(params);

    if (response.code === '0000' && response.data) {
      tableData.value = response.data.data;
      pagination.total = response.data.meta.total;
      
      // 更新统计数据
      statisticsData.totalPractices = response.data.meta.total;
      statisticsData.totalAccesses = response.data.data.reduce((sum, item) => sum + item.access_count, 0);
      statisticsData.totalLearning = response.data.data.reduce((sum, item) => sum + item.learning_count, 0);
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
      export_type: 'practice' as const,
      export_format: 'xlsx' as const,
      time_range: timeRange.value,
      user_group: userGroup.value,
      practice_name: searchKeyword.value || undefined,
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
.admin-page {
  width: 100%;
}

.statistics-cards {
  margin-bottom: var(--hx-space-5);
}

.statistic-card {
  min-width: 0;
}

.data-table {
  background-color: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
}
</style> 