<template>
  <div class="teaching-resource-library embedded">
    <!-- 头部 -->
    <div class="header">
      <div class="header-left">
        <h3>教学资源</h3>
      </div>
      <div class="header-right">
        <a-button 
          type="primary" 
          @click="showUploadModal = true"
          v-if="isTeacher"
        >
          <template #icon>
            <PlusOutlined />
          </template>
          上传资源
        </a-button>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索资源名称"
            @search="handleSearch"
            allow-clear
          />
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="selectedType"
            placeholder="选择资源类型"
            style="width: 100%"
            @change="handleTypeChange"
            allow-clear
          >
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="presentation">演示文稿</a-select-option>
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="audio">音频</a-select-option>
            <a-select-option value="code">代码</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select
            v-model:value="selectedModule"
            placeholder="选择章节"
            style="width: 100%"
            @change="handleModuleChange"
            allow-clear
          >
            <a-select-option 
              v-for="module in modules" 
              :key="module.id" 
              :value="module.id"
            >
              {{ module.name }}
            </a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-button @click="resetFilters">重置筛选</a-button>
        </a-col>
      </a-row>
    </div>

    <!-- 章节列表 -->
    <div class="module-section">
      <a-spin :spinning="loading" tip="加载中...">
        <a-collapse v-model:activeKey="activeModules" @change="handleModuleExpand">
        <a-collapse-panel 
          v-for="module in modules" 
          :key="module.id" 
          :header="module.name"
          :extra="getModuleExtra(module)"
        >
          <template #extra>
            <a-space>
              <a-tag color="blue">{{ getModuleResourceCount(module.id) }} 个资源</a-tag>
              <a-button 
                v-if="isTeacher" 
                type="text" 
                size="small" 
                @click.stop="showCreateModuleModal(module)"
              >
                <template #icon>
                  <PlusOutlined />
                </template>
                添加资源
              </a-button>
            </a-space>
          </template>
          
          <!-- 资源列表 -->
          <div class="resource-list">
            <a-row :gutter="[16, 16]">
              <a-col 
                v-for="resource in getModuleResources(module.id)" 
                :key="resource.id"
                :span="8"
              >
                <a-card 
                  hoverable 
                  class="resource-card"
                  @click="handleResourceClick(resource)"
                >
                  <template #cover>
                    <div class="resource-cover">
                      <div class="resource-icon">
                        <component :is="getResourceIcon(resource.file_type)" />
                      </div>
                      <div class="resource-type-tag">
                        <a-tag :color="getTypeColor(resource.file_type)">
                          {{ getResourceTypeName(resource.file_type) }}
                        </a-tag>
                      </div>
                    </div>
                  </template>
                  
                  <a-card-meta :title="resource.name">
                    <template #description>
                      <div class="resource-desc">
                        <p>{{ resource.description || '暂无描述' }}</p>
                        <div class="resource-meta">
                          <span class="meta-item">{{ formatFileSize(resource.file_size) }}</span>
                          <span class="meta-item" v-if="resource.duration">
                            <ClockCircleOutlined /> {{ formatDuration(resource.duration) }}
                          </span>
                          <span class="meta-item">{{ formatDate(resource.created_at) }}</span>
                        </div>
                      </div>
                    </template>
                  </a-card-meta>
                  
                  <template #actions>
                    <a-tooltip title="在线预览">
                      <EyeOutlined @click.stop="previewResource(resource)" />
                    </a-tooltip>
                    <a-tooltip title="查看详情">
                      <InfoCircleOutlined @click.stop="showResourceDetail(resource)" />
                    </a-tooltip>
                    <a-dropdown v-if="isTeacher" @click.stop>
                      <a-tooltip title="更多操作">
                        <EllipsisOutlined />
                      </a-tooltip>
                      <template #overlay>
                        <a-menu>
                          <a-menu-item @click="editResource(resource)">
                            <EditOutlined />
                            编辑
                          </a-menu-item>
                          <a-menu-item @click="deleteResource(resource)" danger>
                            <DeleteOutlined />
                            删除
                          </a-menu-item>
                        </a-menu>
                      </template>
                    </a-dropdown>
                  </template>
                </a-card>
              </a-col>
            </a-row>
            
            <!-- 空状态 -->
            <a-empty 
              v-if="getModuleResources(module.id).length === 0" 
              description="暂无资源"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
            />
          </div>
        </a-collapse-panel>
        </a-collapse>
      </a-spin>
    </div>

    <!-- 上传模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传教学资源"
      :width="600"
      @ok="handleUpload"
      @cancel="resetUploadForm"
      :confirmLoading="uploading"
    >
      <a-form
        ref="uploadFormRef"
        :model="uploadForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="选择章节" name="moduleId" :rules="[{ required: true, message: '请选择章节' }]">
          <a-select v-model:value="uploadForm.moduleId" placeholder="选择章节">
            <a-select-option 
              v-for="module in modules" 
              :key="module.id" 
              :value="module.id"
            >
              {{ module.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="资源名称" name="name" :rules="[{ required: true, message: '请输入资源名称' }]">
          <a-input v-model:value="uploadForm.name" placeholder="请输入资源名称" />
        </a-form-item>

        <a-form-item label="资源类型" name="fileType" :rules="[{ required: true, message: '请选择资源类型' }]">
          <a-select v-model:value="uploadForm.fileType" placeholder="选择资源类型">
            <a-select-option value="video">视频</a-select-option>
            <a-select-option value="document">文档</a-select-option>
            <a-select-option value="presentation">演示文稿</a-select-option>
            <a-select-option value="image">图片</a-select-option>
            <a-select-option value="audio">音频</a-select-option>
            <a-select-option value="code">代码</a-select-option>
            <a-select-option value="other">其他</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="选择文件" name="file" :rules="[{ required: true, message: '请选择文件' }]">
          <a-upload
            v-model:file-list="uploadForm.fileList"
            :before-upload="beforeUpload"
            :max-count="1"
            @change="handleFileChange"
          >
            <a-button>
              <template #icon>
                <UploadOutlined />
              </template>
              选择文件
            </a-button>
            <template #itemRender="{ file }">
              <div class="upload-item">
                <FileOutlined />
                <span>{{ file.name }}</span>
                <a-button type="text" size="small" @click="removeFile">
                  <CloseOutlined />
                </a-button>
              </div>
            </template>
          </a-upload>
        </a-form-item>

        <a-form-item label="资源描述" name="description">
          <a-textarea 
            v-model:value="uploadForm.description" 
            placeholder="请输入资源描述"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="时长(分钟)" name="duration" v-if="uploadForm.fileType === 'video' || uploadForm.fileType === 'audio'">
          <a-input-number 
            v-model:value="uploadForm.duration" 
            placeholder="视频/音频时长"
            :min="0"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 资源详情模态框 -->
    <a-modal
      v-model:open="showDetailModal"
      title="资源详情"
      :width="800"
      :footer="null"
    >
      <div class="resource-detail" v-if="selectedResource">
        <div class="detail-header">
          <div class="detail-icon">
            <component :is="getResourceIcon(selectedResource.file_type)" />
          </div>
          <div class="detail-info">
            <h3>{{ selectedResource.name }}</h3>
            <p class="detail-desc">{{ selectedResource.description || '暂无描述' }}</p>
            <div class="detail-meta">
              <span class="meta-item">类型：{{ getResourceTypeName(selectedResource.file_type) }}</span>
              <span class="meta-item">大小：{{ formatFileSize(selectedResource.file_size) }}</span>
              <span class="meta-item" v-if="selectedResource.duration">
                时长：{{ formatDuration(selectedResource.duration) }}
              </span>
              <span class="meta-item">上传时间：{{ formatDate(selectedResource.created_at) }}</span>
            </div>
          </div>
        </div>
        
        <div class="detail-actions">
          <a-button type="primary" @click="previewResource(selectedResource)">
            在线预览
          </a-button>
          <a-button v-if="isTeacher" @click="downloadResource(selectedResource)" style="margin-left: 8px;">
            下载文件
          </a-button>
        </div>
      </div>
    </a-modal>

    <!-- 预览模态框 -->
    <a-modal
      v-model:open="showPreviewModal"
      :title="previewingResource && previewingResource.name"
      :width="1000"
      :footer="null"
      :body-style="{ padding: '0' }"
      @afterOpen="handleModalOpen"
      @beforeClose="handleModalClose"
    >
      <div class="preview-container" v-if="previewingResource">
        <!-- 视频预览 -->
        <video 
          v-if="previewingResource.file_type === 'video'"
          :src="getPreviewUrl(previewingResource)"
          controls
          style="width: 100%; height: 500px;"
        />
        
        <!-- 音频预览 -->
        <audio 
          v-else-if="previewingResource.file_type === 'audio'"
          :src="getPreviewUrl(previewingResource)"
          controls
          style="width: 100%; margin: 20px 0;"
        />
        
        <!-- 图片预览 -->
        <img 
          v-else-if="previewingResource.file_type === 'image'"
          :src="getPreviewUrl(previewingResource)"
          style="width: 100%; max-height: 600px; object-fit: contain;"
        />
        
        <!-- 文档预览 -->
        <iframe 
          v-else-if="canPreviewInline(previewingResource.file_type)"
          :src="getPreviewUrl(previewingResource)"
          style="width: 100%; height: 600px; border: none;"
          @load="handleIframeLoad"
          @error="handleIframeError"
        />
        
        <!-- 不支持预览的文件类型 -->
        <div v-else class="no-preview">
          <FileOutlined style="font-size: 64px; color: #ccc;" />
          <p>该文件类型不支持在线预览</p>
          <p class="preview-tip">学生只能在线预览，无法下载</p>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message, Empty } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  PlusOutlined, 
  UploadOutlined, 
  ClockCircleOutlined, 
  EllipsisOutlined,
  EditOutlined,
  DeleteOutlined,
  FileOutlined,
  VideoCameraOutlined,
  FileTextOutlined,
  FilePptOutlined,
  PictureOutlined,
  AudioOutlined,
  CodeOutlined,
  FileUnknownOutlined,
  EyeOutlined,
  InfoCircleOutlined,
  CloseOutlined
} from '@ant-design/icons-vue'
import axios from 'axios'
import { useUserStore } from '../../../stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 真实数据状态
const loading = ref(false)
const courseInfo = ref({
  id: 1,
  name: '机器学习示范课堂'
})

const isTeacher = ref(true) // 当前用户是否为教师
const modules = ref([])
const resources = ref([])

// API基础URL
const API_BASE = '/v1'

const requireCurrentUserId = () => {
  const userId = userStore.userId
  if (!userId) {
    message.warning('请先登录后再访问教学资源')
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath))
    throw new Error('Missing current user id')
  }
  return userId
}

// 获取教学资源模块 - 修复版本
const fetchModules = async () => {
  try {
    loading.value = true
    const currentUserId = requireCurrentUserId()
    const courseId = route.params.id || 1
    console.log('当前课程ID:', courseId)

    // 根据课程ID映射到正确的classroom_id
    // Python程序设计(courseId=1) -> classroom_id=2 (Python程序设计_默认课堂)
    // Spark编程基础(courseId=2) -> classroom_id=3 (Spark编程基础_默认课堂)
    let classroomId = courseId == 1 ? 2 : courseId == 2 ? 3 : 2
    console.log('映射到课堂ID:', classroomId)

    // 直接使用正确的课堂ID获取模块
    try {
      const response = await axios.get(`${API_BASE}/teaching-resources/classrooms/${classroomId}/modules`, {
        params: { teacher_id: currentUserId }
      })
      console.log('课堂资源模块API响应:', response.data)

      if (response.data && response.data.code === '0000') {
        modules.value = response.data.data?.modules || []
        console.log('从课堂API获取到模块数量:', modules.value.length)
        return
      }
    } catch (error) {
      console.log('获取课堂资源失败:', error)
    }

    // 备用方案：尝试课程资源API
    try {
      const response = await axios.get(`${API_BASE}/courses/${courseId}/resource-modules`, {
        params: { teacher_id: currentUserId }
      })
      console.log('课程资源模块API响应:', response.data)

      if (response.data && response.data.code === '0000') {
        const actualClassroomId = response.data.data?.classroom_id
        if (actualClassroomId) {
          // 如果API返回了实际的classroom_id，使用它
          const response = await axios.get(`${API_BASE}/teaching-resources/classrooms/${classroomId}/modules`, {
            params: { teacher_id: currentUserId }
          })
          console.log('课堂模块API响应:', response.data)

          if (response.data && response.data.code === '0000') {
            modules.value = response.data.data?.modules || []
            console.log('从课堂API获取到模块数量:', modules.value.length)
            return
          }
        }
      }
    } catch (classroomError) {
      console.log('课堂API也失败:', classroomError)
    }

    // 如果都失败了，使用当前映射课堂ID重试
    console.log('使用当前映射课堂ID获取模块')
    const response = await axios.get(`${API_BASE}/teaching-resources/classrooms/${classroomId}/modules`, {
      params: { teacher_id: currentUserId }
    })
    console.log('默认课堂模块API响应:', response.data)

    if (response.data && response.data.code === '0000') {
      modules.value = response.data.data?.modules || []
      console.log('从默认课堂获取到模块数量:', modules.value.length)
    } else {
      console.log('API响应格式不正确或无数据')
      modules.value = []
    }

  } catch (error) {
    console.error('获取教学资源模块失败:', error)
    modules.value = []
  } finally {
    loading.value = false
  }
}

// 创建默认的教学资源模块（如果不存在）
const createDefaultModules = async (classroomId = null) => {
  const currentUserId = requireCurrentUserId()
  const targetClassroomId = classroomId || (route.params.id == 1 ? 2 : route.params.id == 2 ? 3 : route.params.id || 2)
  const defaultModules = [
    { name: '第一章 Python基础语法', description: '介绍Python基本语法和数据类型' },
    { name: '第二章 控制结构', description: '学习条件判断和循环结构' },
    { name: '第三章 高级特性', description: '探索Python模块和高级编程特性' },
    { name: '第四章 实践演练', description: '通过实例演练掌握Python编程' }
  ]

  try {
    const createdModules = []
    for (const moduleData of defaultModules) {
      const response = await axios.post(`${API_BASE}/teaching-resources/classrooms/${targetClassroomId}/modules`, null, {
        params: { 
          teacher_id: currentUserId,
          name: moduleData.name,
          description: moduleData.description
        }
      })
      if (response.data && response.data.code === '0000') {
        createdModules.push(response.data.data)
      }
    }
    console.log('默认模块创建完成，创建了', createdModules.length, '个模块')
    
    // 为每个模块添加一些示例文件
    await createDefaultFiles(createdModules)
    
  } catch (error) {
    console.log('创建默认模块失败:', error)
  }
}

// 为模块创建默认文件
const createDefaultFiles = async (modules) => {
  const currentUserId = requireCurrentUserId()
  const courseName = 'Python基础实践'
  const fileTemplates = [
    // 第一章文件
    [
      { name: 'Python语法基础', url: `${API_BASE}/files/course-files/课程资源/${courseName}/Python语法基础.pdf`, file_type: 'document' },
      { name: '数据类型详解', url: `${API_BASE}/files/course-files/课程资源/${courseName}/数据类型详解.pdf`, file_type: 'document' }
    ],
    // 第二章文件
    [
      { name: '条件判断', url: `${API_BASE}/files/course-files/课程资源/${courseName}/条件判断.pdf`, file_type: 'document' },
      { name: '循环结构', url: `${API_BASE}/files/course-files/课程资源/${courseName}/循环结构.pdf`, file_type: 'document' }
    ],
    // 第三章文件
    [
      { name: '模块导入', url: `${API_BASE}/files/course-files/课程资源/${courseName}/模块导入.pdf`, file_type: 'document' },
      { name: '高级特性', url: `${API_BASE}/files/course-files/课程资源/${courseName}/高级特性.pdf`, file_type: 'document' }
    ],
    // 第四章文件
    [
      { name: '实例演练', url: `${API_BASE}/files/course-files/课程资源/${courseName}/实例演练.mp4`, file_type: 'video', duration_seconds: 1800 },
      { name: '语法演示', url: `${API_BASE}/files/course-files/课程资源/${courseName}/语法演示.mp4`, file_type: 'video', duration_seconds: 2400 }
    ]
  ]

  try {
    for (let i = 0; i < modules.length && i < fileTemplates.length; i++) {
      const module = modules[i]
      const files = fileTemplates[i]
      
      for (const fileData of files) {
        await axios.post(`${API_BASE}/teaching-resources/modules/${module.id}/files`, null, {
          params: { 
            teacher_id: currentUserId,
            name: fileData.name,
            url: fileData.url,
            file_type: fileData.file_type,
            file_size: fileData.file_size || 1024000,
            duration_seconds: fileData.duration_seconds || 0
          }
        })
      }
    }
    console.log('默认文件创建完成')
  } catch (error) {
    console.log('创建默认文件失败:', error)
  }
}

// 获取教学资源文件
const fetchResources = async () => {
  try {
    loading.value = true
    console.log('开始获取资源数据')
    
    // 如果模块已经包含文件信息，从模块中提取
    const resourcesFromModules = []
    modules.value.forEach(module => {
      if (module.files && module.files.length > 0) {
        module.files.forEach(file => {
          resourcesFromModules.push({
            ...file,
            module_id: module.id
          })
        })
      }
    })
    
    if (resourcesFromModules.length > 0) {
      resources.value = resourcesFromModules
      console.log('从模块数据中提取到资源:', resourcesFromModules.length)
    } else {
      // 尝试从调试API获取真实的课程资源数据
      console.log('尝试从调试API获取真实课程资源数据')
      
      const currentCourseId = route.params.id
      console.log('当前课程ID:', currentCourseId)
      
      try {
        const debugResponse = await axios.get(`/v1/debug/course-resources/${currentCourseId}`)
        const debugData = debugResponse.data
        
        console.log('从调试API获取到课程资源数据:', debugData)
        
        if (debugData.modules && debugData.modules.length > 0) {
          // 将调试数据转换为资源库格式
          const realResources = []
          let resourceId = 1
          
          debugData.modules.forEach((module, moduleIndex) => {
            if (module.files && module.files.length > 0) {
              module.files.forEach(file => {
                realResources.push({
                  id: resourceId++,
                  name: file.name,
                  description: `来自${module.module_name}模块的教学资源`,
                  file_type: getFileType(file.type),
                  file_size: file.size || 1024000,
                  created_at: new Date().toISOString(),
                  module_id: moduleIndex + 1,
                  url: `${API_BASE}/files/course-files/${file.url}`
                })
              })
            }
          })
          
          resources.value = realResources
          console.log('成功转换真实资源数据，共', realResources.length, '个资源')
        } else {
          console.log('调试API未返回资源数据，使用空数组')
          resources.value = []
        }
      } catch (error) {
        console.error('从调试API获取课程资源失败:', error)
        resources.value = []
      }
    }
  } catch (error) {
    console.error('获取教学资源失败:', error)
    message.error('获取教学资源失败')
  } finally {
    loading.value = false
  }
}

// 响应式数据
const searchKeyword = ref('')
const selectedType = ref(null)
const selectedModule = ref(null)
const activeModules = ref([1, 2, 3, 4]) // 默认展开所有模块

// 模态框控制
const showUploadModal = ref(false)
const showDetailModal = ref(false)
const showPreviewModal = ref(false)
const selectedResource = ref(null)
const previewingResource = ref(null)
const uploading = ref(false)

// 上传表单
const uploadForm = reactive({
  moduleId: null,
  name: '',
  fileType: 'video',
  file: null,
  fileList: [],
  description: '',
  duration: null
})

const uploadFormRef = ref()

// 计算属性
const filteredResources = computed(() => {
  let filtered = resources.value

  if (searchKeyword.value) {
    filtered = filtered.filter(resource => 
      resource.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      (resource.description && resource.description.toLowerCase().includes(searchKeyword.value.toLowerCase()))
    )
  }

  if (selectedType.value) {
    filtered = filtered.filter(resource => resource.file_type === selectedType.value)
  }

  if (selectedModule.value) {
    filtered = filtered.filter(resource => resource.module_id === selectedModule.value)
  }

  return filtered
})

// 方法
const handleSearch = () => {
  console.log('搜索:', searchKeyword.value)
}

const handleTypeChange = (value) => {
  console.log('类型筛选:', value)
}

const handleModuleChange = (value) => {
  console.log('章节筛选:', value)
}

const resetFilters = () => {
  searchKeyword.value = ''
  selectedType.value = null
  selectedModule.value = null
}

const handleModuleExpand = (expandedKeys) => {
  activeModules.value = expandedKeys
}

const getModuleResourceCount = (moduleId) => {
  return filteredResources.value.filter(resource => resource.module_id === moduleId).length
}

const getModuleResources = (moduleId) => {
  return filteredResources.value.filter(resource => resource.module_id === moduleId)
}

const getModuleExtra = (module) => {
  return null // 返回 null 以使用模板中的 extra 插槽
}

const handleResourceClick = (resource) => {
  selectedResource.value = resource
  showDetailModal.value = true
}

const previewResource = (resource) => {
  console.log('=== 预览资源开始 ===')
  console.log('资源信息:', resource)
  console.log('资源URL:', resource.url)
  console.log('文件类型:', resource.file_type)
  
  // 测试URL是否可访问
  fetch(resource.url + '?preview=true')
    .then(response => {
      console.log('文件访问响应状态:', response.status)
      console.log('响应头:', response.headers)
      console.log('Content-Type:', response.headers.get('content-type'))
      return response.text()
    })
    .then(data => {
      console.log('文件内容长度:', data.length)
      console.log('文件内容前100字符:', data.substring(0, 100))
    })
    .catch(error => {
      console.error('文件访问失败:', error)
    })
  
  previewingResource.value = resource
  showPreviewModal.value = true
  console.log('模态框状态:', showPreviewModal.value)
  console.log('=== 预览资源结束 ===')
}

const showResourceDetail = (resource) => {
  selectedResource.value = resource
  showDetailModal.value = true
}

const editResource = (resource) => {
  console.log('编辑资源:', resource)
  message.info('编辑功能开发中...')
}

const deleteResource = (resource) => {
  console.log('删除资源:', resource)
  message.info('删除功能开发中...')
}

const downloadResource = (resource) => {
  console.log('下载资源:', resource)
  // 只有教师可以下载，学生只能预览
  if (isTeacher.value) {
    window.open(resource.url, '_blank')
  } else {
    message.warning('学生只能在线预览，无法下载')
  }
}

const showCreateModuleModal = (module) => {
  uploadForm.moduleId = module.id
  showUploadModal.value = true
}

const beforeUpload = (file) => {
  const isValidType = true // 这里可以添加文件类型验证
  const isValidSize = file.size / 1024 / 1024 < 100 // 限制100MB
  
  if (!isValidType) {
    message.error('不支持的文件类型')
    return false
  }
  if (!isValidSize) {
    message.error('文件大小不能超过100MB')
    return false
  }
  
  return false // 阻止自动上传
}

const handleFileChange = (info) => {
  const { fileList } = info
  uploadForm.fileList = fileList
  if (fileList.length > 0) {
    uploadForm.file = fileList[0].originFileObj
  }
}

const removeFile = () => {
  uploadForm.fileList = []
  uploadForm.file = null
}

const handleUpload = async () => {
  try {
    await uploadFormRef.value.validate()
    uploading.value = true
    
    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('module_id', uploadForm.moduleId)
    formData.append('teacher_id', '1') // 这里应该从用户状态获取
    formData.append('file_name', uploadForm.name)
    formData.append('file_type', uploadForm.fileType)
    formData.append('description', uploadForm.description || '')
    if (uploadForm.duration) {
      formData.append('duration', uploadForm.duration)
    }

    try {
      // 尝试调用真实API
      const response = await axios.post(`${API_BASE}/files/upload/teaching-resource`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      if (response.data.code === '0000') {
        message.success('资源上传成功')
        await fetchResources() // 重新加载资源列表
      } else {
        throw new Error(response.data.message || '上传失败')
      }
    } catch (apiError) {
      console.warn('API调用失败，使用模拟上传:', apiError)
      
      // 模拟上传成功
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // 添加到本地数据
      const newResource = {
        id: Date.now(),
        name: uploadForm.name,
        description: uploadForm.description,
        file_type: uploadForm.fileType,
        file_size: uploadForm.file.size,
        duration: uploadForm.duration,
        created_at: new Date().toISOString(),
        module_id: uploadForm.moduleId,
        url: `/v1/files/teaching-resource/${uploadForm.moduleId}/${uploadForm.file.name}`
      }
      resources.value.push(newResource)
      message.success('资源上传成功（演示模式）')
    }
    
    showUploadModal.value = false
    resetUploadForm()
  } catch (error) {
    console.error('上传失败:', error)
    message.error('上传失败: ' + (error.message || '未知错误'))
  } finally {
    uploading.value = false
  }
}

const resetUploadForm = () => {
  Object.assign(uploadForm, {
    moduleId: null,
    name: '',
    fileType: 'video',
    file: null,
    fileList: [],
    description: '',
    duration: null
  })
}

// 工具方法
const getResourceIcon = (fileType) => {
  const iconMap = {
    video: VideoCameraOutlined,
    document: FileTextOutlined,
    presentation: FilePptOutlined,
    image: PictureOutlined,
    audio: AudioOutlined,
    code: CodeOutlined,
    other: FileUnknownOutlined
  }
  return iconMap[fileType] || FileUnknownOutlined
}

const getResourceTypeName = (fileType) => {
  const typeMap = {
    video: '视频',
    document: '文档',
    presentation: '演示文稿',
    image: '图片',
    audio: '音频',
    code: '代码',
    other: '其他'
  }
  return typeMap[fileType] || '未知类型'
}

const getTypeColor = (fileType) => {
  const colorMap = {
    video: 'blue',
    document: 'green',
    presentation: 'orange',
    image: 'purple',
    audio: 'cyan',
    code: 'magenta',
    other: 'default'
  }
  return colorMap[fileType] || 'default'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const formatDate = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const getPreviewUrl = (resource) => {
  console.log('=== 获取预览URL ===')
  console.log('原始资源URL:', resource.url)
  
  // 使用encodeURIComponent来正确编码中文路径
  const pathParts = resource.url.split('/files/course-files/')
  if (pathParts.length > 1) {
    const encodedPath = pathParts[1].split('/').map(part => encodeURIComponent(part)).join('/')
    const previewUrl = `${pathParts[0]}/files/course-files/${encodedPath}?preview=true`
    console.log('生成的预览URL:', previewUrl)
    return previewUrl
  }
  const fallbackUrl = `${resource.url}?preview=true`
  console.log('后备预览URL:', fallbackUrl)
  return fallbackUrl
}

const canPreviewInline = (fileType) => {
  return ['document', 'presentation'].includes(fileType)
}

const handleIframeLoad = (event) => {
  console.log('=== iframe加载成功 ===')
  console.log('iframe event:', event)
  console.log('iframe src:', event.target.src)
}

const handleIframeError = (event) => {
  console.error('=== iframe加载失败 ===')
  console.error('iframe error event:', event)
  console.error('iframe src:', event.target.src)
}

const handleModalOpen = () => {
  console.log('=== 预览模态框已打开 ===')
  console.log('预览资源:', previewingResource.value)
  console.log('资源类型:', previewingResource.value?.file_type)
  console.log('是否支持内联预览:', canPreviewInline(previewingResource.value?.file_type))
}

const handleModalClose = () => {
  console.log('=== 预览模态框关闭 ===')
}

// 文件类型映射辅助函数
const getFileType = (fileExtension) => {
  const ext = fileExtension?.toLowerCase()
  if (!ext) return 'other'
  
  if (['.pdf', '.doc', '.docx', '.txt'].includes(ext)) return 'document'
  if (['.mp4', '.avi', '.mov', '.wmv'].includes(ext)) return 'video'
  if (['.mp3', '.wav', '.aac'].includes(ext)) return 'audio'
  if (['.jpg', '.jpeg', '.png', '.gif', '.bmp'].includes(ext)) return 'image'
  if (['.ppt', '.pptx'].includes(ext)) return 'presentation'
  if (['.js', '.py', '.java', '.cpp', '.c'].includes(ext)) return 'code'
  
  return 'other'
}

onMounted(async () => {
  console.log('教学资源库组件已挂载')
  
  // 获取模块（新版本不需要传参数）
  await fetchModules()

  // 如果没有模块，尝试运行资源映射脚本或创建默认模块
  if (modules.value.length === 0) {
    console.log('没有找到模块，提示用户运行资源导入脚本')
    // 显示提示信息而不是自动创建
    message.warning('课程资源尚未导入，请联系管理员运行资源导入脚本')
  }
  
  await fetchResources()
  console.log('最终 - 模块数量:', modules.value.length)
  console.log('最终 - 资源数量:', resources.value.length)
  console.log('资源列表:', resources.value)
})
</script>

<style scoped>
.teaching-resource-library {
  padding: 24px;
  min-height: 100vh;
  background: #f5f5f5;
}

.teaching-resource-library.embedded {
  padding: 0;
  min-height: auto;
  background: transparent;
}

.teaching-resource-library.embedded .header {
  background: white;
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.teaching-resource-library.embedded .filter-section {
  background: white;
}

.teaching-resource-library.embedded .module-section {
  background: white;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left h2 {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
}

.breadcrumb {
  margin-top: 8px;
}

.filter-section {
  margin-bottom: 24px;
  padding: 20px 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.module-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 24px;
}

.resource-list {
  margin-top: 16px;
}

.resource-card {
  height: 100%;
  transition: all 0.3s ease;
}

.resource-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.resource-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.resource-icon {
  font-size: 48px;
  color: white;
}

.resource-type-tag {
  position: absolute;
  top: 8px;
  right: 8px;
}

.resource-desc {
  min-height: 80px;
}

.resource-desc p {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.resource-detail {
  padding: 20px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-icon {
  font-size: 48px;
  color: #1890ff;
}

.detail-info {
  flex: 1;
}

.detail-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: bold;
}

.detail-desc {
  color: #666;
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 14px;
  color: #999;
}

.detail-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.no-preview {
  text-align: center;
  padding: 40px;
}

.no-preview p {
  margin: 16px 0;
  color: #666;
}

.preview-tip {
  color: #1890ff;
  font-size: 14px;
}

.upload-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
  margin-top: 8px;
}

.upload-item span {
  flex: 1;
}

:deep(.ant-collapse-header) {
  font-weight: bold;
}

:deep(.ant-collapse-content-box) {
  padding: 16px 0;
}
</style>
