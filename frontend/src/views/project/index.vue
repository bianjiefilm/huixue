<template>
  <div class="page-container">
    <!-- 页面标题 -->
    <div class="page-header-title">
      <h1>项目实训</h1>
      <p class="page-description">
        以实际工作场景为背景的项目实训，帮助学生掌握实际技能并了解行业需求
      </p>
    </div>

    <!-- 顶部横幅 -->
    <div class="page-banner">
      <img src="https://picsum.photos/1200/300?random=banner" alt="项目实训">
    </div>

    <!-- 实训类型推荐 -->
    <div class="training-recommendation">
      <a-row :gutter="24">
        <a-col :span="8">
          <div class="training-card">
            <h3>JupyterLite 实训</h3>
            <p>使用 JupyterLite 进行交互式编程实训，支持在线编码和运行</p>
            <router-link to="/project/jupyter">
              <a-button type="primary">进入 JupyterLite</a-button>
            </router-link>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="training-card">
            <h3>可视化分析实训</h3>
            <p>使用拖拽式可视化工具进行数据分析实训</p>
            <router-link to="/visual">
              <a-button type="primary">进入可视化分析</a-button>
            </router-link>
          </div>
        </a-col>
        <a-col :span="8">
          <div class="training-card">
            <h3>机器学习实训</h3>
            <p>使用拖拽式机器学习工具进行模型训练实训</p>
            <router-link to="/ml">
              <a-button type="primary">进入机器学习</a-button>
            </router-link>
          </div>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section">
      <!-- 行业筛选 -->
      <div class="filter-row">
        <div class="filter-title">行业：</div>
        <div class="filter-content">
          <a-radio-group v-model:value="filters.industry" button-style="solid">
            <a-radio-button v-for="item in industries" :value="item.value">
              {{ item.name }}
            </a-radio-button>
          </a-radio-group>
        </div>
      </div>

      <!-- 模式筛选 -->
      <div class="filter-row">
        <div class="filter-title">模式：</div>
        <div class="filter-content">
          <a-radio-group v-model:value="filters.trainingType" button-style="solid">
            <a-radio-button value="all">全部</a-radio-button>
            <a-radio-button value="dragdrop">拖拽式</a-radio-button>
            <a-radio-button value="coding">编码式</a-radio-button>
          </a-radio-group>
        </div>
      </div>

      <!-- 难度筛选 -->
      <div class="filter-row">
        <div class="filter-title">难度：</div>
        <div class="filter-content">
          <a-radio-group v-model:value="filters.difficulty" button-style="solid">
            <a-radio-button v-for="item in difficultyLevels" :value="item.value">
              {{ item.name }}
            </a-radio-button>
          </a-radio-group>
        </div>
      </div>
    </div>

    <!-- 项目列表 -->
    <a-spin :spinning="loading" tip="加载中...">
      <div class="project-list">
        <a-row :gutter="[24, 24]">
          <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="project in filteredProjects" :key="project.id">
            <router-link :to="`/project/${project.id}`" target="_blank">
              <a-card class="project-card" hoverable>
                <div class="card-badges">
                  <a-tag color="#f50" v-if="project.isPopular">热门</a-tag>
                  <a-tag color="#2db7f5" v-if="project.isNew">新上线</a-tag>
                </div>
                <img :src="project.image" class="card-image" alt="项目封面" />
                <a-card-meta :title="project.title">
                  <template #description>
                    <div class="card-description">
                      <p class="card-desc-text">{{ project.description }}</p>
                      <div class="card-info">
                        <div class="card-tags">
                          <a-tag v-for="(tag, index) in project.tags" :key="index">
                            {{ tag }}
                          </a-tag>
                        </div>
                        <div class="card-meta-info">
                          <div class="card-meta-item">
                            <span>行业：{{ project.industry }}</span>
                          </div>
                          <div class="card-meta-item">
                            <span>类型：{{ project.model_text }}</span>
                          </div>
                          <div class="card-meta-item">
                            <span>难度：{{ project.difficulty_text }}</span>
                          </div>
                          <div class="card-meta-item">
                            <TeamOutlined /> {{ project.enrollCount }}人已参与
                          </div>
                          <div class="card-meta-item">
                            <ClockCircleOutlined /> {{ project.created_at }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </template>
                </a-card-meta>
              </a-card>
            </router-link>
          </a-col>
        </a-row>
      </div>
    </a-spin>

    <!-- 分页控件 -->
    <div class="pagination-container">
      <a-pagination
        v-model:current="currentPage"
        :total="totalProjects"
        :pageSize="pageSize"
        show-quick-jumper
        show-size-changer
        @change="handlePageChange"
        @showSizeChange="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, computed } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { TeamOutlined, ClockCircleOutlined } from '@ant-design/icons-vue';
import { getTrainingLibrary } from '../../api/training';
import { useUserStore } from '../../stores/user';

const router = useRouter();
const userStore = useUserStore();

// 状态变量
const loading = ref(true);
const projects = ref([]);
const industries =  [{"value":"all","name":"全部"},{"value":"能源","name":"能源"},{"value":"制造","name":"制造"},{"value":"金融","name":"金融"},{"value":"零售","name":"零售"},{"value":"电商","name":"电商"},{"value":"政务","name":"政务"},{"value":"交通","name":"交通"},{"value":"环保","name":"环保"},{"value":"医疗","name":"医疗"},{"value":"农业","name":"农业"},{"value":"其他","name":"其他"}];
const trainingTypes = [{"value":"all","name":"全部"},{"value":"dragdrop","name":"拖拽式"},{"value":"coding","name":"编码式"}];
const difficultyLevels = [{"value":"all","name":"全部"},{"value":"easy","name":"初级"},{"value":"medium","name":"中级"},{"value":"hard","name":"高级"}];
const totalProjects = ref(0);
const currentPage = ref(1);
const pageSize = ref(12);

// 筛选条件
const filters = reactive({
  industry: 'all',
  trainingType: 'all',
  difficulty: 'all',
});

// 直接使用API返回的项目列表（已筛选）
const filteredProjects = computed(() => {
  console.log('[FRONTEND] filteredProjects computed called, projects.value:', projects.value);
  const result = projects.value;
  console.log('[FRONTEND] filteredProjects returning:', result);
  return result;
});

// 监听筛选条件变化，重新获取数据
watch(filters, () => {
  fetchProjects();
});

// 获取项目列表
const fetchProjects = async () => {
  try {
    console.log('[FRONTEND] fetchProjects called');
    loading.value = true;

    // 转换筛选条件为API格式
    const apiParams: any = {
      training_type: filters.trainingType === 'all' ? undefined : (filters.trainingType === 'dragdrop' ? 'DRAG_DROP' : 'CODING'),
      difficulty: filters.difficulty === 'all' ? undefined : (filters.difficulty === 'beginner' ? 'beginner' : filters.difficulty === 'medium' ? 'intermediate' : filters.difficulty === 'hard' ? 'advanced' : undefined),
      page: currentPage.value,
      page_size: pageSize.value
    };

    // 如果选择了具体行业，添加到API参数（假设后端支持行业筛选）
    if (filters.industry !== 'all') {
      apiParams.keyword = filters.industry; // 暂时使用keyword参数进行行业筛选
    }

    console.log('[FRONTEND] fetchProjects apiParams:', apiParams);
    const response = await getTrainingLibrary(apiParams);
    console.log('[FRONTEND] fetchProjects response:', response);

    if (response && response.list) {
      console.log('[FRONTEND] fetchProjects response.list:', response.list);
      console.log('[FRONTEND] Setting projects.value with', response.list.length, 'items');
      projects.value = response.list.map(item => {
        console.log('[FRONTEND] Processing item:', item.title);
        return {
          id: item.id,
        title: item.title,
        description: item.intro || (item.title + ' - ' + (['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(item.training_type) ? '拖拽式' : '编码式') + '实训'),
        image: 'https://picsum.photos/300/200?random=' + item.id,
        industry: item.industry || '通用', // 使用API返回的industry字段
        trainingType: {
          id: ['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(item.training_type) ? 'dragdrop' : 'coding',
          name: ['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(item.training_type) ? '拖拽式' : '编码式'
        },
        difficulty: {
          id: item.difficulty === 'beginner' ? 'easy' : item.difficulty === 'intermediate' ? 'medium' : 'hard',
          name: item.difficulty === 'beginner' ? '初级' : item.difficulty === 'intermediate' ? '中级' : '高级'
        },
        model_text: ['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(item.training_type) ? '拖拽式' : '编码式',
        difficulty_text: item.difficulty === 'beginner' ? '初级' : item.difficulty === 'intermediate' ? '中级' : '高级',
        tags: item.tags || [],
        enrollCount: item.participant_count || 0,
        created_at: new Date(item.created_at).toLocaleDateString(),
        isPopular: (item.participant_count || 0) > 50,
        isNew: item.created_at && (Date.now() - new Date(item.created_at).getTime()) < 7 * 24 * 3600 * 1000
        };
      });
      totalProjects.value = response.total || 0;
      console.log('[FRONTEND] fetchProjects totalProjects:', totalProjects.value);
      console.log('[FRONTEND] projects.value after setting:', projects.value);
    } else {
      console.log('[FRONTEND] No data in response, setting projects to empty array');
      console.log('[FRONTEND] Response structure:', response);
      projects.value = [];
      totalProjects.value = 0;
    }
  } catch (error) {
    console.error('获取项目列表失败:', error);
    message.error('获取项目列表失败，请稍后重试');
    projects.value = [];
    totalProjects.value = 0;
  } finally {
    loading.value = false;
  }
};

// 检查登录状态
const checkLoginStatus = () => {
  if (userStore.isLoggedIn) {
    console.log('用户已登录:', userStore.userInfo.username);
  } else {
    console.log('用户未登录');
  }
};

// 处理页码变化
const handlePageChange = (page: number) => {
  currentPage.value = page;
  fetchProjects();
};

// 处理每页数量变化
const handleSizeChange = (current: number, size: number) => {
  currentPage.value = current;
  pageSize.value = size;
  currentPage.value = 1; // 重置到第一页
  fetchProjects();
};

// 生命周期钩子
onMounted(() => {
  console.log('[FRONTEND] Component mounted');
  checkLoginStatus();
  console.log('[FRONTEND] About to call fetchProjects');
  fetchProjects();
  console.log('[FRONTEND] fetchProjects called from onMounted');
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  background-color: #fff;
  border-radius: 4px;
}

.page-header-title {
  margin-bottom: 24px;
}

.page-header-title h1 {
  font-size: 24px;
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.page-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
  margin-bottom: 0;
}

.page-banner {
  margin-bottom: 24px;
  border-radius: 4px;
  overflow: hidden;
}

.page-banner img {
  width: 100%;
  display: block;
}

.training-recommendation {
  margin-bottom: 24px;
}

.training-card {
  background: #fff;
  padding: 24px;
  border-radius: 4px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  text-align: center;
}

.training-card h3 {
  font-size: 18px;
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.85);
}

.training-card p {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 16px;
}

.filter-section {
  background-color: #fafafa;
  padding: 16px;
  margin-bottom: 24px;
  border-radius: 4px;
}

.filter-row {
  display: flex;
  margin-bottom: 16px;
  align-items: center;
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-title {
  width: 80px;
  flex-shrink: 0;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

.filter-content {
  flex: 1;
}

.project-list {
  margin-bottom: 24px;
}

.project-card {
  height: 100%;
  transition: all 0.3s;
  position: relative;
}

.card-badges {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.card-image {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 4px 4px 0 0;
}

.card-description {
  margin-top: 10px;
}

.card-desc-text {
  height: 40px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  margin-bottom: 10px;
  color: rgba(0, 0, 0, 0.65);
}

.card-info {
  margin-top: 10px;
}

.card-tags {
  margin-bottom: 10px;
}

.card-meta-info {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.card-meta-item {
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.card-meta-item .anticon {
  margin-right: 4px;
}

.pagination-container {
  margin-top: 24px;
  text-align: center;
}
</style> 
