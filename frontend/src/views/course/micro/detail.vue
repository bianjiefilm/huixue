<template>
  <div class="detail-page">
    <!-- 内容区域 -->
    <div class="content-container">
      <a-spin :spinning="loading" tip="加载中...">
        <template v-if="course">

          <div class="course-header">
            <div class="course-info">
              <h1 class="course-title">{{ course.title }}</h1>
              <div class="course-meta">
                <a-tag>{{ course.category }}</a-tag>
                <a-tag color="blue">{{ course.level || difficultyText(course.difficulty) }}</a-tag>
                <a-tag color="#1890ff">{{ course.direction }}</a-tag>
                <a-tag color="gold">
                  <template #icon><gift-outlined /></template>
                  {{ totalCoins }} 金币
                </a-tag>
              </div>
            </div>
            <div class="action-buttons">
              <a-button type="primary" @click="showAddToClassroomModal = true">
                <template #icon><plus-outlined /></template>
                添加到课堂
              </a-button>
            </div>
          </div>
          <a-divider />
          
          <!-- 课程内容区域 -->
          <div class="course-content">
            <!-- 实践介绍 -->
            <a-card class="content-card" title="实践介绍">
              <template #extra>
                <info-circle-outlined />
              </template>
              <div class="introduction">
                {{ course.intro || course.summary || course.description || '暂无介绍' }}
              </div>
            </a-card>

            <!-- 课程任务 -->
            <a-card class="content-card" title="全部任务">
              <template #extra>
                <safety-outlined />
              </template>
              <a-empty v-if="!course.tasks || course.tasks.length === 0" description="暂无任务" />
              <div v-else class="tasks-container">
                <a-table 
                  :dataSource="course.tasks" 
                  :columns="taskColumns" 
                  :pagination="false"
                  row-key="id"
                >
                  <template #bodyCell="{ column, record }">
                    <template v-if="column.key === 'order'">
                      {{ record.order_in_practice || 1 }}
                    </template>
                    <template v-else-if="column.key === 'status'">
                      <a-tooltip v-if="record.is_completed" title="已通过">
                        <check-circle-outlined style="color: #52c41a; font-size: 18px;" />
                      </a-tooltip>
                      <a-tooltip v-else title="未完成">
                        <clock-circle-outlined style="color: #d9d9d9; font-size: 18px;" />
                      </a-tooltip>
                    </template>
                    <template v-else-if="column.key === 'title'">
                      <div class="task-title-cell">
                        <div class="task-title">{{ record.title }}</div>
                        <div class="task-description">{{ record.description || '暂无描述' }}</div>
                      </div>
                    </template>
                    <template v-else-if="column.key === 'type'">
                      <a-tag :color="taskTypeColor(record.type)">
                        {{ taskTypeText(record.type) }}
                      </a-tag>
                    </template>
                    <template v-else-if="column.key === 'coin'">
                      <a-tag color="gold">
                        <template #icon><gift-outlined /></template>
                        {{ record.coin || 0 }}
                      </a-tag>
                    </template>
                    <template v-else-if="column.key === 'skills'">
                      <a-space wrap>
                        <a-tag 
                          v-for="skill in record.skills" 
                          :key="skill" 
                          color="blue" 
                          size="small"
                        >
                          {{ skill }}
                        </a-tag>
                      </a-space>
                    </template>
                    <template v-else-if="column.key === 'action'">
                      <a-button type="primary" size="small" @click="navigateToChallenge(record.id)">
                        查看挑战
                      </a-button>
                    </template>
                  </template>
                </a-table>
              </div>
            </a-card>

            <!-- 技能标签 -->
            <a-card class="content-card" title="技能标签">
              <template #extra>
                <tags-outlined />
              </template>
              <a-empty v-if="!course.skills || course.skills.length === 0" description="暂无技能标签" />
              <div v-else class="skills-container">
                <a-space wrap>
                  <a-tag 
                    v-for="skill in course.skills" 
                    :key="skill.id || skill.skill_name" 
                    color="blue"
                  >
                    {{ skill.skill_name || skill }}
                  </a-tag>
                </a-space>
              </div>
            </a-card>

            <!-- 推荐实践 -->
            <a-card class="content-card" title="推荐实践">
              <template #extra>
                <book-outlined />
              </template>
              <a-spin :spinning="loadingRecommended">
                <a-empty v-if="!recommendedCourses.length" description="暂无推荐实践" />
                <div v-else class="recommended-courses">
                  <div class="course-grid">
                    <a-card 
                      v-for="item in recommendedCourses" 
                      :key="item.id"
                      class="recommended-course-card"
                      hoverable
                      :bodyStyle="{ padding: 0 }"
                      @click="navigateToCourse(item.id)"
                    >
                      <div class="rec-card-cover" :style="{ background: item.cover }">
                        <div class="cover-overlay"></div>
                      </div>
                      <div class="course-card-content">
                        <h3 class="course-card-title">{{ item.title }}</h3>
                        <div class="course-card-tags">
                          <a-tag size="small">{{ item.type }}</a-tag>
                          <a-tag size="small" color="blue">{{ item.level }}</a-tag>
                        </div>
                      </div>
                    </a-card>
                  </div>
                </div>
              </a-spin>
            </a-card>
          </div>
        </template>
        <a-result v-else status="warning" title="未找到课程" sub-title="您请求的微课不存在或已被删除"/>
      </a-spin>
    </div>

    <!-- 添加到课堂弹窗 -->
    <a-modal
      v-model:open="showAddToClassroomModal"
      title="添加到课堂"
      @ok="handleAddToClassroom"
      @cancel="showAddToClassroomModal = false"
      :confirm-loading="loadingClassrooms"
      width="600px"
    >
      <a-spin :spinning="loadingClassrooms">
        <a-empty v-if="!classrooms.length" description="暂无可选课堂" />
        <div v-else>
          <div class="form-section">
            <h4>选择课堂</h4>
            <a-radio-group v-model:value="selectedClassroom" class="classroom-list">
              <a-space direction="vertical" style="width: 100%">
                <a-radio
                  v-for="classroom in classrooms"
                  :key="classroom.id"
                  :value="classroom.id"
                >
                  <div class="classroom-item">
                    <div class="classroom-info">
                      <div class="classroom-name">{{ classroom.name }}</div>
                      <div class="classroom-meta">
                        <span>{{ classroom.teacherName }}</span>
                        <span>{{ classroom.studentCount }} 学生</span>
                        <span>创建于 {{ classroom.createdAt }}</span>
                      </div>
                    </div>
                  </div>
                </a-radio>
              </a-space>
            </a-radio-group>
          </div>
          
          <a-divider />
          
          <div class="form-section">
            <h4>同步选项</h4>
            <a-checkbox-group v-model:value="syncOptions" style="width: 100%">
              <a-space direction="vertical">
                <a-checkbox value="resources">同步实验文档</a-checkbox>
                <a-checkbox value="assessments">同步课程考核</a-checkbox>
              </a-space>
            </a-checkbox-group>
          </div>
        </div>
      </a-spin>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { getMicroCourseById, getClassrooms, getRecommendedMicroCourses, getPracticeTasks } from '../../../api/course';
import { techerClassRooms, addClassRoomPractice } from '../../../api/classrooms';
import { microList } from '@/api/cmaterial';
import type { MicroCourse, Classroom } from '../../../types/course';
import { message } from 'ant-design-vue';
import { 
  LikeOutlined,
  EyeOutlined,
  GiftOutlined,
  InfoCircleOutlined,
  SafetyOutlined,
  StarOutlined,
  TagsOutlined,
  BookOutlined,
  PlusOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '../../../stores/user';
import { microDetail } from '@/api/cmaterial';

const router = useRouter();
const route = useRoute();
const userStore = useUserStore(); // 使用用户状态管理
const courseId = route.params.id as string;
const course = ref<MicroCourse | null>(null);
const loading = ref(true);
const recommendedCourses = ref<MicroCourse[]>([]);
const loadingRecommended = ref(false);
const classrooms = ref<Classroom[]>([]);
const loadingClassrooms = ref(false);
const showAddToClassroomModal = ref(false);
const selectedClassroom = ref<string | null>(null);
const syncOptions = ref<string[]>(['resources']); // 默认选中同步实验文档
const activeTaskKeys = ref<string[]>([]);

// 任务表格列定义
const taskColumns = [
  {
    title: '序号',
    key: 'order',
    width: 80,
    align: 'center'
  },
  {
    title: '状态',
    key: 'status',
    width: 80,
    align: 'center'
  },
  {
    title: '任务标题',
    key: 'title',
    minWidth: 200
  },
  {
    title: '题型',
    key: 'type',
    width: 100,
    align: 'center'
  },
  {
    title: '金币',
    key: 'coin',
    width: 80,
    align: 'center'
  },
  {
    title: '技能标签',
    key: 'skills',
    width: 200
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    align: 'center'
  }
];

// 计算总金币数
const totalCoins = computed(() => {
  if (!course.value?.tasks) return 0;
  return course.value.tasks.reduce((total, task) => total + (task.coin || 0), 0);
});

// 任务类型颜色映射
const taskTypeColor = (type: string) => {
  const map: Record<string, string> = {
    'TRUE_FALSE': 'blue',
    'SINGLE_CHOICE': 'green',
    'MULTIPLE_CHOICE': 'cyan',
    'PRACTICE': 'orange'
  };
  return map[type] || 'gray';
};

// 任务类型文本映射
const taskTypeText = (type: string) => {
  const map: Record<string, string> = {
    'TRUE_FALSE': '判断题',
    'SINGLE_CHOICE': '单选题',
    'MULTIPLE_CHOICE': '多选题',
    'PRACTICE': '实践题'
  };
  return map[type] || '未知类型';
};

// 难度文本映射
const difficultyText = (difficulty: string) => {
  const map: Record<string, string> = {
    'beginner': '初级',
    'intermediate': '中级',
    'advanced': '高级',
    'BEGINNER': '初级',
    'INTERMEDIATE': '中级',
    'ADVANCED': '高级'
  };
  return map[difficulty] || difficulty || '未知';
};

// 导航到挑战详情页
const navigateToChallenge = (taskId: string) => {
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录');
    return;
  }
  router.push(`/course/challenge/${courseId}/${taskId}`);
};

// 导航到课程详情页
const navigateToCourse = (id: string) => {
  router.push(`/course/micro/${id}`);
};

// 添加到课堂
const handleAddToClassroom = async () => {
  if (!selectedClassroom.value || !course.value) return;

  // 检查登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录');
    return;
  }

  try {
    loadingClassrooms.value = true;
    
    // 调用添加课程到课堂的API
    await addClassRoomPractice({
      classroom_id: selectedClassroom.value,
      practice_id: course.value.id,
      sync_resources: syncOptions.value.includes('resources'),
      sync_assessments: syncOptions.value.includes('assessments')
    });
    
    message.success('实践课程已成功添加到课堂');
    showAddToClassroomModal.value = false;
    selectedClassroom.value = null;
    syncOptions.value = ['resources']; // 重置同步选项
  } catch (error) {
    console.error('添加到课堂失败:', error);
    message.error('添加到课堂失败，请重试');
  } finally {
    loadingClassrooms.value = false;
  }
};

onMounted(async () => {
  try {
    loading.value = true;
    await getMicroDetail();
    if (course.value) {
      // 加载推荐课程 - 使用相同分类或方向的其他实践
      loadingRecommended.value = true;
      await getRecommendedPractices();
    }
  } catch (error) {
    console.error('获取微课详情失败:', error);
  } finally {
    loading.value = false;
    loadingRecommended.value = false;
  }
});
const getMicroDetail = async () => {
	try {
	  const res = await microDetail(courseId);

	  // API返回的数据结构是: {code: 0000, message: success, data: {...}}
	  // 所以实际数据在 res.data 中
	  const data = res?.data;

	  // 将API响应数据映射为前端需要的格式
	  if (data && data.title) {
	    course.value = {
	      id: data.id?.toString() || '',
	      title: data.title || '',
	      cover: data.cover_url || '',
	      type: data.category || '',
	      level: data.difficulty === 'beginner' ? '初级' :
	             data.difficulty === 'intermediate' ? '中级' :
	             data.difficulty === 'advanced' ? '高级' : '初级',
	      popularity: data.popularity || 0,
	      views: data.views || 0,
	      direction: data.direction || '',
	      category: data.category || '',
	      intro: data.description || data.summary || '',
	      introduction: data.description || data.summary || '',
	      coins: data.coin || 0,
	      skills: data.skills || [],
	      tasks: []  // 初始为空，稍后获取
	    };
	    
	    // 获取关卡(tasks)列表，传入用户ID以获取完成状态
	    try {
	      const userId = userStore.userId || undefined;
	      const tasksRes = await getPracticeTasks(courseId, userId);
	      if (tasksRes?.data?.list) {
	        course.value.tasks = tasksRes.data.list.map((task: any) => {
	          // 解析skills JSON字符串
	          let skillsList: string[] = [];
	          if (task.skills) {
	            try {
	              skillsList = typeof task.skills === 'string' ? JSON.parse(task.skills) : task.skills;
	            } catch {
	              skillsList = [];
	            }
	          }
	          return {
	            id: task.id?.toString() || '',
	            title: task.title || '',
	            type: task.task_type || 'PRACTICE',
	            difficulty: task.difficulty || 'beginner',
	            coin: task.coin || 0,
	            skills: skillsList,
	            order_in_practice: task.order_in_practice || 1,
	            is_completed: task.is_completed || false,
	            completion_score: task.completion_score || 0,
	            passed_tests: task.passed_tests || 0,
	            total_tests: task.total_tests || 0
	          };
	        });
	      }
	    } catch (tasksErr) {
	      console.error('获取关卡列表失败:', tasksErr);
	    }
	  } else {
	    console.log('API返回数据无效:', data);
	    course.value = null;
	  }
	} catch (err) {
	  console.error('Error fetching micro detail:', err);
	  course.value = null;
	}
};


// 获取推荐实践
const getRecommendedPractices = async () => {
  try {
    const res = await microList({
      limit: 6,
      page: 1,
      direction: course.value?.direction, // 使用相同方向
      categories: course.value?.category // 使用相同分类
    });
    
    // 过滤掉当前课程，转换为前端格式
    const practices = res.list || [];
    recommendedCourses.value = practices
      .filter((practice: any) => practice.id !== parseInt(courseId))
      .slice(0, 6)
      .map((practice: any) => ({
        id: practice.id.toString(),
        title: practice.title,
        cover: practice.cover_url || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        type: practice.category || '实践',
        level: difficultyText(practice.difficulty) || '未知'
      }));
      
  } catch (error) {
    console.error('获取推荐实践失败:', error);
  }
};

// 打开添加到课堂弹窗时加载课堂列表
const fetchClassrooms = async () => {
  // 检查登录状态
  if (!userStore.isLoggedIn) {
    message.warning('请先登录');
    showAddToClassroomModal.value = false;
    return;
  }
  
  try {
    loadingClassrooms.value = true;
    
    // 调用真实的课堂列表API
    const response = await techerClassRooms({ 
      page: 1, 
      limit: 100,
      teacher_id: userStore.userId // 使用当前用户ID
    });
    
    // 根据API返回的数据格式调整
    const classroomList = response.data?.list || response.list || [];
    classrooms.value = classroomList.map((classroom: any) => ({
      id: classroom.id,
      name: classroom.name,
      teacherName: classroom.teacher_name || '未知教师',
      studentCount: classroom.student_count || 0,
      createdAt: classroom.created_at || classroom.createdAt || '未知'
    }));
  } catch (error) {
    console.error('获取课堂列表失败:', error);
    message.error('获取课堂列表失败');
  } finally {
    loadingClassrooms.value = false;
  }
};

// 监听弹窗打开
watch(showAddToClassroomModal, (val: boolean) => {
  if (val && classrooms.value.length === 0) {
    fetchClassrooms();
  }
});
</script>

<style scoped>
.detail-page {
  min-height: 100vh;
  background-color: var(--color-bg-1);
}

.content-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  min-height: 600px;
}

.course-header {
  display: flex;
  gap: 30px;
}

.course-info {
  flex: 1;
}

.course-title {
  font-size: 28px;
  font-weight: 500;
  margin-bottom: 16px;
  color: #000;
}

.course-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.course-stats {
  display: flex;
  gap: 20px;
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
}

.stat-item :deep(svg) {
  margin-right: 6px;
  font-size: 16px;
}

.action-buttons {
  margin-top: 20px;
}

.course-cover {
  width: 300px;
  height: 200px;
  overflow: hidden;
  border-radius: 4px;
  flex-shrink: 0;
  position: relative;
  background-size: cover !important;
  background-position: center !important;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.1);
}

.course-content {
  margin-top: 24px;
}

.content-card {
  margin-bottom: 24px;
}

.content-card :deep(.ant-card-head) {
  border-bottom: 1px solid #f0f0f0;
}

.content-card :deep(.ant-card-head-title) {
  font-size: 16px;
  font-weight: 500;
}

.introduction {
  line-height: 1.8;
  color: rgba(0, 0, 0, 0.65);
}

.tasks-container {
  margin-top: 10px;
}

.task-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.task-info {
  flex: 1;
}

.task-meta {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.task-description {
  margin-bottom: 12px;
  color: rgba(0, 0, 0, 0.65);
  line-height: 1.6;
}

.task-skills {
  display: flex;
  align-items: center;
  margin-top: 10px;
}

.task-skills .label {
  margin-right: 8px;
  color: rgba(0, 0, 0, 0.45);
}

.task-actions {
  margin-left: 20px;
}

.task-title-cell .task-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.task-title-cell .task-description {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  line-height: 1.4;
}

.skills-container {
  margin-top: 10px;
}

.recommended-courses {
  margin-top: 10px;
}

.course-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 20px;
}

.recommended-course-card {
  height: 220px;
  overflow: hidden;
  border-radius: 4px;
  cursor: pointer;
}

.rec-card-cover {
  height: 150px;
  position: relative;
  background-size: cover !important;
  background-position: center !important;
}

.course-card-content {
  padding: 12px;
}

.course-card-title {
  font-size: 16px;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.course-card-tags {
  display: flex;
  gap: 8px;
}

.classroom-list {
  max-height: 300px;
  overflow-y: auto;
}

.classroom-item {
  padding: 10px 0;
}

.classroom-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.classroom-meta {
  display: flex;
  gap: 15px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}

.form-section {
  margin-bottom: 16px;
}

.form-section h4 {
  margin-bottom: 12px;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

@media (max-width: 768px) {
  .course-header {
    flex-direction: column-reverse;
  }
  
  .course-cover {
    width: 100%;
    height: 180px;
    margin-bottom: 20px;
  }
  
  .course-meta {
    flex-wrap: wrap;
  }
  
  .task-content {
    flex-direction: column;
  }
  
  .task-actions {
    margin-left: 0;
    margin-top: 16px;
  }
  
  .course-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 576px) {
  .course-grid {
    grid-template-columns: 1fr;
  }
  
  .classroom-meta {
    flex-direction: column;
    gap: 5px;
  }
}
</style> 