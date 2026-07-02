<template>
  <a-modal
    v-model:open="visible"
    title="实践课程设置"
    width="700px"
    @cancel="handleCancel"
    :footer="null"
  >
    <a-spin :spinning="settingsLoading">
      <a-form v-if="courseToEditSettings">
        
        <div class="mokuai"><span class="shuxian"></span>补交设置</div>
        <a-form-item label="补交扣分">
          <a-input-number
            v-model:value="courseToEditSettings.bu_cut"
            :min="0"
            :max="100"
            style="width: 150px"
            addon-after="分"
          />
          <div slot="help" class="form-item-extra">学生在截止时间后提交作业将被扣除相应分数</div>
        </a-form-item>
        <a-form-item label="结束时间">
			<a-input
			  :value="formatDate(courseToEditSettings.bu_enddate)"
			  disabled
			  style="width: 150px"
			>
			  <template #prefix>
			    <CalendarOutlined />
			  </template>
			</a-input>
          <div slot="help" class="form-item-extra">学生延时提交作业的截止时间，同课堂的截止时间</div>
        </a-form-item>
    
        <div class="mokuai"><span class="shuxian"></span>评分设置</div>
        <a-form-item label="总分值">
          <a-input-number
		    disabled
            v-model:value="courseToEditSettings.score"
            :min="0"
            :max="100"
            style="width: 150px"
            addon-after="分"
          />
          <div slot="help" class="form-item-extra">每个课程的总分值固定为100分</div>
        </a-form-item>
		关卡名称(学生完成的关卡，支持跳关学习)
		<div>
			<a-form-item v-for="(tasks,index) in courseToEditSettings.task_scores">
				<span slot="label" class="task-title">{{tasks.title}}</span>
			  <a-input-number
			    v-model:value="courseToEditSettings.task_scores[index].score"
			    :min="0"
			    :max="100"
			    style="width: 150px"
			    addon-after="分"
			  />
			</a-form-item>
		</div>
        <div class="mokuai"><span class="shuxian"></span>公开设置</div>
        <a-form-item>
          <a-checkbox v-model:checked="coursePublicScores">公开成绩</a-checkbox>
          <div slot="help" class="form-item-extra">选中后，已提交作业的学生可查看其他学生的成绩</div>
        </a-form-item>
    
        <a-form-item>
          <a-checkbox v-model:checked="coursePublicAnswers">公开答案</a-checkbox>
          <div slot="help" class="form-item-extra">选中后，学生在关卡通关后可查看标准答案</div>
        </a-form-item>
        <div class="modal-footer">
          <a-button @click="showCourseSettingsModal = false">取消</a-button>
          <a-button type="primary" @click="saveCourseSettings" :loading="savingSettings">保存设置</a-button>
        </div>
      </a-form>
       <a-empty v-else description="无法加载课程设置" />
    </a-spin>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref,computed,onMounted,reactive } from 'vue';
import {
    ReadOutlined, PlusOutlined, DownOutlined, TableOutlined, CodeOutlined, BookOutlined,
    CalendarOutlined, ClockCircleOutlined, FlagOutlined, MenuOutlined
  } from '@ant-design/icons-vue';
import CreateClassroomForm from './CreateClassroomForm.vue';
import type { Classroom } from '@/types/course';
import { getPracticeStting,savePracticeStting } from '@/api/classrooms';
import dayjs, { Dayjs } from 'dayjs';
import { message } from 'ant-design-vue';
interface Props {
    courseId: string;
  }
const props = defineProps<Props>();

const emit = defineEmits(['cancel', 'success']);
const visible = ref(false);
const courseToEditSettings=ref('');
const settingsLoading = ref(false);
const coursePublicScores = ref(false);
const coursePublicAnswers = ref(false);
const savingSettings = ref(false);

// 打开对话框
const open = () => {
  visible.value = true;
  courseToEditSettings.value='';
  settingsLoading.value = true;
  loadSetting();
};
const loadSetting = async () => {
	try {
		const res = await getPracticeStting({ classroom_course_id: Number(props.courseId) });
		// 后端返回的数据直接在 res 中（已由 request 拦截器处理）
		const settings = res.settings_json || res;
		courseToEditSettings.value = settings;
		coursePublicScores.value = settings.publicize_grades || settings.open_score == 1;
		coursePublicAnswers.value = settings.publicize_answers_after_completion || settings.open_answer == 1;
	} catch (error) {
		console.error('加载课程设置失败:', error);
	}
	settingsLoading.value = false;
}
const saveCourseSettings = async () => {
	// 校验关卡分值总和
	if (courseToEditSettings.value.task_scores) {
		const totalScore = courseToEditSettings.value.task_scores.reduce((sum, task) => sum + (task.score || 0), 0);
		if (totalScore !== 100) {
			message.error('所有关卡成绩总和需要等于100分');
			return;
		}
	}

	settingsLoading.value = true;
	let settings = { ...courseToEditSettings.value };
	settings.open_score = coursePublicScores.value ? 1 : 0;
	settings.open_answer = coursePublicAnswers.value ? 1 : 0;
	const res = await savePracticeStting({
		classroom_course_id: Number(props.courseId),
		settings: settings
	});
	
	settingsLoading.value = false;
	visible.value = false;
	message.success('保存成功');
	emit('success');
}
// 处理取消操作
const handleCancel = () => {
	visible.value = false;
  emit('cancel');
};
const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return dayjs(dateStr*1000).format('YYYY-MM-DD'); // Include time for clarity
  };
// 处理创建成功
const handleSuccess = () => {
	visible.value = false;
  emit('success');
};
// 组件挂载时
onMounted(() => {
  //loadSetting();
});
// 暴露方法给父组件
defineExpose({
  open
});
</script> 
<style>
	.form-item-extra {
	  color: #666;
	  font-size: 12px;
	  margin-top: 4px;
	  display: inline-block;
	  padding-left: 5px;
	}
	.modal-footer {
	  display: flex;
	  justify-content: flex-end;
	  margin-top: 24px; /* Increased space */
	  padding-top: 16px; /* Add padding if border is needed */
	  /* border-top: 1px solid #f0f0f0; */ /* Optional: line above footer */
	  gap: 8px;
	}
	.mokuai{
		color: #326bef;
		display: flex;
		align-items: center;
		font-weight: 600;
		margin-bottom: 10px;
	}
	.mokuai .shuxian{
		display: inline-block;
		width: 3px;
		height: 15px;
		background-color: #326bef;
		border-radius: 2px;
		margin-right: 8px;
	}
	.task-title{
		color: #255ad5;
		padding-left: 20px;
		padding-right: 10px;
		display: inline-block;
		margin-top: 4px;
	}
</style>