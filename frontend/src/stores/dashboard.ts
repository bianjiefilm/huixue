import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'

// 活动类型
export interface Activity {
  id: string;
  title: string;
  description: string;
  time: string;
  type: 'user' | 'course' | 'project' | 'exam';
  iconColor: string;
}

// 公告类型
export interface Announcement {
  id: string;
  title: string;
  content: string;
  time: string;
  important: boolean;
}

// 仪表盘数据结构
export interface DashboardData {
  totalUsers: number;
  userIncrease: number;
  totalCourses: number;
  courseIncrease: number;
  totalProjects: number;
  projectIncrease: number;
  totalExams: number;
  examIncrease: number;
  visitsTrend: {
    dates: string[];
    visits: number[];
    activeUsers: number[];
  };
  userDistribution: {
    students: number;
    teachers: number;
    admins: number;
  };
  recentActivities: Activity[];
  announcements: Announcement[];
}

export const useDashboardStore = defineStore('dashboard', () => {
  // 仪表盘数据
  const dashboardData = reactive<DashboardData>({
    totalUsers: 0,
    userIncrease: 0,
    totalCourses: 0,
    courseIncrease: 0,
    totalProjects: 0,
    projectIncrease: 0,
    totalExams: 0,
    examIncrease: 0,
    visitsTrend: {
      dates: [],
      visits: [],
      activeUsers: []
    },
    userDistribution: {
      students: 0,
      teachers: 0,
      admins: 0
    },
    recentActivities: [],
    announcements: []
  });

  // 加载状态
  const loading = ref(false);

  // 获取仪表盘数据
  async function fetchDashboardData() {
    loading.value = true;
    try {
      import('@/api/system').then(async (api) => {
        try {
          const response = await api.getSystemDashboardStats();
          if (response && response.data) {
            dashboardData.totalUsers = response.data.totalUsers || 0;
            dashboardData.totalCourses = response.data.totalCourses || 0;
            dashboardData.totalProjects = response.data.totalProjects || 0;
            dashboardData.totalExams = response.data.totalExams || 0;

            dashboardData.userIncrease = response.data.userIncrease || 0;
            dashboardData.courseIncrease = response.data.courseIncrease || 0;
            dashboardData.projectIncrease = response.data.projectIncrease || 0;
            dashboardData.examIncrease = response.data.examIncrease || 0;
          }
        } catch (apiError) {
          console.error('[Dashboard] 获取系统基础统计失败:', apiError);
        }
      });

      // 对于系统当前未提供的趋势图表、分布图和活动公告，保留原有的部分模拟数据生成以确保页面不抛出渲染空指针错误
      generatePartialMockData();

      return dashboardData;
    } catch (error) {
      console.error('获取仪表盘数据失败:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  // 生成部分模拟数据（保留图表数据的呈现）
  function generatePartialMockData() {

    // 访问趋势
    const today = new Date();
    const dates = [];
    const visits = [];
    const activeUsers = [];

    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(today.getDate() - i);
      dates.push(`${date.getMonth() + 1}/${date.getDate()}`);

      // 生成随机数据
      visits.push(Math.floor(Math.random() * 500) + 500);
      activeUsers.push(Math.floor(Math.random() * 300) + 200);
    }

    dashboardData.visitsTrend.dates = dates;
    dashboardData.visitsTrend.visits = visits;
    dashboardData.visitsTrend.activeUsers = activeUsers;

    // 用户分布
    dashboardData.userDistribution.students = 2106;
    dashboardData.userDistribution.teachers = 385;
    dashboardData.userDistribution.admins = 56;

    // 近期活动
    dashboardData.recentActivities = [
      {
        id: '1',
        title: '新增学生用户',
        description: '新增35名学生用户',
        time: '2023-04-15 09:30',
        type: 'user',
        iconColor: '#1890ff'
      },
      {
        id: '2',
        title: '新建课程',
        description: '教师王明新建了"数据分析与挖掘"课程',
        time: '2023-04-14 14:20',
        type: 'course',
        iconColor: '#52c41a'
      },
      {
        id: '3',
        title: '项目更新',
        description: '更新了"机器学习基础"项目的内容',
        time: '2023-04-14 10:45',
        type: 'project',
        iconColor: '#faad14'
      },
      {
        id: '4',
        title: '考试发布',
        description: '发布了"Python编程基础"期末考试',
        time: '2023-04-13 16:30',
        type: 'exam',
        iconColor: '#722ed1'
      },
      {
        id: '5',
        title: '教师加入',
        description: '新教师李华加入平台',
        time: '2023-04-13 09:15',
        type: 'user',
        iconColor: '#1890ff'
      },
      {
        id: '6',
        title: '优秀作业展示',
        description: '发布了5份优秀学生作业',
        time: '2023-04-12 11:20',
        type: 'project',
        iconColor: '#faad14'
      }
    ];

    // 系统公告
    dashboardData.announcements = [
      {
        id: '1',
        title: '系统维护通知',
        content: '系统将于2023年4月20日凌晨2:00-4:00进行维护升级，期间系统无法访问',
        time: '2023-04-15 10:00',
        important: true
      },
      {
        id: '2',
        title: '新功能上线',
        content: '智能评分系统已上线，欢迎教师用户体验使用',
        time: '2023-04-13 14:30',
        important: false
      },
      {
        id: '3',
        title: '年度教师评优',
        content: '2023年度教师评优活动已开始，请各院系教师积极参与',
        time: '2023-04-12 09:45',
        important: true
      },
      {
        id: '4',
        title: '学期课程安排',
        content: '2023年春季学期课程安排已发布，请教师及时查看',
        time: '2023-04-10 15:20',
        important: false
      },
      {
        id: '5',
        title: '系统使用指南更新',
        content: '系统使用指南已更新，增加了多项新功能的操作说明',
        time: '2023-04-08 11:30',
        important: false
      },
      {
        id: '6',
        title: '数据安全培训',
        content: '将于下周三下午2点举行全校教师数据安全培训',
        time: '2023-04-05 16:40',
        important: true
      }
    ];
  }

  return {
    dashboardData,
    loading,
    fetchDashboardData
  }
}); 