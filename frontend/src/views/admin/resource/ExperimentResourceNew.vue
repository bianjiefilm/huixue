<template>
  <div class="experiment-resource-management">
    <a-page-header title="实验资源管理" :ghost="false" />
    
    <!-- 服务器资源监控 -->
    <a-card :bordered="false" class="monitor-card">
      <div class="monitor-header">
        <h3>服务器资源监控</h3>
        <div class="subtitle">每15秒自动刷新一次</div>
      </div>
      
      <a-row :gutter="24">
        <a-col :span="12">
          <h4>应用服务器</h4>
          <a-row :gutter="16" v-if="applicationServers.length > 0">
            <a-col :span="8" v-for="server in applicationServers" :key="server.id">
              <a-card :bordered="false" class="resource-card">
                <h5>{{ server.name }}</h5>
                <div class="resource-stats">
                  <div class="resource-item">
                    <div>CPU使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.cpu.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.cpu.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.cpu.used }}/{{ server.cpu.total }} 核</div>
                  </div>
                  <div class="resource-item">
                    <div>内存使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.memory.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.memory.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ formatMemory(server.memory.used) }}/{{ formatMemory(server.memory.total) }}</div>
                  </div>
                  <div class="resource-item">
                    <div>存储使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.storage.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.storage.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ formatMemory(server.storage.used) }}/{{ formatMemory(server.storage.total) }}</div>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
          <a-empty v-else description="暂无应用服务器数据" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
        </a-col>

        <a-col :span="12">
          <h4>计算节点</h4>
          <a-row :gutter="16" v-if="computeServers.length > 0">
            <a-col :span="8" v-for="server in computeServers" :key="server.id">
              <a-card :bordered="false" class="resource-card">
                <h5>{{ server.name }}</h5>
                <div class="resource-stats">
                  <div class="resource-item">
                    <div>CPU使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.cpu.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.cpu.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.cpu.used }}/{{ server.cpu.total }} 核</div>
                  </div>
                  <div class="resource-item">
                    <div>内存使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.memory.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.memory.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ formatMemory(server.memory.used) }}/{{ formatMemory(server.memory.total) }}</div>
                  </div>
                  <div class="resource-item">
                    <div>存储使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.storage.usageRate"
                      :width="80"
                      :status="getResourceStatus(server.storage.usageRate)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ formatMemory(server.storage.used) }}/{{ formatMemory(server.storage.total) }}</div>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
          <a-empty v-else description="暂无计算节点数据" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 并发实验设置 -->
    <a-card :bordered="false" class="settings-card">
      <div class="concurrent-setting">
        <span class="setting-label">允许同时开启多个实验</span>
        <a-switch 
          v-model:checked="concurrentSetting.enabled" 
          @change="handleConcurrentSettingChange"
          :loading="loading.concurrentSetting"
        />
      </div>
    </a-card>

    <!-- 容器进程管理 -->
    <a-card :bordered="false" class="container-card">
      <a-space direction="vertical" style="width: 100%">
        <div class="container-header">
          <div>
            <h3>容器进程管理</h3>
            <div class="subtitle">列表每5秒自动刷新一次</div>
          </div>
          <a-space>
            <a-button
              type="primary"
              danger
              :disabled="selectedContainerIds.length === 0"
              :loading="loading.batchStop"
              @click="handleBatchStop"
            >
              批量停止 ({{ selectedContainerIds.length }})
            </a-button>
            <a-button @click="refreshContainerList" :loading="loading.containers">
              <template #icon><ReloadOutlined /></template>
              刷新
            </a-button>
          </a-space>
        </div>
        
        <!-- 筛选条件 -->
        <div class="filter-container">
          <a-row :gutter="16">
            <a-col :span="5">
              <a-input
                v-model:value="filters.keyword"
                placeholder="搜索姓名、账号或课程名"
                @change="handleFilterChange"
              />
            </a-col>
            <a-col :span="4">
              <a-select
                v-model:value="filters.environmentType"
                placeholder="实验类型"
                style="width: 100%"
                @change="handleFilterChange"
              >
                <a-select-option value="">全部类型</a-select-option>
                <a-select-option value="普通实践">普通实践</a-select-option>
                <a-select-option value="jupyter">Jupyter</a-select-option>
                <a-select-option value="云桌面">云桌面</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="5">
              <a-select
                v-model:value="filters.rangeType"
                style="width: 100%"
                @change="handleRangeTypeChange"
              >
                <a-select-option value="startTime">开启时间</a-select-option>
                <a-select-option value="runningTime">运行时长</a-select-option>
                <a-select-option value="cpu">CPU使用率</a-select-option>
                <a-select-option value="memory">内存使用率</a-select-option>
              </a-select>
            </a-col>
            <a-col :span="8">
              <!-- 日期选择器 -->
              <a-range-picker
                v-if="filters.rangeType === 'startTime'"
                v-model:value="filters.timeRange"
                :show-time="{ format: 'HH:mm:ss' }"
                format="YYYY-MM-DD HH:mm:ss"
                style="width: 100%"
                @change="handleFilterChange"
              />
              <!-- 数值输入 -->
              <a-row :gutter="8" v-else>
                <a-col :span="11">
                  <a-input-number
                    v-model:value="filters.valueRange[0]"
                    :min="0"
                    :precision="0"
                    style="width: 100%"
                    @change="handleFilterChange"
                    :placeholder="getRangeTypePlaceholder(filters.rangeType, 'min')"
                  />
                </a-col>
                <a-col :span="2" style="text-align: center">-</a-col>
                <a-col :span="11">
                  <a-input-number
                    v-model:value="filters.valueRange[1]"
                    :min="filters.valueRange[0] || 0"
                    :precision="0"
                    style="width: 100%"
                    @change="handleFilterChange"
                    :placeholder="getRangeTypePlaceholder(filters.rangeType, 'max')"
                  />
                </a-col>
              </a-row>
            </a-col>
            <a-col :span="2">
              <a-button @click="resetFilters">重置</a-button>
            </a-col>
          </a-row>
        </div>

        <!-- 容器列表 -->
        <a-table
          :loading="loading.containers"
          :dataSource="containerProcesses"
          :columns="columns"
          rowKey="id"
          :row-selection="{
            selectedRowKeys: selectedContainerIds,
            onChange: onSelectionChange
          }"
          :pagination="{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showTotal: (total: number) => `共 ${total} 条`,
            onChange: handlePageChange
          }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'experimentType'">
              <a-tag :color="getEnvironmentTypeColor(record.environment_type)">
                {{ getEnvironmentTypeText(record.environment_type) }}
              </a-tag>
            </template>
            
            <template v-else-if="column.key === 'startTime'">
              {{ formatTime(record.start_time) }}
            </template>
            
            <template v-else-if="column.key === 'runningTime'">
              {{ formatRunningTime(record.running_time) }}
            </template>
            
            <template v-else-if="column.key === 'cpu'">
              {{ record.cpu_usage.toFixed(1) }}%
            </template>
            
            <template v-else-if="column.key === 'memory'">
              {{ formatMemory(record.memory_usage) }}/{{ formatMemory(record.memory_limit) }}
            </template>
            
            <template v-else-if="column.key === 'action'">
              <a-button
                size="small"
                danger
                :loading="loadingContainers.includes(record.id)"
                @click="handleStopContainer(record.id)"
              >
                停止
              </a-button>
            </template>
          </template>
        </a-table>
      </a-space>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { message, Empty } from 'ant-design-vue';
import type { Dayjs } from 'dayjs';
import {
  type ServerResource,
  type ContainerProcess,
  type ConcurrentExperimentSetting,
  EnvironmentType,
  getServerNodesOverview,
  getContainerProcesses,
  refreshServerNodes,
  refreshContainerProcesses,
  getConcurrentExperimentSetting,
  updateConcurrentExperimentSetting,
  stopContainer,
  batchStopContainers
} from '@/api/teaching-resources';

// 数据状态
const serverResources = ref<ServerResource[]>([]);
const containerProcesses = ref<ContainerProcess[]>([]);
const concurrentSetting = ref<ConcurrentExperimentSetting>({
  enabled: false,
  updated_at: '',
  updated_by: ''
});

// 加载状态
const loading = reactive({
  servers: false,
  containers: false,
  concurrentSetting: false,
  batchStop: false
});

const loadingContainers = ref<string[]>([]);

// 选中的容器
const selectedContainerIds = ref<string[]>([]);

// 分页状态
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
});

// 筛选条件
const filters = reactive({
  keyword: '',
  environmentType: '',
  rangeType: 'startTime' as 'startTime' | 'runningTime' | 'cpu' | 'memory',
  timeRange: [] as Dayjs[],
  valueRange: [null, null] as (number | null)[]
});

// 计算属性
const applicationServers = computed(() => 
  serverResources.value.filter(server => server.type === 'application')
);

const computeServers = computed(() => 
  serverResources.value.filter(server => server.type === 'compute')
);

// 表格列定义
const columns = [
  {
    title: '序号',
    dataIndex: 'id',
    key: 'id',
    width: 80
  },
  {
    title: '姓名',
    dataIndex: 'user_name',
    key: 'userName',
    width: 120,
    sorter: (a: ContainerProcess, b: ContainerProcess) => a.user_name.localeCompare(b.user_name)
  },
  {
    title: '账号',
    dataIndex: 'user_id',
    key: 'userId',
    width: 140
  },
  {
    title: '课程名称',
    dataIndex: 'course_name',
    key: 'courseName',
    ellipsis: true,
    width: 200
  },
  {
    title: '实验类型',
    key: 'experimentType',
    width: 120
  },
  {
    title: '开始时间',
    key: 'startTime',
    width: 180,
    sorter: (a: ContainerProcess, b: ContainerProcess) => 
      new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
  },
  {
    title: '运行时长',
    key: 'runningTime',
    width: 120,
    sorter: (a: ContainerProcess, b: ContainerProcess) => a.running_time - b.running_time
  },
  {
    title: 'CPU',
    key: 'cpu',
    width: 100,
    sorter: (a: ContainerProcess, b: ContainerProcess) => a.cpu_usage - b.cpu_usage
  },
  {
    title: '内存',
    key: 'memory',
    width: 140
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
    fixed: 'right'
  }
];

// 定时器
let serverResourceTimer: number | undefined;
let containerProcessTimer: number | undefined;

// 初始化数据
onMounted(async () => {
  await Promise.all([
    fetchServerResources(),
    fetchContainerProcesses(),
    fetchConcurrentSetting()
  ]);
  
  // 设置定时刷新
  serverResourceTimer = window.setInterval(fetchServerResources, 15000); // 15秒
  containerProcessTimer = window.setInterval(fetchContainerProcesses, 5000); // 5秒
});

onUnmounted(() => {
  if (serverResourceTimer) {
    clearInterval(serverResourceTimer);
  }
  if (containerProcessTimer) {
    clearInterval(containerProcessTimer);
  }
});

// 获取服务器资源
const fetchServerResources = async () => {
  try {
    loading.servers = true;
    const response = await getServerNodesOverview();
    if (response.code === "0000" || response.code === 200) {
      const { application_servers, compute_servers } = response.data;
      // 转换API返回格式为前端期望的格式
      const transformServer = (server: any, serverType: 'application' | 'compute') => ({
        id: server.id,
        name: server.name,
        type: serverType,
        status: server.status,
        cpu: {
          used: Math.round(server.cpu_usage * (server.container_count || 1) / 10),
          total: Math.round(server.container_count || 4),
          usageRate: Math.round(server.cpu_usage || 0)
        },
        memory: {
          used: Math.round((server.memory_usage / 100) * (server.memory_total || 16384)),
          total: server.memory_total || 16384,
          usageRate: Math.round(server.memory_usage || 0)
        },
        storage: {
          used: Math.round((server.disk_usage / 100) * (server.disk_total || 500)),
          total: server.disk_total || 500,
          usageRate: Math.round(server.disk_usage || 0)
        }
      });
      serverResources.value = [
        ...application_servers.map((server: any) => transformServer(server, 'application')),
        ...compute_servers.map((server: any) => transformServer(server, 'compute'))
      ];
    } else {
      console.error('获取服务器资源失败:', response.message);
    }
  } catch (error) {
    console.error('获取服务器资源失败:', error);
  } finally {
    loading.servers = false;
  }
};

// 获取容器进程
const fetchContainerProcesses = async () => {
  try {
    loading.containers = true;
    
    // 构建API参数
    const params: any = {
      page: pagination.current,
      page_size: pagination.pageSize
    };
    
    if (filters.keyword) {
      params.keyword = filters.keyword;
    }
    
    if (filters.environmentType) {
      params.environment_type = filters.environmentType;
    }
    
    // 时间范围筛选
    if (filters.rangeType === 'startTime' && filters.timeRange && filters.timeRange.length === 2) {
      params.start_time_begin = filters.timeRange[0].format('YYYY-MM-DD HH:mm:ss');
      params.start_time_end = filters.timeRange[1].format('YYYY-MM-DD HH:mm:ss');
    }
    
    // 数值范围筛选
    if (filters.rangeType !== 'startTime' && filters.valueRange.every(v => v !== null)) {
      const [min, max] = filters.valueRange;
      switch (filters.rangeType) {
        case 'runningTime':
          params.duration_min = min! / 60; // 转换为分钟
          params.duration_max = max! / 60;
          break;
        case 'cpu':
          params.cpu_min = min;
          params.cpu_max = max;
          break;
        case 'memory':
          params.memory_min = min;
          params.memory_max = max;
          break;
      }
    }
    
    const response = await getContainerProcesses(params);
    if (response.code === 200) {
      containerProcesses.value = response.data.items;
      pagination.total = response.data.total;
    } else {
      console.error('获取容器进程失败:', response.message);
    }
  } catch (error) {
    console.error('获取容器进程失败:', error);
  } finally {
    loading.containers = false;
  }
};

// 获取并发实验设置
const fetchConcurrentSetting = async () => {
  try {
    const response = await getConcurrentExperimentSetting();
    if (response.code === 200) {
      concurrentSetting.value = response.data;
    } else {
      console.error('获取并发实验设置失败:', response.message);
    }
  } catch (error) {
    console.error('获取并发实验设置失败:', error);
  }
};

// 刷新容器列表
const refreshContainerList = async () => {
  await fetchContainerProcesses();
};

// 处理并发设置变更
const handleConcurrentSettingChange = async (checked: boolean) => {
  try {
    loading.concurrentSetting = true;
    const response = await updateConcurrentExperimentSetting({
      enable: checked,
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === 200) {
      message.success(checked ? '已启用并发实验' : '已禁用并发实验');
      concurrentSetting.value.enabled = checked;
      
      // 如果禁用并发实验并且有容器被停止，刷新列表
      if (!checked && response.data.stopped_count > 0) {
        message.info(`已自动停止 ${response.data.stopped_count} 个多余的实验容器`);
        await fetchContainerProcesses();
      }
    } else {
      message.error(response.message || '设置失败');
      // 恢复开关状态
      concurrentSetting.value.enabled = !checked;
    }
  } catch (error) {
    console.error('设置并发实验失败:', error);
    message.error('设置失败');
    // 恢复开关状态
    concurrentSetting.value.enabled = !checked;
  } finally {
    loading.concurrentSetting = false;
  }
};

// 停止单个容器
const handleStopContainer = async (containerId: string) => {
  try {
    loadingContainers.value.push(containerId);
    const response = await stopContainer(containerId, {
      reason: '管理员手动停止',
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === 200) {
      message.success('容器已停止');
      await fetchContainerProcesses();
    } else {
      message.error(response.message || '停止容器失败');
    }
  } catch (error) {
    console.error('停止容器失败:', error);
    message.error('停止容器失败');
  } finally {
    const index = loadingContainers.value.indexOf(containerId);
    if (index > -1) {
      loadingContainers.value.splice(index, 1);
    }
  }
};

// 批量停止容器
const handleBatchStop = async () => {
  if (selectedContainerIds.value.length === 0) {
    message.warning('请选择要停止的容器');
    return;
  }
  
  try {
    loading.batchStop = true;
    const response = await batchStopContainers({
      container_ids: selectedContainerIds.value,
      reason: '管理员批量停止',
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === 200) {
      const { success_count, failed_count } = response.data;
      if (failed_count === 0) {
        message.success(`成功停止 ${success_count} 个容器`);
      } else {
        message.warning(`成功停止 ${success_count} 个容器，${failed_count} 个失败`);
      }
      
      selectedContainerIds.value = [];
      await fetchContainerProcesses();
    } else {
      message.error(response.message || '批量停止失败');
    }
  } catch (error) {
    console.error('批量停止容器失败:', error);
    message.error('批量停止失败');
  } finally {
    loading.batchStop = false;
  }
};

// 处理筛选条件变更
const handleFilterChange = () => {
  pagination.current = 1;
  fetchContainerProcesses();
};

// 处理范围类型变更
const handleRangeTypeChange = () => {
  filters.timeRange = [];
  filters.valueRange = [null, null];
  handleFilterChange();
};

// 重置筛选条件
const resetFilters = () => {
  filters.keyword = '';
  filters.environmentType = '';
  filters.rangeType = 'startTime';
  filters.timeRange = [];
  filters.valueRange = [null, null];
  pagination.current = 1;
  fetchContainerProcesses();
};

// 处理分页变更
const handlePageChange = (page: number, pageSize: number) => {
  pagination.current = page;
  pagination.pageSize = pageSize;
  fetchContainerProcesses();
};

// 处理表格选择
const onSelectionChange = (selectedRowKeys: string[]) => {
  selectedContainerIds.value = selectedRowKeys;
};

// 工具函数
const getResourceStatus = (usageRate: number) => {
  if (usageRate >= 80) return 'exception';
  if (usageRate >= 50) return 'warning';
  return 'success';
};

const formatMemory = (sizeInMB: number) => {
  if (sizeInMB >= 1024) {
    return `${(sizeInMB / 1024).toFixed(2)} GB`;
  }
  return `${sizeInMB} MB`;
};

const formatRunningTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;
  
  if (hours > 0) {
    return `${hours}小时${minutes}分${remainingSeconds}秒`;
  } else if (minutes > 0) {
    return `${minutes}分${remainingSeconds}秒`;
  }
  return `${remainingSeconds}秒`;
};

const formatTime = (timeString: string) => {
  return new Date(timeString).toLocaleString('zh-CN');
};

const getEnvironmentTypeText = (type: string) => {
  switch (type?.toLowerCase()) {
    case '普通实践':
    case 'normal':
      return '普通实践';
    case 'jupyter':
      return 'Jupyter';
    case '云桌面':
    case 'desktop':
      return '云桌面';
    default:
      return type || '未知类型';
  }
};

const getEnvironmentTypeColor = (type: string) => {
  switch (type?.toLowerCase()) {
    case '普通实践':
    case 'normal':
      return 'blue';
    case 'jupyter':
      return 'green';
    case '云桌面':
    case 'desktop':
      return 'purple';
    default:
      return 'default';
  }
};

const getRangeTypePlaceholder = (rangeType: string, position: 'min' | 'max') => {
  switch (rangeType) {
    case 'runningTime':
      return position === 'min' ? '最小时长(秒)' : '最大时长(秒)';
    case 'cpu':
      return position === 'min' ? '最小CPU(%)' : '最大CPU(%)';
    case 'memory':
      return position === 'min' ? '最小内存(MB)' : '最大内存(MB)';
    default:
      return position === 'min' ? '最小值' : '最大值';
  }
};
</script>

<style scoped>
.experiment-resource-management {
  padding: 24px;
}

.monitor-card {
  margin-bottom: 24px;
}

.monitor-header {
  margin-bottom: 16px;
}

.monitor-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.subtitle {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

.resource-card {
  height: 100%;
  text-align: center;
}

.resource-card h5 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
}

.resource-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.resource-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.resource-detail {
  font-size: 12px;
  color: #666;
}

.settings-card {
  margin-bottom: 24px;
}

.concurrent-setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
}

.container-card {
  margin-bottom: 24px;
}

.container-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.container-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.filter-container {
  margin-bottom: 16px;
}

:deep(.ant-table-thead > tr > th) {
  background-color: #fafafa;
  font-weight: 600;
}

:deep(.ant-progress-circle .ant-progress-text) {
  font-size: 12px;
}
</style> 