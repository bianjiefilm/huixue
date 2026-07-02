<template>
  <div class="course-page">
    <!-- 页面横幅 -->
    <div class="banner">
      <div class="responsive-container banner-content">
        <div class="banner-left">
          <h1>知者非真知也</h1>
          <h2>力行而后知之真</h2>
        </div>
        <div class="banner-right">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="想找什么？搜一搜"
            enter-button
            size="large"
            class="search-input"
            @search="handleSearch"
          />
        </div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="responsive-container content-wrapper">
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
            <a-row :gutter="[20, 20]">
              <a-col :xs="24" :sm="12" :md="8" :lg="6" :xl="4.8" v-for="course in courseResources.slice(0, 5)" :key="course.id">
                <div class="course-card" @click="goToCourseDetail(course.id)">
                  <div class="card-cover" :style="getCoverStyle(course)">
                    <img v-if="course.cover_url" :src="course.cover_url" :alt="course.title" class="cover-img" />
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
                      <span class="source">{{ course.university || '美林数据' }}-{{ course.teacher || 'Tempodata' }}</span>
                      <a-button v-if="course.is_purchased" type="link" size="small" class="go-btn">去选课</a-button>
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
            <a-row :gutter="[20, 20]">
              <a-col :xs="24" :sm="12" :md="8" :lg="6" :xl="4.8" v-for="(practice, index) in microCourses.slice(0, 10)" :key="practice.id">
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
                      <span class="card-count">关卡数 {{ practice.stage_count || practice.card_count || 1 }}</span>
                    </div>
                  </div>
                </div>
              </a-col>
            </a-row>
          </a-spin>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getCourseResources, getMicroCourses } from '@/api/course';
import { RightOutlined, ReadOutlined, ExperimentOutlined } from '@ant-design/icons-vue';

const router = useRouter();
const searchKeyword = ref('');

const loading = reactive({
  courseResources: true,
  microCourses: true
});
const courseResources = ref<any[]>([]);
const microCourses = ref<any[]>([]);

// 颜色配置
const practiceColors = [
  '#1890ff', // 蓝色
  '#52c41a', // 绿色
  '#722ed1', // 紫色
  '#13c2c2', // 青色
  '#faad14', // 黄色
  '#eb2f96', // 粉色
  '#1890ff',
  '#52c41a',
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
  // 根据方向返回不同的背景色
  const directionColors: Record<string, string> = {
    '大数据': 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
    '人工智能': 'linear-gradient(135deg, #2d1a5c 0%, #5a2d87 100%)',
    '区块链': 'linear-gradient(135deg, #1a5c3a 0%, #2d875a 100%)',
    '云计算': 'linear-gradient(135deg, #5c1a3a 0%, #872d5a 100%)',
    '数据库': 'linear-gradient(135deg, #3a5c1a 0%, #5a872d 100%)',
    '编程语言': 'linear-gradient(135deg, #1a5c5c 0%, #2d8787 100%)',
    '金融': 'linear-gradient(135deg, #5c5c1a 0%, #87872d 100%)',
  };
  return {
    background: directionColors[course.direction] || 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)'
  };
};

// 搜索处理
const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({
      path: '/course/resource',
      query: { keyword: searchKeyword.value }
    });
  }
};

// 导航方法
const goToResourceList = () => {
  router.push('/course/resource');
};

const goToPracticeList = () => {
  router.push('/course/micro');
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

    await Promise.all([
      getMaterial(),
      getMicro()
    ]);
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
/* 白色主题样式 */
.course-page {
  min-height: 100%;
  width: 100%;
  background-color: #f5f7fa;
}

.banner {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  height: 180px;
  width: 100%;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.banner::before {
  content: '';
  position: absolute;
  right: 50px;
  top: 50%;
  transform: translateY(-50%);
  width: 120px;
  height: 120px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
}

.responsive-container {
  width: 100%;
  max-width: 1400px;
  padding: 0 24px;
  margin: 0 auto;
}

.banner-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  position: relative;
  z-index: 1;
}

.banner-left h1 {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin: 0;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.banner-left h2 {
  font-size: 28px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 8px 0 0;
}

.banner-right {
  width: 360px;
}

.search-input {
  border-radius: 20px;
  overflow: hidden;
}

.search-input :deep(.ant-input) {
  border-radius: 20px 0 0 20px;
  height: 44px;
  font-size: 14px;
}

.search-input :deep(.ant-btn) {
  border-radius: 0 20px 20px 0;
  height: 44px;
  background: #fff;
  color: #1890ff;
  border: none;
}

.content-wrapper {
  padding-top: 24px;
  padding-bottom: 40px;
}

.section {
  width: 100%;
  margin-bottom: 32px;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
}

.section-icon {
  font-size: 20px;
  margin-right: 8px;
  color: #1890ff;
}

.section-more {
  font-size: 14px;
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #1890ff;
  transition: opacity 0.2s;
}

.section-more:hover {
  opacity: 0.8;
}

/* 课程资源卡片 */
.course-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e8e8e8;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
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
  padding: 16px;
}

.cover-title {
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  line-height: 1.4;
}

.teacher-info {
  position: absolute;
  bottom: 12px;
  left: 12px;
  color: #fff;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-content {
  padding: 12px;
  background: #fff;
}

.course-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: #333;
}

.course-desc {
  font-size: 12px;
  color: #999;
  margin-bottom: 8px;
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
  font-size: 12px;
}

.source {
  color: #666;
}

.go-btn {
  padding: 0;
  height: auto;
  font-size: 12px;
}

/* 元子实践卡片 */
.practice-card {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e8e8e8;
}

.practice-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.practice-cover {
  height: 120px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.practice-title-overlay {
  color: #fff;
  font-size: 16px;
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
  top: 8px;
  right: 8px;
  background: #ff4d4f;
  color: #fff;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
}

.practice-content {
  padding: 12px;
  background: #fff;
}

.practice-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  line-height: 1.4;
  height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #333;
}

.practice-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.card-count {
  color: #999;
}

/* 响应式 */
@media (max-width: 768px) {
  .responsive-container {
    padding: 0 16px;
  }

  .banner {
    height: 140px;
  }

  .banner-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .banner-left h1 {
    font-size: 24px;
  }

  .banner-left h2 {
    font-size: 20px;
  }

  .banner-right {
    width: 100%;
    margin-top: 12px;
  }
}
</style>
