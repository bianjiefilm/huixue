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
                <h5>{{ server.node_name }}</h5>
                <div class="resource-stats">
                  <div class="resource-item">
                    <div>CPU使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.cpu_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.cpu_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_cpu_cores }} 核</div>
                  </div>
                  <div class="resource-item">
                    <div>内存使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.memory_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.memory_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_memory_gb }} GB</div>
                  </div>
                  <div class="resource-item">
                    <div>存储使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.storage_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.storage_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_storage_gb }} GB</div>
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
                <h5>{{ server.node_name }}</h5>
                <div class="resource-stats">
                  <div class="resource-item">
                    <div>CPU使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.cpu_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.cpu_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_cpu_cores }} 核</div>
                  </div>
                  <div class="resource-item">
                    <div>内存使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.memory_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.memory_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_memory_gb }} GB</div>
                  </div>
                  <div class="resource-item">
                    <div>存储使用率</div>
                    <a-progress
                      type="circle"
                      :percent="server.storage_usage_percent"
                      :width="80"
                      :status="getResourceStatus(server.storage_usage_percent)"
                      :format="(percent: number) => `${percent}%`"
                    />
                    <div class="resource-detail">{{ server.total_storage_gb }} GB</div>
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
        
        <!-- 容器进程表格 -->
        <a-table
          :columns="containerColumns"
          :data-source="containerProcesses"
          :row-selection="rowSelection"
          :pagination="{
            total: containerTotal,
            current: containerPagination.page,
            pageSize: containerPagination.pageSize,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total: number, range: [number, number]) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
            onChange: handlePageChange,
            onShowSizeChange: handlePageSizeChange
          }"
          :loading="loading.containers"
          :scroll="{ x: 1200 }"
          size="small"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'userName'">
              <div>
                <div>{{ record.user_name }}</div>
                <div class="sub-text">{{ record.user_id }}</div>
              </div>
            </template>
            <template v-else-if="column.key === 'courseName'">
              <div v-if="record.course_name">
                <div>{{ record.course_name }}</div>
                <div class="sub-text">ID: {{ record.course_id }}</div>
              </div>
              <span v-else class="text-gray">-</span>
            </template>
            <template v-else-if="column.key === 'environmentType'">
              <a-tag :color="getEnvironmentTypeColor(record.environment_type)">
                {{ getEnvironmentTypeText(record.environment_type) }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'startTime'">
              {{ formatDateTime(record.start_time) }}
            </template>
            <template v-else-if="column.key === 'runningTime'">
              {{ formatRunningTime(record.running_time) }}
            </template>
            <template v-else-if="column.key === 'cpu'">
              {{ record.cpu_usage?.toFixed(1) }}%
            </template>
            <template v-else-if="column.key === 'memory'">
              <div>
                <div>{{ formatMemory(record.memory_usage || 0) }}/{{ formatMemory(record.memory_limit || 0) }}</div>
                <div class="sub-text">{{ ((record.memory_usage || 0) / (record.memory_limit || 1) * 100).toFixed(1) }}%</div>
              </div>
            </template>
            <template v-else-if="column.key === 'action'">
              <a-button 
                type="primary" 
                danger 
                size="small"
                :loading="record.stopping"
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
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { message, Empty } from 'ant-design-vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import {
  getServerNodesOverview,
  getContainerProcesses,
  updateConcurrentExperimentSetting,
  getConcurrentExperimentSetting,
  stopContainer,
  batchStopContainers,

  type ContainerProcess,
  type ConcurrentExperimentSetting
} from '@/api/teaching-resources';

// 本地类型定义
interface ServerNode {
  id: number
  node_name: string
  node_type: string
  ip_address: string
  total_cpu_cores: number
  total_memory_gb: number
  total_storage_gb: number
  cpu_usage_percent: number
  memory_usage_percent: number
  storage_usage_percent: number
  status: string
  last_heartbeat: string
  is_active: boolean
  created_at: string
  updated_at?: string
  cpu_status_color: string
  memory_status_color: string
  storage_status_color: string
}

// 响应式数据
const applicationServers = ref<ServerNode[]>([]);
const computeServers = ref<ServerNode[]>([]);
const containerProcesses = ref<ContainerProcess[]>([]);
const selectedContainerIds = ref<string[]>([]);
const containerTotal = ref(0);

// 并发实验设置
const concurrentSetting = ref<ConcurrentExperimentSetting>({
  enabled: false,
  updated_at: '',
  updated_by: ''
});

// 加载状态
const loading = ref({
  serverResources: false,
  containers: false,
  concurrentSetting: false,
  batchStop: false
});

// 筛选条件
const filters = ref({
  keyword: '',
  environmentType: '',
  rangeType: 'startTime',
  timeRange: [] as any[],
  valueRange: [null, null] as (number | null)[]
});

// 分页
const containerPagination = ref({
  page: 1,
  pageSize: 20
});

// 定时器
let serverResourceTimer: number | undefined;
let containerListTimer: number | undefined;

// 表格列定义
const containerColumns = [
  {
    title: '选择',
    width: 60,
    key: 'selection'
  },
  {
    title: '用户',
    dataIndex: 'userName',
    key: 'userName',
    width: 120
  },
  {
    title: '课程',
    dataIndex: 'courseName',
    key: 'courseName',
    width: 150
  },
  {
    title: '实验类型',
    dataIndex: 'environmentType',
    key: 'environmentType',
    width: 100
  },
  {
    title: '开始时间',
    dataIndex: 'startTime',
    key: 'startTime',
    width: 170
  },
  {
    title: '运行时长',
    dataIndex: 'runningTime',
    key: 'runningTime',
    width: 120
  },
  {
    title: 'CPU',
    dataIndex: 'cpu',
    key: 'cpu',
    width: 80
  },
  {
    title: '内存',
    dataIndex: 'memory',
    key: 'memory',
    width: 120
  },
  {
    title: '操作',
    key: 'action',
    width: 80,
    fixed: 'right'
  }
];

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedContainerIds,
  onChange: (selectedRowKeys: string[]) => {
    selectedContainerIds.value = selectedRowKeys;
  }
};

// 页面加载时获取数据
onMounted(async () => {
  await Promise.all([
    fetchServerResources(),
    fetchContainerList(),
    fetchConcurrentSetting()
  ]);
  
  // 设置定时刷新
  serverResourceTimer = window.setInterval(fetchServerResources, 15000); // 15秒
  containerListTimer = window.setInterval(fetchContainerList, 5000); // 5秒
});

// 页面卸载时清除定时器
onUnmounted(() => {
  if (serverResourceTimer) {
    clearInterval(serverResourceTimer);
  }
  if (containerListTimer) {
    clearInterval(containerListTimer);
  }
});

// 获取服务器资源
const fetchServerResources = async () => {
  try {
    loading.value.serverResources = true;
    const response = await getServerNodesOverview();
    if (response.code === '0000' || response.code === 200) {
      // 转换API返回格式为前端期望的格式
      const transformServer = (server: any) => ({
        id: server.id,
        node_name: server.name,
        cpu_usage_percent: Math.round(server.cpu_usage || 0),
        memory_usage_percent: Math.round(server.memory_usage || 0),
        storage_usage_percent: Math.round(server.disk_usage || 0),
        total_cpu_cores: server.container_count || 4,
        total_memory_gb: Math.round((server.memory_total || 16384) / 1024),
        total_storage_gb: server.disk_total || 500
      });
      applicationServers.value = (response.data.application_servers || []).map(transformServer);
      computeServers.value = (response.data.compute_servers || []).map(transformServer);
    } else {
      message.error('获取服务器资源失败: ' + response.message);
    }
  } catch (error) {
    console.error('Error fetching server resources:', error);
    message.error('获取服务器资源失败');
  } finally {
    loading.value.serverResources = false;
  }
};

// 获取容器列表
const fetchContainerList = async () => {
  try {
    loading.value.containers = true;
    
    // 构建API参数
    const params: any = {
      page: containerPagination.value.page,
      page_size: containerPagination.value.pageSize
    };
    
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword;
    }
    
    if (filters.value.environmentType) {
      params.environment_type = filters.value.environmentType;
    }
    
    // 时间范围筛选
    if (filters.value.rangeType === 'startTime' && filters.value.timeRange && filters.value.timeRange.length === 2) {
      params.start_time_begin = filters.value.timeRange[0];
      params.start_time_end = filters.value.timeRange[1];
    }
    
    // 数值范围筛选
    if (filters.value.rangeType !== 'startTime' && filters.value.valueRange && filters.value.valueRange.length === 2) {
      const [min, max] = filters.value.valueRange;
      if (min !== null && max !== null) {
        switch (filters.value.rangeType) {
          case 'runningTime':
            params.duration_min = min;
            params.duration_max = max;
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
    }
    
    const response = await getContainerProcesses(params);
    if (response.code === '0000' || response.code === 200) {
      containerProcesses.value = response.data.items || response.data.list || [];
      containerTotal.value = response.data.total || response.data.meta?.total || 0;
    } else {
      message.error('获取容器进程失败: ' + response.message);
    }
  } catch (error) {
    console.error('Error fetching container processes:', error);
    message.error('获取容器进程失败');
  } finally {
    loading.value.containers = false;
  }
};

// 获取并发实验设置
const fetchConcurrentSetting = async () => {
  try {
    const response = await getConcurrentExperimentSetting();
    if (response.code === '0000' || response.code === 200) {
      concurrentSetting.value = response.data;
    } else {
      message.error('获取并发实验设置失败: ' + response.message);
    }
  } catch (error) {
    console.error('Error fetching concurrent setting:', error);
    message.error('获取并发实验设置失败');
  }
};

// 刷新容器列表
const refreshContainerList = async () => {
  await fetchContainerList();
  message.success('容器列表已刷新');
};

// 并发实验设置变更
const handleConcurrentSettingChange = async (checked: boolean) => {
  try {
    loading.value.concurrentSetting = true;
    const response = await updateConcurrentExperimentSetting({
      enable: checked,
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === '0000' || response.code === 200) {
      concurrentSetting.value.enabled = checked;
      message.success(checked ? '已开启同时进行多个实验' : '已关闭同时进行多个实验');
      
      // 如果关闭了并发实验且有容器被停止，刷新列表
      if (!checked && response.data.stopped_count > 0) {
        message.info(`已自动停止 ${response.data.stopped_count} 个多余的容器`);
        await fetchContainerList();
      }
    } else {
      message.error('设置失败: ' + response.message);
      // 恢复开关状态
      concurrentSetting.value.enabled = !checked;
    }
  } catch (error) {
    console.error('Error updating concurrent setting:', error);
    message.error('设置失败');
    // 恢复开关状态
    concurrentSetting.value.enabled = !checked;
  } finally {
    loading.value.concurrentSetting = false;
  }
};

// 停止单个容器
const handleStopContainer = async (containerId: string) => {
  try {
    // 设置加载状态
    const container = containerProcesses.value.find(c => c.id === containerId);
    if (container) {
      (container as any).stopping = true;
    }
    
    const response = await stopContainer(containerId, {
      reason: '管理员手动停止',
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === '0000' || response.code === 200) {
      message.success('容器已停止');
      // 从列表中移除已停止的容器
      const index = containerProcesses.value.findIndex(c => c.id === containerId);
      if (index !== -1) {
        containerProcesses.value.splice(index, 1);
        containerTotal.value -= 1;
      }
      // 如果当前选中包含该容器，也要移除
      const selectedIndex = selectedContainerIds.value.indexOf(containerId);
      if (selectedIndex !== -1) {
        selectedContainerIds.value.splice(selectedIndex, 1);
      }
    } else {
      message.error('停止容器失败: ' + response.message);
    }
  } catch (error) {
    console.error('Error stopping container:', error);
    message.error('停止容器失败');
  } finally {
    // 清除加载状态
    const container = containerProcesses.value.find(c => c.id === containerId);
    if (container) {
      (container as any).stopping = false;
    }
  }
};

// 批量停止容器
const handleBatchStop = async () => {
  if (selectedContainerIds.value.length === 0) {
    message.warning('请先选择要停止的容器');
    return;
  }
  
  try {
    loading.value.batchStop = true;
    const response = await batchStopContainers({
      container_ids: selectedContainerIds.value,
      reason: '管理员批量停止',
      operator_id: 1 // TODO: 获取当前用户ID
    });
    
    if (response.code === '0000' || response.code === 200) {
      const { success_count, failed_count, stopped_count } = response.data;
      const actualSuccessCount = success_count || stopped_count || 0;
      
      if (failed_count > 0) {
        message.warning(`批量停止完成，成功 ${success_count} 个，失败 ${failed_count} 个`);
      } else {
        message.success(`已成功停止 ${success_count} 个容器`);
      }
      
      // 从列表中移除已成功停止的容器
      response.data.results.forEach((result: any) => {
        if (result.success) {
          const index = containerProcesses.value.findIndex(c => c.id === result.container_id);
          if (index !== -1) {
            containerProcesses.value.splice(index, 1);
            containerTotal.value -= 1;
          }
        }
      });
      
      // 清空选择
      selectedContainerIds.value = [];
    } else {
      message.error('批量停止失败: ' + response.message);
    }
  } catch (error) {
    console.error('Error batch stopping containers:', error);
    message.error('批量停止失败');
  } finally {
    loading.value.batchStop = false;
  }
};

// 筛选变更
const handleFilterChange = () => {
  containerPagination.value.page = 1; // 重置到第一页
  fetchContainerList();
};

// 范围类型变更
const handleRangeTypeChange = () => {
  filters.value.timeRange = [];
  filters.value.valueRange = [null, null];
  handleFilterChange();
};

// 重置筛选条件
const resetFilters = () => {
  filters.value = {
    keyword: '',
    environmentType: '',
    rangeType: 'startTime',
    timeRange: [],
    valueRange: [null, null]
  };
  containerPagination.value.page = 1;
  fetchContainerList();
};

// 分页变更
const handlePageChange = (page: number) => {
  containerPagination.value.page = page;
  fetchContainerList();
};

// 页大小变更
const handlePageSizeChange = (current: number, size: number) => {
  containerPagination.value.page = 1;
  containerPagination.value.pageSize = size;
  fetchContainerList();
};

// 工具函数
const getResourceStatus = (usageRate: number) => {
  if (usageRate >= 80) {
    return 'exception';
  } else if (usageRate >= 50) {
    return 'warning';
  }
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

const formatDateTime = (dateTime: string) => {
  return new Date(dateTime).toLocaleString('zh-CN');
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
  padding: 16px;
}

.monitor-card {
  margin-bottom: 16px;
}

.monitor-header {
  margin-bottom: 20px;
}

.monitor-header h3 {
  margin: 0;
  color: #1890ff;
  font-size: 18px;
  font-weight: 600;
}

.subtitle {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

.resource-card {
  height: 100%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.resource-card h5 {
  margin: 0 0 16px 0;
  color: #262626;
  font-size: 14px;
  font-weight: 600;
  text-align: center;
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
  text-align: center;
}

.resource-item > div:first-child {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.resource-detail {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}

.settings-card {
  margin-bottom: 16px;
}

.concurrent-setting {
  display: flex;
  align-items: center;
  gap: 12px;
}

.setting-label {
  font-size: 14px;
  color: #262626;
  font-weight: 500;
}

.container-card {
  margin-bottom: 16px;
}

.container-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.container-header h3 {
  margin: 0;
  color: #1890ff;
  font-size: 18px;
  font-weight: 600;
}

.filter-container {
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
  margin-bottom: 16px;
}

.sub-text {
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.text-gray {
  color: #999;
}

/* 进度条状态颜色 */
:deep(.ant-progress-circle .ant-progress-text) {
  font-size: 10px !important;
}

:deep(.ant-progress-circle) {
  width: 80px !important;
  height: 80px !important;
}

/* 表格样式 */
:deep(.ant-table-thead > tr > th) {
  background: #fafafa;
  font-weight: 600;
  color: #262626;
}

:deep(.ant-table-tbody > tr > td) {
  padding: 8px 12px;
}

:deep(.ant-table-tbody > tr:hover > td) {
  background: #f5f5f5;
}

/* 标签样式 */
:deep(.ant-tag) {
  border-radius: 4px;
  font-size: 12px;
}

/* 按钮样式 */
:deep(.ant-btn-sm) {
  height: 24px;
  padding: 0 8px;
  font-size: 12px;
}

/* 开关样式 */
:deep(.ant-switch) {
  background-color: #bfbfbf;
}

:deep(.ant-switch-checked) {
  background-color: #1890ff;
}

/* 分页样式 */
:deep(.ant-pagination) {
  text-align: right;
  margin-top: 16px;
}
</style> 