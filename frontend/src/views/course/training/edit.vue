<template>
  <div class="training-edit-page">
    <a-page-header
      title="编辑实训课程"
      sub-title="配置实训内容和设置"
      @back="handleBack"
    >
      <template #extra>
        <a-space>
          <a-button @click="handlePreview">预览</a-button>
          <a-button type="primary" @click="handleSave">保存</a-button>
          <a-button type="primary" @click="handlePublish">发布</a-button>
        </a-space>
      </template>
    </a-page-header>

    <div class="edit-content">
      <a-card>
        <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="basic" tab="基本信息">
            <a-form
              :model="formState"
              :label-col="{ span: 4 }"
              :wrapper-col="{ span: 16 }"
            >
              <a-form-item label="实训名称">
                <a-input v-model:value="formState.name" placeholder="请输入实训名称" />
              </a-form-item>
              
              <a-form-item label="实训类型">
                <a-tag :color="getTypeColor(formState.type)">{{ getTypeText(formState.type) }}</a-tag>
                <span class="form-hint">实训类型创建后不可修改</span>
              </a-form-item>
              
              <a-form-item label="实训介绍">
                <a-textarea
                  v-model:value="formState.intro"
                  placeholder="请输入实训介绍"
                  :rows="4"
                />
              </a-form-item>
              
              <a-form-item label="难易度">
                <a-radio-group v-model:value="formState.difficulty">
                  <a-radio value="beginner">初级</a-radio>
                  <a-radio value="intermediate">中级</a-radio>
                  <a-radio value="advanced">高级</a-radio>
                </a-radio-group>
              </a-form-item>
              
              <a-form-item label="预计时长">
                <a-input-number
                  v-model:value="formState.duration"
                  :min="10"
                  :max="300"
                  addon-after="分钟"
                />
              </a-form-item>
            </a-form>
          </a-tab-pane>
          
          <a-tab-pane key="content" tab="实训内容" :disabled="!trainingId">
            <div v-if="formState.type === 'bi'" class="content-section">
              <h3>BI可视化分析配置</h3>
              <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
                <a-form-item label="数据源">
                  <a-select v-model:value="biConfig.dataSource" placeholder="选择数据源">
                    <a-select-option value="csv">CSV文件</a-select-option>
                    <a-select-option value="database">数据库</a-select-option>
                    <a-select-option value="api">API接口</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="目标任务">
                  <a-textarea
                    v-model:value="biConfig.taskDescription"
                    placeholder="描述学生需要完成的可视化任务"
                    :rows="4"
                  />
                </a-form-item>
                
                <a-form-item label="参考模板">
                  <a-upload
                    :file-list="biConfig.templateFiles"
                    :action="uploadUrl"
                  >
                    <a-button>
                      <UploadOutlined />
                      上传模板文件
                    </a-button>
                  </a-upload>
                </a-form-item>
              </a-form>
            </div>
            
            <div v-else-if="formState.type === 'ai'" class="content-section">
              <h3>AI机器学习配置</h3>
              <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
                <a-form-item label="模型类型">
                  <a-checkbox-group v-model:value="aiConfig.modelTypes">
                    <a-checkbox value="classification">分类</a-checkbox>
                    <a-checkbox value="regression">回归</a-checkbox>
                    <a-checkbox value="clustering">聚类</a-checkbox>
                    <a-checkbox value="neural">神经网络</a-checkbox>
                  </a-checkbox-group>
                </a-form-item>
                
                <a-form-item label="数据集">
                  <a-select v-model:value="aiConfig.dataset" placeholder="选择数据集">
                    <a-select-option value="iris">鸢尾花数据集</a-select-option>
                    <a-select-option value="boston">波士顿房价数据集</a-select-option>
                    <a-select-option value="mnist">MNIST手写数字</a-select-option>
                    <a-select-option value="custom">自定义数据集</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="评估指标">
                  <a-checkbox-group v-model:value="aiConfig.metrics">
                    <a-checkbox value="accuracy">准确率</a-checkbox>
                    <a-checkbox value="precision">精确率</a-checkbox>
                    <a-checkbox value="recall">召回率</a-checkbox>
                    <a-checkbox value="f1">F1分数</a-checkbox>
                  </a-checkbox-group>
                </a-form-item>
              </a-form>
            </div>
            
            <div v-else-if="formState.type === 'jupyter'" class="content-section">
              <h3>Jupyter编码式配置</h3>
              
              <!-- Jupyter编辑器 -->
              <div class="jupyter-editor-container">
                <JupyterEditor
                  :training-id="trainingId"
                  @save="handleJupyterSave"
                />
              </div>
              
              <!-- 数据集管理 -->
              <div class="dataset-section">
                <h4>数据集管理</h4>
                <a-upload
                  :file-list="jupyterConfig.dataFiles"
                  :action="uploadUrl"
                  multiple
                  @change="handleDataFileChange"
                >
                  <a-button>
                    <UploadOutlined />
                    上传数据文件
                  </a-button>
                </a-upload>
                <div class="dataset-hint">
                  上传的数据文件将保存在 /data 目录下，可以在代码中直接访问
                </div>
              </div>
            </div>
          </a-tab-pane>
          
          <a-tab-pane key="guide" tab="实训手册">
            <div class="handbook-editor">
              <RichTextEditor
                v-model:value="guideContent"
                placeholder="请在实验手册中详细描述实训过程，为学生实训提供指引..."
                :height="500"
              />
              <div class="editor-tips">
                <a-alert
                  message="编辑提示"
                  type="info"
                  show-icon
                >
                  <template #description>
                    <ul>
                      <li>支持富文本编辑，可以插入图片、表格、代码块等内容</li>
                      <li>支持Markdown语法，可以在编辑和预览模式间切换</li>
                      <li>建议包含：实训目标、实训步骤、注意事项、参考资料等内容</li>
                      <li>内容会自动保存，无需担心丢失</li>
                    </ul>
                  </template>
                </a-alert>
              </div>
            </div>
          </a-tab-pane>
          
          <a-tab-pane key="settings" tab="高级设置">
            <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 16 }">
              <a-form-item label="允许重置环境">
                <a-switch v-model:checked="settings.allowReset" />
                <span class="form-hint">允许学生重置实训环境到初始状态</span>
              </a-form-item>
              
              <a-form-item label="自动保存">
                <a-switch v-model:checked="settings.autoSave" />
                <span class="form-hint">自动保存学生的操作进度</span>
              </a-form-item>
              
              <a-form-item label="时间限制">
                <a-input-number
                  v-model:value="settings.timeLimit"
                  :min="0"
                  :max="480"
                  addon-after="分钟"
                />
                <span class="form-hint">0表示不限制</span>
              </a-form-item>
              
              <a-form-item label="资源限制">
                <a-space direction="vertical" style="width: 100%">
                  <a-input-group compact>
                    <a-input style="width: 50%" v-model:value="settings.cpuLimit" addon-before="CPU" addon-after="核" />
                    <a-input style="width: 50%" v-model:value="settings.memoryLimit" addon-before="内存" addon-after="GB" />
                  </a-input-group>
                </a-space>
              </a-form-item>
            </a-form>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { message } from 'ant-design-vue';
import { UploadOutlined } from '@ant-design/icons-vue';
import { publishTraining, type TrainingPublishRequest } from '@/api/training';
import { put, get } from '@/utils/request';
import RichTextEditor from '@/components/common/RichTextEditor.vue';
import JupyterEditor from '@/components/training/JupyterEditor.vue';

const router = useRouter();
const route = useRoute();
const trainingId = computed(() => route.params.id as string);

const activeTab = ref('basic');

// 表单数据
const formState = reactive({
  name: '',
  type: 'bi' as 'bi' | 'ai' | 'jupyter',
  intro: '',
  difficulty: 'beginner',
  duration: 60,
  categories: [] as string[],
  skills: [] as string[]
});

// BI配置
const biConfig = reactive({
  dataSource: '',
  taskDescription: '',
  templateFiles: []
});

// AI配置
const aiConfig = reactive({
  modelTypes: [] as string[],
  dataset: '',
  metrics: [] as string[]
});

// Jupyter配置
const jupyterConfig = reactive({
  initialCode: '',
  dependencies: [] as string[],
  dataFiles: [],
  cells: [] as any[]
});

// 实训手册内容
const guideContent = ref('');

// 高级设置
const settings = reactive({
  allowReset: true,
  autoSave: true,
  timeLimit: 0,
  cpuLimit: '1',
  memoryLimit: '2'
});

// 上传地址
const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/v1/upload/file`;
});

// 获取类型文本
const getTypeText = (type: string) => {
  const map: Record<string, string> = {
    'bi': 'BI可视化分析',
    'ai': 'AI机器学习',
    'jupyter': 'Jupyter编码式'
  };
  return map[type] || '未知类型';
};

// 获取类型颜色
const getTypeColor = (type: string) => {
  const map: Record<string, string> = {
    'bi': 'blue',
    'ai': 'purple',
    'jupyter': 'orange'
  };
  return map[type] || 'default';
};

// 返回
const handleBack = () => {
  router.push('/course/training/my');
};

// 预览
const handlePreview = () => {
  message.info('预览功能开发中...');
};

// 保存
const handleSave = async () => {
  try {
    const updateData = {
      title: formState.name,
      description: formState.intro,
      difficulty: formState.difficulty,
      estimated_hours: Math.ceil(formState.duration / 60) // 分钟转小时
    };

    console.log('保存实训数据:', updateData);

    // 调用API更新实训
    const response = await put(`/api/v1/trainings/detail/${trainingId.value}`, updateData);
    console.log('保存响应:', response);

    if (response) {
      message.success('保存成功');
    } else {
      message.error('保存失败');
    }
  } catch (error) {
    console.error('保存失败:', error);
    message.error('保存失败，请稍后重试');
  }
};

// 发布
const handlePublish = async () => {
  try {
    // 弹出发布确认对话框
    const publishData: TrainingPublishRequest = {
      visibility: 'private' // 默认个人发布
    };
    
    const success = await publishTraining(Number(trainingId.value), publishData);
    if (success) {
      message.success('发布成功');
      router.push('/course/training/my');
    } else {
      message.error('发布失败');
    }
  } catch (error) {
    console.error('发布失败:', error);
    message.error('发布失败，请稍后重试');
  }
};

// 插入Markdown语法
const insertMarkdown = (prefix: string, suffix = '') => {
  // 这里简化处理，实际应该在光标位置插入
  guideContent.value += prefix + suffix;
};

// 加载实训数据
const loadTrainingData = async () => {
  try {
    const response = await get(`/api/v1/trainings/detail/${trainingId.value}`);
    if (response?.code === '0000' && response.data) {
      const data = response.data;
      formState.name = data.title || data.name || '';
      formState.type = data.training_type === 'DATA_ANALYSIS' ? 'bi' : data.training_type === 'JUPYTER' ? 'jupyter' : 'bi';
      formState.intro = data.description || data.intro || '';
      formState.difficulty = data.difficulty || 'beginner';
      formState.duration = data.duration_minutes || data.duration || 60;
    }
  } catch (error) {
    console.error('加载实训数据失败:', error);
    message.error('加载实训数据失败');
  }
};

// 处理Jupyter保存
const handleJupyterSave = (cells: any[]) => {
  // 保存Jupyter单元格数据
  jupyterConfig.cells = cells;
  console.log('Jupyter单元格保存:', cells);
};

// 处理数据文件变化
const handleDataFileChange = (event: any) => {
  // 处理数据文件变化逻辑
  console.log('数据文件变化:', event);
};

onMounted(() => {
  if (trainingId.value) {
    loadTrainingData();
  }
});
</script>

<style scoped>
.training-edit-page {
  background-color: #f0f2f5;
  min-height: 100vh;
}

.edit-content {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.content-section {
  padding: 20px 0;
}

.content-section h3 {
  margin-bottom: 20px;
}

.form-hint {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.handbook-editor {
  position: relative;
}

.editor-tips {
  margin-top: 10px;
  padding: 10px;
  background: #fafafa;
  border-radius: 4px;
}

:deep(.ant-page-header) {
  background: #fff;
  padding: 16px 24px;
}

.jupyter-editor-container {
  margin-bottom: 20px;
}

.dataset-section {
  margin-top: 20px;
}

.dataset-section h4 {
  margin-bottom: 10px;
}

.dataset-hint {
  margin-top: 10px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}
</style>