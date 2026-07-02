<template>
  <div class="training-library-page">
    <div class="page-header">
      <div class="header-content">
        <div class="left-content">
          <h2>实训资源库</h2>
          <p class="library-count">共 {{ totalTrainings }} 个实训项目{{ hasFilters ? `，当前显示 ${trainings.length} 个` : '' }}</p>
        </div>
        <a-space>
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索实训名称或描述"
            style="width: 300px"
            @search="handleSearch"
          />
          <a-select
            v-model:value="typeFilter"
            style="width: 150px"
            placeholder="类型筛选"
            @change="handleFilterChange"
          >
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="CODING">编程式实训</a-select-option>
            <a-select-option value="DRAG_DROP">拖拽式实训</a-select-option>
          </a-select>
          <a-select
            v-model:value="difficultyFilter"
            style="width: 150px"
            placeholder="难度筛选"
            @change="handleFilterChange"
          >
            <a-select-option value="">全部难度</a-select-option>
            <a-select-option value="beginner">初级</a-select-option>
            <a-select-option value="intermediate">中级</a-select-option>
            <a-select-option value="advanced">高级</a-select-option>
          </a-select>
          <a-select
            v-model:value="presetFilter"
            style="width: 150px"
            placeholder="来源筛选"
            @change="handleFilterChange"
          >
            <a-select-option value="">全部来源</a-select-option>
            <a-select-option value="true">平台预设</a-select-option>
            <a-select-option value="false">用户发布</a-select-option>
          </a-select>
          <a-button @click="resetFilters">重置筛选</a-button>
          <a-button v-if="userRole === 'admin'" type="primary" @click="initializeLibrary">
            <template #icon><SyncOutlined /></template>
            初始化资源库
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="page-content">
      <a-spin :spinning="loading">
        <a-empty v-if="trainings.length === 0 && !loading" description="暂无实训资源" />
        
        <div v-else class="trainings-grid">
          <a-list
            :data-source="trainings"
            :pagination="pagination"
            :grid="{ gutter: 24, column: 3 }"
          >
            <template #renderItem="{ item }">
              <a-list-item>
                <a-card hoverable class="training-card" @click="handleViewDetail(item)">
                  <template #cover>
                    <div class="card-cover-container">
                      <img alt="实训封面" :src="item.cover || getDefaultCover(item.training_type)" />
                      <a-tag class="type-tag" :color="getTypeColor(item.training_type)">
                        {{ getTypeText(item.training_type) }}
                      </a-tag>
                      <a-tag class="source-tag" :color="item.is_preset ? 'blue' : 'green'">
                        {{ item.is_preset ? '平台预设' : '用户发布' }}
                      </a-tag>
                    </div>
                  </template>
                  <a-card-meta :title="item.title">
                    <template #description>
                      <div class="training-card-desc">
                        <div class="training-intro" :title="item.intro">
                          {{ truncateText(item.intro || '', 80) }}
                        </div>
                        <div class="training-meta">
                          <div class="meta-info">
                            <a-tag>{{ getDifficultyText(item.difficulty) }}</a-tag>
                            <a-tag>{{ item.course_hours }}课时</a-tag>
                            <a-tag v-if="item.dataset_count > 0">{{ item.dataset_count }}个数据集</a-tag>
                            <a-tag v-if="item.industry">{{ item.industry }}</a-tag>
                          </div>
                          <div class="action-info">
                            <span class="creator-name" v-if="item.creator_name">{{ item.creator_name }}</span>
                            <span class="update-time">{{ formatDate(item.updated_at || item.created_at) }}</span>
                          </div>
                        </div>
                      </div>
                    </template>
                  </a-card-meta>
                  <template #actions>
                    <EyeOutlined key="view" @click.stop="handleViewDetail(item)" title="查看详情" />
                    <PlusOutlined key="add" @click.stop="handleAddToClassroom(item)" title="添加到课堂" />
                    <DownloadOutlined key="download" @click.stop="handleDownload(item)" title="下载资源" />
                  </template>
                </a-card>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-spin>
    </div>

    <!-- 实训详情弹窗 -->
    <a-modal
      v-model:open="detailModalVisible"
      title="实训详情"
      width="900px"
      :footer="null"
    >
      <div v-if="currentTraining" class="training-detail">
        <div class="detail-header">
          <h3>{{ currentTraining.title }}</h3>
          <div class="detail-tags">
            <a-tag :color="getTypeColor(currentTraining.training_type)">
              {{ getTypeText(currentTraining.training_type) }}
            </a-tag>
            <a-tag>{{ getDifficultyText(currentTraining.difficulty) }}</a-tag>
            <a-tag v-if="currentTraining.industry">{{ currentTraining.industry }}</a-tag>
            <a-tag :color="currentTraining.is_preset ? 'blue' : 'green'">
              {{ currentTraining.is_preset ? '平台预设' : '用户发布' }}
            </a-tag>
          </div>
        </div>
        
        <div class="detail-content">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="实训简介" :span="2">
              {{ currentTraining.intro }}
            </a-descriptions-item>
            <a-descriptions-item label="课时">
              {{ currentTraining.course_hours }}课时
            </a-descriptions-item>
            <a-descriptions-item label="数据集">
              {{ currentTraining.dataset_count }}个
            </a-descriptions-item>
            <a-descriptions-item label="创建者" v-if="currentTraining.creator_name">
              {{ currentTraining.creator_name }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDate(currentTraining.created_at) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
        
        <div class="detail-actions">
          <a-space>
            <a-button type="primary" @click="handleAddToClassroom(currentTraining)">
              添加到课堂
            </a-button>
            <a-button @click="handleDownload(currentTraining)">
              下载资源
            </a-button>
            <a-button @click="detailModalVisible = false">
              关闭
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>

    <!-- 添加到课堂弹窗 -->
    <a-modal
      v-model:open="addToClassroomModalVisible"
      title="添加实训到课堂"
      @ok="handleConfirmAddToClassroom"
      @cancel="addToClassroomModalVisible = false"
    >
      <a-form
        ref="addToClassroomForm"
        :model="addToClassroomData"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="选择课堂" name="classroomId" :rules="[{ required: true, message: '请选择课堂' }]">
          <a-select
            v-model:value="addToClassroomData.classroomId"
            placeholder="请选择课堂"
            @change="handleClassroomChange"
          >
            <a-select-option
              v-for="classroom in myClassrooms"
              :key="classroom.id"
              :value="classroom.id"
            >
              {{ classroom.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="开始时间" name="startTime" :rules="[{ required: true, message: '请选择开始时间' }]">
          <a-date-picker
            v-model:value="addToClassroomData.startTime"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
            placeholder="请选择开始时间"
          />
        </a-form-item>
        <a-form-item label="结束时间" name="endTime" :rules="[{ required: true, message: '请选择结束时间' }]">
          <a-date-picker
            v-model:value="addToClassroomData.endTime"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
            placeholder="请选择结束时间"
          />
        </a-form-item>
        <a-form-item label="补交设置" name="allowLateSubmission">
          <a-switch
            v-model:checked="addToClassroomData.allowLateSubmission"
            checked-children="允许"
            un-checked-children="禁止"
          />
        </a-form-item>
        <a-form-item
          v-if="addToClassroomData.allowLateSubmission"
          label="补交天数"
          name="lateSubmissionDays"
          :rules="[{ required: true, message: '请输入补交天数' }]"
        >
          <a-input-number
            v-model:value="addToClassroomData.lateSubmissionDays"
            :min="1"
            :max="30"
            style="width: 100%"
            placeholder="允许补交的天数"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { EyeOutlined, PlusOutlined, DownloadOutlined, SyncOutlined } from '@ant-design/icons-vue';
import { 
  getTrainingLibrary, 
  getTrainingLibraryDetail, 
  addTrainingToClassroomFromLibrary,
  seedTrainingResources,
  convertTrainingTypeFromBackend,
  type TrainingLibraryItem,
  type TrainingLibraryQueryParams,
  type AddTrainingToClassroomParams
} from '@/api/training';
import { getMyClassrooms } from '@/api/classroom';
import dayjs, { type Dayjs } from 'dayjs';

// 响应式数据
const loading = ref(false);
const trainings = ref<TrainingLibraryItem[]>([]);
const totalTrainings = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);

// 筛选条件
const searchKeyword = ref('');
const typeFilter = ref('');
const difficultyFilter = ref('');
const presetFilter = ref('');

// 弹窗状态
const detailModalVisible = ref(false);
const addToClassroomModalVisible = ref(false);
const currentTraining = ref<TrainingLibraryItem | null>(null);

// 添加到课堂表单数据
const addToClassroomData = reactive({
  classroomId: '',
  startTime: null as Dayjs | null,
  endTime: null as Dayjs | null,
  allowLateSubmission: false,
  lateSubmissionDays: 3
});

// 我的课堂列表
const myClassrooms = ref<any[]>([]);

// 用户角色（这里应该从用户状态中获取）
const userRole = ref('teacher'); // 'admin', 'teacher', 'student'

// 计算属性
const hasFilters = computed(() => {
  return searchKeyword.value || typeFilter.value || difficultyFilter.value || presetFilter.value;
});

const pagination = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: totalTrainings.value,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) => 
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  onChange: (page: number, size: number) => {
    currentPage.value = page;
    pageSize.value = size;
    loadTrainings();
  }
}));

// 方法
const loadTrainings = async () => {
  loading.value = true;
  try {
    const params: TrainingLibraryQueryParams = {
      page: currentPage.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value || undefined,
      training_type: typeFilter.value || undefined,
      difficulty: difficultyFilter.value || undefined,
      is_preset: presetFilter.value ? presetFilter.value === 'true' : undefined,
      sort_by: 'created_at',
      sort_order: 'desc'
    };

    const result = await getTrainingLibrary(params);
    trainings.value = result.list;
    totalTrainings.value = result.total;
  } catch (error) {
    message.error('获取实训列表失败');
    console.error('获取实训列表失败:', error);
  } finally {
    loading.value = false;
  }
};

const loadMyClassrooms = async () => {
  try {
    const result = await getMyClassrooms();
    // API返回格式: { ongoing: [...], upcoming: [...], ended: [...] }
    // 只显示进行中和即将开始的课堂（不显示已结束的课堂）
    const data = result.data || {};
    myClassrooms.value = [
      ...(data.ongoing || []),
      ...(data.upcoming || [])
    ];
  } catch (error) {
    console.error('获取我的课堂失败:', error);
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  loadTrainings();
};

const handleFilterChange = () => {
  currentPage.value = 1;
  loadTrainings();
};

const resetFilters = () => {
  searchKeyword.value = '';
  typeFilter.value = '';
  difficultyFilter.value = '';
  presetFilter.value = '';
  currentPage.value = 1;
  loadTrainings();
};

const handleViewDetail = async (item: TrainingLibraryItem) => {
  try {
    const detail = await getTrainingLibraryDetail(item.id);
    currentTraining.value = { ...item, ...detail };
    detailModalVisible.value = true;
  } catch (error) {
    message.error('获取实训详情失败');
    console.error('获取实训详情失败:', error);
  }
};

const handleAddToClassroom = (item: TrainingLibraryItem) => {
  currentTraining.value = item;
  // 重置表单数据
  addToClassroomData.classroomId = '';
  addToClassroomData.startTime = null;
  addToClassroomData.endTime = null;
  addToClassroomData.allowLateSubmission = false;
  addToClassroomData.lateSubmissionDays = 3;
  
  addToClassroomModalVisible.value = true;
};

const handleClassroomChange = () => {
  // 可以在这里处理课堂选择变化的逻辑
};

const handleConfirmAddToClassroom = async () => {
  if (!currentTraining.value || !addToClassroomData.classroomId || 
      !addToClassroomData.startTime || !addToClassroomData.endTime) {
    message.error('请完善必填信息');
    return;
  }

  try {
    const params: AddTrainingToClassroomParams = {
      start_time: addToClassroomData.startTime.toISOString(),
      end_time: addToClassroomData.endTime.toISOString(),
      allow_late_submission: addToClassroomData.allowLateSubmission,
      late_submission_days: addToClassroomData.allowLateSubmission ? addToClassroomData.lateSubmissionDays : 0,
      // R3 P0 #6 修: source_type=practice 时 backend 走 classroom_courses 表 (XQ01 类项目实训)
      source_type: (currentTraining.value as any)?.source_type || 'training',
    } as any;

    await addTrainingToClassroomFromLibrary(
      currentTraining.value.id,
      Number(addToClassroomData.classroomId),
      params
    );

    message.success('添加实训到课堂成功');
    addToClassroomModalVisible.value = false;
  } catch (error) {
    message.error('添加实训到课堂失败');
    console.error('添加实训到课堂失败:', error);
  }
};

const handleDownload = (item: TrainingLibraryItem) => {
  // 下载实训资源的逻辑
  message.info('下载功能开发中...');
};

const initializeLibrary = async () => {
  try {
    loading.value = true;
    const result = await seedTrainingResources();
    message.success(`初始化完成：新增${result.created}个，更新${result.updated}个实训`);
    loadTrainings(); // 重新加载列表
  } catch (error) {
    message.error('初始化实训资源库失败');
    console.error('初始化失败:', error);
  } finally {
    loading.value = false;
  }
};

// 工具函数
const getDefaultCover = (type: string) => {
  const covers = {
    'CODING': '/images/training-cover-coding.png',
    'DRAG_DROP': '/images/training-cover-dragdrop.png'
  };
  return covers[type] || '/images/training-cover-default.png';
};

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    'CODING': 'blue',
    'DRAG_DROP': 'green',
    'DATA_ANALYSIS': 'green',  // BI类型也用绿色
    'BI': 'green',
    'VDI': 'purple'
  };
  return colors[type] || 'default';
};

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    'CODING': '编程式实训',
    'DRAG_DROP': '拖拽式实训',
    'DATA_ANALYSIS': '拖拽式实训',  // DATA_ANALYSIS 映射为拖拽式
    'BI': '拖拽式实训',
    'VDI': 'VDI环境'
  };
  return texts[type] || '未知类型';
};

const getDifficultyText = (difficulty: string) => {
  const texts = {
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级'
  };
  return texts[difficulty] || difficulty;
};

const truncateText = (text: string, maxLength: number) => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

const formatDate = (dateStr: string) => {
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm');
};

// 生命周期
onMounted(() => {
  loadTrainings();
  loadMyClassrooms();
});
</script>

<style scoped>
.training-library-page {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  background: white;
  padding: 24px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.left-content h2 {
  margin: 0 0 8px 0;
  color: #f3f4f6;
  font-size: 24px;
  font-weight: 600;
}

.library-count {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.page-content {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.trainings-grid .ant-list-item {
  margin-bottom: 24px;
}

.training-card {
  height: 100%;
  transition: all 0.3s ease;
}

.training-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.card-cover-container {
  position: relative;
  height: 180px;
  overflow: hidden;
}

.card-cover-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-tag, .source-tag {
  position: absolute;
  top: 12px;
  z-index: 1;
}

.type-tag {
  left: 12px;
}

.source-tag {
  right: 12px;
}

.training-card-desc {
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.training-intro {
  flex: 1;
  color: #6b7280;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 12px;
}

.training-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-info .ant-tag {
  margin-right: 4px;
  margin-bottom: 4px;
}

.action-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #9ca3af;
}

.creator-name {
  font-weight: 500;
}

.training-detail {
  padding: 16px 0;
}

.detail-header {
  margin-bottom: 24px;
}

.detail-header h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  font-weight: 600;
  color: #f3f4f6;
}

.detail-tags .ant-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.detail-content {
  margin-bottom: 24px;
}

.detail-actions {
  text-align: right;
}
</style>