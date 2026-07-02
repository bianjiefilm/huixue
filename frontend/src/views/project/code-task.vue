<template>
  <div class="training-code-page">
    <div class="topbar">
      <a-button @click="goBack">返回实训详情</a-button>
      <div class="title-block">
        <h1>{{ task?.title || '编程实训' }}</h1>
        <span v-if="task" class="meta">
          第 {{ task.order_in_training }} 关 · {{ difficultyText }} · {{ task.match_rule }}
        </span>
      </div>
    </div>

    <a-spin :spinning="loading">
      <a-row :gutter="16" class="workspace">
        <a-col :xs="24" :lg="6">
          <div class="panel task-list-panel">
            <div class="panel-title">关卡列表</div>
            <a-empty v-if="tasks.length === 0" description="暂无编程关卡" />
            <button
              v-for="item in tasks"
              :key="item.id"
              class="task-item"
              :class="{ active: item.id === Number(taskId) }"
              @click="openTask(item.id)"
            >
              <span>{{ item.order_in_training }}. {{ item.title }}</span>
              <small>{{ item.difficulty || 'beginner' }}</small>
            </button>
          </div>
        </a-col>

        <a-col :xs="24" :lg="9">
          <div class="panel handbook-panel">
            <div class="panel-title">任务手册</div>
            <div v-if="task?.handbook_markdown" class="handbook" v-html="renderedHandbook"></div>
            <a-empty v-else description="暂无手册内容" />
          </div>
        </a-col>

        <a-col :xs="24" :lg="9">
          <div class="panel editor-panel">
            <div class="editor-header">
              <div>
                <div class="panel-title">代码编辑器</div>
                <span class="meta">Python 3 · Monaco</span>
              </div>
              <div class="editor-actions">
                <a-button type="primary" :loading="submitting" @click="submitCode">
                  提交评测
                </a-button>
                <a-dropdown :trigger="['click']">
                  <a-button type="text" size="small">
                    <template #icon><FontSizeOutlined /></template>
                    字号选择
                  </a-button>
                  <template #overlay>
                    <a-menu @click="handleFontSizeChange">
                      <a-menu-item key="12">12px</a-menu-item>
                      <a-menu-item key="14">14px</a-menu-item>
                      <a-menu-item key="16">16px</a-menu-item>
                      <a-menu-item key="18">18px</a-menu-item>
                      <a-menu-item key="20">20px</a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
                <a-button type="text" size="small" @click="resetAllCode">
                  <template #icon><ReloadOutlined /></template>
                  重置全部代码
                </a-button>
                <a-button type="text" size="small" @click="resetCurrentCode">
                  <template #icon><UndoOutlined /></template>
                  重置本页代码
                </a-button>
                <a-button
                  v-if="hasPassedCode"
                  type="text"
                  size="small"
                  @click="restorePassedCode"
                >
                  <template #icon><RollbackOutlined /></template>
                  返回通关时代码
                </a-button>
              </div>
            </div>

            <div class="editor-shell">
              <MonacoEditor
                v-model:value="code"
                language="python"
                theme="vs"
                :options="editorOptions"
              />
            </div>

            <div v-if="result" class="result-box" :class="result.status">
              <div class="result-head">
                <strong>{{ result.status === 'pass' ? '评测通过' : '评测未通过' }}</strong>
                <span>{{ result.passed_tests }}/{{ result.total_tests }} · {{ result.score }}分</span>
              </div>
              <p v-if="result.error_message">{{ result.error_message }}</p>
            </div>
          </div>
        </a-col>
      </a-row>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Modal, message } from 'ant-design-vue';
import {
  FontSizeOutlined,
  ReloadOutlined,
  RollbackOutlined,
  UndoOutlined,
} from '@ant-design/icons-vue';
import MarkdownIt from 'markdown-it';
import MonacoEditor from '@/components/editor/MonacoEditor.vue';
import {
  evaluateTrainingCodeTask,
  getTrainingCodeTaskPassedSnapshot,
  getTrainingCodeTask,
  getTrainingCodeTasks,
  type TrainingCodeEvaluationResult,
  type TrainingCodeTask,
} from '@/api/training';

const route = useRoute();
const router = useRouter();
const md = new MarkdownIt({ html: true, linkify: true, typographer: true });

const loading = ref(false);
const submitting = ref(false);
const tasks = ref<TrainingCodeTask[]>([]);
const task = ref<TrainingCodeTask | null>(null);
const code = ref('');
const starterCode = ref('');
const result = ref<TrainingCodeEvaluationResult | null>(null);
const passedCode = ref('');
const hasPassedCode = ref(false);
const editorFontSize = ref(Number(localStorage.getItem('r5_code_editor_font_size') || 14));

const trainingId = computed(() => route.params.trainingId as string);
const taskId = computed(() => route.params.taskId as string);
const renderedHandbook = computed(() => md.render(task.value?.handbook_markdown || ''));
const draftKey = computed(() => `r5_code_${trainingId.value}_${taskId.value}`);
const editorOptions = computed(() => ({
  minimap: { enabled: false },
  fontSize: editorFontSize.value,
}));
const difficultyText = computed(() => {
  const map: Record<string, string> = {
    beginner: '初级',
    intermediate: '中级',
    advanced: '高级',
  };
  return map[task.value?.difficulty || ''] || task.value?.difficulty || '初级';
});

const loadTask = async () => {
  if (!trainingId.value || !taskId.value) return;
  loading.value = true;
  result.value = null;
  try {
    const [taskList, taskDetail] = await Promise.all([
      getTrainingCodeTasks(trainingId.value),
      getTrainingCodeTask(trainingId.value, taskId.value),
    ]);
    tasks.value = taskList.tasks || [];
    task.value = taskDetail;
    starterCode.value = taskDetail.starter_code || '# 在这里编写你的代码\n';
    code.value = localStorage.getItem(draftKey.value) || starterCode.value;
    await loadPassedSnapshot();
  } catch (error) {
    console.error('加载编程实训失败:', error);
    message.error('加载编程实训失败');
  } finally {
    loading.value = false;
  }
};

const loadPassedSnapshot = async () => {
  passedCode.value = '';
  hasPassedCode.value = false;
  try {
    const snapshot = await getTrainingCodeTaskPassedSnapshot(trainingId.value, taskId.value);
    if (snapshot.has_passed_code && snapshot.submitted_code) {
      passedCode.value = snapshot.submitted_code;
      hasPassedCode.value = true;
    }
  } catch (error) {
    console.warn('获取通关时代码失败:', error);
  }
};

const saveDraft = () => {
  if (!trainingId.value || !taskId.value) return;
  if (code.value === starterCode.value) {
    localStorage.removeItem(draftKey.value);
    return;
  }
  localStorage.setItem(draftKey.value, code.value);
};

const handleFontSizeChange = (e: any) => {
  const size = Number(e.key);
  editorFontSize.value = size;
  localStorage.setItem('r5_code_editor_font_size', String(size));
  message.success(`字号已调整为 ${size}px`);
};

const resetCurrentCode = () => {
  code.value = starterCode.value;
  localStorage.removeItem(draftKey.value);
  message.success('已重置本页代码');
};

const resetAllCode = () => {
  Modal.confirm({
    title: '确认重置全部代码',
    content: '确定要重置本实训下所有编程关卡的本地草稿吗？当前页也会恢复为初始代码。',
    okText: '确定',
    cancelText: '取消',
    onOk: () => {
      tasks.value.forEach(item => {
        localStorage.removeItem(`r5_code_${trainingId.value}_${item.id}`);
      });
      code.value = starterCode.value;
      message.success('已重置全部代码');
    },
  });
};

const restorePassedCode = () => {
  if (!passedCode.value) {
    message.info('暂无通关时代码');
    return;
  }
  code.value = passedCode.value;
  saveDraft();
  message.success('已返回通关时代码');
};

const submitCode = async () => {
  if (!task.value) return;
  submitting.value = true;
  try {
    result.value = await evaluateTrainingCodeTask(trainingId.value, taskId.value, code.value);
    if (result.value.status === 'pass') {
      passedCode.value = code.value;
      hasPassedCode.value = true;
      message.success('评测通过');
    } else {
      message.warning('评测未通过');
    }
  } catch (error) {
    console.error('提交评测失败:', error);
    message.error('提交评测失败');
  } finally {
    submitting.value = false;
  }
};

const openTask = (id: number) => {
  router.push(`/project/${trainingId.value}/code/${id}`);
};

const goBack = () => {
  router.push(`/project/${trainingId.value}`);
};

watch([trainingId, taskId], loadTask);
watch(code, saveDraft);
onMounted(loadTask);
</script>

<style scoped>
.training-code-page {
  min-height: 100vh;
  padding: 16px 24px 28px;
  background: #f5f7fb;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.title-block h1 {
  margin: 0;
  font-size: 22px;
  line-height: 1.35;
}

.meta {
  color: #667085;
  font-size: 13px;
}

.workspace {
  align-items: stretch;
}

.panel {
  height: calc(100vh - 118px);
  min-height: 560px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: auto;
}

.panel-title {
  margin-bottom: 10px;
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.task-item {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  padding: 10px 12px;
  text-align: left;
  color: #1f2937;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
}

.task-item.active {
  border-color: #1677ff;
  background: #eef5ff;
}

.task-item small {
  color: #6b7280;
}

.handbook {
  color: #1f2937;
  line-height: 1.75;
}

.editor-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.editor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.editor-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 4px;
}

.editor-shell {
  flex: 1;
  min-height: 430px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.result-box {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #fecaca;
  background: #fff1f2;
}

.result-box.pass {
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.result-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
</style>
