<template>
  <div style="padding: 20px;">
    <h1>API测试页面</h1>
    
    <div style="margin: 20px 0;">
      <a-button @click="testMaterialAPI">测试课程教材API</a-button>
      <a-button @click="testMicroAPI" style="margin-left: 10px;">测试微型实验API</a-button>
    </div>
    
    <div style="background: #f0f0f0; padding: 20px; margin-top: 20px;">
      <h2>API响应数据：</h2>
      <pre>{{ JSON.stringify(apiResponse, null, 2) }}</pre>
    </div>
    
    <div style="background: #e0e0e0; padding: 20px; margin-top: 20px;">
      <h2>处理后的数据：</h2>
      <pre>{{ JSON.stringify(processedData, null, 2) }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { materialList, microList } from '@/api/cmaterial';

const apiResponse = ref<any>(null);
const processedData = ref<any>(null);

const testMaterialAPI = async () => {
  console.log('开始测试课程教材API...');
  try {
    const res = await materialList({ limit: 6, page: 1 });
    console.log('原始响应:', res);
    apiResponse.value = res;
    
    // 检查数据结构
    if (res && res.list) {
      processedData.value = res.list.map((item: any) => ({
        id: item.id,
        title: item.title,
        direction: item.direction,
        source: item.source,
        cover_url: item.cover_url
      }));
    }
  } catch (error) {
    console.error('API调用失败:', error);
    apiResponse.value = { error: error.message };
  }
};

const testMicroAPI = async () => {
  console.log('开始测试微型实验API...');
  try {
    const res = await microList({ limit: 8, page: 1 });
    console.log('原始响应:', res);
    apiResponse.value = res;
    
    // 检查数据结构
    if (res && res.list) {
      processedData.value = res.list.map((item: any) => ({
        id: item.id,
        title: item.title,
        direction: item.direction,
        category: item.category,
        difficulty: item.difficulty,
        cover_url: item.cover_url
      }));
    }
  } catch (error) {
    console.error('API调用失败:', error);
    apiResponse.value = { error: error.message };
  }
};
</script>