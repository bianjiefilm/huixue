<template>
  <a-modal
    :open="open"
    title="新建课堂"
    :footer="null"
    @cancel="handleCancel"
    :maskClosable="false"
    :destroyOnClose="true"
    width="600px"
  >
    <create-classroom-form @success="handleSuccess" @cancel="handleCancel" />
  </a-modal>
</template>

<script lang="ts" setup>
// defineProps is a compiler macro and doesn't need to be imported
import CreateClassroomForm from './CreateClassroomForm.vue';
import type { Classroom } from '@/types/course';

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits(['update:open', 'success']);

// 处理取消操作
const handleCancel = () => {
  emit('update:open', false);
};

// 处理创建成功
const handleSuccess = (classroom: Classroom) => {
  emit('success', classroom);
  emit('update:open', false);
};
</script> 