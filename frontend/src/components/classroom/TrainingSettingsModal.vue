<template>
  <a-modal
    v-model:open="visible"
    title="实训项目设置"
    width="600px"
    @cancel="handleCancel"
    @ok="handleSubmit"
    :confirmLoading="loading"
  >
    <a-form
      :model="settings"
      layout="vertical"
    >
      <div class="section-title">
        <span class="divider"></span>
        作业提交设置
      </div>
      
      <a-form-item label="需要提交设计文件">
        <a-switch v-model:checked="settings.requireDesignFiles" />
        <div class="form-item-help">开启后，学生需要上传设计文件（如流程图、架构图等）</div>
      </a-form-item>
      
      <a-form-item label="需要提交实验报告">
        <a-switch v-model:checked="settings.requireReport" />
        <div class="form-item-help">开启后，学生需要提交详细的实验报告</div>
      </a-form-item>
      
      <div class="section-title">
        <span class="divider"></span>
        评分设置
      </div>
      
      <a-form-item label="实训总分值">
        <a-input-number
          v-model:value="settings.totalScore"
          :min="0"
          :max="100"
          style="width: 150px"
          addon-after="分"
        />
      </a-form-item>
      
      <a-form-item label="补交扣分">
        <a-input-number
          v-model:value="settings.lateSubmissionPenalty"
          :min="0"
          :max="50"
          style="width: 150px"
          addon-after="分"
        />
        <div class="form-item-help">学生在截止时间后提交将扣除相应分数</div>
      </a-form-item>
      
      <div class="section-title">
        <span class="divider"></span>
        作业节点设置
      </div>
      
      <a-form-item label="作业节点">
        <div v-for="(node, index) in settings.assignmentNodes" :key="index" class="assignment-node">
          <a-input
            v-model:value="node.name"
            placeholder="节点名称"
            style="width: 200px; margin-right: 10px"
          />
          <a-input-number
            v-model:value="node.score"
            :min="0"
            :max="100"
            placeholder="分值"
            style="width: 100px; margin-right: 10px"
            addon-after="分"
          />
          <a-button
            type="text"
            danger
            @click="removeNode(index)"
            :disabled="settings.assignmentNodes.length <= 1"
          >
            删除
          </a-button>
        </div>
        <a-button type="dashed" block @click="addNode" style="margin-top: 10px">
          <PlusOutlined /> 添加节点
        </a-button>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { PlusOutlined } from '@ant-design/icons-vue';
import { saveTrainingSettings } from '@/api/classrooms';

interface Props {
  trainingId: string;
  classroomId: string;
}

interface AssignmentNode {
  name: string;
  score: number;
}

interface TrainingSettings {
  requireDesignFiles: boolean;
  requireReport: boolean;
  totalScore: number;
  lateSubmissionPenalty: number;
  assignmentNodes: AssignmentNode[];
}

const props = defineProps<Props>();
const emit = (['success', 'cancel']);

const visible = ref(false);
const loading = ref(false);

const settings = reactive<TrainingSettings>({
  requireDesignFiles: false,
  requireReport: false,
  totalScore: 100,
  lateSubmissionPenalty: 10,
  assignmentNodes: [
    { name: '项目设计', score: 30 },
    { name: '功能实现', score: 50 },
    { name: '测试部署', score: 20 }
  ]
});

// 添加作业节点
const addNode = () => {
  settings.assignmentNodes.push({
    name: '',
    score: 0
  });
};

// 删除作业节点
const removeNode = (index: number) => {
  settings.assignmentNodes.splice(index, 1);
};

// 提交设置
const handleSubmit = async () => {
  // 验证节点分数总和
  const totalNodeScore = settings.assignmentNodes.reduce((sum, node) => sum + node.score, 0);
  if (totalNodeScore !== settings.totalScore) {
    message.warning(`作业节点分数总和（${totalNodeScore}分）与总分值（${settings.totalScore}分）不一致`);
    return;
  }
  
  // 验证节点名称
  const emptyNode = settings.assignmentNodes.find(node => !node.name.trim());
  if (emptyNode) {
    message.warning('请填写所有节点名称');
    return;
  }
  
  loading.value = true;
  try {
    await saveTrainingSettings({
      classroom_id: parseInt(props.classroomId),
      training_id: parseInt(props.trainingId),
      settings: {
        require_design_files: settings.requireDesignFiles,
        require_experiment_report: settings.requireReport,
        total_score: settings.totalScore,
        late_submission_penalty: settings.lateSubmissionPenalty,
        assignment_nodes: settings.assignmentNodes
      }
    });
    
    message.success('实训设置保存成功');
    emit('success');
    handleCancel();
  } catch (error) {
    console.error('保存实训设置失败:', error);
    message.error('保存失败，请重试');
  } finally {
    loading.value = false;
  }
};

// 取消
const handleCancel = () => {
  visible.value = false;
  emit('cancel');
};

// 打开对话框
const open = (initialSettings?: Partial<TrainingSettings>) => {
  if (initialSettings) {
    Object.assign(settings, initialSettings);
  }
  visible.value = true;
};

// 暴露方法
defineExpose({
  open
});
</script>

<style scoped>
.section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}

.divider {
  display: inline-block;
  width: 3px;
  height: 16px;
  background-color: #1890ff;
  margin-right: 8px;
}

.form-item-help {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}

.assignment-node {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
</style>