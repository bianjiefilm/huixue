<template>
  <div class="training-grades-page">
    <div class="content-container">
      <div class="back-link">
        <a-button type="link" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回实训详情
        </a-button>
      </div>

      <div class="training-header">
        <div class="training-info">
          <h1 class="training-title">{{ trainingTitle || '实训成绩' }}</h1>
        </div>
      </div>

      <a-spin :spinning="loading">
        <!-- 统计卡片 -->
        <a-card class="stats-card">
          <a-row :gutter="16">
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_students || 0 }}</div>
                <div class="stat-label">总学生数</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.submitted || 0 }}</div>
                <div class="stat-label">已提交</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.late_submitted || 0 }}</div>
                <div class="stat-label">补交</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.graded || 0 }}</div>
                <div class="stat-label">已评分</div>
              </div>
            </a-col>
          </a-row>
          <a-row :gutter="16" style="margin-top: 16px;">
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.not_submitted || 0 }}</div>
                <div class="stat-label">未提交</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-item">
                <div class="stat-value">{{ stats.not_graded || 0 }}</div>
                <div class="stat-label">未评分</div>
              </div>
            </a-col>
          </a-row>
        </a-card>

        <!-- 成绩表格 -->
        <a-card class="grades-card">
          <div class="grades-header">
            <div class="grades-filter">
              <a-input-search
                v-model:value="searchText"
                placeholder="搜索学生姓名或学号"
                style="width: 250px"
                @search="onSearch"
                allow-clear
              />
            </div>
            <div class="grades-export">
              <a-button type="primary" @click="handleExport">
                <template #icon><download-outlined /></template>
                导出成绩
              </a-button>
            </div>
          </div>

          <a-table
            :columns="columns"
            :data-source="filteredStudents"
            :loading="loading"
            :pagination="{
              current: currentPage,
              pageSize: 10,
              total: totalCount,
              showTotal: (total: number) => `共 ${total} 条记录`,
              onChange: (page: number) => {
                currentPage = page;
                fetchGrades();
              }
            }"
            row-key="id"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <a-avatar :size="28" :src="record.avatar">
                    <template #icon><UserOutlined /></template>
                  </a-avatar>
                  <div>
                    <div>{{ record.student_name }}</div>
                    <div style="font-size: 12px; color: #999;">{{ record.student_no }}</div>
                  </div>
                </div>
              </template>
              <template v-if="column.key === 'submission_status'">
                <a-tag :color="getStatusColor(record.submission_status)">
                  {{ getStatusText(record.submission_status) }}
                </a-tag>
              </template>
              <template v-if="column.key === 'overall_score'">
                <span v-if="record.overall_score !== null && record.overall_score > 0" :class="{'score-highlight': record.overall_score >= 90}">
                  {{ record.overall_score }}
                </span>
                <span v-else style="color: #999;">-</span>
              </template>
              <template v-if="column.key === 'action'">
                <a-space>
                  <a-button
                    type="link"
                    :disabled="record.submission_status !== 'submitted' && record.submission_status !== 'late_submitted'"
                    @click="viewHomework(record)"
                  >
                    查看作业
                  </a-button>
                  <a-button
                    type="link"
                    @click="openCommentModal(record)"
                  >
                    {{ record.overall_score && record.overall_score > 0 ? '修改评分' : '评分' }}
                  </a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>
      </a-spin>

      <!-- 评分模态框 -->
      <a-modal
        v-model:open="commentModalVisible"
        :title="`为 ${currentStudent?.student_name || ''} 评分`"
        @ok="submitComment"
        :confirm-loading="submittingComment"
        width="500px"
      >
        <a-form layout="vertical">
          <a-form-item label="分数">
            <a-input-number
              v-model:value="commentForm.score"
              :min="0"
              :max="100"
              style="width: 100%"
            />
          </a-form-item>
          <a-form-item label="点评意见">
            <a-textarea
              v-model:value="commentForm.comment"
              :rows="4"
              placeholder="请输入点评意见"
            />
          </a-form-item>
          <a-form-item>
            <a-checkbox v-model:checked="commentForm.isExcellent">
              设为优秀作业
            </a-checkbox>
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  DownloadOutlined,
  UserOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const classroomId = computed(() => route.params.classroomId as string);
const trainingId = computed(() => route.params.trainingId as string);
const trainingTitle = ref('');

const loading = ref(false);
const students = ref<any[]>([]);
const totalCount = ref(0);
const currentPage = ref(1);
const searchText = ref('');
const stats = ref<any>({});

const commentModalVisible = ref(false);
const commentForm = ref({ score: null as number | null, comment: '', isExcellent: false });
const currentStudent = ref<any>(null);
const submittingComment = ref(false);

const columns = [
  { title: '学生', key: 'name', dataIndex: 'student_name' },
  { title: '提交状态', key: 'submission_status', dataIndex: 'submission_status' },
  { title: '分数', key: 'overall_score', dataIndex: 'overall_score' },
  { title: '最后提交时间', key: 'last_submission_at', dataIndex: 'last_submission_at' },
  { title: '操作', key: 'action', width: 200 }
];

const filteredStudents = computed(() => {
  if (!searchText.value) return students.value;
  const kw = searchText.value.toLowerCase();
  return students.value.filter(s =>
    (s.student_name || '').toLowerCase().includes(kw) ||
    (s.student_no || '').toLowerCase().includes(kw)
  );
});

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    'submitted': 'green',
    'late_submitted': 'orange',
    'in_progress': 'blue',
    'not_started': 'default',
    'not_submitted': 'red'
  };
  return map[status] || 'default';
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    'submitted': '已提交',
    'late_submitted': '补交',
    'in_progress': '进行中',
    'not_started': '未开始',
    'not_submitted': '未提交'
  };
  return map[status] || status;
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-';
  return dateStr.replace('T', ' ').substring(0, 19);
}

async function fetchGrades() {
  loading.value = true;
  try {
    const teacherId = userStore.userInfo?.id;
    if (!teacherId) {
      message.error('无法获取教师ID');
      return;
    }
    const params = new URLSearchParams({
      teacher_id: String(teacherId),
      page: String(currentPage.value),
      page_size: '20'
    });
    if (searchText.value) params.set('keyword', searchText.value);

    const response = await fetch(
      `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/grades?${params}`
    );
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      students.value = (result.data.list || []).map((s: any) => ({
        ...s,
        last_submission_at: formatDate(s.last_submission_at)
      }));
      totalCount.value = result.data.total || 0;
      stats.value = result.data.stats || {};
      if (result.data.training_title) {
        trainingTitle.value = result.data.training_title;
      }
    } else {
      message.error(result.message || '获取成绩失败');
    }
  } catch (error) {
    console.error('获取实训成绩失败:', error);
    message.error('获取实训成绩失败');
  } finally {
    loading.value = false;
  }
}

function viewHomework(record: any) {
  router.push(`/classroom/submission/${record.id}`);
}

function openCommentModal(record: any) {
  currentStudent.value = record;
  commentForm.value = {
    score: record.overall_score || null,
    comment: record.teacher_feedback || '',
    isExcellent: record.is_excellent_work || false
  };
  commentModalVisible.value = true;
}

async function submitComment() {
  if (commentForm.value.score === null) {
    message.warning('请输入分数');
    return;
  }
  submittingComment.value = true;
  try {
    const response = await fetch(
      `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/grade/${currentStudent.value.student_id}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          score: commentForm.value.score,
          feedback: commentForm.value.comment
        })
      }
    );
    const result = await response.json();
    if (result.code === '0000') {
      message.success('评分成功');
      commentModalVisible.value = false;
      fetchGrades();
    } else {
      message.error(result.message || '评分失败');
    }
  } catch (error) {
    console.error('评分失败:', error);
    message.error('评分失败');
  } finally {
    submittingComment.value = false;
  }
}

function handleExport() {
  message.info('导出功能开发中');
}

function goBack() {
  router.push(`/classroom/${classroomId.value}/training/${trainingId.value}`);
}

function onSearch() {
  currentPage.value = 1;
  fetchGrades();
}

onMounted(() => {
  fetchGrades();
});
</script>

<style scoped>
.training-grades-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
.content-container {
  background: #fff;
  border-radius: 2px;
  padding: 24px;
}
.back-link {
  margin-bottom: 16px;
}
.training-header {
  margin-bottom: 24px;
}
.training-title {
  font-size: 24px;
  margin: 0;
}
.stats-card {
  margin-bottom: 16px;
}
.stat-item {
  text-align: center;
}
.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #1890ff;
}
.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}
.grades-card {
  margin-bottom: 16px;
}
.grades-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.score-highlight {
  color: #52c41a;
  font-weight: bold;
}
</style>
