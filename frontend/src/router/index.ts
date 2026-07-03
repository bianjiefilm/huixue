import { createRouter, createWebHashHistory } from 'vue-router'
import type { RouteRecordRaw, RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'
// import { Permission, routePermissions } from '@/constants/permissions'
// import { usePermission } from '@/composables/usePermission'
// import { ElMessage } from 'element-plus'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Root',
    redirect: '/classroom'  // 默认重定向到我的课堂（调试模式）
  },
  {
    path: '/preview/bi/:id',
    name: 'BIPreviewFullscreen',
    component: () => import('../views/visual/preview.vue'),
    meta: {
      title: 'BI 预览',
      requiresAuth: true
    }
  },
  {
    path: '/',
    component: () => import('../components/layout/BasicLayout.vue'),
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('../views/Home.vue'),
        meta: {
          title: '首页'
        }
      },
      {
        path: 'course',
        name: 'Course',
        component: () => import('../views/course/index.vue'),
        meta: {
          title: '课程实践',
          requiresAuth: true  // 需要登录才能访问
        }
      },
      {
        path: 'classroom',
        name: 'Classroom',
        component: () => import('../views/classroom/ClassroomListView.vue'),
        meta: {
          title: '我的课堂',
          requiresAuth: true
        }
      },
      // AI Co-pilot 学生仪表板（新版）
      {
        path: 'student-dashboard',
        name: 'StudentDashboard',
        component: () => import('../views/student/AICopilotDashboard.vue'),
        meta: {
          title: '学习仪表板',
          requiresAuth: true
        }
      },
      // 课堂考试列表 - 必须放在 classroom/:id 之前
      {
        path: 'classroom/:classroomId/exams',
        name: 'ClassroomExams',
        component: () => import('../views/classroom/ClassroomExams.vue'),
        meta: {
          title: '课程考核',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/exam/create',
        name: 'ClassroomExamCreate',
        component: () => import('../views/classroom/ClassroomExamCreate.vue'),
        meta: {
          title: '创建考试',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'classroom/:id',
        name: 'ClassroomDetail',
        component: () => import('../views/classroom/detail.vue'),
        meta: {
          title: '课堂详情',
          requiresAuth: true
        },
        children: [
          {
            path: '',
            name: 'ClassroomDetailDefault',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          },
          {
            path: 'trainings',
            name: 'ClassroomDetailTrainings',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          },
          {
            path: 'resources',
            name: 'ClassroomDetailResources',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          },
          {
            path: 'exams',
            name: 'ClassroomDetailExams',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          },
          {
            path: 'analytics',
            name: 'ClassroomDetailAnalytics',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          },
          {
            path: 'drive',
            name: 'ClassroomDetailDrive',
            component: () => import('../views/classroom/detail.vue'),
            meta: {
              title: '课堂详情',
              requiresAuth: true
            }
          }
        ]
      },
      {
        path: 'classroom/:id/status',
        name: 'CourseStatus',
        component: () => import('../views/classroom/course-status.vue'),
        meta: {
          title: '课程状态管理',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/course/:classroomCourseId/grades',
        name: 'CourseGrades',
        component: () => import('../views/classroom/course-grades.vue'),
        meta: {
          title: '课程成绩',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId/homework/:studentId?',
        name: 'HomeworkDetail',
        component: () => import('../views/classroom/homework-detail.vue'),
        meta: {
          title: '作业详情',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/submission/:progressId',
        name: 'SubmissionDetail',
        component: () => import('../views/classroom/submission/SubmissionDetail.vue'),
        meta: {
          title: '实训作业详情',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:id/student-status',
        name: 'StudentCourseStatus',
        component: () => import('../views/classroom/student-course-status.vue'),
        meta: {
          title: '我的课程状态',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:id/student-grades',
        name: 'StudentGrades',
        component: () => import('../views/classroom/student-grades.vue'),
        meta: {
          title: '个人成绩单',
          requiresAuth: true
        }
      },
      // {
      //   path: 'classroom/:id/excellent-works',
      //   name: 'ExcellentWorks',
      //   component: () => import('../views/classroom/excellent-works.vue'),
      //   meta: {
      //     title: '优秀作业展示',
      //     requiresAuth: true
      //   }
      // },
      {
        path: 'classroom/:id/edit',
        name: 'ClassroomEdit',
        component: () => import('../views/classroom/edit.vue'),
        meta: {
          title: '编辑课堂',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: '/teacher/ai-practice-generator',
        name: 'TeacherAiPracticeGenerator',
        component: () => import('../views/teacher-ai/GeneratorForm.vue'),
        meta: {
          title: 'AI 生成实践闯关任务',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: '/teacher/ai-practice-generator/:jobId/knowledge',
        name: 'TeacherAiPracticeGeneratorKnowledge',
        component: () => import('../views/teacher-ai/KnowledgeConfirm.vue'),
        meta: {
          title: '知识点确认',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: '/teacher/ai-practice-generator/:jobId/drafts',
        name: 'TeacherAiPracticeGeneratorDrafts',
        component: () => import('../views/teacher-ai/DraftsReview.vue'),
        meta: {
          title: '关卡草稿审核',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'classroom/:id/learning-analytics',
        name: 'LearningAnalytics',
        component: () => import('../views/classroom/LearningAnalytics.vue'),
        meta: {
          title: '学情分析',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId',
        name: 'ClassroomCourseDetail',
        component: () => import('../views/classroom/course-detail.vue'),
        meta: {
          title: '课程详情',
          requiresAuth: true
        }
      },
      // 课程考核页面
      {
        path: 'classroom/:classroomId/course/:courseId/exams',
        name: 'CourseExams',
        component: () => import('../views/classroom/course-exam.vue'),
        meta: {
          title: '课程考核',
          requiresAuth: true
        }
      },
      // 考试详情页面 - 暂时注释，文件不存在
      /*
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId',
        name: 'CourseExam',
        component: () => import('../views/classroom/exam.vue'),
        meta: {
          title: '课堂考试',
          requiresAuth: true
        }
      },
      */
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId/marking',
        name: 'ExamMarkingList',
        component: () => import('../views/classroom/exam-marking-list.vue'),
        meta: {
          title: '试卷批阅',
          requiresAuth: true,
          requiresTeacher: true  // [SEC-03修复] 仅教师可访问
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId/marking/:studentId',
        name: 'ExamMarkingDetail',
        component: () => import('../views/classroom/exam-marking-detail.vue'),
        meta: {
          title: '学生试卷批阅',
          requiresAuth: true,
          requiresTeacher: true  // [SEC-03修复] 仅教师可访问
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId/detail',
        name: 'ExamDetail',
        component: () => import('../views/classroom/exam-detail.vue'),
        meta: {
          title: '考试详情',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId/results',
        name: 'ExamResults',
        component: () => import('../views/classroom/exam-results.vue'),
        meta: {
          title: '考试结果',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/course/:courseId/exam/:examId/paper/:studentId',
        name: 'ExamPaperView',
        component: () => import('../views/classroom/exam-paper-view.vue'),
        meta: {
          title: '查看学生试卷',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/exam/:examId/take',
        name: 'ExamTake',
        component: () => import('../views/classroom/exam-take.vue'),
        meta: {
          title: '考试作答',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/exam/:examId/marking',
        name: 'ExamMarkingSimple',
        component: () => import('../views/classroom/exam-marking.vue'),
        meta: {
          title: '考试阅卷',
          requiresAuth: true,
          requiresTeacher: true  // [SEC-03修复] 仅教师可访问
        }
      },
      {
        path: 'classroom/:classroomId/exam/:examId/paper/:studentId',
        name: 'ExamPaperView',
        component: () => import('../views/classroom/exam-paper-view.vue'),
        meta: {
          title: '查看学生试卷',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'classroom/:classroomId/exam/:examId/results',
        name: 'ExamResultsSimple',
        component: () => import('../views/classroom/exam-statistics.vue'),
        meta: {
          title: '考试详情',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'classroom/:classroomId/exam/:examId/my-result',
        name: 'ExamMyResult',
        component: () => import('../views/classroom/exam-my-result.vue'),
        meta: {
          title: '我的成绩',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/training/:trainingId',
        name: 'TrainingDetailInClassroom',
        component: () => import('../views/classroom/TrainingDetailInClassroom.vue'),
        meta: {
          title: '实训详情',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/training/:trainingId/workspace',
        name: 'TrainingWorkspace',
        component: () => import('../views/classroom/TrainingWorkspace.vue'),
        meta: {
          title: '实训工作区',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/bi-training/:trainingId/workspace',
        name: 'BiTrainingWorkspace',
        component: () => import('../views/classroom/BiTrainingWorkspace.vue'),
        meta: {
          title: 'BI 实训工作区',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/training/:trainingId/bi-designer',
        name: 'ClassroomBIDesigner',
        component: () => import('../views/visual/bi-designer.vue'),
        meta: {
          title: 'BI 设计器',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/bi-training/:trainingId/review/:studentId',
        name: 'BiSubmissionReview',
        component: () => import('../views/classroom/BiSubmissionReview.vue'),
        meta: {
          title: 'BI 作业评阅',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'classroom/:classroomId/training/:trainingId/grades',
        name: 'TrainingGrades',
        component: () => import('../views/classroom/TrainingGrades.vue'),
        meta: {
          title: '实训成绩',
          requiresAuth: true
        }
      },
      {
        path: 'classroom/:classroomId/training/:trainingId/homework',
        name: 'TrainingHomework',
        component: () => import('../views/classroom/TrainingHomework.vue'),
        meta: {
          title: '实训作业',
          requiresAuth: true
        }
      },
      // 有限游戏：标准项目实训列表（替换实验性画布）
      {
        path: 'project',
        name: 'project',
        component: () => import('@/views/project/index.vue'),
        meta: {
          title: '项目实训'
        }
      },
      {
        path: 'project/jupyter',
        name: 'projectJupyter',
        component: () => import('@/views/project/ProjectTraining.vue'),
        meta: {
          title: 'JupyterLite 实训',
          requiresAuth: true
        }
      },
      {
        path: 'project/:trainingId/code/:taskId',
        name: 'ProjectTrainingCodeTask',
        component: () => import('@/views/project/code-task.vue'),
        meta: {
          title: '编程实训',
          requiresAuth: true
        }
      },
      {
        path: 'project/:id',
        name: 'projectDetail',
        component: () => import('@/views/project/detail-new.vue'),
        meta: {
          title: '实训详情',
          requiresAuth: true
        }
      },
      {
        path: 'bi-designer/:id',
        name: 'PublicBIDesigner',
        component: () => import('../views/visual/bi-designer.vue'),
        meta: {
          title: 'BI 设计器',
          requiresAuth: true
        }
      },
      {
        path: 'ai-designer/:id',
        name: 'PublicAIDesigner',
        component: () => import('../views/ml/ai-designer.vue'),
        meta: {
          title: 'AI 设计器',
          requiresAuth: true
        }
      },
      {
        path: 'jupyter/:id',
        name: 'PublicJupyterTraining',
        component: () => import('@/views/project/jupyter-training.vue'),
        meta: {
          title: 'Jupyter 编辑器',
          requiresAuth: true
        }
      },
      {
        path: 'project/jupyter/:id',
        name: 'JupyterTraining',
        component: () => import('@/views/project/jupyter-training.vue'),
        meta: {
          title: 'Jupyter编码式实训',
          requiresAuth: true
        }
      },
      {
        path: 'visual',
        name: 'VisualAnalysis',
        component: () => import('../views/visual/bi-designer.vue'),
        meta: {
          title: '可视化分析实训',
          requiresAuth: true
        }
      },
      {
        path: 'visual/preview',
        name: 'VisualPreview',
        component: () => import('../views/visual/preview.vue'),
        meta: {
          title: '可视化分析预览',
          requiresAuth: true // 需要登录才能访问
        }
      },
      {
        path: 'course/resource',
        name: 'CourseResource',
        component: () => import('../views/course/resource/index.vue'),
        meta: {
          title: '实验资源'
        }
      },
      {
        path: 'course/resource/:id',
        name: 'CourseDetail',
        component: () => import('../views/course/resource/detail.vue'),
        meta: {
          title: '课程详情'
        }
      },
      {
        path: 'debug/courses',
        name: 'CourseDebug',
        component: () => import('../views/debug/course-debug.vue'),
        meta: {
          title: '课程数据调试'
        }
      },
      {
        path: 'debug/api-test',
        name: 'APITest',
        component: () => import('../views/debug/api-test.vue'),
        meta: {
          title: 'API测试'
        }
      },
      {
        path: 'course/micro',
        name: 'MicroCourse',
        component: () => import('../views/course/micro/index.vue'),
        meta: {
          title: '微型实验库'
        }
      },
      {
        path: 'course/micro/:id',
        name: 'MicroCourseDetail',
        component: () => import('../views/course/micro/detail.vue'),
        meta: {
          title: '微型实验详情'
        }
      },
      {
        path: 'course/practice/my',
        name: 'MyPractices',
        component: () => import('../views/course/practice/my-practices.vue'),
        meta: {
          title: '我创建的实践',
          requiresAuth: true // 需要登录才能访问
        }
      },
      {
        path: 'course/practice/create',
        name: 'CreatePractice',
        component: () => import('../views/course/practice/create.vue'),
        meta: {
          title: '创建实践课程',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'course/practice/:id/edit',
        name: 'EditPractice',
        component: () => import('../views/course/practice/edit.vue'),
        meta: {
          title: '编辑实践课程',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'course/practice/:id',
        name: 'PracticeDetail',
        component: () => import('../views/course/practice/detail.vue'),
        meta: {
          title: '实践详情',
          requiresAuth: true
        }
      },
      {
        path: 'course/training/my',
        name: 'MyTrainings',
        component: () => import('../views/course/training/my-trainings.vue'),
        meta: {
          title: '我创建的实训',
          requiresAuth: true
        }
      },
      {
        path: 'course/training/create',
        name: 'CreateTraining',
        component: () => import('../views/course/training/create.vue'),
        meta: {
          title: '创建实训课程',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'course/training/:id/edit',
        name: 'EditTraining',
        component: () => import('../views/course/training/edit.vue'),
        meta: {
          title: '编辑实训课程',
          requiresAuth: true,
          requiresTeacher: true
        }
      },
      {
        path: 'course/training/library',
        name: 'TrainingLibrary',
        component: () => import('../views/course/training/training-library.vue'),
        meta: {
          title: '实训资源库',
          requiresAuth: true
        }
      },
      // {
      //   path: 'course/resource/teaching-library',
      //   name: 'TeachingResourceLibrary',
      //   component: () => import('../views/course/resource/teaching-resource-library.vue'),
      //   meta: {
      //     title: '教学资源库',
      //     requiresAuth: true
      //   }
      // },
      {
        path: 'practice/:practiceId/stage/:stageId/test',
        name: 'StageTest',
        component: () => import('../views/practice/StageTest.vue'),
        meta: {
          title: '测试关卡',
          requiresAuth: true
        }
      },
      {
        path: 'course/challenge/:courseId/:taskId',
        name: 'ChallengeDetail',
        component: () => import('../views/course/challenge/detail.vue'),
        meta: {
          title: '挑战详情',
          requiresAuth: true // 需要登录才能访问
        }
      },
      {
        path: 'ml',
        name: 'MachineLearning',
        component: () => import('../views/ml/AiEmbed.vue'),
        meta: {
          title: '机器学习实训',
          requiresAuth: true
        }
      },
      {
        path: 'ml/manual',
        name: 'MLManual',
        component: () => import('../views/ml/manual.vue'),
        meta: {
          title: '机器学习手册'
        }
      },
      // 优秀作业相关 [已移除]
      // {
      //   path: 'excellent-works',
      //   name: 'ExcellentWorksIndex',
      //   component: () => import('../views/excellent-works/index.vue'),
      //   redirect: '/excellent-works/excellent',
      //   meta: {
      //     title: '优秀作业'
      //   },
      //   children: [
      //     {
      //       path: 'excellent',
      //       name: 'ExcellentResults',
      //       component: () => import('../views/excellent-works/excellent-results.vue'),
      //       meta: {
      //         title: '优秀成果'
      //       }
      //     },
      //     {
      //       path: 'collected',
      //       name: 'CollectedWorks',
      //       component: () => import('../views/excellent-works/collected-works.vue'),
      //       meta: {
      //         title: '我收藏的作业',
      //         requiresAuth: true
      //       }
      //     }
      //   ]
      // },
      
      // 考试中心路由
      {
        path: 'exam',
        name: 'ExamCenter',
        component: () => import('../views/exam/index.vue'),
        redirect: '/exam/paper-bank',
        meta: {
          title: '考试中心',
          requiresAuth: true
        },
        children: [
          {
            path: 'paper-bank',
            name: 'PaperBank',
            component: () => import('../views/exam/paper-bank.vue'),
            meta: {
              title: '试卷库',
              requiresAuth: true
            }
          },
          {
            path: 'my-exams',
            name: 'MyExams',
            component: () => import('../views/exam/my-exams.vue'),
            meta: {
              title: '我的考试',
              requiresAuth: true
            }
          },
          {
            path: 'question-bank',
            name: 'QuestionBank',
            component: () => import('../views/exam/question-bank.vue'),
            meta: {
              title: '试题库',
              requiresAuth: true
            }
          },
          {
            path: 'create-question',
            name: 'CreateQuestion',
            component: () => import('../views/exam/create-question.vue'),
            meta: {
              title: '新建试题',
              requiresAuth: true,
              requiresTeacher: true
            }
          },
          {
            path: 'edit-question',
            name: 'EditQuestion',
            component: () => import('../views/exam/edit-question.vue'),
            meta: {
              title: '编辑试题',
              requiresAuth: true,
              requiresTeacher: true
            }
          },
          {
            path: 'edit-paper',
            name: 'EditPaper',
            component: () => import('../views/exam/edit-paper.vue'),
            meta: {
              title: '编辑试卷',
              requiresAuth: true,
              requiresTeacher: true
            }
          },
          {
            path: 'template-paper',
            name: 'TemplatePaper',
            component: () => import('../views/exam/template-paper.vue'),
            meta: {
              title: '模板组卷',
              requiresAuth: true
            }
          }
        ]
      },
      // 个人中心
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/profile/Profile.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true
        }
      },
    ]
  },
  // 登录页面，不使用全局布局
	{
		path: '/login',
		name: 'Login',
		component: () => import('../views/auth/Login.vue'),
		meta: { title: '用户登录' }
	},
  // 独立全屏设计器页面 (用于 iframe 嵌入隔离)
  {
    path: '/designer/bi/:id?/embed',
    name: 'VisualAnalysisDesigner',
    component: () => import('../views/visual/TempoBIEmbed.vue'),
    meta: {
      title: 'BI 设计器',
      // requiresAuth: true // iframe has its own postMessage initialization
    }
  },
  {
    path: '/designer/ml/:id?',
    name: 'MachineLearningDesigner',
    component: () => import('../views/ml/ai-designer.vue'),
    meta: {
      title: 'AI 建模设计器',
      requiresAuth: true
    }
  },
  // 重定向路由，用于无刷新重载当前页面
  {
    path: '/redirect',
    name: 'Redirect',
    component: () => import('../components/layout/BasicLayout.vue'),
    children: [
      {
        path: '',
        name: 'RedirectPage',
        component: () => import('../views/Redirect.vue')
      }
    ]
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/error/NotFound.vue'),
    meta: {
      title: '页面未找到'
    }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('../views/admin/index.vue'),
    meta: {
      title: '系统管理',
      requiresAuth: true
      // 移除requiresAdmin，只在具体页面检查
    },
    redirect: '/admin/dashboard',
    children: [
      // 仪表盘
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/admin/dashboard/index.vue'),
        meta: {
          title: '系统仪表盘',
          requiresAuth: true
          // 移除requiresAdmin，允许所有登录用户访问
        }
      },
      // 资源管理
      {
        path: 'resource-import',
        name: 'ResourceImport',
        component: () => import('../views/admin/resource-import.vue'),
        meta: {
          title: '资源批量导入',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 组织架构管理
      {
        path: 'organization/school-info',
        name: 'SchoolInfo',
        component: () => import('../views/system/school-info.vue'),
        meta: {
          title: '学校信息',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'organization/department',
        name: 'Department',
        component: () => import('../views/admin/organization/Department.vue'),
        meta: {
          title: '院系设置',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 用户管理
      {
        path: 'user/teacher',
        name: 'TeacherManagement',
        component: () => import('../views/system/teacher-management.vue'),
        meta: {
          title: '教师管理',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 学生管理页面
      {
        path: 'user/student',
        name: 'StudentManagement',
        component: () => import('../views/admin/user/Student.vue'),
        meta: {
          title: '学生管理',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'user/role',
        name: 'RoleManagement',
        component: () => import('../views/admin/user/Role.vue'),
        meta: {
          title: '角色授权',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 添加课程管理相关路由
      {
        path: 'course/practice',
        name: 'PracticeCourseManagement',
        component: () => import('../views/admin/course/PracticeCourse.vue'),
        meta: {
          title: '实践课程管理',
          requiresAdmin: true
        }
      },
      {
        path: 'course/training',
        name: 'TrainingCourseManagement',
        component: () => import('../views/admin/course/TrainingCourse.vue'),
        meta: {
          title: '实训课程管理',
          requiresAdmin: true
        }
      },
      {
        path: 'course/practice-approval',
        name: 'PracticeCourseApproval',
        component: () => import('../views/admin/course/PracticeApproval.vue'),
        meta: {
          title: '实践课程审批',
          requiresAdmin: true
        }
      },
      {
        path: 'course/training-approval',
        name: 'TrainingCourseApproval',
        component: () => import('../views/admin/course/TrainingApproval.vue'),
        meta: {
          title: '实训课程审批',
          requiresAdmin: true
        }
      },
      {
        path: 'course/detail/:id',
        name: 'CourseDetail2',
        component: () => import('../views/admin/course/CourseDetail.vue'),
        meta: {
          title: '课程详情',
          requiresAdmin: true
        }
      },
      // 考试管理 - 重定向到试卷库
      {
        path: 'exam-management',
        name: 'AdminExamManagement',
        redirect: '/exam',
        meta: {
          title: '考试管理',
          requiresAdmin: true
        }
      },
      // AI辅助生成路由
      {
        path: 'ai-generation/practice',
        name: 'AICoursePracticeGenerator',
        component: () => import('../views/admin/ai-generation/CoursePracticeGenerator.vue'),
        meta: {
          title: 'AI辅助课程实践生成',
          requiresAdmin: true
        }
      },
      {
        path: 'ai-generation/exam',
        name: 'AIExamQuestionGenerator',
        component: () => import('../views/admin/ai-generation/ExamQuestionGenerator.vue'),
        meta: {
          title: 'AI辅助试题生成',
          requiresAdmin: true
        }
      },
      // 添加教学资源管理相关路由
      {
        path: 'resource/environment',
        name: 'EnvironmentManagement',
        component: () => import('../views/admin/resource/Environment.vue'),
        meta: {
          title: '实践环境管理',
          requiresAdmin: true
        }
      },
      {
        path: 'resource/experiment',
        name: 'ExperimentResourceManagement',
        component: () => import('../views/admin/resource/ExperimentResource.vue'),
        meta: {
          title: '实验资源管理',
          requiresAdmin: true
        }
      },
      // AI内容生成
      {
        path: 'ai-generation',
        name: 'AIGeneration',
        component: () => import('../views/admin/ai-generation/index.vue'),
        meta: {
          title: '内容智能生成',
          requiresAdmin: true
        }
      },
      // 批量课程生成
      {
        path: 'ai-generation/batch',
        name: 'BatchCourseGenerator',
        component: () => import('../views/admin/ai-generation/BatchCourseGenerator.vue'),
        meta: {
          title: '自动化课程生成',
          requiresAdmin: true
        }
      },
      // 实训资源增强
      {
        path: 'ai-generation/training',
        name: 'TrainingResourceEnhancer',
        component: () => import('../views/admin/ai-generation/TrainingResourceEnhancer.vue'),
        meta: {
          title: '实训资源增强',
          requiresAdmin: true
        }
      },
      // AI功能测试页面
      {
        path: 'ai-test',
        name: 'AITest',
        component: () => import('../views/ai-test.vue'),
        meta: {
          title: 'AI功能测试',
          requiresAuth: true
        }
      },
      // 使用日志分析 - 课程统计分析
      {
        path: '/admin/logs/course',
        name: 'AdminCourseStatistics',
        component: () => import('@/views/admin/logs/CourseStatistics.vue'),
        meta: {
          title: '课程统计分析',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 课程详情统计
      {
        path: '/admin/logs/course/:id',
        name: 'AdminCourseDetailStatistics',
        component: () => import('@/views/admin/logs/CourseDetailStatistics.vue'),
        meta: {
          title: '课程访问统计',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 使用日志分析 - 实践统计分析
      {
        path: '/admin/logs/practice',
        name: 'AdminPracticeStatistics',
        component: () => import('@/views/admin/logs/PracticeStatistics.vue'),
        meta: {
          title: '实践统计分析',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 实践详情统计
      {
        path: '/admin/logs/practice/:id',
        name: 'AdminPracticeDetailStatistics',
        component: () => import('@/views/admin/logs/PracticeDetailStatistics.vue'),
        meta: {
          title: '实践访问统计',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 使用日志分析 - 实训统计分析
      {
        path: '/admin/logs/training',
        name: 'AdminTrainingStatistics',
        component: () => import('@/views/admin/logs/TrainingStatistics.vue'),
        meta: {
          title: '实训统计分析',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 实训详情统计
      {
        path: '/admin/logs/training/:id',
        name: 'AdminTrainingDetailStatistics',
        component: () => import('@/views/admin/logs/TrainingDetailStatistics.vue'),
        meta: {
          title: '实训访问统计',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 使用日志分析 - 教师使用统计
      {
        path: '/admin/logs/teacher',
        name: 'AdminTeacherUsageStatistics',
        component: () => import('@/views/admin/logs/TeacherUsageStatistics.vue'),
        meta: {
          title: '教师使用统计',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 使用日志分析 - 学生使用统计
      {
        path: '/admin/logs/student',
        name: 'AdminStudentUsageStatistics',
        component: () => import('@/views/admin/logs/StudentUsageStatistics.vue'),
        meta: {
          title: '学生使用统计',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 添加教师表单路由
      {
        path: 'user/teacher/add',
        name: 'AddTeacher',
        component: () => import('../views/admin/user/TeacherForm.vue'),
        meta: {
          title: '添加教师',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'user/teacher/edit/:id',
        name: 'TeacherEdit',
        component: () => import('../views/admin/user/TeacherForm.vue'),
        meta: {
          title: '编辑教师',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      // 学生添加/编辑页面
      {
        path: 'user/student/add',
        name: 'StudentAdd',
        component: () => import('../views/admin/user/StudentForm.vue'),
        meta: {
          title: '添加学生',
          requiresAuth: true,
          requiresAdmin: true
        }
      },
      {
        path: 'user/student/edit/:id',
        name: 'StudentEdit',
        component: () => import('../views/admin/user/StudentForm.vue'),
        meta: {
          title: '编辑学生',
          requiresAuth: true,
          requiresAdmin: true
        }
      }
    ]
  },
  // 测试相关路由
  {
    path: '/test',
    component: () => import('../components/layout/BasicLayout.vue'),
    children: [
      {
        path: 'student',
        name: 'StudentManagementTest',
        component: () => import('../views/test/StudentManagement.vue'),
        meta: {
          title: '学生管理测试页面'
        }
      },
      {
        path: 'real-data',
        name: 'TestRealData',
        component: () => import('../views/TestRealData.vue'),
        meta: {
          title: '真实数据连接测试'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL),
  routes
})

// 防止路由守卫无限循环的计数器
let navigationCount = 0;
const MAX_NAVIGATIONS = 10;

// 路由前置守卫
router.beforeEach((to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) => {
  // 防止无限循环
  navigationCount++;
  if (navigationCount > MAX_NAVIGATIONS) {
    console.error('路由导航次数过多，可能存在无限循环！');
    navigationCount = 0;
    next(false); // 取消导航
    return;
  }
  
  // 重置计数器
  setTimeout(() => {
    navigationCount = 0;
  }, 1000);
  
  // ========== 关键修复：在最开始就检查是否是来自代理iframe的导航 ==========
  // 这必须在所有其他检查之前执行，以防止iframe的初始加载被拦截
  const referer = typeof document !== 'undefined' ? document.referrer : '';
  const isRefererProxy = referer.includes('/api/v1/environments/proxy/');
  const currentUrl = typeof window !== 'undefined' ? window.location.href : '';
  const isCurrentUrlProxy = currentUrl.includes('/api/v1/environments/proxy/');
  const isInIframe = typeof window !== 'undefined' && window.top !== window.self;
  
  // 关键修复：检查 to.fullPath 和 to.href 是否包含代理路径
  const toPathIncludesProxy = to.path.includes('/api/v1/environments/proxy/') ||
                               to.fullPath.includes('/api/v1/environments/proxy/') ||
                               (to.href && to.href.includes('/api/v1/environments/proxy/'));
  
  // 如果referrer或当前URL包含代理路径，说明这是来自代理iframe的导航，应该立即取消Vue Router处理
  // 或者如果目标路径本身包含代理路径，也应该取消处理
  if (isRefererProxy || isCurrentUrlProxy || toPathIncludesProxy) {
    console.log('[路由守卫] ⚠️ [最早检查] 检测到来自代理iframe的导航，立即取消Vue Router处理:', {
      path: to.path,
      fullPath: to.fullPath,
      href: to.href,
      referrer: referer,
      currentUrl: currentUrl,
      isRefererProxy: isRefererProxy,
      isCurrentUrlProxy: isCurrentUrlProxy,
      toPathIncludesProxy: toPathIncludesProxy,
      isInIframe: isInIframe,
      timestamp: new Date().toISOString()
    });
    next(false) // 取消导航，让浏览器处理
    return
  }
  
  // 调试日志：记录所有路由导航
  const isProxyUrl = currentUrl.includes('/api/v1/environments/proxy/');
  
  // 详细日志：检查所有可能的iframe相关标识
  const hasIframeInPage = typeof document !== 'undefined' && !!document.querySelector('iframe[src*="environments/proxy"]');
  const iframeSrcs = typeof document !== 'undefined' 
    ? Array.from(document.querySelectorAll('iframe')).map(iframe => (iframe as HTMLIFrameElement).src)
    : [];
  
  console.log('[路由守卫] 路由导航:', {
    path: to.path,
    fullPath: to.fullPath,
    href: to.href,
    matched: to.matched.length,
    name: to.name,
    isInIframe: isInIframe,
    windowTop: typeof window !== 'undefined' ? window.top : 'undefined',
    windowSelf: typeof window !== 'undefined' ? window.self : 'undefined',
    referer: referer,
    isRefererProxy: isRefererProxy,
    currentUrl: currentUrl,
    isProxyUrl: isProxyUrl,
    hasIframeInPage: hasIframeInPage,
    iframeSrcs: iframeSrcs
  });
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 慧学`
  } else {
    document.title = '慧学'
  }

  const userStore = useUserStore()
  
  // API路径不应该被Vue Router处理（这些是HTTP请求，不是路由导航）
  // 包括代理端点和其他API端点
  // 注意：iframe的src是相对路径时，浏览器会将其解析为相对于当前页面的路径
  // 但iframe的请求不应该通过Vue Router，所以我们需要在这里阻止路由处理
  // 检查to.path和to.fullPath，因为hash模式下路径可能不同
  // 同时检查to.matched，如果路径没有匹配到任何路由，也应该允许继续
  // 还要检查to.href，因为iframe内的导航可能会触发路由守卫
  // 关键修复：检查to.fullPath和to.href是否包含代理路径
  const isApiPath = to.path.startsWith('/api/') || 
                    to.fullPath.startsWith('/api/') || 
                    to.href?.includes('/api/') ||
                    to.fullPath.includes('/api/v1/environments/proxy/') ||
                    to.href?.includes('/api/v1/environments/proxy/') ||
                    (to.matched.length === 0 && to.path.includes('/api/')) ||
                    // 检查是否是iframe内的导航（通过检查referrer或window.top）
                    (typeof window !== 'undefined' && window.top !== window.self && to.path.includes('/api/')) ||
                    // 关键修复：如果目标路径包含代理路径，也应该被视为API路径
                    to.path.includes('/api/v1/environments/proxy/');
  
  console.log('[路由守卫] API路径检查:', {
    path: to.path,
    fullPath: to.fullPath,
    href: to.href,
    pathStartsWithApi: to.path.startsWith('/api/'),
    fullPathStartsWithApi: to.fullPath.startsWith('/api/'),
    hrefIncludesApi: to.href?.includes('/api/'),
    matchedLength: to.matched.length,
    pathIncludesApi: to.path.includes('/api/'),
    isInIframe: typeof window !== 'undefined' && window.top !== window.self,
    isApiPath: isApiPath
  });
  
  if (isApiPath) {
    // 对于API路径，直接调用next()允许继续，但不执行后续的认证检查
    // 这主要是为了防止iframe的API请求被路由守卫拦截
    console.log('[路由守卫] ✅ 检测到API路径，跳过路由处理:', to.path, to.fullPath, 'href:', to.href);
    next()
    return
  }
  
  // 检查是否是iframe内的导航（通过检查window.top !== window.self）
  // 注意：代理iframe的检查已经在最开始执行过了，这里只检查非代理的iframe导航
  const isInIframeContext = typeof window !== 'undefined' && window.top !== window.self;
  
  console.log('[路由守卫] iframe检查:', {
    isInIframe: isInIframeContext,
    matchedLength: to.matched.length,
    path: to.path,
    fullPath: to.fullPath,
    href: to.href,
    windowLocation: typeof window !== 'undefined' ? window.location.href : 'undefined',
    documentReferrer: referer,
    isRefererProxy: isRefererProxy,
    isCurrentUrlProxy: isCurrentUrlProxy
  });
  
  // 如果是在iframe内，但不是代理iframe（代理iframe已经在最开始检查过了），也应该取消Vue Router处理
  if (isInIframeContext && !isRefererProxy && !isCurrentUrlProxy) {
    // 例外：允许 /designer/ 相关的路由在 iframe 内执行 Vue Router 导航
    if (to.path.startsWith('/designer/')) {
        console.log('[路由守卫] 允许 iframe 内的 /designer/ 导航:', to.path);
    } else {
        // 这是iframe内的导航，但不是代理iframe
        // 如果路径没有匹配到任何路由，可能是iframe内的页面导航，应该允许继续
        if (to.matched.length === 0) {
          console.log('[路由守卫] ⚠️ 检测到iframe内的导航（非代理），路径未匹配到路由，取消Vue Router处理:', to.path, to.fullPath);
          next(false) // 取消导航，让浏览器处理
          return
        }
        // 如果路径匹配到了路由，但这是iframe内的导航，也应该取消Vue Router处理
        // 因为iframe内的导航不应该触发父页面的路由导航
        console.log('[路由守卫] ⚠️ 检测到iframe内的导航（非代理），路径匹配到路由，取消Vue Router处理:', to.path, to.fullPath);
        next(false) // 取消导航，让浏览器处理
        return
    }
  }
  
  // 关键修复：如果当前URL包含 /login 且 referrer 包含代理路径，也应该取消Vue Router处理
  // 这可以防止 iframe 内的登录页面导航被 Vue Router 拦截
  if (currentUrl.includes('/login') && isRefererProxy) {
    console.log('[路由守卫] ⚠️ 检测到来自代理iframe的登录页面导航（通过currentUrl检查），取消Vue Router处理:', {
      path: to.path,
      fullPath: to.fullPath,
      currentUrl: currentUrl,
      referrer: referer
    });
    next(false) // 取消导航，让浏览器处理
    return
  }
  
  // 登录页面不需要权限检查
  // 但是，如果这是来自代理iframe的导航，应该取消Vue Router处理
  if (to.path === '/login') {
    // 检查是否是来自代理iframe的导航
    const referrerForLoginCheck = typeof document !== 'undefined' ? document.referrer : '';
    const isFromProxyIframeForLogin = referrerForLoginCheck.includes('/api/v1/environments/proxy/');
    const currentUrlForLoginCheck = typeof window !== 'undefined' ? window.location.href : '';
    const isCurrentUrlProxyForLogin = currentUrlForLoginCheck.includes('/api/v1/environments/proxy/');
    
    // 关键修复：如果referrer包含代理路径，或者当前URL包含代理路径，或者查询参数中包含代理URL，都应该取消Vue Router处理
    const queryRedirect = to.query?.redirect || to.query?.next || '';
    const isRedirectToProxy = typeof queryRedirect === 'string' && queryRedirect.includes('/api/v1/environments/proxy/');
    
    // 关键修复：检查 to.fullPath 和 to.href 是否包含代理路径
    const toPathIncludesProxyForLogin = to.path.includes('/api/v1/environments/proxy/') ||
                                         to.fullPath.includes('/api/v1/environments/proxy/') ||
                                         (to.href && to.href.includes('/api/v1/environments/proxy/'));
    
    if (isFromProxyIframeForLogin || isCurrentUrlProxyForLogin || isRedirectToProxy || toPathIncludesProxyForLogin) {
      console.log('[路由守卫] ⚠️ 检测到来自代理iframe的登录页面导航，取消Vue Router处理:', {
        path: to.path,
        fullPath: to.fullPath,
        href: to.href,
        referrer: referrerForLoginCheck,
        currentUrl: currentUrlForLoginCheck,
        queryRedirect: queryRedirect,
        isRedirectToProxy: isRedirectToProxy,
        toPathIncludesProxyForLogin: toPathIncludesProxyForLogin
      });
      next(false) // 取消导航，让浏览器处理
      return
    }
    
    next()
    return
  }
  
  // 重定向页面不需要权限检查
  if (to.path === '/redirect' || to.path.startsWith('/redirect/')) {
    next()
    return
  }
  
  // 检查页面是否需要登录权限
  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      
      // 关键修复：再次检查是否是来自代理iframe的导航（在认证检查中）
      const refererForAuth = typeof document !== 'undefined' ? document.referrer : '';
      const isRefererProxyForAuth = refererForAuth.includes('/api/v1/environments/proxy/');
      const currentUrlForAuth = typeof window !== 'undefined' ? window.location.href : '';
      const isCurrentUrlProxyForAuth = currentUrlForAuth.includes('/api/v1/environments/proxy/');
      
      if (isRefererProxyForAuth || isCurrentUrlProxyForAuth) {
        console.log('[路由守卫] ⚠️ [认证检查] 检测到来自代理iframe的导航，立即取消Vue Router处理:', {
          path: to.path,
          fullPath: to.fullPath,
          referrer: refererForAuth,
          currentUrl: currentUrlForAuth,
          isRefererProxy: isRefererProxyForAuth,
          isCurrentUrlProxy: isCurrentUrlProxyForAuth,
          timestamp: new Date().toISOString()
        });
        next(false) // 取消导航，让浏览器处理
        return
      }
      
      // 重定向到登录页面
      // 但是，如果这是iframe内的导航（通过检查window.top !== window.self），不应该重定向
      // 因为iframe内的导航不应该触发Vue Router的路由守卫
      const isInIframeAuth = typeof window !== 'undefined' && window.top !== window.self;
      console.log('[路由守卫] 认证检查:', {
        isLoggedIn: userStore.isLoggedIn,
        isInIframe: isInIframeAuth,
        path: to.path,
        fullPath: to.fullPath,
        requiresAuth: to.meta.requiresAuth
      });
      
      if (isInIframeAuth) {
        // 这是iframe内的导航，不应该被Vue Router处理
        console.log('[路由守卫] ⚠️ 检测到iframe内的导航（requiresAuth），取消Vue Router处理:', to.path, to.fullPath);
        next(false) // 取消导航，让浏览器处理
        return
      }
      
      console.log('[路由守卫] ❌ 未登录，重定向到登录页面:', to.path, to.fullPath);
      next({
        path: '/login',
        query: { redirect: to.fullPath } // 将目标路由的完整路径传递给登录页面
      })
      return
    }
    // 用户已登录，继续导航
  }
  
  // [SEC-FIX] 全局检查：阻止非管理员访问 /admin/* 路径
  // 这是一个安全防护，确保即使路由配置中忘记添加 requiresAdmin，也能阻止非管理员访问
  if (to.path.startsWith('/admin')) {
    const storedUserInfoForAdmin = localStorage.getItem('userInfo');
    let adminCheckRole = 'student';

    if (storedUserInfoForAdmin) {
      try {
        const parsed = JSON.parse(storedUserInfoForAdmin);
        adminCheckRole = parsed.role || 'student';
      } catch (e) {
        console.error('[SEC-FIX] 解析用户信息失败:', e);
      }
    }

    if (adminCheckRole !== 'admin' && adminCheckRole !== '管理员') {
      console.log('[SEC-FIX] 非管理员尝试访问管理后台，已阻止. 当前角色:', adminCheckRole, '路径:', to.path);
      // 动态导入message提示
      if (typeof window !== 'undefined') {
        import('ant-design-vue').then(({ message }) => {
          message.error('您没有权限访问管理后台');
        }).catch(() => {});
      }
      next({ path: '/', replace: true });
      return;
    }
  }

  // 检查管理员权限（针对明确标记 requiresAdmin 的路由）
  if (to.meta.requiresAdmin) {
    // 从localStorage检查用户角色，避免异步初始化问题
    const storedUserInfo = localStorage.getItem('userInfo');
    let userRole = 'student'; // 默认角色

    if (storedUserInfo) {
      try {
        const parsed = JSON.parse(storedUserInfo);
        userRole = parsed.role || 'student';
      } catch (e) {
        console.error('解析用户信息失败:', e);
      }
    }

    // 简化权限检查：只检查用户角色
    if (userRole !== 'admin') {
      // 无管理员权限，重定向到首页
      console.log('User is not admin, redirecting to home. Current role:', userRole);
      next({ path: '/' })
      return
    }
  }
  
  // [SEC-03修复] 检查教师权限
  if (to.meta.requiresTeacher) {
    // 从localStorage检查用户角色
    const storedUserInfo = localStorage.getItem('userInfo');
    let userRole = 'student'; // 默认角色

    if (storedUserInfo) {
      try {
        const parsed = JSON.parse(storedUserInfo);
        userRole = parsed.role || 'student';
      } catch (e) {
        console.error('[SEC-03] 解析用户信息失败:', e);
      }
    }

    // 检查是否为教师或管理员
    const isTeacherOrAdmin = ['teacher', '教师', 'admin', '管理员'].includes(userRole.toLowerCase());
    
    if (!isTeacherOrAdmin) {
      // 无教师权限，显示错误提示并重定向
      console.log('[SEC-03] 用户无教师权限，拒绝访问. 当前角色:', userRole);
      // 使用alert或message提示（如果可用）
      if (typeof window !== 'undefined') {
        // 动态导入message避免初始化问题
        import('ant-design-vue').then(({ message }) => {
          message.error('您没有权限访问该页面');
        }).catch(() => {
          alert('您没有权限访问该页面');
        });
      }
      next({ path: '/', replace: true })  // 使用replace避免浏览器后退按钮问题
      return
    }
    console.log('[SEC-03] 教师权限验证通过. 角色:', userRole);
  }
  
  // 暂时移除复杂的路由权限检查
  // if (to.path in routePermissions) {
  //   const requiredPermissions = routePermissions[to.path]
  //   const { hasAnyPermission } = usePermission()
  //   if (!hasAnyPermission(requiredPermissions)) {
  //     console.log('User lacks required permissions');
  //     next({ path: '/' })
  //     return
  //   }
  // }
  
  next()
})

export default router 
