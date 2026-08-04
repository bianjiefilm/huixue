<template>
  <div class="hx-workspace">
    <!-- 顶部工具栏：不占编辑器高度的固定条 -->
    <header class="hx-workspace__toolbar">
      <div class="header-left">
        <a-button type="link" @click="goBack">
          <ArrowLeftOutlined /> 返回
        </a-button>
        <span class="training-title">{{ training?.title || '实训工作区' }}</span>
      </div>
      
      <div class="header-right">
        <a-button 
          v-if="canSubmit" 
          type="primary" 
          @click="showSubmitModal = true"
          :disabled="submitting"
        >
          <UploadOutlined /> 提交作业
        </a-button>
        <a-divider type="vertical" />
        <a-dropdown>
          <a-button>
            <SettingOutlined /> 环境管理
          </a-button>
          <template #overlay>
            <a-menu @click="handleEnvironmentAction">
              <a-menu-item key="restart">
                <ReloadOutlined /> 重启环境
              </a-menu-item>
              <a-menu-item key="stop">
                <StopOutlined /> 停止环境
              </a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </header>

    <!-- 主要内容区域：左右分栏，flex 吃满剩余视口 -->
    <div class="hx-workspace__body">
      <!-- 左侧：手册内容 -->
      <div class="handbook-panel">
        <div class="panel-header">
          <h3>📄 实训手册</h3>
          <a-button 
            type="text" 
            size="small" 
            @click="toggleHandbookPanel"
            :icon="handbookCollapsed ? h(ExpandOutlined) : h(CompressOutlined)"
          />
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
            <a-card>
              <template #title>📊 成绩信息</template>
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
                <div v-if="studentProgress.gradedAt" class="grade-item">
                  <span class="label">评分时间：</span>
                  <span class="value">{{ formatDate(studentProgress.gradedAt) }}</span>
                </div>
              </div>
            </a-card>
          </div>
        </div>
      </div>

      <!-- 分割线（可拖拽调整大小） -->
      <div class="resizer" @mousedown="startResize"></div>

      <!-- 右侧：VDI环境 -->
      <div class="vdi-panel" :style="{ width: vdiPanelWidth + 'px' }">
        <div class="panel-header">
          <h3>🖥️ 实训环境</h3>
          <div class="environment-status">
            <a-badge :status="environmentStatus === 'running' ? 'success' : 'default'" />
            <span>{{ getStatusText(environmentStatus) }}</span>
          </div>
        </div>
        <div class="panel-body">
          <a-spin :spinning="environmentStatus === 'starting'" tip="环境启动中，请稍候...">
            <div v-if="environmentStatus === 'running' && vncUrl" class="vdi-container">
              <iframe
                ref="vncFrame"
                :src="vncUrl"
                frameborder="0"
                style="width: 100%; height: 100%; display: block;"
                @load="handleVncLoad"
              ></iframe>
            </div>
            <div v-else-if="environmentStatus === 'error'" class="error-container">
              <a-result
                status="error"
                title="环境启动失败"
                :sub-title="errorMessage"
              >
                <template #extra>
                  <a-button type="primary" @click="retryLaunch">重试</a-button>
                </template>
              </a-result>
            </div>
            <div v-else class="empty-container">
              <a-empty description="环境未启动">
                <template #extra>
                  <a-button type="primary" @click="launchEnvironment" :loading="launching">
                    启动环境
                  </a-button>
                </template>
              </a-empty>
            </div>
          </a-spin>
        </div>
      </div>
    </div>

    <!-- 提交作业模态框 -->
    <a-modal
      v-model:open="showSubmitModal"
      title="提交作业"
      :width="600"
      @ok="handleSubmit"
      @cancel="showSubmitModal = false"
      :confirm-loading="submitting"
    >
      <div class="submit-form">
        <!-- 设计文件上传 -->
        <div v-if="training?.require_design_files" class="upload-section">
          <div class="section-title">设计文件（.knwf工作流文件）</div>
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
            <a-button type="link" size="small" @click="handleRemoveDesignFile">删除</a-button>
          </div>
        </div>

        <!-- 实验报告上传 -->
        <div v-if="training?.require_experiment_report" class="upload-section" style="margin-top: 16px;">
          <div class="section-title">实验报告（PDF/Word）</div>
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
            已选择：{{ reportFileList[0].name }}
            <a-button type="link" size="small" @click="handleRemoveReport">删除</a-button>
          </div>
        </div>

        <!-- 提交说明 -->
        <div class="notes-section" style="margin-top: 16px;">
          <div class="section-title">提交说明（可选）</div>
          <a-textarea
            v-model:value="submitNotes"
            :rows="4"
            placeholder="请输入提交说明..."
            :maxlength="500"
            show-count
          />
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, h, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import MarkdownIt from 'markdown-it';
import {
  ArrowLeftOutlined,
  UploadOutlined,
  SettingOutlined,
  ReloadOutlined,
  StopOutlined,
  ExpandOutlined,
  CompressOutlined
} from '@ant-design/icons-vue';
import type { UploadFile } from 'ant-design-vue';
import { launchAndPoll } from '@/utils/polling';
import { useUserStore } from '@/stores/user';
import { getToken } from '@/utils/auth';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 路由参数
const classroomId = computed(() => route.params.classroomId as string);
const trainingId = computed(() => parseInt(route.params.trainingId as string));

// 状态
const loading = ref(false);
const launching = ref(false);
const submitting = ref(false);
const handbookCollapsed = ref(false);
const environmentStatus = ref<'idle' | 'starting' | 'running' | 'error'>('idle');
const errorMessage = ref('');
const vncUrl = ref('');
const handbookContent = ref('');
const showSubmitModal = ref(false);
const designFileList = ref<UploadFile[]>([]);
const reportFileList = ref<UploadFile[]>([]);
const submitNotes = ref('');

// 布局
const vdiPanelWidth = ref(800); // 默认右侧面板宽度
const isResizing = ref(false);
const vncFrame = ref<HTMLIFrameElement | null>(null);

// 数据
const training = ref<any>(null);
const studentProgress = ref({
  status: 'not_started',
  completedPercentage: 0,
  score: null as number | null,
  teacherFeedback: null as string | null,
  gradedAt: null as string | null
});

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
  return studentProgress.value.status === 'in_progress' || environmentStatus.value === 'running';
});

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再访问实训工作区');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 获取实训详情和手册
async function fetchTrainingDetail() {
  loading.value = true;
  try {
    const currentUserId = requireCurrentUserId();
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
    } else {
      console.error('API error:', result);
      message.error(result.message || '加载实训详情失败');
    }
  } catch (error) {
    console.error('获取实训详情失败:', error);
    message.error('加载实训详情失败');
  } finally {
    loading.value = false;
  }
}

// 启动环境
async function launchEnvironment() {
  if (!training.value) {
    message.error('请先加载实训信息');
    return;
  }

  launching.value = true;
  environmentStatus.value = 'starting';
  errorMessage.value = '';

  try {
    const currentUserId = requireCurrentUserId();
    
    // 启动环境并轮询直到就绪
    const status = await launchAndPoll(
      trainingId.value,
      currentUserId,
      {
        maxAttempts: 30,
        interval: 2000,
        onProgress: (status) => {
          console.log('环境启动进度:', status);
        }
      }
    );

    if (status.status === 'running' && status.url) {
      environmentStatus.value = 'running';
      // 确保 VNC URL 包含自动连接参数
      let url = status.url;
      if (url.includes('vnc.html')) {
        const urlObj = new URL(url);
        if (!urlObj.searchParams.has('autoconnect')) {
          urlObj.searchParams.set('autoconnect', 'true');
        }
        if (!urlObj.searchParams.has('resize')) {
          urlObj.searchParams.set('resize', 'scale');
        }
        url = urlObj.toString();
      }
      vncUrl.value = url;
      studentProgress.value.status = 'in_progress';
      message.success('实训环境启动成功！');
    } else {
      throw new Error('环境启动失败');
    }
  } catch (error: any) {
    console.error('启动环境失败:', error);
    environmentStatus.value = 'error';
    errorMessage.value = error.message || '环境启动失败，请重试';
    message.error(errorMessage.value);
  } finally {
    launching.value = false;
  }
}

// 重试启动
function retryLaunch() {
  launchEnvironment();
}

// VNC加载完成
function handleVncLoad() {
  console.log('[VNC调试] ========== VNC环境加载完成 ==========');
  
  // 确保 iframe 获得焦点并可以接收事件
  const iframe = vncFrame.value as HTMLIFrameElement;
  if (!iframe) {
    console.error('[VNC调试] iframe ref 不存在');
    return;
  }
  
  console.log('[VNC调试] iframe 元素找到:', {
    tagName: iframe.tagName,
    src: iframe.src,
    currentStyle: {
      display: iframe.style.display,
      height: iframe.style.height,
      width: iframe.style.width
    }
  });
  
  // 设置 iframe 为 block 显示，确保高度正确
  iframe.style.display = 'block';
  
  // 动态计算并设置高度
  const updateHeight = () => {
    console.log('[VNC调试] ========== 开始更新高度 ==========');
    
    const container = iframe.parentElement as HTMLElement;
    console.log('[VNC调试] 容器元素:', {
      exists: !!container,
      className: container?.className,
      tagName: container?.tagName
    });
    
    if (!container) {
      console.error('[VNC调试] 容器元素不存在');
      return;
    }
    
    // 查找所有父元素并记录它们的高度
    const parentChain: any[] = [];
    let current: HTMLElement | null = container;
    while (current && current !== document.body) {
      const rect = current.getBoundingClientRect();
      const style = window.getComputedStyle(current);
      parentChain.push({
        tag: current.tagName,
        class: current.className,
        rect: {
          width: rect.width,
          height: rect.height
        },
        style: {
          display: style.display,
          position: style.position,
          height: style.height,
          minHeight: style.minHeight,
          maxHeight: style.maxHeight,
          flex: style.flex,
          flexGrow: style.flexGrow,
          flexShrink: style.flexShrink,
          overflow: style.overflow
        }
      });
      current = current.parentElement;
    }
    
    console.log('[VNC调试] 父元素链:', parentChain);
    
    // 找到 panel-body（应该是容器的父元素）
    const panelBody = container.parentElement;
    console.log('[VNC调试] panel-body:', {
      exists: !!panelBody,
      className: panelBody?.className,
      rect: panelBody ? panelBody.getBoundingClientRect() : null,
      computedStyle: panelBody ? {
        height: window.getComputedStyle(panelBody).height,
        display: window.getComputedStyle(panelBody).display,
        flex: window.getComputedStyle(panelBody).flex
      } : null
    });
    
    if (!panelBody) {
      console.error('[VNC调试] panel-body 不存在');
      return;
    }
    
    const panelRect = panelBody.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();
    
    console.log('[VNC调试] 当前尺寸:', {
      panelBodyHeight: panelRect.height,
      containerHeight: containerRect.height,
      iframeHeight: iframe.getBoundingClientRect().height
    });
    
    // 如果 panel-body 高度为 0，尝试使用其他方法
    let targetHeight = panelRect.height;
    
    if (targetHeight === 0) {
      // 尝试从 vdi-panel 获取高度
      const vdiPanel = panelBody.closest('.vdi-panel') as HTMLElement;
      if (vdiPanel) {
        const vdiRect = vdiPanel.getBoundingClientRect();
        const panelHeader = vdiPanel.querySelector('.panel-header') as HTMLElement;
        const headerHeight = panelHeader ? panelHeader.getBoundingClientRect().height : 0;
        targetHeight = vdiRect.height - headerHeight;
        console.log('[VNC调试] 从 vdi-panel 计算高度:', {
          vdiPanelHeight: vdiRect.height,
          headerHeight: headerHeight,
          calculatedHeight: targetHeight
        });
      }
    }
    
    if (targetHeight === 0) {
      // 使用窗口高度减去其他元素
      const workspaceContent = panelBody.closest('.hx-workspace__body') as HTMLElement;
      if (workspaceContent) {
        const contentRect = workspaceContent.getBoundingClientRect();
        targetHeight = contentRect.height;
        console.log('[VNC调试] 从 hx-workspace__body 获取高度:', targetHeight);
      }
    }
    
    if (targetHeight > 0) {
      // 设置容器和 iframe 的高度
      container.style.position = 'absolute';
      container.style.top = '0';
      container.style.left = '0';
      container.style.right = '0';
      container.style.bottom = '0';
      container.style.height = targetHeight + 'px';
      
      iframe.style.height = targetHeight + 'px';
      iframe.style.width = '100%';
      
      // 等待一下再检查
      setTimeout(() => {
        const finalRect = iframe.getBoundingClientRect();
        console.log('[VNC调试] ✅ 高度更新完成:', {
          targetHeight: targetHeight,
          finalHeight: finalRect.height,
          finalWidth: finalRect.width,
          containerFinalHeight: container.getBoundingClientRect().height
        });
      }, 50);
    } else {
      console.warn('[VNC调试] ⚠️ 无法确定目标高度，所有父元素高度都为 0');
    }
  };
  
  // 使用 nextTick 等待 DOM 更新
  nextTick(() => {
    console.log('[VNC调试] nextTick 回调执行');
    updateHeight();
    
    // 延迟再次尝试，以防布局还未完成
    setTimeout(() => {
      console.log('[VNC调试] 延迟更新高度');
      updateHeight();
    }, 200);
    
    // 再延迟一次，确保布局完成
    setTimeout(() => {
      console.log('[VNC调试] 最终更新高度');
      updateHeight();
    }, 500);
  });
  
  // 监听窗口大小变化
  const resizeHandler = () => {
    console.log('[VNC调试] 窗口大小变化，更新高度');
    updateHeight();
  };
  window.addEventListener('resize', resizeHandler);
  
  // 使用 ResizeObserver 监听容器大小变化
  try {
    const resizeObserver = new ResizeObserver((entries) => {
      console.log('[VNC调试] ResizeObserver 触发:', entries.map(e => ({
        target: e.target.className,
        width: e.contentRect.width,
        height: e.contentRect.height
      })));
      updateHeight();
    });
    
    const containerForObserver = iframe.parentElement;
    if (containerForObserver) {
      const panelBodyForObserver = containerForObserver.parentElement;
      if (panelBodyForObserver) {
        resizeObserver.observe(panelBodyForObserver);
        console.log('[VNC调试] ResizeObserver 已注册');
      }
    }
  } catch (e) {
    console.warn('[VNC调试] ResizeObserver 不支持:', e);
  }
  
  // 尝试设置焦点
  try {
    iframe.focus();
    console.log('[VNC调试] iframe 焦点已设置');
  } catch (e) {
    console.warn('[VNC调试] 无法设置 iframe 焦点:', e);
  }
  
  // 添加鼠标事件监听，确保事件可以传递
  iframe.addEventListener('mouseenter', () => {
    console.log('[VNC调试] 鼠标进入 iframe');
    iframe.focus();
  });
  
  // 添加点击事件，确保 iframe 可以获得焦点
  iframe.addEventListener('click', (e) => {
    console.log('[VNC调试] iframe 被点击');
    iframe.focus();
    // 不阻止事件冒泡，让事件传递到 iframe 内部
  }, true);
  
  // 添加 mousedown 事件，确保焦点在点击时设置
  iframe.addEventListener('mousedown', (e) => {
    console.log('[VNC调试] iframe mousedown');
    iframe.focus();
  }, true);
  
  // 确保 iframe 可以接收指针事件
  iframe.style.pointerEvents = 'auto';
  iframe.style.zIndex = '1';
  
  // 确保容器也可以接收事件
  const container = iframe.parentElement as HTMLElement;
  if (container) {
    container.style.pointerEvents = 'auto';
    container.style.zIndex = '1';
  }
  
  // 尝试通过 postMessage 与 noVNC 通信（如果支持）
  try {
    const iframeWindow = iframe.contentWindow;
    if (iframeWindow) {
      // 等待 iframe 内容加载完成后再尝试通信
      setTimeout(() => {
        try {
          // 检查 noVNC 是否已连接
          if (iframeWindow.rfb) {
            console.log('[VNC调试] noVNC RFB 对象存在:', {
              connected: iframeWindow.rfb._connected,
              state: iframeWindow.rfb._state
            });
          } else {
            console.log('[VNC调试] noVNC RFB 对象不存在，等待初始化...');
          }
        } catch (e) {
          console.log('[VNC调试] 无法访问 iframe 内容（跨域限制）:', e.message);
        }
      }, 1000);
    }
  } catch (e) {
    console.warn('[VNC调试] 无法访问 iframe window:', e);
  }
  
  // 检查 iframe 尺寸
  const rect = iframe.getBoundingClientRect();
  console.log('[VNC调试] iframe 初始尺寸:', {
    width: rect.width,
    height: rect.height,
    computedHeight: window.getComputedStyle(iframe).height,
    computedWidth: window.getComputedStyle(iframe).width
  });
}

// 提交作业
async function handleSubmit() {
  if (!training.value) {
    message.error('请先加载实训信息');
    return;
  }

  // 检查是否满足提交要求
  if (training.value.require_design_files && designFileList.value.length === 0) {
    message.error('请上传设计文件（.knwf工作流文件）');
    return;
  }
  
  if (training.value.require_experiment_report && reportFileList.value.length === 0) {
    message.error('请上传实验报告');
    return;
  }

  submitting.value = true;
  try {
    const currentUserId = requireCurrentUserId();
    
    // 先上传文件
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
    const uploadResults = await Promise.all(uploadPromises);
    const uploadErrors = uploadResults.filter(r => r.code !== '0000');
    
    if (uploadErrors.length > 0) {
      message.error('文件上传失败，请重试');
      return;
    }
    
    // 提交作业
    const url = `/api/v1/trainings/${trainingId.value}/submit?classroom_id=${classroomId.value}&student_id=${currentUserId}&notes=${encodeURIComponent(submitNotes.value)}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken() || ''}`,
        'Content-Type': 'application/json'
      }
    });
    
    const result = await response.json();
    if (result.code === '0000') {
      message.success('作业已提交');
      studentProgress.value.status = 'submitted';
      studentProgress.value.completedPercentage = 100;
      showSubmitModal.value = false;
      
      // 清空文件列表
      designFileList.value = [];
      reportFileList.value = [];
      submitNotes.value = '';
      
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

// 文件上传前检查
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

function handleRemoveDesignFile() {
  designFileList.value = [];
}

function handleRemoveReport() {
  reportFileList.value = [];
}

// 环境管理操作
function handleEnvironmentAction({ key }: { key: string }) {
  switch (key) {
    case 'restart':
      if (environmentStatus.value === 'running') {
        message.info('重启环境功能开发中');
      }
      break;
    case 'stop':
      if (environmentStatus.value === 'running') {
        message.info('停止环境功能开发中');
      }
      break;
  }
}

// 切换手册面板
function toggleHandbookPanel() {
  handbookCollapsed.value = !handbookCollapsed.value;
}

// 调整面板大小
function startResize(e: MouseEvent) {
  isResizing.value = true;
  const startX = e.clientX;
  const startWidth = vdiPanelWidth.value;

  function onMouseMove(e: MouseEvent) {
    const diff = startX - e.clientX; // 向左拖拽增加宽度
    const newWidth = Math.max(400, Math.min(1200, startWidth + diff));
    vdiPanelWidth.value = newWidth;
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
function getStatusText(status: string) {
  const texts: any = {
    idle: '未启动',
    starting: '启动中',
    running: '运行中',
    error: '错误'
  };
  return texts[status] || status;
}

function getScoreClass(score: number) {
  if (score >= 90) return 'score-excellent';
  if (score >= 80) return 'score-good';
  if (score >= 60) return 'score-pass';
  return 'score-fail';
}

function formatDate(dateStr: string) {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString('zh-CN');
}

// 生命周期
onMounted(() => {
  fetchTrainingDetail();
  // 如果URL中有环境URL，直接使用（环境已启动）
  if (route.query.envUrl) {
    let url = route.query.envUrl as string;
    // 确保 VNC URL 包含自动连接参数
    if (url.includes('vnc.html')) {
      const urlObj = new URL(url);
      if (!urlObj.searchParams.has('autoconnect')) {
        urlObj.searchParams.set('autoconnect', 'true');
      }
      if (!urlObj.searchParams.has('resize')) {
        urlObj.searchParams.set('resize', 'scale');
      }
      url = urlObj.toString();
    }
    vncUrl.value = url;
    environmentStatus.value = 'running';
    studentProgress.value.status = 'in_progress';
    console.log('从URL参数获取环境URL:', vncUrl.value);
  } else if (route.query.autoLaunch === 'true') {
    // 如果URL中有启动参数，自动启动环境
    setTimeout(() => {
      launchEnvironment();
    }, 500);
  }
});

onUnmounted(() => {
  // 清理事件监听
  if (isResizing.value) {
    isResizing.value = false;
  }
});
</script>

<style scoped lang="less">
/* 全高 shell：禁止再加外层 padding:24 压矮编辑器 */
.hx-workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--hx-header-height));
  background: var(--hx-color-bg-layout);
  overflow: hidden;
}

.hx-workspace__toolbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--hx-space-2);
  padding: var(--hx-space-2) var(--hx-space-4);
  background: var(--hx-color-bg-container);
  border-bottom: 1px solid var(--hx-color-border-muted);

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--hx-space-3);
    min-width: 0;

    .training-title {
      font-size: var(--hx-font-size-base);
      font-weight: 600;
      color: var(--hx-color-text-primary);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: var(--hx-space-2);
    flex-shrink: 0;
  }
}

.hx-workspace__body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  gap: var(--hx-space-2);
  overflow: hidden;

  .handbook-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: var(--hx-color-bg-container);
    border-right: 1px solid var(--hx-color-border-muted);
    overflow: hidden;
    min-width: 0;

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--hx-space-3) var(--hx-space-4);
      border-bottom: 1px solid var(--hx-color-border-muted);
      background: var(--hx-color-bg-layout);

      h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--hx-color-text-primary);
      }
    }

    .panel-body {
      flex: 1;
      overflow-y: auto;
      padding: var(--hx-space-4);
      min-height: 0;

      .handbook-content {
        max-width: 900px;
        margin: 0 auto;

        :deep(.markdown-body) {
          h1, h2, h3 {
            margin-top: var(--hx-space-5);
            margin-bottom: var(--hx-space-3);
            color: var(--hx-color-text-primary);
          }

          p {
            line-height: 1.8;
            color: var(--hx-color-text-secondary);
            margin-bottom: var(--hx-space-3);
          }

          ul, ol {
            padding-left: var(--hx-space-5);
            margin-bottom: var(--hx-space-3);

            li {
              line-height: 1.8;
              color: var(--hx-color-text-secondary);
              margin-bottom: var(--hx-space-2);
            }
          }

          code {
            background: var(--hx-color-bg-layout);
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
          }

          pre {
            background: var(--hx-color-bg-layout);
            padding: var(--hx-space-3);
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
            margin-bottom: var(--hx-space-4);

            th, td {
              border: 1px solid var(--hx-color-border-muted);
              padding: var(--hx-space-2) var(--hx-space-3);
              text-align: left;
            }

            th {
              background: var(--hx-color-bg-layout);
              font-weight: 600;
            }
          }
        }
      }
    }
  }

  .resizer {
    width: 4px;
    background: var(--hx-color-border-muted);
    cursor: col-resize;
    flex-shrink: 0;

    &:hover {
      background: var(--hx-color-primary);
    }
  }

  .vdi-panel {
    display: flex;
    flex-direction: column;
    background: var(--hx-color-bg-container);
    overflow: hidden;
    min-width: 400px;
    min-height: 0;

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: var(--hx-space-3) var(--hx-space-4);
      border-bottom: 1px solid var(--hx-color-border-muted);
      background: var(--hx-color-bg-layout);

      h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: var(--hx-color-text-primary);
      }

      .environment-status {
        display: flex;
        align-items: center;
        gap: var(--hx-space-2);
        font-size: 12px;
        color: var(--hx-color-text-tertiary);
      }
    }

    .panel-body {
      flex: 1;
      position: relative;
      overflow: hidden;
      pointer-events: auto;
      min-height: 0;

      .vdi-container {
        width: 100%;
        height: 100%;
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: auto;
        z-index: 1;

        iframe {
          border: none;
          display: block;
          width: 100%;
          height: 100%;
          pointer-events: auto;
          touch-action: none;
          z-index: 1;
        }
      }

      .error-container,
      .empty-container {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
      }
    }
  }
}

.submit-form {
  .upload-section {
    margin-bottom: 16px;

    .section-title {
      font-weight: 600;
      margin-bottom: 8px;
      color: #262626;
    }

    .file-info {
      margin-top: 8px;
      padding: 8px;
      background: #f5f5f5;
      border-radius: 4px;
      display: flex;
      justify-content: space-between;
      align-items: center;
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
  margin-top: 24px;

  .grade-info {
    .grade-item {
      margin-bottom: 16px;

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
        font-size: 24px;
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
        padding: 12px;
        background: #f5f5f5;
        border-radius: 4px;
        color: #595959;
        line-height: 1.6;
      }
    }
  }
}
</style>
