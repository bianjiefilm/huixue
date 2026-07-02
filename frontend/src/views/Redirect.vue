<template>
  <div>重定向中...</div>
</template>

<script setup>
import { onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const route = useRoute();
const router = useRouter();

onMounted(() => {
  const { query } = route;
  const { path, _t, ...otherQuery } = query;
  
  // 防止重定向到自身
  if (path && path !== '/redirect' && path !== route.path) {
    const targetPath = Array.isArray(path) ? path[0] : path;
    if (typeof targetPath === 'string') {
      // 移除 path 和 _t 参数，保留其他查询参数
      router.replace({
        path: targetPath,
        query: otherQuery
      });
    } else {
      router.replace('/');
    }
  } else {
    router.replace('/');
  }
});
</script> 