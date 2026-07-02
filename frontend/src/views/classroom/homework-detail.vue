<template>
  <div class="homework-detail-page">
    <a-spin :spinning="loading" tip="加载中...">
      <div v-if="currentStudent" class="content-container">
        <div class="back-link">
          <a-button type="link" @click="goBack">
            <template #icon><arrow-left-outlined /></template>
            返回作业列表
          </a-button>
        </div>

        <!-- 实训名称 -->
        <div v-if="courseName" class="training-name-header">
          <h2>{{ courseName }}</h2>
        </div>

        <div class="homework-header">
          <div class="student-info">
            <a-avatar :size="40" :src="currentStudent.avatar" style="margin-right: 12px;">
              <template #icon><user-outlined /></template>
            </a-avatar>
            <h1 class="student-name">{{ currentStudent.name }} 的作业</h1>
            <a-tag :color="getStatusColor(currentStudent.status)">
              {{ getStatusText(currentStudent.status) }}
            </a-tag>
            <a-tag :color="currentStudent.commentStatus === 'commented' ? 'green' : 'orange'">
              {{ currentStudent.commentStatus === 'commented' ? '已点评' : '未点评' }}
            </a-tag>
            <template v-if="currentStudent.isExcellent">
              <a-tag color="gold">
                <template #icon><trophy-outlined /></template>
                优秀作业
              </a-tag>
            </template>
          </div>
          <div class="action-buttons">
            <template v-if="currentStudent.status === 'submitted' || currentStudent.status === 'late_submitted'">
              <a-button 
                type="primary" 
                @click="openCommentModal"
                :disabled="submittingComment"
              >
                {{ currentStudent.commentStatus === 'commented' ? '修改点评' : '点评作业' }}
              </a-button>
              <template v-if="currentStudent.commentStatus === 'commented'">
                <a-button 
                  v-if="!currentStudent.isExcellent" 
                  type="primary"
                  @click="markAsExcellent"
                >
                  <template #icon><star-outlined /></template>
                  评为优秀作业
                </a-button>
                <a-button 
                  v-else
                  danger
                  @click="removeExcellent"
                >
                  <template #icon><stop-outlined /></template>
                  取消优秀标记
                </a-button>
              </template>
            </template>
          </div>
        </div>

        <div class="submission-info">
          <a-descriptions bordered :column="{ xxl: 4, xl: 3, lg: 3, md: 3, sm: 2, xs: 1 }">
            <a-descriptions-item label="学号">{{ currentStudent.studentId }}</a-descriptions-item>
            <a-descriptions-item label="开始时间">{{ currentStudent.startedAt ? formatDateTime(currentStudent.startedAt) : '-' }}</a-descriptions-item>
            <a-descriptions-item label="提交时间">{{ currentStudent.submittedAt ? formatDateTime(currentStudent.submittedAt) : '-' }}</a-descriptions-item>
            <a-descriptions-item label="成绩">{{ currentStudent.score !== null ? currentStudent.score : '-' }}</a-descriptions-item>
          </a-descriptions>
        </div>

        <a-row :gutter="16" class="homework-content">
          <a-col :span="12" class="student-list-container">
            <a-card title="学生列表" class="student-list-card">
              <template #extra>
                <a-input-search 
                  v-model:value="searchText" 
                  placeholder="搜索学生姓名或学号" 
                  style="width: 200px"
                  @search="onSearch"
                />
              </template>
              <div class="student-list">
                <a-list 
                  size="small"
                  :data-source="filteredStudents"
                  :loading="loading"
                >
                  <template #renderItem="{ item }">
                    <a-list-item
                      :class="{ 'selected-student': item.id === currentStudent.id }"
                      @click="selectStudent(item)"
                    >
                      <a-list-item-meta>
                        <template #avatar>
                          <a-badge :dot="isPendingReview(item)" :offset="[-2, 2]">
                            <a-avatar :size="36" :src="item.avatar">
                              <template #icon><user-outlined /></template>
                            </a-avatar>
                          </a-badge>
                        </template>
                        <template #title>
                          <div class="student-list-item">
                            <span class="student-name">{{ item.name }}</span>
                            <div class="student-tags">
                              <a-tag :color="getReviewStatusColor(item)" size="small">
                                {{ getReviewStatusText(item) }}
                              </a-tag>
                              <a-tag v-if="item.isExcellent" color="gold" size="small">
                                优秀
                              </a-tag>
                            </div>
                          </div>
                        </template>
                        <template #description>
                          <span class="student-id">{{ item.studentId }}</span>
                          <span v-if="item.submittedAt" class="submit-time">
                            提交于: {{ formatDate(item.submittedAt) }}
                          </span>
                        </template>
                      </a-list-item-meta>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
            </a-card>
          </a-col>
          <a-col :span="12" class="homework-detail-container">
            <a-card title="作业内容" class="homework-detail-card">
              <template #extra>
                <a-radio-group v-model:value="activeTab" button-style="solid">
                  <a-radio-button value="design">设计文件</a-radio-button>
                  <a-radio-button value="report">实验报告</a-radio-button>
                </a-radio-group>
              </template>
              <div class="homework-viewer">
                <!-- BI Submission Viewer -->
                <div v-if="isBiSubmission" class="bi-viewer" style="height: 600px; width: 100%;">
                   <BiDesigner 
                      v-if="courseId"
                      :trainingId="courseId" 
                      :classroomId="classroomId"
                      :readOnly="true"
                      :snapshot="snapshotData"
                   />
                </div>

                <template v-else-if="activeTab === 'design'">
                  <div v-if="hasDesignFile" class="design-file-viewer">
                    <img :src="designFile?.previewUrl" alt="设计文件预览" class="preview-image" v-if="designFile?.previewUrl" />
                    <div class="file-info">
                      <a-descriptions size="small" :column="1" bordered>
                        <a-descriptions-item label="文件名">{{ designFile?.name || '-' }}</a-descriptions-item>
                        <a-descriptions-item label="大小">{{ designFile ? formatFileSize(designFile.size) : '-' }}</a-descriptions-item>
                        <a-descriptions-item label="上传时间">{{ designFile ? formatDateTime(designFile.createdAt) : '-' }}</a-descriptions-item>
                      </a-descriptions>
                      <a-button type="primary" style="margin-top: 16px" @click="downloadDesignFile">
                        <template #icon><download-outlined /></template>
                        下载设计文件
                      </a-button>
                    </div>
                  </div>
                  <a-empty v-else description="暂无设计文件" />
                </template>
                <template v-else-if="activeTab === 'report'">
                  <div v-if="hasReport" class="report-viewer">
                    <a-typography>
                      <a-typography-title :level="4">{{ experimentReport?.title || '实验报告' }}</a-typography-title>
                      <a-typography-paragraph>
                        <div class="report-content" v-html="experimentReport?.content || '<p>报告内容加载中...</p>'"></div>
                      </a-typography-paragraph>
                    </a-typography>
                    <div class="file-actions">
                      <a-button type="primary" @click="downloadReport">
                        <template #icon><download-outlined /></template>
                        导出报告
                      </a-button>
                    </div>
                  </div>
                  <a-empty v-else description="暂无实验报告" />
                </template>
              </div>
            </a-card>
          </a-col>
        </a-row>

        <a-card v-if="currentStudent.commentStatus === 'commented'" title="教师点评" class="comment-card">
          <div class="comment-content">
            <a-alert 
              :message="`评分：${currentStudent.score} 分`"
              :type="getScoreLevel(currentStudent.score || 0)"
              show-icon
              style="margin-bottom: 16px"
            />
            <a-typography>
              <a-typography-paragraph>
                {{ currentStudent.comment || '暂无点评内容' }}
              </a-typography-paragraph>
            </a-typography>
          </div>
        </a-card>
      </div>
      <a-result v-else-if="!loading" status="404" title="找不到学生作业" sub-title="您访问的作业不存在或已被删除">
        <template #extra>
          <a-button type="primary" @click="goBack">返回作业列表</a-button>
        </template>
      </a-result>
    </a-spin>

    <!-- 点评模态框 -->
    <a-modal
      v-model:open="commentModalVisible"
      :title="`为 ${currentStudent?.name || ''} 评分点评`"
      @ok="submitComment"
      :confirm-loading="submittingComment"
      width="600px"
    >
      <a-form layout="vertical">
        <a-form-item label="分数">
          <div style="display: flex; gap: 8px;">
            <a-input-number 
              v-model:value="commentForm.score" 
              :min="0" 
              :max="100" 
              style="flex: 1" 
            />
            <a-button 
              type="primary"
              @click="getAISuggestion"
              :loading="aiLoading"
            >
              <template #icon><bulb-outlined /></template>
              AI建议
            </a-button>
          </div>
        </a-form-item>
        
        <!-- AI建议展示区域 -->
        <a-alert 
          v-if="aiSuggestion"
          type="info"
          show-icon
          closable
          @close="aiSuggestion = null"
          style="margin-bottom: 16px;"
        >
          <template #message>AI评分建议</template>
          <template #description>
            <div style="margin-bottom: 8px;">
              <strong>建议分数：</strong>{{ aiSuggestion.score }}分
            </div>
            <div style="margin-bottom: 8px;">
              <strong>评语：</strong>{{ aiSuggestion.comment }}
            </div>
            <div v-if="aiSuggestion.suggestions && aiSuggestion.suggestions.length > 0">
              <strong>改进建议：</strong>
              <ul style="margin: 4px 0; padding-left: 20px;">
                <li v-for="(suggestion, index) in aiSuggestion.suggestions" :key="index">
                  {{ suggestion }}
                </li>
              </ul>
            </div>
            <a-button 
              type="link" 
              size="small" 
              @click="applyAISuggestion"
              style="padding: 0; margin-top: 8px;"
            >
              采用AI建议
            </a-button>
          </template>
        </a-alert>
        
        <a-form-item label="点评意见">
          <a-textarea 
            v-model:value="commentForm.comment" 
            :rows="4" 
            placeholder="请输入点评意见" 
          />
        </a-form-item>
        <a-form-item>
          <a-checkbox v-model:checked="commentForm.isExcellent">
            设为优秀作业（可供其他学生参考学习）
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import dayjs from 'dayjs';
import {
  ArrowLeftOutlined,
  StarOutlined,
  TrophyOutlined,
  StopOutlined,
  DownloadOutlined,
  BulbOutlined,
  UserOutlined
} from '@ant-design/icons-vue';
import axios from 'axios';
import request from '@/utils/request'; // Import request utility
import { useClassroomStore } from '../../stores/classroom';
import { useUserStore } from '@/stores/user';
import BiDesigner from '@/components/BiDesigner.vue'; // Import BiDesigner

interface TrainingStudentGrade {
  id: string;
  name: string;
  studentId: string;
  status: 'not_started' | 'not_submitted' | 'submitted' | 'late_submitted';
  startedAt: string | null;
  submittedAt: string | null;
  score: number | null;
  commentStatus: 'not_commented' | 'commented';
  comment: string;
  isExcellent: boolean;
}

interface DesignFile {
  id: string;
  name: string;
  url: string;
  size: number;
  type: string;
  createdAt: string;
  previewUrl?: string; // Added for preview
}

interface Report {
  id: string;
  title: string;
  content: string;
  createdAt: string;
}

const route = useRoute();
const router = useRouter();
const classroomStore = useClassroomStore();
const userStore = useUserStore();

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再查看作业详情');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 加载状态
const loading = ref(false);
const submittingComment = ref(false);

// 当前课堂ID和课程ID
const classroomId = computed(() => route.params.classroomId as string);
const courseId = computed(() => route.params.courseId as string);
const studentId = computed(() => route.params.studentId as string);
const courseType = computed(() => route.query.courseType as string || '');
const courseName = computed(() => route.query.courseName as string || '');

// 当前学生和所有学生列表
const currentStudent = ref<TrainingStudentGrade | null>(null);
const students = ref<TrainingStudentGrade[]>([]);

// 搜索
const searchText = ref('');
const filteredStudents = computed(() => {
  if (!searchText.value) return students.value;
  
  const lowerSearchText = searchText.value.toLowerCase();
  return students.value.filter(student => 
    student.name.toLowerCase().includes(lowerSearchText) || 
    student.studentId.toLowerCase().includes(lowerSearchText)
  );
});

// 查看作业相关状态
const activeTab = ref('design');
const hasDesignFile = computed(() => {
  // 实际项目中应该根据当前学生作业情况判断
  return currentStudent.value && 
    (currentStudent.value.status === 'submitted' || currentStudent.value.status === 'late_submitted');
});
const hasReport = computed(() => {
  // 实际项目中应该根据当前学生作业情况判断
  return currentStudent.value && 
    (currentStudent.value.status === 'submitted' || currentStudent.value.status === 'late_submitted');
});

// 设计文件和实验报告数据
const designFile = ref<DesignFile | null>(null);
const experimentReport = ref<Report | null>(null);

// BI Submission State
const isBiSubmission = ref(false);
const snapshotData = ref(null);

// 获取学生提交的文件
const fetchStudentSubmission = async (studentId: string) => {
  try {
    isBiSubmission.value = false;
    snapshotData.value = null;
    designFile.value = null;
    experimentReport.value = null;

    // Try to fetch BI submission first
    try {
       // Use token for authentication
       const response = await request.get(`/api/v1/trainings/submissions/${studentId}`);
       if (response.code === '0000' && response.data) {
          const data = response.data;
          if (data.submission_snapshot) {
              isBiSubmission.value = true;
              snapshotData.value = data.submission_snapshot;
              // If BI submission found, we might not need to load others, or we can load them as supplementary
              return; 
          }
       }
    } catch (e) {
       console.warn("Not a BI submission or fetch failed:", e);
    }

    // TODO: 调用实际的API获取学生提交的文件
    // const response = await getStudentSubmission(route.params.homeworkId, studentId);
    // if (response.code === '0000') {
    //   designFile.value = response.data.designFile;
    //   experimentReport.value = response.data.report;
    // }
    
    // 暂时使用默认数据 (如果未找到BI提交)
    designFile.value = {
      id: '1',
      name: '市场品质分析设计.fig',
      url: '/v1/files/design.fig',
      size: 5.4 * 1024 * 1024,
      type: 'application/fig',
      createdAt: dayjs().subtract(2, 'day').format('YYYY-MM-DD HH:mm:ss'),
      previewUrl: '' // 预览不可用时留空
    };
    
    experimentReport.value = {
      id: '1',
      title: '企业经营分析项目报告',
      content: '<h3>项目报告</h3><p>报告内容加载中...</p>',
      createdAt: dayjs().subtract(2, 'day').format('YYYY-MM-DD HH:mm:ss')
    };
  } catch (error) {
    console.error('获取学生提交失败:', error);
  }
};

// 评分和点评相关状态
const commentModalVisible = ref(false);
const commentForm = reactive({
  score: 0,
  comment: '',
  isExcellent: false
});

// AI助手相关状态
const aiLoading = ref(false);
const aiSuggestion = ref<{
  score: number;
  comment: string;
  suggestions: string[];
} | null>(null);

// 打开点评模态框
const openCommentModal = () => {
  if (!currentStudent.value) return;
  
  commentForm.score = currentStudent.value.score ?? 0;
  commentForm.comment = currentStudent.value.comment;
  commentForm.isExcellent = currentStudent.value.isExcellent;
  commentModalVisible.value = true;
};

// 获取AI评分建议
const getAISuggestion = async () => {
  if (!currentStudent.value) return;
  
  aiLoading.value = true;
  try {
    // 获取作业内容（这里假设作业内容在currentStudent中）
    const studentAnswer = currentStudent.value.comment || '学生提交的作业内容';
    
    // 调用AI API
    const response = await axios.post('/v1/ai/grade', {
      training_id: route.params.homeworkId,  // 使用作业ID
      student_answer: studentAnswer,
      user_id: requireCurrentUserId()
    });
    
    if (response.data) {
      aiSuggestion.value = response.data;
      message.success('AI建议已生成');
    }
  } catch (error: any) {
    console.error('获取AI建议失败:', error);
    message.error(error.response?.data?.detail || 'AI服务暂时不可用');
  } finally {
    aiLoading.value = false;
  }
};

// 采用AI建议
const applyAISuggestion = () => {
  if (!aiSuggestion.value) return;
  
  commentForm.score = aiSuggestion.value.score;
  commentForm.comment = aiSuggestion.value.comment;
  
  // 如果有改进建议，追加到评语中
  if (aiSuggestion.value.suggestions && aiSuggestion.value.suggestions.length > 0) {
    commentForm.comment += '\n\n改进建议：\n' + aiSuggestion.value.suggestions.join('\n');
  }
  
  message.success('已采用AI建议');
};

// 提交点评
const submitComment = async () => {
  if (!currentStudent.value) return;
  
  submittingComment.value = true;
  
  try {
    // Backend expects query parameters for this POST request
    const teacherId = userStore.userInfo?.user_id || userStore.userId;
    
    const queryString = new URLSearchParams({
        score: commentForm.score.toString(),
        comment: commentForm.comment || '',
        is_excellent: String(commentForm.isExcellent),
        teacher_id: String(teacherId)
    }).toString();

    const response = await request.post(`/api/v1/training-submissions/${currentStudent.value.id}/review?${queryString}`);

    if (response.code === '0000') {
      currentStudent.value.score = commentForm.score;
      currentStudent.value.comment = commentForm.comment;
      currentStudent.value.isExcellent = commentForm.isExcellent;
      currentStudent.value.commentStatus = 'commented';
      
      message.success('点评提交成功');
      commentModalVisible.value = false;
    } else {
      message.error(response.message || '点评提交失败');
    }
  } catch (error: any) {
    console.error('点评提交失败:', error);
    message.error(error.message || '点评提交失败');
  } finally {
    submittingComment.value = false;
  }
};

// 标记为优秀作业
const markAsExcellent = () => {
  if (!currentStudent.value) return;
  
  currentStudent.value.isExcellent = true;
  message.success(`已将 ${currentStudent.value.name} 的作业设为优秀作业`);
};

// 移除优秀作业标记
const removeExcellent = () => {
  if (!currentStudent.value) return;
  
  currentStudent.value.isExcellent = false;
  message.success(`已取消 ${currentStudent.value.name} 作业的优秀标记`);
};

// 选择学生
const selectStudent = (student: TrainingStudentGrade) => {
  currentStudent.value = student;
  // 加载学生提交的作业内容
  if (student.id) {
    fetchStudentSubmission(student.id);
  }
};

// 下载设计文件
const downloadDesignFile = () => {
  if (!designFile.value) return;
  window.open(designFile.value.url, '_blank');
};

// 下载实验报告
const downloadReport = () => {
  if (!experimentReport.value) return;
  window.open(experimentReport.value.content, '_blank'); // Assuming content is the URL for download
};

// 搜索
const onSearch = () => {
  // 这里不需要额外操作，computed属性会自动处理
};

// 返回上一页
const goBack = () => {
  router.push(`/classroom/${classroomId.value}/course/${courseId.value}/grades`);
};

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'not_started': return '未开始';
    case 'not_submitted': return '未提交';
    case 'submitted': return '已提交';
    case 'late_submitted': return '已补交';
    default: return '未知状态';
  }
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  switch (status) {
    case 'not_started': return 'default';
    case 'not_submitted': return 'blue';
    case 'submitted': return 'green';
    case 'late_submitted': return 'orange';
    default: return 'default';
  }
};

// 判断是否待评（已提交但未点评）- 用于红点标记
const isPendingReview = (item: TrainingStudentGrade) => {
  const hasSubmitted = item.status === 'submitted' || item.status === 'late_submitted';
  const notReviewed = item.commentStatus !== 'commented';
  return hasSubmitted && notReviewed;
};

// 获取评阅状态文本（未交/待评/已评）
const getReviewStatusText = (item: TrainingStudentGrade) => {
  if (item.status === 'not_started' || item.status === 'not_submitted') {
    return '未交';
  }
  if (item.commentStatus === 'commented') {
    return '已评';
  }
  return '待评';
};

// 获取评阅状态颜色
const getReviewStatusColor = (item: TrainingStudentGrade) => {
  if (item.status === 'not_started' || item.status === 'not_submitted') {
    return 'default';  // 灰色 - 未交
  }
  if (item.commentStatus === 'commented') {
    return 'green';    // 绿色 - 已评
  }
  return 'orange';     // 橙色 - 待评
};

// 获取分数等级
const getScoreLevel = (score: number): 'success' | 'warning' | 'error' => {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'error';
};

// 格式化日期
const formatDate = (dateStr?: string | null) => {
  if (!dateStr) return '-';
  return dayjs(dateStr).format('YYYY-MM-DD');
};

// 格式化日期时间
const formatDateTime = (dateStr: string | null) => {
  if (!dateStr) return '-';
  return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss');
};

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 获取学生作业详情
const fetchHomeworkDetail = async () => {
  loading.value = true;
  
  try {
    // Call real API to get grades (which includes student list)
    const teacherId = userStore.userInfo?.user_id || userStore.userId;
    const params: any = {
        teacher_id: teacherId,
        page: 1,
        page_size: 100
    };
    // 如果是实训课程，传递 course_type 参数
    if (courseType.value) {
        params.course_type = courseType.value;
    }
    const response = await request.get(`/api/v1/classrooms/${classroomId.value}/courses/${courseId.value}/grades`, {
        params
    });

    if (response.code === '0000' && response.data && response.data.grades) {
        // 映射API返回的状态到前端使用的状态值
        const mapStatus = (grade: any): string => {
            // 优先使用提交状态
            if (grade.submissionStatus) {
                const submissionStatusUpper = grade.submissionStatus.toUpperCase();
                if (submissionStatusUpper === 'SUBMITTED') return 'submitted';
                if (submissionStatusUpper === 'LATE_SUBMISSION') return 'late_submitted';
                if (submissionStatusUpper === 'NOT_SUBMITTED') return 'not_submitted';
            }
            // 使用学生状态
            if (grade.status) {
                const statusUpper = grade.status.toUpperCase();
                if (statusUpper === 'COMPLETED' || statusUpper === 'COMPLETED_ON_TIME') return 'submitted';
                if (statusUpper === 'COMPLETED_LATE') return 'late_submitted';
                if (statusUpper === 'NOT_STARTED') return 'not_started';
                if (statusUpper === 'LEARNING') return 'not_submitted';
            }
            return 'not_started';
        };

        const gradeList = response.data.grades.map((grade: any) => ({
            id: grade.id.toString(), // This is progress_id
            name: grade.name,
            studentId: grade.studentId,
            status: mapStatus(grade),
            startedAt: null,
            submittedAt: grade.submittedAt,
            score: grade.score,
            commentStatus: grade.commentStatus,
            comment: '', // API doesn't return comment in list, need fetch detail
            isExcellent: grade.isExcellentWork || false
        }));
        students.value = gradeList;

        // Find current student
        if (studentId.value) {
            const student = gradeList.find((s: any) => s.id === studentId.value);
            if (student) {
                currentStudent.value = student;
                // Fetch full submission details
                await fetchStudentSubmission(student.id);
            } else {
                // Fallback if student not in list (pagination?)
                console.warn(`Student ${studentId.value} not found in list, fetching directly...`);
                await fetchStudentSubmission(studentId.value);
                // Create a temporary student object from submission data
                if (snapshotData.value || designFile.value || experimentReport.value) {
                   // We need basic info which we might not have... 
                   // For now let's hope the list covers it or we fetch profile separately
                }
            }
        } else if (gradeList.length > 0) {
             currentStudent.value = gradeList[0];
             await fetchStudentSubmission(gradeList[0].id);
        }
    } else {
        console.warn("Failed to fetch grades, using mock data");
        // Fallback to mock data... (keep existing mock logic or remove)
    }
    
  } catch (error) {
    console.error('获取作业详情失败:', error);
    message.error('获取作业详情失败');
  } finally {
    loading.value = false;
  }
};

// 组件挂载时获取作业详情
onMounted(() => {
  fetchHomeworkDetail();
});

// 监听学生ID变化，重新加载数据
watch(studentId, (newId) => {
  if (newId) {
    fetchHomeworkDetail();
  }
});
</script>

<style scoped>
.homework-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.content-container {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.back-link {
  margin-bottom: 16px;
}

.training-name-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.training-name-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.homework-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.student-name {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  margin-right: 12px;
  display: inline-block;
}

.student-info {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.submission-info {
  margin-bottom: 24px;
}

.homework-content {
  margin-bottom: 24px;
}

.student-list-container, .homework-detail-container {
  margin-bottom: 24px;
}

.student-list-card, .homework-detail-card, .comment-card {
  height: 100%;
}

.student-list {
  max-height: 400px;
  overflow-y: auto;
}

.student-list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-tags {
  display: flex;
  gap: 4px;
}

.student-id {
  color: rgba(0, 0, 0, 0.45);
  margin-right: 8px;
}

.submit-time {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.selected-student {
  background-color: #e6f7ff;
}

.homework-viewer {
  min-height: 400px;
}

.design-file-viewer {
  display: flex;
  gap: 16px;
}

.report-content {
  min-height: 200px;
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}

.file-info {
  margin-top: 16px;
}

.file-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.comment-card {
  margin-bottom: 24px;
}

.comment-content {
  padding: 8px;
}
</style> 
