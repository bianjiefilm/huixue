<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar
      :title="(courseData?.type === 'practice' ? '实践课程' : '实训课程') + '详情'"
      show-back
      back-to="/admin/course/practice"
    />

    <a-spin :spinning="loading">
      <a-card :bordered="false" v-if="courseData">
        <a-row :gutter="16" class="course-header">
          <a-col :span="6">
            <div class="course-cover">
              <img :src="courseData.cover" alt="课程封面" />
            </div>
          </a-col>
          <a-col :span="18">
            <div class="course-title">
              <h1>{{ courseData.title }}</h1>
              <a-tag :color="getStatusColor(courseData.status)">
                {{ getStatusText(courseData.status) }}
              </a-tag>
            </div>
            <div class="course-meta">
              <p><strong>教师：</strong>{{ courseData.teacher }}</p>
              <p><strong>所属院校：</strong>{{ courseData.university }}</p>
              <p v-if="courseData.type === 'practice'">
                <strong>所属方向：</strong>{{ (courseData as PracticeCourse).direction }}
              </p>
              <p v-if="courseData.type === 'practice'">
                <strong>所属分类：</strong>{{ (courseData as PracticeCourse).category }}
              </p>
              <p v-if="courseData.type === 'training'">
                <strong>所属行业：</strong>{{ (courseData as TrainingCourse).industry }}
              </p>
              <p><strong>创建时间：</strong>{{ formatDateTime(courseData.createdAt) }}</p>
              <p><strong>更新时间：</strong>{{ formatDateTime(courseData.updatedAt) }}</p>
            </div>
            <div class="course-actions">
              <a-space>
                <a-button 
                  v-if="courseData.status === 'published'" 
                  type="primary" 
                  danger
                  @click="showUnpublishConfirm"
                >
                  下架课程
                </a-button>
                <a-button 
                  v-else 
                  type="primary"
                  @click="showPublishConfirm"
                >
                  发布课程
                </a-button>
                <a-button @click="goBack">返回列表</a-button>
              </a-space>
            </div>
          </a-col>
        </a-row>
        
        <a-divider orientation="left">课程详情</a-divider>
        
        <div class="course-description">
          <div v-html="courseData.description"></div>
        </div>
      </a-card>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { useAdminCourseStore } from '@/stores/admin-course';
import type { BaseCourse, PracticeCourse, TrainingCourse } from '@/types/admin';
import { CourseStatus, CourseType } from '@/types/admin';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const route = useRoute();
const router = useRouter();
const adminCourseStore = useAdminCourseStore();

// 课程ID
const courseId = computed(() => route.params.id as string);

// 数据加载状态
const loading = ref(true);

// 课程数据
const courseData = ref<PracticeCourse | TrainingCourse | null>(null);

// 页面加载时获取数据
onMounted(async () => {
  try {
    loading.value = true;
    // 获取课程详情
    const course = await adminCourseStore.fetchCourseDetail(courseId.value);
    courseData.value = course;
  } catch (error) {
    message.error('获取课程详情失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
});

// 返回上一页
const goBack = () => {
  router.back();
};

// 格式化日期时间
const formatDateTime = (dateTimeString: string) => {
  const date = new Date(dateTimeString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
};

// 获取状态对应的颜色
const getStatusColor = (status: CourseStatus) => {
  switch (status) {
    case CourseStatus.PUBLISHED:
      return 'green';
    case CourseStatus.UNPUBLISHED:
      return 'orange';
    case CourseStatus.PENDING:
      return 'blue';
    case CourseStatus.REJECTED:
      return 'red';
    default:
      return 'default';
  }
};

// 获取状态对应的文本
const getStatusText = (status: CourseStatus) => {
  switch (status) {
    case CourseStatus.PUBLISHED:
      return '已发布';
    case CourseStatus.UNPUBLISHED:
      return '未发布';
    case CourseStatus.PENDING:
      return '待审批';
    case CourseStatus.REJECTED:
      return '已驳回';
    default:
      return '未知状态';
  }
};

// 下架课程确认
const showUnpublishConfirm = () => {
  if (!courseData.value) return;
  
  Modal.confirm({
    title: '确认下架课程',
    content: `确定要下架课程 "${courseData.value.title}" 吗？下架后该课程将不再公开展示。`,
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const success = await adminCourseStore.unpublishCourse(courseId.value);
        if (success) {
          message.success('课程已成功下架');
          // 重新获取课程数据
          const course = await adminCourseStore.fetchCourseDetail(courseId.value);
          courseData.value = course;
        } else {
          message.error('下架课程失败');
        }
      } catch (error) {
        message.error('操作失败');
        console.error(error);
      }
    },
  });
};

// 发布课程确认
const showPublishConfirm = () => {
  if (!courseData.value) return;
  
  Modal.confirm({
    title: '确认发布课程',
    content: `确定要发布课程 "${courseData.value.title}" 吗？发布后该课程将对所有用户可见。`,
    okText: '确定',
    okType: 'primary',
    cancelText: '取消',
    async onOk() {
      try {
        const success = await adminCourseStore.publishCourse(courseId.value);
        if (success) {
          message.success('课程已成功发布');
          // 重新获取课程数据
          const course = await adminCourseStore.fetchCourseDetail(courseId.value);
          courseData.value = course;
        } else {
          message.error('发布课程失败');
        }
      } catch (error) {
        message.error('操作失败');
        console.error(error);
      }
    },
  });
};
</script>

<style scoped>
.admin-page {
  width: 100%;
}

.course-header {
  margin-bottom: var(--hx-space-5);
}

.course-cover {
  width: 100%;
  height: 0;
  padding-bottom: 56.25%; /* 16:9 宽高比 */
  position: relative;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f0f0f0;
}

.course-cover img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.course-title {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.course-title h1 {
  margin: 0 16px 0 0;
  font-size: 24px;
  line-height: 32px;
}

.course-meta {
  margin-bottom: 24px;
}

.course-meta p {
  margin-bottom: 8px;
  line-height: 22px;
}

.course-actions {
  margin-top: 24px;
}

.course-description {
  margin-top: 16px;
  line-height: 1.8;
}
</style> 