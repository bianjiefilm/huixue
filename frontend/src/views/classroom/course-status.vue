<template>
  <PageShell max-width="wide" class="course-status-page">
    <a-spin :spinning="loading" tip="加载中...">
      <template v-if="currentClassroom">
        <PageHeaderBar
          :title="currentClassroom.name"
          :subtitle="getStatusText(currentClassroom.status)"
          show-back
          back-to="/classroom"
        />

        <!-- 课堂基本信息卡片 -->
        <a-card class="info-card">
          <a-row :gutter="16">
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ currentClassroom.semester }}</div>
                <div class="stat-label">学期</div>
              </div>
            </a-col>
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ currentClassroom.credits }}</div>
                <div class="stat-label">学分</div>
              </div>
            </a-col>
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ totalCourses }}</div>
                <div class="stat-label">实验数量</div>
              </div>
            </a-col>
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ currentClassroom.experimentStageCount || 0 }}</div>
                <div class="stat-label">实验关卡数</div>
              </div>
            </a-col>
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ currentClassroom.studentCount }}</div>
                <div class="stat-label">学生</div>
              </div>
            </a-col>
            <a-col :span="4">
              <div class="stat-item">
                <div class="stat-value">{{ currentClassroom.coinsCount || 0 }}</div>
                <div class="stat-label">金币</div>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 课程状态标签 -->
        <div class="status-tabs-container">
          <a-radio-group v-model:value="currentStatus" button-style="solid" @change="handleStatusChange">
            <a-radio-button value="all">全部课程 {{ totalCourses }}</a-radio-button>
            <template v-if="currentClassroom.status !== 'past'">
              <a-radio-button value="unpublished">未发布 {{ unpublishedCount }}</a-radio-button>
              <a-radio-button value="learning">学习中 {{ learningCount }}</a-radio-button>
              <a-radio-button value="makeup">补交中 {{ makeupCount }}</a-radio-button>
              <a-radio-button value="completed">已完成 {{ completedCount }}</a-radio-button>
            </template>
            <template v-else>
              <a-radio-button value="unpublished">未发布 {{ unpublishedCount }}</a-radio-button>
              <a-radio-button value="ended">已结束 {{ endedCount }}</a-radio-button>
            </template>
          </a-radio-group>

          <!-- 当选中未发布标签时显示的批量操作按钮 -->
          <div v-if="currentStatus === 'unpublished' && unpublishedCount > 0 && currentClassroom.status !== 'past'" class="batch-actions">
            <a-button type="primary" @click="handlePublishAll">全部发布</a-button>
            <a-button danger @click="handleDeleteAll">全部删除</a-button>
          </div>
        </div>

        <!-- 课程列表 -->
        <div class="course-list-container">
          <a-empty v-if="filteredCourses.length === 0" :description="`暂无${getCurrentStatusText()}课程`" />
          
          <!-- 表格展示课程 -->
          <a-table
            v-else
            :dataSource="filteredCourses"
            :columns="courseColumns"
            :pagination="{ pageSize: 10 }"
            :rowKey="record => record.id"
          >
            <!-- 课程名称列 -->
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'name'">
                <div class="course-name-cell">
                  <div :class="['status-dot', `status-${record.status}`]"></div>
                  <span>{{ record.name }}</span>
                  <flag-outlined v-if="record.completedCount === currentClassroom.studentCount" class="completed-flag" />
                </div>
              </template>

              <!-- 学生完成情况列 -->
              <template v-if="column.dataIndex === 'studentProgress'">
                <div v-if="record.status === 'completed' || record.completedCount === currentClassroom.studentCount">
                  <check-circle-outlined class="success-icon" /> 已完成 {{ record.completedCount }} 人
                </div>
                <div v-else class="student-progress">
                  <div>
                    <span class="progress-label">学习中/补交中:</span>
                    <span class="progress-value learning">{{ record.learningCount }}</span>
                  </div>
                  <div>
                    <span class="progress-label">已完成:</span>
                    <span class="progress-value completed">{{ record.completedCount }}</span>
                  </div>
                  <div>
                    <span class="progress-label">未开始:</span>
                    <span class="progress-value not-started">{{ record.notStartedCount }}</span>
                  </div>
                </div>
              </template>

              <!-- 时间信息列 -->
              <template v-if="column.dataIndex === 'timeInfo'">
                <div v-if="record.status === 'unpublished'">
                  <calendar-outlined /> 创建时间: {{ formatDate(record.createTime) }}
                </div>
                <div v-else>
                  <calendar-outlined /> {{ formatDate(record.startDate) }} 至 {{ formatDate(record.endDate) }}
                  <div v-if="record.status === 'learning' || record.status === 'makeup'" class="remaining-time">
                    <clock-circle-outlined /> 剩余时间: {{ record.remainingTime }}
                  </div>
                </div>
              </template>

              <!-- 操作列 -->
              <template v-if="column.dataIndex === 'actions'">
                <div class="action-buttons">
                  <template v-if="record.status === 'unpublished' && currentClassroom.status !== 'past'">
                    <a-button type="primary" size="small" @click="handlePublish(record)">发布</a-button>
                    <a-button size="small" @click="handleRename(record)">重命名</a-button>
                    <a-button size="small" @click="handleSettings(record)">设置</a-button>
                    <a-button danger size="small" @click="handleDelete(record)">删除</a-button>
                  </template>
                  <template v-else-if="currentClassroom.status === 'past'">
                    <a-button type="primary" size="small" @click="handleViewGrades(record)">查看成绩</a-button>
                    <a-button size="small" @click="handleViewDetails(record)">查看详情</a-button>
                    <a-button v-if="record.type === 'training'" size="small" @click="handleViewAssignments(record)">作业列表</a-button>
                  </template>
                  <template v-else>
                    <a-button type="primary" size="small" @click="handleViewGrades(record)">查看成绩</a-button>
                    <template v-if="record.status !== 'completed' && record.completedCount !== currentClassroom.studentCount">
                      <a-button size="small" @click="handleRename(record)">重命名</a-button>
                      <a-button size="small" @click="handleSettings(record)">设置</a-button>
                      <a-button danger size="small" @click="handleDelete(record)">删除</a-button>
                    </template>
                    <a-button v-if="record.type === 'training'" size="small" @click="handleViewAssignments(record)">作业列表</a-button>
                  </template>
                </div>
              </template>
            </template>
          </a-table>
        </div>
      </template>
      <a-result v-else status="404" title="找不到课堂" sub-title="您访问的课堂不存在或已被删除">
        <template #extra>
          <router-link to="/classroom">
            <a-button type="primary">返回课堂列表</a-button>
          </router-link>
        </template>
      </a-result>
    </a-spin>

    <!-- 重命名课程弹窗 -->
    <a-modal
      v-model:open="renameModalVisible"
      title="重命名课程"
      @ok="confirmRename"
      :confirmLoading="modalLoading"
    >
      <a-form layout="vertical">
        <a-form-item label="课程名称">
          <a-input v-model:value="editingCourseName" placeholder="请输入新的课程名称" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 删除确认弹窗 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="删除课程"
      @ok="confirmDelete"
      :confirmLoading="modalLoading"
      okText="删除"
      okType="danger"
    >
      <p>确定要删除课程 "{{ editingCourseName }}" 吗？此操作不可恢复。</p>
    </a-modal>

    <!-- 批量删除确认弹窗 -->
    <a-modal
      v-model:open="batchDeleteModalVisible"
      title="批量删除课程"
      @ok="confirmBatchDelete"
      :confirmLoading="modalLoading"
      okText="删除"
      okType="danger"
    >
      <p>确定要删除所有未发布的课程吗？此操作不可恢复。</p>
    </a-modal>

    <!-- 批量发布确认弹窗 -->
    <a-modal
      v-model:open="batchPublishModalVisible"
      title="批量发布课程"
      @ok="confirmBatchPublish"
      :confirmLoading="modalLoading"
    >
      <p>确定要发布所有未发布的课程吗？</p>
    </a-modal>

    <!-- 课程发布弹窗 -->
    <CoursePublishModal
      ref="publishModalRef"
      :classroom-id="parseInt(classroomId)"
      :course-id="publishingCourseId"
      :course-name="publishingCourseName"
      :classroom-end-date="currentClassroom?.endDate"
      @success="handlePublishSuccess"
      @cancel="handlePublishCancel"
    />

    <!-- 批量发布弹窗 -->
    <CoursePublishModal
      ref="batchPublishModalRef"
      :classroom-id="parseInt(classroomId)"
      :course-ids="unpublishedCourseIds"
      :classroom-end-date="currentClassroom?.endDate"
      @success="handlePublishSuccess"
      @cancel="handlePublishCancel"
    />
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import { 
  ArrowLeftOutlined, 
  CalendarOutlined, 
  ClockCircleOutlined, 
  FlagOutlined,
  CheckCircleOutlined
} from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import { useClassroomStore } from '../../stores/classroom';
import { useUserStore } from '../../stores/user';
import type { ClassroomDetail, CourseItem, CourseStatus } from '@/types/classroom';
import { 
  getClassroomCoursesWithStats, 
  getClassroomCoursesSummary,
  publishClassroomCourses,
  deleteClassroomCourses,
  publishSingleCourse,
  deleteSingleCourse,
  renameClassroomCourse
} from '../../api/classrooms';
import type { TableColumnsType } from 'ant-design-vue';
import CoursePublishModal from '@/components/classroom/CoursePublishModal.vue';

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();
const userStore = useUserStore();

// 加载状态
const loading = ref(false);
// 当前课堂ID
const classroomId = computed(() => route.params.id as string);
// 当前课堂
const currentClassroom = computed(() => classroomStore.currentClassroom);
// 当前状态筛选
const currentStatus = ref('all');
// 课程列表
const coursesList = ref<CourseItem[]>([]);
// 状态统计数据
const statusSummary = ref({
  total: 0,
  unpublished: 0,
  ongoing: 0,
  makeup: 0,
  finished: 0
});

// 获取当前用户ID
const currentUserId = computed(() => userStore.userId);

const requireCurrentUserId = () => {
  const userId = currentUserId.value;
  if (!userId) {
    message.warning('请先登录后再管理课程状态');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 弹窗状态
const renameModalVisible = ref(false);
const deleteModalVisible = ref(false);
const batchDeleteModalVisible = ref(false);
const batchPublishModalVisible = ref(false);
const modalLoading = ref(false);
const editingCourseId = ref('');
const editingCourseName = ref('');

// 发布相关
const publishModalRef = ref();
const batchPublishModalRef = ref();
const publishingCourseId = ref<number>();
const publishingCourseName = ref<string>();
const unpublishedCourseIds = computed(() => 
  unpublishedCourses.value.map(course => parseInt(course.id))
);

// 课程表格列定义
const courseColumns = reactive<TableColumnsType>([
  {
    title: '课程名称',
    dataIndex: 'name',
    key: 'name',
    width: '30%',
  },
  {
    title: '课程类型',
    dataIndex: 'type',
    key: 'type',
    width: '10%',
    customRender: ({ text }) => {
      return text === 'practice' ? '实践课程' : '实训课程';
    }
  },
  {
    title: '学生完成情况',
    dataIndex: 'studentProgress',
    key: 'studentProgress',
    width: '20%',
  },
  {
    title: '时间信息',
    dataIndex: 'timeInfo',
    key: 'timeInfo',
    width: '20%',
  },
  {
    title: '操作',
    dataIndex: 'actions',
    key: 'actions',
    width: '20%',
  }
]);

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'ongoing': return '正在上课';
    case 'upcoming': return '未开始';
    case 'past': return '历史课堂';
    default: return '未知状态';
  }
};

// 获取状态类名
const getStatusClass = (status: string) => {
  switch (status) {
    case 'ongoing': return 'status-ongoing';
    case 'upcoming': return 'status-upcoming';
    case 'past': return 'status-past';
    default: return '';
  }
};

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 获取当前状态文本
const getCurrentStatusText = () => {
  switch (currentStatus.value) {
    case 'all': return '全部';
    case 'unpublished': return '未发布';
    case 'learning': return '学习中';
    case 'makeup': return '补交中';
    case 'completed': return '已完成';
    case 'ended': return '已结束';
    default: return '';
  }
};

// 基于API统计数据的计数
const totalCourses = computed(() => statusSummary.value.total);
const unpublishedCount = computed(() => statusSummary.value.unpublished);
const learningCount = computed(() => statusSummary.value.ongoing);
const makeupCount = computed(() => statusSummary.value.makeup);
const completedCount = computed(() => statusSummary.value.finished);

// 历史课堂的已结束课程数（总数减去未发布）
const endedCount = computed(() => {
  if (currentClassroom.value?.status !== 'past') return 0;
  return statusSummary.value.total - statusSummary.value.unpublished;
});

// 过滤后的课程列表（用于筛选显示）
const unpublishedCourses = computed(() => {
  return coursesList.value.filter(course => course.status === 'unpublished');
});

const learningCourses = computed(() => {
  return coursesList.value.filter(course => course.status === 'learning');
});

const makeupCourses = computed(() => {
  return coursesList.value.filter(course => course.status === 'makeup');
});

const completedCourses = computed(() => {
  return coursesList.value.filter(course => 
    course.status === 'completed' || course.completedCount === currentClassroom.value?.studentCount
  );
});

const endedCourses = computed(() => {
  if (currentClassroom.value?.status !== 'past') return [];
  return coursesList.value.filter(course => course.status !== 'unpublished');
});

// 根据当前筛选状态过滤课程
const filteredCourses = computed(() => {
  switch (currentStatus.value) {
    case 'unpublished':
      return unpublishedCourses.value;
    case 'learning':
      return learningCourses.value;
    case 'makeup':
      return makeupCourses.value;
    case 'completed':
      return completedCourses.value;
    case 'ended':
      return endedCourses.value;
    default:
      return coursesList.value;
  }
});

// 处理状态切换
const handleStatusChange = (e: any) => {
  console.log('切换到状态:', e.target.value);
  // 重新获取过滤后的数据
  fetchCourseList();
};

// 处理课程发布
const handlePublish = async (course: CourseItem) => {
  publishingCourseId.value = parseInt(course.id);
  publishingCourseName.value = course.name;
  publishModalRef.value?.open();
};

// 处理重命名
const handleRename = (course: CourseItem) => {
  editingCourseId.value = course.id;
  editingCourseName.value = course.name;
  renameModalVisible.value = true;
};

// 确认重命名
const confirmRename = async () => {
  if (!editingCourseName.value.trim()) {
    message.error('课程名称不能为空');
    return;
  }
  
  modalLoading.value = true;
  
  try {
    const response = await renameClassroomCourse(
      parseInt(editingCourseId.value),
      editingCourseName.value,
      requireCurrentUserId()
    );
    
    if (response.code === '0000') {
      message.success('课程重命名成功');
      // 重新加载课程列表
      await fetchCourseList();
    } else {
      message.error(response.message || '重命名失败');
    }
  } catch (error) {
    console.error('重命名课程失败:', error);
    message.error('重命名课程失败，请稍后重试');
  } finally {
    modalLoading.value = false;
    renameModalVisible.value = false;
  }
};

// 处理设置
const handleSettings = (course: CourseItem) => {
  message.info(`设置课程 "${course.name}" 的功能尚未实现`);
};

// 处理删除
const handleDelete = (course: CourseItem) => {
  editingCourseId.value = course.id;
  editingCourseName.value = course.name;
  deleteModalVisible.value = true;
};

// 确认删除
const confirmDelete = async () => {
  modalLoading.value = true;
  
  try {
    const response = await deleteSingleCourse({
      classroomCourseId: parseInt(editingCourseId.value),
      teacherId: requireCurrentUserId()
    });
    
    if (response.code === '0000') {
      message.success('课程删除成功');
      // 重新加载课程列表
      await fetchCourseList();
    } else {
      message.error(response.message || '删除课程失败');
    }
  } catch (error) {
    console.error('删除课程失败:', error);
    message.error('删除课程失败，请稍后重试');
  } finally {
    modalLoading.value = false;
    deleteModalVisible.value = false;
  }
};

// 批量发布
const handlePublishAll = () => {
  if (unpublishedCount.value === 0) {
    message.info('没有未发布的课程可发布');
    return;
  }
  
  batchPublishModalRef.value?.open();
};

// 确认批量发布（旧的，保留以兼容）
const confirmBatchPublish = async () => {
  batchPublishModalVisible.value = false;
  batchPublishModalRef.value?.open();
};

// 发布成功回调
const handlePublishSuccess = async () => {
  await fetchCourseList();
};

// 发布取消回调
const handlePublishCancel = () => {
  publishingCourseId.value = undefined;
  publishingCourseName.value = undefined;
};

// 批量删除
const handleDeleteAll = () => {
  if (unpublishedCount.value === 0) {
    message.info('没有未发布的课程可删除');
    return;
  }
  
  batchDeleteModalVisible.value = true;
};

// 确认批量删除
const confirmBatchDelete = async () => {
  modalLoading.value = true;
  
  try {
    // 获取所有未发布课程的ID
    const unpublishedCourseIds = unpublishedCourses.value.map(course => parseInt(course.id));
    const deleteCount = unpublishedCourseIds.length;
    
    const response = await deleteClassroomCourses({
      classroomId: parseInt(classroomId.value),
      courseIds: unpublishedCourseIds,
      teacherId: requireCurrentUserId()
    });
    
    if (response.code === '0000') {
      message.success(`成功删除了 ${deleteCount} 个课程`);
      // 重新加载课程列表
      await fetchCourseList();
    } else {
      message.error(response.message || '批量删除课程失败');
    }
  } catch (error) {
    console.error('批量删除课程失败:', error);
    message.error('批量删除课程失败，请稍后重试');
  } finally {
    modalLoading.value = false;
    batchDeleteModalVisible.value = false;
  }
};

// 查看成绩
const handleViewGrades = (course: CourseItem) => {
  const courseName = course.name || course.title || '';
  const courseType = course.type || 'practice';
  const classroomCourseId = course.classroom_course_id || course.classroomCourseId || course.id;
  router.push({
    path: `/classroom/${classroomId.value}/course/${classroomCourseId}/grades`,
    query: {
      courseName,
      courseType,
      courseId: course.course_id,
      practiceId: course.practice_id
    }
  });
};

// 查看详情
const handleViewDetails = (course: CourseItem) => {
  message.info(`查看课程 "${course.name}" 的详情功能尚未实现`);
};

// A查看作业列表
const handleViewAssignments = (course: CourseItem) => {
  message.info(`查看课程 "${course.name}" 的作业列表功能尚未实现`);
};

// 获取课堂详情和课程列表
const fetchCourseList = async () => {
  try {
    loading.value = true;
    
    // 同时获取课程列表和统计数据
    const [coursesResponse, summaryResponse] = await Promise.all([
      getClassroomCoursesWithStats({
        classroomId: parseInt(classroomId.value),
        status: currentStatus.value === 'all' ? undefined : currentStatus.value,
        teacherId: requireCurrentUserId()
      }),
      getClassroomCoursesSummary(parseInt(classroomId.value), requireCurrentUserId())
    ]);
    
    // 处理课程列表数据
    if (coursesResponse.code === '0000') {
      const coursesData = coursesResponse.data.list || [];
      coursesList.value = coursesData.map((course: any) => ({
        id: course.id.toString(),
        classroom_course_id: course.id,
        course_id: course.course_id || course.course?.id,
        practice_id: course.practice_id || course.practice?.id,
        name: course.course?.title || course.name || '未命名课程',
        type: course.course?.course_type || 'practice',
        status: mapBackendStatusToFrontend(course.teacher_publish_status),
        completedCount: course.completed_students || 0,
        learningCount: course.learning_students || 0,
        notStartedCount: course.not_started_students || 0,
        createTime: course.created_at,
        startDate: course.start_at,
        endDate: course.deadline_at,
        remainingTime: course.remaining_days ? `${course.remaining_days}天` : '已截止'
      }));
    }
    
    // 处理统计数据
    if (summaryResponse.code === '0000') {
      statusSummary.value = {
        total: summaryResponse.data.total || 0,
        unpublished: summaryResponse.data.unpublished || 0,
        ongoing: summaryResponse.data.ongoing || 0,
        makeup: summaryResponse.data.makeup || 0,
        finished: summaryResponse.data.finished || 0
      };
    }
  } catch (error) {
    console.error('获取课程列表失败:', error);
    message.error('获取课程列表失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 后端状态映射到前端状态
const mapBackendStatusToFrontend = (backendStatus: string) => {
  const statusMap: Record<string, string> = {
    'UNPUBLISHED': 'unpublished',
    'LEARNING': 'learning', 
    'MAKEUP': 'makeup',
    'COMPLETED': 'completed'
  };
  return statusMap[backendStatus] || 'unpublished';
};

// 获取课堂详情
const fetchClassroomDetail = async () => {
  loading.value = true;
  try {
    await classroomStore.fetchClassroomDetail(classroomId.value);
    fetchCourseList();
  } catch (error) {
    console.error('获取课堂详情失败:', error);
    message.error('获取课堂详情失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 组件挂载时获取课堂详情
onMounted(() => {
  fetchClassroomDetail();
});
</script>

<style scoped>
.course-status-page {
  /* PageShell handles outer padding */
}




.status-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  color: #fff;
  margin-right: 16px;
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
}

.info-card {
  margin-bottom: 24px;
}

.stat-item {
  text-align: center;
  padding: 16px 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1890ff;
}

.stat-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.status-tabs-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.course-list-container {
  margin-bottom: 24px;
}

.course-name-cell {
  display: flex;
  align-items: center;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 8px;
}

.status-unpublished {
  background-color: #d9d9d9;
}

.status-learning {
  background-color: #1890ff;
}

.status-makeup {
  background-color: #faad14;
}

.status-completed {
  background-color: #52c41a;
}

.status-ended {
  background-color: #8c8c8c;
}

.completed-flag {
  color: #f5222d;
  margin-left: 8px;
}

.student-progress {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-label {
  color: rgba(0, 0, 0, 0.45);
  margin-right: 8px;
}

.progress-value.learning {
  color: #1890ff;
}

.progress-value.completed {
  color: #52c41a;
  font-weight: 500;
}

.progress-value.not-started {
  color: #d9d9d9;
}

.success-icon {
  color: #52c41a;
  margin-right: 8px;
}

.remaining-time {
  color: #faad14;
  margin-top: 4px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style> 
