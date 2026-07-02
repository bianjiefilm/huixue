<template>
  <div class="debug-container">
    <h1>课程数据调试页面</h1>
    
    <div class="section">
      <h2>课程教材 (Course Materials)</h2>
      <button @click="fetchCourseMaterials">获取课程教材</button>
      <div class="data-display">
        <pre>{{ JSON.stringify(courseMaterials, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="section">
      <h2>微型实验 (Micro Courses)</h2>
      <button @click="fetchMicroCourses">获取微型实验</button>
      <div class="data-display">
        <pre>{{ JSON.stringify(microCourses, null, 2) }}</pre>
      </div>
    </div>
    
    <div class="section">
      <h2>原始API响应</h2>
      <div class="data-display">
        <pre>{{ JSON.stringify(rawResponse, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { getCourseResources, getMicroCourses } from '@/api/course';
import { materialList, microList } from '@/api/cmaterial';

const courseMaterials = ref<any[]>([]);
const microCourses = ref<any[]>([]);
const rawResponse = ref<any>({});

const fetchCourseMaterials = async () => {
  try {
    // 获取处理后的数据
    const processed = await getCourseResources();
    courseMaterials.value = processed;
    
    // 获取原始响应
    const raw = await materialList({ limit: 10, page: 1 });
    rawResponse.value.courseMaterials = raw;
    
    console.log('处理后的课程教材:', processed);
    console.log('原始课程教材响应:', raw);
  } catch (error) {
    console.error('获取课程教材失败:', error);
  }
};

const fetchMicroCourses = async () => {
  try {
    // 获取处理后的数据
    const processed = await getMicroCourses();
    microCourses.value = processed;
    
    // 获取原始响应
    const raw = await microList({ limit: 10, page: 1 });
    rawResponse.value.microCourses = raw;
    
    console.log('处理后的微型实验:', processed);
    console.log('原始微型实验响应:', raw);
  } catch (error) {
    console.error('获取微型实验失败:', error);
  }
};
</script>

<style scoped>
.debug-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.section {
  margin-bottom: 40px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
}

h1 {
  color: #333;
  margin-bottom: 30px;
}

h2 {
  color: #666;
  margin-bottom: 20px;
}

button {
  padding: 10px 20px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-bottom: 20px;
}

button:hover {
  background-color: #40a9ff;
}

.data-display {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}
</style>