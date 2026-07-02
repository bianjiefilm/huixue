<template>
  <div class="statistics-container">
    <div class="page-header">
      <h2 class="page-title">课程统计分析 <span v-if="timeRangeLabel">({{ timeRangeLabel }})</span></h2>
    </div>

    <!-- 时间筛选 -->
    <div class="filter-bar">
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
    </div>

    <!-- 统计卡片 -->
    <div class="statistics-cards">
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="课程总数" :value="statisticsData.totalCourses" :valueStyle="{ color: '#3f8600' }">
          <template #prefix>
            <read-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="内置课程数" :value="statisticsData.systemCourses" :valueStyle="{ color: '#0096FF' }">
          <template #prefix>
            <database-outlined />
          </template>
        </a-statistic>
      </a-card>
      <a-card class="statistic-card" :bordered="false">
        <a-statistic title="教师公开课程数" :value="statisticsData.teacherPublicCourses" :valueStyle="{ color: '#722ED1' }">
          <template #prefix>
            <team-outlined />
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
      row-key="course_id"
      class="data-table"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'course_name'">
          <a @click="showCourseDetail(record)">{{ record.course_name }}</a>
        </template>
        <template v-else-if="column.dataIndex === 'course_type'">
          <a-tag :color="getTypeColor(record.course_type)">{{ record.course_type }}</a-tag>
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs, { Dayjs } from 'dayjs';
import { 
  ReadOutlined, 
  DatabaseOutlined, 
  TeamOutlined,
  ExportOutlined
} from '@ant-design/icons-vue';
import { 
  getCourseStatistics, 
  exportStatisticsData,
  TimeRange,
  formatTimeRangeText,
  type CourseStatisticsParams,
  type CourseStatisticsItem
} from '@/api/usage-statistics';

// 列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'course_id',
    width: 80,
  },
  {
    title: '课程名称',
    dataIndex: 'course_name',
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
  },
  {
    title: '创建课堂次数',
    dataIndex: 'classroom_creation_count',
    sorter: true,
  },
  {
    title: '类型',
    dataIndex: 'course_type',
  }
];

// 路由
const router = useRouter();

// 表格数据
const loading = ref(false);
const exportLoading = ref(false);
const tableData = ref<CourseStatisticsItem[]>([]);
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
  totalCourses: 0,
  systemCourses: 0,
  teacherPublicCourses: 0,
  totalVisits: 0,
  totalVisitors: 0,
  avgVisits: 0
});

// 时间筛选
const timeRange = ref<TimeRange>(TimeRange.TODAY);
const customDateRange = ref<[Dayjs, Dayjs]>([dayjs().subtract(7, 'day'), dayjs()]);
const platformCreatedDate = dayjs('2018-10-06'); // 平台创建日期

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

// 获取类型颜色
const getTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    '实践课程': 'blue',
    '实训课程': 'green',
    '课程教材': 'orange',
    '内置课程': 'purple'
  };
  return colorMap[type] || 'default';
};

// 获取课程类型显示名称
const getCourseTypeDisplayName = (type: string) => {
  const typeMap: Record<string, string> = {
    'PRACTICE': '实践课程',
    'TRAINING': '实训课程',
    'COURSE_MATERIAL': '课程教材',
    'SYSTEM': '内置课程'
  };
  return typeMap[type] || type;
};

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

// 处理表格变化（排序、分页）
const handleTableChange = (pag: any, filters: any, sorter: any) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  
  // 处理排序逻辑如果需要的话
  fetchData();
};

// 课程详情页
const showCourseDetail = (record: CourseStatisticsItem) => {
  router.push({
    path: `/admin/logs/course/${record.course_id}`,
    query: { 
      timeRange: timeRange.value,
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
    const params: CourseStatisticsParams = {
      page: pagination.current,
      page_size: pagination.pageSize,
      time_range: timeRange.value
    };

    // 处理自定义时间范围
    if (timeRange.value === TimeRange.CUSTOM && customDateRange.value) {
      params.start_date = customDateRange.value[0].format('YYYY-MM-DD');
      params.end_date = customDateRange.value[1].format('YYYY-MM-DD');
    }

    // 请求数据
    const response = await getCourseStatistics(params);

    if ((response.code === '0000' || response.code === 1) && response.data) {
      // 处理数据格式转换
      const rawData = response.data.data || [];
      tableData.value = rawData.map(item => ({
        ...item,
        course_type: getCourseTypeDisplayName(item.course_type)
      }));

      pagination.total = response.data.meta?.total || 0;

      // 更新统计数据
      statisticsData.totalCourses = response.data.meta?.total || 0;
      statisticsData.systemCourses = tableData.value.filter(item => item.course_type === '内置课程').length;
      statisticsData.teacherPublicCourses = tableData.value.filter(item => item.course_type === '教师课程').length;
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
      export_type: 'course' as const,
      export_format: 'xlsx' as const,
      time_range: timeRange.value,
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
}

.custom-date-picker {
  margin-left: 16px;
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

.action-bar {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style> 