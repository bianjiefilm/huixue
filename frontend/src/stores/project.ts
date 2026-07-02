import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { getProjectList, getProjectDetail } from '../api/training';

// 项目实训状态存储
export const useProjectStore = defineStore('project', () => {
  // 状态
  const currentProject = ref<ProjectDetail | null>(null);
  const projects = ref<Project[]>([]);
  const loading = ref(false);
  const projectLoading = ref(false);
  
  // 筛选条件
  const filters = ref<ProjectFilter>({
    industry: 'all',
    trainingType: 'all',
    difficulty: 'all',
  });
  
  // 行业、模式、难度数据
  const industries = ref<Array<{ id: string; name: string }>>([]);
  const projectModes = ref<Array<{ id: string; name: string }>>([]);
  const difficultyLevels = ref<Array<{ id: string; name: string }>>([]);
  const totalProjects = ref(0);
  
  // 操作手册激活标签
  const activeManualKey = ref<string>('1');
  
  // 挑战列表激活键
  const activeChallengeKey = ref<string[]>(['0']);

  // 操作
  // 设置筛选条件
  const setFilter = (key: keyof ProjectFilter, value: string) => {
    if (filters.value) {
      filters.value[key] = value;
    }
  };
  
  // 重置筛选条件
  const resetFilters = () => {
    filters.value = {
      industry: 'all',
      trainingType: 'all',
      difficulty: 'all',
    };
  };
  
  // 获取项目列表
  const fetchProjects = async () => {
    try {
      loading.value = true;
      const response = await getProjectList(filters.value);
      
      projects.value = response.projects || [];
      totalProjects.value = response.total || 0;
      industries.value = response.industries || [];
      projectModes.value = response.trainingTypes || [];
      difficultyLevels.value = response.difficultyLevels || [];
    } catch (error) {
      console.error('获取项目列表失败:', error);
    } finally {
      loading.value = false;
    }
  };
  
  // 获取项目详情
  const fetchProjectDetail = async (id: string) => {
    try {
      projectLoading.value = true;
      currentProject.value = await getProjectDetail(id);
    } catch (error) {
      console.error('获取项目详情失败:', error);
      currentProject.value = null;
    } finally {
      projectLoading.value = false;
    }
  };
  
  // 设置当前项目
  const setCurrentProject = (project: ProjectDetail) => {
    currentProject.value = project;
  };
  
  // 清空当前项目
  const clearCurrentProject = () => {
    currentProject.value = null;
  };
  
  // 设置操作手册激活标签
  const setActiveManualKey = (key: string) => {
    activeManualKey.value = key;
  };
  
  // 设置挑战列表激活键
  const setActiveChallengeKey = (keys: string[]) => {
    activeChallengeKey.value = keys;
  };

  return {
    // 状态
    currentProject,
    projects,
    loading,
    projectLoading,
    filters,
    industries,
    projectModes,
    difficultyLevels,
    totalProjects,
    activeManualKey,
    activeChallengeKey,
    
    // 操作
    setFilter,
    resetFilters,
    fetchProjects,
    fetchProjectDetail,
    setCurrentProject,
    clearCurrentProject,
    setActiveManualKey,
    setActiveChallengeKey
  };
}); 