<template>
  <div class="toc-tree">
    <div v-if="nodes.length === 0" class="toc-empty">
      暂无目录
    </div>
    <div v-else class="toc-list">
      <TOCTreeNode
        v-for="node in nodes"
        :key="node.id"
        :node="node"
        :activeAnchor="activeAnchor"
        @node-click="handleNodeClick"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps, defineEmits } from 'vue';
import type { TOCNode } from '@/composables/useHandbookParser';
import TOCTreeNode from './TOCTreeNode.vue';

interface Props {
  nodes: TOCNode[];
  activeAnchor?: string;
}

interface Emits {
  (e: 'node-click', anchorId: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const handleNodeClick = (anchorId: string) => {
  emit('node-click', anchorId);
};
</script>

<style scoped>
.toc-tree {
  width: 100%;
}

.toc-empty {
  color: #999;
  text-align: center;
  padding: 20px;
  font-size: 14px;
}

.toc-list {
  padding: 0;
  margin: 0;
}
</style>
