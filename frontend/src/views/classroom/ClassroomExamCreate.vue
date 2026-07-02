<template>
  <div class="classroom-exam-create-page">
    <div class="content-container">
      <div class="back-link">
        <a-button type="link" @click="goBack">
          <template #icon><arrow-left-outlined /></template>
          返回考试列表
        </a-button>
      </div>

      <div class="page-header">
        <h1 class="page-title">创建考试</h1>
        <p class="page-subtitle">选择试卷来源，为课堂创建一场考试</p>
      </div>

      <a-spin :spinning="paperLoading">
        <a-card class="create-options-card">
          <div class="options-grid">
            <!-- 从试卷库选择 -->
            <div class="option-card" @click="showPaperSelector = true">
              <div class="option-icon">
                <folder-outlined />
              </div>
              <div class="option-title">从试卷库选择</div>
              <div class="option-desc">从已有试卷中选择，快速创建考试</div>
            </div>

            <!-- 新建试卷 -->
            <div class="option-card" @click="handleCreateNewPaper">
              <div class="option-icon">
                <plus-circle-outlined />
              </div>
              <div class="option-title">新建试卷</div>
              <div class="option-desc">创建新试卷，编辑后发布考试</div>
            </div>
          </div>
        </a-card>
      </a-spin>

      <!-- 选择试卷弹窗 -->
      <a-modal
        v-model:open="showPaperSelector"
        title="选择试卷"
        width="600px"
        @ok="confirmSelectPaper"
        :confirm-loading="createExamLoading"
        :ok-text="'确认创建'"
      >
        <a-form layout="vertical">
          <a-form-item label="考试名称" required>
            <a-input
              v-model:value="examForm.name"
              placeholder="请输入考试名称"
              :maxlength="50"
            />
          </a-form-item>
          <a-form-item label="选择试卷" required>
            <a-select
              v-model:value="examForm.paperId"
              placeholder="请选择试卷"
              :loading="paperLoading"
              size="large"
            >
              <a-select-option v-for="paper in paperOptions" :key="paper.value" :value="paper.value">
                {{ paper.label }}
              </a-select-option>
            </a-select>
          </a-form-item>
          <div v-if="paperOptions.length === 0 && !paperLoading" style="text-align: center; color: #999;">
            暂无试卷，请先创建试卷
          </div>
        </a-form>
      </a-modal>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  FolderOutlined,
  PlusCircleOutlined
} from '@ant-design/icons-vue';
import { getPaperList, createExamFromPaper } from '@/api/exam';
import { useUserStore } from '@/stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const classroomId = route.params.classroomId as string;

const showPaperSelector = ref(false);
const paperLoading = ref(false);
const createExamLoading = ref(false);
const paperOptions = ref<any[]>([]);
const examForm = ref({ name: '', paperId: null as number | null });

async function fetchPaperList() {
  paperLoading.value = true;
  try {
    const response = await getPaperList({
      teacher_id: Number(userStore.userId),
      page: 1,
      page_size: 100
    });
    if (response.code === '0000' && response.data) {
      paperList.value = response.data.list || [];
      paperOptions.value = paperList.value.map((paper: any) => ({
        value: paper.id,
        label: `${paper.title || paper.paper_name} (${paper.question_count}题, ${paper.total_score}分)`
      }));
    }
  } catch (error) {
    console.error('加载试卷列表失败:', error);
    message.error('加载试卷列表失败');
  } finally {
    paperLoading.value = false;
  }
}

const paperList = ref<any[]>([]);

async function confirmSelectPaper() {
  if (!examForm.value.name) {
    message.warning('请输入考试名称');
    return;
  }
  if (!examForm.value.paperId) {
    message.warning('请选择试卷');
    return;
  }

  createExamLoading.value = true;
  try {
    const response = await createExamFromPaper(
      examForm.value.paperId,
      {
        exam_title: examForm.value.name,
        classroom_id: Number(classroomId)
      },
      Number(userStore.userId)
    );

    if (response.code === '0000') {
      message.success('创建考试成功');
      showPaperSelector.value = false;
      router.push(`/classroom/${classroomId}/exams`);
    } else {
      message.error(response.message || '创建考试失败');
    }
  } catch (error) {
    console.error('创建考试失败:', error);
    message.error('创建考试失败');
  } finally {
    createExamLoading.value = false;
  }
}

function handleCreateNewPaper() {
  router.push('/exam/edit-paper');
}

function goBack() {
  router.push(`/classroom/${classroomId}/exams`);
}

onMounted(() => {
  fetchPaperList();
});
</script>

<style scoped>
.classroom-exam-create-page {
  max-width: 800px;
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
.page-header {
  margin-bottom: 32px;
  text-align: center;
}
.page-title {
  font-size: 28px;
  margin: 0 0 8px 0;
}
.page-subtitle {
  color: #666;
  margin: 0;
}
.create-options-card {
  margin-bottom: 24px;
}
.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
.option-card {
  border: 2px solid #f0f0f0;
  border-radius: 8px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}
.option-card:hover {
  border-color: #1890ff;
  background: #f0f5ff;
}
.option-icon {
  font-size: 48px;
  color: #1890ff;
  margin-bottom: 16px;
}
.option-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
}
.option-desc {
  font-size: 14px;
  color: #666;
}
</style>
