<template>
  <PageShell max-width="wide" class="create-coding-page">
    <PageHeaderBar
      title="新建编码式实训"
      subtitle="编码式实训以 Jupyter notebook 为工具，支持创建在线编码实训课程"
      show-back
      back-to="/project/create"
    />

    <a-card class="form-card">
      <a-steps
        :current="currentStep"
        size="small"
        class="steps"
      >
        <a-step title="填写基本信息" />
        <a-step title="配置环境" />
        <a-step title="编辑实验手册" />
        <a-step title="编辑任务与数据集" />
        <a-step title="预览与发布" />
      </a-steps>

      <!-- 基本信息表单 -->
      <div v-show="currentStep === 0" class="step-content">
        <a-form
          :model="formState"
          :rules="rules"
          ref="formRef"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 16 }"
        >
          <a-form-item label="实训名称" name="name">
            <a-input 
              v-model:value="formState.name" 
              placeholder="请输入实训名称"
              :maxLength="50"
              show-count
            />
          </a-form-item>

          <a-form-item label="实训简介" name="description">
            <a-textarea
              v-model:value="formState.description"
              placeholder="请输入实训简介"
              :rows="4"
              :maxLength="500"
              show-count
            />
          </a-form-item>

          <a-form-item label="所属行业" name="industry">
            <a-select
              v-model:value="formState.industry"
              placeholder="请选择所属行业"
            >
              <a-select-option value="it">IT/互联网</a-select-option>
              <a-select-option value="finance">金融/财务</a-select-option>
              <a-select-option value="education">教育/培训</a-select-option>
              <a-select-option value="medical">医疗/健康</a-select-option>
              <a-select-option value="manufacture">制造/生产</a-select-option>
              <a-select-option value="retail">零售/消费</a-select-option>
              <a-select-option value="agriculture">农业/环保</a-select-option>
              <a-select-option value="transportation">交通/物流</a-select-option>
              <a-select-option value="energy">能源/化工</a-select-option>
              <a-select-option value="others">其他</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="难易度" name="difficulty">
            <a-radio-group v-model:value="formState.difficulty">
              <a-radio value="basic">初级</a-radio>
              <a-radio value="intermediate">中级</a-radio>
              <a-radio value="advanced">高级</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="实验课时" name="duration">
            <a-input-number
              v-model:value="formState.duration"
              :min="1"
              :max="100"
              placeholder="请输入数字"
              addon-after="课时"
            />
          </a-form-item>
        </a-form>
      </div>

      <!-- 配置环境 -->
      <div v-show="currentStep === 1" class="step-content">
        <a-alert
          type="info"
          show-icon
          message="环境配置说明"
          description="请根据实训需求配置适当的计算资源。更高的配置可以提升运行效率，但也会消耗更多的系统资源。"
          class="env-alert"
        />

        <a-form
          :model="formState.environment"
          layout="vertical"
          class="env-form"
        >
          <a-form-item label="运行环境" name="type" required>
            <a-select
              v-model:value="formState.environment.type"
              placeholder="请选择实训环境"
            >
              <a-select-option value="python3">Python 3 标准环境</a-select-option>
              <a-select-option value="tensorflow">TensorFlow 2.x</a-select-option>
              <a-select-option value="pytorch">PyTorch 1.x</a-select-option>
              <a-select-option value="r">R 语言环境</a-select-option>
              <a-select-option value="data-science">数据科学环境(含Pandas、Numpy等)</a-select-option>
            </a-select>
          </a-form-item>

          <div class="resource-config">
            <h3>资源配置</h3>
            
            <a-row :gutter="24">
              <a-col :span="8">
                <a-form-item label="存储空间" required>
                  <a-select v-model:value="formState.environment.storage">
                    <a-select-option value="5">5GB</a-select-option>
                    <a-select-option value="10">10GB</a-select-option>
                    <a-select-option value="20">20GB</a-select-option>
                    <a-select-option value="50">50GB</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="内存" required>
                  <a-select v-model:value="formState.environment.memory">
                    <a-select-option value="2">2GB</a-select-option>
                    <a-select-option value="4">4GB</a-select-option>
                    <a-select-option value="8">8GB</a-select-option>
                    <a-select-option value="16">16GB</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="CPU" required>
                  <a-select v-model:value="formState.environment.cpu">
                    <a-select-option value="1">1 核</a-select-option>
                    <a-select-option value="2">2 核</a-select-option>
                    <a-select-option value="4">4 核</a-select-option>
                    <a-select-option value="8">8 核</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
          </div>

          <a-form-item label="GPU支持" required>
            <a-radio-group v-model:value="formState.environment.gpu">
              <a-radio :value="false">不需要</a-radio>
              <a-radio :value="true">需要</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="预安装包" name="packages">
            <a-textarea
              v-model:value="formState.environment.packages"
              placeholder="每行一个包名，例如：numpy==1.20.0"
              :rows="4"
            />
            <div class="helper-text">注：学生可以在实训中自行安装其他包，此处仅指定默认预装的包</div>
          </a-form-item>
        </a-form>
      </div>

      <!-- 实验手册编辑 -->
      <div v-show="currentStep === 2" class="step-content manual-edit-container">
        <a-alert
          type="info"
          show-icon
          message="实验手册编辑指南"
          description="请在实验手册中详细描述实训过程，为学生实训提供指引。您可以添加图片、列表、代码块等富文本内容。"
          class="manual-alert"
        />
        
        <div class="rich-editor">
          <a-textarea
            v-model:value="formState.manual"
            placeholder="请输入实验手册内容..."
            :rows="15"
            :maxLength="10000"
            show-count
          />
          <p class="editor-tip">注: 此处简化为文本区域，实际应当使用富文本编辑器</p>
        </div>
      </div>

      <!-- 编辑任务与数据集 -->
      <div v-show="currentStep === 3" class="step-content">
        <a-alert
          type="info"
          show-icon
          message="Jupyter任务说明"
          description="在实际编辑界面中，您将使用嵌入式Jupyter编辑器创建代码文件，学生进行实训时将直接看到这些代码文件。您也可以上传数据集供学生使用。"
          class="jupyter-alert"
        />

        <div class="jupyter-container">
          <div class="datasets-section">
            <h3>数据集管理</h3>
            <p>您可以上传数据文件以供实训使用</p>
            
            <a-table
              :columns="datasetColumns"
              :data-source="formState.datasets"
              :pagination="false"
              size="small"
              class="datasets-table"
            >
              <template #bodyCell="{ column, record, index }">
                <template v-if="column.key === 'action'">
                  <a-button type="link" size="small" disabled>复制地址</a-button>
                  <a-button 
                    type="link" 
                    danger 
                    size="small" 
                    @click="removeDataset(index)"
                  >
                    删除
                  </a-button>
                </template>
              </template>
            </a-table>
            
            <div class="upload-placeholder">
              <a-alert
                type="info"
                show-icon
                message="数据集管理即将开启"
                description="当前版本仅支持在保存后到“实训详情 > 数据集管理”页面上传真实数据集。"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 预览与发布 -->
      <div v-show="currentStep === 4" class="step-content preview-container">
        <a-alert
          type="warning"
          show-icon
          message="发布前确认"
          description="请确认所有信息填写正确。发布后的实训项目将显示在项目实训资源库中，所有教师用户均可查看并使用。"
          class="preview-alert"
        />

        <div class="preview-content">
          <h2>{{ formState.name || '未命名实训' }}</h2>
          
          <a-descriptions bordered>
            <a-descriptions-item label="实训简介" :span="3">
              {{ formState.description || '无' }}
            </a-descriptions-item>
            <a-descriptions-item label="所属行业">
              {{ getIndustryName(formState.industry) }}
            </a-descriptions-item>
            <a-descriptions-item label="难易度">
              {{ getDifficultyName(formState.difficulty) }}
            </a-descriptions-item>
            <a-descriptions-item label="实验课时">
              {{ formState.duration }} 课时
            </a-descriptions-item>
            <a-descriptions-item label="运行环境" :span="3">
              {{ getEnvironmentName(formState.environment.type) }}
            </a-descriptions-item>
            <a-descriptions-item label="存储空间">
              {{ formState.environment.storage }}GB
            </a-descriptions-item>
            <a-descriptions-item label="内存">
              {{ formState.environment.memory }}GB
            </a-descriptions-item>
            <a-descriptions-item label="CPU">
              {{ formState.environment.cpu }} 核
            </a-descriptions-item>
            <a-descriptions-item label="GPU支持">
              {{ formState.environment.gpu ? '是' : '否' }}
            </a-descriptions-item>
            <a-descriptions-item label="实训手册" :span="2">
              {{ formState.manual ? '已编写' : '未编写' }}
            </a-descriptions-item>
            <a-descriptions-item label="数据集数量">
              {{ formState.datasets.length }} 个
            </a-descriptions-item>
          </a-descriptions>

          <div v-if="formState.datasets.length > 0" class="datasets-preview">
            <h3>数据集预览</h3>
            <a-list 
              size="small" 
              bordered 
              :data-source="formState.datasets"
            >
              <template #renderItem="{ item }">
                <a-list-item>
                  <a-list-item-meta :title="item.name">
                    <template #description>
                      大小：{{ formatFileSize(item.size) }}
                    </template>
                  </a-list-item-meta>
                </a-list-item>
              </template>
            </a-list>
          </div>
        </div>
      </div>

      <!-- 表单操作按钮 -->
      <div class="form-actions">
        <a-button 
          v-if="currentStep > 0" 
          @click="prevStep"
        >
          上一步
        </a-button>
        <a-button 
          v-if="currentStep < 4" 
          type="primary" 
          @click="nextStep"
        >
          下一步
        </a-button>
        <a-button 
          v-if="currentStep === 4" 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          保存并发布
        </a-button>
        <a-button 
          v-if="currentStep === 4" 
          @click="handleSaveDraft"
          :loading="saving"
        >
          保存为草稿
        </a-button>
      </div>
    </a-card>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message, Form } from 'ant-design-vue';
import { PlusOutlined, InboxOutlined } from '@ant-design/icons-vue';
import PageShell from '@/components/common/PageShell.vue';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';

const router = useRouter();
const formRef = ref();
const currentStep = ref(0);
const submitting = ref(false);
const saving = ref(false);

// 数据集列定义
const datasetColumns = [
  {
    title: '文件名',
    dataIndex: 'name',
    key: 'name',
  },
  {
    title: '大小',
    dataIndex: 'size',
    key: 'size',
    customRender: ({ text }: { text: number }) => formatFileSize(text),
  },
  {
    title: '上传时间',
    dataIndex: 'uploadTime',
    key: 'uploadTime',
  },
  {
    title: '操作',
    key: 'action',
  },
];

interface Dataset {
  key: string;
  name: string;
  size: number;
  uploadTime: string;
  path: string;
}

interface Environment {
  type: string;
  storage: string;
  memory: string;
  cpu: string;
  gpu: boolean;
  packages: string;
}

interface FormState {
  name: string;
  description: string;
  industry: string;
  difficulty: string;
  duration: number;
  manual: string;
  environment: Environment;
  datasets: Dataset[];
}

const formState = reactive<FormState>({
  name: '',
  description: '',
  industry: '',
  difficulty: 'basic',
  duration: 2,
  manual: '',
  environment: {
    type: '',
    storage: '10',
    memory: '4',
    cpu: '2',
    gpu: false,
    packages: ''
  },
  datasets: [
    {
      key: '1',
      name: '示例数据集.csv',
      size: 1024 * 1024 * 2.5, // 2.5MB
      uploadTime: '2023-04-14 10:30:45',
      path: '/datasets/example.csv'
    }
  ]
});

const rules = {
  name: [
    { required: true, message: '请输入实训名称', trigger: 'blur' },
    { min: 2, max: 50, message: '实训名称长度需在2-50个字符之间', trigger: 'blur' }
  ],
  description: [
    { required: true, message: '请输入实训简介', trigger: 'blur' },
    { max: 500, message: '实训简介不能超过500个字符', trigger: 'blur' }
  ],
  industry: [
    { required: true, message: '请选择所属行业', trigger: 'change' }
  ],
  difficulty: [
    { required: true, message: '请选择难易度', trigger: 'change' }
  ],
  duration: [
    { required: true, message: '请输入实验课时', trigger: 'blur' },
    { type: 'number', min: 1, max: 100, message: '实验课时需在1-100之间', trigger: 'blur' }
  ]
};

// 获取行业名称
const getIndustryName = (value: string) => {
  const industryMap: Record<string, string> = {
    'it': 'IT/互联网',
    'finance': '金融/财务',
    'education': '教育/培训',
    'medical': '医疗/健康',
    'manufacture': '制造/生产',
    'retail': '零售/消费',
    'agriculture': '农业/环保',
    'transportation': '交通/物流',
    'energy': '能源/化工',
    'others': '其他'
  };
  return industryMap[value] || '未选择';
};

// 获取难度名称
const getDifficultyName = (value: string) => {
  const difficultyMap: Record<string, string> = {
    'basic': '初级',
    'intermediate': '中级',
    'advanced': '高级'
  };
  return difficultyMap[value] || '未选择';
};

// 获取环境名称
const getEnvironmentName = (value: string) => {
  const envMap: Record<string, string> = {
    'python3': 'Python 3 标准环境',
    'tensorflow': 'TensorFlow 2.x',
    'pytorch': 'PyTorch 1.x',
    'r': 'R 语言环境',
    'data-science': '数据科学环境(含Pandas、Numpy等)'
  };
  return envMap[value] || '未选择';
};

// 格式化文件大小
const formatFileSize = (size: number) => {
  if (size < 1024) {
    return size + ' B';
  } else if (size < 1024 * 1024) {
    return (size / 1024).toFixed(2) + ' KB';
  } else if (size < 1024 * 1024 * 1024) {
    return (size / (1024 * 1024)).toFixed(2) + ' MB';
  } else {
    return (size / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }
};

// 处理数据集上传
const handleDatasetUpload = (info: any) => {
  // 模拟上传，实际环境中应该调用上传API
  const { file } = info;
  
  message.info(`模拟上传文件: ${file.name}`);
  
  const dataset: Dataset = {
    key: Date.now().toString(),
    name: file.name,
    size: file.size || Math.random() * 1024 * 1024 * 10, // 模拟文件大小
    uploadTime: new Date().toLocaleString(),
    path: `/datasets/${file.name}`
  };
  
  formState.datasets.push(dataset);
};

// 删除数据集
const removeDataset = (index: number) => {
  formState.datasets.splice(index, 1);
};

// 上一步
const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value -= 1;
  }
};

// 下一步
const nextStep = async () => {
  if (currentStep.value === 0) {
    try {
      await formRef.value.validate();
      currentStep.value += 1;
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  } else if (currentStep.value === 1) {
    if (!formState.environment.type) {
      message.warning('请选择运行环境');
      return;
    }
    currentStep.value += 1;
  } else if (currentStep.value === 2) {
    if (!formState.manual) {
      message.warning('请编辑实验手册内容');
      return;
    }
    currentStep.value += 1;
  } else if (currentStep.value === 3) {
    // 实际应用中可能需要检查Jupyter编辑器内容是否已保存
    currentStep.value += 1;
  }
};

// 提交表单
const handleSubmit = async () => {
  try {
    submitting.value = true;
    
    // 提交表单逻辑，这里模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    message.success('编码式实训创建成功');
    
    // 跳转到实训详情页
    router.push('/project/myprojects');
  } catch (error) {
    console.error('提交失败:', error);
    message.error('创建失败，请重试');
  } finally {
    submitting.value = false;
  }
};

// 保存为草稿
const handleSaveDraft = async () => {
  try {
    saving.value = true;
    
    // 保存草稿逻辑，这里模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    message.success('已保存为草稿');
    
    // 跳转到我的实训页面
    router.push('/project/myprojects');
  } catch (error) {
    console.error('保存草稿失败:', error);
    message.error('保存草稿失败，请重试');
  } finally {
    saving.value = false;
  }
};
</script>

<style scoped>
.create-coding-page {
  min-height: 100%;
}

.form-card {
  margin-bottom: var(--hx-space-5);
}

.steps {
  margin-bottom: 24px;
}

.step-content {
  margin-bottom: 24px;
  min-height: 400px;
}

.env-alert, .manual-alert, .jupyter-alert, .preview-alert {
  margin-bottom: 16px;
}

.env-form {
  margin-top: 16px;
}

.resource-config {
  margin: 16px 0;
  border: 1px solid #f0f0f0;
  padding: 16px;
  border-radius: 4px;
  background-color: #fafafa;
}

.resource-config h3 {
  margin-bottom: 16px;
}

.helper-text {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 4px;
}

.manual-edit-container {
  min-height: 500px;
}

.rich-editor {
  margin-top: 16px;
}

.editor-tip {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 8px;
}

.jupyter-container {
  margin-top: 16px;
}

.datasets-section {
  margin-top: 24px;
}

.datasets-section h3 {
  margin-bottom: 12px;
}

.datasets-table {
  margin-bottom: 16px;
}

.upload-container {
  margin-top: 16px;
}

.upload-area {
  margin-bottom: 8px;
}

.upload-placeholder {
  margin-top: 12px;
}

.preview-content {
  margin-top: 16px;
}

.preview-content h2 {
  margin-bottom: 16px;
}

.datasets-preview {
  margin-top: 24px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style> 