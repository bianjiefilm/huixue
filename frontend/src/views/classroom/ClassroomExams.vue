<template>
  <div class="classroom-exams-page">
    <ClassroomExamList :classroomId="classroomId" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ClassroomExamList from './ClassroomExamList.vue';

const route = useRoute();
const classroomId = computed(() => route.params.classroomId as string);
</script>

<style scoped>
.classroom-exams-page {
  min-height: 100vh;
  background: #f5f5f5;
}
</style>
