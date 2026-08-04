<template>
  <PageShell max-width="wide" class="course-page">
    <PageHeaderBar title="课程实践" :subtitle="headerSubtitle">
      <template #actions>
        <a-button type="primary" @click="goToMyPractices">
          <template #icon><PlusOutlined /></template>
          我创建的实践
        </a-button>
      </template>
    </PageHeaderBar>

    <Stack direction="horizontal" :gap="3" class="course-filters">
      <a-input-search
        v-model:value="searchKeyword"
        placeholder="想找什么？搜一搜"
        enter-button
        allow-clear
        class="search-input"
        @search="handleSearch"
      />
    </Stack>

    <!-- 课程资源部分 -->
    <div class="section course-section">
      <div class="section-header">
        <div class="section-title">
          <ReadOutlined class="section-icon" />
          课程资源
        </div>
        <div class="section-more" @click="goToResourceList">
          查看更多 <RightOutlined />
        </div>
      </div>
      <div class="course-list">
        <a-spin :spinning="loading.courseResources">
          <EmptyStateBlock
            v-if="!loading.courseResources && courseResources.length === 0"
            description="暂无课程资源"
          />
          <a-row v-else :gutter="[16, 16]">
            <a-col
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
              :xl="4"
              v-for="course in courseResources.slice(0, 5)"
              :key="course.id"
            >
              <div class="course-card" @click="goToCourseDetail(course.id)">
                <div class="card-cover" :style="getCoverStyle(course)">
                  <img
                    v-if="course.cover_url"
                    :src="course.cover_url"
                    :alt="course.title"
                    class="cover-img"
                  />
                  <div v-else class="cover-placeholder">
                    <div class="cover-title">{{ course.direction || course.title }}</div>
                  </div>
                  <div v-if="course.teacher" class="teacher-info">
                    <span>{{ course.university || '知名高校' }}</span>
                    <span>{{ course.teacher }}</span>
                  </div>
                </div>
                <div class="card-content">
                  <div class="course-title">{{ course.title }}</div>
                  <div class="course-desc">{{ course.description || '暂无描述' }}</div>
                  <div class="course-meta">
                    <span class="source"
                      >{{ course.university || '美林数据' }}-{{ course.teacher || 'Tempodata' }}</span
                    >
                    <a-button v-if="course.is_purchased" type="link" size="small" class="go-btn"
                      >去选课</a-button
                    >
                  </div>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-spin>
      </div>
    </div>

    <!-- 元子实践部分 -->
    <div class="section practice-section">
      <div class="section-header">
        <div class="section-title">
          <ExperimentOutlined class="section-icon" />
          元子实践
        </div>
        <div class="section-more" @click="goToPracticeList">
          查看更多 <RightOutlined />
        </div>
      </div>
      <div class="course-list">
        <a-spin :spinning="loading.microCourses">
          <EmptyStateBlock
            v-if="!loading.microCourses && microCourses.length === 0"
            description="暂无元子实践"
          />
          <a-row v-else :gutter="[16, 16]">
            <a-col
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
              :xl="4"
              v-for="(practice, index) in microCourses.slice(0, 10)"
              :key="practice.id"
            >
              <div class="practice-card" @click="goToPracticeDetail(practice.id)">
                <div class="practice-cover" :style="{ backgroundColor: getPracticeColor(index) }">
                  <div class="practice-title-overlay">{{ practice.title }}</div>
                  <div v-if="practice.status === 'learning'" class="learning-badge">正在上课</div>
                </div>
                <div class="practice-content">
                  <div class="practice-title">
                    <a-tag v-if="practice.is_video" color="purple">VUE</a-tag>
                    {{ practice.title }}
                  </div>
                  <div class="practice-meta">
                    <a-tag size="small">{{ practice.level || '初级' }}</a-tag>
                    <span class="card-count"
                      >关卡数 {{ practice.stage_count || practice.card_count || 1 }}</span
                    >
                  </div>
                </div>
              </div>
            </a-col>
          </a-row>
        </a-spin>
      </div>
    </div>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getCourseResources, getMicroCourses } from '@/api/course';
import {
  RightOutlined,
  ReadOutlined,
  ExperimentOutlined,
  PlusOutlined
} from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import Stack from '@/components/common/Stack.vue';

const router = useRouter();
const searchKeyword = ref('');

const loading = reactive({
  courseResources: true,
  microCourses: true
});
const courseResources = ref<any[]>([]);
const microCourses = ref<any[]>([]);

const headerSubtitle = computed(() => {
  const resourceCount = courseResources.value.length;
  const practiceCount = microCourses.value.length;
  return `${resourceCount} 门课程资源 · ${practiceCount} 个元子实践`;
});

// 颜色配置
const practiceColors = [
  'var(--hx-color-primary)',
  'var(--hx-color-success)',
  '#722ed1',
  '#13c2c2',
  'var(--hx-color-warning)',
  '#eb2f96',
  'var(--hx-color-primary)',
  'var(--hx-color-success)',
  '#722ed1',
  '#13c2c2'
];

const getPracticeColor = (index: number) => {
  return practiceColors[index % practiceColors.length];
};

const getCoverStyle = (course: any) => {
  if (course.cover_url) {
    return {};
  }
  const directionColors: Record<string, string> = {
    大数据: 'linear-gradient(135deg, var(--hx-color-primary) 0%, #40a9ff 100%)',
    人工智能: 'linear-gradient(135deg, #2d1a5c 0%, #5a2d87 100%)',
    区块链: 'linear-gradient(135deg, #1a5c3a 0%, #2d875a 100%)',
    云计算: 'linear-gradient(135deg, #5c1a3a 0%, #872d5a 100%)',
    数据库: 'linear-gradient(135deg, #3a5c1a 0%, #5a872d 100%)',
    编程语言: 'linear-gradient(135deg, #1a5c5c 0%, #2d8787 100%)',
    金融: 'linear-gradient(135deg, #5c5c1a 0%, #87872d 100%)'
  };
  return {
    background:
      directionColors[course.direction] ||
      'linear-gradient(135deg, var(--hx-color-primary) 0%, #40a9ff 100%)'
  };
};

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/course/resource',
      query: { keyword: searchKeyword.value }
    });
  }
};

const goToResourceList = () => {
  router.push('/course/resource');
};

const goToPracticeList = () => {
  router.push('/course/micro');
};

const goToMyPractices = () => {
  router.push('/course/practice/my');
};

const goToCourseDetail = (id: number) => {
  router.push(`/course/resource/${id}`);
};

const goToPracticeDetail = (id: number) => {
  router.push(`/course/micro/${id}`);
};

onMounted(async () => {
  try {
    loading.courseResources = true;
    loading.microCourses = true;

    await Promise.all([getMaterial(), getMicro()]);
  } finally {
    loading.courseResources = false;
    loading.microCourses = false;
  }
});

const getMaterial = async () => {
  try {
    const courses = await getCourseResources();
    courseResources.value = courses;
  } catch (err) {
    console.error('获取课程资源失败:', err);
  }
};

const getMicro = async () => {
  try {
    const practices = await getMicroCourses();
    microCourses.value = practices;
  } catch (err) {
    console.error('获取元子实践失败:', err);
  }
};
</script>

<style scoped>
.course-filters {
  margin-bottom: var(--hx-space-5);
}

.search-input {
  width: min(360px, 100%);
}

.section {
  width: 100%;
  margin-bottom: var(--hx-space-5);
  background: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
  padding: var(--hx-space-5);
  border: 1px solid var(--hx-color-border-muted);
  box-shadow: var(--hx-shadow-sm);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--hx-space-4);
  padding-bottom: var(--hx-space-3);
  border-bottom: 1px solid var(--hx-color-border-muted);
}

.section-title {
  font-size: var(--hx-font-size-md);
  font-weight: 600;
  color: var(--hx-color-text-primary);
  display: flex;
  align-items: center;
}

.section-icon {
  font-size: var(--hx-font-size-lg);
  margin-right: var(--hx-space-2);
  color: var(--hx-color-primary);
}

.section-more {
  font-size: var(--hx-font-size-base);
  display: flex;
  align-items: center;
  cursor: pointer;
  color: var(--hx-color-primary);
  transition: opacity var(--hx-transition-fast);
}

.section-more:hover {
  opacity: 0.8;
}

.course-card {
  background: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--hx-transition-normal);
  border: 1px solid var(--hx-color-border-muted);
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--hx-shadow-md);
  border-color: var(--hx-color-primary);
}

.card-cover {
  height: 160px;
  position: relative;
  overflow: hidden;
}

.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: #fff;
  padding: var(--hx-space-4);
}

.cover-title {
  font-size: var(--hx-font-size-lg);
  font-weight: 600;
  text-align: center;
  line-height: 1.4;
}

.teacher-info {
  position: absolute;
  bottom: var(--hx-space-3);
  left: var(--hx-space-3);
  color: #fff;
  font-size: var(--hx-font-size-xs);
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-1);
}

.card-content {
  padding: var(--hx-space-3);
  background: var(--hx-color-bg-container);
}

.course-title {
  font-size: var(--hx-font-size-base);
  font-weight: 600;
  margin-bottom: var(--hx-space-2);
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: var(--hx-color-text-primary);
}

.course-desc {
  font-size: var(--hx-font-size-xs);
  color: var(--hx-color-text-tertiary);
  margin-bottom: var(--hx-space-2);
  line-height: 1.5;
  height: 36px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.course-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--hx-font-size-xs);
}

.source {
  color: var(--hx-color-text-secondary);
}

.go-btn {
  padding: 0;
  height: auto;
  font-size: var(--hx-font-size-xs);
}

.practice-card {
  background: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-sm);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--hx-transition-normal);
  border: 1px solid var(--hx-color-border-muted);
}

.practice-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--hx-shadow-md);
  border-color: var(--hx-color-primary);
}

.practice-cover {
  height: 120px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--hx-space-4);
}

.practice-title-overlay {
  color: #fff;
  font-size: var(--hx-font-size-md);
  font-weight: 600;
  text-align: center;
  line-height: 1.4;
  max-height: 88px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.learning-badge {
  position: absolute;
  top: var(--hx-space-2);
  right: var(--hx-space-2);
  background: var(--hx-color-error);
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: var(--hx-radius-xs, 4px);
}

.practice-content {
  padding: var(--hx-space-3);
  background: var(--hx-color-bg-container);
}

.practice-title {
  font-size: var(--hx-font-size-base);
  font-weight: 500;
  margin-bottom: var(--hx-space-2);
  line-height: 1.4;
  height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--hx-color-text-primary);
}

.practice-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: var(--hx-font-size-xs);
}

.card-count {
  color: var(--hx-color-text-tertiary);
}
</style>
