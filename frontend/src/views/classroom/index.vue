<template>
  <div class="classroom-page">
    <!-- 顶部横幅 -->
    <div class="hero-banner">
      <div class="banner-content">
        <div class="banner-text">
          <h1 class="banner-title">成就未来 数字人才</h1>
          <p class="banner-subtitle">{{ userRole === 'teacher' ? '管理您的课堂，发布课程、查看进度、评阅作业' : '探索数据世界，开启学习之旅' }}</p>
        </div>
        <div class="banner-stats" v-if="userRole === 'teacher' || userRole === 'admin'">
          <div class="stat-item">
            <span class="stat-value">{{ totalClassrooms }}</span>
            <span class="stat-label">课堂总数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ ongoingCount }}</span>
            <span class="stat-label">正在进行</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ totalStudents }}</span>
            <span class="stat-label">学生总数</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 页面内容区 -->
    <div class="page-content">

    <!-- 课堂类型切换 -->
    <div class="classroom-tabs">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="ongoing" tab="正在上课">
          <div class="tab-content">
            <div class="action-bar" v-if="userRole === 'teacher' || userRole === 'admin'">
              <a-button type="primary" @click="showCreateModal = true">
                <template #icon><plus-outlined /></template>
                创建课堂
              </a-button>
            </div>
            <a-spin :spinning="classroomStore.loading.ongoing">
              <template v-if="classroomStore.classrooms.ongoing.length > 0">
                <a-row :gutter="[16, 16]">
                  <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="classroom in classroomStore.classrooms.ongoing" :key="classroom.id">
                    <ClassroomCard 
                      :classroom="classroom" 
                      :status="'正在上课'" 
                      :is-editable="userRole === 'teacher' || userRole === 'admin'"
                      @delete="handleDeleteDropdown"
                    />
                  </a-col>
                </a-row>
              </template>
              <a-empty v-else :description="userRole === 'teacher' ? '暂无正在上课的课堂，可开始创建课堂' : '暂无正在上课的课堂'" />
            </a-spin>
          </div>
        </a-tab-pane>
        <a-tab-pane key="upcoming" tab="未开始">
          <div class="tab-content">
            <div class="action-bar" v-if="userRole === 'teacher' || userRole === 'admin'">
              <a-button type="primary" @click="showCreateModal = true">
                <template #icon><plus-outlined /></template>
                创建课堂
              </a-button>
            </div>
            <a-spin :spinning="classroomStore.loading.upcoming">
              <template v-if="classroomStore.classrooms.upcoming.length > 0">
                <a-row :gutter="[16, 16]">
                  <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="classroom in classroomStore.classrooms.upcoming" :key="classroom.id">
                    <ClassroomCard 
                      :classroom="classroom" 
                      :status="'未开始'" 
                      :is-editable="userRole === 'teacher' || userRole === 'admin'"
                      @delete="handleDeleteDropdown"
                    />
                  </a-col>
                </a-row>
              </template>
              <a-empty v-else description="暂无未开始的课堂" />
            </a-spin>
          </div>
        </a-tab-pane>
        <a-tab-pane key="past" tab="历史课堂">
          <div class="tab-content">
            <a-spin :spinning="classroomStore.loading.past">
              <template v-if="classroomStore.classrooms.past.length > 0">
                <a-row :gutter="[16, 16]">
                  <a-col :xs="24" :sm="12" :md="8" :lg="6" v-for="classroom in classroomStore.classrooms.past" :key="classroom.id">
                    <ClassroomCard 
                      :classroom="classroom" 
                      :status="'已结束'" 
                      :is-editable="false"
                      @delete="handleDeleteDropdown"
                    />
                  </a-col>
                </a-row>
              </template>
              <a-empty v-else description="暂无历史课堂" />
            </a-spin>
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    </div><!-- 结束 page-content -->

    <!-- 创建课堂弹窗 - 仅教师和管理员可见 -->
    <a-modal
      v-if="userRole === 'teacher' || userRole === 'admin'"
      v-model:open="showCreateModal"
      title="创建课堂"
      @ok="handleCreateClassroom"
      :confirmLoading="classroomStore.loading.create"
      width="600px"
    >
      <a-form :model="newClassroom" :rules="rules" ref="formRef" layout="vertical">
        <a-form-item name="name" label="课堂名称">
          <a-input v-model:value="newClassroom.name" placeholder="请输入课堂名称" />
        </a-form-item>
        <a-form-item name="description" label="课堂描述">
          <a-textarea v-model:value="newClassroom.description" placeholder="请输入课堂描述" :rows="4" />
        </a-form-item>
        <a-form-item name="dateRange" label="起止时间">
          <a-range-picker 
            v-model:value="newClassroom.dateRange" 
            style="width: 100%"
            show-time 
            format="YYYY-MM-DD HH:mm"
          />
        </a-form-item>
        <a-form-item name="credits" label="学分">
          <a-input-number v-model:value="newClassroom.credits" :min="1" :max="100" style="width: 100%" />
        </a-form-item>
        <a-form-item name="semester" label="学期">
          <a-input v-model:value="calculatedSemester" disabled placeholder="根据开始时间自动生成" />
        </a-form-item>
        <a-form-item name="addStudents" label="添加学生">
          <a-checkbox v-model:checked="newClassroom.addStudents">
            添加学生至本课堂
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, computed } from 'vue';
import { message } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import { useUserStore } from '../../stores/user';
import type { UserRole } from '../../stores/user';
import { useClassroomStore } from '../../stores/classroom';
import ClassroomCard from '../../components/classroom/ClassroomCard.vue';
import dayjs from 'dayjs';
import type { ClassroomDetail } from '@/types/classroom';
import { addClassRoom, deleteClassroom } from '@/api/classrooms';


// 导入状态管理
const userStore = useUserStore();
const classroomStore = useClassroomStore();

// 获取当前用户角色
const userRole = computed<UserRole>(() => userStore.userInfo.role as UserRole || 'student');

// 获取角色文本
const getRoleText = (role: string) => {
  switch (role) {
    case 'student': return '学生';
    case 'teacher': return '教师';
    case 'admin': return '管理员';
    default: return '未知';
  }
};

// 获取角色类型颜色
const getRoleType = (role: string) => {
  switch (role) {
    case 'student': return 'info';
    case 'teacher': return 'success';
    case 'admin': return 'warning';
    default: return 'info';
  }
};

// 统计数据
const totalClassrooms = computed(() => {
  return classroomStore.classrooms.ongoing.length +
         classroomStore.classrooms.upcoming.length +
         classroomStore.classrooms.past.length;
});

const ongoingCount = computed(() => classroomStore.classrooms.ongoing.length);

const totalStudents = computed(() => {
  let count = 0;
  [...classroomStore.classrooms.ongoing, ...classroomStore.classrooms.upcoming].forEach(c => {
    count += c.studentCount || c.student_count || 0;
  });
  return count;
});

// Tab激活状态
const activeTab = ref('ongoing');

// 创建课堂相关
const showCreateModal = ref(false);
const formRef = ref<FormInstance>();
const newClassroom = reactive<{
  name: string;
  description: string;
  dateRange: any[];
  credits: number;
  addStudents: boolean;
}>({
  name: '',
  description: '',
  dateRange: [],
  credits: 1,
  addStudents: false
});

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入课堂名称', trigger: 'blur' }],
  dateRange: [{ required: true, type: 'array', message: '请选择起止时间', trigger: 'change' }],
  credits: [{ required: true, type: 'number', message: '请输入学分', trigger: 'change' }]
};

// 计算学期
const calculatedSemester = computed(() => {
  if (!newClassroom.dateRange || newClassroom.dateRange.length === 0) {
    return '';
  }
  const startDate = dayjs(newClassroom.dateRange[0]);
  const year = startDate.year();
  const month = startDate.month() + 1;
  const day = startDate.date();
  
  // 7月1日之前为春季，7月1日及之后为秋季
  if (month < 7 || (month === 7 && day < 1)) {
    return `${year}年春季`;
  } else {
    return `${year}年秋季`;
  }
});

// 监听Tab切换，加载对应数据
watch(activeTab, (val) => {
  const status = val as 'ongoing' | 'upcoming' | 'past';
  if (userRole.value === 'student') {
    // 对于学生，一次性加载所有状态的数据
    if (classroomStore.classrooms.ongoing.length === 0 &&
        classroomStore.classrooms.upcoming.length === 0 &&
        classroomStore.classrooms.past.length === 0) {
      const studentId = userStore.userId?.toString();
      classroomStore.fetchClassrooms('ongoing', userRole.value, studentId);
    }
  } else {
    // 对于教师，按需加载
    if (classroomStore.classrooms[status].length === 0) {
      classroomStore.fetchClassrooms(status, userRole.value);
    }
  }
});

// 创建课堂
const handleCreateClassroom = () => {
  formRef.value?.validate().then(async () => {
    try {
      if (!newClassroom.dateRange || newClassroom.dateRange.length !== 2) {
        message.error('请选择起止时间');
        return;
      }

      const classroom: Partial<ClassroomDetail> = {
        name: newClassroom.name,
        description: newClassroom.description,
        startDate: dayjs(newClassroom.dateRange[0]).format('YYYY-MM-DD HH:mm:ss'),
        endDate: dayjs(newClassroom.dateRange[1]).format('YYYY-MM-DD HH:mm:ss'),
        credits: newClassroom.credits,
        teacherName: userStore.userInfo?.username || '当前教师',
        teacherId: userStore.userInfo?.id || 'currentTeacher',
      };

      postAdd(classroom);
      
    } catch (error) {
      console.error('创建课堂失败:', error);
      message.error('创建课堂失败，请稍后重试');
    }
  });
};
const postAdd = async (classroom: any) => {
	try {
	  await addClassRoom(classroom);
	  message.success('创建课堂成功');
	  showCreateModal.value = false;
	  
	  // 重载课堂数据，刷新处于“正在上课/未开始”的列表
	  if (userRole.value === 'teacher' || userRole.value === 'admin') {
	    classroomStore.fetchClassrooms('ongoing', userRole.value);
	    classroomStore.fetchClassrooms('upcoming', userRole.value);
	  }

	  // 重置表单
	  newClassroom.name = '';
	  newClassroom.description = '';
	  newClassroom.dateRange = [];
	  newClassroom.credits = 1;
	  newClassroom.addStudents = false;
	} catch (err) {
	}
}
// 初始化
onMounted(() => {
  // 默认加载正在上课的课堂
  if (userRole.value === 'student') {
    // 对于学生，一次性加载所有状态的数据
    const studentId = userStore.userId?.toString();
    classroomStore.fetchClassrooms('ongoing', userRole.value, studentId);
  } else {
    // 对于教师，按需加载
    classroomStore.fetchClassrooms('ongoing', userRole.value);
  }
});
</script>

<style scoped>
.classroom-page {
  min-height: 100vh;
  background: #f0f2f5;
}

/* 顶部横幅 */
.hero-banner {
  background: linear-gradient(135deg, #1890ff 0%, #0050c8 100%);
  color: white;
  padding: 40px 24px;
  margin-bottom: 0;
}

.banner-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.banner-text {
  flex: 1;
}

.banner-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
  letter-spacing: 2px;
}

.banner-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.banner-stats {
  display: flex;
  gap: 40px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: 14px;
  opacity: 0.85;
  margin-top: 4px;
}

/* 页面内容区 */
.page-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.classroom-tabs {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.action-bar {
  margin-bottom: 16px;
  text-align: right;
}

.tab-content {
  padding: 8px 0;
  min-height: 300px;
}

/* 响应式 */
@media (max-width: 768px) {
  .banner-content {
    flex-direction: column;
    text-align: center;
    gap: 24px;
  }

  .banner-title {
    font-size: 24px;
  }

  .banner-stats {
    gap: 24px;
  }

  .stat-value {
    font-size: 28px;
  }
}
</style> 