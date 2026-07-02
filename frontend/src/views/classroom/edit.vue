<template>
  <div class="classroom-edit-page">
    <a-spin :spinning="loading" tip="加载中...">
      <div class="content-container">
        <!-- 返回按钮 -->
        <div class="back-link">
          <router-link :to="`/classroom/${classroomId}`">
            <a-button type="link">
              <template #icon><arrow-left-outlined /></template>
              返回课堂详情
            </a-button>
          </router-link>
        </div>

        <!-- 页面标题 -->
        <div class="page-header">
          <h1>编辑课堂</h1>
          <p class="page-description">修改课堂信息及相关设置</p>
        </div>

        <!-- 编辑表单 -->
        <a-card class="edit-form-card">
          <a-form
            :model="formState"
            :rules="rules"
            ref="formRef"
            layout="vertical"
            @finish="handleSubmit"
          >
            <a-form-item name="name" label="课堂名称">
              <a-input v-model:value="formState.name" placeholder="请输入课堂名称" />
            </a-form-item>
            
            <a-form-item name="description" label="课堂描述">
              <a-textarea 
                v-model:value="formState.description" 
                placeholder="请输入课堂描述" 
                :rows="4" 
              />
            </a-form-item>
            
            <a-form-item label="起止时间" required>
              <div class="date-range-container">
                <a-form-item-rest>
                  <a-tooltip :title="isOngoing ? '课堂已开始，无法修改开始时间' : ''">
                    <a-date-picker
                      v-model:value="formState.startDate"
                      show-time
                      format="YYYY-MM-DD HH:mm"
                      placeholder="开始时间"
                      :disabled="isOngoing"
                      style="width: 45%"
                    />
                  </a-tooltip>
                </a-form-item-rest>
                <span class="date-separator">至</span>
                <a-form-item-rest>
                  <a-date-picker
                    v-model:value="formState.endDate"
                    show-time
                    format="YYYY-MM-DD HH:mm"
                    placeholder="结束时间"
                    :disabled-date="disabledEndDate"
                    style="width: 45%"
                  />
                </a-form-item-rest>
              </div>
              <div v-if="isOngoing" class="ongoing-hint">
                <InfoCircleOutlined /> 课堂正在进行中，开始时间不可修改
              </div>
            </a-form-item>
            
            <a-form-item name="credits" label="学分">
              <a-input-number
                v-model:value="formState.credits"
                :min="1"
                :max="100"
                style="width: 100%"
              />
            </a-form-item>
            
            <a-form-item>
              <a-space>
                <a-button type="primary" html-type="submit" :loading="submitting">保存修改</a-button>
                <a-button @click="handleCancel">取消</a-button>
              </a-space>
            </a-form-item>
          </a-form>
        </a-card>
      </div>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';
import { ArrowLeftOutlined, InfoCircleOutlined } from '@ant-design/icons-vue';
import { useClassroomStore } from '../../stores/classroom';
import dayjs from 'dayjs';
import type { ClassroomDetail } from '@/types/classroom';

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();
const formRef = ref<FormInstance>();

// 状态变量
const loading = ref(false);
const submitting = ref(false);
const classroomId = computed(() => route.params.id as string);

// 表单状态
const formState = reactive({
  name: '',
  description: '',
  startDate: null as any,
  endDate: null as any,
  credits: 0
});

// 原始开始日期（用于判断课堂是否已开始）
const originalStartDate = ref<any>(null);

// 判断课堂是否正在进行中（已开始但未结束）
const isOngoing = computed(() => {
  if (!originalStartDate.value) return false;
  const now = dayjs();
  const start = dayjs(originalStartDate.value);
  return now.isAfter(start);
});

// 禁用结束日期（必须在开始日期之后）
const disabledEndDate = (current: any) => {
  if (!formState.startDate) return false;
  return current && current.valueOf() <= dayjs(formState.startDate).valueOf();
};

// 表单验证规则
const rules = {
  name: [{ required: true, message: '请输入课堂名称', trigger: 'blur' }],
  credits: [{ required: true, type: 'number', message: '请输入学分', trigger: 'change' }]
};

// 获取课堂信息并填充表单
const fetchClassroomDetail = async () => {
  loading.value = true;
  try {
    await classroomStore.fetchClassroomDetail(classroomId.value);
    
    if (classroomStore.currentClassroom) {
      const classroom = classroomStore.currentClassroom;
      
      // 填充表单（兼容 snake_case 和 camelCase）
      formState.name = classroom.name;
      formState.description = classroom.description || '';

      // 兼容 API 返回的 snake_case 和 camelCase 字段名
      const startDateValue = classroom.startDate || (classroom as any).start_date;
      const endDateValue = classroom.endDate || (classroom as any).end_date;
      const creditsValue = classroom.credits ?? (classroom as any).credit ?? 0;

      formState.startDate = dayjs(startDateValue);
      formState.endDate = dayjs(endDateValue);
      formState.credits = creditsValue;

      // 保存原始开始日期，用于判断课堂状态
      originalStartDate.value = startDateValue;
    } else {
      message.error('获取课堂信息失败');
      router.push('/classroom');
    }
  } catch (error) {
    console.error('获取课堂详情失败:', error);
    message.error('获取课堂详情失败，请稍后重试');
  } finally {
    loading.value = false;
  }
};

// 提交表单
const handleSubmit = async () => {
  submitting.value = true;
  try {
    // 验证日期
    if (!formState.startDate || !formState.endDate) {
      message.error('请选择起止时间');
      submitting.value = false;
      return;
    }

    // 验证结束时间必须在开始时间之后
    if (dayjs(formState.endDate).isBefore(dayjs(formState.startDate))) {
      message.error('结束时间必须在开始时间之后');
      submitting.value = false;
      return;
    }

    const data: Partial<ClassroomDetail> = {
      name: formState.name,
      description: formState.description,
      // 如果课堂已开始，保持原始开始时间不变
      startDate: isOngoing.value
        ? dayjs(originalStartDate.value).format('YYYY-MM-DD HH:mm:ss')
        : dayjs(formState.startDate).format('YYYY-MM-DD HH:mm:ss'),
      endDate: dayjs(formState.endDate).format('YYYY-MM-DD HH:mm:ss'),
      credits: formState.credits
    };

    await classroomStore.updateClassroomInfo(classroomId.value, data);

    message.success('课堂信息更新成功');
    router.push(`/classroom/${classroomId.value}`);
  } catch (error) {
    console.error('更新课堂失败:', error);
    message.error('更新课堂失败，请稍后重试');
  } finally {
    submitting.value = false;
  }
};

// 取消编辑
const handleCancel = () => {
  router.push(`/classroom/${classroomId.value}`);
};

// 初始化
onMounted(() => {
  fetchClassroomDetail();
});
</script>

<style scoped>
.classroom-edit-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.content-container {
  background: #fff;
  border-radius: 2px;
  padding: 24px;
}

.back-link {
  margin-bottom: 16px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.85);
}

.page-description {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.45);
}

.edit-form-card {
  margin-bottom: 24px;
}

.date-range-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-separator {
  color: rgba(0, 0, 0, 0.45);
  flex-shrink: 0;
}

.ongoing-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #faad14;
  display: flex;
  align-items: center;
  gap: 4px;
}
</style> 