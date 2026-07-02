<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible width="200" class="admin-sider">
      <div class="admin-sider-menu">
        <a-menu
          mode="inline"
          v-model:selectedKeys="selectedKeys"
          v-model:openKeys="openKeys"
          :style="{ height: '100%', borderRight: 0 }"
        >
          <a-menu-item key="dashboard">
            <template #icon>
              <DashboardOutlined />
            </template>
            <span>仪表盘</span>
            <router-link to="/admin/dashboard"></router-link>
          </a-menu-item>
          <a-sub-menu key="organization">
            <template #icon>
              <TeamOutlined />
            </template>
            <template #title>组织架构</template>
            <a-menu-item key="school-info">
              <router-link to="/admin/organization/school-info">学校信息</router-link>
            </a-menu-item>
            <a-menu-item key="department">
              <router-link to="/admin/organization/department">院系设置</router-link>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="user">
            <template #icon>
              <UserOutlined />
            </template>
            <template #title>用户管理</template>
            <a-menu-item key="teacher">
              <router-link to="/admin/user/teacher">教师管理</router-link>
            </a-menu-item>
            <a-menu-item key="student">
              <router-link to="/admin/user/student">学生管理</router-link>
            </a-menu-item>
            <a-menu-item key="role">
              <router-link to="/admin/user/role">角色授权</router-link>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="course">
            <template #icon>
              <BookOutlined />
            </template>
            <template #title>课程管理</template>
            <a-menu-item key="practice-course">
              <router-link to="/admin/course/practice">实践课程管理</router-link>
            </a-menu-item>
            <a-menu-item key="training-course">
              <router-link to="/admin/course/training">实训课程管理</router-link>
            </a-menu-item>
            <a-menu-item key="practice-approval">
              <router-link to="/admin/course/practice-approval">实践课程审批</router-link>
            </a-menu-item>
            <a-menu-item key="training-approval">
              <router-link to="/admin/course/training-approval">实训课程审批</router-link>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="resource">
            <template #icon>
              <CloudServerOutlined />
            </template>
            <template #title>教学资源管理</template>
            <a-menu-item key="environment-management">
              <router-link to="/admin/resource/environment">实践环境管理</router-link>
            </a-menu-item>
            <a-menu-item key="admin-resource-experiment">
              <router-link to="/admin/resource/experiment">实验资源管理</router-link>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="ai-generation">
            <template #icon>
              <RobotOutlined />
            </template>
            <template #title>AI智能生成</template>
            <a-menu-item key="ai-practice-generator">
              <router-link to="/admin/ai-generation/practice">课程实践生成</router-link>
            </a-menu-item>
            <a-menu-item key="ai-exam-generator">
              <router-link to="/admin/ai-generation/exam">考核试题生成</router-link>
            </a-menu-item>
            <a-menu-item key="ai-batch-generator">
              <router-link to="/admin/ai-generation/batch">自动化课程生成</router-link>
            </a-menu-item>
            <a-menu-item key="ai-training-enhancer">
              <router-link to="/admin/ai-generation/training">实训资源增强</router-link>
            </a-menu-item>
          </a-sub-menu>
          <a-sub-menu key="admin-logs">
            <template #title>
              <span>
                <bar-chart-outlined />
                <span>使用日志分析</span>
              </span>
            </template>
            <a-menu-item key="admin-logs-course">
              <router-link to="/admin/logs/course">课程统计分析</router-link>
            </a-menu-item>
            <a-menu-item key="admin-logs-practice">
              <router-link to="/admin/logs/practice">实践统计分析</router-link>
            </a-menu-item>
            <a-menu-item key="admin-logs-training">
              <router-link to="/admin/logs/training">实训统计分析</router-link>
            </a-menu-item>
            <a-menu-item key="admin-logs-teacher">
              <router-link to="/admin/logs/teacher">教师使用统计</router-link>
            </a-menu-item>
            <a-menu-item key="admin-logs-student">
              <router-link to="/admin/logs/student">学生使用统计</router-link>
            </a-menu-item>
          </a-sub-menu>
        </a-menu>
      </div>
    </a-layout-sider>
    <a-layout>
      <a-layout-content class="admin-content">
        <div class="admin-content-wrapper">
          <router-view></router-view>
        </div>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { 
  UserOutlined, 
  TeamOutlined, 
  DashboardOutlined,
  BookOutlined,
  CloudServerOutlined,
  BarChartOutlined,
  RobotOutlined
} from '@ant-design/icons-vue';

const route = useRoute();
const collapsed = ref(false);
const selectedKeys = ref<string[]>([]);
const openKeys = ref<string[]>(['organization']);

// 根据当前路由更新菜单选中状态
watch(() => route.path, (path) => {
  const pathSegments = path.split('/');
  if (pathSegments.length > 2) {
    if (pathSegments[2] === 'organization' || pathSegments[2] === 'user' || 
        pathSegments[2] === 'course' || pathSegments[2] === 'resource') {
      openKeys.value = [pathSegments[2]];
      
      if (pathSegments.length > 3) {
        let key = pathSegments[3];
        // 处理课程审批的key
        if (key === 'practice-approval' || key === 'training-approval') {
          selectedKeys.value = [key];
        } else if (key === 'practice' || key === 'training') {
          selectedKeys.value = [`${key}-course`];
        } else if (key === 'environment') {
          selectedKeys.value = ['environment-management'];
        } else if (key === 'experiment') {
          selectedKeys.value = ['admin-resource-experiment'];
        } else {
          selectedKeys.value = [key];
        }
      }
    } else if (pathSegments[2] === 'ai-generation') {
      selectedKeys.value = ['ai-generation'];
      openKeys.value = [];
    } else if (pathSegments[2] === 'logs') {
      openKeys.value = ['admin-logs'];
      if (pathSegments.length > 3) {
        selectedKeys.value = [`admin-logs-${pathSegments[3]}`];
      }
    } else {
      selectedKeys.value = [pathSegments[2]];
    }
  }
}, { immediate: true });
</script>

<style scoped>
.admin-sider {
  background: #fff;
}

.admin-sider-menu {
  height: 100%;
}

.admin-content {
  padding: 24px;
  background: #f0f2f5;
  min-height: calc(100vh - 64px);
}

.admin-content-wrapper {
  padding: 24px;
  background: #fff;
  border-radius: 4px;
}
</style>

<style>
/* 修复管理后台侧边栏收缩按钮深色问题 - 使用全局样式覆盖 */
.admin-sider .ant-layout-sider-trigger {
  background: #f0f2f5 !important;
  color: rgba(0, 0, 0, 0.65) !important;
  border-top: 1px solid #e8e8e8;
}

.admin-sider .ant-layout-sider-trigger:hover {
  background: #e6e6e6 !important;
  color: rgba(0, 0, 0, 0.85) !important;
}
</style> 