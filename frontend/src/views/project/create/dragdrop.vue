<template>
  <div class="page-container">
    <div class="page-header">
      <a-breadcrumb class="breadcrumb">
        <a-breadcrumb-item>
          <router-link to="/project">项目实训</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>
          <router-link to="/project/create">新建实训</router-link>
        </a-breadcrumb-item>
        <a-breadcrumb-item>新建拖拽式实训</a-breadcrumb-item>
      </a-breadcrumb>
      <h1>新建拖拽式实训</h1>
      <p class="page-description">
        拖拽式实训中使用 bigdata-huigoo可视化分析平台与 bigdata-huigoo机器学习开发平台作为实训工具
      </p>
    </div>

    <a-card class="form-card">
      <a-steps
        :current="currentStep"
        size="small"
        class="steps"
      >
        <a-step title="填写基本信息" />
        <a-step title="编辑实验手册" />
        <a-step title="设置项目作业" />
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

          <a-form-item label="实训手册" class="manual-item">
            <div class="manual-preview">
              <p v-if="formState.manual">已编辑实验手册 {{ formState.manual.length }} 字符</p>
              <p v-else>尚未编辑实验手册</p>
            </div>
            <a-button type="primary" @click="goToManualEdit">编辑手册</a-button>
          </a-form-item>
        </a-form>
      </div>

      <!-- 实验手册编辑 -->
      <div v-show="currentStep === 1" class="step-content manual-edit-container">
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

      <!-- 项目作业设置 -->
      <div v-show="currentStep === 2" class="step-content">
        <a-alert
          type="info"
          show-icon
          message="项目作业设置说明"
          description="至少需设置一个作业节点，至多可设置三个作业节点。根据实训需要可设置不同设计工具，让学生组合使用拖拽式机器学习工具（AI）与可视化分析工具（BI）完成组合项目任务。"
          class="assignment-alert"
        />

        <div class="assignments-container">
          <div v-for="(assignment, index) in formState.assignments" :key="index" class="assignment-item">
            <a-card class="assignment-card" :title="`作业 ${index + 1}`">
              <template #extra>
                <a-button 
                  danger 
                  type="text" 
                  v-if="formState.assignments.length > 1"
                  @click="removeAssignment(index)"
                >
                  删除
                </a-button>
              </template>
              
              <a-form layout="vertical">
                <a-form-item label="作业名称" required>
                  <a-input 
                    v-model:value="assignment.name" 
                    placeholder="请输入作业名称" 
                  />
                </a-form-item>
                
                <a-form-item label="设计工具" required>
                  <a-select 
                    v-model:value="assignment.tool" 
                    placeholder="请选择设计工具"
                  >
                    <a-select-option value="visual">可视化分析工具（BI）</a-select-option>
                    <a-select-option value="ml">机器学习工具（AI）</a-select-option>
                    <a-select-option value="both">BI+AI 组合</a-select-option>
                  </a-select>
                </a-form-item>
                
                <a-form-item label="作业描述">
                  <a-textarea 
                    v-model:value="assignment.description" 
                    placeholder="请输入作业描述"
                    :rows="3"
                  />
                </a-form-item>
                
                <a-form-item label="作业要求">
                  <a-radio-group v-model:value="assignment.requireSubmission">
                    <a-radio :value="true">需要提交设计文件</a-radio>
                    <a-radio :value="false">不需要提交</a-radio>
                  </a-radio-group>
                </a-form-item>
              </a-form>
            </a-card>
          </div>

          <a-button 
            type="dashed" 
            block 
            @click="addAssignment" 
            :disabled="formState.assignments.length >= 3"
            class="add-assignment-btn"
          >
            <PlusOutlined /> 添加作业节点
          </a-button>
        </div>

        <a-form 
          :model="formState" 
          :label-col="{ span: 4 }" 
          :wrapper-col="{ span: 16 }"
          class="report-form"
        >
          <a-form-item label="实验报告" name="requireReport">
            <a-radio-group v-model:value="formState.requireReport">
              <a-radio :value="true">需要提交实验报告</a-radio>
              <a-radio :value="false">不需要提交实验报告</a-radio>
            </a-radio-group>
          </a-form-item>
        </a-form>
      </div>

      <!-- 预览与发布 -->
      <div v-show="currentStep === 3" class="step-content preview-container">
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
            <a-descriptions-item label="实训手册" :span="3">
              {{ formState.manual ? '已编写' : '未编写' }}
            </a-descriptions-item>
            <a-descriptions-item label="实验报告">
              {{ formState.requireReport ? '需要提交' : '不需要提交' }}
            </a-descriptions-item>
            <a-descriptions-item label="作业节点数" :span="2">
              {{ formState.assignments.length }} 个节点
            </a-descriptions-item>
          </a-descriptions>

          <div class="assignments-preview">
            <h3>作业节点预览</h3>
            <a-collapse>
              <a-collapse-panel 
                v-for="(assignment, index) in formState.assignments" 
                :key="index"
                :header="`作业 ${index + 1}: ${assignment.name}`"
              >
                <p><strong>设计工具:</strong> {{ getToolName(assignment.tool) }}</p>
                <p><strong>作业描述:</strong> {{ assignment.description || '无' }}</p>
                <p><strong>作业要求:</strong> {{ assignment.requireSubmission ? '需要提交设计文件' : '不需要提交' }}</p>
              </a-collapse-panel>
            </a-collapse>
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
          v-if="currentStep < 3" 
          type="primary" 
          @click="nextStep"
        >
          下一步
        </a-button>
        <a-button 
          v-if="currentStep === 3" 
          type="primary" 
          @click="handleSubmit"
          :loading="submitting"
        >
          保存并发布
        </a-button>
        <a-button 
          v-if="currentStep === 3" 
          @click="handleSaveDraft"
          :loading="saving"
        >
          保存为草稿
        </a-button>
      </div>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useRouter } from 'vue-router';
import { message, Form } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';

const router = useRouter();
const formRef = ref();
const currentStep = ref(0);
const submitting = ref(false);
const saving = ref(false);

interface Assignment {
  name: string;
  tool: string;
  description: string;
  requireSubmission: boolean;
}

interface FormState {
  name: string;
  description: string;
  industry: string;
  difficulty: string;
  duration: number;
  manual: string;
  assignments: Assignment[];
  requireReport: boolean;
}

const formState = reactive<FormState>({
  name: '',
  description: '',
  industry: '',
  difficulty: 'basic',
  duration: 2,
  manual: '',
  assignments: [
    {
      name: '',
      tool: '',
      description: '',
      requireSubmission: true
    }
  ],
  requireReport: true
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

// 获取工具名称
const getToolName = (value: string) => {
  const toolMap: Record<string, string> = {
    'visual': '可视化分析工具（BI）',
    'ml': '机器学习工具（AI）',
    'both': 'BI+AI 组合'
  };
  return toolMap[value] || '未选择';
};

// 添加作业
const addAssignment = () => {
  if (formState.assignments.length < 3) {
    formState.assignments.push({
      name: '',
      tool: '',
      description: '',
      requireSubmission: true
    });
  }
};

// 删除作业
const removeAssignment = (index: number) => {
  if (formState.assignments.length > 1) {
    formState.assignments.splice(index, 1);
  }
};

// 前往手册编辑
const goToManualEdit = () => {
  currentStep.value = 1;
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
    if (!formState.manual) {
      message.warning('请编辑实验手册内容');
      return;
    }
    currentStep.value += 1;
  } else if (currentStep.value === 2) {
    // 验证作业节点
    let valid = true;
    
    for (const assignment of formState.assignments) {
      if (!assignment.name || !assignment.tool) {
        valid = false;
        message.warning('请完成所有作业节点的必填项');
        break;
      }
    }
    
    // 检查是否至少有一项需要提交
    const hasSubmission = formState.assignments.some(a => a.requireSubmission) || formState.requireReport;
    
    if (!hasSubmission) {
      valid = false;
      message.warning('项目作业的作业要求和实验报告，至少有一项为"是"');
    }
    
    if (valid) {
      currentStep.value += 1;
    }
  }
};

// 提交表单
const handleSubmit = async () => {
  try {
    submitting.value = true;
    
    // 提交表单逻辑，这里模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    message.success('拖拽式实训创建成功');
    
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
.page-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.breadcrumb {
  margin-bottom: 16px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 12px;
}

.page-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.form-card {
  margin-bottom: 24px;
}

.steps {
  margin-bottom: 24px;
}

.step-content {
  margin-bottom: 24px;
  min-height: 400px;
}

.manual-edit-container {
  min-height: 500px;
}

.manual-alert, .assignment-alert, .preview-alert {
  margin-bottom: 16px;
}

.rich-editor {
  margin-top: 16px;
}

.editor-tip {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
  margin-top: 8px;
}

.manual-item {
  display: flex;
  align-items: center;
}

.manual-preview {
  flex: 1;
  margin-right: 16px;
}

.assignments-container {
  margin-top: 16px;
}

.assignment-item {
  margin-bottom: 16px;
}

.assignment-card {
  margin-bottom: 16px;
}

.add-assignment-btn {
  margin-bottom: 24px;
}

.report-form {
  margin-top: 16px;
}

.preview-content {
  margin-top: 16px;
}

.preview-content h2 {
  margin-bottom: 16px;
}

.assignments-preview {
  margin-top: 24px;
}

.assignments-preview h3 {
  margin-bottom: 16px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style> 