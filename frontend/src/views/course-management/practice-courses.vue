<template>
  <div class="practice-courses-page">
    <a-layout class="full-height">
      <!-- 左侧分类树 -->
      <a-layout-sider 
        width="280" 
        theme="light" 
        class="category-sider"
        :style="{ borderRight: '1px solid #e8e8e8' }"
      >
        <div class="category-header">
          <h3>实践课程分类</h3>
        </div>
        <div class="category-tree">
          <a-tree
            v-model:selectedKeys="selectedKeys"
            v-model:expandedKeys="expandedKeys"
            :tree-data="categoryTree"
            :show-line="true"
            :default-expand-all="true"
            @select="onCategorySelect"
          />
        </div>
      </a-layout-sider>

      <!-- 右侧课程列表 -->
      <a-layout-content class="course-content">
        <div class="content-header">
          <div class="title-section">
            <h2>{{ currentCategoryTitle }}</h2>
            <span class="course-count">共 {{ courseList.total }} 门课程</span>
          </div>
          
          <div class="action-section">
            <a-space>
              <a-button type="primary" @click="showImportModal">
                <template #icon><ImportOutlined /></template>
                导入课程
              </a-button>
              <a-button @click="refreshList" :loading="loading">
                <template #icon><ReloadOutlined /></template>
                刷新
              </a-button>
            </a-space>
          </div>
        </div>

        <!-- 排序和筛选 -->
        <div class="filter-section">
          <a-space>
            <span>排序：</span>
            <a-select
              v-model:value="queryParams.sort_field"
              style="width: 120px"
              @change="loadCourseList"
            >
              <a-select-option value="updated_at">更新时间</a-select-option>
              <a-select-option value="created_at">创建时间</a-select-option>
              <a-select-option value="title">课程名称</a-select-option>
            </a-select>
            
            <a-select
              v-model:value="queryParams.sort_order"
              style="width: 80px"
              @change="loadCourseList"
            >
              <a-select-option value="desc">降序</a-select-option>
              <a-select-option value="asc">升序</a-select-option>
            </a-select>
          </a-space>
        </div>

        <!-- 课程列表 -->
        <div class="course-list" v-if="!loading">
          <a-row :gutter="[16, 16]">
            <a-col 
              v-for="course in courseList.items" 
              :key="course.id" 
              :xs="24" 
              :sm="12" 
              :md="8" 
              :lg="6"
            >
              <a-card 
                hoverable 
                class="course-card"
                :body-style="{ padding: '16px' }"
              >
                <template #cover>
                  <div class="course-cover">
                    <img 
                      v-if="course.cover_url" 
                      :src="course.cover_url" 
                      :alt="course.title"
                      @error="onImageError"
                    />
                    <div v-else class="default-cover">
                      <BookOutlined />
                    </div>
                  </div>
                </template>

                <template #actions>
                  <EyeOutlined key="view" @click="viewCourseDetail(course)" />
                  <CloudDownloadOutlined 
                    v-if="course.can_unpublish" 
                    key="unpublish" 
                    @click="showUnpublishModal(course)" 
                  />
                  <CloudUploadOutlined 
                    v-if="course.can_publish" 
                    key="publish" 
                    @click="showPublishModal(course)" 
                  />
                </template>

                <a-card-meta>
                  <template #title>
                    <a-tooltip :title="course.title">
                      <span class="course-title" @click="viewCourseDetail(course)">
                        {{ course.title }}
                      </span>
                    </a-tooltip>
                  </template>
                  
                  <template #description>
                    <div class="course-info">
                      <div class="info-row">
                        <a-tag color="blue">{{ getDifficultyText(course.difficulty) }}</a-tag>
                        <span class="task-count">{{ course.task_count }} 个任务</span>
                      </div>
                      
                      <div class="info-row">
                        <span class="creator">
                          <UserOutlined />
                          {{ course.creator?.full_name || course.creator?.username || '系统导入' }}
                        </span>
                      </div>
                      
                      <div class="info-row">
                        <span class="update-time">
                          更新：{{ formatDate(course.updated_at) }}
                        </span>
                      </div>
                      
                      <div class="info-row">
                        <a-tag 
                          :color="getStatusColor(course.publish_status, course.visibility)"
                          class="status-tag"
                        >
                          {{ getStatusText(course.publish_status, course.visibility) }}
                        </a-tag>
                      </div>
                    </div>
                  </template>
                </a-card-meta>
              </a-card>
            </a-col>
          </a-row>

          <!-- 空状态 -->
          <a-empty v-if="courseList.items.length === 0" description="暂无课程数据" />
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
        </div>

        <!-- 分页 -->
        <div class="pagination-container" v-if="courseList.total > 0">
          <a-pagination
            v-model:current="queryParams.page"
            v-model:page-size="queryParams.page_size"
            :total="courseList.total"
            :show-size-changer="true"
            :show-quick-jumper="true"
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="loadCourseList"
            @show-size-change="loadCourseList"
          />
        </div>
      </a-layout-content>
    </a-layout>

    <!-- 课程详情抽屉 -->
    <a-drawer
      v-model:open="detailDrawerVisible"
      title="课程详情"
      width="600"
      :body-style="{ padding: '24px' }"
    >
      <course-detail-panel
        v-if="selectedCourse"
        :course="selectedCourse"
        course-type="practice"
        @action="onCourseAction"
      />
    </a-drawer>

    <!-- 下架确认模态框 -->
    <a-modal
      v-model:open="unpublishModalVisible"
      title="确认下架课程"
      @ok="confirmUnpublish"
      @cancel="unpublishModalVisible = false"
    >
      <p>确定要下架课程 <strong>{{ actionCourse?.title }}</strong> 吗？</p>
      <p class="text-warning">
        <ExclamationCircleOutlined />
        下架后，课程将不再对学生可见。
        {{ actionCourse?.creator ? '教师创建的课程将转为个人发布状态。' : '管理员导入的课程可重新发布。' }}
      </p>
      
      <a-form-item label="下架原因（可选）">
        <a-textarea
          v-model:value="actionReason"
          placeholder="请输入下架原因..."
          :rows="3"
          :max-length="200"
          show-count
        />
      </a-form-item>
    </a-modal>

    <!-- 发布确认模态框 -->
    <a-modal
      v-model:open="publishModalVisible"
      title="确认发布课程"
      @ok="confirmPublish"
      @cancel="publishModalVisible = false"
    >
      <p>确定要发布课程 <strong>{{ actionCourse?.title }}</strong> 吗？</p>
      <p class="text-info">
        <InfoCircleOutlined />
        发布后，课程将对所有学生可见。
      </p>
      
      <a-form-item label="发布说明（可选）">
        <a-textarea
          v-model:value="actionReason"
          placeholder="请输入发布说明..."
          :rows="3"
          :max-length="200"
          show-count
        />
      </a-form-item>
    </a-modal>

    <!-- 课程导入模态框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入课程资源"
      width="800px"
      :footer="null"
      @cancel="importModalVisible = false"
    >
      <a-spin :spinning="scanning">
        <div class="import-modal-content">
          <!-- 扫描按钮 -->
          <div class="scan-section">
            <a-button type="primary" @click="scanResources" :loading="scanning">
              <template #icon><ScanOutlined /></template>
              扫描可导入资源
            </a-button>
            <span class="scan-tip">点击扫描服务器上的课程资源目录</span>
          </div>

          <!-- 扫描结果 -->
          <div v-if="scanResult" class="scan-result">
            <a-divider>发现 {{ scanResult.courses.length }} 个课程资源</a-divider>

            <a-empty v-if="scanResult.courses.length === 0" description="未发现可导入的课程资源" />

            <a-table
              v-else
              :dataSource="scanResult.courses"
              :columns="importColumns"
              :row-selection="{ selectedRowKeys: selectedCourses, onChange: onSelectChange }"
              :pagination="{ pageSize: 10 }"
              row-key="path"
              size="small"
            >
              <template #bodyCell="{ column, record }">
                <template v-if="column.key === 'title'">
                  <div class="course-title-cell">
                    <BookOutlined class="course-icon" />
                    <span>{{ record.title }}</span>
                  </div>
                </template>
                <template v-if="column.key === 'difficulty'">
                  <a-tag :color="getDifficultyColor(record.difficulty)">
                    {{ getDifficultyText(record.difficulty) }}
                  </a-tag>
                </template>
                <template v-if="column.key === 'action'">
                  <a-button
                    size="small"
                    type="link"
                    @click="importSingleCourse(record)"
                    :loading="importingPath === record.path"
                  >
                    导入
                  </a-button>
                </template>
              </template>
            </a-table>

            <!-- 批量导入 -->
            <div class="batch-import-section" v-if="selectedCourses.length > 0">
              <a-space>
                <span>已选择 {{ selectedCourses.length }} 个课程</span>
                <a-checkbox v-model:checked="forceUpdate">强制更新已存在的课程</a-checkbox>
                <a-button type="primary" @click="batchImportCourses" :loading="batchImporting">
                  批量导入
                </a-button>
              </a-space>
            </div>
          </div>
        </div>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  BookOutlined,
  EyeOutlined,
  CloudDownloadOutlined,
  CloudUploadOutlined,
  UserOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  ImportOutlined,
  ScanOutlined
} from '@ant-design/icons-vue'
import {
  CourseManagementAPI,
  type CategoryNode,
  type PracticeCourseItem,
  type PracticeCourseDetail,
  type PracticeCourseQuery,
  type CourseActionRequest,
  SortOrderEnum
} from '@/api/course-management'
import {
  scanResources as scanResourcesAPI,
  importCourse as importCourseAPI,
  batchImportCourses as batchImportCoursesAPI,
  type ScanResult,
  type ScannedCourse
} from '@/api/course-import'
import CourseDetailPanel from './components/CourseDetailPanel.vue'

// 响应式数据
const loading = ref(false)
const selectedKeys = ref<string[]>(['root'])
const expandedKeys = ref<string[]>(['root'])
const categoryTree = ref<any[]>([])
const courseList = reactive({
  items: [] as PracticeCourseItem[],
  total: 0,
  page: 1,
  page_size: 20,
  total_pages: 0
})

const queryParams = reactive<PracticeCourseQuery>({
  category: undefined,
  page: 1,
  page_size: 20,
  sort_field: 'updated_at',
  sort_order: SortOrderEnum.DESC
})

// 详情抽屉
const detailDrawerVisible = ref(false)
const selectedCourse = ref<PracticeCourseDetail | null>(null)

// 操作模态框
const unpublishModalVisible = ref(false)
const publishModalVisible = ref(false)
const actionCourse = ref<PracticeCourseItem | null>(null)
const actionReason = ref('')

// 导入模态框
const importModalVisible = ref(false)
const scanning = ref(false)
const scanResult = ref<ScanResult | null>(null)
const selectedCourses = ref<string[]>([])
const forceUpdate = ref(false)
const importingPath = ref<string | null>(null)
const batchImporting = ref(false)

// 导入表格列配置
const importColumns = [
  { title: '课程名称', dataIndex: 'title', key: 'title' },
  { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 100 },
  { title: '分类', dataIndex: 'category', key: 'category', width: 120 },
  { title: '操作', key: 'action', width: 80 }
]

// 计算属性
const currentCategoryTitle = computed(() => {
  if (!selectedKeys.value.length) return '全部实践课程'
  
  const selectedKey = selectedKeys.value[0]
  if (selectedKey === 'root') return '全部实践课程'
  
  // 递归查找分类标题
  const findCategoryTitle = (nodes: any[], key: string): string => {
    for (const node of nodes) {
      if (node.key === key) return node.title
      if (node.children) {
        const found = findCategoryTitle(node.children, key)
        if (found) return found
      }
    }
    return ''
  }
  
  return findCategoryTitle(categoryTree.value, selectedKey) || '未知分类'
})

// 生命周期
onMounted(() => {
  loadCategoryTree()
  loadCourseList()
})

// 方法
const loadCategoryTree = async () => {
  try {
    const response = await CourseManagementAPI.getPracticeCourseCategories()
    categoryTree.value = [
      {
        key: 'root',
        title: '全部实践课程',
        children: response.categories
      }
    ]
    expandedKeys.value = ['root']
  } catch (error) {
    console.error('加载分类树失败:', error)
    message.error('加载分类树失败')
  }
}

const loadCourseList = async () => {
  loading.value = true
  try {
    const response = await CourseManagementAPI.getPracticeCourses(queryParams)
    Object.assign(courseList, response)
  } catch (error) {
    console.error('加载课程列表失败:', error)
    message.error('加载课程列表失败')
  } finally {
    loading.value = false
  }
}

const onCategorySelect = (selectedKeys: string[]) => {
  if (selectedKeys.length === 0) return
  
  const selectedKey = selectedKeys[0]
  queryParams.category = selectedKey === 'root' ? undefined : selectedKey
  queryParams.page = 1
  loadCourseList()
}

const refreshList = () => {
  loadCourseList()
}

const viewCourseDetail = async (course: PracticeCourseItem) => {
  try {
    const detail = await CourseManagementAPI.getPracticeCourseDetail(course.id)
    selectedCourse.value = detail
    detailDrawerVisible.value = true
  } catch (error) {
    console.error('加载课程详情失败:', error)
    message.error('加载课程详情失败')
  }
}

const showUnpublishModal = (course: PracticeCourseItem) => {
  actionCourse.value = course
  actionReason.value = ''
  unpublishModalVisible.value = true
}

const showPublishModal = (course: PracticeCourseItem) => {
  actionCourse.value = course
  actionReason.value = ''
  publishModalVisible.value = true
}

const confirmUnpublish = async () => {
  if (!actionCourse.value) return
  
  try {
    const request: CourseActionRequest = {
      course_id: actionCourse.value.id,
      action: 'unpublish',
      reason: actionReason.value || undefined
    }
    
    const response = await CourseManagementAPI.practiceCourseAction(request)
    
    if (response.success) {
      message.success(response.message)
      unpublishModalVisible.value = false
      loadCourseList()
    } else {
      message.error(response.message)
    }
  } catch (error) {
    console.error('下架课程失败:', error)
    message.error('下架课程失败')
  }
}

const confirmPublish = async () => {
  if (!actionCourse.value) return
  
  try {
    const request: CourseActionRequest = {
      course_id: actionCourse.value.id,
      action: 'publish',
      reason: actionReason.value || undefined
    }
    
    const response = await CourseManagementAPI.practiceCourseAction(request)
    
    if (response.success) {
      message.success(response.message)
      publishModalVisible.value = false
      loadCourseList()
    } else {
      message.error(response.message)
    }
  } catch (error) {
    console.error('发布课程失败:', error)
    message.error('发布课程失败')
  }
}

const onCourseAction = (action: string, course: any) => {
  if (action === 'unpublish') {
    showUnpublishModal(course)
  } else if (action === 'publish') {
    showPublishModal(course)
  }
  detailDrawerVisible.value = false
}

const onImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  img.style.display = 'none'
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const getDifficultyText = (difficulty?: string) => {
  return CourseManagementAPI.getDifficultyText(difficulty)
}

const getStatusText = (publishStatus: string, visibility: string) => {
  if (visibility === 'PUBLIC' && publishStatus === 'PUBLISHED') {
    return '已发布'
  } else if (visibility === 'PRIVATE') {
    return '个人发布'
  } else if (publishStatus === 'EDITING') {
    return '未发布'
  }
  return '未知状态'
}

const getStatusColor = (publishStatus: string, visibility: string) => {
  if (visibility === 'PUBLIC' && publishStatus === 'PUBLISHED') {
    return 'green'
  } else if (visibility === 'PRIVATE') {
    return 'orange'
  } else if (publishStatus === 'EDITING') {
    return 'gray'
  }
  return 'default'
}

// ========== 课程导入相关方法 ==========

const showImportModal = () => {
  importModalVisible.value = true
  scanResult.value = null
  selectedCourses.value = []
  forceUpdate.value = false
}

const scanResources = async () => {
  scanning.value = true
  try {
    const response = await scanResourcesAPI()
    if (response.code === '0000') {
      scanResult.value = response.data.resources
      message.success(`扫描完成，发现 ${response.data.courses} 个课程资源`)
    } else {
      message.error(response.msg || '扫描失败')
    }
  } catch (error) {
    console.error('扫描资源失败:', error)
    message.error('扫描资源失败')
  } finally {
    scanning.value = false
  }
}

const onSelectChange = (keys: string[]) => {
  selectedCourses.value = keys
}

const importSingleCourse = async (course: ScannedCourse) => {
  importingPath.value = course.path
  try {
    const result = await importCourseAPI({
      resource_path: course.path,
      force_update: forceUpdate.value
    })
    if (result.code === '0000') {
      message.success(`课程 "${course.title}" 导入成功`)
      loadCourseList() // 刷新课程列表
    } else if (result.code === '1001') {
      message.warning(result.msg)
    } else {
      message.error(result.msg || '导入失败')
    }
  } catch (error) {
    console.error('导入课程失败:', error)
    message.error('导入课程失败')
  } finally {
    importingPath.value = null
  }
}

const batchImportCourses = async () => {
  if (selectedCourses.value.length === 0) {
    message.warning('请选择要导入的课程')
    return
  }

  batchImporting.value = true
  try {
    const result = await batchImportCoursesAPI({
      resource_paths: selectedCourses.value,
      force_update: forceUpdate.value
    })

    if (result.success > 0) {
      message.success(`成功导入 ${result.success} 个课程`)
    }
    if (result.failed > 0) {
      message.warning(`${result.failed} 个课程导入失败`)
    }

    selectedCourses.value = []
    loadCourseList() // 刷新课程列表
  } catch (error) {
    console.error('批量导入失败:', error)
    message.error('批量导入失败')
  } finally {
    batchImporting.value = false
  }
}

const getDifficultyColor = (difficulty?: string) => {
  const colorMap: Record<string, string> = {
    'beginner': 'green',
    'intermediate': 'blue',
    'advanced': 'orange',
    'expert': 'red'
  }
  return colorMap[difficulty || 'beginner'] || 'default'
}
</script>

<style scoped>
.practice-courses-page {
  height: 100vh;
  background: #f5f5f5;
}

.full-height {
  height: 100%;
}

.category-sider {
  background: white;
  overflow-y: auto;
}

.category-header {
  padding: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.category-header h3 {
  margin: 0;
  color: #333;
}

.category-tree {
  padding: 16px;
}

.course-content {
  padding: 24px;
  overflow-y: auto;
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-section h2 {
  margin: 0;
  color: #333;
}

.course-count {
  color: #666;
  font-size: 14px;
  margin-left: 12px;
}

.filter-section {
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 6px;
}

.course-list {
  min-height: 400px;
}

.course-card {
  height: 100%;
  transition: all 0.3s;
}

.course-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.course-cover {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

.course-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-cover {
  font-size: 48px;
  color: #ccc;
}

.course-title {
  cursor: pointer;
  color: #1890ff;
  transition: color 0.3s;
}

.course-title:hover {
  color: #40a9ff;
}

.course-info {
  font-size: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.task-count {
  color: #666;
}

.creator {
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.update-time {
  color: #999;
  font-size: 11px;
}

.status-tag {
  font-size: 11px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.pagination-container {
  margin-top: 24px;
  text-align: center;
}

.text-warning {
  color: #fa8c16;
}

.text-info {
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .practice-courses-page {
    height: auto;
  }
  
  .full-height {
    height: auto;
  }
  
  .category-sider {
    display: none;
  }
  
  .course-content {
    padding: 16px;
  }
  
  .content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}

/* 导入模态框样式 */
.import-modal-content {
  min-height: 300px;
}

.scan-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.scan-tip {
  color: #999;
  font-size: 13px;
}

.scan-result {
  margin-top: 16px;
}

.course-title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.course-icon {
  color: #1890ff;
}

.batch-import-section {
  margin-top: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}
</style> 