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
          <a-menu-item key="setting">
            <span>设置</span>
          </a-menu-item>
          <a-menu-item key="rename">
            <span>重命名</span>
          </a-menu-item>
          <a-menu-item key="delete">
            <span>删除</span>
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>

    <!-- 重命名弹框 -->
    <a-modal
      v-model:open="renameModalVisible"
      title="重命名课程"
      :maskClosable="false"
      @cancel="handleRenameCancel"
      :width="400"
    >
      <div class="rename-container">
        <a-form layout="vertical">
          <a-form-item label="课程名称" required>
            <a-input
              v-model:value="newName"
              placeholder="请输入课程名称"
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
      title="删除课程"
      :maskClosable="false"
      @cancel="handleDeleteCancel"
      :width="450"
    >
      <div class="delete-warning">
        <p>确定要删除课程"<strong>{{ courseName }}</strong>"吗？</p>
        <a-alert
          type="warning"
          show-icon
          :message="'删除后将清空该课程下所有学生的作业提交记录和成绩数据，此操作不可恢复！'"
          style="margin-top: 12px"
        />
      </div>
      <template #footer>
        <a-button @click="handleDeleteCancel">取消</a-button>
        <a-button type="primary" danger @click="handleDeleteSubmit">确认删除</a-button>
      </template>
    </a-modal>

    <!-- 课程设置模态框 -->
    <course-settings-modal
      ref="settingsMosdalRef"
      :courseId="String(courseId)"
      @success="handleSettingSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { message } from 'ant-design-vue';
import { EllipsisOutlined } from '@ant-design/icons-vue';
import { renameClassroomCourse, delClassRoomPractice } from '@/api/classrooms';
import CourseSettingsModal from '../../components/classroom/CourseSettingsModal.vue';

interface Course {
  id: number;
  name?: string;
  name_override?: string;
  title?: string;
  course_name?: string;
  [key: string]: any;
}

interface CourseProps {
  course: Course;
  chapterId?: number | string;
}

const props = defineProps<CourseProps>();
const emit = defineEmits(['rename', 'delete', 'edit', 'publish', 'viewStudents']);

const renameModalVisible = ref(false);
const deleteModalVisible = ref(false);
const newName = ref('');
const settingsMosdalRef = ref();

// 计算课程ID和名称
const courseId = computed(() => props.course?.id);
const courseName = computed(() =>
  props.course?.name_override || props.course?.title || props.course?.name || props.course?.course_name || ''
);

// 处理菜单点击
const handleMenuClick = ({ key }: { key: string }) => {
  if (key === 'rename') {
    renameModalVisible.value = true;
    newName.value = courseName.value;
  } else if (key === 'delete') {
    deleteModalVisible.value = true;
  } else if (key === 'setting') {
    settingsMosdalRef.value.open();
  }
};

// 重命名相关
const handleRenameCancel = () => {
  renameModalVisible.value = false;
};

const handleRenameSubmit = async () => {
  if (!newName.value.trim()) {
    message.warning('请输入课程名称');
    return;
  }
  try {
    await renameClassroomCourse(Number(courseId.value), newName.value);
    message.success('课程重命名成功');
    renameModalVisible.value = false;
    emit('rename');
  } catch (error) {
    console.error('重命名失败:', error);
  }
};

// 删除相关
const handleDeleteCancel = () => {
  deleteModalVisible.value = false;
};

const handleDeleteSubmit = async () => {
  try {
    await delClassRoomPractice({ classroom_course_id: Number(courseId.value) });
    message.success('课程删除成功');
    deleteModalVisible.value = false;
    emit('delete');
  } catch (error) {
    console.error('删除失败:', error);
  }
};

const handleSettingSuccess = () => {
  emit('rename');
};
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