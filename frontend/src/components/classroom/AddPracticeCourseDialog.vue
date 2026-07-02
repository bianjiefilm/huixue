<template>
  <a-modal
    v-model:open="visible"
    title="添加实践课程"
    width="900px"
    :footer="null"
    @cancel="handleCancel"
  >
    <div class="course-selection-container">
      <!-- 搜索框 -->
      <div class="search-bar">
        <a-input-search 
          placeholder="请输入内容" 
          style="width: 200px" 
          @search="onSearch" 
          v-model:value="searchText"
        />
      </div>

      <!-- 统计显示 -->
      <div class="course-count">
        共有 <span class="highlight">{{courses.length || 0}}</span> 个课程
      </div>

      <!-- 分类标签区域 -->
      <div class="filter-tags">
        <!-- 方向类别 -->
        <div class="tag-group">
          <span class="tag-title">方向:</span>
          <a-radio-group v-model:value="filters.direction" buttonStyle="solid">
            <a-radio-button value="all" class="tag-btn">全部</a-radio-button>
            <a-radio-button value="大数据技术" class="tag-btn">大数据技术</a-radio-button>
            <a-radio-button value="人工智能" class="tag-btn">人工智能</a-radio-button>
            <a-radio-button value="云计算" class="tag-btn">云计算</a-radio-button>
            <a-radio-button value="物联网" class="tag-btn">物联网</a-radio-button>
            <a-radio-button value="数据分析" class="tag-btn">数据分析</a-radio-button>
            <a-radio-button value="Web开发" class="tag-btn">Web开发</a-radio-button>
          </a-radio-group>
        </div>

        <!-- 难度类别 -->
        <div class="tag-group">
          <span class="tag-title">难度:</span>
          <a-radio-group v-model:value="filters.difficulty" buttonStyle="solid">
            <a-radio-button value="all" class="tag-btn">全部</a-radio-button>
            <a-radio-button value="easy" class="tag-btn">初级</a-radio-button>
            <a-radio-button value="medium" class="tag-btn">中级</a-radio-button>
            <a-radio-button value="hard" class="tag-btn">高级</a-radio-button>
          </a-radio-group>
        </div>
      </div>

      <!-- 课程列表 -->
      <div class="course-list">
        <a-row :gutter="[16, 16]">
          <a-col :span="12" v-for="(course, index) in filteredCourses" :key="course.id">
            <div 
              class="course-card" 
              :class="getStatusClass(course.id,course.iscz)"
              @click="toggleCourseSelection(course.id,course.iscz)"
            >
              <div class="card-checkbox">
                <a-checkbox :checked="selectedCourses.includes(course.id)" @change="toggleCourseSelection(course.id, course.iscz)" @click.stop/>
              </div>
              <div class="card-cover" :style="{ backgroundColor: getBgColor(index) }">
				  <div class="course-icon">
				    <CodeOutlined />
				  </div>
			  </div>
              <div class="card-content">
                <h3 class="course-title">{{course.title || course.name}}</h3>
                <p class="course-desc">{{course.description || course.introduction}}</p>
                <div class="course-info">
                  <a-tag size="small">{{ course.type_text }}</a-tag>
                  <a-tag size="small" color="blue">{{ course.difficulty_text }}</a-tag>
                  <a-tag size="small" color="#1890ff">{{ course.direction }}</a-tag>
                </div>
              </div>
            </div>
          </a-col>
        </a-row>
      </div>

      <!-- 已选择区域 -->
      <div class="selected-area">
        <div class="selected-count">
          <a-checkbox 
            :checked="selectedCourses.length > 0 && selectedCourses.length === courses.length" 
            :indeterminate="selectedCourses.length > 0 && selectedCourses.length < courses.length"
            @change="toggleSelectAll"
          />
          已选择 <span class="select-count">{{selectedCourses.length}}</span> 个课程
        </div>
        <div class="selected-tags">
          <a-tag 
            v-for="id in selectedCourses" 
            :key="id" 
            closable 
            @close="removeCourse(id)"
            color="blue"
          >
            {{getCourseById(id).name}}
          </a-tag>
        </div>
        
        <!-- 章节选择 -->
        <div class="chapter-selection" v-if="selectedCourses.length > 0">
          <span class="chapter-label">添加到章节:</span>
          <a-select v-model:value="selectedChapterId" style="width: 200px" placeholder="请选择章节">
            <a-select-option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
              {{ chapter.title }}
            </a-select-option>
          </a-select>
        </div>
        
        <div class="action-buttons">
          <a-button @click="handleCancel">取消</a-button>
          <a-button type="primary" @click="handleSubmit" :disabled="selectedCourses.length === 0">
            保存
          </a-button>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { EyeOutlined,CodeOutlined } from '@ant-design/icons-vue';
import { getChapterList, addClassRoomPractice, getAvailableCoursesForClassroom } from '@/api/classrooms';

const emit = defineEmits(['success', 'cancel']);
const visible = ref(false);
const searchText = ref('');
const selectedCourses = ref<string[]>([]);
const selectedChapterId = ref('');
const chapters = ref<any[]>([]);
const courses = ref<any[]>([]);

interface Props {
	chapterId: string;
	classroomId: string;
	nowcourses:[]
}
const props = defineProps<Props>();
// 过滤条件
const filters = reactive({
  direction: 'all',
  category: 'all',
  difficulty: 'all'
});

// 加载章节数据
const loadChapters = async () => {
  const res = await getChapterList({classroom_id:props.classroomId});
  // 处理API响应格式
  const chapterList = res.data?.chapters || res.chapters || res || [];
  chapters.value = chapterList;
  if(props.chapterId>0){
	  selectedChapterId.value=props.chapterId;
  }else if(chapterList.length>0){
	  selectedChapterId.value=chapterList[0].id;
  }
};
// 根据筛选条件过滤课程
const filteredCourses = computed(() => {
  return courses.value.filter(course => {
    // 搜索文本过滤
    const courseName = (course.title || course.name || '').toLowerCase();
    if (searchText.value && !courseName.includes(searchText.value.toLowerCase())) {
      return false;
    }
    
    // 方向过滤
    if (filters.direction !== 'all' && course.direction !== filters.direction) {
      return false;
    }
    
    
    // 难度过滤
    if (filters.difficulty !== 'all') {
      let difficulty = '';
      
      if (course.difficulty_text === '初级') difficulty = 'beginner';
      else if (course.difficulty_text === '中级') difficulty = 'intermediate';
      else if (course.difficulty_text === '高级') difficulty = 'advanced';
      
      if (difficulty !== filters.difficulty) {
        return false;
      }
    }
	/* let index = props.nowcourses.indexOf(course.id);
	if (index !== -1) {
	  return false;
	}*/
    return true;
  });
});

// 打开对话框
const open = () => {
  visible.value = true;
  selectedCourses.value = [];
  getCourseList();
  loadChapters();
};

// 取消操作
const handleCancel = () => {
  visible.value = false;
  selectedCourses.value = [];
  emit('cancel');
};

// 搜索操作
const onSearch = (value: string) => {
  searchText.value = value;
};

// 切换课程选择状态
const toggleCourseSelection = (courseId: string,iscz) => {
	let index2 = props.nowcourses.indexOf(courseId);
	if (index2 == -1) {
		const index = selectedCourses.value.indexOf(courseId);
		if (index === -1) {
		  selectedCourses.value.push(courseId);
		} else {
		  selectedCourses.value.splice(index, 1);
		}
	}
  
};

// 切换全选
const toggleSelectAll = (e: any) => {
  if (e.target.checked) {
    selectedCourses.value = filteredCourses.value.map(course => course.id);
  } else {
    selectedCourses.value = [];
  }
};

// 移除已选课程
const removeCourse = (courseId: string) => {
  const index = selectedCourses.value.indexOf(courseId);
  if (index !== -1) {
    selectedCourses.value.splice(index, 1);
  }
};

// 根据ID获取课程
const getCourseById = (id: string) => {
  return courses.value.find(course => course.id === id) || { title: '' };
};

// 提交选择
const handleSubmit =async () => {
  if (selectedCourses.value.length === 0) {
    message.warning('请至少选择一个课程');
    return;
  }

  if (!selectedChapterId.value) {
    message.warning('请选择要添加到的章节');
    return;
  }
	try {
	  const res = await addClassRoomPractice({
		  classroom_id:props.classroomId,
		  chapter_id:selectedChapterId.value,
		  course_type:'practice',
		  course_ids:selectedCourses.value.join(',')
	  });
	  message.success(`已添加 ${selectedCourses.value.length} 个课程到章节`);
	  visible.value = false;
	  emit('success');
	} catch (err) {
	}
};
const getCourseList = async () => {
	const classroomId = typeof props.classroomId === 'string' ? parseInt(props.classroomId) : props.classroomId;
	const res = await getAvailableCoursesForClassroom({
		classroomId: classroomId,
		courseType: 'practice',
		pageSize: 50
	});
	// Handle various response formats
    let list: any[] = [];
    if (Array.isArray(res)) {
        list = res;
    } else if (res.data && Array.isArray(res.data.courses)) {
        list = res.data.courses;
    } else if (res.data && Array.isArray(res.data.list)) {
        list = res.data.list;
    } else if (Array.isArray(res.data)) {
        list = res.data;
    } else if (Array.isArray(res.list)) {
        list = res.list;
    }

	// Use temporary array to avoid multiple reactivity updates
	const newCourses: any[] = [];
	list.forEach((item: any) => {
		let index2 = -1;
		if(props.nowcourses) index2 = props.nowcourses.indexOf(item.id);

		if (index2 !== -1) {
		  item.iscz=1;
		}else{
			item.iscz=0;
		}
		newCourses.push(item);
	});
	courses.value = newCourses;
}
// 组件挂载时
onMounted(() => {
  // getCourseList() is now called when the dialog opens
});

// 暴露方法给父组件
defineExpose({
  open
});
const getBgColor=(index)=> {
  // 根据索引返回不同的颜色
  const colors = ['#00b42a', '#f7ba1e', '#722ed1', '#0fc6c2', '#9fdb1d', '#165dff', '#00b42a', '#722ed1', '#0fc6c2']; // 示例颜色数组
  return colors[index % colors.length]; // 确保索引在数组范围内
}
const getStatusClass=(id,iscz)=> {
	const index = selectedCourses.value.indexOf(id);
	let clasName='';
	if (index !== -1) {
	  clasName='selected';
	}
	let index2 = props.nowcourses.indexOf(id);
	if (index2 !== -1) {
		clasName=clasName+' bghuise';
	}
	return clasName;
};
</script>

<style scoped>
.course-selection-container {
  padding: 0 10px;
}
.bghuise{
	opacity: 0.4;
	background-color: #e5e1e1;
}
.search-bar {
  margin-bottom: 16px;
  text-align: right;
}

.course-count {
  margin-bottom: 16px;
  font-size: 14px;
}

.highlight {
  color: #1890ff;
  font-weight: bold;
}

.filter-tags {
  margin-bottom: 20px;
}

.tag-group {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.tag-title {
  margin-right: 10px;
  color: #666;
  min-width: 40px;
}

.tag-btn {
  margin-right: 4px;
  font-size: 13px;
  padding: 0 12px;
}

.course-list {
  margin-bottom: 20px;
  max-height: 350px;
  overflow-y: auto;
  padding-right: 5px;
  overflow-x: hidden;
}

.course-card {
  position: relative;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
  display: flex;
  height: 150px;
}

.course-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.course-card.selected {
  border-color: #1890ff;
  background-color: #e6f7ff;
}

.card-checkbox {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 2;
}

.card-cover {
  position: relative;
  width: 100%;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
}

.course-icon {
  font-size: 40px;
  color: #fff;
}

.card-content {
  padding: 10px;
  flex: 1;
}

.course-title {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.course-desc {
  margin-bottom: 10px;
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.course-info {
  display: flex;
  font-size: 12px;
  color: #999;
}

.difficulty, .views {
  margin-right: 12px;
}

.icon-views {
  display: inline-block;
  width: 14px;
  height: 14px;
  background-image: url('data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSI2NCA2NCA4OTYgODk2IiBmb2N1c2FibGU9ImZhbHNlIiBkYXRhLWljb249ImV5ZSIgd2lkdGg9IjFlbSIgaGVpZ2h0PSIxZW0iIGZpbGw9ImN1cnJlbnRDb2xvciIgYXJpYS1oaWRkZW49InRydWUiPjxwYXRoIGQ9Ik05NDIuMiA0ODYuMkM4NDcuNCAyODYuNSA3MDQuMSAxODYgNTEyIDE4NmMtMTkyLjIgMC0zMzUuNCA5OS43LTQzMC4yIDMwMC4zYTYwLjMgNjAuMyAwIDAwMCA1MS41QzE3Ni42IDczNy41IDMxOS45IDgzOCA1MTIgODM4YzE5Mi4yIDAgMzM1LjQtMTAwLjcgNDMwLjItMzAwLjNhNjAuMyA2MC4zIDAgMDAwLTUxLjV6TTUxMiA3NzZjLTE1MSAwLTI4My41LTgxLjUtMzYwLjgtMjU2QzIyOC41IDM0NS41IDM2MSAyNDggNTEyIDI0OGMxNTEgMCAyODMuNCA4MC42IDM2MC43IDI1Ni0yNy4xIDE3NS45LTIwOS43IDI3Mi04Ljc3MnoiPjwvcGF0aD48cGF0aCBkPSJNNTEyIDQwNmExMDYgMTA2IDAgMTAwIDIxMiAxMDYgMTA2IDAgMDAwLTIxMnptMCAxNjBhNTMuMyA1My4zIDAgMTEwLTEwNi42QTUzLjMgNTMuMyAwIDAxNTEyIDU2NnoiPjwvcGF0aD48L3N2Zz4=');
  background-size: contain;
  background-repeat: no-repeat;
  vertical-align: text-bottom;
  margin-right: 2px;
}

.selected-area {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.selected-count {
  margin-bottom: 12px;
}

.select-count {
  color: #1890ff;
  font-weight: bold;
}

.chapter-selection {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.chapter-label {
  margin-right: 10px;
  color: #666;
}

.selected-tags {
  margin-bottom: 16px;
  min-height: 32px;
}

.action-buttons {
  display: flex;
  justify-content: flex-end;
}

.action-buttons button {
  margin-left: 8px;
}
</style> 