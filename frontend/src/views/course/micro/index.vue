<template>
  <div class="micro-page">
    <!-- 搜索横幅 -->
    <div class="search-banner">
      <div class="search-container">
        <h1>微型实验库</h1>
        <p>从基础概念到实际应用，快速提升您的技能水平</p>
        
        <!-- 关键词搜索栏 -->
        <div class="search-box">
          <a-input-search
            v-model:value="searchKeyword"
            placeholder="搜索课程名称"
            enter-button="搜索"
            size="large"
            allow-clear
            @search="handleSearch"
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
        <!-- 方向筛选 -->
        <div class="filter-item">
          <div class="filter-label">方向：</div>
          <div class="filter-content">
            <a-radio-group v-model:value="filters.direction" @change="handleFilterChange">
              <a-radio-button value="">全部</a-radio-button>
              <a-radio-button v-for="direction in directions" :key="direction" :value="direction">
                {{ direction }}
              </a-radio-button>
            </a-radio-group>
          </div>
        </div>
        
        <!-- 分类筛选 -->
        <div class="filter-item">
          <div class="filter-label">分类：</div>
          <div class="filter-content">
            <a-radio-group v-model:value="filters.category" @change="handleFilterChange">
              <a-radio-button value="">全部</a-radio-button>
              <a-radio-button v-for="category in filteredCategories" :key="category" :value="category">
                {{ category }}
              </a-radio-button>
            </a-radio-group>
          </div>
        </div>
        
        <!-- 难度筛选 -->
        <div class="filter-item">
          <div class="filter-label">难度：</div>
          <div class="filter-content">
            <a-radio-group v-model:value="filters.level" @change="handleFilterChange">
              <a-radio-button value="">全部</a-radio-button>
              <a-radio-button value="初级">初级</a-radio-button>
              <a-radio-button value="中级">中级</a-radio-button>
              <a-radio-button value="高级">高级</a-radio-button>
            </a-radio-group>
          </div>
        </div>
        
        <!-- 重置筛选 -->
        <div class="filter-reset">
          <a-button type="primary" ghost @click="resetFilters">
            <template #icon><reload-outlined /></template>
            重置筛选
          </a-button>
        </div>
      </div>
    </div>

    <!-- 课程列表 -->
    <div class="course-section">
      <a-spin :spinning="loading">
        <div v-if="microCourses.length > 0" class="course-list">
          <a-layout style="background: transparent;">
            <a-layout-content style="min-height: auto;">
              <a-row :gutter="[16, 16]">
                <a-col :xs="24" :sm="12" :md="8" :lg="6" :xl="6" :xxl="4" v-for="course in sortedCourses" :key="course.id">
                  <a-card class="course-card" :hoverable="true" :bodyStyle="{ padding: '0' }">
                    <a :href="`#/course/micro/${course.id}`" target="_blank" class="card-link">
                      <div class="card-cover" :style="{ backgroundImage: `url(${course.cover})` }">
                        <div class="cover-overlay"></div>
                        <div class="direction-tag">{{ course.direction }}</div>
                      </div>
                      <div class="card-content">
                        <div class="course-title" :title="course.title">{{ course.title }}</div>
                        <div class="course-info">
                          <a-tag size="small">{{ course.type || '实践' }}</a-tag>
                          <a-tag size="small" color="blue">{{ course.level }}</a-tag>
                          <a-tag size="small" color="green">{{ course.category }}</a-tag>
                        </div>
                        <div class="course-stats">
                          <span>
                            <like-outlined /> {{ course.popularity }}
                          </span>
                          <span>
                            <eye-outlined /> {{ course.views }}
                          </span>
                        </div>
                      </div>
                    </a>
                  </a-card>
                </a-col>
              </a-row>
            </a-layout-content>
          </a-layout>
        </div>
        <a-empty v-else description="没有找到符合条件的微型实验" />
      </a-spin>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, watchEffect } from 'vue';
import { storeToRefs } from 'pinia';
import { useCourseStore } from '../../../stores/course';
import { useRoute } from 'vue-router';
// 从Ant Design图标库导入
import { LikeOutlined, EyeOutlined, SearchOutlined, ReloadOutlined } from '@ant-design/icons-vue';
import type { MicroCourse } from '../../../types/course';

const route = useRoute();
const courseStore = useCourseStore();
const { microCourses, microDirections, microCategories } = storeToRefs(courseStore);
const loading = ref(true);
const searchKeyword = ref('');
const sortBy = ref('popularity');

// 筛选条件
const filters = reactive({
  direction: '',
  category: '',
  level: ''
});

// 方向和分类列表
const directions = computed(() => microDirections.value);
const categories = computed(() => microCategories.value);

// 简化computed属性，避免复杂的依赖关系导致循环
const filteredCategories = computed(() => {
  return categories.value; // 暂时简化，不依赖于动态筛选
});

const sortedCourses = computed(() => {
  return microCourses.value; // 暂时简化，直接返回原始数据
});

// 搜索处理
const handleSearch = () => {
  courseStore.setMicroFilter('keyword', searchKeyword.value);
  refreshCourses();
};

// 难度级别映射
const levelMapping = {
  '初级': 'beginner',
  '中级': 'intermediate',
  '高级': 'advanced'
};

// 筛选条件变更处理
const handleFilterChange = () => {
  courseStore.setMicroFilter('direction', filters.direction);
  courseStore.setMicroFilter('category', filters.category);
  courseStore.setMicroFilter('level', filters.level ? levelMapping[filters.level] : '');
  refreshCourses();
};

// 排序方式变更处理
const handleSortChange = () => {
  // 仅前端排序，不需要刷新数据
};

// 重置筛选条件
const resetFilters = () => {
  searchKeyword.value = '';
  filters.direction = '';
  filters.category = '';
  filters.level = '';
  courseStore.resetMicroFilters();
  refreshCourses();
};

// 刷新课程数据
const refreshCourses = async () => {
  loading.value = true;
  try {
    await courseStore.fetchMicroCourses();
  } finally {
    loading.value = false;
  }
};

// 初始化数据
onMounted(async () => {
  loading.value = true;
  try {
    await Promise.all([
      courseStore.fetchMicroDirections(),
      courseStore.fetchMicroCategories()
    ]);

    // 从URL参数初始化筛选条件
    const query = route.query;
    if (query.direction) {
      filters.direction = query.direction as string;
    }
    if (query.category) {
      filters.category = query.category as string;
    }
    if (query.level) {
      // 将英文枚举值映射回中文显示值
      const reverseMapping = {
        'beginner': '初级',
        'intermediate': '中级',
        'advanced': '高级'
      };
      filters.level = reverseMapping[query.level as string] || query.level as string;
    }
    if (query.search) {
      searchKeyword.value = query.search as string;
    }

    // 最后加载课程数据，确保筛选条件已设置
    await courseStore.fetchMicroCourses();
  } finally {
    loading.value = false;
  }
});

// 移除watchEffect监听，避免响应式循环
// 改为手动调用刷新，或者在具体操作时调用
</script>

<style scoped>
.micro-page {
  min-height: 100vh;
  background-color: var(--color-bg-1);
}

.search-banner {
  height: 200px;
  background: linear-gradient(135deg, #7b2ff7, #9e7bff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.search-banner::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: url('https://arco.design/vue/assets/pattern.4a5e5a98.svg');
  opacity: 0.2;
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
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.search-container p {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 20px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.search-box {
  width: 100%;
  max-width: 500px;
  margin: 0 auto;
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.filter-section {
  background-color: var(--color-bg-2);
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
  width: 60px;
  font-size: 14px;
  color: var(--color-text-2);
  flex-shrink: 0;
}

.filter-content {
  flex: 1;
}

.filter-reset {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.course-section {
  min-height: 400px;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.course-list {
  margin-top: 20px;
  width: 100%;
}

/* 卡片列修复 */
.course-col {
  position: relative !important;
  float: none !important;
  left: 0 !important;
  box-sizing: border-box !important;
  display: flex !important;
}

.card-link {
  display: block;
  width: 100%;
  height: 100%;
  position: relative;
  left: 0;
  transform: none;
}

.course-card {
  transition: transform 0.3s;
  height: 100%;
  width: 100%;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
  border: none;
  display: flex;
  flex-direction: column;
  position: relative;
  left: 0;
  transform: none;
}

.course-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
}

.card-cover {
  height: 160px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  width: 100%;
  left: 0;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.2), transparent);
  z-index: 1;
}

.direction-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  line-height: 1.5;
  color: #fff;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 4px;
  z-index: 1;
}

.card-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: auto;
  min-height: 120px;
  width: 100%;
  position: relative;
  left: 0;
}

.course-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
  margin-bottom: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  height: 20px;
  line-height: 20px;
}

.course-info {
  font-size: 12px;
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 22px;
  max-width: 100%;
}

.course-info :deep(.arco-tag) {
  margin-right: 0;
  padding: 0 4px;
  height: 20px;
  line-height: 18px;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  -webkit-writing-mode: horizontal-tb !important;
  -ms-writing-mode: lr-tb !important;
  direction: ltr !important;
  unicode-bidi: normal !important;
  transform: none !important;
}

.course-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: auto;
}

.course-stats span {
  display: flex;
  align-items: center;
}

.course-stats :deep(svg) {
  margin-right: 4px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .search-banner {
    height: 180px;
  }
  
  .search-container h1 {
    font-size: 24px;
  }
  
  .search-container p {
    font-size: 14px;
  }
  
  .search-box {
    max-width: 90%;
  }
  
  .filter-label {
    margin-bottom: 6px;
  }
  
  .course-list {
    margin-top: 12px;
  }
  
  .card-content {
    height: auto; /* 改为自动高度 */
    min-height: 120px;
    padding: 10px;
  }
  
  .course-title {
    margin-bottom: 8px;
  }
  
  .course-info {
    margin-bottom: 8px;
  }
  
  /* 确保筛选器在移动端可以横向滚动 */
  .filter-content {
    padding-bottom: 8px;
    margin-bottom: 4px;
  }
  
  /* 调整卡片外边距 */
  .course-card {
    margin-bottom: 4px;
  }
  
  /* 在极小屏幕上减小卡片内标签的大小 */
  .course-info :deep(.arco-tag) {
    font-size: 10px;
    height: 18px;
    line-height: 16px;
    max-width: 70px;
  }
  
  /* 修复标签折叠问题 */
  .direction-tag, .course-title, .course-info {
    text-orientation: mixed !important;
    writing-mode: horizontal-tb !important;
    -webkit-writing-mode: horizontal-tb !important;
    transform: none !important;
  }
}
</style> 