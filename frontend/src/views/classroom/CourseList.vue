<template>
	<!-- 功能按钮区 - 仅教师/管理员可见，历史课堂不显示 -->
	<div class="function-buttons" v-if="!isHistoricalClassroom && isTeacherView">
	  <a-button type="primary" @click="showAddChapterModal = true">添加章节</a-button>
	  <a-dropdown>
	    <template #overlay>
	      <a-menu @click="handleAddCourseMenuClick">
	        <a-menu-item key="timetable">按课表添加课程</a-menu-item>
	        <a-menu-item key="practice">添加实践课程</a-menu-item>
	        <a-menu-item key="training">添加实训项目</a-menu-item>
	      </a-menu>
	    </template>
	    <a-button>
	      添加课程 <DownOutlined />
	    </a-button>
	  </a-dropdown>
	  <a-button @click="toggleSortMode">{{ isSortMode ? '完成排序' : '调整排序' }}</a-button>
	  <a-button @click="$emit('refresh-trainings')" style="margin-left: 10px">刷新实训</a-button>
	  <!--<div class="search-box">
	    <a-input placeholder="输入关键字进行搜索" suffix="🔍" />
	  </div>-->
	</div>
	
	<!-- 课程状态标签 - 根据角色和课堂状态显示不同选项 -->
	<div class="status-tabs">
	  <div class="status-tab" :class="{ active: currentStatus === 'all' }" @click="setCourseFilter('all')">全部课程 {{ totalCourseCount }}</div>

	  <!-- 学生端 - 历史课堂：全部课程/已完成/未完成 -->
	  <template v-if="isStudentView && isHistoricalClassroom">
	    <div class="status-tab" :class="{ active: currentStatus === 'completed' }" @click="setCourseFilter('completed')">已完成 {{ studentCompletedCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'not_completed' }" @click="setCourseFilter('not_completed')">未完成 {{ studentNotCompletedCount }}</div>
	  </template>

	  <!-- 学生端 - 正在上课：全部课程/未开始/学习中/待补交/已完成 -->
	  <template v-else-if="isStudentView && !isHistoricalClassroom">
	    <div class="status-tab" :class="{ active: currentStatus === 'not_started' }" @click="setCourseFilter('not_started')">未开始 {{ notStartedCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'learning' }" @click="setCourseFilter('learning')">学习中 {{ learningCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'makeup' }" @click="setCourseFilter('makeup')">待补交 {{ pendingMakeupCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'completed' }" @click="setCourseFilter('completed')">已完成 {{ completedCourseCount }}</div>
	  </template>

	  <!-- 教师端 - 历史课堂：全部课程/未发布/已结束 -->
	  <template v-else-if="isTeacherView && isHistoricalClassroom">
	    <div class="status-tab" :class="{ active: currentStatus === 'unpublished' }" @click="setCourseFilter('unpublished')">未发布 {{ unpublishedCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'ended' }" @click="setCourseFilter('ended')">已结束 {{ endedCourseCount }}</div>
	  </template>

	  <!-- 教师端 - 正在上课：全部课程/未发布/学习中/补交中/已完成 -->
	  <template v-else>
	    <div class="status-tab" :class="{ active: currentStatus === 'unpublished' }" @click="setCourseFilter('unpublished')">
	      未发布 {{ unpublishedCourseCount }}
	      <template v-if="currentStatus === 'unpublished'">
	        <a-button type="link" class="publish-all-btn" @click.stop="openPublishAllDialog">全部发布</a-button>
	        <a-button type="link" class="delete-all-btn" danger @click.stop="openDeleteAllDialog">全部删除</a-button>
	      </template>
	    </div>
	    <div class="status-tab" :class="{ active: currentStatus === 'learning' }" @click="setCourseFilter('learning')">学习中 {{ learningCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'makeup' }" @click="setCourseFilter('makeup')">补交中 {{ makeupCourseCount }}</div>
	    <div class="status-tab" :class="{ active: currentStatus === 'completed' }" @click="setCourseFilter('completed')">已完成 {{ completedCourseCount }}</div>
	  </template>
	</div>

	<!-- 学生端班级进度统计行 -->
	<div v-if="isStudentView" class="classroom-stats-row">
	  <span class="stats-item">
	    <span class="stats-label">未开始</span>
	    <span class="stats-value not-started">{{ notStartedCourseCount }}人</span>
	  </span>
	  <span class="stats-divider">|</span>
	  <span class="stats-item">
	    <span class="stats-label">进行中</span>
	    <span class="stats-value learning">{{ learningCourseCount }}人</span>
	  </span>
	  <span class="stats-divider">|</span>
	  <span class="stats-item">
	    <span class="stats-label">待补交</span>
	    <span class="stats-value makeup">{{ pendingMakeupCourseCount }}人</span>
	  </span>
	  <span class="stats-divider">|</span>
	  <span class="stats-item">
	    <span class="stats-label">已完成</span>
	    <span class="stats-value completed">{{ completedCourseCount }}人</span>
	  </span>
	  <span class="stats-divider">|</span>
	  <span class="stats-item total">
	    <span class="stats-label">全部课程</span>
	    <span class="stats-value">{{ totalCourseCount }}个</span>
	  </span>
	</div>

	<!-- 排序模式 -->
	<div v-if="isSortMode" class="sortable-content">
	  <div class="sort-hint">
	    <p>拖拽调整章节和课程顺序，完成后点击"完成排序"保存</p>
	  </div>
	  <draggable
	    v-model="sortableCourses"
	    group="courses"
	    @end="onDragEnd"
	    handle=".drag-handle"
	    item-key="id"
	  >
	    <template #item="{ element: item }">
	      <div :class="item.type === 'chapter' ? 'sortable-chapter-item' : 'sortable-course-item'">
	        <div class="drag-handle">⋮⋮</div>
	        <div class="item-content">
	          <span class="item-type" :class="item.type === 'chapter' ? 'chapter-type' : (item.course_type === 'training' ? 'training-type' : 'practice-type')">
	            {{ item.type === 'chapter' ? '章节' : (item.course_type === 'training' ? '实训' : '实践') }}
	          </span>
	          <span class="item-title">{{ item.type === 'chapter' ? item.name : (item.name_override || item.title || item.name) }}</span>
	        </div>
	      </div>
	    </template>
	  </draggable>
	  <div v-if="sortableCourses.length === 0" class="empty-sort-list">
	    <p>暂无可排序的内容</p>
	  </div>
	</div>

	<!-- 正常显示模式 -->
	<div v-else>
	  <!-- 章节模式：带折叠功能 -->
	  <template v-if="isChapterFormat && chaptersData.length > 0">
	    <a-collapse v-model:activeKey="expandedChapters" class="chapter-collapse">
	      <a-collapse-panel
	        v-for="(chapter, chapterIndex) in chaptersData"
	        :key="chapter.id"
	        :header="chapter.name.match(/^第[一二三四五六七八九十\d]+章/) ? chapter.name : getChapterNumber(chapterIndex) + ' ' + chapter.name"
	      >
	        <template #extra>
	          <div class="chapter-extra" @click.stop>
	            <span class="chapter-course-count">{{ chapter.courses?.length || 0 }}个课程</span>
	            <!-- 历史课堂不显示章节操作按钮 -->
	            <template v-if="!isHistoricalClassroom">
	              <a-button
	                v-if="hasUnpublishedCoursesInChapter(chapter)"
	                type="link"
	                size="small"
	                @click.stop="handlePublishChapter({ chapterId: chapter.id, chapterName: chapter.name })"
	              >
	                批量发布
	              </a-button>
	              <chapter-dropdown
	                :id="chapter.id"
	                :name="chapter.name"
	                :hasCourses="chapter.courses && chapter.courses.length > 0"
	                :hasUnpublishedCourses="hasUnpublishedCoursesInChapter(chapter)"
	                @rename="handleChapterRename"
	                @delete="handleDeleteChapter"
	                @add-course="openAddCourseToChapter"
	                @publish-all="handlePublishChapter"
	              />
	            </template>
	          </div>
	        </template>
	        <!-- 章节内课程列表 -->
	        <div v-if="chapter.courses && chapter.courses.length > 0">
	          <div v-for="(course, courseIndex) in filterCoursesByStatus(chapter.courses)" :key="course.id" class="course-item">
	            <div class="course-title">
	              <span class="course-number">{{ courseIndex + 1 }}.</span>
	              <span class="course-name-link" :class="{ 'clickable': course.type !== 'training' }" @click="navigateToCourseDetail(course)">
	                {{ course.name_override || course.course_name || course.title || course.name }}
	              </span>
	              <div class="mandatory-tag" v-if="course.is_required">必修</div>
	              <div class="course-status" :class="getStatusClass(course.status)">{{ getStatusText(course.status) }}</div>
	              <div v-if="isAllCompleted && isAllCompleted(course)" class="all-completed-flag">
	                <img src="/images/red-flag.svg" alt="全员完成" class="flag-icon" />
	                <span style="font-size: 12px; color: #f5222d; font-weight: 500;">全员完成</span>
	              </div>
	            </div>
	            <div v-if="course.type === 'training'" class="training-extra-info">
	              <div class="training-industry">所属行业：{{ course.direction || '未设置' }}</div>
	              <div class="training-intro">实训简介：{{ course.description || '暂无简介' }}</div>
	            </div>
	            <div class="course-time">创建时间：{{ formatDate(course.created_at) }}</div>
	            <!-- 教师端统计信息 -->
	            <template v-if="isTeacherView">
	              <!-- 已完成状态：只显示小旗图标和已完成人数 -->
	              <div class="course-student-stats" v-if="course.status === 'completed'">
	                <span class="completed-all-text">已完成 {{ course.completedCount || props.studentCount }}人</span>
	              </div>
	              <!-- 学习中/补交中状态：显示未开始 | 进行中 | 已完成 -->
	              <div class="course-student-stats" v-else-if="course.status !== 'unpublished'">
	                <span v-if="course.status === 'makeup'">补交中 {{ course.makeupCount || 0 }}人</span>
	                <span v-if="course.status === 'makeup'">|</span>
	                <span>未开始 {{ course.notStartedCount || 0 }}人</span>
	                <span>|</span>
	                <span>进行中 {{ course.learningCount || 0 }}人</span>
	                <span>|</span>
	                <span>已完成 {{ course.completedCount || 0 }}人</span>
	              </div>
	            </template>
	            <!-- 学生端进度信息 -->
	            <div class="course-student-progress" v-if="isStudentView">
	              <span>进度：{{ course.completed_task_count || 0 }}/{{ course.task_count || 0 }} 关卡</span>
	            </div>
	            <div class="course-time-remaining"
              :class="{ urgent: isTimeUrgent(course.status === 'makeup' || course.status === 'pending_makeup' ? props.classroomEndDate : course.deadline_at) }"
              v-if="course.status === 'learning' || course.status === 'in_progress' || course.status === 'makeup' || course.status === 'pending_makeup'">
              {{ getRemainingTimeLabel(course.status) }}：{{ calculateRemainingTime(course.status === 'makeup' || course.status === 'pending_makeup' ? props.classroomEndDate : course.deadline_at) }}
            </div>
	            <div class="course-actions">
	              <a-button size="small" v-if="course.status !== 'unpublished' && isTeacherView" @click="handleViewGrades(course)">查看成绩</a-button>
	              <!-- 历史课堂不显示发布和更多操作，学生不显示 -->
	              <template v-if="!isHistoricalClassroom && isTeacherView">
	                <a-button size="small" type="primary" v-if="course.status === 'unpublished'" @click="openPublishDialog(course.id)">发 布</a-button>
	                <course-dropdown
	                  :course="course"
	                  :chapterId="chapter.id"
	                  @edit="handleCourseEdit"
	                  @delete="handleCourseDelete"
	                  @publish="handleCoursePublish"
	                  @view-students="handleViewStudents"
	                />
	              </template>
	            </div>
	          </div>
	        </div>
	        <a-empty v-else description="暂无课程" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
	      </a-collapse-panel>
	    </a-collapse>
	  </template>

	  <!-- 扁平模式：无章节结构 -->
	  <template v-else>
	    <div v-for="(course, courseIndex) in localCourses" :key="course.id" class="course-item">
	      <div class="course-title">
	        <span class="course-number">{{ courseIndex + 1 }}.</span>
	        <span class="course-name-link" :class="{ 'clickable': course.type !== 'training' }" @click="navigateToCourseDetail(course)">
	          {{ course.name_override || course.course_name || course.title || course.name }}
	        </span>
	        <div class="mandatory-tag" v-if="course.is_required">必修</div>
	        <div class="course-status" :class="getStatusClass(course.status)">{{ getStatusText(course.status) }}</div>
	        <div v-if="isAllCompleted && isAllCompleted(course)" class="all-completed-flag">
	          <img src="/images/red-flag.svg" alt="全员完成" class="flag-icon" />
	          <span style="font-size: 12px; color: #f5222d; font-weight: 500;">全员完成</span>
	        </div>
	      </div>
	      <div v-if="course.type === 'training'" class="training-extra-info">
	        <div class="training-industry">所属行业：{{ course.direction || '未设置' }}</div>
	        <div class="training-intro">实训简介：{{ course.description || '暂无简介' }}</div>
	      </div>
	      <div class="course-time">创建时间：{{ formatDate(course.created_at) }}</div>
	      <!-- 教师端统计信息 -->
	      <template v-if="isTeacherView">
	        <!-- 已完成状态：只显示小旗图标和已完成人数 -->
	        <div class="course-student-stats" v-if="course.status === 'completed'">
	          <span class="completed-all-text">已完成 {{ course.completedCount || props.studentCount }}人</span>
	        </div>
	        <!-- 学习中/补交中状态：显示未开始 | 进行中 | 已完成 -->
	        <div class="course-student-stats" v-else-if="course.status !== 'unpublished'">
	          <span v-if="course.status === 'makeup'">补交中 {{ course.makeupCount || 0 }}人</span>
	          <span v-if="course.status === 'makeup'">|</span>
	          <span>未开始 {{ course.notStartedCount || 0 }}人</span>
	          <span>|</span>
	          <span>进行中 {{ course.learningCount || 0 }}人</span>
	          <span>|</span>
	          <span>已完成 {{ course.completedCount || 0 }}人</span>
	        </div>
	      </template>
	      <!-- 学生端进度信息 -->
	      <div class="course-student-progress" v-if="isStudentView">
	        <span>进度：{{ course.completed_task_count || 0 }}/{{ course.task_count || 0 }} 关卡</span>
	      </div>
	      <div class="course-time-remaining"
              :class="{ urgent: isTimeUrgent(course.status === 'makeup' || course.status === 'pending_makeup' ? props.classroomEndDate : course.deadline_at) }"
              v-if="course.status === 'learning' || course.status === 'in_progress' || course.status === 'makeup' || course.status === 'pending_makeup'">
              {{ getRemainingTimeLabel(course.status) }}：{{ calculateRemainingTime(course.status === 'makeup' || course.status === 'pending_makeup' ? props.classroomEndDate : course.deadline_at) }}
            </div>
	      <div class="course-actions">
	        <a-button size="small" v-if="course.status !== 'unpublished' && isTeacherView" @click="handleViewGrades(course)">查看成绩</a-button>
	        <!-- 历史课堂不显示发布和更多操作，学生不显示 -->
	        <template v-if="!isHistoricalClassroom && isTeacherView">
	          <a-button size="small" type="primary" v-if="course.status === 'unpublished'" @click="openPublishDialog(course.id)">发 布</a-button>
	          <course-dropdown
	            :course="course"
	            :chapterId="chapterId"
	            @edit="handleCourseEdit"
	            @delete="handleCourseDelete"
	            @publish="handleCoursePublish"
	            @view-students="handleViewStudents"
	          />
	        </template>
	      </div>
	    </div>
	  </template>
	</div>
      <!-- Modals -->
      <a-modal
        v-model:open="showAddChapterModal"
        title="添加章节"
        @ok="handleAddChapter"
        @cancel="showAddChapterModal = false"
      >
        <a-form layout="vertical">
          <a-form-item label="章节名称" required>
            <a-input v-model:value="chapterNameInput" placeholder="请输入章节名称" />
          </a-form-item>
        </a-form>
      </a-modal>
	  <!-- 添加实践课程对话框 -->
	  <add-practice-course-dialog ref="addPracticeCourseDialogRef" @success="handleChapterRename" :chapterId="chapterId" :classroomId="props.classroomId" :nowcourses="nowcourses" />
	  
	  <!-- 按课表添加课程对话框 -->
	  <add-course-by-timetable-dialog ref="addCourseByTimetableDialogRef" @success="handleChapterRename" :classroomId="props.classroomId" :chapterId="chapterId" />
	  
	  <!-- 课程发布设置对话框 -->
	  <a-modal
	    v-model:open="publishDialogVisible"
	    :title="publishDialogTitle"
	    :width="500"
	    @cancel="cancelPublish"
	    :maskClosable="false"
	    :destroyOnClose="true"
	    class="publish-dialog"
	    :footer="null"
	  >
	    <div class="publish-dialog-content">
	      <a-form :model="publishForm" layout="vertical">
	        <a-form-item label="发布时间" required>
	          <div class="date-input-wrapper">
	            <a-input
	              :value="publishForm.start_date"
	              disabled
	              class="date-input"
	            >
	              <template #prefix>
	                <CalendarOutlined />
	              </template>
	            </a-input>
	          </div>
	          <div class="form-item-help">学生能够开始学习并提交作业的时间</div>
	        </a-form-item>
	        
	        <a-form-item label="截止时间" required>
	          <div class="date-input-wrapper">
	            <a-date-picker 
	              v-model:value="publishForm.end_date" 
	              :disabled-date="disabledDate"
	              style="width: 100%"
	              format="YYYY-MM-DD"
	              value-format="YYYY-MM-DD"
	              class="date-input"
	            >
	              <template #suffixIcon>
	                <CalendarOutlined />
	              </template>
	            </a-date-picker>
	          </div>
	          <div class="form-item-help">学生按时提交作业的截止时间，此时间后提交的作业为补交作业</div>
	        </a-form-item>
	  
	        <a-form-item label="课程属性" required>
	          <div class="course-type-wrapper">
	            <a-radio-group v-model:value="publishForm.is_required">
	              <a-radio :value="1">必修</a-radio>
	              <a-radio :value="0">拓展</a-radio>
	            </a-radio-group>
	          </div>
	          <div class="form-item-help">拓展课程为专业技能拓展，闯关成绩不计入本课堂总分</div>
	        </a-form-item>
	      </a-form>
	    </div>
	  
	    <div class="modal-footer">
	      <a-button @click="cancelPublish">取消</a-button>
	      <a-button type="primary" :loading="publishLoading" @click="confirmPublish">确定</a-button>
	    </div>
	  </a-modal>
	  
	  <!-- 添加实训项目对话框 -->
	  <add-training-course-dialog
	    ref="addTrainingCourseDialogRef"
	    :classroom-id="props.classroomId"
	    :existing-training-ids="existingTrainingIds"
    @success="handleTrainingAddSuccess"
  />

  <!-- 删除章节确认对话框 -->
  <a-modal
    v-model:open="showDeleteChapterModal"
    title="确认删除"
    @ok="confirmDeleteChapter"
    @cancel="cancelDelete"
    :ok-button-props="{ danger: true }"
    ok-text="删除"
    cancel-text="取消"
  >
    <p>确定要删除章节 "{{ chapterToDelete }}" 吗？</p>
    <p style="color: #ff4d4f; margin-top: 8px;">⚠️ 删除章节将同时删除其下的所有课程，此操作不可恢复！</p>
  </a-modal>
  </template>
  
  <script setup lang="ts">
  import { ref, computed, watch, reactive } from 'vue';
  import { useRouter } from 'vue-router';
  import { message, Modal, Empty } from 'ant-design-vue';
  import { useLoading, useMultipleLoading } from '@/composables/useLoading';
  import {
    ReadOutlined, PlusOutlined, DownOutlined, TableOutlined, CodeOutlined, BookOutlined,
    CalendarOutlined, ClockCircleOutlined, FlagOutlined, MenuOutlined
  } from '@ant-design/icons-vue';
  import dayjs, { Dayjs } from 'dayjs';
  import { addClassRoomChapter,pushClassRoomPractice, deleteClassRoomPracticeBatch } from '@/api/classrooms';
  import type { CourseItem, CourseStatus } from '@/types/classroom'; // Adjust path as needed
  import AddPracticeCourseDialog from '@/components/classroom/AddPracticeCourseDialog.vue';
  import AddCourseByTimetableDialog from '@/components/classroom/AddCourseByTimetableDialog.vue';
  import AddTrainingCourseDialog from '@/components/classroom/AddTrainingCourseDialog.vue';
  import ChapterDropdown from '../../components/classroom/ChapterDropdown.vue';
  import CourseDropdown from '../../components/classroom/CourseDropdown.vue';
  import draggable from 'vuedraggable';
  
  interface Props {
    courses: CourseItem[] | ChapterItem[];
    classroomId: string;
    classroomStatus: string;
    classroomEndDate?: string; // Pass classroom end date for validation/defaults
    studentCount: number;
    userRole?: string; // 用户角色：teacher/student/admin
  }
  
  const props = defineProps<Props>();
  const emit = defineEmits(['navigate-to-course-detail', 'view-grades', 'update-courses']); // Event to notify parent of changes

  const router = useRouter();

  // 导航到课程详情页面
  const navigateToCourseDetail = (course: any) => {
    // 实训课程不导航到课程详情
    if (course.type === 'training') {
      return;
    }
    const courseId = course.id || course.original_course_id;
    if (courseId) {
      router.push(`/classroom/${props.classroomId}/course/${courseId}`);
    }
  };
  
  // const classroomStore = useClassroomStore(); // Uncomment if store actions are used directly
  
  // --- Local State ---
  const currentCourseFilter = ref<string>('all');
  const showAddChapterModal = ref(false);
  const showDeleteChapterModal = ref(false);
  const addPracticeCourseDialogRef = ref();
  const addCourseByTimetableDialogRef = ref();

  // 检查数据格式：如果是章节数组，返回true
  const isChapterFormat = computed(() => {
    return Array.isArray(props.courses) &&
           props.courses.length > 0 &&
           props.courses[0] &&
           typeof props.courses[0] === 'object' &&
           'courses' in props.courses[0];
  });

  // 统一的课程数据处理
  const normalizedCourses = computed(() => {
    if (isChapterFormat.value) {
      // 章节格式：展平为课程数组
      const result = (props.courses as ChapterItem[]).reduce((allCourses: CourseItem[], chapter) => {
        return allCourses.concat(chapter.courses || []);
      }, []);
      return result;
    } else {
      // 直接课程数组格式
      const result = props.courses as CourseItem[];
      return result;
    }
  });
  const addTrainingCourseDialogRef = ref();
  const nowcourses = ref([]);
  const existingTrainingIds = ref<number[]>([]);
  const isSortMode = ref(false);  // 是否处于排序模式
  const sortableCourses = ref<any[]>([]); // 排序模式下的扁平化课程列表

  // 章节折叠状态：默认全部展开
  const expandedChapters = ref<string[]>([]);

  // 章节数据
  const chaptersData = computed(() => {
    if (isChapterFormat.value) {
      return props.courses as any[];
    }
    return [];
  });

  // 初始化展开所有章节
  watch(chaptersData, (chapters) => {
    if (chapters && chapters.length > 0) {
      expandedChapters.value = chapters.map((ch: any) => ch.id);
    }
  }, { immediate: true });

  const chapterNameInput = ref(''); // For adding chapter
  const chapterToDelete = ref<string | null>(null);
  
  
  const chapterId= ref('0');
  // 课程发布相关变量
  const publishDialogVisible = ref(false);
  const publishDialogTitle = ref('发布设置');
  const publishMode = ref<'single' | 'chapter' | 'all'>('single');
  const publishLoading = ref(false);
  
  // Loading状态
  const { loading: coursesLoading, withLoading: withCoursesLoading } = useLoading();
  const { loading: addChapterLoading, withLoading: withAddChapterLoading } = useLoading();
  
  // 发布表单数据
  const publishForm = reactive({
	id:'',
	start_date:'',
    end_date: '', // 使用字符串类型，适配value-format="YYYY-MM-DD"
    is_required: 1,
	status:'learning',
	chapterId: '',
	chapterName: ''
  });
  // Store raw courses data
  const rawCourses = ref([]);

  // --- Watchers ---
  // Update raw courses when prop changes
  watch(() => props.courses, (newCourses) => {
    rawCourses.value = newCourses || [];
  	nowcourses.value=[];

  	// 处理不同数据格式
  	if (Array.isArray(newCourses) && newCourses.length > 0) {
  	  if (isChapterFormat.value) {
  	    // 章节格式
  	    newCourses.forEach((item: any)=>{
  	      if (item.courses && Array.isArray(item.courses)) {
  	        item.courses.forEach((item2: any)=>{
  	          nowcourses.value.push(item2.original_course_id)
  	        });
  	      }
  	    })
  	  } else {
  	    // 直接课程格式
  	    newCourses.forEach((item: any)=>{
  	      nowcourses.value.push(item.original_course_id)
  	    })
  	  }
  	}
  }, { immediate: true, deep: true });

  // Computed localCourses with filtering
  const localCourses = computed(() => {
    if (currentCourseFilter.value === 'all') {
      return normalizedCourses.value;
    }

    // 历史课堂特殊筛选：已结束 = 非未发布的所有课程
    if (currentCourseFilter.value === 'ended') {
      return normalizedCourses.value.filter(course => course.status !== 'unpublished');
    }

    // 学生端特殊筛选：未完成 = 非已完成状态的课程
    if (currentCourseFilter.value === 'not_completed') {
      return normalizedCourses.value.filter(course =>
        course.status !== 'completed' &&
        course.status !== 'on_time_completed' &&
        course.status !== 'late_completed'
      );
    }

    // Filter courses by status
    return normalizedCourses.value.filter(course => course.status === currentCourseFilter.value);
  });
  
  // --- Computed Properties ---
  const practiceCourses = computed(() => {
    return normalizedCourses.value.filter(course => course.type === 'practice');
  });

  const trainingCourses = computed(() => {
    return normalizedCourses.value.filter(course => course.type === 'training');
  });

  // Status filtering computed properties
  const currentStatus = computed(() => currentCourseFilter.value);

  const totalCourseCount = computed(() => {
    return normalizedCourses.value.length;
  });

  const learningCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => calculateStudentStatus(course) === 'learning').length;
  });

  const makeupCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => calculateStudentStatus(course) === 'makeup').length;
  });

  const completedCourseCount = computed(() => {
    return normalizedCourses.value.filter(course =>
      calculateStudentStatus(course) === 'completed' ||
      calculateStudentStatus(course) === 'on_time_completed' ||
      calculateStudentStatus(course) === 'late_completed'
    ).length;
  });

  const unpublishedCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => course.status === 'unpublished').length;
  });

  // 历史课堂判断
  const isHistoricalClassroom = computed(() => {
    return props.classroomStatus === 'ENDED';
  });

  // 是否是学生视图
  const isStudentView = computed(() => {
    return props.userRole === 'student';
  });

  // 是否是教师/管理员视图
  const isTeacherView = computed(() => {
    return props.userRole === 'teacher' || props.userRole === 'admin';
  });

  // 已结束课程数量（历史课堂使用：除未发布外的所有课程）
  const endedCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => course.status !== 'unpublished').length;
  });

  // 学生端状态计数
  // 未开始课程数量（学生端）
  const notStartedCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => calculateStudentStatus(course) === 'not_started').length;
  });

  // 待补交课程数量（学生端 - 相当于教师端的补交中）
  const pendingMakeupCourseCount = computed(() => {
    return normalizedCourses.value.filter(course => calculateStudentStatus(course) === 'makeup').length;
  });

  // 学生端历史课堂：已完成课程数（按时完成 + 补交完成）
  const studentCompletedCount = computed(() => {
    return normalizedCourses.value.filter(course =>
      calculateStudentStatus(course) === 'completed' ||
      calculateStudentStatus(course) === 'on_time_completed' ||
      calculateStudentStatus(course) === 'late_completed'
    ).length;
  });

  // 学生端历史课堂：未完成课程数
  const studentNotCompletedCount = computed(() => {
    return normalizedCourses.value.filter(course =>
      calculateStudentStatus(course) !== 'completed' &&
      calculateStudentStatus(course) !== 'on_time_completed' &&
      calculateStudentStatus(course) !== 'late_completed'
    ).length;
  });


  // --- 学生状态计算辅助函数 ---
  // 根据学生学习进度数据计算状态（用于学生视图）
  // 状态判断逻辑：
  // - 未开始: lastAccessTime 为空
  // - 学中: 有 lastAccessTime && progress < 100% && now <= deadline
  // - 待补交: progress < 100% && deadline < now <= classroomEndTime
  // - 已完成: progress == 100%
  const calculateStudentStatus = (course: any): string => {
    // 如果是教师视图或课程没有学习进度数据，返回原始状态
    if (!isStudentView.value) {
      return course.status || 'not_started';
    }

    // 获取学习进度数据
    const lastAccessTime = course.lastAccessTime || course.last_access_time;
    const progress = course.progress || 0;
    const deadline = course.deadline || course.end_date;
    const classroomEndTime = course.classroomEndTime || course.classroom_end_time;
    const now = new Date();

    // 判断截止时间
    const deadlineDate = deadline ? new Date(deadline) : null;
    const classroomEndDate = classroomEndTime ? new Date(classroomEndTime) : null;

    // 进度100% = 已完成
    if (progress >= 100) {
      // 判断是按时完成还是补交完成
      if (deadlineDate && now <= deadlineDate) {
        return 'on_time_completed';
      } else {
        return 'late_completed';
      }
    }

    // 进度<100%
    // 未开始：没有访问记录
    if (!lastAccessTime) {
      return 'not_started';
    }

    // 学中：有访问记录且在截止时间内
    if (deadlineDate && now <= deadlineDate) {
      return 'learning';
    }

    // 待补交：超过截止时间但未超过课堂结束时间
    if (classroomEndDate && now <= classroomEndDate) {
      return 'makeup';
    }

    // 已过期（超过课堂结束时间）
    return 'makeup';
  };

  // --- Methods -->
  
  // Utility Functions (can be moved to a separate utils file if preferred)
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '';
    return dayjs(dateStr).format('YYYY-MM-DD'); // Include time for clarity
  };
  
  const getCourseStatusText = (status: CourseStatus) => {
    switch (status) {
      case 'unpublished': return '未发布';
      case 'learning': return '学习中';
      case 'makeup': return '补交中';
      case 'completed': return '已完成';
      default: return '未知状态';
    }
  };
  
  const getCourseStatusClass = (status: CourseStatus) => {
    switch (status) {
      case 'unpublished': return 'status-unpublished';
      case 'learning': return 'status-learning';
      case 'makeup': return 'status-makeup';
      case 'completed': return 'status-completed';
      default: return '';
    }
  };
  // 获取课程状态对应的类名
  const getStatusClass = (status: string) => {
    // 统一转换为小写进行比较，空值默认为未开始
    const normalizedStatus = (status || 'not_started').toLowerCase();

    // 学生端样式
    if (isStudentView.value) {
      switch (normalizedStatus) {
        case 'not_started':
        case '':
        case 'undefined':
        case 'null':
          return 'not-started-status';
        case 'learning':
        case 'in_progress':
          return 'learning-status';
        case 'makeup':
        case 'pending_makeup':
          return 'makeup-status';
        case 'completed':
        case 'on_time_completed':
          return 'completed-status';
        case 'late_completed':
          return 'late-completed-status';
        default:
          return 'not-started-status';
      }
    }

    // 教师端样式
    switch (normalizedStatus) {
      case 'not_started':
        return 'not-started-status';
      case 'learning':
      case 'in_progress':
        return 'learning-status';
      case 'makeup':
      case 'pending_makeup':
        return 'makeup-status';
      case 'completed':
      case 'on_time_completed':
        return 'completed-status';
      case 'late_completed':
        return 'late-completed-status';
      case 'unpublished':
      case '':
      case 'undefined':
      case 'null':
        return 'unpublished-status';
      default:
        return '';
    }
  };
  
  // 获取课程状态文本
  const getStatusText = (status: string) => {
    // 统一转换为小写进行比较，空值默认为未开始
    const normalizedStatus = (status || 'not_started').toLowerCase();

    // 学生端特有状态
    if (isStudentView.value) {
      switch (normalizedStatus) {
        case 'not_started':
        case '':
        case 'undefined':
        case 'null':
          return '未开始';
        case 'learning':
        case 'in_progress':
          return '学习中';
        case 'makeup':
        case 'pending_makeup':
          return '待补交';
        case 'completed':
        case 'on_time_completed':
          return '按时完成';
        case 'late_completed':
          return '补交完成';
        default:
          // 学生端未知状态默认显示为未开始
          return '未开始';
      }
    }

    // 教师端状态
    switch (normalizedStatus) {
      case 'not_started':
        return '未开始';
      case 'learning':
        return '学习中';
      case 'makeup':
        return '补交中';
      case 'completed':
        return '已完成';
      case 'unpublished':
      case '':
      case 'undefined':
      case 'null':
        return '未发布';
      default:
        return '未知状态';
    }
  };
  
  const disabledDate = (current: Dayjs) => {
    // Cannot select days before today
    let isDisabled = current && current < dayjs().startOf('day');
    // Cannot select days after classroom end date (if provided)
    if (!isDisabled && props.classroomEndDate) {
        isDisabled = current > dayjs(props.classroomEndDate).endOf('day');
    }
    return isDisabled;
  };
  
  const calculateRemainingTime = (endDateStr?: string): string => {
      if (!endDateStr) return 'N/A';
      const end = dayjs(endDateStr);
      const now = dayjs();
      const diff = end.diff(now, 'minute');
  
      if (diff <= 0) {
          return '已到期';
      }
  
      const days = Math.floor(diff / (24 * 60));
      const hours = Math.floor((diff % (24 * 60)) / 60);
      const minutes = diff % 60;
  
      let result = '';
      if (days > 0) result += `${days}天`;
      if (hours > 0) result += `${hours}小时`;
      if (minutes > 0 || (days === 0 && hours === 0)) result += `${minutes}分`; // Show minutes if less than an hour or exactly 0
  
      return result || '即将到期';
  };

  // 获取剩余时间标签（根据角色和状态）
  const getRemainingTimeLabel = (status: string): string => {
    const normalizedStatus = (status || '').toLowerCase();
    const isMakeup = normalizedStatus === 'makeup' || normalizedStatus === 'pending_makeup';

    if (isStudentView.value) {
      return isMakeup ? '补交剩余时间' : '学习剩余时间';
    }
    return isMakeup ? '补交截止时间' : '截止时间';
  };

  // 判断剩余时间是否紧急（小于1小时）
  const isTimeUrgent = (endDateStr?: string): boolean => {
    if (!endDateStr) return false;
    const end = dayjs(endDateStr);
    const now = dayjs();
    const diff = end.diff(now, 'minute');
    // 小于60分钟视为紧急
    return diff > 0 && diff < 60;
  };


  // Course Filtering and Grouping
  const setCourseFilter = (status: string) => {
    currentCourseFilter.value = status;
  };

  const filterCoursesByStatus = (courses: CourseItem[]) => {
    if (currentCourseFilter.value === 'all') return courses;
    // 历史课堂特殊筛选：已结束 = 非未发布的所有课程
    if (currentCourseFilter.value === 'ended') {
      return courses.filter(course => course.status !== 'unpublished');
    }
    return courses.filter(course => course.status === currentCourseFilter.value);
  };
  
  // 查看成绩
  const handleViewGrades = (course: CourseItem) => {
    console.log('[CourseList] 查看成绩:', course);
    emit('view-grades', course);
  };

  // 编辑课程
  const handleCourseEdit = (course: CourseItem) => {
    console.log('[CourseList] 编辑课程:', course);
    // TODO: 实现编辑课程逻辑，或导航到编辑页面
    message.info('编辑功能开发中');
  };

  // 删除课程
  const handleCourseDelete = (course: CourseItem) => {
    console.log('[CourseList] 删除课程:', course);
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除课程 "${course.name_override || course.title || course.name}" 吗？此操作不可恢复！`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      async onOk() {
        try {
          // TODO: 调用删除课程API
          console.log('删除课程:', course.id);
          message.success('课程删除成功');
          emit('update-courses');
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败，请重试');
        }
      }
    });
  };

  // 发布课程
  const handleCoursePublish = (course: CourseItem) => {
    console.log('[CourseList] 发布课程:', course);
    openPublishDialog(course.id);
  };

  // 查看学生
  const handleViewStudents = (course: CourseItem) => {
    console.log('[CourseList] 查看学生:', course);
    // TODO: 实现查看学生逻辑
    message.info('查看学生功能开发中');
  };

  const openPublishDialog = (courseId: string) => {
    publishDialogVisible.value = true;
    publishMode.value = 'single';
    publishDialogTitle.value = '发布设置';
    
    // 设置默认截止时间为7天后
    const defaultEndDate = new Date();
    defaultEndDate.setDate(defaultEndDate.getDate() + 7);
    publishForm.start_date=formatDate(new Date());
    // 如果默认时间超过了课堂截止时间，则使用课堂截止时间
    publishForm.end_date = formatDate(defaultEndDate);
    publishForm.id=courseId;
    // 设置默认必修
    publishForm.is_required =1;
  };

  // 打开全部发布对话框
  const openPublishAllDialog = () => {
    // 获取所有未发布的课程
    const unpublishedCourses = localCourses.value.filter(course => course.status === 'unpublished');
    
    if (unpublishedCourses.length === 0) {
      message.warning('没有未发布的课程');
      return;
    }
    
    publishDialogVisible.value = true;
    publishMode.value = 'all';
    publishDialogTitle.value = `全部发布（${unpublishedCourses.length}个课程）`;
    
    // 设置默认截止时间为7天后
    const defaultEndDate = new Date();
    defaultEndDate.setDate(defaultEndDate.getDate() + 7);
    publishForm.start_date = formatDate(new Date());
    publishForm.end_date = formatDate(defaultEndDate);
    publishForm.is_required = 1;
  };

  // 打开全部删除对话框
  const openDeleteAllDialog = () => {
    // 获取所有未发布的课程
    const unpublishedCourses = normalizedCourses.value.filter(course => course.status === 'unpublished');

    if (unpublishedCourses.length === 0) {
      message.warning('没有未发布的课程');
      return;
    }

    Modal.confirm({
      title: '确认删除',
      content: `确定要删除全部 ${unpublishedCourses.length} 个未发布的课程吗？此操作不可恢复！`,
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      async onOk() {
        try {
          const courseIds = unpublishedCourses.map((c: any) => c.id);
          await deleteClassRoomPracticeBatch({
            classroom_id: parseInt(props.classroomId as string),
            course_ids: courseIds
          });
          message.success(`成功删除 ${unpublishedCourses.length} 个课程`);
          emit('update-courses');
        } catch (error) {
          console.error('删除失败:', error);
          message.error('删除失败，请重试');
        }
      }
    });
  };

  // 处理章节批量发布
  const handlePublishChapter = ({ chapterId, chapterName }: { chapterId: string; chapterName: string }) => {
    // 获取该章节下所有未发布的课程
    const chapter = chaptersData.value.find(ch => ch.id === chapterId);
    if (!chapter || !chapter.courses) return;
    
    const unpublishedCourses = chapter.courses.filter(course => course.status === 'unpublished');
    
    if (unpublishedCourses.length === 0) {
      message.warning('该章节没有未发布的课程');
      return;
    }
    
    publishDialogVisible.value = true;
    publishMode.value = 'chapter';
    publishDialogTitle.value = `发布"${chapterName}"中的${unpublishedCourses.length}个课程`;
    publishForm.chapterId = chapterId;
    publishForm.chapterName = chapterName;
    
    // 设置默认截止时间为7天后
    const defaultEndDate = new Date();
    defaultEndDate.setDate(defaultEndDate.getDate() + 7);
    publishForm.start_date = formatDate(new Date());
    publishForm.end_date = formatDate(defaultEndDate);
    publishForm.is_required = 1;
  };

  // 检查章节是否有未发布课程
  const hasUnpublishedCoursesInChapter = (chapter: any) => {
    return chapter.courses && chapter.courses.some(course => course.status === 'unpublished');
  };
  const cancelPublish = () => {
    publishDialogVisible.value = false;
  };
  const confirmPublish= async () => {
    if (!publishForm.end_date) {
        message.error('请选择截止时间');
        return;
    }
    
    publishLoading.value = true;
    
    try {
      let courseIds: number[] = [];
      
      if (publishMode.value === 'single') {
        // 单个课程发布
        courseIds = [parseInt(publishForm.id)];
      } else if (publishMode.value === 'all') {
        // 全部发布 - 获取所有未发布课程的ID
        courseIds = localCourses.value
          .filter(course => course.status === 'unpublished')
          .map(course => parseInt(course.id));
      } else if (publishMode.value === 'chapter') {
        // 按章节发布 - 获取指定章节下所有未发布课程的ID
        const chapter = chaptersData.value.find(ch => ch.id === publishForm.chapterId);
        if (chapter && chapter.courses) {
          courseIds = chapter.courses
            .filter(course => course.status === 'unpublished')
            .map(course => parseInt(course.id));
        }
      }
      
      // 调用发布API
      await pushClassRoomPractice({
        classroom_id: parseInt(props.classroomId),
        course_ids: courseIds,
        deadline_at: publishForm.end_date,
        is_mandatory: publishForm.is_required === 1
      });
      
      // 关闭对话框
      publishDialogVisible.value = false;
      
      // 显示发布成功消息
      const successMsg = publishMode.value === 'all' 
        ? `成功发布${courseIds.length}个课程` 
        : '课程发布成功';
      message.success(successMsg);
      
      emit('update-courses');
    } catch (error) {
      console.error('发布失败', error);
      message.error('发布失败，请重试');
    } finally {
      publishLoading.value = false;
    }
  };
  // 打开添加课程到指定章节弹框
  const openAddCourseToChapter = (chapterIds: string) => {
    // 记录当前选中的章节，后续添加课程时使用
    //localStorage.setItem('selectedChapterId', chapterId);
    // 打开添加课程弹框
	chapterId.value=chapterIds;
    openAddPracticeCourseDialog();
  };
  // 打开添加实践课程对话框
  const openAddPracticeCourseDialog = () => {
    addPracticeCourseDialogRef.value.open();
  };

  // 处理添加课程菜单点击
  const handleAddCourseMenuClick = ({ key }: { key: string }) => {
    if (key === 'timetable') {
      addCourseByTimetableDialogRef.value.open();
    } else if (key === 'practice') {
      openAddPracticeCourseDialog();
    } else if (key === 'training') {
      // 打开添加实训项目对话框
      addTrainingCourseDialogRef.value.open();
    }
  };
  // Chapter Management
  const handleAddChapter = async () => {
    const name = chapterNameInput.value.trim();
    if (!name) {
      message.error('章节名称不能为空');
      return;
    }
    
    try {
      await withAddChapterLoading(async () => {
        await addClassRoomChapter(props.classroomId, name);
      });
      message.success(`章节 "${name}" 添加成功`);
      chapterNameInput.value = '';
      emit('update-courses');
    } catch (e) {
      console.error('Add chapter failed:', e);
    } finally {
      showAddChapterModal.value = false;
    }
  };
  
  // 处理章节重命名
  const handleChapterRename = (data: {}) => {
    emit('update-courses');
  };
  
  // 处理实训项目添加成功
  const handleTrainingAddSuccess = () => {
    emit('update-courses');
  };
  
  // 切换排序模式
  const toggleSortMode = async () => {
    if (isSortMode.value) {
      // 退出排序模式，保存排序
      await saveCourseOrder();
    } else {
      // 进入排序模式，准备排序数据
      prepareSortableCourses();
    }
    isSortMode.value = !isSortMode.value;
  };

  // 准备排序模式的数据结构
  const prepareSortableCourses = () => {
    sortableCourses.value = [];
    if (isChapterFormat.value) {
      // 章节格式
      props.courses.forEach((chapter: any) => {
        // 添加章节
        sortableCourses.value.push({
          type: 'chapter',
          id: chapter.id,
          name: chapter.name
        });
        // 添加章节下的课程
        chapter.courses.forEach((course: any) => {
          sortableCourses.value.push({
            type: 'course',
            id: course.id,
            name_override: course.name_override,
            title: course.title,
            name: course.name || course.course_name,
            course_type: course.type === 'training' || course.source_type === 'training' ? 'training' : 'practice'
          });
        });
      });
    } else {
      // 直接课程格式 - 为每个课程创建一个默认章节
      sortableCourses.value.push({
        type: 'chapter',
        id: 'default',
        name: '默认章节'
      });
      props.courses.forEach((course: any) => {
        sortableCourses.value.push({
          type: 'course',
          id: course.id,
          name_override: course.name_override,
          title: course.title,
          name: course.name || course.course_name,
          course_type: course.type === 'training' || course.source_type === 'training' ? 'training' : 'practice'
        });
      });
    }
  };

  // 拖拽结束处理
  const onDragEnd = (event: any) => {
    // 防止实训课程被拖拽到章节内部
    const draggedItem = sortableCourses.value[event.newIndex];
    if (draggedItem.type === 'course' && draggedItem.course_type === 'training') {
      // 检查是否被拖拽到章节位置（章节后面第一个课程之前）
      let isDraggedToChapter = false;
      for (let i = 0; i < event.newIndex; i++) {
        const item = sortableCourses.value[i];
        if (item.type === 'chapter') {
          isDraggedToChapter = true;
          break;
        }
      }
      if (isDraggedToChapter) {
        // 恢复原始位置
        sortableCourses.value.splice(event.newIndex, 1);
        sortableCourses.value.splice(event.oldIndex, 0, draggedItem);
        message.warning('实训课程不能放入章节内');
      }
    }
  };
  
  // 保存课程排序
  const saveCourseOrder = async () => {
    try {
      // 从扁平化的sortableCourses重建层级结构
      const newOrder: any[] = [];
      let currentChapter = null;

      sortableCourses.value.forEach((item: any, index: number) => {
        if (item.type === 'chapter') {
          // 如果之前有章节，先保存它
          if (currentChapter) {
            newOrder.push(currentChapter);
          }
          // 开始新章节
          currentChapter = {
            id: item.id,
            name: item.name,
            courses: []
          };
        } else if (item.type === 'course' && currentChapter) {
          // 添加课程到当前章节
          currentChapter.courses.push({
            id: item.id,
            name_override: item.name_override,
            title: item.title,
            type: item.course_type === 'training' ? 'training' : 'practice'
          });
        }
      });

      // 保存最后一个章节
      if (currentChapter) {
        newOrder.push(currentChapter);
      }

      // TODO: 调用后端API保存排序
      console.log('新的排序结构:', newOrder);

      // 临时模拟保存成功
      message.success('排序保存成功');
    } catch (error) {
      console.error('保存排序失败:', error);
      message.error('保存排序失败');
    }
  };
  
  const handleDeleteChapter = (chapter: string) => {
    chapterToDelete.value = chapter;
    showDeleteChapterModal.value = true;
  };

  // 确认删除章节
  const confirmDeleteChapter = async () => {
    if (!chapterToDelete.value) return;

    try {
      // TODO: 调用删除章节API
      console.log('删除章节:', chapterToDelete.value);
      message.success(`章节 "${chapterToDelete.value}" 已删除`);
      showDeleteChapterModal.value = false;
      chapterToDelete.value = null;
      emit('update-courses'); // 通知父组件刷新数据
    } catch (error) {
      message.error('删除章节失败');
    }
  };

  // 取消删除
  const cancelDelete = () => {
    showDeleteChapterModal.value = false;
    chapterToDelete.value = null;
  };
  
  // 获取章节编号
  const getChapterNumber = (index: number) => {
    const chineseNumbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
    return `第${chineseNumbers[index] || (index + 1)}章`;
  };
  
  // 判断是否全员完成
  const isAllCompleted = (course: any) => {
    const totalCount = (course.completedCount || 0) + (course.learningCount || 0) + (course.notStartedCount || 0);
    return totalCount > 0 && course.completedCount === totalCount && course.status === 'completed';
  };
  
  </script>
  
  <style scoped>
  .function-buttons {
    display: flex;
    margin-bottom: 20px;
    align-items: center;
  }
  
  .function-buttons .ant-btn {
    margin-right: 10px;
  }
  
  .search-box {
    margin-left: auto;
    width: 250px;
  }
  
  .status-tabs {
    display: flex;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 20px;
  }
  
  .status-tab {
    padding: 10px 15px;
    margin-right: 10px;
    cursor: pointer;
    border-bottom: 2px solid transparent;
  }
  
  .status-tab.active {
    color: #1890ff;
    border-bottom: 2px solid #1890ff;
  }
  
  .course-list {
    margin-bottom: 20px;
  }
  
  .chapter-section {
    margin-bottom: 24px;
  }
  
  .chapter-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #f0f0f0;
    margin-bottom: 8px;
  }
  
  .chapter-title {
    font-size: 16px;
    font-weight: bold;
  }
  
  .chapter-actions {
    display: flex;
    align-items: center;
  }
  
  .chapter-action-btn {
    margin-right: 8px;
  }
  
  .course-item {
    position: relative;
    padding: 15px;
	padding-left: 40px;
    border-bottom: 1px solid #efecec;
  }

  .training-extra-info {
    margin: 8px 0;
    padding: 8px 12px;
    background-color: #f6ffed;
    border: 1px solid #b7eb8f;
    border-radius: 4px;
  }

  .training-industry {
    font-size: 12px;
    color: #52c41a;
    margin-bottom: 4px;
    font-weight: 500;
  }

  .training-intro {
    font-size: 12px;
    color: #666;
    line-height: 1.4;
  }
  
  .mandatory-tag {
    display: inline-block;
    background-color: #e6f7ff;
    color: #1890ff;
    padding: 0 6px;
    font-size: 12px;
    border-radius: 4px;
	margin-right: 5px;
  }
  
  .course-status {
    display: inline-block;
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

  .not-started-status {
    background-color: #e6f7ff;
    color: #1890ff;
    border: 1px solid #1890ff;
  }

  .late-completed-status {
    background-color: #fff7e6;
    color: #fa8c16;
  }
  
  .course-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
  }
  
  .course-number {
    color: #1890ff;
    font-weight: 500;
    margin-right: 8px;
  }

  .course-name-link {
    margin-right: 8px;
  }

  .course-name-link.clickable {
    cursor: pointer;
    color: #1890ff;
    transition: color 0.3s;
  }

  .course-name-link.clickable:hover {
    color: #40a9ff;
    text-decoration: underline;
  }

  .all-completed-flag {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-left: auto;
  }
  
  .flag-icon {
    width: 20px;
    height: 20px;
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

  /* 倒计时样式优化 */
  .course-time-remaining {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 100%);
    border: 1px solid #ffd591;
    border-radius: 6px;
    font-size: 13px;
    color: #d46b08;
    font-weight: 500;
  }

  .course-time-remaining::before {
    content: '⏱';
    font-size: 14px;
  }

  .course-time-remaining.urgent {
    background: linear-gradient(135deg, #fff1f0 0%, #fff2f0 100%);
    border-color: #ffa39e;
    color: #cf1322;
    animation: pulse-urgent 2s infinite;
  }

  @keyframes pulse-urgent {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .completed-all-text {
    color: #f5222d;
    font-weight: 500;
  }
  
  .course-actions {
    margin-top: 10px;
  }
  
  .empty-chapter {
    padding: 20px;
    text-align: center;
    color: #999;
    border-radius: 4px;
    margin-bottom: 16px;
  }
  
  /* 新增样式 */
  .chapter-course-count {
    font-size: 12px;
    color: #1890ff;
    margin-left: 8px;
    background-color: #e6f7ff;
    padding: 2px 8px;
    border-radius: 10px;
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
  .course-actions {
    display: flex;
    gap: 10px;
    align-items: center;
    justify-content: flex-end;
  }
  
  /* Training Course Specific */
  .training-meta {
    margin-bottom: 8px;
    display: flex;
    gap: 8px;
  }
  
  .training-intro {
    margin-bottom: 12px;
    line-height: 1.5;
    color: #595959;
  }
  
  .training-courses-section {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
  
  /* Modal Styles */
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    margin-top: 24px; /* Increased space */
    padding-top: 16px; /* Add padding if border is needed */
    /* border-top: 1px solid #f0f0f0; */ /* Optional: line above footer */
    gap: 8px;
  }
  
  .form-item-extra {
    color: #666;
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.4;
  }
  
  /* Sort Modal Styles */
  .sort-container {
    padding: 0 10px;
  }
  
  .sort-description {
    margin-bottom: 20px;
    color: rgba(0, 0, 0, 0.65);
  }
  .sort-description ul {
      padding-left: 20px;
      margin-top: 8px;
  }
  
  .sortable-content {
    margin-bottom: 20px;
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;
    border: 1px dashed #d9d9d9;
  }

  .sort-hint {
    margin-bottom: 16px;
    padding: 12px;
    background: #e6f7ff;
    border-radius: 4px;
    border: 1px solid #91d5ff;
  }

  .sort-hint p {
    margin: 0;
    color: #1890ff;
    font-size: 14px;
  }

  .sortable-chapter-item,
  .sortable-course-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    margin-bottom: 8px;
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    cursor: move;
    transition: all 0.2s;
  }

  .sortable-chapter-item:hover,
  .sortable-course-item:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    border-color: #1890ff;
  }

  .sortable-chapter-item {
    background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
    border-color: #91d5ff;
  }

  .sortable-course-item {
    margin-left: 24px;
  }

  .drag-handle {
    color: #bfbfbf;
    margin-right: 12px;
    font-size: 18px;
    cursor: grab;
  }

  .drag-handle:active {
    cursor: grabbing;
  }

  .item-content {
    display: flex;
    align-items: center;
    flex: 1;
  }

  .item-type {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 12px;
    font-weight: 500;
  }

  .chapter-type {
    background: #1890ff;
    color: #fff;
  }

  .practice-type {
    background: #52c41a;
    color: #fff;
  }

  .training-type {
    background: #722ed1;
    color: #fff;
  }

  .item-title {
    font-size: 14px;
    color: #333;
  }

  .empty-sort-list {
    text-align: center;
    padding: 40px;
    color: #999;
  }

  .sortable-content h3 {
      margin-bottom: 12px;
      font-size: 16px;
  }
  
  .chapters-container, .training-courses {
    margin-bottom: 24px;
  }
  
  .chapter-item {
    border: 1px solid #d9d9d9; /* Slightly darker border */
    border-radius: 4px;
    margin-bottom: 12px;
    background-color: #fff;
    /* overflow: hidden; */ /* Can hide shadows if needed */
  }
  
  .chapter-header {
    background-color: #fafafa;
    padding: 10px 12px;
    display: flex;
    align-items: center;
    cursor: move;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .chapter-title {
    margin-left: 8px;
    font-weight: 500;
  }
  
  .courses-list {
    padding: 8px 12px; /* Padding around courses inside chapter */
  }
  
  /* Shared style for draggable course items */
  .sortable-content .course-item {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    border-radius: 4px;
    margin: 4px 0;
    background-color: #f5f5f5; /* Background for draggable items */
    border: 1px solid #e8e8e8;
    cursor: move;
  }
  
  .drag-handle {
    color: #bfbfbf;
    margin-right: 8px;
    font-size: 16px;
  }
  
  .sortable-content .course-title {
    flex: 1;
    font-size: 14px; /* Consistent font size in sort modal */
    font-weight: normal;
  }
  
  .sortable-content .course-status {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 10px;
    color: #fff;
    margin-left: 8px; /* Space before status tag */
  }
  /* 发布按钮样式 */
  .publish-all-btn {
    font-size: 12px;
    margin-left: 8px;
    padding: 0 4px;
  }
  
  /* 发布对话框样式 */
  .publish-dialog-content {
    padding: 0 10px;
  }
  
  .form-item-help {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    margin-top: 4px;
  }
  
  .publish-dialog {
    .date-input-wrapper,
    .course-type-wrapper {
      width: 100%;
    }
    
    .date-input {
      width: 100%;
    }
    
    .modal-footer {
      display: flex;
      justify-content: flex-end;
      margin-top: 24px;
      padding: 10px 16px;
      border-top: 1px solid #f0f0f0;
      
      button {
        margin-left: 8px;
      }
    }
    
    :deep(.ant-form-item-required::before) {
      display: inline-block;
      margin-right: 4px;
      color: #ff4d4f;
      font-size: 14px;
      font-family: SimSun, sans-serif;
      line-height: 1;
      content: "*";
    }
    
    :deep(.ant-form-item-label > label) {
      font-size: 14px;
      font-weight: 500;
    }
  }
  
  
  /* Ant Collapse Panel Header Alignment */
  :deep(.ant-collapse-header) {
      align-items: center !important;
  }
  :deep(.ant-collapse-extra) {
      margin-left: auto; /* Push extra content to the right */
  }

  /* 章节折叠面板样式 */
  .chapter-collapse {
    background: transparent;
    border: none;
  }

  .chapter-collapse :deep(.ant-collapse-item) {
    margin-bottom: 12px;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
  }

  .chapter-collapse :deep(.ant-collapse-header) {
    background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
    padding: 12px 16px !important;
    font-weight: 600;
    font-size: 15px;
    color: #1890ff;
  }

  .chapter-collapse :deep(.ant-collapse-content) {
    border-top: 1px solid #e8e8e8;
  }

  .chapter-collapse :deep(.ant-collapse-content-box) {
    padding: 0 !important;
  }

  .chapter-extra {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .chapter-extra .chapter-course-count {
    font-size: 12px;
    color: #1890ff;
    background-color: #e6f7ff;
    padding: 2px 8px;
    border-radius: 10px;
    font-weight: normal;
  }

  /* 班级进度统计行样式 */
  .classroom-stats-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 12px 16px;
    margin-bottom: 16px;
    background: linear-gradient(135deg, #f0f5ff 0%, #e6f7ff 100%);
    border: 1px solid #91d5ff;
    border-radius: 8px;
    font-size: 14px;
  }

  .stats-item {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .stats-label {
    color: #595959;
  }

  .stats-value {
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
  }

  .stats-value.not-started {
    color: #1890ff;
    background-color: rgba(24, 144, 255, 0.1);
  }

  .stats-value.learning {
    color: #1890ff;
    background-color: rgba(24, 144, 255, 0.15);
  }

  .stats-value.makeup {
    color: #fa8c16;
    background-color: rgba(250, 140, 22, 0.1);
  }

  .stats-value.completed {
    color: #52c41a;
    background-color: rgba(82, 196, 26, 0.1);
  }

  .stats-item.total .stats-value {
    color: #262626;
    background-color: rgba(0, 0, 0, 0.04);
  }

  .stats-divider {
    color: #d9d9d9;
  }
  </style>