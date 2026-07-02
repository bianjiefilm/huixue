<template>
    <a-card class="info-card">
      <template #title>
        <div class="card-title">
          <InfoCircleOutlined />
          <span>课堂基本信息</span>
        </div>
      </template>
      <a-descriptions v-if="classroom" :column="{ xs: 1, sm: 2, md: 3 }">
        <a-descriptions-item label="教师">{{ classroom.teacher }}</a-descriptions-item>
        <a-descriptions-item label="起止时间">
          {{ formatDate(classroom.start_date) }} 至 {{ formatDate(classroom.end_date) }}
        </a-descriptions-item>
        <a-descriptions-item label="学期">{{ classroom.semester }}</a-descriptions-item>
        <a-descriptions-item label="学分">{{ classroom.credits }}</a-descriptions-item>
        <a-descriptions-item label="学生数量">{{ classroom.students }}</a-descriptions-item>
        <a-descriptions-item label="创建时间">{{ classroom.created_at }}</a-descriptions-item>
      </a-descriptions>
      <div v-if="classroom && classroom.description" class="classroom-description">
        <h3>课堂描述</h3>
        <p>{{ classroom.description }}</p>
      </div>
      <a-empty v-else-if="!classroom" description="暂无课堂信息" />
    </a-card>
  </template>
  
  <script setup lang="ts">
  import { InfoCircleOutlined } from '@ant-design/icons-vue';
  import { Descriptions, DescriptionsItem } from 'ant-design-vue';
  import dayjs from 'dayjs';
  import type { ClassroomDetail } from '@/types/classroom'; // Adjust path as needed
  
  interface Props {
    classroom: ClassroomDetail | null;
  }
  
  defineProps<Props>();
  
  // 模块注册 (Ant Design Vue specific)
  const ADescriptions = Descriptions;
  const ADescriptionsItem = DescriptionsItem;
  
  // 格式化日期
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return dayjs(dateStr).format('YYYY-MM-DD');
  };
  </script>
  
  <style scoped>
  .info-card {
    margin-bottom: 24px;
  }
  
  .card-title {
    display: flex;
    align-items: center;
  }
  
  .card-title :deep(svg) {
    margin-right: 8px;
    font-size: 16px;
  }
  
  .classroom-description {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
  
  .classroom-description h3 {
    font-size: 16px;
    margin-bottom: 8px;
  }
  </style>