<template>
  <div class="training-create-page">
    <a-card class="training-card" title="新建实训课程">
      <a-form 
        ref="formRef"
        :model="formState"
        :rules="rules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 18 }"
      >
        <!-- 实训名称 -->
        <a-form-item label="实训名称" name="name">
          <a-input 
            v-model:value="formState.name" 
            placeholder="请输入实训名称" 
            :maxlength="60"
            show-count
          />
        </a-form-item>

        <!-- 实训类型 -->
        <a-form-item label="实训类型" name="type">
          <a-radio-group v-model:value="formState.type" @change="handleTypeChange">
            <a-radio value="bi">BI可视化分析实训</a-radio>
            <a-radio value="ai">AI机器学习实训</a-radio>
            <a-radio value="jupyter">Jupyter编码式实训</a-radio>
          </a-radio-group>
          <div class="type-description">
            <p v-if="formState.type === 'bi'">
              <InfoCircleOutlined /> BI可视化分析实训：学生将使用拖拽式界面创建数据可视化图表和仪表板
            </p>
            <p v-if="formState.type === 'ai'">
              <InfoCircleOutlined /> AI机器学习实训：学生将通过流程化界面构建和训练机器学习模型
            </p>
            <p v-if="formState.type === 'jupyter'">
              <InfoCircleOutlined /> Jupyter编码式实训：学生将在Jupyter环境中编写代码完成数据分析任务
            </p>
          </div>
        </a-form-item>

        <!-- 实训介绍 -->
        <a-form-item label="实训介绍" name="intro">
          <a-textarea 
            v-model:value="formState.intro"
            placeholder="请输入实训介绍，说明实训的目标和主要内容" 
            :auto-size="{ minRows: 4, maxRows: 10 }"
            :maxlength="500"
            show-count
          />
        </a-form-item>

        <!-- 难易度 -->
        <a-form-item label="难易度" name="difficulty">
          <a-radio-group v-model:value="formState.difficulty">
            <a-radio value="beginner">初级</a-radio>
            <a-radio value="intermediate">中级</a-radio>
            <a-radio value="advanced">高级</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 方向分类 -->
        <a-form-item label="方向分类（可选）" name="categories">
          <a-select
            v-model:value="formState.categories"
            placeholder="请选择方向分类（最多选择3个）"
            mode="multiple"
            :options="categoryOptions"
            :max-tag-count="3"
            :max="3"
            @change="handleCategoryChange"
            style="width: 100%"
          >
            <template #tagRender="{ value, closable, onClose }">
              <a-tag :closable="closable" @close="onClose">
                {{ getCategoryLabel(value) }}
              </a-tag>
            </template>
          </a-select>
          <div v-if="formState.categories.length >= 3" class="form-item-hint" style="color: #ff4d4f">
            已达到最多选择3个分类的限制
          </div>
        </a-form-item>

        <!-- 实训环境（根据类型显示不同的环境选项） -->
        <a-form-item v-if="showEnvironmentSelect" label="实训环境" name="environment">
          <a-select
            v-model:value="formState.environment"
            placeholder="请选择实训环境"
            style="width: 100%"
            @change="handleEnvironmentChange"
          >
            <a-select-option v-for="env in filteredEnvironments" :key="env.id" :value="env.id">
              {{ env.name }} {{ env.description ? `(${env.description})` : '' }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 预计时长 -->
        <a-form-item label="预计时长" name="duration">
          <a-input-number
            v-model:value="formState.duration"
            placeholder="请输入预计完成时长"
            :min="10"
            :max="300"
            addon-after="分钟"
            style="width: 200px"
          />
          <span class="form-item-hint">建议设置为30-120分钟</span>
        </a-form-item>

        <!-- 封面图片 -->
        <a-form-item label="封面图片" name="coverImage">
          <a-upload
            v-model:file-list="fileList"
            name="file"
            list-type="picture-card"
            class="cover-uploader"
            :show-upload-list="false"
            :action="uploadUrl"
            :before-upload="beforeUpload"
            @change="handleCoverChange"
          >
            <img v-if="formState.coverImage" :src="formState.coverImage" alt="封面" style="width: 100%" />
            <div v-else>
              <PlusOutlined />
              <div style="margin-top: 8px">上传封面</div>
            </div>
          </a-upload>
          <div class="form-item-hint">建议尺寸：16:9，支持 JPG、PNG 格式，大小不超过 2MB</div>
        </a-form-item>

        <!-- 技能标签 -->
        <a-form-item label="技能标签" name="skills">
          <a-select
            v-model:value="formState.skills"
            mode="tags"
            placeholder="请输入或选择技能标签"
            :options="skillOptions"
            style="width: 100%"
          />
          <div class="form-item-hint">输入技能名称后按回车添加，例如：数据分析、机器学习、Python等</div>
        </a-form-item>

        <!-- 表单操作按钮 -->
        <a-form-item :wrapper-col="{ offset: 4, span: 18 }">
          <a-space>
            <a-button type="primary" :loading="creating" @click="handleSubmit">创建实训</a-button>
            <a-button @click="handleCancel">取消</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import type { FormInstance, UploadChangeParam } from 'ant-design-vue';
import { InfoCircleOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { 
  createTraining, 
  fetchTrainingEnvironments,
  type NewTraining,
  type TrainingEnvironment,
  type DirectionCategory
} from '@/api/training';
import { fetchDirectionCategories } from '@/api/practice';
import { useUserStore } from '@/stores/user';

const router = useRouter();
const userStore = useUserStore();

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再创建实训课程');
    router.push('/login');
    throw new Error('Missing current user id');
  }
  return userId;
};
const formRef = ref<FormInstance>();
const creating = ref(false);
const fileList = ref([]);

// 表单数据
const formState = reactive({
  name: '',
  type: 'bi' as 'bi' | 'ai' | 'jupyter',
  intro: '',
  difficulty: 'beginner' as 'beginner' | 'intermediate' | 'advanced',
  categories: [] as string[],
  environment: undefined as string | undefined,
  duration: 60,
  coverImage: '',
  skills: [] as string[]
});

// 环境列表
const environments = ref<TrainingEnvironment[]>([]);
const directionCategories = ref<DirectionCategory[]>([]);

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入实训名称', trigger: 'blur' },
    { min: 2, max: 60, message: '实训名称长度应在 2-60 个字符之间', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择实训类型', trigger: 'change' }
  ],
  intro: [
    { required: true, message: '请输入实训介绍', trigger: 'blur' },
    { min: 10, max: 500, message: '实训介绍长度应在 10-500 个字符之间', trigger: 'blur' }
  ],
  difficulty: [
    { required: true, message: '请选择难易度', trigger: 'change' }
  ],
  categories: [
    { required: false, message: '请选择方向分类', trigger: 'change', type: 'array' }
  ],
  duration: [
    { required: true, message: '请输入预计时长', trigger: 'blur' }
  ]
};

// 技能标签选项
const skillOptions = computed(() => {
  // 根据实训类型提供不同的技能建议
  const skillsByType: Record<string, string[]> = {
    bi: ['数据可视化', 'BI分析', 'Dashboard设计', 'SQL', '数据分析', '报表制作'],
    ai: ['机器学习', '深度学习', 'Python', 'TensorFlow', 'PyTorch', '数据预处理', '模型评估'],
    jupyter: ['Python', '数据分析', 'Pandas', 'NumPy', 'Matplotlib', 'Jupyter', '编程']
  };
  
  const skills = skillsByType[formState.type] || [];
  return skills.map(skill => ({ value: skill, label: skill }));
});

// 是否显示环境选择（Jupyter类型需要选择环境）
const showEnvironmentSelect = computed(() => {
  return formState.type === 'jupyter';
});

// 根据类型过滤环境
const filteredEnvironments = computed(() => {
  if (formState.type === 'jupyter') {
    return environments.value.filter(env => env.type === 'jupyter' || env.type === 'python');
  }
  return environments.value;
});

// 分类选项
const categoryOptions = computed(() => {
  const options: any[] = [];
  directionCategories.value.forEach(primary => {
    // 添加一级分类
    options.push({
      value: primary.id,
      label: primary.name
    });
    // 添加二级分类
    if (primary.children) {
      primary.children.forEach(secondary => {
        options.push({
          value: secondary.id,
          label: `${primary.name} - ${secondary.name}`
        });
      });
    }
  });
  return options;
});

// 获取分类标签
const getCategoryLabel = (value: string) => {
  const option = categoryOptions.value.find(opt => opt.value === value);
  return option ? option.label : value;
};

// 上传地址
const uploadUrl = computed(() => {
  return `${import.meta.env.VITE_API_BASE_URL}/v1/upload/image`;
});

// 处理类型改变
const handleTypeChange = () => {
  // 切换类型时清空环境选择
  formState.environment = undefined;
  
  // 清空技能标签，让用户重新选择
  formState.skills = [];
};

// 处理分类选择变化
const handleCategoryChange = (value: string[]) => {
  if (value.length > 3) {
    formState.categories = value.slice(0, 3);
    message.warning('最多只能选择3个分类');
  }
};

// 处理环境选择变化
const handleEnvironmentChange = (value: string) => {
  console.log('选择的环境:', value);
};

// 上传前检查
const beforeUpload = (file: File) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('只能上传 JPG/PNG 格式的图片！');
    return false;
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('图片大小不能超过 2MB！');
    return false;
  }
  return true;
};

// 处理封面上传
const handleCoverChange = (info: UploadChangeParam) => {
  if (info.file.status === 'uploading') {
    return;
  }
  if (info.file.status === 'done') {
    // 假设服务器返回的数据格式为 { url: 'xxx' }
    if (info.file.response && info.file.response.data) {
      formState.coverImage = info.file.response.data.url;
      message.success('封面上传成功');
    }
  } else if (info.file.status === 'error') {
    message.error('封面上传失败');
  }
};

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value?.validateFields();
    
    creating.value = true;
    
    const trainingData: NewTraining = {
      name: formState.name,
      type: formState.type,
      intro: formState.intro,
      difficulty: formState.difficulty,
      categories: formState.categories,
      environment: formState.environment,
      coverImage: formState.coverImage
    };
    
    // 获取当前用户ID
    const creatorId = requireCurrentUserId();
    
    const result = await createTraining(trainingData, creatorId);
    
    if (result) {
      message.success('实训课程创建成功');
      // 跳转到编辑页面
      router.push(`/course/training/${result.training_id}/edit`);
    } else {
      message.error('创建失败，请稍后重试');
    }
  } catch (error) {
    console.error('创建实训失败:', error);
    message.error('创建失败，请检查输入是否正确');
  } finally {
    creating.value = false;
  }
};

// 取消
const handleCancel = () => {
  router.back();
};

// 加载环境列表
const loadEnvironments = async () => {
  try {
    environments.value = await fetchTrainingEnvironments();
  } catch (error) {
    console.error('加载环境列表失败:', error);
  }
};

// 加载方向分类
const loadDirectionCategories = async () => {
  try {
    // 使用practice的API，因为方向分类是通用的
    directionCategories.value = await fetchDirectionCategories();
  } catch (error) {
    console.error('加载方向分类失败:', error);
  }
};

// 初始化
onMounted(() => {
  loadEnvironments();
  loadDirectionCategories();
});
</script>

<style scoped>
.training-create-page {
  padding: 24px;
  background-color: #f0f2f5;
  min-height: 100vh;
}

.training-card {
  max-width: 1000px;
  margin: 0 auto;
}

.form-item-hint {
  margin-left: 8px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
}

.type-description {
  margin-top: 8px;
  padding: 8px 12px;
  background-color: #f0f7ff;
  border-radius: 4px;
}

.type-description p {
  margin: 0;
  font-size: 12px;
  color: #1890ff;
  display: flex;
  align-items: center;
  gap: 4px;
}

.cover-uploader :deep(.ant-upload) {
  width: 200px;
  height: 112px;
}

.cover-uploader :deep(.ant-upload-select-picture-card) {
  width: 200px;
  height: 112px;
}
</style>
