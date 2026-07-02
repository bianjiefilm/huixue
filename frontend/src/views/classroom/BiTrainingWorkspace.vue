<template>
  <div class="bi-training-workspace-page">
    <!-- 顶部工具栏 -->
    <div class="workspace-header">
      <div class="header-left">
        <a-button type="link" @click="goBack">
          <ArrowLeftOutlined /> 返回
        </a-button>
        <span class="training-title">{{ training?.title || 'BI 可视化分析实训' }}</span>
      </div>

      <div class="header-center">
        <span class="save-status" :class="saveStatusClass">
          <span v-if="saveStatus === 'saving'"><LoadingOutlined /> 保存中...</span>
          <span v-else-if="saveStatus === 'saved'"><CheckCircleOutlined /> 已保存</span>
          <span v-else-if="saveStatus === 'error'"><ExclamationCircleOutlined /> 保存失败</span>
          <span v-else><CloudOutlined /> 未保存</span>
        </span>
      </div>

      <div class="header-right">
        <a-button @click="handleSaveDraft" :loading="saveStatus === 'saving'">
          <SaveOutlined /> 保存草稿
        </a-button>
        <a-button
          v-if="canSubmit"
          type="primary"
          @click="showSubmitModal = true"
          :disabled="submitting"
        >
          <UploadOutlined /> 提交作业
        </a-button>
      </div>
    </div>

    <!-- 主要内容区域：左右分栏 -->
    <div class="workspace-content">
      <!-- 左侧：手册内容 -->
      <div class="handbook-panel" :style="{ width: handbookCollapsed ? '48px' : handbookWidth + 'px' }">
        <div class="panel-header" v-show="!handbookCollapsed">
          <h3>实训手册</h3>
          <a-button
            type="text"
            size="small"
            @click="toggleHandbookPanel"
          >
            <LeftOutlined />
          </a-button>
        </div>
        <div class="panel-collapse-bar" v-show="handbookCollapsed" @click="toggleHandbookPanel">
          <RightOutlined />
          <span class="collapse-text">实训手册</span>
        </div>
        <div class="panel-body" v-show="!handbookCollapsed">
          <div class="handbook-content">
            <a-spin :spinning="loading" tip="加载手册中...">
              <div v-if="handbookContent" v-html="renderedHandbookContent" class="markdown-body"></div>
              <a-empty v-else description="暂无手册内容" />
            </a-spin>
          </div>

          <!-- 成绩显示区域 -->
          <div v-if="studentProgress.score !== null" class="grade-section">
            <a-card size="small">
              <template #title>成绩信息</template>
              <div class="grade-info">
                <div class="grade-item">
                  <span class="label">得分：</span>
                  <span class="value score-value" :class="getScoreClass(studentProgress.score)">
                    {{ studentProgress.score }} 分
                  </span>
                </div>
                <div v-if="studentProgress.teacherFeedback" class="grade-item">
                  <span class="label">教师评语：</span>
                  <div class="feedback-content">{{ studentProgress.teacherFeedback }}</div>
                </div>
              </div>
            </a-card>
          </div>
        </div>
      </div>

      <!-- 分割线（可拖拽调整大小） -->
      <div class="resizer" @mousedown="startResize" v-show="!handbookCollapsed"></div>

      <!-- 右侧：BI 可视化画布 -->
      <div class="bi-panel">
        <div class="panel-header">
          <h3>可视化分析画布</h3>
          <div class="dataset-info" v-if="datasets.length > 0">
            <DatabaseOutlined />
            <span>数据集: {{ datasets.map(d => d.name).join(', ') }}</span>
          </div>
        </div>
        <div class="panel-body">
          <a-spin :spinning="dataLoading" tip="加载数据中...">
            <iframe
              v-if="!dataLoading && datasets.length > 0"
              ref="biIframeRef"
              :src="iframeSrc"
              class="bi-designer-iframe"
              frameborder="0"
              style="width: 100%; height: 100%; min-height: 600px;"
            ></iframe>
            <a-empty v-else-if="!dataLoading" description="暂无数据集">
              <template #extra>
                <a-button type="primary" @click="loadDatasets">重新加载</a-button>
              </template>
            </a-empty>
          </a-spin>
        </div>
      </div>
    </div>

    <!-- 提交作业模态框 -->
    <a-modal
      v-model:open="showSubmitModal"
      title="提交 BI 分析作业"
      :width="600"
      @ok="handleSubmit"
      @cancel="showSubmitModal = false"
      :confirm-loading="submitting"
    >
      <div class="submit-form">
        <a-alert
          message="提交说明"
          description="提交后将保存您当前的可视化分析配置作为作业成果，数据不会被提交。"
          type="info"
          show-icon
          style="margin-bottom: 16px;"
        />

        <!-- 缩略图预览 -->
        <div class="thumbnail-section" v-if="submissionThumbnail">
          <div class="section-title">分析截图预览</div>
          <img :src="submissionThumbnail" alt="分析截图" class="thumbnail-preview" />
        </div>

        <!-- 设计文件上传 -->
        <div v-if="training?.require_design_files" class="upload-section">
          <div class="section-title">
            <span>设计文件（.knwf工作流文件）</span>
            <a-tag color="orange">必填</a-tag>
          </div>
          <a-upload
            v-model:file-list="designFileList"
            :before-upload="beforeUploadDesignFile"
            :max-count="1"
            accept=".knwf"
          >
            <a-button>
              <UploadOutlined /> 选择文件
            </a-button>
          </a-upload>
          <div v-if="designFileList.length > 0" class="file-info">
            已选择：{{ designFileList[0].name }}
            <a-button type="link" size="small" danger @click="handleRemoveDesignFile">删除</a-button>
          </div>
        </div>

        <!-- 实验报告上传 -->
        <div v-if="training?.require_experiment_report" class="upload-section">
          <div class="section-title">
            <span>实验报告（PDF/Word）</span>
            <a-tag color="orange">必填</a-tag>
          </div>
          <a-upload
            v-model:file-list="reportFileList"
            :before-upload="beforeUploadReport"
            :max-count="1"
            accept=".pdf,.doc,.docx"
          >
            <a-button>
              <UploadOutlined /> 选择文件
            </a-button>
          </a-upload>
          <div v-if="reportFileList.length > 0" class="file-info">
            <span>
              <FilePdfOutlined v-if="reportFileList[0].name?.endsWith('.pdf')" />
              <FileWordOutlined v-else />
              {{ reportFileList[0].name }}
            </span>
            <a-button type="link" size="small" danger @click="handleRemoveReport">删除</a-button>
          </div>
        </div>

        <!-- 提交说明 -->
        <div class="notes-section">
          <div class="section-title">提交说明（可选）</div>
          <a-textarea
            v-model:value="submitNotes"
            :rows="4"
            placeholder="请输入您的分析思路和结论..."
            :maxlength="1000"
            show-count
          />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import MarkdownIt from 'markdown-it';
import type { UploadFile } from 'ant-design-vue';
import {
  ArrowLeftOutlined,
  UploadOutlined,
  SaveOutlined,
  LeftOutlined,
  RightOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  CloudOutlined,
  DatabaseOutlined,
  FileWordOutlined,
  FilePdfOutlined
} from '@ant-design/icons-vue';
import { getToken } from '@/utils/auth';
import { useBiAutoSave } from '@/composables/useBiAutoSave';
import { useUserStore } from '@/stores/user';

const route = useRoute();
const router = useRouter();

// 路由参数
const classroomId = computed(() => route.params.classroomId as string);
const trainingId = computed(() => parseInt(route.params.trainingId as string));

const userStore = useUserStore();
const currentStudentId = computed(() => {
  return route.query.student_id ? parseInt(route.query.student_id as string) : userStore.userId;
});

const requireCurrentStudentId = () => {
  const userId = currentStudentId.value;
  if (!userId) {
    message.warning('请先登录后再访问 BI 实训工作区');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 组件引用
const biIframeRef = ref<HTMLIFrameElement | null>(null);
const iframeReady = ref(false);
const latestSpec = ref<any>(null);

const iframeSrc = computed(() => {
  return `/#/designer/bi/${trainingId.value}/embed?classroomId=${classroomId.value}`;
});

// 状态
const loading = ref(false);
const dataLoading = ref(false);
const submitting = ref(false);
const handbookCollapsed = ref(false);
const handbookWidth = ref(400);
const isResizing = ref(false);
const showSubmitModal = ref(false);
const submitNotes = ref('');
const submissionThumbnail = ref('');
const designFileList = ref<UploadFile[]>([]);
const reportFileList = ref<UploadFile[]>([]);

// 数据
const training = ref<any>(null);
const handbookContent = ref('');
const datasets = ref<any[]>([]);
const draftSnapshot = ref<any>(null);
const mergedDatasetData = ref<any[]>([]);
const isReadOnly = ref(false);

const studentProgress = ref({
  status: 'not_started',
  completedPercentage: 0,
  score: null as number | null,
  teacherFeedback: null as string | null,
  gradedAt: null as string | null
});

// 自动保存
const { saveStatus, saveDraft, loadDraft } = useBiAutoSave({
  trainingId: trainingId.value,
  classroomId: classroomId.value,
  studentId: currentStudentId.value,
  getSpec: async () => {
    return latestSpec.value || draftSnapshot.value;
  }
});

const saveStatusClass = computed(() => ({
  'status-saving': saveStatus.value === 'saving',
  'status-saved': saveStatus.value === 'saved',
  'status-error': saveStatus.value === 'error',
  'status-idle': saveStatus.value === 'idle'
}));

// Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

const renderedHandbookContent = computed(() => {
  if (!handbookContent.value) return '';
  return md.render(handbookContent.value);
});

const canSubmit = computed(() => {
  return studentProgress.value.status === 'in_progress' ||
         studentProgress.value.status === 'not_started';
});

// 获取实训详情和手册
async function fetchTrainingDetail() {
  loading.value = true;
  try {
    const currentUserId = requireCurrentStudentId();
    const url = `/api/v1/classrooms/${classroomId.value}/trainings/${trainingId.value}/details?student_id=${currentUserId}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      training.value = result.data;
      handbookContent.value = result.data.handbook_content || result.data.handbookContent || '';
      studentProgress.value = {
        status: result.data.progress?.status || 'not_started',
        completedPercentage: result.data.progress?.completedPercentage || 0,
        score: result.data.progress?.score || result.data.progress?.overall_score || null,
        teacherFeedback: result.data.progress?.teacher_feedback || result.data.progress?.teacherFeedback || null,
        gradedAt: result.data.progress?.graded_at || result.data.progress?.gradedAt || null
      };

      // 检查是否只读（已评分）
      isReadOnly.value = studentProgress.value.score !== null;
    } else {
      message.error(result.message || '加载实训详情失败');
    }
  } catch (error) {
    console.error('获取实训详情失败:', error);
    message.error('加载实训详情失败');
  } finally {
    loading.value = false;
  }
}

// 加载数据集
async function loadDatasets() {
  dataLoading.value = true;
  try {
    const url = `/api/v1/trainings/${training.value?.training_id || trainingId.value}/bi-dataset?classroom_id=${classroomId.value}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    const result = await response.json();

    if (result.code === '0000' && result.data) {
      datasets.value = result.data.datasets || [];

      // 合并所有数据集数据 - 通过 product_id 和 store_id 关联
      if (datasets.value.length > 0) {
        mergedDatasetData.value = mergeDatasets(datasets.value);
        console.log('Merged dataset rows:', mergedDatasetData.value.length);
      }
    } else {
      console.error('加载数据集失败:', result.message);
      message.warning(result.message || '数据集加载失败，请检查实训数据是否已配置');
    }
  } catch (error) {
    console.error('加载数据集失败:', error);
    message.error('数据集加载失败，请稍后重试');
  } finally {
    dataLoading.value = false;
  }
}

// 移除 BOM 字符并规范化对象的 key
function normalizeBOMKeys(obj: any): any {
  if (!obj || typeof obj !== 'object') return obj;
  const result: any = {};
  for (const key of Object.keys(obj)) {
    // 移除 BOM 字符 (\uFEFF)
    const cleanKey = key.replace(/^\uFEFF/, '');
    result[cleanKey] = obj[key];
  }
  return result;
}

// 合并多个数据集，通过 product_id 和 store_id 关联
function mergeDatasets(datasetsArray: any[]): any[] {
  if (!datasetsArray || datasetsArray.length === 0) return [];

  // 找到各个数据集
  let transactions: any[] = [];
  let products: any[] = [];
  let stores: any[] = [];

  for (const ds of datasetsArray) {
    const name = ds.name?.toLowerCase() || '';
    // 规范化数据，移除 BOM 字符
    const data = (ds.data || []).map(normalizeBOMKeys);

    if (name.includes('transaction') || name.includes('retail_transaction')) {
      transactions = data;
    } else if (name.includes('product')) {
      products = data;
    } else if (name.includes('store')) {
      stores = data;
    }
  }

  // 如果只有一个数据集，直接返回（已规范化）
  if (datasetsArray.length === 1) {
    return (datasetsArray[0].data || []).map(normalizeBOMKeys);
  }

  // 如果没有交易表，尝试按顺序使用（向后兼容）
  if (transactions.length === 0) {
    // 查找包含 trans_id 或 trans_date 字段的表作为主表
    for (const ds of datasetsArray) {
      const data = (ds.data || []).map(normalizeBOMKeys);
      if (data.length > 0 && (data[0].trans_id !== undefined || data[0].trans_date !== undefined)) {
        transactions = data;
        break;
      }
    }
  }

  // 如果仍然没有交易表，返回第一个数据集
  if (transactions.length === 0) {
    console.warn('No transactions table found, using first dataset');
    return (datasetsArray[0].data || []).map(normalizeBOMKeys);
  }

  // 构建 products 和 stores 的查找映射
  const productMap = new Map<string, any>();
  for (const p of products) {
    if (p.product_id) {
      productMap.set(p.product_id, p);
    }
  }

  const storeMap = new Map<string, any>();
  for (const s of stores) {
    if (s.store_id) {
      storeMap.set(s.store_id, s);
    }
  }

  console.log('Merging datasets - transactions:', transactions.length, 'products:', products.length, 'stores:', stores.length);

  // 合并数据
  const merged = transactions.map(tx => {
    const result = { ...tx };

    // 关联商品信息
    if (tx.product_id && productMap.has(tx.product_id)) {
      const product = productMap.get(tx.product_id);
      // 添加商品字段（避免覆盖已有字段）
      if (product.product_name !== undefined) result.product_name = product.product_name;
      if (product.category !== undefined) result.category = product.category;
      if (product.cost_price !== undefined) result.cost_price = product.cost_price;
      if (product.retail_price !== undefined) result.retail_price = product.retail_price;
    }

    // 关联门店信息
    if (tx.store_id && storeMap.has(tx.store_id)) {
      const store = storeMap.get(tx.store_id);
      // 添加门店字段
      if (store.store_name !== undefined) result.store_name = store.store_name;
      if (store.city !== undefined) result.city = store.city;
      if (store.store_type !== undefined) result.store_type = store.store_type;
      if (store.size_sqm !== undefined) result.size_sqm = store.size_sqm;
    }

    return result;
  });

  console.log('Merged data fields:', merged.length > 0 ? Object.keys(merged[0]) : []);
  return merged;
}

// 加载草稿
async function loadDraftSnapshot() {
  try {
    const draft = await loadDraft();
    if (draft) {
      draftSnapshot.value = draft.snapshot;
      message.info('已恢复上次的分析草稿');
    }
  } catch (error) {
    console.error('加载草稿失败:', error);
  }
}

// 手动保存草稿
async function handleSaveDraft() {
  try {
    const spec = latestSpec.value || draftSnapshot.value;
    if (spec) {
      await saveDraft(spec);
      message.success('草稿已保存');
    }
  } catch (error) {
    console.error('保存草稿失败:', error);
    message.error('保存草稿失败');
  }
}

// 监听 spec 变化（用于自动保存）
function handleSpecChange(spec: any) {
  latestSpec.value = spec;
  console.log('Spec changed via iframe, auto-save will trigger...');
}

// 保存设计
function handleSaveDesign(data: any) {
  console.log('Saving design:', data);
  saveDraft(data);
  message.success('设计已保存');
}

// 提交作业
async function handleSubmit() {
  if (!latestSpec.value && !draftSnapshot.value) {
    message.error('请先完成可视化分析');
    return;
  }

  // 检查是否满足提交要求
  if (training.value?.require_design_files && designFileList.value.length === 0) {
    message.error('请上传设计文件（.knwf工作流文件）');
    return;
  }

  if (training.value?.require_experiment_report && reportFileList.value.length === 0) {
    message.error('请上传实验报告');
    return;
  }

  submitting.value = true;
  try {
    const currentUserId = requireCurrentStudentId();

    // 获取当前配置
    const spec = latestSpec.value || draftSnapshot.value;
    if (!spec) {
      message.error('无法获取分析配置');
      return;
    }

    // 先上传文件（如果有）
    const uploadPromises: Promise<any>[] = [];

    if (designFileList.value.length > 0) {
      const file = designFileList.value[0];
      const formData = new FormData();
      formData.append('file', file.originFileObj as File);
      formData.append('classroom_id', classroomId.value);
      formData.append('student_id', currentUserId.toString());
      formData.append('file_type', 'design_file');

      uploadPromises.push(
        fetch(`/api/v1/trainings/${trainingId.value}/upload-submission`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken() || ''}`
          },
          body: formData
        }).then(res => res.json())
      );
    }

    if (reportFileList.value.length > 0) {
      const file = reportFileList.value[0];
      const formData = new FormData();
      formData.append('file', file.originFileObj as File);
      formData.append('classroom_id', classroomId.value);
      formData.append('student_id', currentUserId.toString());
      formData.append('file_type', 'experiment_report');

      uploadPromises.push(
        fetch(`/api/v1/trainings/${trainingId.value}/upload-submission`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${getToken() || ''}`
          },
          body: formData
        }).then(res => res.json())
      );
    }

    // 等待所有文件上传完成
    if (uploadPromises.length > 0) {
      const uploadResults = await Promise.all(uploadPromises);
      const uploadErrors = uploadResults.filter(r => r.code !== '0000');

      if (uploadErrors.length > 0) {
        message.error('文件上传失败，请重试');
        return;
      }
    }

    // 构建提交数据
    const submissionData = {
      schemaVersion: 'gwalk-v0.4.77',
      platformVersion: '2.1.0',
      snapshot: spec,
      thumbnail: submissionThumbnail.value,
      notes: submitNotes.value
    };

    // 提交到服务器
    const url = `/api/v1/trainings/${trainingId.value}/submit?classroom_id=${classroomId.value}&student_id=${currentUserId}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        snapshot_json: submissionData
      })
    });

    const result = await response.json();
    if (result.code === '0000') {
      message.success('作业已提交');
      studentProgress.value.status = 'submitted';
      studentProgress.value.completedPercentage = 100;
      showSubmitModal.value = false;
      submitNotes.value = '';

      // 清空文件列表
      designFileList.value = [];
      reportFileList.value = [];

      // 刷新进度信息
      await fetchTrainingDetail();
    } else {
      message.error(result.message || '提交作业失败');
    }
  } catch (error) {
    console.error('提交作业失败:', error);
    message.error('提交作业失败');
  } finally {
    submitting.value = false;
  }
}

// 文件上传前检查 - 设计文件
function beforeUploadDesignFile(file: File) {
  const isKNWF = file.name.toLowerCase().endsWith('.knwf');
  if (!isKNWF) {
    message.error('只能上传 .knwf 格式的工作流文件');
    return false;
  }
  const isLt50M = file.size / 1024 / 1024 < 50;
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB');
    return false;
  }
  return false; // 阻止自动上传，手动控制
}

// 文件上传前检查 - 实验报告
function beforeUploadReport(file: File) {
  const isPDF = file.name.toLowerCase().endsWith('.pdf');
  const isWord = file.name.toLowerCase().endsWith('.doc') || file.name.toLowerCase().endsWith('.docx');
  if (!isPDF && !isWord) {
    message.error('只能上传 PDF 或 Word 格式的文件');
    return false;
  }
  const isLt50M = file.size / 1024 / 1024 < 50;
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB');
    return false;
  }
  return false; // 阻止自动上传，手动控制
}

// 删除设计文件
function handleRemoveDesignFile() {
  designFileList.value = [];
}

// 删除实验报告
function handleRemoveReport() {
  reportFileList.value = [];
}

// 切换手册面板
function toggleHandbookPanel() {
  handbookCollapsed.value = !handbookCollapsed.value;
}

// 调整面板大小
function startResize(e: MouseEvent) {
  isResizing.value = true;
  const startX = e.clientX;
  const startWidth = handbookWidth.value;

  function onMouseMove(e: MouseEvent) {
    const diff = e.clientX - startX;
    const newWidth = Math.max(200, Math.min(600, startWidth + diff));
    handbookWidth.value = newWidth;
  }

  function onMouseUp() {
    isResizing.value = false;
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  }

  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
}

// 返回
function goBack() {
  router.push(`/classroom/${classroomId.value}`);
}

// 工具函数
function getScoreClass(score: number) {
  if (score >= 90) return 'score-excellent';
  if (score >= 80) return 'score-good';
  if (score >= 60) return 'score-pass';
  return 'score-fail';
}

function sendDataToIframe() {
  if (biIframeRef.value && biIframeRef.value.contentWindow && iframeReady.value) {
    try {
      const payloadObj = JSON.parse(JSON.stringify({
        trainingId: trainingId.value,
        classroomId: classroomId.value,
        initialData: mergedDatasetData.value,
        snapshot: draftSnapshot.value,
        readOnly: isReadOnly.value
      }));
      biIframeRef.value.contentWindow.postMessage({
        type: 'INIT_BI_DESIGNER',
        payload: payloadObj
      }, '*');
    } catch (e) {
      console.error('[BiTrainingWorkspace] Failed to clone payload for iframe:', e);
    }
  }
}

function handleIframeMessage(event: MessageEvent) {
  const data = event.data;
  if (!data || typeof data !== 'object') return;
  
  if (data.type === 'BI_DESIGNER_READY') {
    iframeReady.value = true;
    sendDataToIframe();
  } else if (data.type === 'BI_DESIGNER_SAVE') {
    handleSaveDesign(data.payload);
  } else if (data.type === 'BI_DESIGNER_SPEC_CHANGE') {
    handleSpecChange(data.payload);
  }
}

// 监听 trainingId 变化，重新加载数据和 iframe
watch(trainingId, async (newId) => {
  if (!newId) return;
  datasets.value = [];
  await fetchTrainingDetail();
  await loadDatasets();
  await loadDraftSnapshot();
  if (studentProgress.value.status === 'not_started') {
    studentProgress.value.status = 'in_progress';
  }
  sendDataToIframe();
});

// 生命周期
onMounted(async () => {
  window.addEventListener('message', handleIframeMessage);

  await fetchTrainingDetail();
  await loadDatasets();
  await loadDraftSnapshot();

  // 更新进度状态
  if (studentProgress.value.status === 'not_started') {
    studentProgress.value.status = 'in_progress';
  }

  // 确保数据加载完成后，如果 iframe 已经就绪，再次发送最新数据
  sendDataToIframe();
});

onUnmounted(() => {
  window.removeEventListener('message', handleIframeMessage);
  if (isResizing.value) {
    isResizing.value = false;
  }
});
</script>

<style scoped lang="less">
.bi-training-workspace-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;

  .workspace-header {
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

      .training-title {
        font-size: 16px;
        font-weight: 600;
        color: #262626;
      }
    }

    .header-center {
      .save-status {
        font-size: 13px;
        padding: 4px 12px;
        border-radius: 4px;

        &.status-saving {
          color: #1890ff;
          background: #e6f7ff;
        }
        &.status-saved {
          color: #52c41a;
          background: #f6ffed;
        }
        &.status-error {
          color: #ff4d4f;
          background: #fff2f0;
        }
        &.status-idle {
          color: #8c8c8c;
          background: #fafafa;
        }
      }
    }

    .header-right {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .workspace-content {
    display: flex;
    flex: 1;
    overflow: hidden;

    .handbook-panel {
      display: flex;
      flex-direction: column;
      background: white;
      border-right: 1px solid #e8e8e8;
      overflow: hidden;
      transition: width 0.2s ease;

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
      }

      .panel-collapse-bar {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px 8px;
        cursor: pointer;
        background: #fafafa;
        height: 100%;

        &:hover {
          background: #f0f0f0;
        }

        .collapse-text {
          writing-mode: vertical-rl;
          margin-top: 12px;
          font-size: 13px;
          color: #595959;
        }
      }

      .panel-body {
        flex: 1;
        overflow-y: auto;
        padding: 16px;

        .handbook-content {
          :deep(.markdown-body) {
            h1, h2, h3 {
              margin-top: 20px;
              margin-bottom: 10px;
              color: #262626;
            }

            p {
              line-height: 1.8;
              color: #595959;
              margin-bottom: 12px;
            }

            ul, ol {
              padding-left: 24px;
              margin-bottom: 12px;

              li {
                line-height: 1.8;
                color: #595959;
                margin-bottom: 6px;
              }
            }

            code {
              background: #f5f5f5;
              padding: 2px 6px;
              border-radius: 3px;
              font-family: 'Courier New', monospace;
            }

            pre {
              background: #f5f5f5;
              padding: 12px;
              border-radius: 4px;
              overflow-x: auto;

              code {
                background: transparent;
                padding: 0;
              }
            }

            img {
              max-width: 100%;
              height: auto;
              border-radius: 4px;
            }

            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 16px;

              th, td {
                border: 1px solid #e8e8e8;
                padding: 8px 12px;
                text-align: left;
              }

              th {
                background: #fafafa;
                font-weight: 600;
              }
            }
          }
        }
      }
    }

    .resizer {
      width: 4px;
      background: #e8e8e8;
      cursor: col-resize;
      flex-shrink: 0;

      &:hover {
        background: #1890ff;
      }
    }

    .bi-panel {
      flex: 1;
      display: flex;
      flex-direction: column;
      background: white;
      overflow: hidden;
      min-width: 600px;

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

        .dataset-info {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #8c8c8c;
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

.submit-form {
  .thumbnail-section {
    margin-bottom: 16px;

    .section-title {
      font-weight: 600;
      margin-bottom: 8px;
      color: #262626;
    }

    .thumbnail-preview {
      max-width: 100%;
      max-height: 200px;
      border: 1px solid #e8e8e8;
      border-radius: 4px;
    }
  }

  .upload-section {
    margin-bottom: 16px;
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;
    border: 1px dashed #d9d9d9;

    .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-weight: 600;
      margin-bottom: 12px;
      color: #262626;
    }

    .file-info {
      margin-top: 12px;
      padding: 10px 12px;
      background: #fff;
      border-radius: 4px;
      border: 1px solid #e8e8e8;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 13px;
      color: #595959;

      span {
        display: flex;
        align-items: center;
        gap: 6px;
      }
    }
  }

  .notes-section {
    .section-title {
      font-weight: 600;
      margin-bottom: 8px;
      color: #262626;
    }
  }
}

.grade-section {
  margin-top: 16px;

  .grade-info {
    .grade-item {
      margin-bottom: 12px;

      &:last-child {
        margin-bottom: 0;
      }

      .label {
        font-weight: 600;
        color: #595959;
        margin-right: 8px;
      }

      .value {
        color: #262626;
      }

      .score-value {
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

      .feedback-content {
        margin-top: 8px;
        padding: 8px;
        background: #f5f5f5;
        border-radius: 4px;
        color: #595959;
        line-height: 1.6;
      }
    }
  }
}
</style>
