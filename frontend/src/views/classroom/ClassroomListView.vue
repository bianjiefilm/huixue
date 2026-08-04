<template>
  <PageShell max-width="wide">
    <PageHeaderBar
      title="我的课堂"
      :subtitle="`${totalClassrooms} 个课堂 · ${learnings.length} 进行中 · ${totalStudents} 名学生`"
    >
      <template #actions>
        <a-button v-if="isTeacherOrAdmin" type="primary" @click="showCreateModal">
          <template #icon><PlusOutlined /></template>
          新建课堂
        </a-button>
      </template>
    </PageHeaderBar>

    <a-tabs v-model:activeKey="activeTabKey" class="classroom-tabs">
      <a-tab-pane key="learning" tab="正在上课">
        <a-spin :spinning="loading">
          <EmptyStateBlock
            v-if="learnings.length === 0 && !loading"
            description="暂无正在上课的课堂"
          />
          <div v-else-if="learnings.length > 0" class="classroom-card-list">
            <a-card
              v-for="(classroom, index) in learnings"
              :key="classroom.id"
              class="classroom-card"
              @click="enterClassroom(classroom.id)"
            >
              <template #cover>
                <div class="classroom-cover-gradient" :style="{ background: getGradientByIndex(index) }">
                  <div class="cover-overlay">
                    <span class="cover-title">{{ classroom.name }}</span>
                    <span class="cover-date">{{ formatDateRange(classroom.start_date, classroom.end_date) }}</span>
                  </div>
                </div>
              </template>
              <div class="classroom-header">
                <h3 class="classroom-title">{{ classroom.name }}</h3>
                <a-tag :color="getStatusColor(learnings)">
                  {{ getStatusText(learnings) }}
                </a-tag>
              </div>
              <div class="classroom-info">
                <p><span class="label">教师:</span> {{ classroom.teacher_name }}</p>
                <p><span class="label">起止时间:</span> {{ formatDateRange(classroom.start_date, classroom.end_date) }}</p>
                <p><span class="label">学期:</span> {{ classroom.semester }}</p>
                <p><span class="label">学分:</span> {{ classroom.credit || 0 }}</p>
                <p><span class="label">学生数:</span> {{ classroom.student_count || 0 }}人</p>
                <p><span class="label">实验数:</span> {{ classroom.experiment_count || 0 }}个</p>
                <p><span class="label">实验关卡:</span> {{ classroom.level_count || 0 }}个</p>
                <p><span class="label">金币数:</span> {{ classroom.coin_count || 0 }}个</p>
                <div class="remaining-time" v-if="getRemainingTime(classroom.end_date)">
                  <ClockCircleOutlined />
                  <span>剩余时间：{{ getRemainingTime(classroom.end_date) }}</span>
                </div>
                <div class="progress-section">
                  <div class="progress-header">
                    <span class="label">学习进度</span>
                    <span class="progress-text">{{ classroom.completed_experiment_count || 0 }}/{{ classroom.experiment_count || 0 }} 实验</span>
                  </div>
                  <a-progress
                    :percent="getProgressPercent(classroom)"
                    :stroke-color="{ '0%': 'var(--hx-color-primary)', '100%': 'var(--hx-color-success)' }"
                    :show-info="false"
                    size="small"
                  />
                </div>
              </div>
              <div class="classroom-actions">
                <a-button type="link" @click.stop="enterClassroom(classroom.id)">进入课堂</a-button>
                <a-dropdown>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="edit" @click="editClassroom(classroom.id)">
                        <EditOutlined /> 编辑课堂
                      </a-menu-item>
                      <a-menu-item key="delete" @click="showDeleteConfirm(classroom)">
                        <DeleteOutlined /> 删除课堂
                      </a-menu-item>
                    </a-menu>
                  </template>
                  <a-button type="text" @click.stop>
                    <MoreOutlined />
                  </a-button>
                </a-dropdown>
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-tab-pane>

      <a-tab-pane key="upcoming" tab="未开始">
        <a-spin :spinning="loading">
          <EmptyStateBlock
            v-if="upcomings.length === 0 && !loading"
            description="暂无未开始的课堂"
          />
          <div v-else-if="upcomings.length > 0" class="classroom-card-list">
            <a-card
              v-for="(classroom, index) in upcomings"
              :key="classroom.id"
              class="classroom-card"
              @click="enterClassroom(classroom.id)"
            >
              <template #cover>
                <div class="classroom-cover-gradient" :style="{ background: getGradientByIndex(index) }">
                  <div class="cover-overlay">
                    <span class="cover-title">{{ classroom.name }}</span>
                    <span class="cover-date">{{ formatDateRange(classroom.start_date, classroom.end_date) }}</span>
                  </div>
                </div>
              </template>
              <div class="classroom-header">
                <h3 class="classroom-title">{{ classroom.name }}</h3>
                <a-tag color="blue">未开始</a-tag>
              </div>
              <div class="classroom-info">
                <p><span class="label">教师:</span> {{ classroom.teacher_name }}</p>
                <p><span class="label">起止时间:</span> {{ formatDateRange(classroom.start_date, classroom.end_date) }}</p>
                <p><span class="label">学期:</span> {{ classroom.semester }}</p>
                <p><span class="label">学分:</span> {{ classroom.credit || 0 }}</p>
                <p><span class="label">学生数:</span> {{ classroom.student_count || 0 }}人</p>
                <p><span class="label">实验数:</span> {{ classroom.experiment_count || 0 }}个</p>
                <p><span class="label">实验关卡:</span> {{ classroom.level_count || 0 }}个</p>
                <p><span class="label">金币数:</span> {{ classroom.coin_count || 0 }}个</p>
                <div class="remaining-time" v-if="getRemainingTime(classroom.end_date)">
                  <ClockCircleOutlined />
                  <span>剩余时间：{{ getRemainingTime(classroom.end_date) }}</span>
                </div>
                <div class="progress-section">
                  <div class="progress-header">
                    <span class="label">学习进度</span>
                    <span class="progress-text">{{ classroom.completed_experiment_count || 0 }}/{{ classroom.experiment_count || 0 }} 实验</span>
                  </div>
                  <a-progress
                    :percent="getProgressPercent(classroom)"
                    :stroke-color="{ '0%': 'var(--hx-color-primary)', '100%': 'var(--hx-color-success)' }"
                    :show-info="false"
                    size="small"
                  />
                </div>
              </div>
              <div class="classroom-actions">
                <a-button type="link" @click.stop="enterClassroom(classroom.id)">进入课堂</a-button>
                <a-dropdown>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="edit" @click="editClassroom(classroom.id)">
                        <EditOutlined /> 编辑课堂
                      </a-menu-item>
                      <a-menu-item key="delete" @click="showDeleteConfirm(classroom)">
                        <DeleteOutlined /> 删除课堂
                      </a-menu-item>
                    </a-menu>
                  </template>
                  <a-button type="text" @click.stop>
                    <MoreOutlined />
                  </a-button>
                </a-dropdown>
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-tab-pane>

      <a-tab-pane key="completed" tab="历史课堂">
        <a-spin :spinning="loading">
          <EmptyStateBlock
            v-if="completeds.length === 0 && !loading"
            description="暂无已结课的课堂"
          />
          <div v-else-if="completeds.length > 0" class="classroom-card-list">
            <a-card
              v-for="(classroom, index) in completeds"
              :key="classroom.id"
              class="classroom-card completed-card"
              @click="enterClassroom(classroom.id)"
            >
              <template #cover>
                <div class="classroom-cover-gradient" :style="{ background: getGradientByIndex(index) }">
                  <div class="cover-overlay">
                    <span class="cover-title">{{ classroom.name }}</span>
                    <span class="cover-date">{{ formatDateRange(classroom.start_date, classroom.end_date) }}</span>
                  </div>
                </div>
              </template>
              <div class="classroom-header">
                <h3 class="classroom-title">{{ classroom.name }}</h3>
                <a-tag color="default">已结课</a-tag>
              </div>
              <div class="classroom-info">
                <p><span class="label">教师:</span> {{ classroom.teacher_name }}</p>
                <p><span class="label">起止时间:</span> {{ formatDateRange(classroom.start_date, classroom.end_date) }}</p>
                <p><span class="label">学期:</span> {{ classroom.semester }}</p>
                <p><span class="label">学分:</span> {{ classroom.credit || 0 }}</p>
                <p><span class="label">学生数:</span> {{ classroom.student_count || 0 }}人</p>
                <p><span class="label">实验数:</span> {{ classroom.experiment_count || 0 }}个</p>
                <p><span class="label">实验关卡:</span> {{ classroom.level_count || 0 }}个</p>
                <p><span class="label">金币数:</span> {{ classroom.coin_count || 0 }}个</p>
                <div class="progress-section">
                  <div class="progress-header">
                    <span class="label">学习进度</span>
                    <span class="progress-text">{{ classroom.completed_experiment_count || 0 }}/{{ classroom.experiment_count || 0 }} 实验</span>
                  </div>
                  <a-progress
                    :percent="getProgressPercent(classroom)"
                    :stroke-color="{ '0%': 'var(--hx-color-primary)', '100%': 'var(--hx-color-success)' }"
                    :show-info="false"
                    size="small"
                  />
                </div>
              </div>
              <div class="classroom-actions">
                <a-button type="link" @click.stop="enterClassroom(classroom.id)">查看详情</a-button>
                <a-tooltip title="历史课堂为只读状态，不可编辑">
                  <InfoCircleOutlined class="readonly-hint" />
                </a-tooltip>
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-tab-pane>
    </a-tabs>

    <create-classroom-modal
      v-model:open="createModalVisible"
      @success="handleCreateSuccess"
    />

    <a-modal
      v-model:open="deleteModalVisible"
      title="确认删除"
      @ok="confirmDelete"
      :confirm-loading="deleteLoading"
      @cancel="cancelDelete"
    >
      <p>确定要删除课堂 "{{ classroomToDelete?.name }}" 吗？</p>
      <p>此操作不可恢复，请谨慎操作。</p>
    </a-modal>
  </PageShell>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed, watch } from 'vue';
import { PlusOutlined, InfoCircleOutlined, MoreOutlined, EditOutlined, DeleteOutlined, ClockCircleOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import { getClassrooms } from '@/api/course';
import { useRouter } from 'vue-router';
import { useClassroomStore } from '@/stores/classroom';
import { useUserStore } from '@/stores/user';
import { getToken } from '@/utils/auth';
import CreateClassroomModal from '@/components/classroom/CreateClassroomModal.vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';
import type { Classroom } from '@/types/course';
import dayjs from 'dayjs';
import { techerClassRooms } from '@/api/classrooms';

const router = useRouter();
const classroomStore = useClassroomStore();
const userStore = useUserStore();

// 用户角色计算属性
const userRole = computed(() => userStore.userRole || 'student');
const isTeacherOrAdmin = computed(() => userRole.value === 'teacher' || userRole.value === 'admin');

// 当前激活的标签页
const activeTabKey = ref('learning');

// 创建课堂模态框可见性
const createModalVisible = ref(false);

// 删除课堂相关状态
const deleteModalVisible = ref(false);
const deleteLoading = ref(false);
const classroomToDelete = ref<Classroom | null>(null);

// 加载状态
const loading = ref(false);

// 课堂列表数据
const classrooms = ref([]);
const learnings = ref([]);
const upcomings = ref([]);
const completeds = ref([]);

// 统计计算属性
const totalClassrooms = computed(() => {
  return learnings.value.length + upcomings.value.length + completeds.value.length;
});

const totalStudents = computed(() => {
  let count = 0;
  [...learnings.value, ...upcomings.value].forEach((c: any) => {
    count += c.student_count || 0;
  });
  return count;
});

// 计算进度百分比
const getProgressPercent = (classroom: any) => {
  const completed = classroom.completed_experiment_count || 0;
  const total = classroom.experiment_count || 0;
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
};

// 高质感渐变色配置
const gradients = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',  // 紫罗兰
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',  // 粉红玫瑰
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',  // 蓝天碧海
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',  // 翠竹绿
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',  // 晚霞
  'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',  // 薄荷绿
  'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)',  // 樱花
  'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)',  // 暖阳
  'linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 100%)',  // 冰川蓝
  'linear-gradient(135deg, #d299c2 0%, #fef9d7 100%)',  // 薰衣草
];

const getGradientByIndex = (index: number) => {
  return gradients[index % gradients.length];
};

// 计算剩余时间
const getRemainingTime = (endDateStr?: string): string => {
  if (!endDateStr) return '';
  const end = dayjs(endDateStr);
  const now = dayjs();
  const diff = end.diff(now, 'minute');

  if (diff <= 0) return '已结束';

  const days = Math.floor(diff / (24 * 60));
  const hours = Math.floor((diff % (24 * 60)) / 60);
  const minutes = diff % 60;

  if (days > 0) return `${days}天${hours}小时`;
  if (hours > 0) return `${hours}小时${minutes}分`;
  return `${minutes}分钟`;
};

// 加载课堂数据
const loadClassrooms = async () => {
  loading.value = true;
  try {
    // 根据用户角色调用不同的API
    const userRole = userStore.userRole || 'student';
    const studentId = userRole === 'student' ? userStore.userId : undefined;

    console.log('Loading classrooms for role:', userRole, 'studentId:', studentId);

    if (userRole === 'student' && studentId) {
      // 对于学生，直接调用学生API
      const token = getToken();
      const response = await fetch(`/api/v1/user/classrooms?student_id=${studentId}`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      console.log('Student API response:', data);

      // 更新本地状态
      learnings.value = data.data.ongoing || [];
      upcomings.value = data.data.upcoming || [];
      completeds.value = data.data.past || [];

      console.log('Updated local state - learnings:', learnings.value.length,
                  'upcomings:', upcomings.value.length, 'completeds:', completeds.value.length);

    } else {
      // 对于教师，使用原来的API
      const response = await techerClassRooms({});
      const data = response.data || response;
      learnings.value = data.ongoing || [];
      upcomings.value = data.upcoming || [];
      completeds.value = data.ended || [];
    }

  } catch (error) {
    message.error('获取课堂列表失败，请重试');
    console.error('获取课堂列表失败:', error);
  } finally {
    loading.value = false;
  }
};

// 获取课堂状态颜色
const getStatusColor = (classrooms: any[]) => {
  // 这里传递的是learnings数组，我们需要根据当前标签页判断状态
  if (activeTabKey.value === 'learning') {
    return 'green';
  } else if (activeTabKey.value === 'upcoming') {
    return 'blue';
  } else {
    return 'default';
  }
};

// 获取课堂状态文本
const getStatusText = (classrooms: any[]) => {
  if (activeTabKey.value === 'learning') {
    return '正在上课';
  } else if (activeTabKey.value === 'upcoming') {
    return '未开始';
  } else {
    return '已结课';
  }
};

// 显示创建课堂模态框
const showCreateModal = () => {
  createModalVisible.value = true;
};

// 处理创建课堂成功
const handleCreateSuccess = (classroom: Classroom) => {
  // 重新加载课堂列表
  loadClassrooms();
  // 根据课堂状态切换到对应的标签页
  const startDate = classroom.start_date || classroom.startDate || '';
  const endDate = classroom.end_date || classroom.endDate || '';
  const now = dayjs();
  const start = dayjs(startDate);
  const end = dayjs(endDate);

  if (now.isBefore(start)) {
    activeTabKey.value = 'upcoming';
  } else if (now.isAfter(end)) {
    activeTabKey.value = 'completed';
  } else {
    activeTabKey.value = 'learning';
  }
};

// 进入课堂详情页
const enterClassroom = (id: string) => {
  console.log('进入课堂:', id);
  router.push(`/classroom/${id}`).catch(err => {
    console.error('导航失败:', err);
  });
};

// 编辑课堂
const editClassroom = (id: string) => {
  router.push(`/classroom/${id}/edit`);
};

// 显示删除确认框
const showDeleteConfirm = (classroom: Classroom) => {
  classroomToDelete.value = classroom;
  deleteModalVisible.value = true;
};

// 确认删除课堂
const confirmDelete = async () => {
  if (!classroomToDelete.value) return;

  deleteLoading.value = true;
  try {
    const deletedId = classroomToDelete.value.id;

    // 调用store中的删除方法
    await classroomStore.deleteClassroom(deletedId);

    // 从对应的列表中移除该课堂
    const removeFromList = (list: any[]) => {
      const index = list.findIndex(c => c.id === deletedId);
      if (index !== -1) {
        list.splice(index, 1);
        return true;
      }
      return false;
    };

    // 依次从三个列表中尝试移除
    if (!removeFromList(learnings.value)) {
      if (!removeFromList(upcomings.value)) {
        removeFromList(completeds.value);
      }
    }

    message.success('课堂删除成功');
    deleteModalVisible.value = false;
    classroomToDelete.value = null;
  } catch (error) {
    if (error instanceof Error) {
      message.error(error.message);
    } else {
      message.error('删除课堂失败，请重试');
    }
  } finally {
    deleteLoading.value = false;
  }
};

// 取消删除
const cancelDelete = () => {
  deleteModalVisible.value = false;
  // 延迟清空，避免弹窗关闭动画期间课堂名称显示为空
  setTimeout(() => {
    classroomToDelete.value = null;
  }, 300);
};

// 格式化日期范围
const formatDateRange = (startDate: string, endDate: string) => {
  if (!startDate || !endDate) return '未设置';
  const start = dayjs(startDate).format('YYYY.MM.DD');
  const end = dayjs(endDate).format('YYYY.MM.DD');
  return `${start} - ${end}`;
};

// 监听标签页切换
watch(activeTabKey, (newTab) => {
  // 当切换到不同的标签页时，可能需要重新加载数据
  // 但由于我们一次性加载了所有数据，这里不需要额外操作
});

// 组件挂载时加载数据
onMounted(() => {
  // 【调试模式已禁用】正常加载课堂列表
  loadClassrooms();
});
</script>

<style scoped>
.classroom-tabs {
  margin-top: 0;
}

.classroom-card-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--hx-space-4);
}

.classroom-card {
  width: 100%;
  cursor: pointer;
  transition: all var(--hx-transition-normal);
  overflow: hidden;
  background: var(--hx-color-bg-container);
  border: 1px solid var(--hx-color-border-muted);
  border-radius: var(--hx-radius-sm);
}

.classroom-card:hover {
  box-shadow: var(--hx-shadow-md);
  transform: translateY(-2px);
  border-color: var(--hx-color-primary);
}

.classroom-card :deep(.ant-card-body) {
  padding: 0;
}

.classroom-cover-gradient {
  width: 100%;
  height: 140px;
  display: flex;
  align-items: flex-end;
  padding: var(--hx-space-4);
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}

.classroom-cover-gradient::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(0, 0, 0, 0.1) 0%, rgba(0, 0, 0, 0.4) 100%);
  z-index: 1;
}

.cover-overlay {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-1);
  width: 100%;
}

.cover-title {
  font-size: var(--hx-font-size-md);
  font-weight: 600;
  color: #fff;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cover-date {
  font-size: var(--hx-font-size-xs);
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.classroom-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--hx-space-4) var(--hx-space-4) var(--hx-space-2);
}

.classroom-title {
  margin: 0;
  font-size: var(--hx-font-size-md);
  font-weight: 500;
  color: var(--hx-color-text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: var(--hx-space-2);
}

.classroom-info {
  padding: 0 var(--hx-space-4);
  margin-bottom: var(--hx-space-4);
}

.classroom-info p {
  margin-bottom: 6px;
  font-size: var(--hx-font-size-sm);
  color: var(--hx-color-text-secondary);
}

.label {
  font-weight: 500;
  margin-right: var(--hx-space-2);
  color: var(--hx-color-text-primary);
}

.remaining-time {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: var(--hx-space-2);
  padding: 6px 10px;
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
  border-radius: var(--hx-radius-sm);
  font-size: var(--hx-font-size-sm);
  color: #d46b08;
  font-weight: 500;
}

.remaining-time :deep(svg) {
  font-size: var(--hx-font-size-base);
}

.progress-section {
  margin-top: var(--hx-space-3);
  padding-top: var(--hx-space-3);
  border-top: 1px solid var(--hx-color-border-muted);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--hx-space-2);
}

.progress-header .label {
  font-weight: 500;
  color: var(--hx-color-text-primary);
}

.progress-text {
  font-size: var(--hx-font-size-sm);
  color: var(--hx-color-text-secondary);
}

.classroom-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--hx-space-3) var(--hx-space-4);
  border-top: 1px solid var(--hx-color-border-muted);
  background: var(--hx-color-bg-layout);
}

.readonly-hint {
  color: var(--hx-color-text-tertiary);
  margin-left: var(--hx-space-2);
}

.completed-card {
  opacity: 0.8;
}

.completed-card:hover {
  opacity: 1;
}
</style>
