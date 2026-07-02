<template>
  <div class="bi-submission-review-page">
    <!-- 顶部工具栏 -->
    <div class="review-header">
      <div class="header-left">
        <a-button type="link" @click="goBack">
          <ArrowLeftOutlined /> 返回
        </a-button>
        <span class="review-title">BI 作业评阅</span>
        <a-tag color="blue">{{ studentName }}</a-tag>
      </div>

      <div class="header-right">
        <a-button type="primary" @click="showGradeModal = true" :disabled="isGraded">
          <EditOutlined /> {{ isGraded ? '已评分' : '评分' }}
        </a-button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="review-content">
      <!-- 左侧：提交信息 -->
      <div class="info-panel">
        <a-card title="提交信息" :bordered="false">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="学生">{{ studentName }}</a-descriptions-item>
            <a-descriptions-item label="提交时间">{{ formatDate(submission?.submittedAt) }}</a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(submission?.status)">
                {{ getStatusText(submission?.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="版本">{{ submission?.schemaVersion || '-' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <a-card title="学生说明" :bordered="false" style="margin-top: 16px;" v-if="submission?.notes">
          <div class="student-notes">{{ submission.notes }}</div>
        </a-card>

        <a-card title="评分详情" :bordered="false" style="margin-top: 16px;" v-if="isGraded">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="得分">
              <span class="score" :class="getScoreClass(submission?.score)">
                {{ submission?.score }} 分
              </span>
            </a-descriptions-item>
            <a-descriptions-item label="评语">
              <div class="feedback">{{ submission?.teacherFeedback || '-' }}</div>
            </a-descriptions-item>
            <a-descriptions-item label="评分时间">{{ formatDate(submission?.gradedAt) }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 设计文件列表 -->
        <a-card title="设计文件" :bordered="false" style="margin-top: 16px;" v-if="designFiles.length > 0">
          <div class="file-list">
            <div v-for="(file, index) in designFiles" :key="index" class="file-item">
              <div class="file-info">
                <component :is="getFileIcon(file.file_name || file.name)" class="file-icon" />
                <span class="file-name">{{ file.file_name || file.name }}</span>
              </div>
              <div class="file-actions">
                <a-button type="link" size="small" @click="previewFile(file)" v-if="getFileType(file.file_name || file.name) !== 'knwf'">
                  <EyeOutlined /> 预览
                </a-button>
                <a-button type="link" size="small" @click="downloadFile(file)">
                  <DownloadOutlined /> 下载
                </a-button>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 实验报告列表 -->
        <a-card title="实验报告" :bordered="false" style="margin-top: 16px;" v-if="experimentReports.length > 0">
          <div class="file-list">
            <div v-for="(file, index) in experimentReports" :key="index" class="file-item">
              <div class="file-info">
                <component :is="getFileIcon(file.file_name || file.name)" class="file-icon" />
                <span class="file-name">{{ file.file_name || file.name }}</span>
              </div>
              <div class="file-actions">
                <a-button type="link" size="small" @click="previewFile(file)">
                  <EyeOutlined /> 预览
                </a-button>
                <a-button type="link" size="small" @click="downloadFile(file)">
                  <DownloadOutlined /> 下载
                </a-button>
              </div>
            </div>
          </div>
        </a-card>

        <!-- 缩略图预览 -->
        <a-card title="分析截图" :bordered="false" style="margin-top: 16px;" v-if="submission?.thumbnail">
          <img :src="submission.thumbnail" alt="分析截图" class="thumbnail-preview" />
        </a-card>
      </div>

      <!-- 右侧：BI 可视化预览 -->
      <div class="preview-panel">
        <div class="panel-header">
          <h3>可视化分析预览</h3>
          <span class="readonly-badge">只读模式</span>
        </div>
        <div class="panel-body">
          <a-spin :spinning="loading" tip="加载中...">
            <BiDesigner
              v-if="!loading && datasets.length > 0"
              ref="biDesignerRef"
              :trainingId="trainingId"
              :classroomId="classroomId"
              :initialData="mergedDatasetData"
              :snapshot="submission?.snapshot"
              :readOnly="true"
            />
            <a-empty v-else-if="!loading" description="无法加载可视化预览" />
          </a-spin>
        </div>
      </div>
    </div>

    <!-- 评分模态框 -->
    <a-modal
      v-model:open="showGradeModal"
      title="评分"
      :width="500"
      @ok="handleGrade"
      :confirm-loading="grading"
    >
      <a-form :model="gradeForm" layout="vertical">
        <a-form-item label="得分 (0-100)">
          <a-input-number
            v-model:value="gradeForm.score"
            :min="0"
            :max="100"
            style="width: 100%;"
            placeholder="请输入分数"
          />
        </a-form-item>
        <a-form-item label="评语">
          <a-textarea
            v-model:value="gradeForm.feedback"
            :rows="4"
            placeholder="请输入评语（可选）"
            :maxlength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 文件预览组件 -->
    <ResourcePreview
      v-model:visible="showPreview"
      :resource="previewResource"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  EditOutlined,
  FileWordOutlined,
  FilePdfOutlined,
  FileOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';
import BiDesigner from '@/components/BiDesigner.vue';
import ResourcePreview from '@/components/common/ResourcePreview.vue';
import { getToken } from '@/utils/auth';

const route = useRoute();
const router = useRouter();

// 路由参数
const classroomId = computed(() => route.params.classroomId as string);
const trainingId = computed(() => parseInt(route.params.trainingId as string));
const studentId = computed(() => parseInt(route.params.studentId as string));

// 组件引用
const biDesignerRef = ref<InstanceType<typeof BiDesigner> | null>(null);

// 状态
const loading = ref(true);
const grading = ref(false);
const showGradeModal = ref(false);
const showPreview = ref(false);
const previewResource = ref<any>(null);

// 数据
const submission = ref<any>(null);
const studentName = ref('');
const datasets = ref<any[]>([]);
const mergedDatasetData = ref<any[]>([]);
const designFiles = ref<any[]>([]);
const experimentReports = ref<any[]>([]);

const gradeForm = ref({
  score: null as number | null,
  feedback: ''
});

const isGraded = computed(() => {
  return submission.value?.status === 'GRADED' || submission.value?.score !== null;
});

// 获取提交详情
async function fetchSubmission() {
  loading.value = true;
  try {
    // 获取学生提交信息
    const url = `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/submission/${studentId.value}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      submission.value = result.data;
      studentName.value = result.data.studentName || `学生 ${studentId.value}`;

      // 解析上传的文件
      if (result.data.files) {
        designFiles.value = result.data.files.design_files || [];
        experimentReports.value = result.data.files.experiment_reports || [];
      } else if (result.data.training_assignment_files) {
        try {
          const filesData = typeof result.data.training_assignment_files === 'string'
            ? JSON.parse(result.data.training_assignment_files)
            : result.data.training_assignment_files;
          designFiles.value = filesData.design_files || [];
          experimentReports.value = filesData.experiment_reports || [];
        } catch (e) {
          console.error('解析文件数据失败:', e);
        }
      }

      // 加载数据集
      await loadDatasets();

      // 如果已评分，填充表单
      if (result.data.score !== null) {
        gradeForm.value.score = result.data.score;
        gradeForm.value.feedback = result.data.teacherFeedback || '';
      }
    } else {
      message.error(result.message || '获取提交信息失败');
    }
  } catch (error) {
    console.error('获取提交信息失败:', error);
    message.error('获取提交信息失败');
  } finally {
    loading.value = false;
  }
}

// 加载数据集
async function loadDatasets() {
  try {
    const url = `/api/v1/trainings/${trainingId.value}/bi-dataset?classroom_id=${classroomId.value}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      datasets.value = result.data.datasets || [];

      if (datasets.value.length > 0) {
        mergedDatasetData.value = datasets.value[0].data || [];
      }
    }
  } catch (error) {
    console.error('加载数据集失败:', error);
  }
}

// 提交评分
async function handleGrade() {
  if (gradeForm.value.score === null) {
    message.error('请输入分数');
    return;
  }

  grading.value = true;
  try {
    const url = `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/grade/${studentId.value}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        score: gradeForm.value.score,
        feedback: gradeForm.value.feedback
      })
    });

    const result = await response.json();
    if (result.code === '0000') {
      message.success('评分成功');
      showGradeModal.value = false;

      // 刷新数据
      await fetchSubmission();
    } else {
      message.error(result.message || '评分失败');
    }
  } catch (error) {
    console.error('评分失败:', error);
    message.error('评分失败');
  } finally {
    grading.value = false;
  }
}

// 返回
function goBack() {
  router.back();
}

// 预览文件
function previewFile(file: any) {
  const fileType = getFileType(file.file_name || file.name);
  previewResource.value = {
    id: file.file_path || file.url,
    title: file.file_name || file.name,
    url: file.file_path || file.url,
    fileType: fileType
  };
  showPreview.value = true;
}

// 下载文件
function downloadFile(file: any) {
  const url = file.file_path || file.url;
  const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;

  const link = document.createElement('a');
  link.href = url.startsWith('/') ? `${backendBaseUrl}${url}` : url;
  link.download = file.file_name || file.name || 'download';
  link.target = '_blank';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  message.success('开始下载文件');
}

// 获取文件类型
function getFileType(filename: string): string {
  if (!filename) return 'unknown';
  const ext = filename.toLowerCase().split('.').pop() || '';
  if (ext === 'pdf') return 'pdf';
  if (['doc', 'docx'].includes(ext)) return 'doc';
  if (ext === 'knwf') return 'knwf';
  return ext;
}

// 获取文件图标
function getFileIcon(filename: string) {
  const ext = (filename || '').toLowerCase().split('.').pop() || '';
  if (ext === 'pdf') return FilePdfOutlined;
  if (['doc', 'docx'].includes(ext)) return FileWordOutlined;
  return FileOutlined;
}

// 工具函数
function formatDate(dateStr: string | null | undefined) {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleString('zh-CN');
}

function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    'SUBMITTED': 'blue',
    'GRADED': 'green',
    'IN_PROGRESS': 'orange',
    'NOT_STARTED': 'default'
  };
  return colors[status] || 'default';
}

function getStatusText(status: string) {
  const texts: Record<string, string> = {
    'SUBMITTED': '已提交',
    'GRADED': '已评分',
    'IN_PROGRESS': '进行中',
    'NOT_STARTED': '未开始'
  };
  return texts[status] || status;
}

function getScoreClass(score: number | null) {
  if (score === null) return '';
  if (score >= 90) return 'score-excellent';
  if (score >= 80) return 'score-good';
  if (score >= 60) return 'score-pass';
  return 'score-fail';
}

// 生命周期
onMounted(() => {
  fetchSubmission();
});
</script>

<style scoped lang="less">
.bi-submission-review-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;

  .review-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: white;
    border-bottom: 1px solid #e8e8e8;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;

      .review-title {
        font-size: 16px;
        font-weight: 600;
        color: #262626;
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .review-content {
    display: flex;
    flex: 1;
    overflow: hidden;
    padding: 16px;
    gap: 16px;

    .info-panel {
      width: 360px;
      flex-shrink: 0;
      overflow-y: auto;

      .student-notes {
        color: #595959;
        line-height: 1.6;
        white-space: pre-wrap;
      }

      .score {
        font-size: 20px;
        font-weight: 600;

        &.score-excellent {
          color: #52c41a;
        }
        &.score-good {
          color: #1890ff;
        }
        &.score-pass {
          color: #faad14;
        }
        &.score-fail {
          color: #ff4d4f;
        }
      }

      .feedback {
        color: #595959;
        line-height: 1.6;
        white-space: pre-wrap;
      }

      .thumbnail-preview {
        max-width: 100%;
        border: 1px solid #e8e8e8;
        border-radius: 4px;
      }

      .file-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .file-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 12px;
        background: #fafafa;
        border-radius: 6px;
        border: 1px solid #f0f0f0;

        &:hover {
          background: #f5f5f5;
          border-color: #e8e8e8;
        }
      }

      .file-info {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;

        .file-icon {
          font-size: 18px;
          color: #1890ff;
        }

        .file-name {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: #595959;
          font-size: 13px;
        }
      }

      .file-actions {
        display: flex;
        gap: 4px;
        flex-shrink: 0;
      }
    }

    .preview-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: white;
      border-radius: 4px;
      overflow: hidden;

      .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #e8e8e8;
        background: #fafafa;

        h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 600;
          color: #262626;
        }

        .readonly-badge {
          font-size: 12px;
          color: #8c8c8c;
          padding: 2px 8px;
          background: #f5f5f5;
          border-radius: 4px;
        }
      }

      .panel-body {
        flex: 1;
        position: relative;
        overflow: hidden;
      }
    }
  }
}
</style>
