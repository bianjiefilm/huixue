<template>
  <div class="practice-create-page">
    <a-card class="practice-card" title="新建实践课程">
      <a-form 
        ref="formRef"
        :model="formState"
        :rules="rules"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 18 }"
      >
        <!-- 实践名称 -->
        <a-form-item label="实践名称" name="name">
          <a-input 
            v-model:value="formState.name" 
            placeholder="请输入实践名称" 
            :maxlength="60"
            show-count
          />
        </a-form-item>

        <!-- 实践分类 -->
        <a-form-item label="实践分类" name="type">
          <a-radio-group v-model:value="formState.type">
            <a-radio value="code">在线编码实践</a-radio>
            <a-radio value="desktop">云桌面实践</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 实践介绍 -->
        <a-form-item label="实践介绍" name="introduction">
          <a-textarea 
            v-model:value="formState.introduction"
            placeholder="请输入实践介绍" 
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
        <a-form-item label="方向分类" name="categories">
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

        <!-- 实践环境 -->
        <a-form-item label="实践环境" name="environment">
          <a-select
            v-model:value="formState.environment"
            placeholder="请选择实践环境"
            style="width: 100%"
            @change="handleEnvironmentChange"
          >
            <a-select-option v-for="env in environments" :key="env.id" :value="env.id">
              {{ env.name }} ({{ env.description }})
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 高级配置区域 -->
        <a-collapse v-if="formState.environment" v-model:activeKey="activeCollapse">
          <a-collapse-panel key="advanced" header="高级配置">
            <!-- 存储空间 -->
            <a-form-item label="存储空间" name="storageSpace" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-input-number
                v-model:value="formState.storageSpace"
                :min="1"
                :max="1000"
                addon-after="Mi"
                style="width: 200px"
              />
              <span class="form-item-hint">存储空间最大值为 1Gi</span>
            </a-form-item>

            <!-- 内存限制 -->
            <a-form-item label="内存限制" name="memoryLimit" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-input-number
                v-model:value="formState.memoryLimit"
                :min="1"
                :max="2000"
                addon-after="Mi"
                style="width: 200px"
              />
              <span class="form-item-hint">内存限制最大值为 2Gi，最小值为 300Mi</span>
            </a-form-item>

            <!-- CPU限制 -->
            <a-form-item label="CPU限制" name="cpuLimit" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <a-input-number
                v-model:value="formState.cpuLimit"
                :min="0.5"
                :max="2"
                :step="0.1"
                :precision="1"
                style="width: 200px"
              />
              <span class="form-item-hint">CPU限制最大值为 2，最小值为 0.5</span>
            </a-form-item>

            <!-- 持久化路径 -->
            <a-form-item label="持久化路径" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
              <div class="persist-paths">
                <a-space v-for="(path, index) in persistPaths" :key="index" style="display: flex; margin-bottom: 8px">
                  <a-input
                    v-model:value="persistPaths[index]"
                    placeholder="请输入持久化路径"
                    style="width: 300px"
                  />
                  <a-button
                    type="primary"
                    danger
                    @click="removePersistPath(index)"
                    v-if="persistPaths.length > 1"
                  >
                    <template #icon><DeleteOutlined /></template>
                  </a-button>
                </a-space>
                <a-button type="dashed" @click="addPersistPath" style="width: 300px; margin-top: 8px">
                  <template #icon><PlusOutlined /></template>
                  添加路径
                </a-button>
              </div>
            </a-form-item>
          </a-collapse-panel>
        </a-collapse>

        <!-- 表单操作按钮 -->
        <a-form-item :wrapper-col="{ span: 18, offset: 4 }">
          <a-space>
            <a-button @click="resetForm">取消</a-button>
            <a-button type="primary" @click="submitForm" :loading="submitting">保存</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue';
import type { FormInstance } from 'ant-design-vue';

import { fetchPracticeEnvironments, fetchDirectionCategories, createPractice } from '../../../api/practice';
import type { PracticeEnvironment, DirectionCategory, NewPractice } from '../../../api/practice';
import { useUserStore } from '../../../stores/user';

const router = useRouter();
const userStore = useUserStore();
const formRef = ref<FormInstance>();
const submitting = ref(false);
const activeCollapse = ref<string[]>([]);
const environments = ref<PracticeEnvironment[]>([]);
const categories = ref<DirectionCategory[]>([]);
const persistPaths = ref<string[]>(['']);

// 表单数据
const formState = reactive<Partial<NewPractice>>({
  name: '',
  type: 'code',
  introduction: '',
  difficulty: 'beginner',
  categories: [],
  environment: '',
  storageSpace: 50,
  memoryLimit: 1024,
  cpuLimit: 1
});

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入实践名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择实践分类', trigger: 'change' }],
  introduction: [{ required: true, message: '请输入实践介绍', trigger: 'blur' }],
  difficulty: [{ required: true, message: '请选择难易度', trigger: 'change' }],
  categories: [
    { required: true, type: 'array', message: '请选择至少一个方向分类', trigger: 'change' },
    { type: 'array', max: 3, message: '最多只能选择3个分类', trigger: 'change' }
  ],
  environment: [{ required: true, message: '请选择实践环境', trigger: 'change' }],
  storageSpace: [
    { required: true, message: '请输入存储空间', trigger: 'blur' },
    { type: 'number', min: 1, max: 1000, message: '存储空间必须在 1-1000 范围内', trigger: 'blur' }
  ],
  memoryLimit: [
    { required: true, message: '请输入内存限制', trigger: 'blur' },
    { type: 'number', min: 300, max: 2000, message: '内存限制必须在 300-2000 范围内', trigger: 'blur' }
  ],
  cpuLimit: [
    { required: true, message: '请输入CPU限制', trigger: 'blur' },
    { type: 'number', min: 0.5, max: 2, message: 'CPU限制必须在 0.5-2 范围内', trigger: 'blur' }
  ]
};

// 处理分类选择变化
const handleCategoryChange = (values: string[]) => {
  if (values.length > 3) {
    // 限制最多选择3个
    formState.categories = values.slice(0, 3);
    message.warning('最多只能选择3个分类');
  }
};

// 获取分类标签显示文本
const getCategoryLabel = (value: string): string => {
  const option = categoryOptions.value.find(opt => opt.value === value);
  return option ? option.label : value;
};

// 扁平化分类下拉选项，支持分组显示
const categoryOptions = computed(() => {
  const options: { label: string; value: string; group?: string }[] = [];
  
  categories.value.forEach(category => {
    // 如果有子分类，添加子分类作为选项
    if (category.children && category.children.length > 0) {
      category.children.forEach(subCategory => {
        options.push({
          label: subCategory.name,
          value: subCategory.id,
          group: category.name
        });
      });
    } else {
      // 如果没有子分类，直接添加一级分类作为选项
      options.push({
        label: category.name,
        value: category.id,
        group: undefined
      });
    }
  });
  
  // 按分组整理选项
  const groupedOptions: any[] = [];
  const groups = new Map();
  
  options.forEach(opt => {
    if (!groups.has(opt.group)) {
      groups.set(opt.group, {
        label: opt.group,
        options: []
      });
    }
    groups.get(opt.group).options.push({
      label: opt.label,
      value: opt.value
    });
  });
  
  groups.forEach(group => {
    groupedOptions.push(group);
  });
  
  return groupedOptions;
});

// 添加持久化路径
const addPersistPath = () => {
  persistPaths.value.push('');
};

// 移除持久化路径
const removePersistPath = (index: number) => {
  persistPaths.value.splice(index, 1);
};

// 处理环境选择变化
const handleEnvironmentChange = (value: string) => {
  if (value && activeCollapse.value.length === 0) {
    activeCollapse.value = ['advanced'];
  }
};

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value?.validate();
    
    submitting.value = true;
    
    // 过滤空的持久化路径
    const validPaths = persistPaths.value.filter(path => path.trim() !== '');
    
    const practiceData: NewPractice = {
      ...formState as NewPractice,
      persistPaths: validPaths.length > 0 ? validPaths : undefined
    };
    
    const creatorId = userStore.userInfo.id;
    const result = await createPractice(practiceData, creatorId);
    
    if (result) {
      message.success('实践课程创建成功');
      // 跳转到编辑关卡页面
      router.push(`/course/practice/${result.practice_id}/edit`);
    } else {
      message.error('实践课程创建失败');
    }
  } catch (error) {
    console.error('表单验证失败:', error);
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields();
  router.back();
};

// 初始化数据
onMounted(async () => {
  try {
    console.log('[create.vue onMounted] 开始加载数据...');
    
    // 并行加载数据
    const [envData, catData] = await Promise.all([
      fetchPracticeEnvironments(),
      fetchDirectionCategories()
    ]);
    
    console.log('[create.vue onMounted] 环境数据:', envData);
    console.log('[create.vue onMounted] 分类数据:', catData);
    
    environments.value = envData;
    categories.value = catData;
    
    console.log('[create.vue onMounted] environments.value 赋值后:', environments.value);
    console.log('[create.vue onMounted] categories.value 赋值后:', categories.value);
  } catch (error) {
    console.error('[create.vue onMounted] 初始化数据失败:', error);
    message.error('加载数据失败，请刷新页面重试');
  }
});
</script>

<style scoped>
.practice-create-page {
  padding: 24px;
  background-color: #f0f2f5;
}

.practice-card {
  max-width: 1000px;
  margin: 0 auto;
}

.form-item-hint {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.persist-paths {
  display: flex;
  flex-direction: column;
}
</style> 