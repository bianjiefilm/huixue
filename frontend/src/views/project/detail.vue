<template>
  <div class="page-container">
    <a-spin :spinning="projectLoading" tip="加载中...">
      <template v-if="projectInfo">
        <!-- 返回按钮 -->
        <div class="back-link">
          <a-button type="link" @click="goBack">
            <ArrowLeftOutlined /> 返回列表
          </a-button>
        </div>

        <!-- 项目头部 -->
        <div class="project-header">
          <div class="project-header-left">
            <h1 class="project-title">{{ projectInfo.name }}</h1>
            <div class="project-meta">
              <a-tag class="meta-tag">
                <span>行业：{{ projectInfo.industry }}</span>
              </a-tag>
              <a-tag class="meta-tag">
                <span>模式：{{ projectInfo.model_text }}</span>
              </a-tag>
              <a-tag class="meta-tag">
                <span>难度：{{ projectInfo.difficulty_text }}</span>
              </a-tag>
              <a-tag class="meta-tag">
                <TeamOutlined /> {{ projectInfo.enrollCount }}人已参与
              </a-tag>
              <a-tag class="meta-tag">
                <ClockCircleOutlined /> {{ projectInfo.created_at }}
              </a-tag>
            </div>
            <div class="project-tags">
              <a-tag v-for="(tag, index) in projectInfo.tags" :key="index" color="blue">
                {{ tag }}
              </a-tag>
              <a-tag color="#f50" v-if="projectInfo.isPopular">热门</a-tag>
              <a-tag color="#2db7f5" v-if="projectInfo.isNew">新上线</a-tag>
            </div>
          </div>
          <div class="project-header-right">
            <a-button type="primary" size="large" class="participate-btn" @click="handleParticipate">
              立即参与
            </a-button>
            <router-link to="/visual" class="visual-link">
              <a-button type="default" size="large">
                <template #icon><bar-chart-outlined /></template>
                可视化分析实训
              </a-button>
            </router-link>
          </div>
        </div>

        <!-- 项目封面 -->
        <div class="project-banner">
          <img :src="projectInfo.image" alt="项目封面" />
        </div>

        <!-- 项目详情 -->
        <a-card class="project-details">
          <a-tabs v-model:activeKey="activeTabs" type="card">
            <a-tab-pane key="1" tab="实训介绍">
              <div class="detail-section">
                <h2>实训介绍</h2>
                <p>{{ projectInfo.description }}</p>
              </div>

              <a-divider />
              
              <div class="detail-section">
                <h2>学习目标</h2>
                <ul class="goal-list">
                  <li v-for="(goal, index) in projectInfo.goals" :key="index">
                    <CheckOutlined /> {{ goal }}
                  </li>
                </ul>
              </div>

              <a-divider />
              
              <div class="detail-section">
                <h2>课程大纲</h2>
                <a-collapse v-model:activeKey="activeCollapseKey" accordion expand-icon-position="right">
                  <a-collapse-panel v-for="(chapter, index) in projectInfo.syllabus" :key="index" :header="chapter.title">
                    <ul class="syllabus-list">
                      <li v-for="(item, itemIndex) in chapter.items" :key="itemIndex">
                        {{ item }}
                      </li>
                    </ul>
                  </a-collapse-panel>
                </a-collapse>
              </div>

              <a-divider />
              
              <div class="detail-section">
                <h2>参与要求</h2>
                <ul class="requirement-list">
                  <li v-for="(req, index) in projectInfo.requirements" :key="index">
                    <InfoCircleOutlined /> {{ req }}
                  </li>
                </ul>
              </div>
            </a-tab-pane>
            
            <!-- 操作手册标签页 -->
            <a-tab-pane key="2" tab="操作手册">
              <div class="manual-container">
                <div v-if="projectInfo.isMLProject" class="ml-notice">
                  <a-alert
                    message="发现机器学习实训资源"
                    description="本项目包含机器学习专题内容，可以通过左侧菜单查看或使用专业的机器学习工作区进行实训。"
                    type="info"
                    show-icon
                  >
                    <template #icon>
                      <experiment-outlined />
                    </template>
                    <template #action>
                      <a-space>
                        <router-link to="/ml">
                          <a-button type="primary" size="small">
                            打开机器学习工作区
                          </a-button>
                        </router-link>
                        <router-link to="/ml/manual">
                          <a-button size="small">
                            查看机器学习手册
                          </a-button>
                        </router-link>
                      </a-space>
                    </template>
                  </a-alert>
                </div>
                <a-row :gutter="24">
                  <!-- 左侧导航 -->
                  <a-col :xs="24" :md="6">
                    <a-menu
                      :selectedKeys="[projectInfo.activeManualKey]"
                      class="manual-menu"
                      mode="inline"
                      @select="handleManualSelect"
                    >
                      <a-menu-item 
                        v-for="section in projectInfo.manualSections" 
                        :key="section.id"
                      >
                        {{ section.title }}
                      </a-menu-item>
                      
                      <!-- 添加机器学习专题菜单项，修改为路由链接 -->
                      <a-menu-item v-if="projectInfo.isMLProject" key="ml-manual" class="ml-menu-item">
                        <router-link to="/ml/manual">
                          <experiment-outlined /> 机器学习专题
                        </router-link>
                      </a-menu-item>
                    </a-menu>
                  </a-col>
                  
                  <!-- 右侧内容 -->
                  <a-col :xs="24" :md="18">
                    <div class="manual-content" v-if="currentManualSection">
                      <h2 class="manual-title">{{ currentManualSection.title }}</h2>
                      <div class="manual-text" v-html="currentManualSection.content"></div>
                    </div>
                    <a-empty v-else description="请选择左侧章节" />
                  </a-col>
                </a-row>
              </div>
            </a-tab-pane>
            
            <!-- 训练挑战标签页 -->
            <a-tab-pane key="3" tab="训练挑战">
              <div class="challenges-container">
                <h2 class="section-title">挑战列表</h2>
                
                <a-list 
                  class="challenge-list"
                  :data-source="projectInfo.challenges"
                  :pagination="false"
                >
                  <template #renderItem="{ item: challenge }">
                    <a-list-item>
                      <a-card class="challenge-card" :bordered="false">
                        <div class="challenge-header">
                          <h3 class="challenge-title">{{ challenge.title }}</h3>
                          <a-tag :color="getStatusColor(challenge.status)">
                            {{ getStatusText(challenge.status) }}
                          </a-tag>
                        </div>
                        <p class="challenge-desc">{{ challenge.description }}</p>
                        <div class="challenge-meta">
                          <div class="meta-section">
                            <a-tag color="blue">{{ challenge.type }}</a-tag>
                            <a-tag color="orange">{{ challenge.difficulty }}</a-tag>
                            <span class="challenge-points">
                              <TrophyOutlined /> {{ challenge.points }} 积分
                            </span>
                          </div>
                          <div class="meta-actions">
                            <a-button type="primary" @click="startChallenge(challenge)">
                              开始挑战
                            </a-button>
                          </div>
                        </div>
                      </a-card>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-tab-pane>
            
            <a-tab-pane key="4" tab="评价反馈">
              <a-empty description="暂无评价" />
            </a-tab-pane>
            <a-tab-pane key="5" tab="常见问题">
              <a-empty description="暂无常见问题" />
            </a-tab-pane>
          </a-tabs>
        </a-card>
      </template>
      <template v-else>
        <a-result
          status="404"
          title="未找到项目"
          sub-title="您请求的项目不存在或已被删除"
        >
          <template #extra>
            <a-button type="primary" @click="goBack">
              返回列表
            </a-button>
          </template>
        </a-result>
      </template>
    </a-spin>

    <!-- 机器学习训练手册抽屉 -->
    <MLManualDrawer v-model:open="showMLManual" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { 
  TeamOutlined, 
  ClockCircleOutlined, 
  CheckOutlined, 
  InfoCircleOutlined, 
  ArrowLeftOutlined,
  TrophyOutlined,
  BarChartOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import MLManualDrawer from '../../components/ml/MLManualDrawer.vue';
import { getProjectDetail } from '@/api/training';

const route = useRoute();
const router = useRouter();
const projectId = route.params.id as string;
const projectInfo=ref([]);
// 使用Pinia store
//const projectStore = useProjectStore();
const userStore = useUserStore();

// 状态变量
const activeTabs = ref<string>('1');
const activeCollapseKey = ref<string[]>(['0']); // 默认展开第一个章节
const showMLManual = ref<boolean>(false); // 控制机器学习实训手册抽屉的显示
const projectLoading=ref<boolean>(false);

// 获取当前选中的操作手册章节
const currentManualSection = computed<ManualSection | undefined>(() => {
  /*if (!projectStore.currentProject || !projectStore.currentProject.manualSections) {
    return undefined;
  }
  
  const activeKey = projectStore.activeManualKey;
  return projectStore.currentProject.manualSections.find(section => section.id === activeKey);*/
});

// 处理操作手册章节选择
const handleManualSelect = ({ key }: { key: string }) => {
  // 对于机器学习手册，不再打开抽屉，而是通过路由跳转
  if (key === 'ml-manual') {
    router.push('/ml/manual');
    return;
  }
  //projectStore.setActiveManualKey(key);
};

// 获取挑战状态颜色
const getStatusColor = (status?: string) => {
  switch (status) {
    case 'completed':
      return 'green';
    case 'in_progress':
      return 'blue';
    case 'not_started':
    default:
      return 'default';
  }
};

// 获取挑战状态文本
const getStatusText = (status?: string) => {
  switch (status) {
    case 'completed':
      return '已完成';
    case 'in_progress':
      return '进行中';
    case 'not_started':
    default:
      return '未开始';
  }
};

// 返回列表页
const goBack = () => {
  router.push('/project');
};

// 处理立即参与
const handleParticipate = () => {
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再参与项目');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    return;
  }
  message.success('已成功参与项目');
};

// 开始挑战
const startChallenge = (challenge: Challenge) => {
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再进行挑战');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    return;
  }
  message.info(`开始挑战: ${challenge.title}`);
};

// 监听路由变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    fetchProjects();
  }
});
// 获取项目列表
const fetchProjects = async () => {
	projectLoading.value=true;
  try {
    const response = await getProjectDetail(projectId);
    projectInfo.value = response;
  } catch (error) {
    message.error('获取项目列表失败，请稍后重试');
  }finally {
    projectLoading.value = false;
  }
};
// 生命周期钩子
onMounted(() => {
  // 初始化加载数据
  fetchProjects();
  
  // 初始化激活的操作手册标签
  /*if (projectStore.currentProject?.manualSections?.length) {
    projectStore.setActiveManualKey(projectStore.currentProject.manualSections[0].id);
  }*/
});
</script>

<style scoped>
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.back-link {
  margin: 20px 0;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.project-header-left {
  flex: 1;
}

.project-title {
  font-size: 24px;
  margin-bottom: 12px;
}

.project-meta {
  margin-bottom: 12px;
}

.meta-tag {
  margin-right: 8px;
}

.project-tags {
  margin-bottom: 12px;
}

.project-header-right {
  flex-shrink: 0;
  margin-left: 20px;
}

.participate-btn {
  min-width: 120px;
}

.visual-link {
  margin-left: 10px;
}

.project-banner {
  width: 100%;
  height: 300px;
  overflow: hidden;
  border-radius: 8px;
  margin-bottom: 20px;
}

.project-banner img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.project-details {
  margin-bottom: 20px;
}

.detail-section {
  margin-bottom: 20px;
}

.goal-list, .syllabus-list, .requirement-list {
  list-style: none;
  padding-left: 0;
}

.goal-list li, .requirement-list li {
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
}

.goal-list li :deep(.anticon), .requirement-list li :deep(.anticon) {
  margin-right: 8px;
  margin-top: 4px;
}

/* 操作手册样式 */
.manual-container {
  min-height: 500px;
}

.manual-menu {
  border-right: 1px solid #f0f0f0;
  height: 100%;
}

.manual-content {
  padding: 0 0 0 20px;
}

.manual-title {
  font-size: 20px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.manual-text {
  line-height: 1.8;
  font-size: 14px;
}

/* 挑战列表样式 */
.section-title {
  font-size: 20px;
  margin-bottom: 16px;
}

.challenge-card {
  width: 100%;
  margin-bottom: 16px;
}

.challenge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.challenge-title {
  margin: 0;
  font-size: 16px;
}

.challenge-desc {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 12px;
}

.challenge-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.meta-section {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.challenge-points {
  margin-left: 8px;
}

/* 响应式布局 */
@media (max-width: 768px) {
  .project-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .project-header-right {
    margin-left: 0;
    margin-top: 16px;
    width: 100%;
  }
  
  .participate-btn {
    width: 100%;
  }
  
  .manual-content {
    padding: 20px 0 0 0;
  }
}

/* 机器学习专题样式 */
.ml-notice {
  margin-bottom: 20px;
}

.ml-menu-item {
  font-weight: bold !important;
  color: #1890ff !important;
}

.ml-menu-item :deep(.anticon) {
  color: #1890ff !important;
}
</style> 