<template>
  <div class="ai-embed-container">
    <iframe
      :src="iframeSrc"
      class="ai-designer-iframe"
      frameborder="0"
    ></iframe>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// Pass any query params (e.g., id) to the iframe
const iframeSrc = computed(() => {
  const idStr = route.query.id ? `/${route.query.id}` : '';
  return `/#/designer/ml${idStr}?embedded=true`;
});
</script>

<style scoped>
.ai-embed-container {
  width: 100%;
  height: calc(100vh - 64px); /* Assuming header is 64px */
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #f0f2f5;
}

.ai-designer-iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}
</style>
