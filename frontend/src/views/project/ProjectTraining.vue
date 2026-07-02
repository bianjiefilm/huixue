<template>
  <div class="project-training">
    <JupyterLite :url="jupyterUrl" />
    
    <!-- 右侧悬浮按钮 -->
    <div class="float-buttons">
      <a-button type="primary" @click="showDatasetDrawer">
        数据集
      </a-button>
      <a-button type="primary" style="margin-top: 16px" @click="showManualDrawer">
        实训手册
      </a-button>
    </div>

    <!-- 数据集抽屉 -->
    <a-drawer
      title="数据集"
      placement="right"
      :width="400"
      :open="datasetDrawerVisible"
      @close="closeDatasetDrawer"
    >
      <a-spin :spinning="loadingDatasets">
        <a-list :data-source="datasetList" :bordered="true">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-space>
                <span>{{ item.name }}</span>
                <span class="dataset-size">{{ item.size }}</span>
                <a-button type="link" @click="copyPath(item.storage_path)">复制路径</a-button>
                <a-button type="link" @click="downloadFile(item.storage_path)">下载</a-button>
              </a-space>
              <div class="dataset-desc">{{ item.description }}</div>
            </a-list-item>
          </template>
        </a-list>
      </a-spin>
    </a-drawer>

    <!-- 实训手册抽屉 -->
    <a-drawer
      title="实训手册"
      placement="right"
      :width="600"
      :open="manualDrawerVisible"
      @close="closeManualDrawer"
    >
      <a-spin :spinning="loadingManual">
        <a-typography>
          <a-typography-title :level="2">{{ trainingData.name }}</a-typography-title>
          <a-typography-paragraph>
            {{ trainingData.intro || trainingData.description }}
          </a-typography-paragraph>
          <a-typography-title :level="3">任务目标</a-typography-title>
          <a-typography-paragraph>
            <ul>
              <li v-for="(task, index) in trainingData.tasks" :key="index">
                {{ task }}
              </li>
            </ul>
          </a-typography-paragraph>
          
          <a-divider />
          
          <a-typography-title :level="3">实施步骤</a-typography-title>
          <a-collapse v-model:activeKey="activeStepKey" accordion>
            <a-collapse-panel v-for="(step, index) in trainingData.steps" :key="index.toString()" :header="step.title">
              <p>{{ step.content }}</p>
            </a-collapse-panel>
          </a-collapse>
        </a-typography>
      </a-spin>
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import JupyterLite from '@/components/JupyterLite.vue';
import { message } from 'ant-design-vue';
import axios from 'axios';
import { getProjectDetail } from '@/api/training';
import { getTrainingHandbook, getTrainingDatasets } from '@/api/training-environments';

const route = useRoute();
const trainingType = route.query.type?.toString() || 'default';

// 状态变量
const loadingDatasets = ref(false);
const loadingManual = ref(false);
const datasetList = ref([]);
// Jupyter URL - 动态获取服务器地址
const getJupyterUrl = () => {
  const hostname = window.location.hostname;
  // 如果是 localhost 或 127.0.0.1，使用 localhost，否则使用 hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8888/lab?token=huixue_token';
  }
  // 对于远程服务器，使用当前域名访问 Jupyter
  return `http://${hostname}:8888/lab?token=huixue_token`;
};
const jupyterUrl = ref(getJupyterUrl());
const projectInfo=ref([]);
const trainingData = ref({
  title: '',
  description: '',
  tasks: [],
  steps: [] as Array<{ title: string; content: string }>
});
const activeStepKey = ref(['0']); // 默认展开第一个步骤

// 抽屉状态
const datasetDrawerVisible = ref(false);
const manualDrawerVisible = ref(false);
const fetchProjects = async () => {
	loadingManual.value=true;
  try {
    const response = await getProjectDetail('1');
    projectInfo.value = response;
	fetchTrainingManual();
  } catch (error) {
    message.error('获取失败，请稍后重试');
  }finally {
    loadingManual.value = false;
  }
};
// 获取数据集列表
const fetchDatasets = async () => {
  try {
    loadingDatasets.value = true;
    const trainingId = Number(route.params.id || route.query.id || 1); // 获取实训ID

    // 使用真实API获取数据集
    const response = await getTrainingDatasets(trainingId);
    datasetList.value = response.data?.datasets || response.datasets || [];

    // 如果API失败，使用备用数据
    if (!datasetList.value.length && projectInfo.value.dataset) {
      datasetList.value = [projectInfo.value.dataset];
    }
  } catch (error) {
    console.error('获取数据集失败:', error);
    // 使用备用数据
    if (projectInfo.value.dataset) {
      datasetList.value = [projectInfo.value.dataset];
    } else {
      message.error('获取数据集失败，请稍后重试');
    }
  } finally {
    loadingDatasets.value = false;
  }
};

// 获取实训手册数据
const fetchTrainingManual = async () => {
  try {
    loadingManual.value = true;
    const trainingId = Number(route.params.id || route.query.id || 1); // 获取实训ID

    // 使用真实API获取手册
    const response = await getTrainingHandbook(trainingId);
    const content = response.data?.content || response.content || '';

    // 解析Markdown内容为结构化数据
    if (content) {
      // 简单解析Markdown内容
      const lines = content.split('\n');
      let currentStep = 0;
      const steps = [];
      let inSteps = false;

      for (const line of lines) {
        if (line.includes('实训简介') || line.includes('简介')) {
          trainingData.value.description = lines[lines.indexOf(line) + 1] || '';
        }
        if (line.includes('学习目标')) {
          const tasksStart = lines.indexOf(line) + 1;
          const tasks = [];
          for (let i = tasksStart; i < lines.length && lines[i].startsWith('-'); i++) {
            tasks.push(lines[i].replace(/^-\s*/, ''));
          }
          trainingData.value.tasks = tasks;
        }
        if (line.includes('### ') && line.includes('步骤')) {
          inSteps = true;
        }
        if (inSteps && line.match(/^\d+\./)) {
          steps.push({
            title: `步骤 ${++currentStep}`,
            content: line.replace(/^\d+\.\s*/, '')
          });
        }
      }

      if (steps.length > 0) {
        trainingData.value.steps = steps;
      }
    }

    // 如果API失败或解析失败，使用备用数据
    if (!trainingData.value.tasks.length && projectInfo.value.jupyter_file) {
      trainingData.value = projectInfo.value.jupyter_file;
    }
  } catch (error) {
    console.error('获取实训手册失败:', error);
    // 使用备用数据
    if (projectInfo.value.jupyter_file) {
      trainingData.value = projectInfo.value.jupyter_file;
    } else {
      message.error('获取实训手册失败，请稍后重试');
    }
  } finally {
    loadingManual.value = false;
  }
};

// 抽屉控制函数
const showDatasetDrawer = () => {
  if (datasetList.value.length === 0) {
    fetchDatasets();
  }
  datasetDrawerVisible.value = true;
};

const closeDatasetDrawer = () => {
  datasetDrawerVisible.value = false;
};

const showManualDrawer = () => {
  manualDrawerVisible.value = true;
};

const closeManualDrawer = () => {
  manualDrawerVisible.value = false;
};

// 复制路径
const copyPath = (path: string) => {
  navigator.clipboard.writeText(path).then(() => {
    message.success('路径已复制到剪贴板');
  });
};

// 下载文件
const downloadFile = (path: string) => {
  // 实际项目中需要调用后端API
  message.success(`开始下载文件: ${path}`);
};

// 生命周期钩子
onMounted(() => {
  // 提前加载实训手册数据
  fetchProjects();
});
</script>

<style scoped>
.project-training {
  position: relative;
  width: 100%;
  height: 100%;
}

.float-buttons {
  position: fixed;
  right: 20px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.dataset-size {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.dataset-desc {
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
  margin-top: 4px;
}
</style> 