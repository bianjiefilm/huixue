<template>
  <div class="bi-embed-container">
    <TempoBIDesigner
      v-if="isReady"
      ref="designerRef"
      :trainingId="trainingId"
      :classroomId="classroomId"
      :initialData="initialData"
      :snapshot="snapshot"
      :readOnly="readOnly"
      @save="onSave"
      @spec-change="onSpecChange"
    />
    <div v-else class="loading-overlay">
      <a-spin tip="正在初始化可视化环境..." />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import TempoBIDesigner from '@/components/TempoBIDesigner.vue';

const route = useRoute();
const designerRef = ref<any>(null);

// State synced via postMessage
const isReady = ref(false);
const trainingId = ref<number | string>(route.params.id as string || '');
const classroomId = ref<string>(route.query.classroomId as string || '');
const initialData = ref<any[]>([]);
const snapshot = ref<any>(null);
const readOnly = ref<boolean>(false);

// Handle incoming messages from parent window
const handleMessage = (event: MessageEvent) => {
  const data = event.data;
  if (data?.type === 'INIT_BI_DESIGNER') {
    if (data.payload.trainingId) trainingId.value = data.payload.trainingId;
    if (data.payload.classroomId) classroomId.value = data.payload.classroomId;
    if (data.payload.initialData) initialData.value = data.payload.initialData;
    if (data.payload.snapshot) snapshot.value = data.payload.snapshot;
    if (data.payload.readOnly !== undefined) readOnly.value = data.payload.readOnly;
    
    isReady.value = true;
  }
};

const onSave = (data: any) => {
  try {
    window.parent?.postMessage({ type: 'BI_DESIGNER_SAVE', payload: JSON.parse(JSON.stringify(data)) }, '*');
  } catch (e) {
    console.warn('BI_DESIGNER_SAVE postMessage failed:', e);
  }
};

const onSpecChange = (spec: any) => {
  try {
    window.parent?.postMessage({ type: 'BI_DESIGNER_SPEC_CHANGE', payload: JSON.parse(JSON.stringify(spec)) }, '*');
  } catch (e) {
    console.warn('BI_DESIGNER_SPEC_CHANGE postMessage failed:', e);
  }
};

onMounted(() => {
  window.addEventListener('message', handleMessage);
  // Notify parent that iframe is ready to receive data
  window.parent?.postMessage({ type: 'BI_DESIGNER_READY' }, '*');
});

onUnmounted(() => {
  window.removeEventListener('message', handleMessage);
});
</script>

<style scoped>
.bi-embed-container {
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.loading-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  background: white;
}
</style>
