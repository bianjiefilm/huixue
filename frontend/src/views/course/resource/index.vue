<template>
  <div class="resource-page">
    <!-- 搜索横幅 -->
    <div class="search-banner">
      <div class="search-container">
        <h1>课程资源库</h1>
        <p>探索丰富的教学资源，提升您的学习效果</p>

        <!-- 关键词搜索栏 -->
        <div class="search-box">
          <a-input-search
            v-model:value="keyword"
            placeholder="搜索课程名称、教师、学校、描述"
            enter-button="搜索"
            size="large"
            allow-clear
            @search="handleSearch"
            @pressEnter="handleSearch"
          >
            <template #prefix>
              <search-outlined />
            </template>
          </a-input-search>
        </div>
      </div>
    </div>

    <!-- 筛选条件部分 -->
    <div class="filter-section">
      <div class="filter-container">
        <!-- 课程方向筛选 -->
        <div class="filter-item">
          <div class="filter-label">课程方向：</div>
          <div class="filter-content">
            <a-radio-group v-model:value="selectedDirection" @change="handleDirectionChange">
              <a-radio-button value="">全部</a-radio-button>
              <a-radio-button v-for="dir in directions" :key="dir" :value="dir">
                {{ dir }}
              </a-radio-button>
            </a-radio-group>
          </div>
        </div>

        <!-- 重置筛选 -->
        <div class="filter-reset" v-if="selectedDirection || keyword">
          <a-button type="primary" ghost @click="clearFilters">
            <template #icon><reload-outlined /></template>
            重置筛选
          </a-button>
        </div>
      </div>
    </div>

    <!-- 课程列表 -->
    <div class="course-section">
      <a-spin :spinning="loading">
        <div v-if="filteredCourses.length > 0" class="course-list">
          <a-row :gutter="[16, 16]">
            <a-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6" :xxl="4" v-for="course in filteredCourses" :key="course.id">
              <a-card class="course-card" :hoverable="true" :bodyStyle="{ padding: '0' }">
                <a :href="`#/course/resource/${course.id}`" target="_blank" class="card-link">
                  <div class="card-cover" :style="getCoverStyle(course)">
                    <div class="cover-overlay"></div>
                    <div class="cover-text">{{ course.direction || course.title }}</div>
                    <div class="university-tag">{{ course.source || '知名高校' }}</div>
                  </div>
                  <div class="card-content">
                    <div class="course-title" :title="course.title">{{ course.title }}</div>
                    <div class="course-info">
                      <a-tag color="blue">{{ course.direction || '通用' }}</a-tag>
                      <span class="university">{{ course.source || '知名高校' }}</span>
                    </div>
                  </div>
                </a>
              </a-card>
            </a-col>
          </a-row>
        </div>
        <a-empty v-else description="没有找到符合条件的课程资源" />
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import { materialList } from '@/api/cmaterial';

const route = useRoute();

// 状态
const loading = ref(true);
const keyword = ref('');
const selectedDirection = ref('');
const allCourses = ref<any[]>([]);

// 方向列表（从数据中提取）
const directions = computed(() => {
  const dirSet = new Set<string>();
  allCourses.value.forEach(course => {
    if (course.direction) {
      dirSet.add(course.direction);
    }
  });
  return Array.from(dirSet);
});

// 颜色配置
const directionColors: Record<string, string> = {
  '大数据': 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)',
  '人工智能': 'linear-gradient(135deg, #2d1a5c 0%, #5a2d87 100%)',
  '区块链': 'linear-gradient(135deg, #1a5c3a 0%, #2d875a 100%)',
  '云计算': 'linear-gradient(135deg, #5c1a3a 0%, #872d5a 100%)',
  '数据库': 'linear-gradient(135deg, #3a5c1a 0%, #5a872d 100%)',
  '编程语言': 'linear-gradient(135deg, #1a5c5c 0%, #2d8787 100%)',
  '金融': 'linear-gradient(135deg, #5c5c1a 0%, #87872d 100%)',
  '互联网': 'linear-gradient(135deg, #5c1a5c 0%, #872d87 100%)',
};

const getCoverStyle = (course: any) => {
  if (course.cover_url) {
    return {
      backgroundImage: `url(${course.cover_url})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center'
    };
  }
  return {
    background: directionColors[course.direction] || 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)'
  };
};

// 筛选后的课程列表（计算属性）
const filteredCourses = computed(() => {
  let result = allCourses.value;

  // 按方向筛选
  if (selectedDirection.value) {
    result = result.filter(course => course.direction === selectedDirection.value);
  }

  // 按关键词筛选（本地搜索作为补充）
  if (keyword.value.trim()) {
    const kw = keyword.value.trim().toLowerCase();
    result = result.filter(course =>
      (course.title && course.title.toLowerCase().includes(kw)) ||
      (course.description && course.description.toLowerCase().includes(kw)) ||
      (course.direction && course.direction.toLowerCase().includes(kw))
    );
  }

  return result;
});

// 获取课程数据
const fetchCourses = async (searchKeyword?: string) => {
  loading.value = true;
  try {
    const params: any = { limit: 100, page: 1 };
    if (searchKeyword && searchKeyword.trim()) {
      params.search = searchKeyword.trim();
    }
    const res = await materialList(params);
    console.log('API响应:', res);
    allCourses.value = res?.data?.list || res?.list || [];
    console.log('课程数量:', allCourses.value.length);
  } catch (err) {
    console.error('获取课程失败:', err);
    allCourses.value = [];
  } finally {
    loading.value = false;
  }
};

// 处理方向筛选变化
const handleDirectionChange = () => {
  console.log('方向筛选:', selectedDirection.value);
  // 使用计算属性自动过滤，无需额外操作
};

// 处理搜索
const handleSearch = async () => {
  console.log('搜索关键词:', keyword.value);
  // 如果关键词不为空，调用后端搜索API
  if (keyword.value.trim()) {
    await fetchCourses(keyword.value);
  } else {
    await fetchCourses();
  }
};

// 清除筛选条件
const clearFilters = async () => {
  keyword.value = '';
  selectedDirection.value = '';
  await fetchCourses();
};

// 初始化
onMounted(async () => {
  // 检查URL参数中是否有搜索关键词
  if (route.query.keyword) {
    keyword.value = route.query.keyword as string;
  }
  await fetchCourses(keyword.value || undefined);
});
</script>

<style scoped>
.resource-page {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.search-banner {
  height: 200px;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.search-container {
  position: relative;
  z-index: 1;
  text-align: center;
  width: 100%;
  max-width: 1200px;
  padding: 0 20px;
}

.search-container h1 {
  font-size: 32px;
  font-weight: 500;
  margin-bottom: 10px;
  color: #fff;
}

.search-container p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 20px;
  color: #fff;
}

.search-box {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
}

/* 筛选部分样式 */
.filter-section {
  background-color: #fff;
  padding: 16px 0;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.filter-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.filter-item {
  display: flex;
  margin-bottom: 16px;
  align-items: center;
}

.filter-item:last-child {
  margin-bottom: 0;
}

.filter-label {
  width: 80px;
  font-size: 14px;
  color: #333;
  flex-shrink: 0;
  font-weight: 500;
}

.filter-content {
  flex: 1;
  overflow-x: auto;
}

.filter-reset {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.course-section {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.course-list {
  margin-bottom: 40px;
}

.course-card {
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.3s;
  border: 1px solid #e8e8e8;
}

.course-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.card-link {
  display: block;
  height: 100%;
  text-decoration: none;
  color: inherit;
}

.card-cover {
  height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  color: white;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.1);
}

.cover-text {
  position: relative;
  z-index: 1;
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  padding: 0 16px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.university-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 2px 8px;
  background-color: rgba(0, 0, 0, 0.5);
  border-radius: 12px;
  font-size: 12px;
  z-index: 2;
}

.card-content {
  padding: 16px;
  background: #fff;
}

.course-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  line-height: 1.4;
  height: 42px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  color: #333;
}

.course-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.university {
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .search-container h1 {
    font-size: 24px;
  }

  .search-container p {
    font-size: 14px;
  }

  .filter-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-label {
    margin-bottom: 8px;
  }

  .filter-content {
    width: 100%;
  }
}
</style>
