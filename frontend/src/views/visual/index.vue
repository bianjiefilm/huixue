<template>
  <div>
	 <iframe
	   ref="jupyterFrame"
	   :src="bigdataurl"
	   width="100%"
	   style="height: calc(100vh - 70px);"
	   frameborder="0"
	 ></iframe>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import VisualEditor from '../../components/visual/VisualEditor.vue';
import PropertyPanel from '../../components/visual/PropertyPanel.vue';
import ManualDrawer from '../../components/visual/ManualDrawer.vue';
import { useUserStore } from '../../stores/user';

const router = useRouter();
const userStore = useUserStore();
const bigdataurl = ref('http://1.95.89.253/bigdatav/index.html#/page/create');
// 状态变量
const showPropertyPanel = ref(false);
const showManualDrawer = ref(false);
const selectedComponent = ref<Record<string, any> | undefined>(undefined);

// 处理属性更新
const handlePropertiesUpdate = (component: any, properties: any) => {
  // 检查用户登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录后再编辑可视化组件');
    router.push('/login?redirect=' + encodeURIComponent(router.currentRoute.value.fullPath));
    return;
  }
  
  // 更新组件属性的逻辑
  console.log('更新组件属性:', component, properties);
};

// 检查登录状态
const checkLoginStatus = () => {
  if (userStore.isLoggedIn) {
    console.log('用户已登录:', userStore.userInfo.username);
  } else {
    console.log('用户未登录');
  }
};

// 生命周期钩子
onMounted(() => {
  checkLoginStatus();
});
</script>

<style scoped>
/* 内容样式 */
</style> 