<template>
  <div class="file-explorer">
    <div class="file-explorer-header">
      <div class="file-explorer-title">
        <folder-outlined />
        <span>文件资源管理器</span>
      </div>
    </div>
    <div class="file-explorer-content">
      <a-tree
        :tree-data="treeData"
        :selected-keys="selectedKeys"
        :expanded-keys="expandedKeys"
        :auto-expand-parent="true"
        @select="onSelect"
        @expand="onExpand"
      >
        <template #title="{ title, key, isLeaf }">
          <span class="file-node">
            <folder-outlined v-if="!isLeaf" />
            <file-outlined v-else />
            <span class="file-name">{{ title }}</span>
          </span>
        </template>
      </a-tree>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { FolderOutlined, FileOutlined } from '@ant-design/icons-vue';

// 定义树节点类型
interface TreeNode {
  key: string;
  title: string;
  isLeaf?: boolean;
  children?: TreeNode[];
}

// 定义组件属性
const props = defineProps({
  files: {
    type: Array as () => TreeNode[],
    default: () => []
  },
  defaultSelectedKey: {
    type: String,
    default: ''
  }
});

// 定义事件
const emit = (['select']);

// 状态
const treeData = ref<TreeNode[]>(props.files);
const selectedKeys = ref<string[]>([props.defaultSelectedKey]);
const expandedKeys = ref<string[]>([]);

// 选择文件事件处理
const onSelect = (keys: string[], info: any) => {
  selectedKeys.value = keys;
  if (keys.length > 0) {
    emit('select', keys[0], info.node);
  }
};

// 展开/折叠文件夹事件处理
const onExpand = (keys: string[]) => {
  expandedKeys.value = keys;
};

// 暴露给父组件的方法
defineExpose({
  selectFile: (key: string) => {
    selectedKeys.value = [key];
    emit('select', key);
  }
});
</script>

<style scoped>
.file-explorer {
  width: 100%;
  height: 100%;
  border: 1px solid #e8e8e8;
  border-radius: 2px;
  background-color: #fafafa;
  overflow: auto;
}

.file-explorer-header {
  padding: 8px 16px;
  border-bottom: 1px solid #e8e8e8;
  background-color: #f5f5f5;
}

.file-explorer-title {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}

.file-explorer-title :deep(svg) {
  margin-right: 8px;
  color: rgba(0, 0, 0, 0.65);
}

.file-explorer-content {
  padding: 8px;
}

.file-node {
  display: flex;
  align-items: center;
}

.file-node :deep(svg) {
  margin-right: 8px;
  color: rgba(0, 0, 0, 0.65);
}

.file-name {
  font-size: 14px;
}
</style> 