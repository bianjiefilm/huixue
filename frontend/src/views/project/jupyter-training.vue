<template>
  <div class="jupyter-training-page">
    <!-- 顶部状态栏 -->
    <div class="training-header">
      <div class="header-left">
        <span class="project-name">{{ projectName }}</span>
      </div>

      <div class="header-center">
        <!-- 倒计时显示 -->
        <div class="countdown-display">
          <ClockCircleOutlined class="countdown-icon" />
          <span class="countdown-time">{{ formatTime(remainingTime) }}</span>
        </div>
      </div>

      <div class="header-right">
        <!-- 延时按钮 -->
        <a-tooltip title="延长30分钟（剩余时间少于20分钟时可用）">
          <a-button
            :type="canExtend ? 'primary' : 'default'"
            :disabled="!canExtend"
            @click="handleExtendTime"
            :loading="extending"
            class="action-btn"
          >
            <FieldTimeOutlined />
            <span>延时</span>
          </a-button>
        </a-tooltip>

        <a-divider type="vertical" />

        <!-- 重置环境 -->
        <a-tooltip title="重置环境（不影响代码）">
          <a-button @click="showResetEnvConfirm" class="action-btn">
            <SyncOutlined />
            <span>重置环境</span>
          </a-button>
        </a-tooltip>

        <!-- 重置代码仓库 -->
        <a-tooltip title="重置代码仓库（恢复初始状态）">
          <a-button @click="showResetRepoConfirm" class="action-btn" danger>
            <RollbackOutlined />
            <span>重置代码</span>
          </a-button>
        </a-tooltip>

        <a-divider type="vertical" />

        <!-- 用户信息 -->
        <div class="user-info">
          <a-avatar :src="userStore.userInfo.avatar" size="small" />
          <span class="user-name">{{ userStore.userInfo.nickname || '用户' }}</span>
        </div>

        <a-divider type="vertical" />

        <!-- 退出按钮 -->
        <a-tooltip title="退出实训环境">
          <a-button type="text" @click="handleExit" class="exit-btn">
            <PoweroffOutlined />
          </a-button>
        </a-tooltip>
      </div>
    </div>

    <!-- Jupyter容器 -->
    <div class="jupyter-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-overlay">
        <a-spin size="large" tip="正在启动 Jupyter 环境..." />
      </div>

      <!-- 模拟模式提示 -->
      <div v-else-if="mockMode" class="mock-jupyter">
        <div class="mock-header">
          <div class="jupyter-logo">
            <img src="https://jupyter.org/assets/homepage/main-logo.svg" alt="Jupyter" style="height: 40px;" />
          </div>
          <div class="mock-toolbar">
            <a-button size="small"><SaveOutlined /> 保存</a-button>
            <a-button size="small"><PlusOutlined /> 插入</a-button>
            <a-button size="small" type="primary"><CaretRightOutlined /> 运行</a-button>
            <a-button size="small"><StopOutlined /> 停止</a-button>
            <a-button size="small"><ReloadOutlined /> 重启内核</a-button>
          </div>
        </div>
        <div class="mock-notebook">
          <div class="notebook-cell markdown">
            <div class="cell-content">
              <h1># 欢迎使用 Jupyter Notebook</h1>
              <p>这是一个编码式实训环境演示</p>
            </div>
          </div>
          <div class="notebook-cell code">
            <div class="cell-prompt">In [1]:</div>
            <div class="cell-input">
              <pre>import pandas as pd
import numpy as np

# 读取数据集
df = pd.read_csv('/home/jovyan/work/datasets/data.csv')
df.head()</pre>
            </div>
          </div>
          <div class="notebook-cell code">
            <div class="cell-prompt">In [2]:</div>
            <div class="cell-input">
              <pre>print("Hello, Jupyter!")</pre>
            </div>
            <div class="cell-output">
              <div class="output-prompt">Out[2]:</div>
              <pre>Hello, Jupyter!</pre>
            </div>
          </div>
          <div class="notebook-cell code empty">
            <div class="cell-prompt">In [ ]:</div>
            <div class="cell-input">
              <textarea placeholder="在此输入代码..."></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- 真实Jupyter iframe -->
      <iframe
        v-else
        ref="jupyterFrame"
        :src="jupyterUrl"
        frameborder="0"
        class="jupyter-iframe"
        @load="handleJupyterLoad"
      ></iframe>
    </div>

    <!-- 右侧悬浮侧栏按钮 -->
    <div class="floating-sidebar">
      <div class="sidebar-btn" @click="showDatasets = true">
        <DatabaseOutlined />
        <span>数据集</span>
      </div>
      <div class="sidebar-btn" @click="showManual = true">
        <BookOutlined />
        <span>实训手册</span>
      </div>
    </div>

    <!-- 数据集抽屉 -->
    <a-drawer
      v-model:open="showDatasets"
      title="数据集"
      placement="right"
      :width="400"
      class="dataset-drawer"
    >
      <a-spin :spinning="loadingDatasets">
        <div class="dataset-list">
          <a-empty v-if="datasets.length === 0" description="暂无数据集" />
          <div v-else>
            <div v-for="dataset in datasets" :key="dataset.id" class="dataset-item">
              <div class="dataset-main">
                <FileTextOutlined class="file-icon" />
                <div class="dataset-info">
                  <div class="dataset-name">{{ dataset.name }}</div>
                  <div class="dataset-size">{{ formatFileSize(dataset.size) }}</div>
                </div>
              </div>
              <div class="dataset-actions">
                <a-tooltip title="复制路径">
                  <a-button type="text" size="small" @click="copyDatasetPath(dataset.path)">
                    <CopyOutlined />
                  </a-button>
                </a-tooltip>
                <a-tooltip title="下载">
                  <a-button type="text" size="small" @click="downloadDataset(dataset)">
                    <DownloadOutlined />
                  </a-button>
                </a-tooltip>
              </div>
            </div>
          </div>
        </div>
      </a-spin>
    </a-drawer>

    <!-- 实训手册抽屉 -->
    <a-drawer
      v-model:open="showManual"
      title="实训手册"
      placement="right"
      :width="520"
      class="manual-drawer"
    >
      <a-spin :spinning="loadingManual">
        <div class="manual-toc" v-if="manualToc.length > 0">
          <h4>目录</h4>
          <a-anchor :items="manualToc" @click="handleTocClick" />
        </div>
        <a-divider v-if="manualToc.length > 0" />
        <div class="manual-content" v-html="manualContent"></div>
      </a-spin>
    </a-drawer>

    <!-- 环境到期遮罩 -->
    <div v-if="environmentExpired" class="expired-overlay">
      <div class="expired-content">
        <ClockCircleOutlined class="expired-icon" />
        <h2>实训环境已到期</h2>
        <p>您的实训时间已用完，环境将自动关闭</p>
        <a-button type="primary" @click="goBack">返回项目页面</a-button>
      </div>
    </div>

    <!-- 重置确认弹窗 -->
    <a-modal
      v-model:open="showResetConfirm"
      :title="resetConfirmTitle"
      @ok="confirmReset"
      @cancel="showResetConfirm = false"
      :confirmLoading="resetting"
      :okButtonProps="{ danger: resetAction === 'repo' }"
    >
      <a-alert
        :message="resetWarningMessage"
        :type="resetAction === 'repo' ? 'error' : 'warning'"
        show-icon
        style="margin-bottom: 16px"
      />
      <p>{{ resetConfirmMessage }}</p>
    </a-modal>

    <!-- 退出确认弹窗 -->
    <a-modal
      v-model:open="showExitConfirm"
      title="确认退出"
      @ok="confirmExit"
      @cancel="showExitConfirm = false"
    >
      <p>确定要退出实训环境吗？</p>
      <p class="exit-hint">您的代码会自动保存，下次进入可继续编辑。</p>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import {
  ClockCircleOutlined,
  FieldTimeOutlined,
  SyncOutlined,
  RollbackOutlined,
  PoweroffOutlined,
  DatabaseOutlined,
  BookOutlined,
  FileTextOutlined,
  CopyOutlined,
  DownloadOutlined,
  SaveOutlined,
  PlusOutlined,
  CaretRightOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons-vue';
import { useUserStore } from '@/stores/user';
import {
  launchJupyterEnvironment,
  extendEnvironmentTime,
  resetEnvironment,
  resetCodeRepository,
  getProjectDatasets,
  getTrainingManual
} from '@/api/training';
import type { Dataset, LaunchEnvironmentResponse } from '@/api/types/project';
import MarkdownIt from 'markdown-it';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 状态
const projectId = ref(route.params.id as string || '');
const projectName = ref('Jupyter编码式实训');
const jupyterUrl = ref('');
const envId = ref('');
const remainingTime = ref(1800); // 30分钟
const loading = ref(true);
const mockMode = ref(false);
const extending = ref(false);
const resetting = ref(false);
const loadingDatasets = ref(false);
const loadingManual = ref(false);
const showDatasets = ref(false);
const showManual = ref(false);
const showResetConfirm = ref(false);
const showExitConfirm = ref(false);
const resetAction = ref<'env' | 'repo'>('env');
const datasets = ref<Dataset[]>([]);
const manualContent = ref('');
const manualToc = ref<any[]>([]);
const environmentExpired = ref(false);

// Markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

// 计算属性
const canExtend = computed(() => remainingTime.value < 1200); // 少于20分钟时可延时

const resetConfirmTitle = computed(() => {
  return resetAction.value === 'env' ? '确认重置环境' : '确认重置代码仓库';
});

const resetWarningMessage = computed(() => {
  return resetAction.value === 'env'
    ? '重置环境将重启Jupyter服务，但不会影响您的代码'
    : '警告：重置代码仓库将删除所有修改，恢复到初始状态，此操作不可撤销！';
});

const resetConfirmMessage = computed(() => {
  return resetAction.value === 'env'
    ? '确定要重置环境吗？Jupyter服务将重启。'
    : '您确定要重置代码仓库吗？用户新建的文件将被删除，预置文件将恢复初始内容。';
});

// 倒计时
const countdownInterval = ref<any>(null);

const startCountdown = () => {
  countdownInterval.value = setInterval(() => {
    if (remainingTime.value > 0) {
      remainingTime.value--;
    } else {
      clearInterval(countdownInterval.value);
      environmentExpired.value = true;
    }
  }, 1000);
};

const formatTime = (seconds: number) => {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 启动Jupyter环境
const launchJupyter = async () => {
  try {
    loading.value = true;
    const response: any = await launchJupyterEnvironment(projectId.value);
    // 动态生成 Jupyter URL，根据当前访问的主机名和后端返回的端口
    // 优先使用后端返回的完整URL（推荐方式）
    const hostname = window.location.hostname;

    // 优先使用后端返回的完整URL，否则使用host_port构造
    if (response.url) {
      jupyterUrl.value = response.url;
    } else {
      // 从response中获取host_port
      const port = response.host_port || 8888;
      // 如果是本地访问或VPN IP，使用实际访问的hostname
      // 这样可以确保正确访问Docker Swarm暴露的端口
      const jupyterBaseUrl = `http://${hostname}:${port}`;
      jupyterUrl.value = `${jupyterBaseUrl}/lab?token=huixue_token`;
    }
    envId.value = response.envId;
    remainingTime.value = response.remainingTime * 60;
    mockMode.value = false;
    startCountdown();
  } catch (error) {
    console.error('启动Jupyter环境失败，使用模拟模式:', error);
    // 使用模拟模式
    mockMode.value = true;
    startCountdown();
    message.info('Jupyter服务暂不可用，当前为演示模式');
  } finally {
    loading.value = false;
  }
};

// 延长时间
const handleExtendTime = async () => {
  if (!canExtend.value) return;

  try {
    extending.value = true;
    if (!mockMode.value) {
      await extendEnvironmentTime(envId.value, { minutes: 30 });
    }
    remainingTime.value += 1800;
    message.success('已延长30分钟');
  } catch (error) {
    console.error('延时失败:', error);
    message.error('延时失败，请重试');
  } finally {
    extending.value = false;
  }
};

// 重置操作
const showResetEnvConfirm = () => {
  resetAction.value = 'env';
  showResetConfirm.value = true;
};

const showResetRepoConfirm = () => {
  resetAction.value = 'repo';
  showResetConfirm.value = true;
};

const confirmReset = async () => {
  try {
    resetting.value = true;

    if (!mockMode.value) {
      if (resetAction.value === 'env') {
        await resetEnvironment(envId.value);
      } else {
        await resetCodeRepository(envId.value);
      }
    }

    message.success(resetAction.value === 'env' ? '环境重置成功' : '代码仓库已重置');
    showResetConfirm.value = false;

    // 刷新Jupyter
    if (jupyterFrame.value && !mockMode.value) {
      jupyterFrame.value.src = jupyterUrl.value;
    }
  } catch (error) {
    console.error('重置失败:', error);
    message.error('操作失败，请重试');
  } finally {
    resetting.value = false;
  }
};

// 退出
const handleExit = () => {
  showExitConfirm.value = true;
};

const confirmExit = () => {
  showExitConfirm.value = false;
  goBack();
};

const goBack = () => {
  router.push(`/project/${projectId.value}`);
};

// 数据集操作
const fetchDatasets = async () => {
  try {
    loadingDatasets.value = true;
    datasets.value = await getProjectDatasets(projectId.value);
  } catch (error) {
    console.error('获取数据集失败:', error);
    // 使用模拟数据
    datasets.value = [
      { id: '1', name: 'data.csv', path: '/home/jovyan/work/datasets/data.csv', size: 1024000, description: '主数据集' },
      { id: '2', name: 'train.csv', path: '/home/jovyan/work/datasets/train.csv', size: 512000, description: '训练数据' },
      { id: '3', name: 'test.csv', path: '/home/jovyan/work/datasets/test.csv', size: 256000, description: '测试数据' }
    ];
  } finally {
    loadingDatasets.value = false;
  }
};

const copyDatasetPath = (path: string) => {
  navigator.clipboard.writeText(path).then(() => {
    message.success('路径已复制到剪贴板');
  }).catch(() => {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = path;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    message.success('路径已复制到剪贴板');
  });
};

const downloadDataset = (dataset: Dataset) => {
  message.info('开始下载: ' + dataset.name);
  const link = document.createElement('a');
  link.href = `/api/v1/datasets/${dataset.id}/download`;
  link.download = dataset.name;
  link.click();
};

// 获取实训手册
const fetchManual = async () => {
  try {
    loadingManual.value = true;
    const content = await getTrainingManual(projectId.value);
    manualContent.value = md.render(content);
    // 生成目录
    generateToc(content);
  } catch (error) {
    console.error('获取实训手册失败:', error);
    manualContent.value = `
      <h1>实训手册</h1>
      <h2>1. 实训概述</h2>
      <p>本实训将指导您使用 Jupyter Notebook 进行数据分析和机器学习实践。</p>
      <h2>2. 实训目标</h2>
      <ul>
        <li>掌握 Jupyter Notebook 的基本操作</li>
        <li>学会使用 Python 进行数据处理</li>
        <li>完成数据可视化分析</li>
      </ul>
      <h2>3. 实训步骤</h2>
      <h3>3.1 数据加载</h3>
      <p>使用 pandas 库读取数据集...</p>
      <h3>3.2 数据探索</h3>
      <p>查看数据基本信息...</p>
      <h3>3.3 数据可视化</h3>
      <p>使用 matplotlib 绑制图表...</p>
    `;
    manualToc.value = [
      { key: '1', href: '#1', title: '1. 实训概述' },
      { key: '2', href: '#2', title: '2. 实训目标' },
      { key: '3', href: '#3', title: '3. 实训步骤', children: [
        { key: '3-1', href: '#3-1', title: '3.1 数据加载' },
        { key: '3-2', href: '#3-2', title: '3.2 数据探索' },
        { key: '3-3', href: '#3-3', title: '3.3 数据可视化' }
      ]}
    ];
  } finally {
    loadingManual.value = false;
  }
};

const generateToc = (content: string) => {
  const headings = content.match(/^#{1,3}\s+.+$/gm) || [];
  manualToc.value = headings.map((h, i) => ({
    key: String(i),
    href: `#heading-${i}`,
    title: h.replace(/^#+\s+/, '')
  }));
};

const handleTocClick = (e: Event, link: { href: string }) => {
  e.preventDefault();
  const el = document.querySelector(link.href);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth' });
  }
};

// Jupyter加载完成
const jupyterFrame = ref<HTMLIFrameElement | null>(null);
const handleJupyterLoad = () => {
  console.log('Jupyter环境加载完成');
};

// 生命周期
onMounted(() => {
  launchJupyter();
  fetchDatasets();
  fetchManual();
});

onUnmounted(() => {
  if (countdownInterval.value) {
    clearInterval(countdownInterval.value);
  }
});
</script>

<style scoped>
.jupyter-training-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #fafafa;
}

/* 顶部状态栏 */
.training-header {
  height: 48px;
  background: #fafafa;
  border-bottom: 1px solid #3c3c3c;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-name {
  font-size: 14px;
  font-weight: 500;
  color: #cccccc;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.countdown-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a5a 100%);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.countdown-icon {
  color: #fff;
  font-size: 16px;
}

.countdown-time {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  font-family: 'Monaco', 'Consolas', monospace;
  letter-spacing: 2px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  color: #cccccc;
  font-size: 13px;
}

.exit-btn {
  color: #ff6b6b;
  font-size: 18px;
}

.exit-btn:hover {
  color: #ff4d4d;
  background: rgba(255, 77, 77, 0.1);
}

/* Jupyter容器 */
.jupyter-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.jupyter-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
}

/* 模拟Jupyter */
.mock-jupyter {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.mock-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: #f7f7f7;
  border-bottom: 1px solid #e0e0e0;
}

.jupyter-logo {
  display: flex;
  align-items: center;
}

.mock-toolbar {
  display: flex;
  gap: 8px;
}

.mock-notebook {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.notebook-cell {
  margin-bottom: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
}

.notebook-cell.markdown {
  padding: 16px;
  background: #fff;
}

.notebook-cell.code {
  background: #f7f7f7;
}

.cell-prompt {
  padding: 8px 12px;
  color: #303f9f;
  font-family: monospace;
  font-weight: bold;
  background: #e8eaf6;
}

.cell-input {
  padding: 12px;
  background: #fafafa;
}

.cell-input pre {
  margin: 0;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.5;
}

.cell-input textarea {
  width: 100%;
  min-height: 60px;
  border: none;
  background: transparent;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  resize: vertical;
  outline: none;
}

.cell-output {
  padding: 12px;
  background: #fff;
  border-top: 1px solid #e0e0e0;
}

.output-prompt {
  color: #d84315;
  font-family: monospace;
  font-weight: bold;
  margin-bottom: 8px;
}

/* 右侧悬浮侧栏 */
.floating-sidebar {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 100;
}

.sidebar-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 10px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  border-radius: 8px 0 0 8px;
  box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s;
  writing-mode: horizontal-tb;
}

.sidebar-btn:first-child {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.sidebar-btn:hover {
  padding-right: 16px;
}

.sidebar-btn span {
  writing-mode: vertical-rl;
  text-orientation: mixed;
}

/* 数据集抽屉 */
.dataset-list {
  padding: 8px 0;
}

.dataset-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.dataset-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.dataset-main {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
  color: #1890ff;
}

.dataset-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
}

.dataset-size {
  font-size: 12px;
  color: #8c8c8c;
}

.dataset-actions {
  display: flex;
  gap: 4px;
}

/* 实训手册 */
.manual-toc {
  margin-bottom: 16px;
}

.manual-toc h4 {
  margin-bottom: 12px;
  color: #262626;
}

.manual-content {
  padding: 0 4px;
  line-height: 1.8;
}

.manual-content :deep(h1) {
  font-size: 22px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.manual-content :deep(h2) {
  font-size: 18px;
  margin-top: 24px;
  margin-bottom: 12px;
}

.manual-content :deep(h3) {
  font-size: 16px;
  margin-top: 16px;
  margin-bottom: 8px;
}

.manual-content :deep(pre) {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

.manual-content :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
}

/* 到期遮罩 */
.expired-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.expired-content {
  text-align: center;
  color: #fff;
}

.expired-icon {
  font-size: 64px;
  color: #ff6b6b;
  margin-bottom: 24px;
}

.expired-content h2 {
  font-size: 24px;
  margin-bottom: 12px;
}

.expired-content p {
  color: #999;
  margin-bottom: 24px;
}

.exit-hint {
  color: #8c8c8c;
  font-size: 13px;
}

/* Ant Design 分隔线 */
:deep(.ant-divider-vertical) {
  background: #3c3c3c;
  height: 20px;
}
</style>
