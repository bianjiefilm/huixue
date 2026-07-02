<template>
  <div class="chapter-dropdown">
    <a-dropdown :trigger="['click']">
      <a class="ant-dropdown-link" @click.prevent>
        <a-button type="text" class="action-button">
          <EllipsisOutlined />
        </a-button>
      </a>
      <template #overlay>
        <a-menu @click="handleMenuClick">
          <a-menu-item key="rename">
            <span>重命名</span>
          </a-menu-item>
          <a-menu-item key="publishAll" v-if="hasUnpublishedCourses">
            <span>发布本章节所有课程</span>
          </a-menu-item>
          <a-menu-item key="delete" :disabled="hasCourses && disableDeleteWithCourses">
            <span>删除</span>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>

    <!-- 重命名弹框 -->
    <a-modal
      v-model:open="renameModalVisible"
      title="重命名章节"
      :maskClosable="false"
      @cancel="handleRenameCancel"
      :width="400"
    >
      <div class="rename-container">
        <a-form layout="vertical">
          <a-form-item label="章节名称" required>
            <a-input 
              v-model:value="newName" 
              placeholder="请输入章节名称"
              allow-clear
            />
          </a-form-item>
        </a-form>
      </div>
      <template #footer>
        <a-button @click="handleRenameCancel">取消</a-button>
        <a-button type="primary" @click="handleRenameSubmit" :disabled="!newName">确定</a-button>
      </template>
    </a-modal>

    <!-- 删除确认弹框 -->
    <a-modal
      v-model:open="deleteModalVisible"
      title="删除章节"
      :maskClosable="false"
      @cancel="handleDeleteCancel"
      :width="400"
    >
      <p>确定要删除章节"{{ name }}"吗？</p>
      <p v-if="hasCourses" class="warning-text">注意：该章节下的课程也将被一并删除。</p>
      <template #footer>
        <a-button @click="handleDeleteCancel">取消</a-button>
        <a-button type="primary" danger @click="handleDeleteSubmit">确定</a-button>
      </template>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import { EllipsisOutlined } from '@ant-design/icons-vue';
import { editClassRoomChapter,delClassRoomChapter } from '@/api/classrooms';

interface ChapterProps {
  id: string;
  name: string;
  hasCourses?: boolean;
  hasUnpublishedCourses?: boolean;
}

const props = defineProps<ChapterProps>();
const emit = defineEmits(['rename', 'delete', 'publishAll']);

const renameModalVisible = ref(false);
const deleteModalVisible = ref(false);
const newName = ref('');
const disableDeleteWithCourses = ref(false); // 设置为true可防止带课程的章节被删除

// 处理菜单点击
const handleMenuClick = ({ key }: { key: string }) => {
  if (key === 'rename') {
    renameModalVisible.value = true;
    newName.value = props.name;
  } else if (key === 'delete') {
    deleteModalVisible.value = true;
  } else if (key === 'publishAll') {
    emit('publishAll', { chapterId: props.id, chapterName: props.name });
  }
};

// 重命名相关
const handleRenameCancel = () => {
  renameModalVisible.value = false;
};

const handleRenameSubmit = async () => {
  if (!newName.value.trim()) {
    message.warning('请输入章节名称');
    return;
  }
	await editClassRoomChapter({id:props.id,name: newName.value});
  message.success('章节重命名成功');
  renameModalVisible.value = false;
  emit('rename');
};

// 删除相关
const handleDeleteCancel = () => {
  deleteModalVisible.value = false;
};

const handleDeleteSubmit = async () => {
	await delClassRoomChapter({id:props.id});
  emit('rename');
  message.success('章节删除成功');
  deleteModalVisible.value = false;
};

// 计算属性
const hasCourses = ref(props.hasCourses || false);
const hasUnpublishedCourses = ref(props.hasUnpublishedCourses || false);
const chapterName = ref(props.name);
</script>

<style scoped>
.chapter-dropdown {
  display: inline-block;
}

.action-button {
  padding: 0;
  font-size: 16px;
  line-height: 1;
}

.warning-text {
  color: #ff4d4f;
}
</style> 