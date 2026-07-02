<template>
    <div>
      <!-- 返回按钮 -->
      <div class="back-link">
        <router-link to="/classroom">
          <a-button type="link">
            <template #icon><arrow-left-outlined /></template>
            返回课堂列表
          </a-button>
        </router-link>
      </div>
  
      <!-- 课堂标题和状态 -->
      <div class="classroom-header">
        <div v-if="classroom" class="status-badge" :class="getStatusClass(classroom.status)">
          {{ getStatusText(classroom.status) }}
        </div>
        <h1 v-if="classroom" class="classroom-title">{{ classroom.name }}</h1>
        <div class="header-actions">
          <router-link :to="`/classroom/${classroomId}/status`" v-if="showTeacherView">
            <a-button type="primary" style="margin-right: 8px;">
              课程状态管理
            </a-button>
          </router-link>
          <router-link :to="`/classroom/${classroomId}/student-status`" v-if="showStudentView">
            <a-button type="primary" style="margin-right: 8px;">
              我的课程状态
            </a-button>
          </router-link>
          <a-button v-if="classroom && classroom.status !== 'past' && showTeacherView" type="primary" @click="emit('edit')" style="margin-right: 8px;">
            编辑课堂
          </a-button>
          <a-button v-if="classroom && classroom.status !== 'past' && showTeacherView" type="primary" danger @click="emit('delete')">
            删除课堂
          </a-button>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue';
  import { ArrowLeftOutlined } from '@ant-design/icons-vue';
  import type { ClassroomDetail } from '@/types/classroom'; // Adjust path as needed
  
  interface Props {
    classroom: ClassroomDetail | null;
    classroomId: string;
    showTeacherView: boolean;
    showStudentView: boolean;
  }
  
  const props = defineProps<Props>();
  const emit = defineEmits(['edit', 'delete']);
  
  // 获取状态文本
  const getStatusText = (status?: string) => {
    if (!status) return '';
    switch (status) {
      case 'ongoing': return '正在上课';
      case 'upcoming': return '未开始';
      case 'past': return '已结束';
      default: return '未知状态';
    }
  };
  
  // 获取状态类名
  const getStatusClass = (status?: string) => {
    if (!status) return '';
    switch (status) {
      case 'ongoing': return 'status-ongoing';
      case 'upcoming': return 'status-upcoming';
      case 'past': return 'status-past';
      default: return '';
    }
  };
  </script>
  
  <style scoped>
  .back-link {
    margin-bottom: 16px;
  }
  
  .classroom-header {
    display: flex;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px; /* Added gap for better wrapping */
  }
  
  .status-badge {
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 14px;
    color: #fff;
    /* margin-right: 16px; Removed margin, using gap */
  }
  
  .status-ongoing {
    background-color: #1890ff;
  }
  
  .status-upcoming {
    background-color: #52c41a;
  }
  
  .status-past {
    background-color: #d9d9d9;
  }
  
  .classroom-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0;
    flex: 1;
    min-width: 150px; /* Ensure title doesn't collapse too much */
  }
  
  .header-actions {
    margin-left: auto; /* Pushes actions to the right */
    display: flex;
    flex-wrap: wrap; /* Allow buttons to wrap */
    gap: 8px; /* Space between buttons */
  }
  </style>