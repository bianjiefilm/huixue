<template>
  <PageShell max-width="wide" class="training-homework-page">
    <PageHeaderBar
      :title="trainingTitle || '实训作业'"
      subtitle="作业列表与评分"
      show-back
      :back-to="`/classroom/${classroomId}/training/${trainingId}`"
    />

    <a-spin :spinning="loading">
      <!-- 作业统计 -->
      <a-row :gutter="16" class="stats-row">
        <a-col :span="6">
          <a-card size="small">
            <div class="stat-item">
              <div class="stat-value">{{ totalCount }}</div>
              <div class="stat-label">作业总数</div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <div class="stat-item">
              <div class="stat-value">{{ stats.graded || 0 }}</div>
              <div class="stat-label">已评分</div>
            </div>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card size="small">
            <div class="stat-item">
              <div class="stat-value">{{ stats.not_graded || 0 }}</div>
              <div class="stat-label">未评分</div>
            </div>
          </a-card>
        </a-col>
      </a-row>

      <!-- 作业列表 -->
      <a-card class="table-card">
        <div class="homework-header">
          <a-input-search
            v-model:value="searchText"
            placeholder="搜索学生姓名或学号"
            style="width: 250px"
            @search="onSearch"
            allow-clear
          />
        </div>

        <a-table
          :columns="columns"
          :data-source="filteredHomework"
          :loading="loading"
          :pagination="{
            current: currentPage,
            pageSize: 10,
            total: totalCount,
            showTotal: (total: number) => `共 ${total} 条`,
            onChange: (page: number) => {
              currentPage = page;
              fetchHomework();
            }
          }"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'name'">
              <div class="student-cell">
                <a-avatar :size="28">
                  <template #icon><UserOutlined /></template>
                </a-avatar>
                <div>
                  <div>{{ record.student_name }}</div>
                  <div class="student-no">{{ record.student_no }}</div>
                </div>
              </div>
            </template>
            <template v-if="column.key === 'status'">
              <a-tag :color="getStatusColor(record.submission_status)">
                {{ getStatusText(record.submission_status) }}
              </a-tag>
            </template>
            <template v-if="column.key === 'score'">
              <span
                v-if="record.overall_score"
                :class="{ 'score-highlight': record.overall_score >= 90 }"
              >
                {{ record.overall_score }}
              </span>
              <span v-else class="muted">-</span>
            </template>
            <template v-if="column.key === 'action'">
              <a-space>
                <a-button type="link" @click="viewHomework(record)">查看详情</a-button>
                <a-button type="link" @click="openCommentModal(record)">
                  {{ record.overall_score ? '修改评分' : '评分' }}
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
          <a-input-number v-model:value="commentForm.score" :min="0" :max="100" style="width: 100%" />
        </a-form-item>
        <a-form-item label="点评意见">
          <a-textarea
            v-model:value="commentForm.comment"
            :rows="4"
            placeholder="请输入点评意见"
          />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="commentForm.isExcellent"> 设为优秀作业 </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import { UserOutlined } from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const route = useRoute();
const router = useRouter();

const classroomId = computed(() => route.params.classroomId as string);
const trainingId = computed(() => route.params.trainingId as string);
const trainingTitle = ref('');

const loading = ref(false);
const homeworkList = ref<any[]>([]);
const totalCount = ref(0);
const currentPage = ref(1);
const searchText = ref('');
const stats = ref<any>({});

const commentModalVisible = ref(false);
const commentForm = ref({ score: null as number | null, comment: '', isExcellent: false });
const currentStudent = ref<any>(null);
const submittingComment = ref(false);

const columns = [
  { title: '学生', key: 'name' },
  { title: '提交状态', key: 'status' },
  { title: '分数', key: 'score' },
  { title: '最后提交时间', key: 'last_submission_at' },
  { title: '操作', key: 'action', width: 180 }
];

const filteredHomework = computed(() => {
  if (!searchText.value) return homeworkList.value;
  const kw = searchText.value.toLowerCase();
  return homeworkList.value.filter(
    (h) =>
      (h.student_name || '').toLowerCase().includes(kw) ||
      (h.student_no || '').toLowerCase().includes(kw)
  );
});

function getStatusColor(status: string) {
  const map: Record<string, string> = {
    submitted: 'green',
    late_submitted: 'orange'
  };
  return map[status] || 'default';
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    submitted: '已提交',
    late_submitted: '补交'
  };
  return map[status] || status;
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return '-';
  return dateStr.replace('T', ' ').substring(0, 19);
}

async function fetchHomework() {
  loading.value = true;
  try {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      page_size: '20'
    });
    if (searchText.value) params.set('keyword', searchText.value);

    const response = await fetch(
      `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/homework?${params}`
    );
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      homeworkList.value = (result.data.list || []).map((h: any) => ({
        ...h,
        last_submission_at: formatDate(h.last_submission_at)
      }));
      totalCount.value = result.data.total || 0;
      if (result.data.stats) stats.value = result.data.stats;
      if (result.data.training_title) {
        trainingTitle.value = result.data.training_title;
      }
    } else {
      message.error(result.message || '获取作业列表失败');
    }
  } catch (error) {
    console.error('获取作业列表失败:', error);
    message.error('获取作业列表失败');
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
      fetchHomework();
    } else {
      message.error(result.message || '评分失败');
    }
  } catch (error) {
    message.error('评分失败');
  } finally {
    submittingComment.value = false;
  }
}

function onSearch() {
  currentPage.value = 1;
  fetchHomework();
}

onMounted(() => {
  fetchHomework();
});
</script>

<style scoped>
.stats-row {
  margin-bottom: var(--hx-space-4);
}

.table-card {
  margin-bottom: var(--hx-space-4);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: var(--hx-font-size-lg);
  font-weight: bold;
  color: var(--hx-color-primary);
}

.stat-label {
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
  margin-top: var(--hx-space-1);
}

.homework-header {
  margin-bottom: var(--hx-space-4);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-cell {
  display: flex;
  align-items: center;
  gap: var(--hx-space-2);
}

.student-no {
  font-size: var(--hx-font-size-xs);
  color: var(--hx-color-text-tertiary);
}

.muted {
  color: var(--hx-color-text-tertiary);
}

.score-highlight {
  color: var(--hx-color-success);
  font-weight: bold;
}
</style>
