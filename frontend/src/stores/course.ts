import { defineStore } from 'pinia';
import type { CourseResource, MicroCourse, Tag } from '../types/course';
import { getCourseResources, getMicroCourses, getTags, getMicroDirections, getMicroCategories } from '../api/course';

export const useCourseStore = defineStore('course', {
  state: () => ({
    courseResources: [] as CourseResource[],
    microCourses: [] as MicroCourse[],
    tags: [] as Tag[],
    selectedTags: [] as string[],
    keyword: '',
    microFilters: {
      keyword: '',
      direction: '',
      category: '',
      level: ''
    },
    microDirections: [] as string[],
    microCategories: [] as string[],
    loading: {
      courseResources: false,
      microCourses: false,
      tags: false,
      microDirections: false,
      microCategories: false
    }
  }),
  
  getters: {
    filteredCourseResources(): CourseResource[] {
      return this.courseResources;
    }
  },
  
  actions: {
    // 设置搜索关键词
    setKeyword(keyword: string) {
      this.keyword = keyword;
    },
    
    // 设置微型实验筛选条件
    setMicroFilter(key: 'keyword' | 'direction' | 'category' | 'level', value: string) {
      this.microFilters[key] = value;
    },
    
    // 重置微型实验筛选条件
    resetMicroFilters() {
      this.microFilters = {
        keyword: '',
        direction: '',
        category: '',
        level: ''
      };
    },
    
    // 切换标签选中状态
    toggleTag(tagName: string) {
      const index = this.selectedTags.indexOf(tagName);
      if (index > -1) {
        this.selectedTags.splice(index, 1);
      } else {
        this.selectedTags.push(tagName);
      }
    },
    
    // 清空筛选条件
    clearFilters() {
      this.selectedTags = [];
      this.keyword = '';
    },
    
    // 获取课程资源列表
    async fetchCourseResources() {
      this.loading.courseResources = true;
      try {
        this.courseResources = await getCourseResources(this.keyword, this.selectedTags);
      } catch (error) {
        console.error('获取课程资源失败:', error);
      } finally {
        this.loading.courseResources = false;
      }
    },
    
    // 获取微课程列表
    async fetchMicroCourses() {
      this.loading.microCourses = true;
      try {
        const { keyword, direction, category, level } = this.microFilters;
        const courses = await getMicroCourses(keyword, direction, category, level);

        // 直接设置数据，Vue会自动处理响应式更新
        this.microCourses = courses;
      } catch (error) {
        console.error('获取微课程失败:', error);
      } finally {
        this.loading.microCourses = false;
      }
    },
    
    // 获取标签列表
    async fetchTags() {
      this.loading.tags = true;
      try {
        this.tags = await getTags();
      } catch (error) {
        console.error('获取标签失败:', error);
      } finally {
        this.loading.tags = false;
      }
    },
    
    // 获取微型实验方向列表
    async fetchMicroDirections() {
      this.loading.microDirections = true;
      try {
        this.microDirections = await getMicroDirections();
      } catch (error) {
        console.error('获取微型实验方向失败:', error);
      } finally {
        this.loading.microDirections = false;
      }
    },
    
    // 获取微型实验分类列表
    async fetchMicroCategories() {
      this.loading.microCategories = true;
      try {
        this.microCategories = await getMicroCategories();
      } catch (error) {
        console.error('获取微型实验分类失败:', error);
      } finally {
        this.loading.microCategories = false;
      }
    },

    // 更新课堂课程的任务完成状态（用于技能标签重新计算）
    updateClassroomCourseTaskStatus(classroomId: string, courseId: string, taskId: string, completed: boolean) {
      // 这里主要用于触发其他组件重新获取数据
      // 实际的状态更新在组件内部处理
      console.log(`更新课堂课程任务状态: classroom=${classroomId}, course=${courseId}, task=${taskId}, completed=${completed}`);
    }
  }
}); 