<template>
  <div class="learning-stats-tab">
    <a-spin :spinning="loading" tip="加载中...">
      <!-- 操作栏 -->
      <div class="action-bar">
        <div class="selection-info">
          <span v-if="selectedStudentIds.length > 0">
            已选择 {{ selectedStudentIds.length }} 个学生
          </span>
        </div>
        <div class="action-buttons">
          <a-button 
            :disabled="selectedStudentIds.length === 0"
            @click="exportSelected"
          >
            导出所选
          </a-button>
          <a-button type="primary" @click="exportAll">
            导出全部
          </a-button>
        </div>
      </div>

      <!-- 学生统计表格 -->
      <a-table
        v-model:selectedRowKeys="selectedStudentIds"
        :columns="columns"
        :data-source="studentsList"
        :pagination="pagination"
        :loading="loading"
        :row-selection="rowSelection"
        :row-key="(record: any) => record.student_id"
        @change="handleTableChange"
      >
        <!-- 在线状态 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'online_status'">
            <a-badge 
              :status="record.online_status === 'online' ? 'success' : 'default'"
              :text="record.online_status === 'online' ? '在线' : '离线'"
            />
          </template>
          
          <!-- 年级/班级 -->
          <template v-else-if="column.key === 'grade_class'">
            <span>{{ formatGradeClass(record) }}</span>
          </template>
          
          <!-- 实践完成数 -->
          <template v-else-if="column.key === 'practice_completed'">
            <span>{{ record.practice_completed || 0 }}</span>
          </template>
          
          <!-- 实践平均分 -->
          <template v-else-if="column.key === 'practice_average'">
            <span>{{ formatScore(record.practice_average_score) }}</span>
          </template>
          
          <!-- 实训完成数 -->
          <template v-else-if="column.key === 'training_completed'">
            <span>{{ record.training_completed || 0 }}</span>
          </template>
          
          <!-- 实训平均分 -->
          <template v-else-if="column.key === 'training_average'">
            <span>{{ formatScore(record.training_average_score) }}</span>
          </template>
          
          <!-- 课程平均分 -->
          <template v-else-if="column.key === 'course_average'">
            <a-tag :color="getScoreColor(record.course_average_score)">
              {{ formatScore(record.course_average_score) }}
            </a-tag>
          </template>
          
          <!-- 总学习时长 -->
          <template v-else-if="column.key === 'study_hours'">
            <span>{{ formatStudyHours(record.total_study_hours) }}</span>
          </template>
          
          <!-- 查看成绩单 -->
          <template v-else-if="column.key === 'action'">
            <a-button 
              type="link" 
              size="small"
              @click="viewTranscript(record)"
            >
              查看成绩单
            </a-button>
          </template>
        </template>
      </a-table>

      <!-- 统计摘要 -->
      <div class="summary-section" v-if="summary">
        <a-card title="统计摘要" size="small">
          <a-row :gutter="16">
            <a-col :span="4">
              <a-statistic title="总学生数" :value="summary.total_students" />
            </a-col>
            <a-col :span="4">
              <a-statistic title="在线学生" :value="summary.online_students" />
            </a-col>
            <a-col :span="4">
              <a-statistic 
                title="实践平均分" 
                :value="summary.avg_practice_score" 
                :precision="1"
                suffix="分"
              />
            </a-col>
            <a-col :span="4">
              <a-statistic 
                title="实训平均分" 
                :value="summary.avg_training_score" 
                :precision="1"
                suffix="分"
              />
            </a-col>
            <a-col :span="4">
              <a-statistic 
                title="总体平均分" 
                :value="summary.avg_overall_score" 
                :precision="1"
                suffix="分"
              />
            </a-col>
            <a-col :span="4">
              <a-statistic 
                title="在线率" 
                :value="summary.total_students > 0 ? Math.round((summary.online_students / summary.total_students) * 100) : 0" 
                suffix="%"
              />
            </a-col>
          </a-row>
        </a-card>
      </div>
    </a-spin>

    <!-- 学生成绩单弹窗 -->
    <a-modal
      v-model:open="transcriptModalVisible"
      title="学生成绩单"
      width="80%"
      :footer="null"
    >
      <StudentTranscriptView
        v-if="selectedStudent"
        :classroom-id="classroomId"
        :student-id="selectedStudent.student_id"
        :teacher-id="teacherId"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import { useRouter } from 'vue-router';
import { 
  getLearningStudents, 
  exportLearningAnalytics,
  formatStudyHours,
  getOnlineStatusColor 
} from '../../api/analytics';
import type { 
  StudentLearningStats, 
  LearningStudentsResponse,
  ExportAnalyticsRequest 
} from '../../api/analytics';
import StudentTranscriptView from './StudentTranscriptView.vue';

// Props
interface Props {
  classroomId: number;
  teacherId: number;
  courseType: 'required' | 'optional';
  keyword?: string;
}

const props = defineProps<Props>();

const router = useRouter();

// 状态管理
const loading = ref(false);
const studentsList = ref<StudentLearningStats[]>([]);
const summary = ref<LearningStudentsResponse['summary'] | null>(null);
const selectedStudentIds = ref<number[]>([]);
const transcriptModalVisible = ref(false);
const selectedStudent = ref<StudentLearningStats | null>(null);

// 分页
const pagination = ref({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number, range: [number, number]) => 
    `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
});

// 表格列定义
const columns = [
  {
    title: '姓名',
    dataIndex: 'student_name',
    key: 'name',
    width: 100,
    fixed: 'left' as const,
  },
  {
    title: '学号',
    dataIndex: 'student_number',
    key: 'student_number',
    width: 120,
  },
  {
    title: '在线状态',
    key: 'online_status',
    width: 100,
  },
  {
    title: '年级/班级',
    key: 'grade_class',
    width: 120,
  },
  {
    title: '实践完成数',
    key: 'practice_completed',
    width: 100,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.practice_completed || 0) - (b.practice_completed || 0),
  },
  {
    title: '实践平均分',
    key: 'practice_average',
    width: 100,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.practice_average_score || 0) - (b.practice_average_score || 0),
  },
  {
    title: '实训完成数',
    key: 'training_completed',
    width: 100,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.training_completed || 0) - (b.training_completed || 0),
  },
  {
    title: '实训平均分',
    key: 'training_average',
    width: 100,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.training_average_score || 0) - (b.training_average_score || 0),
  },
  {
    title: '课程平均分',
    key: 'course_average',
    width: 110,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.course_average_score || 0) - (b.course_average_score || 0),
  },
  {
    title: '总学习时长',
    key: 'study_hours',
    width: 110,
    sorter: (a: StudentLearningStats, b: StudentLearningStats) => 
      (a.total_study_hours || 0) - (b.total_study_hours || 0),
  },
  {
    title: '操作',
    key: 'action',
    width: 100,
    fixed: 'right' as const,
  },
];

// 行选择配置
const rowSelection = {
  selectedRowKeys: selectedStudentIds,
  onChange: (selectedRowKeys: number[]) => {
    selectedStudentIds.value = selectedRowKeys;
  },
  getCheckboxProps: (record: StudentLearningStats) => ({
    disabled: false,
    name: record.student_name,
  }),
};

// 计算属性
const courseTypeText = computed(() => 
  props.courseType === 'required' ? '必修' : '拓展'
);

// 加载学生数据
async function loadStudentsData() {
  loading.value = true;
  try {
    const response = await getLearningStudents({
      classroom_id: props.classroomId,
      teacher_id: props.teacherId,
      course_type: props.courseType,
      keyword: props.keyword,
      page: pagination.value.current,
      page_size: pagination.value.pageSize,
    });

    if (response.code === '0000') {
      studentsList.value = response.data.list;
      summary.value = response.data.summary;
      pagination.value.total = response.data.meta.total;
    } else {
      message.error(response.message || '获取学生数据失败');
    }
  } catch (error) {
    console.error('获取学生数据失败:', error);
    message.error('获取学生数据失败');
  } finally {
    loading.value = false;
  }
}

// 表格变化处理
function handleTableChange(pag: any) {
  pagination.value.current = pag.current;
  pagination.value.pageSize = pag.pageSize;
  loadStudentsData();
}

// 查看成绩单
function viewTranscript(student: StudentLearningStats) {
  selectedStudent.value = student;
  transcriptModalVisible.value = true;
}

// 导出所选
async function exportSelected() {
  if (selectedStudentIds.value.length === 0) {
    message.warning('请选择要导出的学生');
    return;
  }
  
  await exportData({
    course_type: props.courseType,
    selected_student_ids: selectedStudentIds.value,
    export_format: 'excel'
  });
}

// 导出全部
async function exportAll() {
  await exportData({
    course_type: props.courseType,
    export_format: 'excel'
  });
}

// 执行导出
async function exportData(request: any) {
  try {
    const response = await exportLearningAnalytics({
      classroom_id: props.classroomId,
      teacher_id: props.teacherId,
      course_type: request.course_type,
      student_ids: request.selected_student_ids
    }) as unknown as Blob;

    // Check if it's an error in JSON format masquerading as a blob
    if (response.type === 'application/json') {
      const text = await response.text();
      const errData = JSON.parse(text);
      message.error(errData.detail || errData.message || '导出失败');
      return;
    }

    message.success(`开始导出`);
    
    // Create a download link for the blob
    const url = window.URL.createObjectURL(response);
    const link = document.createElement('a');
    link.href = url;
    const timeStr = new Date().toISOString().replace(/[-:T]/g, '').slice(0,14);
    const typeName = props.courseType === 'required' ? '必修' : '拓展';
    link.setAttribute('download', `学情统计_${typeName}_${timeStr}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
    
  } catch (error) {
    console.error('导出失败:', error);
    message.error('导出失败');
  }
}

// 辅助函数
function formatGradeClass(record: StudentLearningStats): string {
  const parts = [];
  if (record.grade) parts.push(record.grade);
  if (record.class_name) parts.push(record.class_name);
  return parts.join(' / ') || '-';
}

function formatScore(score?: number): string {
  return score !== undefined ? score.toFixed(1) : '-';
}

function getScoreColor(score?: number): string {
  if (!score) return 'default';
  if (score >= 90) return 'green';
  if (score >= 80) return 'blue';
  if (score >= 70) return 'orange';
  if (score >= 60) return 'gold';
  return 'red';
}

// 组件挂载时加载数据
onMounted(() => {
  loadStudentsData();
});

// 监听props变化
watch(() => [props.classroomId, props.teacherId, props.courseType, props.keyword], () => {
  pagination.value.current = 1; // 重置到第一页
  loadStudentsData();
});
</script>

<style lang="less" scoped>
.learning-stats-tab {
  .action-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px;
    background: #f5f5f5;
    border-radius: 4px;
    
    .selection-info {
      color: #666;
      font-size: 14px;
    }
    
    .action-buttons {
      .ant-btn + .ant-btn {
        margin-left: 8px;
      }
    }
  }
  
  .summary-section {
    margin-top: 16px;
  }
  
  :deep(.ant-table-wrapper) {
    .ant-table-thead > tr > th {
      background: #fafafa;
      font-weight: 600;
    }
    
    .ant-table-tbody > tr:hover > td {
      background: #f5f5f5;
    }
  }
}
</style>