<template>
  <a-modal
    v-model:open="visible"
    :title="isMultiple ? '批量发布课程' : '发布课程'"
    width="600px"
    @cancel="handleCancel"
    @ok="handleOk"
    :confirmLoading="loading"
  >
    <a-form
      ref="formRef"
      :model="formState"
      :rules="rules"
      layout="vertical"
    >
      <div v-if="!isMultiple" class="course-info">
        <h4>{{ courseName }}</h4>
      </div>
      <div v-else class="course-info">
        <h4>将发布 {{ courseIds.length }} 个课程</h4>
      </div>

      <a-form-item label="截止时间" name="deadline">
        <a-date-picker
          v-model:value="formState.deadline"
          show-time
          :disabled-date="disabledDate"
          format="YYYY-MM-DD HH:mm"
          placeholder="请选择截止时间"
          style="width: 100%"
        />
        <div class="form-help">学生需要在此时间前完成课程学习</div>
      </a-form-item>

      <a-form-item label="课程属性" name="isMandatory">
        <a-radio-group v-model:value="formState.isMandatory">
          <a-radio :value="true">必修课程</a-radio>
          <a-radio :value="false">选修课程</a-radio>
        </a-radio-group>
        <div class="form-help">必修课程将计入最终成绩</div>
      </a-form-item>

      <a-form-item label="迟交设置">
        <a-checkbox v-model:checked="formState.allowLateSubmission">
          允许迟交
        </a-checkbox>
        <div v-if="formState.allowLateSubmission" class="late-settings">
          <a-form-item label="迟交扣分" name="lateDeduction">
            <a-input-number
              v-model:value="formState.lateDeduction"
              :min="0"
              :max="100"
              style="width: 150px"
            />
            <span class="unit">分</span>
          </a-form-item>
          <a-form-item label="补交截止时间" name="makeupDeadline">
            <a-date-picker
              v-model:value="formState.makeupDeadline"
              show-time
              :disabled-date="disabledMakeupDate"
              format="YYYY-MM-DD HH:mm"
              placeholder="不填则默认为截止时间后7天"
              style="width: 100%"
            />
          </a-form-item>
        </div>
      </a-form-item>

      <a-form-item label="成绩设置">
        <a-checkbox v-model:checked="formState.publicizeGrades">
          公开成绩
        </a-checkbox>
        <div class="form-help">选中后，学生可查看其他学生的成绩</div>
      </a-form-item>

      <a-form-item label="答案设置">
        <a-checkbox v-model:checked="formState.publicizeAnswers">
          完成后公开答案
        </a-checkbox>
        <div class="form-help">选中后，学生完成课程后可查看标准答案</div>
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { message } from 'ant-design-vue';
import type { FormInstance } from 'ant-design-vue';
import type { Dayjs } from 'dayjs';
import dayjs from 'dayjs';
import { publishSingleCourse, publishClassroomCourses } from '@/api/classrooms';
import { useUserStore } from '@/stores/user';

interface PublishFormState {
  deadline: Dayjs | null;
  isMandatory: boolean;
  allowLateSubmission: boolean;
  lateDeduction: number;
  makeupDeadline: Dayjs | null;
  publicizeGrades: boolean;
  publicizeAnswers: boolean;
}

const props = defineProps<{
  classroomId: number;
  courseId?: number;
  courseIds?: number[];
  courseName?: string;
  classroomEndDate?: string;
}>();

const emit = defineEmits(['success', 'cancel']);

const userStore = useUserStore();
const visible = ref(false);
const loading = ref(false);
const formRef = ref<FormInstance>();

const isMultiple = computed(() => props.courseIds && props.courseIds.length > 0);

const formState = reactive<PublishFormState>({
  deadline: null,
  isMandatory: true,
  allowLateSubmission: true,
  lateDeduction: 10,
  makeupDeadline: null,
  publicizeGrades: false,
  publicizeAnswers: false
});

const rules = {
  deadline: [
    { required: true, message: '请选择截止时间', trigger: 'change' }
  ],
  lateDeduction: [
    { required: true, message: '请输入迟交扣分', trigger: 'blur' }
  ]
};

// 禁用日期：不能早于今天，不能晚于课堂结束时间
const disabledDate = (current: Dayjs) => {
  const today = dayjs().startOf('day');
  const endDate = props.classroomEndDate ? dayjs(props.classroomEndDate) : null;
  
  if (current.isBefore(today)) {
    return true;
  }
  
  if (endDate && current.isAfter(endDate)) {
    return true;
  }
  
  return false;
};

// 补交截止时间不能早于截止时间
const disabledMakeupDate = (current: Dayjs) => {
  if (!formState.deadline) {
    return true;
  }
  
  return current.isBefore(formState.deadline);
};

const open = () => {
  visible.value = true;
  // 重置表单
  formState.deadline = null;
  formState.isMandatory = true;
  formState.allowLateSubmission = true;
  formState.lateDeduction = 10;
  formState.makeupDeadline = null;
  formState.publicizeGrades = false;
  formState.publicizeAnswers = false;
};

const handleCancel = () => {
  visible.value = false;
  emit('cancel');
};

const handleOk = async () => {
  try {
    await formRef.value?.validateFields();
    loading.value = true;

    const publishData = {
      deadline_at: formState.deadline?.format('YYYY-MM-DD HH:mm:ss'),
      is_mandatory: formState.isMandatory,
      allow_late_submission: formState.allowLateSubmission,
      late_submission_deduction_points: formState.allowLateSubmission ? formState.lateDeduction : 0,
      makeup_deadline_at: formState.makeupDeadline?.format('YYYY-MM-DD HH:mm:ss'),
      publicize_grades: formState.publicizeGrades,
      publicize_answers_after_completion: formState.publicizeAnswers
    };

    if (isMultiple.value) {
      // 批量发布
      const response = await publishClassroomCourses({
        classroomId: props.classroomId,
        courseIds: props.courseIds!,
        teacherId: userStore.userId,
        ...publishData
      });
      
      if (response.code === '0000') {
        message.success(`成功发布 ${props.courseIds!.length} 个课程`);
        visible.value = false;
        emit('success');
      } else {
        message.error(response.message || '发布失败');
      }
    } else {
      // 单个发布
      const response = await publishSingleCourse({
        classroomId: props.classroomId,
        courseId: props.courseId!,
        teacherId: userStore.userId,
        ...publishData
      });
      
      if (response.code === '0000') {
        message.success('课程发布成功');
        visible.value = false;
        emit('success');
      } else {
        message.error(response.message || '发布失败');
      }
    }
  } catch (error) {
    console.error('发布课程失败:', error);
    if (error !== 'validation failed') {
      message.error('发布课程失败，请稍后重试');
    }
  } finally {
    loading.value = false;
  }
};

defineExpose({
  open
});
</script>

<style scoped>
.course-info {
  margin-bottom: 20px;
  padding: 12px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.course-info h4 {
  margin: 0;
  color: #333;
}

.form-help {
  color: #666;
  font-size: 12px;
  margin-top: 4px;
}

.late-settings {
  margin-top: 12px;
  padding-left: 24px;
}

.unit {
  margin-left: 8px;
}
</style>