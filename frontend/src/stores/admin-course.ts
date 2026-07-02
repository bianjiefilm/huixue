import { defineStore } from 'pinia';
import { 
  CourseType, 
  CourseStatus, 
  ApprovalStatus, 
  ApprovalType,
  type CourseCategory, 
  type PracticeCourse, 
  type TrainingCourse, 
  type CourseApproval,
  EnvironmentType,
  type EnvironmentConfig,
  type ServerResource,
  type ContainerProcess
} from '../types/admin';
// Mock 数据已移除，使用真实 API 获取数据
// 导入真实API
import {
  getServerNodesOverview,
  getContainerProcesses,
  refreshServerNodes,
  refreshContainerProcesses,
  updateConcurrentExperimentSetting,
  getConcurrentExperimentSetting,
  stopContainer,
  batchStopContainers,
  getEnvironmentConfigs
} from '@/api/teaching-resources';

import { CourseManagementAPI } from '@/api/course-management';

export const useAdminCourseStore = defineStore('adminCourse', {
  state: () => ({
    // 课程分类树
    practiceCourseCategories: [] as CourseCategory[],
    trainingCourseCategories: [] as CourseCategory[],
    
    // 课程列表
    practiceCourses: [] as PracticeCourse[],
    trainingCourses: [] as TrainingCourse[],
    
    // 审批记录列表
    practiceApprovals: [] as CourseApproval[],
    trainingApprovals: [] as CourseApproval[],
    
    // 环境配置
    environmentConfigs: [] as EnvironmentConfig[],
    
    // 服务器资源
    serverResources: [] as ServerResource[],
    
    // 允许同时开启多个实验
    allowMultipleExperiments: false,
    
    // 容器进程
    containerProcesses: [] as ContainerProcess[],
    
    // 加载状态
    loading: {
      practiceCourseCategories: false,
      trainingCourseCategories: false,
      practiceCourses: false,
      trainingCourses: false,
      practiceApprovals: false,
      trainingApprovals: false,
      environmentConfigs: false,
      serverResources: false,
      containerProcesses: false
    },
    
    // 筛选条件
    filters: {
      practice: {
        keyword: '',
        categoryKey: 'root',
        sortField: 'updatedAt',
        sortOrder: 'descend'
      },
      training: {
        keyword: '',
        categoryKey: 'root',
        sortField: 'updatedAt',
        sortOrder: 'descend'
      },
      practiceApproval: {
        keyword: '',
        applicant: '',
        type: '',
        appliedTimeRange: [] as string[],
        approvedTimeRange: [] as string[],
        status: '',
        sortField: 'appliedAt',
        sortOrder: 'descend'
      },
      trainingApproval: {
        keyword: '',
        applicant: '',
        type: '',
        appliedTimeRange: [] as string[],
        approvedTimeRange: [] as string[],
        status: '',
        sortField: 'appliedAt',
        sortOrder: 'descend'
      },
      environment: {
        keyword: '',
        type: ''
      },
      container: {
        keyword: '',
        userName: '',
        userId: '',
        courseName: '',
        experimentType: '',
        rangeType: 'startTime', // 'startTime' | 'runningTime' | 'cpu' | 'memory'
        timeRange: [] as string[],
        valueRange: [] as number[]
      }
    }
  }),

  getters: {
    // 根据筛选条件过滤的实践课程列表
    filteredPracticeCourses(): PracticeCourse[] {
      const { keyword, categoryKey, sortField, sortOrder } = this.filters.practice;
      
      // 筛选过滤
      let filtered = [...this.practiceCourses];
      
      // 关键词筛选
      if (keyword) {
        const lowerKeyword = keyword.toLowerCase();
        filtered = filtered.filter(course => 
          course.title.toLowerCase().includes(lowerKeyword) || 
          course.teacher.toLowerCase().includes(lowerKeyword) ||
          course.university.toLowerCase().includes(lowerKeyword)
        );
      }
      
      // 分类筛选
      if (categoryKey && categoryKey !== 'root') {
        // 递归查找指定类别下的所有子类
        const findChildKeys = (categories: CourseCategory[], targetKey: string): string[] => {
          for (const category of categories) {
            if (category.key === targetKey) {
              if (!category.children) return [category.key];
              return [category.key, ...category.children.flatMap(child => findChildKeys([child], child.key))];
            }
            if (category.children) {
              const result = findChildKeys(category.children, targetKey);
              if (result.length > 0) return result;
            }
          }
          return [];
        };
        
        const categoryKeys = findChildKeys(this.practiceCourseCategories, categoryKey);
        
        filtered = filtered.filter(course => {
          // 从分类key中提取实际的分类名称（去掉direction_或category_前缀）
          return categoryKeys.some(key => {
            const keyName = key.replace(/^(direction_|category_)/, '');
            return course.direction.includes(keyName) || course.category.includes(keyName);
          });
        });
      }
      
      // 排序
      filtered = filtered.sort((a, b) => {
        let compareA, compareB;
        
        // 根据排序字段获取排序值
        if (sortField === 'updatedAt' || sortField === 'createdAt') {
          compareA = new Date(a[sortField as keyof PracticeCourse] as string).getTime();
          compareB = new Date(b[sortField as keyof PracticeCourse] as string).getTime();
        } else {
          compareA = a[sortField as keyof PracticeCourse];
          compareB = b[sortField as keyof PracticeCourse];
        }
        
        // 根据排序方向进行比较
        if (sortOrder === 'ascend') {
          return compareA > compareB ? 1 : -1;
        } else {
          return compareA < compareB ? 1 : -1;
        }
      });
      
      return filtered;
    },

    // 根据筛选条件过滤的实训课程列表
    filteredTrainingCourses(): TrainingCourse[] {
      const { keyword, categoryKey, sortField, sortOrder } = this.filters.training;
      
      // 筛选过滤
      let filtered = [...this.trainingCourses];
      
      // 关键词筛选
      if (keyword) {
        const lowerKeyword = keyword.toLowerCase();
        filtered = filtered.filter(course => 
          course.title.toLowerCase().includes(lowerKeyword) || 
          course.teacher.toLowerCase().includes(lowerKeyword) ||
          course.university.toLowerCase().includes(lowerKeyword)
        );
      }
      
      // 行业分类筛选
      if (categoryKey && categoryKey !== 'root') {
        // 递归查找指定类别下的所有子类
        const findChildKeys = (categories: CourseCategory[], targetKey: string): string[] => {
          for (const category of categories) {
            if (category.key === targetKey) {
              if (!category.children) return [category.key];
              return [category.key, ...category.children.flatMap(child => findChildKeys([child], child.key))];
            }
            if (category.children) {
              const result = findChildKeys(category.children, targetKey);
              if (result.length > 0) return result;
            }
          }
          return [];
        };
        
        const categoryKeys = findChildKeys(this.trainingCourseCategories, categoryKey);
        
        filtered = filtered.filter(course => {
          // 这里简化处理，实际需要根据具体分类结构进行匹配
          return categoryKeys.some(key => 
            course.industry.includes(key)
          );
        });
      }
      
      // 排序
      filtered = filtered.sort((a, b) => {
        let compareA, compareB;
        
        // 根据排序字段获取排序值
        if (sortField === 'updatedAt' || sortField === 'createdAt') {
          compareA = new Date(a[sortField as keyof TrainingCourse] as string).getTime();
          compareB = new Date(b[sortField as keyof TrainingCourse] as string).getTime();
        } else {
          compareA = a[sortField as keyof TrainingCourse];
          compareB = b[sortField as keyof TrainingCourse];
        }
        
        // 根据排序方向进行比较
        if (sortOrder === 'ascend') {
          return compareA > compareB ? 1 : -1;
        } else {
          return compareA < compareB ? 1 : -1;
        }
      });
      
      return filtered;
    },

    // 待审批的实践课程列表
    pendingPracticeApprovals(): CourseApproval[] {
      return this.practiceApprovals.filter(item => item.status === ApprovalStatus.PENDING);
    },

    // 已审批的实践课程列表
    approvedPracticeApprovals(): CourseApproval[] {
      return this.practiceApprovals.filter(item => item.status !== ApprovalStatus.PENDING);
    },

    // 待审批的实训课程列表
    pendingTrainingApprovals(): CourseApproval[] {
      return this.trainingApprovals.filter(item => item.status === ApprovalStatus.PENDING);
    },

    // 已审批的实训课程列表
    approvedTrainingApprovals(): CourseApproval[] {
      return this.trainingApprovals.filter(item => item.status !== ApprovalStatus.PENDING);
    }
  },

  actions: {
    // 设置筛选条件
    setFilter(type: string, field: string, value: any) {
      // @ts-ignore (类型安全处理较复杂)
      this.filters[type][field] = value;
    },

    // 重置筛选条件
    resetFilters(type: string) {
      if (type === 'practice') {
        this.filters.practice = {
          keyword: '',
          categoryKey: 'root',
          sortField: 'updatedAt',
          sortOrder: 'descend'
        };
      } else if (type === 'training') {
        this.filters.training = {
          keyword: '',
          categoryKey: 'root',
          sortField: 'updatedAt',
          sortOrder: 'descend'
        };
      } else if (type === 'practiceApproval') {
        this.filters.practiceApproval = {
          keyword: '',
          applicant: '',
          type: '',
          appliedTimeRange: [],
          approvedTimeRange: [],
          status: '',
          sortField: 'appliedAt',
          sortOrder: 'descend'
        };
      } else if (type === 'trainingApproval') {
        this.filters.trainingApproval = {
          keyword: '',
          applicant: '',
          type: '',
          appliedTimeRange: [],
          approvedTimeRange: [],
          status: '',
          sortField: 'appliedAt',
          sortOrder: 'descend'
        };
      } else if (type === 'environment') {
        this.filters.environment = {
          keyword: '',
          type: ''
        };
      } else if (type === 'container') {
        this.filters.container = {
          keyword: '',
          userName: '',
          userId: '',
          courseName: '',
          experimentType: '',
          rangeType: 'startTime',
          timeRange: [],
          valueRange: []
        };
      }
    },

    // ==================== 加载数据 ====================
    // 获取实践课程分类
    async fetchPracticeCourseCategories() {
      try {
        this.loading.practiceCourseCategories = true;
        const response = await CourseManagementAPI.getPracticeCourseCategories();
        this.practiceCourseCategories = response.categories || [];
        return this.practiceCourseCategories;
      } catch (error) {
        console.error('Error fetching practice course categories:', error);
        return [];
      } finally {
        this.loading.practiceCourseCategories = false;
      }
    },

    // 获取实训课程分类
    async fetchTrainingCourseCategories() {
      try {
        this.loading.trainingCourseCategories = true;
        const response = await CourseManagementAPI.getTrainingCourseCategories();
        this.trainingCourseCategories = response.categories || [];
        return this.trainingCourseCategories;
      } catch (error) {
        console.error('Error fetching training course categories:', error);
        return [];
      } finally {
        this.loading.trainingCourseCategories = false;
      }
    },

    // 获取实践课程列表
    async fetchPracticeCourses(params?: any) {
      try {
        this.loading.practiceCourses = true;
        const response = await CourseManagementAPI.getPracticeCourses(params || {});
        // 转换API数据为前端期望的格式
        this.practiceCourses = (response.items || []).map((item: any) => ({
          id: item.id,
          title: item.title,
          teacher: item.creator?.full_name || '未知教师',
          university: item.source || '-',
          direction: item.direction || '-',
          category: item.category || '-',
          status: item.visibility === 'PUBLIC' ? CourseStatus.PUBLISHED : CourseStatus.UNPUBLISHED,
          updatedAt: item.updated_at,
          cover: item.cover_url,
          description: item.description,
          task_count: item.task_count,
          coin: item.coin,
          created_at: item.created_at
        }));
        return this.practiceCourses;
      } catch (error) {
        console.error('Error fetching practice courses:', error);
        return [];
      } finally {
        this.loading.practiceCourses = false;
      }
    },

    // 获取实训课程列表
    async fetchTrainingCourses(params?: any) {
      try {
        this.loading.trainingCourses = true;
        const response = await CourseManagementAPI.getTrainingCourses(params || {});
        // 转换API数据为前端期望的格式
        this.trainingCourses = (response.items || []).map((item: any) => ({
          id: item.id,
          title: item.title,
          teacher: item.creator?.full_name || '未知教师',
          university: item.source || '-',
          industry: item.industry || '-',
          training_type: item.training_type || '-',
          status: item.visibility === 'PUBLIC' ? CourseStatus.PUBLISHED : CourseStatus.UNPUBLISHED,
          updatedAt: item.updated_at,
          cover: item.cover_url,
          description: item.description,
          course_hours: item.course_hours || 0,
          difficulty: item.difficulty || 'BEGINNER',
          created_at: item.created_at
        }));
        return this.trainingCourses;
      } catch (error) {
        console.error('Error fetching training courses:', error);
        return [];
      } finally {
        this.loading.trainingCourses = false;
      }
    },

    // 获取课程详情
    async fetchCourseDetail(id: string): Promise<PracticeCourse | TrainingCourse | any> {
      // 转换实训课程响应为前端期望格式
      const transformTrainingResponse = (response: any) => ({
        ...response,
        type: 'training',
        createdAt: response.created_at,
        updatedAt: response.updated_at,
        status: response.can_unpublish ? 'published' : 'draft',
        teacher: response.creator?.full_name || response.creator?.username || '未知',
        university: response.source || '-',
        cover: response.cover_url || '/default-cover.png',
        description: response.intro || response.handbook_content || ''
      });

      // 转换实践课程响应为前端期望格式
      const transformPracticeResponse = (response: any) => ({
        ...response,
        type: 'practice',
        createdAt: response.created_at,
        updatedAt: response.updated_at,
        status: response.publish_status === 'PUBLISHED' ? 'published' : 'draft',
        teacher: response.creator?.full_name || response.creator?.username || '未知',
        university: response.source || '-',
        cover: response.cover_url || '/default-cover.png'
      });

      try {
        // 判断课程类型并调用相应API
        if (id.startsWith('p-')) {
          // 实践课程
          const courseId = parseInt(id.replace('p-', ''));
          const response = await CourseManagementAPI.getPracticeCourseDetail(courseId);
          return transformPracticeResponse(response);
        } else if (id.startsWith('t-')) {
          // 实训课程
          const courseId = parseInt(id.replace('t-', ''));
          const response = await CourseManagementAPI.getTrainingCourseDetail(courseId);
          return transformTrainingResponse(response);
        } else {
          // 尝试作为数字ID查询
          const courseId = parseInt(id);
          if (!isNaN(courseId)) {
            try {
              const response = await CourseManagementAPI.getPracticeCourseDetail(courseId);
              return transformPracticeResponse(response);
            } catch {
              const response = await CourseManagementAPI.getTrainingCourseDetail(courseId);
              return transformTrainingResponse(response);
            }
          }
        }

        throw new Error('Course not found');
      } catch (error) {
        console.error('Error fetching course detail:', error);
        throw error;
      }
    },

    // 加载实践课程审批记录
    async fetchPracticeApprovals(params?: any) {
      this.loading.practiceApprovals = true;
      try {
        console.log('开始获取实践课程审批记录，参数:', { course_type: 'PRACTICE', ...params });
        const response = await CourseManagementAPI.getCourseRequests({
          course_type: 'PRACTICE',
          ...params
        });
        console.log('实践课程审批API响应:', response);
        // 处理可能的不同响应格式
        const data = response.data || response;
        const items = data.items || data || [];
        // 将API响应转换为前端期望的格式
        this.practiceApprovals = items.map((item: any) => ({
          id: String(item.id),
          courseId: String(item.course_id),
          courseTitle: item.course?.title || '未知课程',
          applicant: item.applicant?.full_name || item.applicant?.username || '未知申请人',
          applicantId: String(item.applicant?.id || ''),
          type: item.request_type === 'PUBLISH' ? ApprovalType.PUBLISH : ApprovalType.UNPUBLISH,
          status: item.status as ApprovalStatus,
          reason: item.application_reason,
          feedback: item.review_comments,
          appliedAt: item.applied_at,
          approvedAt: item.reviewed_at
        }));
        console.log('设置practiceApprovals:', this.practiceApprovals);
      } catch (error) {
        console.error('获取实践课程审批记录失败:', error);
      } finally {
        this.loading.practiceApprovals = false;
      }
    },

    // 加载实训课程审批记录
    async fetchTrainingApprovals(params?: any) {
      this.loading.trainingApprovals = true;
      try {
        const response = await CourseManagementAPI.getCourseRequests({
          course_type: 'TRAINING',
          ...params
        });
        const data = response.data || response;
        const items = data.items || data || [];
        // 将API响应转换为前端期望的格式
        this.trainingApprovals = items.map((item: any) => ({
          id: String(item.id),
          courseId: String(item.course_id),
          courseTitle: item.course?.title || '未知课程',
          applicant: item.applicant?.full_name || item.applicant?.username || '未知申请人',
          applicantId: String(item.applicant?.id || ''),
          type: item.request_type === 'PUBLISH' ? ApprovalType.PUBLISH : ApprovalType.UNPUBLISH,
          status: item.status as ApprovalStatus,
          reason: item.application_reason,
          feedback: item.review_comments,
          appliedAt: item.applied_at,
          approvedAt: item.reviewed_at
        }));
      } catch (error) {
        console.error('获取实训课程审批记录失败:', error);
      } finally {
        this.loading.trainingApprovals = false;
      }
    },

    // 获取环境配置列表
    async fetchEnvironmentConfigs() {
      try {
        this.loading.environmentConfigs = true;
        const response = await getEnvironmentConfigs();
        if (response.code === 200) {
          this.environmentConfigs = response.data.items || [];
        } else {
          console.error('获取环境配置失败:', response.message);
          throw new Error(response.message);
        }
        return this.environmentConfigs;
      } catch (error) {
        console.error('Error fetching environment configs:', error);
        return [];
      } finally {
        this.loading.environmentConfigs = false;
      }
    },
    
    // 更新环境配置
    async updateEnvironmentConfig(id: string, data: {
      storage: { min: number, max: number, default: number },
      memory: { min: number, max: number, default: number },
      cpu: { min: number, max: number, default: number }
    }) {
      try {
        // 模拟API请求
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // 找到要更新的环境
        const index = this.environmentConfigs.findIndex(env => env.id === id);
        if (index !== -1) {
          // 更新环境配置
          this.environmentConfigs[index] = {
            ...this.environmentConfigs[index],
            storage: data.storage,
            memory: data.memory,
            cpu: data.cpu
          };
          return true;
        }
        return false;
      } catch (error) {
        console.error('Error updating environment config:', error);
        return false;
      }
    },
    
    // 获取服务器资源概览
    async fetchServerResources() {
      try {
        this.loading.serverResources = true;
        const response = await getServerNodesOverview();
        if (response.code === 200) {
          // 将后端数据格式转换为前端需要的格式
          const { application_servers, compute_servers } = response.data;
          this.serverResources = [
            ...application_servers.map((server: any) => ({
              ...server,
              type: 'application' as const
            })),
            ...compute_servers.map((server: any) => ({
              ...server,
              type: 'compute' as const
            }))
          ];
        } else {
          console.error('获取服务器资源失败:', response.message);
          throw new Error(response.message);
        }
        return this.serverResources;
      } catch (error) {
        console.error('Error fetching server resources:', error);
        throw error;
      } finally {
        this.loading.serverResources = false;
      }
    },
    
    // 获取容器进程列表（支持筛选条件）
    async fetchContainerProcesses(params?: {
      keyword?: string;
      environment_type?: string;
      start_time_begin?: string;
      start_time_end?: string;
      duration_min?: number;
      duration_max?: number;
      cpu_min?: number;
      cpu_max?: number;
      memory_min?: number;
      memory_max?: number;
      page?: number;
      page_size?: number;
    }) {
      try {
        this.loading.containerProcesses = true;
        
        // 如果没有传入参数，使用当前筛选条件
        let apiParams = params;
        if (!apiParams) {
          const filters = this.filters.container;
          
          // 构建API参数
          apiParams = {
            page: 1,
            page_size: 100
          };
          
          if (filters.keyword) {
            apiParams.keyword = filters.keyword;
          }
          
          if (filters.experimentType) {
            apiParams.environment_type = filters.experimentType;
          }
          
          // 时间范围筛选
          if (filters.rangeType === 'startTime' && filters.timeRange && filters.timeRange.length === 2) {
            apiParams.start_time_begin = filters.timeRange[0];
            apiParams.start_time_end = filters.timeRange[1];
          }
          
          // 数值范围筛选
          if (filters.rangeType !== 'startTime' && filters.valueRange && filters.valueRange.length === 2) {
            const [min, max] = filters.valueRange;
            if (min !== null && max !== null) {
              switch (filters.rangeType) {
                case 'runningTime':
                  apiParams.duration_min = min;
                  apiParams.duration_max = max;
                  break;
                case 'cpu':
                  apiParams.cpu_min = min;
                  apiParams.cpu_max = max;
                  break;
                case 'memory':
                  apiParams.memory_min = min;
                  apiParams.memory_max = max;
                  break;
              }
            }
          }
        }
        
        const response = await getContainerProcesses(apiParams);
        if (response.code === 200) {
          this.containerProcesses = response.data.items;
        } else {
          console.error('获取容器进程失败:', response.message);
          throw new Error(response.message);
        }
        return this.containerProcesses;
      } catch (error) {
        console.error('Error fetching container processes:', error);
        throw error;
      } finally {
        this.loading.containerProcesses = false;
      }
    },

    // ==================== 课程操作 ====================
    // 下架课程
    async unpublishCourse(id: string, reason?: string) {
      try {
        const courseId = parseInt(id.replace(/[pt]-/, ''));
        if (id.startsWith('p-')) {
          const response = await CourseManagementAPI.practiceCourseAction({
            course_id: courseId,
            action: 'unpublish',
            reason
          });
          return response.success;
        } else if (id.startsWith('t-')) {
          const response = await CourseManagementAPI.trainingCourseAction({
            course_id: courseId,
            action: 'unpublish',
            reason
          });
          return response.success;
        }
        return false;
      } catch (error) {
        console.error('下架课程失败:', error);
        return false;
      }
    },

    // 发布课程
    async publishCourse(id: string, reason?: string) {
      try {
        const courseId = parseInt(id.replace(/[pt]-/, ''));
        if (id.startsWith('p-')) {
          const response = await CourseManagementAPI.practiceCourseAction({
            course_id: courseId,
            action: 'publish',
            reason
          });
          return response.success;
        } else if (id.startsWith('t-')) {
          const response = await CourseManagementAPI.trainingCourseAction({
            course_id: courseId,
            action: 'publish',
            reason
          });
          return response.success;
        }
        return false;
      } catch (error) {
        console.error('发布课程失败:', error);
        return false;
      }
    },

    // ==================== 审批操作 ====================
    // 批准课程申请
    async approveCourseApplication(id: string, feedback: string) {
      try {
        const requestId = parseInt(id);
        const response = await CourseManagementAPI.approveCourseRequest(requestId, {
          action: 'approve',
          review_comments: feedback
        });
        
        if (response.success) {
          // 重新加载审批列表
          await this.fetchPracticeApprovals();
          await this.fetchTrainingApprovals();
        }
        
        return response.success;
      } catch (error) {
        console.error('批准课程申请失败:', error);
        return false;
      }
    },

    // 拒绝课程申请
    async rejectCourseApplication(id: string, feedback: string) {
      try {
        const requestId = parseInt(id);
        const response = await CourseManagementAPI.approveCourseRequest(requestId, {
          action: 'reject',
          review_comments: feedback
        });
        
        if (response.success) {
          // 重新加载审批列表
          await this.fetchPracticeApprovals();
          await this.fetchTrainingApprovals();
        }
        
        return response.success;
      } catch (error) {
        console.error('拒绝课程申请失败:', error);
        return false;
      }
    },

    // ==================== 实验资源操作 ====================
    // 获取并发实验设置
    async fetchConcurrentExperimentSetting() {
      try {
        const response = await getConcurrentExperimentSetting();
        if (response.code === 200) {
          this.allowMultipleExperiments = response.data.enabled;
          return response.data;
        } else {
          console.error('获取并发实验设置失败:', response.message);
          throw new Error(response.message);
        }
      } catch (error) {
        console.error('Error fetching concurrent experiment setting:', error);
        throw error;
      }
    },

    // 设置是否允许同时开启多个实验
    async setAllowMultipleExperiments(allow: boolean) {
      try {
        const response = await updateConcurrentExperimentSetting({
          enable: allow,
          operator_id: 1 // TODO: 获取当前用户ID
        });
        
        if (response.code === 200) {
          this.allowMultipleExperiments = allow;
          
          // 如果API响应包含已停止的容器信息，更新本地列表
          if (response.data && response.data.stopped_count > 0) {
            // 重新获取容器列表以反映最新状态
            await this.fetchContainerProcesses();
          }
          
          return response.data;
        } else {
          console.error('设置并发实验失败:', response.message);
          throw new Error(response.message);
        }
      } catch (error) {
        console.error('Error setting multiple experiments:', error);
        throw error;
      }
    },
    
    // 停止容器（支持单个和批量）
    async stopContainers(containerIds: string[]) {
      try {
        if (containerIds.length === 1) {
          // 停止单个容器
          const response = await stopContainer(containerIds[0], {
            reason: '管理员手动停止',
            operator_id: 1 // TODO: 获取当前用户ID
          });
          
          if (response.code === 200) {
            // 从本地列表中移除已停止的容器
            const index = this.containerProcesses.findIndex(p => p.id === containerIds[0]);
            if (index !== -1) {
              this.containerProcesses.splice(index, 1);
            }
            return { success: true, results: [{ container_id: containerIds[0], success: true }] };
          } else {
            console.error('停止容器失败:', response.message);
            throw new Error(response.message);
          }
        } else {
          // 批量停止容器
          const response = await batchStopContainers({
            container_ids: containerIds,
            reason: '管理员批量停止',
            operator_id: 1 // TODO: 获取当前用户ID
          });
          
          if (response.code === 200) {
            // 从本地列表中移除已成功停止的容器
            response.data.results.forEach((result: any) => {
              if (result.success) {
                const index = this.containerProcesses.findIndex(p => p.id === result.container_id);
                if (index !== -1) {
                  this.containerProcesses.splice(index, 1);
                }
              }
            });
            return response.data;
          } else {
            console.error('批量停止容器失败:', response.message);
            throw new Error(response.message);
          }
        }
      } catch (error) {
        console.error('Error stopping containers:', error);
        throw error;
      }
    },

    // 选择/取消选择容器
    toggleContainerSelection(id: string) {
      const index = this.containerProcesses.findIndex(container => container.id === id);
      if (index > -1) {
        this.containerProcesses[index].selected = !this.containerProcesses[index].selected;
      }
    },

    // 获取已选择的容器ID列表
    getSelectedContainerIds() {
      return this.containerProcesses
        .filter(container => container.selected)
        .map(container => container.id);
    },

    // 清除所有容器选择
    clearContainerSelections() {
      this.containerProcesses.forEach(container => {
        container.selected = false;
      });
    }
  }
}); 