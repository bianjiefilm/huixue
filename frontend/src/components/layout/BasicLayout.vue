<template>
  <a-layout class="global-layout" :class="{ 'global-layout--workspace': hideFooter }">
    <!-- 顶部导航 -->
    <a-layout-header class="page-header">
      <div class="header-content">
        <div class="logo">
          <router-link to="/" class="logo-link">
            <img src="@/assets/logo.svg" alt="Logo" />
            <span>慧学</span>
          </router-link>
        </div>
        <div class="nav">
          <nav class="top-nav-menu" aria-label="主导航">
            <!-- 我的课堂：学生和教师可见，管理员不可见 -->
            <button
              type="button"
              class="top-nav-item"
              :class="{ active: activeKey === 'classroom' }"
              v-if="isStudentOrTeacher"
              @click="navigateTop('/classroom')"
            >
              我的课堂
            </button>
            <!-- 课程实践：仅教师可见 -->
            <button
              type="button"
              class="top-nav-item"
              :class="{ active: activeKey === 'course' }"
              v-if="isTeacher"
              @click="navigateTop('/course')"
            >
              课程实践
            </button>
            <!-- 项目实训：仅教师可见 -->
            <button
              type="button"
              class="top-nav-item"
              :class="{ active: activeKey === 'project' }"
              v-if="isTeacher"
              @click="navigateTop('/project')"
            >
              项目实训
            </button>
            <!-- 系统管理：仅管理员可见 -->
            <button
              type="button"
              class="top-nav-item admin-menu-item"
              :class="{ active: activeKey === 'admin' }"
              v-if="userStore.isAdmin"
              @click="navigateTop('/admin')"
            >
              <SettingOutlined />
              系统管理
            </button>
          </nav>
        </div>
        <div class="user-info">
          <!-- 创建按钮 -->
		  <!--
          <a-dropdown class="create-dropdown" :trigger="['hover']" v-if="userStore.isLoggedIn">
            <a-button type="text" class="create-btn" shape="circle">
              <template #icon><PlusOutlined style="font-size: 20px" /></template>
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item key="create-practice">
                  <router-link to="/course/practice/create">新建实践</router-link>
                </a-menu-item>
                <a-menu-item key="create-training">
                  <router-link to="/project/create">新建实训</router-link>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>-->
          
          <!-- 调试用的身份切换按钮 -->
		  <!--
          <a-dropdown v-if="userStore.isLoggedIn" class="role-switch-dropdown">
            <a-button>
              {{ getCurrentRoleText() }}
              <down-outlined />
            </a-button>
            <template #overlay>
              <a-menu @click="handleRoleSwitch">
                <a-menu-item key="student">
                  <TeamOutlined />
                  学生身份
                </a-menu-item>
                <a-menu-item key="teacher">
                  <UserOutlined />
                  教师身份
                </a-menu-item>
                <a-menu-item key="admin">
                  <CrownOutlined />
                  管理员身份
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>-->
          
          <!-- 未登录状态 -->
          <a-button v-if="!userStore.isLoggedIn" type="primary" @click="showLoginModal">
            登录
          </a-button>
          
          <!-- 已登录状态 -->
          <a-dropdown v-else>
            <div class="user-dropdown-link">
              <a-avatar 
                :src="userStore.userInfo.avatar"
                :size="36"
                shape="circle"
                :alt="userStore.userInfo.username"
                class="user-avatar"
              >
                <template #icon v-if="!userStore.userInfo.avatar"><UserOutlined /></template>
              </a-avatar>
              <span class="username">{{ userStore.userInfo.realname }}</span>
			  <a-tag color="blue">{{getCurrentRoleText()}}</a-tag>
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">
                  <router-link to="/profile">
                    <UserOutlined />
                    个人中心
                  </router-link>
                </a-menu-item>
                <!-- 我创建的实践：仅教师可见 -->
                <a-menu-item key="my-practices" v-if="isTeacher">
                  <router-link to="/course/practice/my">
                    <AppstoreOutlined />
                    我创建的实践
                  </router-link>
                </a-menu-item>
                <!-- 我创建的实训：仅教师可见 -->
                <a-menu-item key="my-trainings" v-if="isTeacher">
                  <router-link to="/course/training/my">
                    <ExperimentOutlined />
                    我创建的实训
                  </router-link>
                </a-menu-item>
                <a-menu-item key="settings">
                  <SettingOutlined />
                  设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">
                  <LogoutOutlined />
                  退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
    </a-layout-header>

    <!-- 内容区域 -->
    <a-layout-content class="page-content">
      <router-view />
    </a-layout-content>

    <!-- 页脚 -->
    <a-layout-footer v-if="!hideFooter" class="page-footer">
      <div class="footer-content">
        <p>© {{ new Date().getFullYear() }} 慧学. All Rights Reserved.</p>
      </div>
    </a-layout-footer>
    
    <!-- 登录模态框 -->
    <a-modal
      v-model:open="loginModalVisible"
      title="用户登录"
      @ok="handleLogin"
      :confirmLoading="loginLoading"
    >
      <a-form
        :model="loginForm"
        @finish="handleLogin"
        :label-col="{ span: 5 }"
        :wrapper-col="{ span: 16 }"
		ref="loginformRef"
      >
        <a-form-item
          label="用户名"
          name="username"
          :rules="[{ required: true, message: '请输入用户名' }]"
        >
          <a-input v-model:value="loginForm.username" placeholder="用户名/手机号" />
        </a-form-item>
        <a-form-item
          label="密码"
          name="password"
          :rules="[{ required: true, message: '请输入密码' }]"
        >
          <a-input-password v-model:value="loginForm.password" />
        </a-form-item>
		<!--
        <a-form-item name="remember" :wrapper-col="{ offset: 5 }">
          <a-checkbox v-model:checked="loginForm.remember">记住我</a-checkbox>
        </a-form-item>-->
      </a-form>
    </a-modal>
  </a-layout>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import type { ValidateErrorEntity } from 'ant-design-vue/es/form';
import {
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  TeamOutlined,
  CrownOutlined,
  DownOutlined,
  PlusOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  HomeOutlined,
  AppstoreOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import type { UserRole } from '../../stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const loginformRef = ref();

const hideFooter = computed(() => Boolean(route.meta.hideFooter));

// 计算属性：判断是否为教师
const isTeacher = computed(() => {
  return userStore.userInfo.role === 'teacher';
});

// 计算属性：判断是否为学生
const isStudent = computed(() => {
  return userStore.userInfo.role === 'student';
});

// 计算属性：判断是学生或教师（非管理员）
const isStudentOrTeacher = computed(() => {
  const role = userStore.userInfo.role;
  return role === 'student' || role === 'teacher';
});

// 获取当前角色文本
const getCurrentRoleText = () => {
  switch (userStore.userInfo.role) {
    case 'student':
      return '学生';
    case 'teacher':
      return '教师';
    case 'admin':
      return '管理员';
    default:
      return '未知身份';
  }
};

// 处理角色切换
const handleRoleSwitch = ({ key }: { key: string }) => {
  userStore.switchRole(key as UserRole);
  message.success(`已切换到${getCurrentRoleText()}`);
  
  // 不需要刷新整个页面，只需要重新加载当前路由组件
  const currentRoute = router.currentRoute.value;
  router.replace({
    path: '/redirect',
    query: { 
      path: currentRoute.fullPath,
      _t: Date.now()
    }
  });
};

// 登录模态框相关
const loginModalVisible = ref(false);
const loginLoading = ref(false);
const loginForm = ref({
  username: '',
  password: '',
  remember: false
});

// 显示登录模态框
const showLoginModal = () => {
  loginModalVisible.value = true;
};

// 处理登录请求
const handleLogin = async () => {
  loginformRef.value.validate()
  .then(() => {
  	doLogin();
  })
  .catch((error: ValidateErrorEntity<loginForm>) => {
  	//console.log('error', error);
  });
};
const doLogin=async()=>{
  loginLoading.value = true;
	try {
	  await userStore.login({
	    username: loginForm.value.username,
	    password: loginForm.value.password
	  });
	  message.success('登录成功');
	  loginModalVisible.value = false;
	  
	  // 获取重定向路径
	  const redirectPath = route.query.redirect as string || '/';
	  
	  // 如果有重定向路径，跳转到该路径，否则刷新当前页面
	  if (redirectPath && redirectPath !== route.path) {
	    router.push(redirectPath);
	  } else {
	    router.go(0);
	  }
	} catch (error) {
	  //message.error(error.msg);
	} finally {
	  loginLoading.value = false;
	}
};
// 处理登出
const handleLogout = () => {
  userStore.logout();
  message.success('已退出登录');
  // 如果当前页面需要登录权限，则重定向到首页
  if (route.meta.requiresAuth) {
    router.push('/');
  }
};

const navigateTop = (path: string) => {
  const targetHash = `#${path}`;
  if (window.location.hash !== targetHash) {
    window.location.hash = targetHash;
    return;
  }

  if (route.path !== path) {
    router.push(path);
  }
};

// 根据当前路由计算激活的菜单项
const activeKey = computed(() => {
  const path = route.path;

  if (path.startsWith('/course') && !path.startsWith('/course/resource')) return 'course';
  if (path.startsWith('/classroom')) return 'classroom';
  if (path.startsWith('/project')) return 'project';
  if (path.startsWith('/admin')) return 'admin';
  // if (path.startsWith('/excellent-works')) return 'excellent-works';
  // if (path.startsWith('/resource') || path.startsWith('/course/resource')) return 'resource';
  if (path.startsWith('/competition')) return 'competition';
  if (path.startsWith('/exam')) return 'exam';
  if (path.startsWith('/dashboard')) return 'dashboard';
  if (path === '/') return 'course';

  return '';
});
</script>

<style scoped>
.global-layout {
  min-height: 100vh;
  background: var(--hx-color-bg-layout);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: var(--hx-z-header);
  height: var(--hx-header-height);
  line-height: var(--hx-header-height);
  padding: 0 var(--hx-space-5);
  background: var(--hx-color-bg-container);
  border-bottom: 1px solid var(--hx-color-border-muted);
}

.header-content {
  height: var(--hx-header-height);
  display: flex;
  align-items: center;
  max-width: 1440px;
  margin: 0 auto;
}

.logo {
  height: 32px;
  display: flex;
  align-items: center;
  margin-right: var(--hx-space-7);
}

.logo img {
  height: 24px;
  margin-right: var(--hx-space-2);
}

.logo span {
  font-size: 18px;
  font-weight: 500;
  color: var(--hx-color-text-primary);
}

.logo-link {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: inherit;
}

.logo-link:hover {
  color: var(--hx-color-primary);
}

.nav {
  flex: 1;
}

.top-nav-menu {
  display: flex;
  align-items: center;
  gap: var(--hx-space-1);
  height: var(--hx-header-height);
}

.top-nav-item {
  display: inline-flex;
  align-items: center;
  height: var(--hx-header-height);
  padding: 0 var(--hx-space-4);
  gap: var(--hx-space-2);
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--hx-color-text-primary);
  cursor: pointer;
  font-size: var(--hx-font-size-base);
  line-height: var(--hx-header-height);
  text-decoration: none;
  transition: color 0.2s, border-color 0.2s;
}

.top-nav-item:hover,
.top-nav-item.active {
  color: var(--hx-color-primary);
  border-bottom-color: var(--hx-color-primary);
}

.top-nav-item.admin-menu-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.user-info {
  display: flex;
  align-items: center;
}

.create-dropdown {
  margin-right: var(--hx-space-4);
}

.create-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  color: var(--hx-color-text-secondary);
}

.create-btn:hover {
  color: var(--hx-color-primary);
  background-color: var(--hx-color-primary-dim);
}

.role-switch-dropdown {
  margin-right: var(--hx-space-4);
}

.user-dropdown-link {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 0 4px;
  height: 44px;
}

.user-avatar {
  flex-shrink: 0;
  border: 1px solid var(--hx-color-border-muted);
  box-shadow: var(--hx-shadow-sm);
  background-color: var(--hx-color-bg-container);
}

.username {
  margin-left: var(--hx-space-2);
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-right: 5px;
}

.page-content {
  min-height: calc(100vh - var(--hx-header-height) - var(--hx-footer-height));
  padding: 0;
  background-color: var(--hx-color-bg-layout);
}

.global-layout--workspace .page-content {
  min-height: calc(100vh - var(--hx-header-height));
}

.page-footer {
  text-align: center;
  padding: var(--hx-space-5) 0;
  background: var(--hx-color-bg-layout);
  color: var(--hx-color-text-tertiary);
}

.footer-content {
  max-width: 1440px;
  margin: 0 auto;
  color: var(--hx-color-text-tertiary);
}
</style>
