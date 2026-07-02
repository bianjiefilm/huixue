<template>
	<div class="resources-header">
	    <h2>项目实训</h2>
	    <a-button v-if="isTeacherView && !isHistoricalClassroom" type="primary" @click="openAddProjectDialog">添加实训</a-button>
	  </div>
	  <div v-for="course in trainingList" :key="course.id" class="training-item">
	    <div class="course-header">
	      <div class="course-main-info">
	        <div class="mandatory-tag" v-if="course.isRequired">必修</div>
	        <div class="course-status" :class="getStatusClass(course.status)">{{ getStatusText(course.status) }}</div>
	        <div class="course-title">{{ course.name }}</div>
	        <!-- 全员完成标识 -->
	        <div v-if="isAllCompleted(course)" class="all-completed-flag">
	          <img src="/images/red-flag.svg" alt="全员完成" class="flag-icon" />
	          <span class="flag-text">全员完成</span>
	        </div>
	      </div>
	      <div class="course-meta-info">
	        <span class="industry-tag" v-if="course.industry">
	          <TagOutlined /> {{ course.industry }}
	        </span>
	        <span class="divider" v-if="course.industry && course.trainingType">|</span>
	        <span class="type-tag" v-if="course.trainingType">
	          {{ getTrainingTypeText(course.trainingType) }}
	        </span>
	      </div>
	    </div>
	    <div class="course-intro" v-if="course.introduction">
	      {{ course.introduction }}
	    </div>
	    <!-- 教师端统计信息 -->
	    <div class="course-student-stats" v-if="isTeacherView">
	      <span v-if="course.status === 'makeup'">补交中 {{ course.learningCount }}人</span>
	      <span v-if="course.status === 'makeup'">|</span>
	      <span>已完成 {{ course.completedCount }}人</span>
	      <span>|</span>
	      <span>未开始 {{ course.notStartedCount }}人</span>
	    </div>
	    <!-- 学生端进度信息 -->
	    <div class="course-student-progress" v-if="isStudentView">
	      <span>进度：{{ course.completed_task_count || 0 }}/{{ course.task_count || 0 }} 关卡</span>
	    </div>
	    <div class="course-actions">
	      <!-- 教师端操作 -->
	      <template v-if="isTeacherView">
	        <a-button size="small" type="primary" @click="viewTrainingDetail(course)">查看详情</a-button>
	        <a-button size="small" v-if="course.status !== 'unpublished'" @click="viewGrades(course)">查看成绩</a-button>
	        <a-button size="small" v-if="course.status !== 'unpublished'" @click="viewHomework(course)">作业列表</a-button>
	        <a-button size="small" v-if="!isHistoricalClassroom" @click="openSettingsDialog(course)">设置</a-button>
	        <a-button size="small" type="primary" v-if="course.status === 'unpublished' && !isHistoricalClassroom" @click="openPublishDialog(course)">发布</a-button>
	      </template>
	      <!-- 学生端操作 -->
	      <template v-else-if="isStudentView">
	        <a-button size="small" @click="viewTrainingDetail(course)">查看详情</a-button>
	        <!-- 历史课堂：只能查看记录，不能开启实训 -->
	        <template v-if="isHistoricalClassroom">
	          <a-button size="small" type="primary" @click="viewStudentRecord(course)">查看记录</a-button>
	        </template>
	        <!-- 正在上课：可以开启实训 -->
	        <template v-else>
	          <a-button size="small" type="primary" @click="startTraining(course)">开启实训</a-button>
	        </template>
	      </template>
	    </div>
	  </div>
	  <div v-if="trainingList.length === 0" class="empty-training">
	    <p v-if="isTeacherView">暂无实训课程，请点击"添加实训"按钮添加</p>
	    <p v-else>暂无实训课程</p>
	  </div>
	  <!-- Add Student Modal -->
	  <a-modal
	    v-model:open="showAddProjectModal"
	    title="添加实训"
	    :width="900"
	    :footer="null"
	    @cancel="cancelAddProject"
	  >
	     <div class="add-student-container">
	       
	    
	       <!-- Student Selection (Right Panel) -->
	       <div class="student-selection-container">
	         <!-- Available Students -->
	         <div class="available-students">
	           <div class="section-title">
	             <h4>可选 ({{ localprojectList.length }})</h4>
	             
	           </div>
	           <a-spin :spinning="loadingStudents">
	             <a-table
	               :dataSource="localprojectList"
	               :columns="projectColumns"
	               :pagination="{ pageSize: 5 }"
	               rowKey="id"
	               size="small"
	               :rowSelection="{
	                 selectedRowKeys: selectedAvailableKeys,
	                 onChange: onAvailableSelectionChange,
	                 getCheckboxProps: (record) => ({
	                     disabled: isProjectAlreadyAdded(record.id) || isProjectSelectedToAdd(record.id),
	                     name: record.id,
	                 }),
	               }"
	               :scroll="{ y: 200 }"
	             >
	               <template #bodyCell="{ column, record }">
	                  <template v-if="column.key === 'name'">
	                      <span :style="{ color: isProjectAlreadyAdded(record.id) ? '#bfbfbf' : 'inherit' }">
	                          {{ record.name }} {{ isProjectAlreadyAdded(record.id) ? '(已在课堂)' : '' }}
	                      </span>
	                  </template>
	               </template>
	             </a-table>
	           </a-spin>
	         </div>
	    
	         <!-- Selected Students -->
	         <div class="selected-students">
	           <div class="section-title">
	             <h4>已选 ({{ selectedProjectToAdd.length }})</h4>
	             <a-button
	               type="link"
	               danger
	               size="small"
	               :disabled="selectedToRemoveKeys.length === 0"
	               @click="removeSelectedStudents"
	             >
	               移除已选 ({{ selectedToRemoveKeys.length }})
	             </a-button>
	           </div>
	           <a-table
	             :dataSource="selectedProjectToAdd"
	             :columns="selectedProjectColumns"
	             :pagination="{ pageSize: 5 }"
	             rowKey="id"
	             size="small"
	             :rowSelection="{
	               selectedRowKeys: selectedToRemoveKeys,
	               onChange: onSelectedToRemoveChange
	             }"
	             :scroll="{ y: 150 }"
	           >
	             <template #bodyCell="{ column, record }">
	               <template v-if="column.key === 'action'">
	                 <a-button type="link" danger size="small" @click="removeStudentFromSelected(record)">移除</a-button>
	               </template>
	             </template>
	           </a-table>
	         </div>
	    
	         <!-- Action Buttons -->
	         <div class="student-selection-buttons">
	           <a-button @click="cancelAddProject">取消</a-button>
	           <a-button type="primary" @click="saveAddedStudents" :disabled="selectedProjectToAdd.length === 0">
	             确认添加 {{ selectedProjectToAdd.length }} 个实训
	           </a-button>
	         </div>
	       </div>
	     </div>
	  </a-modal>
</template>

<script setup lang="ts">
	import { ref, computed, watch, onMounted, h} from 'vue';
	import { useRouter } from 'vue-router';
	import { message, Modal } from 'ant-design-vue';
	import { TeamOutlined,ReloadOutlined, EditOutlined, PlusOutlined, MenuOutlined, DownOutlined, UpOutlined, SearchOutlined, UserOutlined, CalendarOutlined, FileOutlined, PlayCircleOutlined, FileTextOutlined, FilePdfOutlined, FileWordOutlined, FilePptOutlined, FileImageOutlined, FolderOutlined, MoreOutlined, TagOutlined } from '@ant-design/icons-vue';
	import { getRoomProjectList,addRoomProjects } from '@/api/classrooms';
	import { getTrainingLibrary, launchClassroomTraining } from '@/api/training';
	import { useUserStore } from '@/stores/user';
	interface Props {
	  classroomId: string;
	  userRole?: string;
	  classroomStatus?: string;
	}
	const props = defineProps<Props>();
	const router = useRouter();
	const userStore = useUserStore();

	// 是否是学生视图
	const isStudentView = computed(() => {
	  return props.userRole === 'student';
	});

	// 是否是教师/管理员视图
	const isTeacherView = computed(() => {
	  return props.userRole === 'teacher' || props.userRole === 'admin';
	});

	// 历史课堂判断
	const isHistoricalClassroom = computed(() => {
	  return props.classroomStatus === 'ENDED';
	});
	// 资源列表
	const trainingList = ref<any[]>([]);
	const localprojectList = ref<any[]>([]);
	const showAddProjectModal = ref(false);
	const loadingStudents = ref(false);
	const selectedProjectToAdd = ref<any[]>([]);
	const selectedToRemoveKeys = ref<any[]>([]);
	const selectedAvailableKeys = ref<string[]>([]); 
	// 模拟对话框方法
	const openAddResourceDialog = () => {
	  message.info('教学资源上传功能尚未实现');
	};
	
	// 查看成绩
	const viewGrades = (course: any) => {
	  const courseName = course.name || course.training_title || '';
  const classroomCourseId = course.classroom_course_id || course.classroomCourseId || course.id;
  router.push({
    path: `/classroom/${props.classroomId}/course/${classroomCourseId}/grades`,
    query: {
      courseName,
      courseType: 'training',
      courseId: course.course_id,
      practiceId: course.practice_id
    }
  });
	};
	
	// 查看作业列表
	const viewHomework = (course: any) => {
	  const courseName = course.name || course.training_title || '';
	  router.push({
    path: `/classroom/${props.classroomId}/course/${course.id}/homework`,
    query: { courseType: 'training', courseName }
  });
	};
	
	// 打开设置对话框
	const openSettingsDialog = (course: any) => {
	  // TODO: 实现实训设置功能
	  message.info('实训设置功能即将上线');
	};
	
	// 打开发布对话框
	const openPublishDialog = (course: any) => {
	  // TODO: 实现发布功能
	  message.info('发布功能即将上线');
	};
	// 加载课堂资源
	const loadResources =async() => {
	  try {
	    const res =await getRoomProjectList({classroom_id:props.classroomId});
        const resources = res.data?.list || res.data || [];
	    if (resources && resources.length > 0) {
	      // 映射 API 返回字段到模板使用的字段
	      trainingList.value = resources.map((item: any) => ({
	        ...item,
	        name: item.training_title || item.title || item.name,
	        trainingType: item.training_type,
	        industry: item.industry,
	        introduction: item.intro,
	        status: item.status || 'unpublished', // 使用API返回的状态，默认为unpublished
	        completedCount: item.completed_count || 0,
	        notStartedCount: item.not_started_count || 0,
	        learningCount: item.learning_count || 0
	      }));
	    } else {
          trainingList.value = [];
        }
	  } catch (error) {
	    message.error('加载实训失败');
        trainingList.value = [];
	  }
	};
	const projectColumns = [
	  { title: '实训名称', dataIndex: 'name', key: 'name', width: 120 },
	  { title: '行业', dataIndex: 'industry', key: 'industry', width: 120 },
	  { title: '实训模式', dataIndex: 'model_text', key: 'model_text', width: 120 },
	  { title: '难度', dataIndex: 'difficulty_text', key: 'difficulty_text', width: 120 },
	];
	const selectedProjectColumns = [
	  { title: '实训名称', dataIndex: 'name', key: 'name', width: 120 },
	  { title: '行业', dataIndex: 'industry', key: 'industry', width: 120 },
	  { title: '实训模式', dataIndex: 'model_text', key: 'model_text', width: 120 },
	  { title: '难度', dataIndex: 'difficulty_text', key: 'difficulty_text', width: 120 },
	  { title: '操作', key: 'action', width: 80 },
	];
	
	onMounted(() => {
	  loadResources(); // Load initial list (e.g., all students or from root org)
	});
	const openAddProjectDialog=async()=>{
		showAddProjectModal.value=true;
		loadingStudents.value = true;
		try {
		  const res = await getTrainingLibrary({ page: 1, page_size: 50 });
		  if (res && res.list && res.list.length > 0) {
		    // 转换数据格式以匹配表格列
		    localprojectList.value = res.list.map((item: any) => ({
		      ...item,
		      name: item.title,
		      model_text: ['DRAG_DROP', 'DATA_ANALYSIS', 'BI'].includes(item.training_type) ? '拖拽式' : '编码式',
		      difficulty_text: item.difficulty === 'beginner' ? '初级' : item.difficulty === 'intermediate' ? '中级' : '高级'
		    }));
		  }
		} catch (error) {
		  message.error('加载实训失败');
		} finally {
		  loadingStudents.value = false;
		}
	}
	const isProjectAlreadyAdded = (projectId: string): boolean => {
	    return trainingList.value.some(s => s.id === projectId);
	};
	const isProjectSelectedToAdd = (projectId: string): boolean => {
	    return selectedProjectToAdd.value.some(s => s.id === projectId);
	};
	const resetAddProjectModal = () => {
	    selectedProjectToAdd.value = [];
	    selectedToRemoveKeys.value = [];
		selectedAvailableKeys.value = [];
	};
	
	const cancelAddProject = () => {
	  showAddProjectModal.value = false;
	  resetAddProjectModal();
	};
	const onAvailableSelectionChange = (keys: string[]) => {
	    const newlySelectedKeys = keys.filter(key => !selectedAvailableKeys.value.includes(key));
	    const deselectedKeys = selectedAvailableKeys.value.filter(key => !keys.includes(key));
	
	    // Add newly selected project (that are not already added or selected)
	    newlySelectedKeys.forEach(key => {
	        const project = localprojectList.value.find(s => s.id === key);
	        if (project && !isProjectAlreadyAdded(project.id) && !isProjectSelectedToAdd(project.id)) {
	            selectedProjectToAdd.value.push(project);
	        }
	    });
	
	    // Remove deselected students from the "to add" list
	    selectedProjectToAdd.value = selectedProjectToAdd.value.filter(s => !deselectedKeys.includes(s.id));
	
	    // Update the keys for the available table's selection state
	    selectedAvailableKeys.value = keys.filter(key => !isProjectAlreadyAdded(key)); // Keep selection only for valid items
	};
	const onSelectedToRemoveChange = (keys: string[]) => {
	  selectedToRemoveKeys.value = keys;
	};
	const removeStudentFromSelected = (project) => {
	  selectedProjectToAdd.value = selectedProjectToAdd.value.filter(s => s.id !== project.id);
	  // Also deselect from the available table if it was selected there
	  selectedAvailableKeys.value = selectedAvailableKeys.value.filter(key => key !== project.id);
	};
	const removeSelectedStudents = () => {
	  if (selectedToRemoveKeys.value.length === 0) return;
	  const keysToRemove = [...selectedToRemoveKeys.value];
	  selectedProjectToAdd.value = selectedProjectToAdd.value.filter(s =>
	    !keysToRemove.includes(s.id)
	  );
	   // Also deselect from the available table
	  selectedAvailableKeys.value = selectedAvailableKeys.value.filter(key => !keysToRemove.includes(key));
	  selectedToRemoveKeys.value = []; // Clear removal selection
	};
	const saveAddedStudents = async () => {
	  if (selectedProjectToAdd.value.length === 0) return;
	
	  const trainingIdsToAdd = selectedProjectToAdd.value.map(s => s.id);
	
	  message.loading('正在添加...', 1.5);
	  try {
	    await addRoomProjects({classroom_id: parseInt(props.classroomId), course_ids: trainingIdsToAdd});
	    message.success('添加成功');
	    showAddProjectModal.value = false;
	    loadResources();
	    resetAddProjectModal();
	  } catch (error) {
	    message.error('添加失败');
	    console.error(error);
	  }
	};
	// 获取课程状态对应的类名
	const getStatusClass = (status: string) => {
	  switch (status) {
	    case 'learning':
	      return 'learning-status';
	    case 'makeup':
	      return 'makeup-status';
	    case 'completed':
	      return 'completed-status';
	    case 'unpublished':
	      return 'unpublished-status';
	    default:
	      return '';
	  }
	};
	
	// 获取课程状态文本
	const getStatusText = (status: string) => {
	  switch (status) {
	    case 'learning':
	      return '学习中';
	    case 'makeup':
	      return '补交中';
	    case 'completed':
	      return '已完成';
	    case 'unpublished':
	      return '未发布';
	    default:
	      return '';
	  }
	};
	
	// 判断是否全员完成
	const isAllCompleted = (course: any) => {
	  // 当已完成人数等于总人数，且总人数大于0时，表示全员完成
	  const totalCount = (course.completedCount || 0) + (course.learningCount || 0) + (course.notStartedCount || 0);
	  return totalCount > 0 && course.completedCount === totalCount && course.status === 'completed';
	};
	
	// 获取实训类型文本
	const getTrainingTypeText = (type: string) => {
	  const typeMap: Record<string, string> = {
	    'ai': 'AI设计器',
	    'bi': 'BI报表',
	    'jupyter': 'Jupyter笔记本'
	  };
	  return typeMap[type] || type;
	};

	const viewTrainingDetail = (course: any) => {
	  router.push(`/classroom/${props.classroomId}/training/${course.training_id}`);
	};

	// 学生开启实训
	const startTraining = async (course: any) => {
	  message.loading('正在准备实训环境...', 0);
	  try {
	    const result = await launchClassroomTraining(
	        course.training_id,
	        props.classroomId,
	        course.trainingType || course.training_type,
	        userStore.userId || ''
	    );
	    message.destroy();

	    if (result.code === '0000') {
	        const tType = course.trainingType || course.training_type;
	        if (tType === 'DATA_ANALYSIS' || tType === 'DRAG_DROP' || tType === 'BI') {
	            const routeUrl = router.resolve(`/classroom/${props.classroomId}/training/${course.training_id}/bi-designer`).href;
	            window.open(routeUrl, '_blank');
	            message.success('实训环境就绪，即将进入分析台');
	        } else if (result.data?.url) {
	            let url = result.data.url;
	            const hostname = window.location.hostname;
	            const targetHost = (hostname === 'localhost' || hostname === '127.0.0.1') ? 'localhost' : hostname;
	            url = url.replace(/https?:\/\/huixue-jupyter:8888/g, `http://${targetHost}:8888`);
	            url = url.replace(/https?:\/\/jupyter:8888/g, `http://${targetHost}:8888`);
	            url = url.replace(/http:\/\/localhost:8888/g, `http://${targetHost}:8888`);
	            url = url.replace(/http:\/\/127\.0\.0\.1:8888/g, `http://${targetHost}:8888`);
	            if (url && !url.includes('token=')) {
	                url += (url.includes('?') ? '&' : '?') + 'token=huixue_token';
	            }
	            window.open(url, '_blank');
	            message.success('Jupyter 环境已启动');
	        } else {
	            message.success('实训环境准备就绪');
	        }
	    } else {
	        message.error(result.message || "启动实训失败: API未返回成功");
	    }
	  } catch (err: any) {
	    message.destroy();
	    console.error('[startTraining] API调用异常:', err);
	    message.error(`启动异常: ${err.message}`);
	  }
	};

	// 学生查看历史记录
	const viewStudentRecord = (course: any) => {
	  router.push(`/classroom/${props.classroomId}/training/${course.training_id}/record`);
	};
</script>

<style scoped>
	.resources-header,
	.exams-header, 
	.analytics-header, 
	.cloud-header {
	  display: flex;
	  justify-content: space-between;
	  align-items: center;
	  margin-bottom: 20px;
	}
	
	.resources-header h2, 
	.exams-header h2, 
	.analytics-header h2, 
	.cloud-header h2 {
	  margin: 0;
	  font-size: 18px;
	  font-weight: 500;
	}
	
	.empty-training,
	.empty-resource, 
	.empty-exam, 
	.empty-analytics, 
	.empty-cloud {
	  padding: 40px 20px;
	  text-align: center;
	  color: #999;
	  background-color: #f9f9f9;
	  border-radius: 4px;
	  margin-top: 20px;
	}
	
	/* 实训课程项样式 */
	.training-item {
	  background: #fff;
	  border: 1px solid #e8e8e8;
	  border-radius: 8px;
	  padding: 16px;
	  margin-bottom: 12px;
	  position: relative;
	}
	
	.course-header {
	  display: flex;
	  justify-content: space-between;
	  align-items: flex-start;
	  margin-bottom: 8px;
	}
	
	.course-main-info {
	  display: flex;
	  align-items: center;
	  flex-wrap: wrap;
	  gap: 8px;
	}
	
	.course-meta-info {
	  display: flex;
	  align-items: center;
	  font-size: 13px;
	  color: #666;
	}
	
	.industry-tag, .type-tag {
	  display: flex;
	  align-items: center;
	  gap: 4px;
	}
	
	.divider {
	  margin: 0 8px;
	  color: #d9d9d9;
	}
	
	.course-intro {
	  font-size: 13px;
	  color: #666;
	  margin-bottom: 12px;
	  line-height: 1.5;
	  display: -webkit-box;
	  -webkit-line-clamp: 2;
	  -webkit-box-orient: vertical;
	  overflow: hidden;
	  text-overflow: ellipsis;
	}
	
	/* 全员完成标识 */
	.all-completed-flag {
	  display: flex;
	  align-items: center;
	  gap: 4px;
	  margin-left: 12px;
	}
	
	.flag-icon {
	  width: 20px;
	  height: 20px;
	}
	
	.flag-text {
	  font-size: 12px;
	  color: #f5222d;
	  font-weight: 500;
	}
	
	.resources-description, 
	.exams-description, 
	.analytics-description, 
	.cloud-description {
	  color: #666;
	  margin-bottom: 20px;
	  padding: 15px;
	  background-color: #f5f5f5;
	  border-radius: 4px;
	}
	.student-selection-container {
	  flex: 1;
	  display: flex;
	  flex-direction: column;
	  /* padding-left: 16px; Removed, using gap */
	  overflow: hidden; /* Prevent container overflow */
	}
	
	.available-students,
	.selected-students {
	  margin-bottom: 16px;
	  display: flex;
	  flex-direction: column;
	  min-height: 0; /* Allow shrinking */
	}
	.available-students {
	    flex-basis: 55%; /* Allocate more space to available */
	}
	.selected-students {
	    flex-basis: 45%;
	}
	
	
	.section-title {
	  display: flex;
	  justify-content: space-between;
	  align-items: center;
	  margin-bottom: 8px;
	  flex-shrink: 0;
	}
	
	.section-title h4 {
	  margin: 0;
	  font-size: 16px;
	}
	
	/* Style tables inside modal */
	.add-student-container .ant-table-wrapper {
	    flex-grow: 1; /* Allow table wrapper to fill space */
	    overflow: hidden; /* Hide wrapper overflow */
	}
	.add-student-container .ant-spin-nested-loading,
	.add-student-container .ant-spin-container,
	.add-student-container .ant-table,
	.add-student-container .ant-table-container,
	.add-student-container .ant-table-body {
	    height: 100%; /* Make table elements fill height */
	    overflow-y: auto !important; /* Ensure table body is scrollable */
	}
	.add-student-container .ant-table-body {
	     overflow-y: auto !important; /* Force scroll */
	}
	
	
	.student-selection-buttons {
	  display: flex;
	  justify-content: flex-end;
	  margin-top: auto; /* Push to bottom */
	  padding-top: 16px;
	  border-top: 1px solid #f0f0f0;
	  flex-shrink: 0;
	  gap: 8px;
	}
	
	/* Style disabled rows in available table */
	:deep(.ant-table-row-disabled) td {
	    color: #bfbfbf !important;
	    cursor: not-allowed;
	}
	:deep(.ant-table-row-disabled) .ant-checkbox-wrapper {
	    cursor: not-allowed;
	}
	:deep(.ant-table-row-disabled) .ant-checkbox-inner {
	    background-color: #f5f5f5 !important;
	    border-color: #d9d9d9 !important;
	}
	.training-list {
	  margin-bottom: 20px;
	}
	
	.training-item {
	  position: relative;
	  padding: 15px;
	  border-bottom: 1px solid #f0f0f0;
	  background-color: #fff;
	  transition: all 0.3s;
	}
	
	.training-item:hover {
	  background-color: #f5f5f5;
	}
	.training-courses-container {
	  margin-bottom: 24px;
	}
	.mandatory-tag {
	  position: absolute;
	  top: 15px;
	  left: 15px;
	  background-color: #e6f7ff;
	  color: #1890ff;
	  padding: 0 6px;
	  font-size: 12px;
	  border-radius: 4px;
	}
	
	.course-status {
	  position: absolute;
	  top: 15px;
	  left: 70px;
	  padding: 0 6px;
	  font-size: 12px;
	  border-radius: 4px;
	}
	
	.learning-status {
	  background-color: #e6f7ff;
	  color: #1890ff;
	}
	
	.makeup-status {
	  background-color: #fffbe6;
	  color: #faad14;
	}
	
	.completed-status {
	  background-color: #f6ffed;
	  color: #52c41a;
	}
	
	.unpublished-status {
	  background-color: #f5f5f5;
	  color: #999999;
	}
	.course-time, .course-student-stats, .course-time-remaining, .course-student-progress {
	  font-size: 14px;
	  color: #888;
	  margin-bottom: 5px;
	}

	.course-student-progress {
	  color: #1890ff;
	  font-weight: 500;
	}
	.course-actions {
	  margin-top: 10px;
	}
</style>
