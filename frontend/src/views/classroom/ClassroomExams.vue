<template>
  <PageShell max-width="wide" class="classroom-exams-page">
    <ClassroomExamList :classroomId="classroomId" />
  </PageShell>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ClassroomExamList from './ClassroomExamList.vue';
import PageShell from '@/components/common/PageShell.vue';

const route = useRoute();
const classroomId = computed(() => route.params.classroomId as string);
</script>

<style scoped>
.classroom-exams-page {
  min-height: 0;
}
</style>
