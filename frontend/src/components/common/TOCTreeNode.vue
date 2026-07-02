<template>
  <div class="toc-tree-node" :class="{ 'is-active': isActive }">
    <div
      class="toc-node-title"
      :class="`level-${node.level}`"
      @click="handleClick"
    >
      <span class="node-icon" v-if="hasChildren">
        <span v-if="expanded">▼</span>
        <span v-else>▶</span>
      </span>
      <span class="node-text">{{ node.title }}</span>
    </div>

    <div v-if="hasChildren && expanded" class="toc-node-children">
      <TOCTreeNode
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :activeAnchor="activeAnchor"
        @node-click="$emit('node-click', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { TOCNode } from '@/composables/useHandbookParser';

interface Props {
  node: TOCNode;
  activeAnchor?: string;
}

interface Emits {
  (e: 'node-click', anchorId: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const expanded = ref(true); // 默认展开

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0;
});

const isActive = computed(() => {
  return props.activeAnchor === props.node.anchorId;
});

const handleClick = () => {
  // 如果有子节点，切换展开状态
  if (hasChildren.value) {
    expanded.value = !expanded.value;
  }

  // 触发点击事件
  emit('node-click', props.node.anchorId);
};
</script>

<style scoped>
.toc-tree-node {
  margin-bottom: 4px;
}

.toc-node-title {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
  font-size: 14px;
  color: #595959;
  user-select: none;
}

.toc-node-title:hover {
  background-color: #f0f0f0;
  color: #1890ff;
}

.toc-node-title.is-active,
.toc-tree-node.is-active > .toc-node-title {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 500;
}

.node-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 6px;
  font-size: 10px;
  color: #8c8c8c;
}

.node-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 根据层级设置缩进 */
.toc-node-title.level-1 {
  padding-left: 12px;
  font-weight: 500;
  font-size: 15px;
}

.toc-node-title.level-2 {
  padding-left: 24px;
}

.toc-node-title.level-3 {
  padding-left: 36px;
  font-size: 13px;
}

.toc-node-title.level-4 {
  padding-left: 48px;
  font-size: 13px;
}

.toc-node-title.level-5 {
  padding-left: 60px;
  font-size: 12px;
}

.toc-node-title.level-6 {
  padding-left: 72px;
  font-size: 12px;
}

.toc-node-children {
  margin-top: 2px;
}
</style>
