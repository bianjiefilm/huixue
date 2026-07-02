<template>
  <div class="training-course-management">
    <a-page-header title="实训课程管理" :ghost="false" />
    
    <div class="training-course-container">
      <a-row :gutter="16">
        <!-- 左侧分类树 -->
        <a-col :span="6">
          <a-card title="行业分类" :bordered="false" class="category-tree-card">
            <a-spin :spinning="loading.trainingCourseCategories">
              <a-tree
                v-model:expandedKeys="expandedKeys"
                v-model:selectedKeys="selectedKeys"
                :tree-data="trainingCourseCategories"
                @select="onSelectCategory"
              />
            </a-spin>
          </a-card>
        </a-col>
        
        <!-- 右侧课程列表 -->
        <a-col :span="18">
          <a-card :bordered="false" class="course-list-card">
            <!-- 顶部搜索和筛选 -->
            <div class="search-bar">
              <a-input-search
                v-model:value="keyword"
                placeholder="搜索课程名称、教师或院校"
                style="width: 300px"
                @search="onSearch"
                enter-button
              />
              <a-space>
                <a-button @click="resetFilters">
                  <template #icon><ReloadOutlined /></template>
                  重置筛选
                </a-button>
              </a-space>
            </div>
            
            <!-- 课程列表 -->
            <a-table
              :loading="loading.trainingCourses"
              :dataSource="filteredTrainingCourses"
              :columns="columns"
              :pagination="{ pageSize: 10, showTotal: (total: number) => `共 ${total} 条` }"
              :rowKey="(record: any) => record.id"
            >
              <!-- 封面列 -->
              <template #bodyCell="{ column, record }">
                <template v-if="column.dataIndex === 'cover'">
                  <img :src="record.cover" class="course-cover" alt="课程封面" />
                </template>
                
                <!-- 状态列 -->
                <template v-else-if="column.dataIndex === 'status'">
                  <a-tag :color="record.status === 'published' ? 'green' : 'orange'">
                    {{ record.status === 'published' ? '已发布' : '未发布' }}
                  </a-tag>
                </template>
                
                <!-- 操作列 -->
                <template v-else-if="column.dataIndex === 'action'">
                  <a-space>
                    <a-button type="link" size="small" @click="viewCourse(record)">查看</a-button>
                    <a-button 
                      v-if="record.status === 'published'" 
                      type="link" 
                      size="small" 
                      @click="showUnpublishConfirm(record)"
                    >
                      下架
                    </a-button>
                    <a-button 
                      v-else 
                      type="link" 
                      size="small" 
                      @click="showPublishConfirm(record)"
                    >
                      发布
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { message, Modal } from 'ant-design-vue';
import { useAdminCourseStore } from '@/stores/admin-course';
import { CourseStatus, type TrainingCourse } from '@/types/admin';

const router = useRouter();
const adminCourseStore = useAdminCourseStore();

// 加载状态和数据
const loading = computed(() => adminCourseStore.loading);
const trainingCourseCategories = computed(() => adminCourseStore.trainingCourseCategories);
const filteredTrainingCourses = computed(() => adminCourseStore.filteredTrainingCourses);

// 分类树状态
const expandedKeys = ref<string[]>(['root']);
const selectedKeys = ref<string[]>(['root']);

// 搜索关键词
const keyword = ref('');

// 表格列定义
const columns = [
  {
    title: '封面',
    dataIndex: 'cover',
    width: 100,
  },
  {
    title: '课程名称',
    dataIndex: 'title',
    ellipsis: true,
    sorter: (a: TrainingCourse, b: TrainingCourse) => a.title.localeCompare(b.title),
  },
  {
    title: '教师',
    dataIndex: 'teacher',
    width: 120,
    sorter: (a: TrainingCourse, b: TrainingCourse) => a.teacher.localeCompare(b.teacher),
  },
  {
    title: '所属院校',
    dataIndex: 'university',
    width: 180,
    ellipsis: true,
  },
  {
    title: '所属行业',
    dataIndex: 'industry',
    width: 120,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
    filters: [
      { text: '已发布', value: CourseStatus.PUBLISHED },
      { text: '未发布', value: CourseStatus.UNPUBLISHED },
    ],
    onFilter: (value: string, record: TrainingCourse) => record.status === value,
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    width: 170,
    sorter: (a: TrainingCourse, b: TrainingCourse) =>
      new Date(a.updatedAt).getTime() - new Date(b.updatedAt).getTime(),
    defaultSortOrder: 'descend',
    customRender: ({ text }: { text: string }) => text ? new Date(text).toLocaleString('zh-CN') : '-',
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150,
    fixed: 'right',
  },
];

// 页面加载时获取数据
onMounted(async () => {
  if (trainingCourseCategories.value.length === 0) {
    await adminCourseStore.fetchTrainingCourseCategories();
  }
  await adminCourseStore.fetchTrainingCourses();
});

// 选择分类
const onSelectCategory = (selectedKeys: string[]) => {
  if (selectedKeys.length > 0) {
    adminCourseStore.setFilter('training', 'categoryKey', selectedKeys[0]);
  }
};

// 搜索
const onSearch = () => {
  adminCourseStore.setFilter('training', 'keyword', keyword.value);
};

// 重置筛选条件
const resetFilters = () => {
  keyword.value = '';
  selectedKeys.value = ['root'];
  adminCourseStore.resetFilters('training');
};

// 查看课程详情
const viewCourse = (course: TrainingCourse) => {
  router.push(`/admin/course/detail/${course.id}`);
};

// 下架课程确认
const showUnpublishConfirm = (course: TrainingCourse) => {
  Modal.confirm({
    title: '确认下架课程',
    content: `确定要下架课程 "${course.title}" 吗？下架后该课程将不再公开展示。`,
    okText: '确定',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      const success = await adminCourseStore.unpublishCourse(course.id);
      if (success) {
        message.success('课程已成功下架');
      } else {
        message.error('下架课程失败');
      }
    },
  });
};

// 发布课程确认
const showPublishConfirm = (course: TrainingCourse) => {
  Modal.confirm({
    title: '确认发布课程',
    content: `确定要发布课程 "${course.title}" 吗？发布后该课程将对所有用户可见。`,
    okText: '确定',
    okType: 'primary',
    cancelText: '取消',
    async onOk() {
      const success = await adminCourseStore.publishCourse(course.id);
      if (success) {
        message.success('课程已成功发布');
      } else {
        message.error('发布课程失败');
      }
    },
  });
};
</script>

<style scoped>
.training-course-management {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.training-course-container {
  flex: 1;
  margin-top: 16px;
}

.category-tree-card {
  height: 100%;
  min-height: 600px;
}

.course-list-card {
  height: 100%;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.course-cover {
  width: 80px;
  height: 45px;
  object-fit: cover;
  border-radius: 4px;
}
</style> 