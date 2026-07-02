<template>
    <a-card class="stats-card">
      <template #title>
        <div class="card-title">
          <PieChartOutlined />
          <span>课程进度统计</span>
        </div>
      </template>
      <a-row v-if="classroom" :gutter="16">
        <a-col :xs="24" :sm="12" :md="8">
          <a-statistic
            title="实验总数"
            :value="classroom.courses_count || 0"
            :valueStyle="{ color: '#1890ff' }"
          >
            <template #prefix>
              <ExperimentOutlined />
            </template>
          </a-statistic>
        </a-col>
        <a-col :xs="24" :sm="12" :md="8">
          <a-statistic
            title="实验关卡数"
            :value="classroom.task_count || 0"
            :valueStyle="{ color: '#52c41a' }"
          >
            <template #prefix>
              <flag-outlined />
            </template>
          </a-statistic>
        </a-col>
      </a-row>
      <div class="progress-section" v-if="classroom && classroom.completedExperiments !== undefined && classroom.totalExperiments !== undefined">
        <h3>实验完成情况</h3>
        <div class="progress-info">
          <div class="progress-text">
            已学习 {{ classroom.completedExperiments }}/{{ classroom.totalExperiments }} 实验
          </div>
          <a-progress :percent="getProgressPercent()" :status="getProgressStatus()" />
        </div>
      </div>
       <a-empty v-else-if="!classroom" description="暂无统计信息" />
    </a-card>
  </template>
  
  <script setup lang="ts">
  import { computed } from 'vue';
  import { PieChartOutlined, ExperimentOutlined, FlagOutlined, TrophyOutlined } from '@ant-design/icons-vue';
  import type { ClassroomDetail } from '@/types/classroom'; // Adjust path as needed
  
  interface Props {
    classroom: ClassroomDetail | null;
  }
  
  const props = defineProps<Props>();
  
  // 计算进度百分比
  const getProgressPercent = () => {
    if (!props.classroom) return 0;
    const { completedExperiments, totalExperiments } = props.classroom;
    if (completedExperiments === undefined || totalExperiments === undefined || totalExperiments === 0) {
      return 0;
    }
    return Math.round((completedExperiments / totalExperiments) * 100);
  };
  
  // 获取进度状态
  const getProgressStatus = () => {
    if (!props.classroom) return 'normal';
    const percent = getProgressPercent();
    if (percent === 100) return 'success';
    if (props.classroom.status === 'past') return 'exception';
    return 'active';
  };
  </script>
  
  <style scoped>
  .stats-card {
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
  
  .progress-section {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
  
  .progress-section h3 {
    font-size: 16px;
    margin-bottom: 16px;
  }
  
  .progress-info {
    margin-bottom: 16px;
  }
  
  .progress-text {
    margin-bottom: 8px;
    font-size: 14px;
    color: rgba(0, 0, 0, 0.65);
  }
  </style>