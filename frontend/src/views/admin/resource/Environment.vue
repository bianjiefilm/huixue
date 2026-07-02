<template>
  <div class="environment-management">
    <a-page-header title="实践环境管理" :ghost="false" />
    
    <a-card :bordered="false" class="content-card">
      <!-- 筛选条件 -->
      <div class="filter-container">
        <a-row :gutter="16">
          <a-col :span="6">
            <a-input-search
              v-model:value="filters.keyword"
              placeholder="搜索环境名称"
              style="width: 100%"
              @search="handleSearch"
              enter-button
            />
          </a-col>
          <a-col :span="4">
            <a-select
              v-model:value="filters.type"
              placeholder="环境类型"
              style="width: 100%"
              @change="handleSearch"
            >
              <a-select-option value="">全部类型</a-select-option>
              <a-select-option :value="EnvironmentType.NORMAL">普通实践</a-select-option>
              <a-select-option :value="EnvironmentType.JUPYTER">Jupyter</a-select-option>
              <a-select-option :value="EnvironmentType.DESKTOP">云桌面</a-select-option>
            </a-select>
          </a-col>
          <a-col :span="4">
            <a-button @click="resetFilters">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-col>
        </a-row>
      </div>
      
      <!-- 环境列表 -->
      <a-table
        :loading="loading.environmentConfigs"
        :dataSource="filteredEnvironments"
        :columns="columns"
        rowKey="id"
        :pagination="{ pageSize: 10, showTotal: (total: number) => `共 ${total} 条` }"
      >
        <!-- 环境类型列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="getEnvironmentTypeColor(record.type)">
              {{ getEnvironmentTypeText(record.type) }}
            </a-tag>
          </template>

          <!-- Docker镜像列 -->
          <template v-else-if="column.key === 'docker_image'">
            <span v-if="record.docker_image" class="docker-image">
              {{ record.docker_image }}
            </span>
            <span v-else class="no-image">未配置</span>
          </template>

          <!-- 状态列 -->
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'green' : 'default'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>

          <!-- 存储空间列 -->
          <template v-else-if="column.key === 'storage'">
            <div>
              <div>最小: {{ record.storage.min }} MB</div>
              <div>最大: {{ record.storage.max }} MB</div>
              <div>默认: {{ record.storage.default }} MB</div>
            </div>
          </template>
          
          <!-- 内存列 -->
          <template v-else-if="column.key === 'memory'">
            <div>
              <div>最小: {{ record.memory.min }} MB</div>
              <div>最大: {{ record.memory.max }} MB</div>
              <div>默认: {{ record.memory.default }} MB</div>
            </div>
          </template>
          
          <!-- CPU列 -->
          <template v-else-if="column.key === 'cpu'">
            <div>
              <div>最小: {{ record.cpu.min }} 核</div>
              <div>最大: {{ record.cpu.max }} 核</div>
              <div>默认: {{ record.cpu.default }} 核</div>
            </div>
          </template>
          
          <!-- 操作列 -->
          <template v-else-if="column.key === 'action'">
            <a-button type="primary" size="small" @click="editEnvironment(record)">编辑</a-button>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 编辑环境配置弹窗 -->
    <a-modal
      v-model:open="editModal.visible"
      title="高级配置"
      width="700px"
      @ok="handleSave"
      @cancel="cancelEdit"
      :confirmLoading="editModal.loading"
    >
      <div v-if="editModal.record" class="edit-form">
        <a-alert 
          message="警告" 
          description="修改环境配置会影响到平台内教师用户创建课程时所选用的实验环境，不建议手动修改。" 
          type="warning" 
          show-icon 
          style="margin-bottom: 20px"
        />
        
        <a-descriptions title="环境信息" bordered>
          <a-descriptions-item label="环境名称" :span="3">{{ editModal.record.name }}</a-descriptions-item>
          <a-descriptions-item label="环境类型" :span="3">
            <a-tag :color="getEnvironmentTypeColor(editModal.record.type)">
              {{ getEnvironmentTypeText(editModal.record.type) }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
        
        <a-divider />
        
        <h3>存储空间配置</h3>
        <a-row :gutter="16" class="config-row">
          <a-col :span="8">
            <a-form-item label="最小值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.storage.min" 
                :min="1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.storage.max" 
                :min="editModal.form.storage.min || 1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="默认值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.storage.default" 
                :min="editModal.form.storage.min || 1"
                :max="editModal.form.storage.max || 9999"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <h3>内存配置</h3>
        <a-row :gutter="16" class="config-row">
          <a-col :span="8">
            <a-form-item label="最小值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.memory.min" 
                :min="1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.memory.max" 
                :min="editModal.form.memory.min || 1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="默认值 (MB)" required>
              <a-input-number 
                v-model:value="editModal.form.memory.default" 
                :min="editModal.form.memory.min || 1"
                :max="editModal.form.memory.max || 9999"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <h3>CPU配置</h3>
        <a-row :gutter="16" class="config-row">
          <a-col :span="8">
            <a-form-item label="最小值 (核)" required>
              <a-input-number
                v-model:value="editModal.form.cpu.min"
                :min="1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="最大值 (核)" required>
              <a-input-number
                v-model:value="editModal.form.cpu.max"
                :min="editModal.form.cpu.min || 1"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="默认值 (核)" required>
              <a-input-number
                v-model:value="editModal.form.cpu.default"
                :min="editModal.form.cpu.min || 1"
                :max="editModal.form.cpu.max || 100"
                :precision="0"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider />

        <h3>Docker镜像配置</h3>
        <a-row :gutter="16" class="config-row">
          <a-col :span="16">
            <a-form-item label="镜像名称">
              <a-input
                v-model:value="editModal.form.docker_image"
                placeholder="例如: huixue/bigdata-env:latest"
              />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="服务端口">
              <a-input-number
                v-model:value="editModal.form.docker_port"
                :min="1"
                :max="65535"
                :precision="0"
                style="width: 100%"
                placeholder="默认8888"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <h3>其他配置</h3>
        <a-row :gutter="16" class="config-row">
          <a-col :span="24">
            <a-form-item label="环境描述">
              <a-textarea
                v-model:value="editModal.form.description"
                placeholder="请输入环境描述信息..."
                :rows="3"
                :maxLength="500"
                showCount
              />
            </a-form-item>
          </a-col>
        </a-row>
        <a-row :gutter="16" class="config-row">
          <a-col :span="24">
            <a-form-item label="启用状态">
              <a-switch
                v-model:checked="editModal.form.is_active"
                checked-children="启用"
                un-checked-children="禁用"
              />
              <span class="status-tip">禁用后，教师创建课程时将无法选择此环境</span>
            </a-form-item>
          </a-col>
        </a-row>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { 
  EnvironmentType, 
  type EnvironmentConfig,
  getEnvironmentConfigs,
  updateEnvironmentConfig 
} from '@/api/teaching-resources';

// 数据状态
const environmentConfigs = ref<EnvironmentConfig[]>([]);
const loading = reactive({
  environmentConfigs: false
});

// 筛选条件
const filters = reactive({
  keyword: '',
  type: ''
});

// 表格列定义
const columns = [
  {
    title: '环境名称',
    dataIndex: 'name',
    key: 'name',
    sorter: (a: EnvironmentConfig, b: EnvironmentConfig) => a.name.localeCompare(b.name)
  },
  {
    title: '环境类型',
    dataIndex: 'type',
    key: 'type',
    width: 100,
    filters: [
      { text: '普通实践', value: EnvironmentType.NORMAL },
      { text: 'Jupyter', value: EnvironmentType.JUPYTER },
      { text: '云桌面', value: EnvironmentType.DESKTOP }
    ],
    onFilter: (value: string, record: EnvironmentConfig) => record.type === value
  },
  {
    title: 'Docker镜像',
    dataIndex: 'docker_image',
    key: 'docker_image',
    width: 200,
    ellipsis: true
  },
  {
    title: '存储空间',
    dataIndex: 'storage',
    key: 'storage',
    width: 130
  },
  {
    title: '内存',
    dataIndex: 'memory',
    key: 'memory',
    width: 130
  },
  {
    title: 'CPU',
    dataIndex: 'cpu',
    key: 'cpu',
    width: 130
  },
  {
    title: '状态',
    dataIndex: 'is_active',
    key: 'is_active',
    width: 80
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    fixed: 'right'
  }
];

// 编辑环境配置弹窗状态
const editModal = reactive({
  visible: false,
  loading: false,
  record: null as EnvironmentConfig | null,
  form: {
    storage: {
      min: 0,
      max: 0,
      default: 0
    },
    memory: {
      min: 0,
      max: 0,
      default: 0
    },
    cpu: {
      min: 0,
      max: 0,
      default: 0
    },
    docker_image: '' as string,
    docker_port: 8888 as number,
    description: '' as string,
    is_active: true as boolean
  }
});

// 获取环境数据
const fetchEnvironmentConfigs = async () => {
  try {
    loading.environmentConfigs = true;
    const response = await getEnvironmentConfigs({
      environment_type: filters.type || undefined,
      keyword: filters.keyword || undefined,
      page: 1,
      page_size: 100
    });
    
    if (response.code === "0000" || response.code === 200) {
      environmentConfigs.value = response.data?.items || [];
    } else {
      message.error(response.message || '获取环境配置失败');
    }
  } catch (error) {
    console.error('获取环境配置失败:', error);
    message.error('获取环境配置失败');
  } finally {
    loading.environmentConfigs = false;
  }
};

// 初始化数据
onMounted(async () => {
  await fetchEnvironmentConfigs();
});

// 过滤后的环境列表
const filteredEnvironments = computed(() => {
  let result = environmentConfigs.value;
  
  // 关键词筛选
  if (filters.keyword) {
    const keyword = filters.keyword.toLowerCase();
    result = result.filter((item: EnvironmentConfig) => 
      item.name.toLowerCase().includes(keyword)
    );
  }
  
  // 类型筛选
  if (filters.type) {
    result = result.filter((item: EnvironmentConfig) => item.type === filters.type);
  }
  
  return result;
});

// 搜索
const handleSearch = async () => {
  await fetchEnvironmentConfigs();
};

// 重置筛选条件
const resetFilters = async () => {
  filters.keyword = '';
  filters.type = '';
  await fetchEnvironmentConfigs();
};

// 获取环境类型对应的文本
const getEnvironmentTypeText = (type: EnvironmentType) => {
  switch (type) {
    case EnvironmentType.NORMAL:
      return '普通实践';
    case EnvironmentType.JUPYTER:
      return 'Jupyter';
    case EnvironmentType.DESKTOP:
      return '云桌面';
    default:
      return '未知类型';
  }
};

// 获取环境类型对应的颜色
const getEnvironmentTypeColor = (type: EnvironmentType) => {
  switch (type) {
    case EnvironmentType.NORMAL:
      return 'blue';
    case EnvironmentType.JUPYTER:
      return 'green';
    case EnvironmentType.DESKTOP:
      return 'purple';
    default:
      return 'default';
  }
};

// 编辑环境配置
const editEnvironment = (record: EnvironmentConfig) => {
  editModal.record = record;
  editModal.form.storage = { ...record.storage };
  editModal.form.memory = { ...record.memory };
  editModal.form.cpu = { ...record.cpu };
  editModal.form.docker_image = record.docker_image || '';
  editModal.form.docker_port = record.docker_port || 8888;
  editModal.form.description = record.description || '';
  editModal.form.is_active = record.is_active !== false;
  editModal.visible = true;
};

// 取消编辑
const cancelEdit = () => {
  editModal.visible = false;
  // 重置表单
  setTimeout(() => {
    editModal.record = null;
  }, 300);
};

// 保存环境配置
const handleSave = async () => {
  if (!editModal.record) return;

  // 表单验证
  if (
    editModal.form.storage.min > editModal.form.storage.max ||
    editModal.form.storage.default < editModal.form.storage.min ||
    editModal.form.storage.default > editModal.form.storage.max ||
    editModal.form.memory.min > editModal.form.memory.max ||
    editModal.form.memory.default < editModal.form.memory.min ||
    editModal.form.memory.default > editModal.form.memory.max ||
    editModal.form.cpu.min > editModal.form.cpu.max ||
    editModal.form.cpu.default < editModal.form.cpu.min ||
    editModal.form.cpu.default > editModal.form.cpu.max
  ) {
    message.error('配置参数有误，请检查最小值、最大值和默认值的关系');
    return;
  }

  editModal.loading = true;

  try {
    // 更新环境配置（包含所有字段）
    const response = await updateEnvironmentConfig(
      editModal.record.id,
      {
        storage: editModal.form.storage,
        memory: editModal.form.memory,
        cpu: editModal.form.cpu,
        docker_image: editModal.form.docker_image || undefined,
        docker_port: editModal.form.docker_port || undefined,
        description: editModal.form.description || undefined,
        is_active: editModal.form.is_active
      }
    );

    if (response.code === "0000" || response.code === 200) {
      message.success('环境配置已更新');
      editModal.visible = false;
      // 刷新环境列表
      await fetchEnvironmentConfigs();
    } else {
      message.error(response.message || '更新环境配置失败');
    }
  } catch (error) {
    console.error('更新环境配置出错:', error);
    message.error('更新失败: ' + (error instanceof Error ? error.message : '未知错误'));
  } finally {
    editModal.loading = false;
  }
};
</script>

<style scoped>
.environment-management {
  padding-bottom: 24px;
}

.content-card {
  margin-top: 16px;
}

.filter-container {
  margin-bottom: 16px;
}

.edit-form {
  max-height: 600px;
  overflow-y: auto;
}

.config-row {
  margin-bottom: 20px;
}

h3 {
  margin: 16px 0;
  font-weight: 500;
  font-size: 16px;
}

.docker-image {
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  color: #1890ff;
}

.no-image {
  color: #999;
  font-style: italic;
}

.status-tip {
  margin-left: 12px;
  color: #999;
  font-size: 12px;
}
</style> 