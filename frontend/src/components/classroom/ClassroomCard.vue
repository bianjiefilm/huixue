<template>
  <a-card class="classroom-card" :hoverable="true" :bodyStyle="{ padding: '0' }">
    <div class="card-content">
      <div class="card-header">
        <div class="header-left">
          <div class="status-badge" :class="getBadgeClass(status)">{{ status }}</div>
          <div class="classroom-title" @click="handleViewClassroom" style="cursor: pointer;">{{ classroom.name }}</div>
        </div>
        <div class="header-right" @click.stop v-if="isEditable || status !== '已结束'">
          <a-dropdown placement="bottomRight">
            <a class="more-action-btn" @click.prevent>
              <MoreOutlined style="font-size: 16px; color: #999;" />
            </a>
            <template #overlay>
              <a-menu>
                <a-menu-item key="enter" @click="handleViewClassroom">
                  进入课堂
                </a-menu-item>
                <a-menu-item key="edit" v-if="isEditable && status !== '已结束'" @click="handleEditClassroom">
                  编辑
                </a-menu-item>
                <a-menu-item key="delete" v-if="isEditable && status !== '已结束'" @click="handleDeleteClassroom">
                  <span style="color: #ff4d4f;">删除</span>
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
      <div class="classroom-info">
        <div class="info-row">
          <TeamOutlined />
          <span>教师: {{ classroom.teacherName }}</span>
        </div>
        <div class="info-row">
          <CalendarOutlined />
          <span>起止时间: {{ formatDateRange(classroom.startDate, classroom.endDate) }}</span>
        </div>
        <div class="info-row">
          <BookOutlined />
          <span>学期: {{ classroom.semester }}</span>
        </div>
        <div class="info-row">
          <TrophyOutlined />
          <span>学分: {{ classroom.credits }}</span>
        </div>
        <div class="info-row" v-if="classroom.experimentCount !== undefined">
          <ExperimentOutlined />
          <span>实验数: {{ classroom.experimentCount }}</span>
        </div>
        <div class="info-row" v-if="classroom.studentCount !== undefined">
          <TeamOutlined />
          <span>学生数量: {{ classroom.studentCount }}</span>
        </div>
      </div>
      <div class="progress-info" v-if="classroom.completedExperiments !== undefined && classroom.totalExperiments !== undefined">
        <div class="progress-text">
          已学习 {{ classroom.completedExperiments }}/{{ classroom.totalExperiments }} 实验
        </div>
        <a-progress :percent="getProgressPercent()" :status="getProgressStatus()" />
      </div>
      <div class="card-actions-wrapper">
        <!-- Deleted the original card-actions and buttons per UX -->
      </div>
    </div>
  </a-card>
</template>

import { computed, createVNode } from 'vue';
import { useRouter } from 'vue-router';
import { TeamOutlined, CalendarOutlined, BookOutlined, TrophyOutlined, ExperimentOutlined, MoreOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
import { Modal } from 'ant-design-vue';

// 定义组件属性
const props = defineProps({
  classroom: {
    type: Object,
    required: true
  },
  status: {
    type: String,
    default: '正在上课'
  },
  isEditable: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['delete']);

const router = useRouter();

// 获取徽章样式类
const getBadgeClass = (status: string) => {
  switch (status) {
    case '正在上课': return 'status-ongoing';
    case '未开始': return 'status-upcoming';
    case '已结束': return 'status-past';
    default: return '';
  }
};

// 格式化日期范围
const formatDateRange = (startDate: string, endDate: string) => {
  if (!startDate || !endDate) return '无日期信息';
  return `${startDate.substring(0, 10)} 至 ${endDate.substring(0, 10)}`;
};

// 计算进度百分比
const getProgressPercent = () => {
  if (props.classroom.completedExperiments === undefined || props.classroom.totalExperiments === undefined || props.classroom.totalExperiments === 0) {
    return 0;
  }
  return Math.round((props.classroom.completedExperiments / props.classroom.totalExperiments) * 100);
};

// 获取进度状态
const getProgressStatus = () => {
  const percent = getProgressPercent();
  if (percent === 100) return 'success';
  if (props.status === '已结束') return 'exception';
  return 'active';
};

// 查看课堂详情
const handleViewClassroom = () => {
  router.push(`/classroom/${props.classroom.id}`);
};

// 编辑课堂
const handleEditClassroom = () => {
  router.push(`/classroom/${props.classroom.id}/edit`);
};

// 删除课堂
const handleDeleteClassroom = () => {
  Modal.confirm({
    title: '删除后将无法恢复，是否确认删除？',
    icon: createVNode(ExclamationCircleOutlined),
    content: '删除课堂将不可逆',
    okType: 'danger',
    onOk() {
      emit('delete', props.classroom.id);
    },
  });
};
</script>

<style scoped>
.classroom-card {
  height: 100%;
  transition: all 0.3s;
}

.classroom-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.09);
}

.card-content {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.more-action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  transition: background 0.3s;
}

.more-action-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.status-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  color: #fff;
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
  font-size: 16px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
  flex: 1;
}

.classroom-info {
  margin-bottom: 16px;
}

.info-row {
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
}

.info-row :deep(svg) {
  margin-right: 8px;
  font-size: 14px;
}

.progress-info {
  margin-bottom: 16px;
}

.progress-text {
  margin-bottom: 8px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.card-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}
</style> 