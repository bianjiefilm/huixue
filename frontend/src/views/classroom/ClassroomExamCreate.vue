<template>
  <PageShell max-width="default" class="classroom-exam-create-page">
    <PageHeaderBar
      title="创建考试"
      subtitle="选择试卷来源，为课堂创建一场考试"
      show-back
      :back-to="`/classroom/${classroomId}/exams`"
    />

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
        <div v-if="paperOptions.length === 0 && !paperLoading" class="empty-papers-hint">
          暂无试卷，请先创建试卷
        </div>
      </a-form>
    </a-modal>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  FolderOutlined,
  PlusCircleOutlined
} from '@ant-design/icons-vue';
import { getPaperList, createExamFromPaper } from '@/api/exam';
import { useUserStore } from '@/stores/user';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

const classroomId = route.params.classroomId as string;

const showPaperSelector = ref(false);
const paperLoading = ref(false);
const createExamLoading = ref(false);
const paperOptions = ref<any[]>([]);
const examForm = ref({ name: '', paperId: null as number | null });
const paperList = ref<any[]>([]);

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

onMounted(() => {
  fetchPaperList();
});
</script>

<style scoped>
.create-options-card {
  margin-bottom: var(--hx-space-5);
}
.options-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--hx-space-5);
}
.option-card {
  border: 2px solid var(--hx-color-border-muted);
  border-radius: 8px;
  padding: var(--hx-space-6);
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}
.option-card:hover {
  border-color: var(--hx-color-primary);
  background: var(--hx-color-primary-bg, #f0f5ff);
}
.option-icon {
  font-size: 48px;
  color: var(--hx-color-primary);
  margin-bottom: var(--hx-space-4);
}
.option-title {
  font-size: var(--hx-font-size-lg);
  font-weight: 600;
  margin-bottom: var(--hx-space-2);
}
.option-desc {
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
}
.empty-papers-hint {
  text-align: center;
  color: var(--hx-color-text-secondary);
}
@media (max-width: 576px) {
  .options-grid {
    grid-template-columns: 1fr;
  }
}
</style>
