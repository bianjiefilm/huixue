<template>
  <div v-if="showDebug" class="resource-debug-panel">
    <a-card title="资源调试面板" :bordered="false">
      <template #extra>
        <a-button @click="refreshDebugInfo" :loading="loading" type="primary" size="small">
          刷新
        </a-button>
      </template>

      <!-- 基本信息 -->
      <a-descriptions title="课程信息" :column="2" bordered size="small">
        <a-descriptions-item label="课程ID">{{ debugInfo.course_id }}</a-descriptions-item>
        <a-descriptions-item label="课程名称">{{ debugInfo.course_title }}</a-descriptions-item>
        <a-descriptions-item label="课程类型">{{ debugInfo.course_type }}</a-descriptions-item>
        <a-descriptions-item label="资源模块数">{{ debugInfo.total_modules }}</a-descriptions-item>
        <a-descriptions-item label="文件总数">{{ debugInfo.total_files }}</a-descriptions-item>
        <a-descriptions-item label="文件类型">
          <a-tag v-for="(count, type) in debugInfo.file_types" :key="type" color="blue">
            {{ type }}: {{ count }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>

      <!-- 路径分析 -->
      <a-divider />
      <a-descriptions title="路径匹配分析" :column="1" bordered size="small">
        <a-descriptions-item label="期望路径">
          {{ debugInfo.path_analysis?.expected_path }}
        </a-descriptions-item>
        <a-descriptions-item label="匹配状态">
          <a-badge 
            :status="debugInfo.path_analysis?.mismatched_files?.length > 0 ? 'error' : 'success'"
            :text="debugInfo.path_analysis?.mismatched_files?.length > 0 ? '存在不匹配' : '完全匹配'"
          />
        </a-descriptions-item>
      </a-descriptions>

      <!-- 不匹配文件列表 -->
      <div v-if="debugInfo.path_analysis?.mismatched_files?.length > 0" class="mismatch-section">
        <a-alert 
          message="发现路径不匹配的文件" 
          type="warning" 
          show-icon 
          style="margin: 16px 0"
        />
        <a-table 
          :dataSource="debugInfo.path_analysis.mismatched_files" 
          :columns="mismatchColumns"
          :pagination="false"
          size="small"
        />
        
        <!-- 修复按钮 -->
        <div style="margin-top: 16px; text-align: right;">
          <a-button @click="showFixModal = true" type="danger">
            修复路径不匹配
          </a-button>
        </div>
      </div>

      <!-- 模块详情 -->
      <a-divider />
      <a-collapse v-if="debugInfo.modules?.length > 0">
        <a-collapse-panel 
          v-for="module in debugInfo.modules" 
          :key="module.module_id"
          :header="`${module.module_name} (${module.file_count} 个文件)`"
        >
          <a-list
            :dataSource="module.files"
            size="small"
            :pagination="{ pageSize: 10 }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span>{{ item.name }}</span>
                    <a-tag color="green" style="margin-left: 8px">{{ item.type }}</a-tag>
                  </template>
                  <template #description>
                    <div>路径: {{ item.url }}</div>
                    <div>大小: {{ formatFileSize(item.size) }}</div>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-button 
                    size="small" 
                    @click="testFileAccess(item.url)"
                  >
                    测试访问
                  </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-collapse-panel>
      </a-collapse>
    </a-card>

    <!-- 修复路径模态框 -->
    <a-modal
      v-model:open="showFixModal"
      title="修复资源路径"
      @ok="fixResourcePaths"
      :confirmLoading="fixing"
    >
      <p>确定要修复所有不匹配的资源路径吗？</p>
      <p>这将更新 {{ debugInfo.path_analysis?.mismatched_files?.length }} 个文件的路径。</p>
      <a-checkbox v-model:checked="dryRun">试运行（不实际修改）</a-checkbox>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import axios from 'axios'

const props = defineProps({
  courseId: {
    type: Number,
    required: true
  }
})

// 是否显示调试面板（可以通过URL参数控制）
const showDebug = computed(() => {
  const urlParams = new URLSearchParams(window.location.search)
  return urlParams.get('debug') === 'true'
})

const loading = ref(false)
const debugInfo = ref({})
const showFixModal = ref(false)
const fixing = ref(false)
const dryRun = ref(true)

const mismatchColumns = [
  {
    title: '文件名',
    dataIndex: 'file',
    key: 'file',
  },
  {
    title: '当前路径',
    dataIndex: 'current_path',
    key: 'current_path',
  },
  {
    title: '期望课程',
    dataIndex: 'expected_course',
    key: 'expected_course',
  },
  {
    title: '实际课程',
    dataIndex: 'actual_course',
    key: 'actual_course',
  }
]

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

const fetchDebugInfo = async () => {
  loading.value = true
  try {
    const response = await axios.get(`/v1/debug/course-resources/${props.courseId}`)
    debugInfo.value = response.data
  } catch (error) {
    message.error('获取调试信息失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

const refreshDebugInfo = () => {
  fetchDebugInfo()
}

const testFileAccess = async (fileUrl) => {
  try {
    // 构建完整的文件访问URL，使用course-files端点
    const testUrl = `/v1/files/course-files/${encodeURIComponent(fileUrl)}?preview=true`
    
    // 使用HEAD请求测试文件是否可访问
    await axios.head(testUrl, {
      timeout: 5000
    })
    message.success('文件访问正常')
  } catch (error) {
    if (error.response?.status === 404) {
      message.error('文件不存在')
    } else if (error.response?.status === 405) {
      // Method Not Allowed - 尝试GET请求
      try {
        await axios.get(testUrl, {
          headers: {
            'Range': 'bytes=0-1023'
          },
          timeout: 5000
        })
        message.success('文件访问正常')
      } catch (getError) {
        message.error('文件访问失败: ' + getError.message)
      }
    } else {
      message.error('文件访问失败: ' + error.message)
    }
  }
}

const fixResourcePaths = async () => {
  fixing.value = true
  try {
    const response = await axios.post(
      `/v1/debug/fix-resource-paths/${props.courseId}?dry_run=${dryRun.value}`
    )
    
    if (dryRun.value) {
      message.info(`试运行完成，将修复 ${response.data.fixes_count} 个文件`)
    } else {
      message.success(`成功修复 ${response.data.fixes_count} 个文件路径`)
      // 刷新调试信息
      await fetchDebugInfo()
    }
    
    showFixModal.value = false
  } catch (error) {
    message.error('修复失败: ' + error.message)
  } finally {
    fixing.value = false
  }
}

onMounted(() => {
  if (showDebug.value) {
    fetchDebugInfo()
  }
})
</script>

<style scoped>
.resource-debug-panel {
  margin-top: 16px;
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
}

.mismatch-section {
  margin-top: 16px;
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
}

:deep(.ant-collapse-header) {
  font-weight: 500;
}
</style>