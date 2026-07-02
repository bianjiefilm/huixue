<template>
  <div class="submission-detail-page">
    <div class="page-header">
      <a-page-header
        title="作业详情"
        :sub-title="trainingType === 'CODING' ? '查看学生提交的Jupyter Notebook' : '查看学生提交的BI分析结果'"
        @back="() => $router.go(-1)"
      >
        <template #extra>
           <a-space>
             <div class="student-info" v-if="submission">
                <a-tag color="blue">学生ID: {{ submission.student_id }}</a-tag>
                <a-tag :color="statusColor">{{ statusText }}</a-tag>
                <a-tag color="purple">{{ trainingType === 'CODING' ? 'Jupyter实训' : 'BI实训' }}</a-tag>
             </div>
           </a-space>
        </template>
      </a-page-header>
    </div>

    <div class="content-wrapper">
      <a-spin :spinning="loading" tip="正在加载作业数据...">
        <div v-if="error" class="error-message">
          <a-alert type="error" :message="error" show-icon />
        </div>
        
        <!-- Jupyter/CODING Mode -->
        <div v-else-if="submission && trainingType === 'CODING'" class="jupyter-container">
          <div v-if="jupyterUrl" class="jupyter-frame-wrapper">
            <div class="jupyter-header">
              <span>📓 学生Jupyter Notebook (只读模式)</span>
              <a-button size="small" type="link" @click="openJupyterInNewTab">
                在新标签页打开
              </a-button>
            </div>
            <iframe 
              :src="jupyterUrl" 
              class="jupyter-iframe"
              frameborder="0"
              allow="clipboard-read; clipboard-write"
            ></iframe>
          </div>
          <div v-else class="jupyter-placeholder">
            <a-result
              status="info"
              title="Jupyter环境加载中"
              sub-title="正在启动只读Jupyter环境..."
            >
              <template #extra>
                <a-spin />
              </template>
            </a-result>
          </div>
        </div>
        
        <!-- BI Mode -->
        <div v-else-if="submission" class="bi-container">
          <BiDesigner
            v-if="trainingId && biData.length > 0"
            :training-id="trainingId"
            :classroom-id="submission.classroom_id"
            :read-only="true"
            :snapshot="submission.submission_snapshot"
            :initial-data="biData"
          />
          <a-empty v-else description="无法加载实训数据" />
        </div>
      </a-spin>
    </div>
    
    <div class="grading-panel" v-if="submission">
        <a-card title="评分与反馈" size="small">
            <a-form layout="vertical">
                <a-form-item label="得分">
                    <a-input-number v-model:value="gradeForm.score" :min="0" :max="100" />
                </a-form-item>
                <a-form-item label="评语">
                    <a-textarea v-model:value="gradeForm.comment" :rows="4" />
                </a-form-item>
                <a-form-item>
                    <a-button type="primary" :loading="submitting" @click="submitGrade">提交评分</a-button>
                </a-form-item>
            </a-form>
        </a-card>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message } from 'ant-design-vue';
import BiDesigner from '@/components/BiDesigner.vue';
import request from '@/utils/request';
import { queryEnvironmentStatus } from '@/api/training';
import { useUserStore } from '@/stores/user';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const progressId = route.params.progressId;

const loading = ref(true);
const submitting = ref(false);
const error = ref('');
const submission = ref<any>(null);
const trainingId = ref<number | string>('');
const trainingType = ref<string>(''); // CODING, DRAG_DROP, DATA_ANALYSIS
const biData = ref<any[]>([]);
const jupyterUrl = ref<string>('');

const gradeForm = ref({
    score: 0,
    comment: ''
});

const statusColor = computed(() => {
    const status = submission.value?.status;
    if (status === 'SUBMITTED') return 'green';
    if (status === 'LATE_SUBMISSION') return 'orange';
    if (status === 'GRADED') return 'blue';
    return 'default';
});

const statusText = computed(() => {
     const map: Record<string, string> = {
         'NOT_STARTED': '未开始',
         'IN_PROGRESS': '进行中',
         'SUBMITTED': '已提交',
         'LATE_SUBMISSION': '迟交',
         'GRADED': '已评分',
         'PASSED': '通过',
         'FAILED': '未通过'
     };
     return map[submission.value?.status] || submission.value?.status;
});

const fetchSubmission = async () => {
    try {
        loading.value = true;
        // 1. Get Submission Details
        const res = await request.get(`/api/v1/trainings/submissions/${progressId}`);
        if (res.code === '0000') {
            submission.value = res.data;
            trainingId.value = res.data.training_id;
            trainingType.value = res.data.training_type || '';
            
            gradeForm.value.score = res.data.score || 0;
            gradeForm.value.comment = res.data.teacher_feedback || '';

            if (trainingId.value) {
                // 2. Fetch Training Data based on type
                if (trainingType.value === 'CODING') {
                    await fetchJupyterEnvironment(trainingId.value, res.data.classroom_id);
                } else {
                    await fetchTrainingData(trainingId.value, res.data.classroom_id);
                }
            } else {
                error.value = "无法关联到实训项目，请联系管理员";
            }
        } else {
            error.value = res.message || '获取作业失败';
        }
    } catch (e: any) {
        console.error("Fetch error:", e);
        error.value = "加载失败: " + (e.message || '未知错误');
    } finally {
        loading.value = false;
    }
};

// For CODING/Jupyter type
const fetchJupyterEnvironment = async (tId: string | number, cId: string | number) => {
    try {
        // use GET to hit the Cloud SDK orchestration, passing student_id so Teacher views the Student's container
        const studentId = submission.value?.student_id || '';
        const res = await request.get(`/api/v1/jupyter/${tId}/launch?classroom_id=${cId}&student_id=${studentId}`);
        if (res.code === '0000' && res.data) {
            let status = res.data.status;
            let finalUrl = res.data.url;
            
            if (status === 'starting') {
                message.loading({ content: '正在为学生分配环境资源，请稍候...', key: 'jupyterTeacherBoot' });
                
                let retries = 0;
                while (status === 'starting' && retries < 15) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    try {
                        const pollResult = await queryEnvironmentStatus(tId, studentId);
                        if (pollResult.code === '0000' && pollResult.data) {
                            status = pollResult.data.status;
                            if (status === 'running' && pollResult.data.url) {
                                finalUrl = pollResult.data.url;
                                break;
                            }
                        }
                    } catch (e) { console.warn(e); }
                    retries++;
                }
                
                if (status !== 'running') {
                    message.warning({ content: '学生环境启动超时', key: 'jupyterTeacherBoot', duration: 3 });
                } else {
                    message.success({ content: '学生环境已就绪', key: 'jupyterTeacherBoot', duration: 2 });
                }
            }
            
            let url = finalUrl || '';
            // 动态生成 Jupyter URL，根据当前访问的主机名
            const hostname = window.location.hostname;
            const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
            const targetHost = isLocal ? 'localhost' : hostname;

            // 替换所有可能的 Docker 内部地址和 localhost 为目标主机
            url = url.replace(/http:\/\/jupyter:8888/g, `http://${targetHost}:8888`);
            url = url.replace(/http:\/\/localhost:8888/g, `http://${targetHost}:8888`);
            url = url.replace(/http:\/\/127\.0\.0\.1:8888/g, `http://${targetHost}:8888`);

            // 如果没有 URL，使用动态生成的基础 URL
            if (!url) {
                url = `http://${targetHost}:8888/lab?token=huixue_token`;
            }

            jupyterUrl.value = url;
        } else {
            message.warning("无法启动Jupyter环境");
        }
    } catch (e) {
        console.error("Fetch Jupyter environment error", e);
        message.error("Jupyter环境启动失败");
    }
};

// For BI type
const fetchTrainingData = async (tId: string | number, cId: string | number) => {
    try {
        const res = await request.post(`/api/v1/trainings/${tId}/launch?classroom_id=${cId}&training_type=bi`);
        if (res.code === '0000' && res.data) {
            // If data is direct list
            if (Array.isArray(res.data)) {
                 biData.value = res.data;
            } else if (Array.isArray(res.data.data)) {
                 biData.value = res.data.data; // Handle potential wrapper
            } else {
                 console.warn("Unknown data format from launch API", res.data);
            }
        } else {
            message.warning("无法加载实训数据");
        }
    } catch (e) {
        console.error("Fetch training data error", e);
        message.error("实训数据加载失败");
    }
};

const openJupyterInNewTab = () => {
    if (jupyterUrl.value) {
        window.open(jupyterUrl.value, '_blank');
    }
};

const submitGrade = async () => {
    if (!submission.value) return;
    
    // 验证分数
    if (gradeForm.value.score < 0 || gradeForm.value.score > 100) {
        message.warning('分数必须在0-100之间');
        return;
    }

    submitting.value = true;
    try {
        const classroomCourseId = submission.value.classroom_course_id;
        const studentId = submission.value.student_id;
        const teacherId = userStore.userId || userStore.userInfo?.id;
        
        if (!classroomCourseId || !studentId) {
            throw new Error("缺少必要参数(classroomCourseId or studentId)");
        }

        const payload = {
            score: gradeForm.value.score,
            feedback: gradeForm.value.comment,
            is_excellent: false // 可以添加勾选框支持
        };

        const res = await request.post(
            `/api/v1/classroom-courses/${classroomCourseId}/students/${studentId}/grade?teacher_id=${teacherId}`,
            payload
        );
        
        if (res.code === '0000') {
            message.success('评分提交成功');
            // 刷新状态
            fetchSubmission();
        } else {
            message.error(res.message || '评分失败');
        }
        
    } catch (e: any) {
        message.error("评分提交失败: " + e.message);
    } finally {
        submitting.value = false;
    }
};

onMounted(() => {
    fetchSubmission();
});
</script>

<style scoped>
.submission-detail-page {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #f0f2f5;
}

.page-header {
    background: #fff;
    padding: 16px 24px;
    margin-bottom: 16px;
}

.content-wrapper {
    flex: 1;
    margin: 0 24px;
    display: flex;
    flex-direction: column;
    height: calc(100vh - 200px); /* Adjust based on header/footer */
}

.bi-container {
    flex: 1;
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
}

.jupyter-container {
    flex: 1;
    background: #fff;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}

.jupyter-frame-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
}

.jupyter-header {
    padding: 12px 16px;
    background: #f5f5f5;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 500;
}

.jupyter-iframe {
    flex: 1;
    width: 100%;
    min-height: 600px;
    border: none;
}

.jupyter-placeholder {
    padding: 100px 20px;
    text-align: center;
}

.grading-panel {
    position: fixed;
    right: 24px;
    top: 100px;
    width: 300px;
    z-index: 100;
    box-shadow: -2px 0 8px rgba(0,0,0,0.1);
}

.error-message {
    padding: 20px;
}
</style>

