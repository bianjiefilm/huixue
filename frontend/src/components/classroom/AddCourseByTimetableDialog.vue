<template>
  <a-modal
    v-model:open="visible"
    :title="currentStep === 1 ? '按课表添加课程' : '导入选项确认'"
    :width="currentStep === 1 ? '900px' : '500px'"
    :footer="null"
    @cancel="handleCancel"
  >
    <!-- 步骤1：选择课程和章节 -->
    <div v-if="currentStep === 1" class="timetable-selection-container">
      <!-- 搜索栏 -->
      <div class="search-section">
        <a-input-search
          v-model:value="searchText"
          placeholder="搜索课程名称"
          style="width: 300px"
          @search="onSearch"
        />
      </div>

      <!-- 方向筛选 -->
      <div class="filter-section">
        <span class="filter-label">方向:</span>
        <a-radio-group v-model:value="selectedDirection" buttonStyle="solid">
          <a-radio-button value="all" class="filter-btn">全部</a-radio-button>
          <a-radio-button value="大数据技术" class="filter-btn">大数据技术</a-radio-button>
          <a-radio-button value="人工智能" class="filter-btn">人工智能</a-radio-button>
          <a-radio-button value="云计算" class="filter-btn">云计算</a-radio-button>
          <a-radio-button value="金融" class="filter-btn">金融</a-radio-button>
          <a-radio-button value="数据分析" class="filter-btn">数据分析</a-radio-button>
        </a-radio-group>
      </div>

      <!-- 课程选择区域 -->
      <div class="course-selection">
        <a-row :gutter="16">
          <a-col :span="10">
            <div class="selection-panel">
              <div class="panel-header">
                <h4>可选课程</h4>
                <span class="count">{{ availableCourses.length }}个课程</span>
              </div>
              <div class="course-list-container">
                <a-radio-group v-model:value="selectedCourseId" style="width: 100%">
                  <div
                    v-for="course in filteredCourses"
                    :key="course.id"
                    class="course-item"
                    :class="{ selected: selectedCourseId === course.id }"
                    @click="selectCourse(course.id)"
                  >
                    <a-radio :value="course.id" />
                    <div class="course-info">
                      <div class="course-name">{{ course.title }}</div>
                      <div class="course-meta">
                        <span class="course-type">{{ course.course_type === 'practice' ? '实践课程' : course.course_type === 'training' ? '实训课程' : '课程教材' }}</span>
                        <span class="divider">·</span>
                        <span class="difficulty">{{ course.difficulty }}</span>
                        <span class="divider">·</span>
                        <span class="direction">{{ course.direction }}</span>
                      </div>
                    </div>
                  </div>
                </a-radio-group>
              </div>
            </div>
          </a-col>

          <a-col :span="4" class="transfer-buttons">
            <a-button
              type="primary"
              :disabled="!selectedCourseId"
              @click="previewSelectedCourse"
            >
              预览 <RightOutlined />
            </a-button>
          </a-col>

          <a-col :span="10">
            <div class="selection-panel">
              <div class="panel-header">
                <h4>课程章节预览</h4>
                <span class="count" v-if="previewCourse">{{ selectedModules.length }}个章节已选</span>
              </div>
              <div class="preview-container" v-if="previewCourse">
                <div class="preview-course-name">{{ previewCourse.title }}</div>
                <a-checkbox-group v-model:value="selectedModules" style="width: 100%">
                  <div
                    v-for="(module, index) in previewCourse.modules"
                    :key="module.id"
                    class="module-item"
                  >
                    <a-checkbox :value="module.id">
                      <span class="module-number">第{{ index + 1 }}章</span>
                      <span class="module-name">{{ module.name }}</span>
                      <span class="module-lessons">({{ module.lesson_count || 0 }}节课)</span>
                    </a-checkbox>
                  </div>
                </a-checkbox-group>

                <div class="module-actions">
                  <a-checkbox
                    :checked="isAllModulesSelected"
                    :indeterminate="isIndeterminate"
                    @change="toggleAllModules"
                  >
                    全选
                  </a-checkbox>
                </div>
              </div>
              <div v-else class="empty-preview">
                <Empty description="请先选择课程查看章节" />
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 底部栏：显示已选课程 -->
      <div class="selected-course-bar" v-if="selectedCourseId">
        <span class="selected-label">已选择:</span>
        <span class="selected-course-name">{{ getSelectedCourseName() }}</span>
      </div>

      <!-- 章节选择 -->
      <div class="chapter-selection">
        <span class="chapter-label">添加到章节:</span>
        <a-select
          v-model:value="selectedChapterId"
          style="width: 300px"
          placeholder="请选择目标章节"
        >
          <a-select-option
            v-for="chapter in chapters"
            :key="chapter.id"
            :value="chapter.id"
          >
            {{ chapter.title || chapter.name }}
          </a-select-option>
        </a-select>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <a-button @click="handleCancel">取消</a-button>
        <a-button
          type="primary"
          @click="goToStep2"
          :disabled="!canProceedToStep2"
        >
          下一步
        </a-button>
      </div>
    </div>

    <!-- 步骤2：导入选项确认 -->
    <div v-else class="import-options-container">
      <div class="import-summary">
        <p>您已选择课程：<strong>{{ previewCourse?.title }}</strong></p>
        <p>已选章节：<strong>{{ selectedModules.length }}</strong> 个</p>
        <p>添加到：<strong>{{ getSelectedChapterName() }}</strong></p>
      </div>

      <a-divider />

      <div class="import-options">
        <h4>请选择需要导入的内容：</h4>
        <div class="options-list">
          <a-checkbox v-model:checked="importOptions.outline">
            <span class="option-label">课程大纲</span>
            <span class="option-desc">导入课程的教学大纲和目标</span>
          </a-checkbox>
          <a-checkbox v-model:checked="importOptions.resources">
            <span class="option-label">教学资源</span>
            <span class="option-desc">导入课件、视频、文档等教学资源</span>
          </a-checkbox>
          <a-checkbox v-model:checked="importOptions.assessments">
            <span class="option-label">课程考核</span>
            <span class="option-desc">导入作业、测验、考试等考核内容</span>
          </a-checkbox>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <a-button @click="goToStep1">上一步</a-button>
        <a-button
          type="primary"
          @click="handleSubmit"
          :loading="submitLoading"
        >
          确定导入
        </a-button>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { message, Empty, Divider as ADivider } from 'ant-design-vue';
import { RightOutlined } from '@ant-design/icons-vue';
import { get, post } from '@/utils/request';
import { useUserStore } from '@/stores/user';

interface Props {
  classroomId: string;
  chapterId?: string;
}

interface Course {
  id: string;
  name: string;
  chapter_count: number;
  lesson_count: number;
  modules?: Module[];
}

interface Module {
  id: string;
  name: string;
  lesson_count: number;
}

const props = defineProps<Props>();
const emit = defineEmits(['success', 'cancel']);

const visible = ref(false);
const currentStep = ref(1); // 1: 选择课程, 2: 导入选项确认
const searchText = ref('');
const selectedDirection = ref('all'); // 方向筛选
const availableCourses = ref<Course[]>([]);
const selectedCourseId = ref<string>(''); // 单选模式
const previewCourse = ref<Course | null>(null);
const selectedModules = ref<string[]>([]);
const chapters = ref<any[]>([]);
const selectedChapterId = ref('');
const submitLoading = ref(false);

// 导入选项
const importOptions = ref({
  outline: true,      // 课程大纲
  resources: true,    // 教学资源
  assessments: true   // 课程考核
});

// 计算属性
const filteredCourses = computed(() => {
  let courses = availableCourses.value;

  // 方向筛选
  if (selectedDirection.value !== 'all') {
    courses = courses.filter(course => course.direction === selectedDirection.value);
  }

  // 搜索文本筛选
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase();
    courses = courses.filter(course =>
      (course.title || course.name || '').toLowerCase().includes(keyword)
    );
  }

  return courses;
});

const isAllModulesSelected = computed(() => {
  if (!previewCourse.value || !previewCourse.value.modules) return false;
  return selectedModules.value.length === previewCourse.value.modules.length;
});

const isIndeterminate = computed(() => {
  if (!previewCourse.value || !previewCourse.value.modules) return false;
  return selectedModules.value.length > 0 &&
         selectedModules.value.length < previewCourse.value.modules.length;
});

const canProceedToStep2 = computed(() => {
  return selectedCourseId.value &&
         selectedModules.value.length > 0 &&
         selectedChapterId.value;
});

// 方法
const open = () => {
  visible.value = true;
  currentStep.value = 1;
  selectedCourseId.value = '';
  selectedDirection.value = 'all';
  searchText.value = '';
  selectedModules.value = [];
  previewCourse.value = null;
  importOptions.value = { outline: true, resources: true, assessments: true };
  loadAvailableCourses();
  loadChapters();
};

const handleCancel = () => {
  visible.value = false;
  currentStep.value = 1;
  emit('cancel');
};

const onSearch = (value: string) => {
  searchText.value = value;
};

const selectCourse = (courseId: string) => {
  selectedCourseId.value = courseId;
};

const goToStep1 = () => {
  currentStep.value = 1;
};

const goToStep2 = () => {
  if (!canProceedToStep2.value) {
    message.warning('请选择课程、章节和目标位置');
    return;
  }
  currentStep.value = 2;
};

const getSelectedChapterName = () => {
  const chapter = chapters.value.find(ch => ch.id === selectedChapterId.value);
  return chapter?.title || chapter?.name || '未选择';
};

// 获取已选课程名称
const getSelectedCourseName = () => {
  const course = availableCourses.value.find(c => c.id === selectedCourseId.value);
  return course?.title || course?.name || '';
};

const previewSelectedCourse = async () => {
  if (!selectedCourseId.value) {
    message.warning('请先选择一个课程');
    return;
  }

  await loadCourseDetails(selectedCourseId.value);
};

const toggleAllModules = (e: any) => {
  if (!previewCourse.value || !previewCourse.value.modules) return;
  
  if (e.target.checked) {
    selectedModules.value = previewCourse.value.modules.map(m => m.id);
  } else {
    selectedModules.value = [];
  }
};

const handleSubmit = async () => {
  submitLoading.value = true;

  try {
    const response = await post(`/v1/classrooms/${props.classroomId}/courses/add-by-timetable`, {
      source_course_id: selectedCourseId.value,
      selected_modules: selectedModules.value,
      target_chapter_id: selectedChapterId.value,
      import_options: {
        include_outline: importOptions.value.outline,
        include_resources: importOptions.value.resources,
        include_assessments: importOptions.value.assessments
      }
    });

    if (response) {
      if (response.code === '0000' || response.code === 1 || response.code === '1' || response.message === 'success' || !response.code) {
        message.success('课程导入成功');
        visible.value = false;
        currentStep.value = 1;
        emit('success');
      } else {
        message.error(response.message || response.msg || '导入失败');
      }
    }
  } catch (error) {
    console.error('导入课程失败:', error);
    message.error('导入课程失败');
  } finally {
    submitLoading.value = false;
  }
};

// 加载可用课程列表
const loadAvailableCourses = async () => {
  try {
    const response = await get('/v1/courses/library');
    availableCourses.value = response.data.list || [];
  } catch (error) {
    console.error('获取课程列表失败:', error);
    message.error('获取课程列表失败');
  }
};

// 加载课程详情
const loadCourseDetails = async (courseId: string) => {
  try {
    const response = await get(`/v1/courses/${courseId}/modules`);
    const course = availableCourses.value.find(c => c.id === courseId);
    if (course) {
      previewCourse.value = {
        ...course,
        modules: response.data.list || []
      };
      selectedModules.value = []; // 重置选择
    }
  } catch (error) {
    console.error('获取课程章节失败:', error);
    message.error('获取课程章节失败');
  }
};

// 加载章节列表
const loadChapters = async () => {
  try {
    const userStore = useUserStore();
    const response = await get(`/api/v1/classrooms/${props.classroomId}/chapters`, {
      teacher_id: userStore.userId
    });
    chapters.value = response.data?.chapters || response.data?.list || [];
    
    if (props.chapterId && chapters.value.some(ch => ch.id === props.chapterId)) {
      selectedChapterId.value = props.chapterId;
    } else if (chapters.value.length > 0) {
      selectedChapterId.value = chapters.value[0].id;
    }
  } catch (error) {
    console.error('获取章节列表失败:', error);
  }
};

// 监听弹窗显示状态变化
watch(() => visible.value, (newVisible) => {
  if (newVisible) {
    // 弹窗打开时重新加载数据
    loadAvailableCourses();
    loadChapters();
  }
});

// 暴露方法给父组件
defineExpose({
  open
});
</script>

<style scoped>
.timetable-selection-container {
  padding: 0 10px;
}

.search-section {
  margin-bottom: 16px;
}

.filter-section {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.filter-label {
  margin-right: 12px;
  color: #666;
  font-weight: 500;
}

.filter-btn {
  margin-right: 4px;
  font-size: 13px;
}

.selected-course-bar {
  background-color: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.selected-label {
  color: #1890ff;
  font-weight: 500;
  margin-right: 8px;
}

.selected-course-name {
  color: #333;
  font-weight: 500;
}

.course-selection {
  margin-bottom: 20px;
}

.selection-panel {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.count {
  font-size: 12px;
  color: #999;
}

.course-list-container,
.preview-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.course-item {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
}

.course-item:hover {
  border-color: #1890ff;
  background-color: #f6f9ff;
}

.course-item.selected {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.course-info {
  flex: 1;
  margin-left: 12px;
}

.course-name {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.course-meta {
  font-size: 12px;
  color: #999;
}

.divider {
  margin: 0 8px;
}

.transfer-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-course-name {
  font-size: 16px;
  font-weight: 500;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.module-item {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.module-item:last-child {
  border-bottom: none;
}

.module-number {
  color: #999;
  margin-right: 8px;
}

.module-name {
  font-size: 14px;
}

.module-lessons {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

.module-actions {
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}

.empty-preview {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chapter-selection {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.chapter-label {
  margin-right: 12px;
  font-weight: 500;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 导入选项容器样式 */
.import-options-container {
  padding: 0 10px;
}

.import-summary {
  background-color: #f5f5f5;
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 16px;
}

.import-summary p {
  margin: 8px 0;
  color: #666;
}

.import-summary strong {
  color: #333;
}

.import-options h4 {
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.options-list :deep(.ant-checkbox-wrapper) {
  display: flex;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  transition: all 0.3s;
}

.options-list :deep(.ant-checkbox-wrapper:hover) {
  border-color: #1890ff;
  background-color: #f6f9ff;
}

.options-list :deep(.ant-checkbox-wrapper-checked) {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.option-label {
  font-weight: 500;
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}

.option-desc {
  font-size: 12px;
  color: #999;
  display: block;
}
</style>