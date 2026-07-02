<template>
  <div class="excellent-works-page">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 返回按钮 -->
      <div class="back-link">
        <router-link :to="`/classroom/${classroomId}/status`">
          <a-button type="link">
            <template #icon><arrow-left-outlined /></template>
            返回课程管理
          </a-button>
        </router-link>
      </div>

      <!-- 页面标题 -->
      <div class="page-header">
        <h1>优秀作业展示</h1>
        <div class="header-meta">
          <span>展示学生的优秀实训作业，供其他学生参考学习</span>
        </div>
      </div>

      <!-- 筛选区域 -->
      <a-card class="filter-card">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-select 
              v-model:value="filterCourseId" 
              placeholder="选择课程"
              style="width: 100%"
              allowClear
              @change="handleFilterChange"
            >
              <a-select-option value="">全部课程</a-select-option>
              <a-select-option 
                v-for="course in courseList" 
                :key="course.id"
                :value="course.id"
              >
                {{ course.name }}
              </a-select-option>
            </a-select>
          </a-col>
          <a-col :span="8">
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索学生姓名"
              @search="handleSearch"
            />
          </a-col>
          <a-col :span="8">
            <a-radio-group 
              v-model:value="courseTypeFilter" 
              button-style="solid"
              @change="handleFilterChange"
            >
              <a-radio-button value="">全部类型</a-radio-button>
              <a-radio-button value="TRAINING">实训课程</a-radio-button>
            </a-radio-group>
          </a-col>
        </a-row>
      </a-card>

      <!-- 优秀作业列表 -->
      <div class="works-list">
        <a-empty v-if="excellentWorks.length === 0 && !loading" description="暂无优秀作业" />
        
        <a-row v-else :gutter="[16, 16]">
          <a-col 
            v-for="work in excellentWorks" 
            :key="work.id"
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6"
          >
            <a-card 
              hoverable 
              class="work-card"
              @click="viewWorkDetail(work)"
            >
              <template #cover>
                <div class="work-cover">
                  <file-text-outlined />
                </div>
              </template>
              
              <a-card-meta>
                <template #title>
                  <div class="work-title">{{ work.course_name }}</div>
                </template>
                <template #description>
                  <div class="work-info">
                    <div class="student-info">
                      <a-avatar 
                        :src="work.avatar_url" 
                        :size="24"
                        class="student-avatar"
                      >
                        {{ work.student_name.charAt(0) }}
                      </a-avatar>
                      <span class="student-name">{{ work.student_name }}</span>
                    </div>
                    <div class="work-meta">
                      <div class="meta-item">
                        <clock-circle-outlined />
                        <span>{{ formatDate(work.submission_time) }}</span>
                      </div>
                      <div class="meta-item">
                        <trophy-outlined />
                        <span class="score">{{ work.score }}分</span>
                      </div>
                    </div>
                    <div class="teacher-feedback" v-if="work.teacher_feedback">
                      <p class="feedback-label">教师点评：</p>
                      <p class="feedback-content">{{ work.teacher_feedback }}</p>
                    </div>
                  </div>
                </template>
              </a-card-meta>
            </a-card>
          </a-col>
        </a-row>

        <!-- 分页 -->
        <div class="pagination-container" v-if="totalRecords > 0">
          <a-pagination
            v-model:current="currentPage"
            v-model:pageSize="pageSize"
            :total="totalRecords"
            :show-size-changer="true"
            :show-total="(total: number) => `共 ${total} 条记录`"
            @change="handlePageChange"
          />
        </div>
      </div>
    </a-spin>

    <!-- 作业详情模态框 -->
    <a-modal
      v-model:open="detailModalVisible"
      :title="`${currentWork?.student_name} - ${currentWork?.course_name}`"
      width="800px"
      :footer="null"
    >
      <div class="work-detail" v-if="currentWork">
        <div class="detail-header">
          <div class="student-section">
            <a-avatar 
              :src="currentWork.avatar_url" 
              :size="48"
            >
              {{ currentWork.student_name.charAt(0) }}
            </a-avatar>
            <div class="student-detail">
              <h3>{{ currentWork.student_name }}</h3>
              <p>学号：{{ currentWork.student_number }}</p>
            </div>
          </div>
          <div class="score-section">
            <div class="score-value">{{ currentWork.score }}</div>
            <div class="score-label">得分</div>
          </div>
        </div>

        <a-divider />

        <div class="detail-content">
          <div class="section">
            <h4>提交时间</h4>
            <p>{{ formatDateTime(currentWork.submission_time) }}</p>
          </div>

          <div class="section">
            <h4>教师点评</h4>
            <p>{{ currentWork.teacher_feedback || '暂无点评' }}</p>
          </div>

          <div class="section" v-if="currentWork.graded_by_teacher_name">
            <h4>批阅教师</h4>
            <p>{{ currentWork.graded_by_teacher_name }}</p>
          </div>

          <div class="section" v-if="currentWork.design_files && currentWork.design_files.length > 0">
            <h4>设计文件</h4>
            <div class="file-list">
              <a-button 
                v-for="(file, index) in currentWork.design_files" 
                :key="`design-${index}`"
                type="link"
                @click="downloadFile(file)"
              >
                <file-outlined /> {{ getFileName(file) }}
              </a-button>
            </div>
          </div>

          <div class="section" v-if="currentWork.experiment_reports && currentWork.experiment_reports.length > 0">
            <h4>实验报告</h4>
            <div class="file-list">
              <a-button 
                v-for="(file, index) in currentWork.experiment_reports" 
                :key="`report-${index}`"
                type="link"
                @click="downloadFile(file)"
              >
                <file-text-outlined /> {{ getFileName(file) }}
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import { 
  ArrowLeftOutlined, 
  FileTextOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  FileOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import { useClassroomStore } from '../../stores/classroom';
import {
  getClassroomExcellentWorks,
  type ExcellentWork
} from '../../api/grades';

// 路由相关
const route = useRoute();
const userStore = useUserStore();
const classroomStore = useClassroomStore();
const classroomId = computed(() => route.params.id as string);

// 状态管理
const loading = ref(false);
const excellentWorks = ref<ExcellentWork[]>([]);
const currentPage = ref(1);
const pageSize = ref(12);
const totalRecords = ref(0);
const searchText = ref('');
const filterCourseId = ref('');
const courseTypeFilter = ref('');
const courseList = ref<any[]>([]);

// 详情模态框
const detailModalVisible = ref(false);
const currentWork = ref<ExcellentWork | null>(null);

// 获取课程列表
const loadCourseList = async () => {
  // 从课堂信息中获取课程列表
  if (classroomStore.currentClassroom?.courses) {
    courseList.value = classroomStore.currentClassroom.courses.filter(
      course => course.type === 'training' // 只有实训课程有优秀作业
    );
  }
};

// 加载优秀作业列表
const loadExcellentWorks = async () => {
  loading.value = true;
  try {
    const params: any = {
      classroom_id: parseInt(classroomId.value),
      page: currentPage.value,
      page_size: pageSize.value
    };

    // 添加用户身份参数
    if (userStore.currentUser?.role === 'teacher') {
      params.teacher_id = userStore.currentUser.id;
    } else {
      params.student_id = userStore.currentUser?.id;
    }

    // 添加课程类型筛选
    if (courseTypeFilter.value) {
      params.course_type = courseTypeFilter.value;
    }

    const res = await getClassroomExcellentWorks(params);
    
    if (res.code === '0000') {
      excellentWorks.value = res.data.list;
      totalRecords.value = res.data.meta.total;
    } else {
      message.error(res.message || '获取优秀作业列表失败');
    }
  } catch (error) {
    console.error('获取优秀作业列表失败:', error);
    message.error('获取优秀作业列表失败');
  } finally {
    loading.value = false;
  }
};

// 格式化日期
const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD');
};

// 格式化日期时间
const formatDateTime = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
};

// 获取文件名
const getFileName = (filePath: string) => {
  return filePath.split('/').pop() || filePath;
};

// 处理筛选变化
const handleFilterChange = () => {
  currentPage.value = 1;
  loadExcellentWorks();
};

// 处理搜索
const handleSearch = () => {
  currentPage.value = 1;
  // 这里可以实现前端过滤，或者如果后端支持搜索，可以调用API
  loadExcellentWorks();
};

// 处理分页变化
const handlePageChange = () => {
  loadExcellentWorks();
};

// 查看作业详情
const viewWorkDetail = (work: ExcellentWork) => {
  currentWork.value = work;
  detailModalVisible.value = true;
};

// 下载文件
const downloadFile = (fileUrl: string) => {
  // 实际项目中这里应该处理文件下载
  window.open(fileUrl, '_blank');
};

// 生命周期钩子
onMounted(async () => {
  await classroomStore.fetchClassroomDetail(classroomId.value);
  await loadCourseList();
  await loadExcellentWorks();
});
</script>

<style scoped>
.excellent-works-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.header-meta {
  color: rgba(0, 0, 0, 0.65);
  font-size: 14px;
}

.filter-card {
  margin-bottom: 24px;
}

.works-list {
  min-height: 400px;
}

.work-card {
  height: 100%;
  transition: all 0.3s ease;
}

.work-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.work-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 48px;
  color: #fff;
}

.work-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.work-info {
  font-size: 14px;
}

.student-info {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.student-avatar {
  margin-right: 8px;
}

.student-name {
  font-weight: 500;
}

.work-meta {
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 4px;
}

.meta-item :deep(svg) {
  margin-right: 8px;
  font-size: 14px;
}

.score {
  color: #52c41a;
  font-weight: 500;
}

.teacher-feedback {
  border-top: 1px solid #f0f0f0;
  padding-top: 12px;
  margin-top: 12px;
}

.feedback-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin: 0 0 4px 0;
}

.feedback-content {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.85);
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 32px;
}

/* 详情模态框样式 */
.work-detail {
  padding: 16px 0;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.student-section {
  display: flex;
  align-items: center;
}

.student-detail {
  margin-left: 16px;
}

.student-detail h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
}

.student-detail p {
  margin: 0;
  color: rgba(0, 0, 0, 0.65);
}

.score-section {
  text-align: center;
}

.score-value {
  font-size: 32px;
  font-weight: 600;
  color: #52c41a;
}

.score-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.detail-content .section {
  margin-bottom: 24px;
}

.detail-content h4 {
  font-size: 16px;
  font-weight: 500;
  margin: 0 0 12px 0;
}

.detail-content p {
  margin: 0;
  color: rgba(0, 0, 0, 0.85);
  line-height: 1.6;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-list .ant-btn {
  justify-content: flex-start;
  text-align: left;
}
</style>