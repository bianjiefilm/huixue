<template>
  <div class="exam-question-generator">
    <!-- 页面标题 -->
    <a-page-header
      title="AI辅助试题生成"
      sub-title="通过上传教学文件，智能生成各类型考试题目"
      @back="() => $router.back()"
    >
      <template #extra>
        <a-space>
          <a-button @click="handleReset">重置</a-button>
          <a-button 
            type="primary" 
            @click="handleBatchImport"
            :disabled="!hasReviewedQuestions"
            :loading="importing"
          >
            <UploadOutlined /> 批量导入题库
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主体内容 -->
    <div class="generator-content">
      <a-row :gutter="24">
        <!-- 左侧：文件上传和设置 -->
        <a-col :span="8">
          <a-card title="上传文件和设置">
            <!-- 文件上传 -->
            <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
              <a-form-item label="教学文件">
                <a-upload
                  v-model:file-list="fileList"
                  :max-count="1"
                  :before-upload="beforeUpload"
                  @change="handleFileChange"
                >
                  <a-button>
                    <UploadOutlined /> 选择文件
                  </a-button>
                </a-upload>
                <div class="upload-hint">
                  支持PDF、PPT、PPTX、DOC、DOCX格式
                </div>
              </a-form-item>

              <a-divider>题目数量设置</a-divider>

              <a-form-item label="单选题">
                <a-input-number 
                  v-model:value="questionConfig.singleChoice"
                  :min="0"
                  :max="50"
                />
              </a-form-item>

              <a-form-item label="多选题">
                <a-input-number 
                  v-model:value="questionConfig.multipleChoice"
                  :min="0"
                  :max="30"
                />
              </a-form-item>

              <a-form-item label="判断题">
                <a-input-number 
                  v-model:value="questionConfig.trueFalse"
                  :min="0"
                  :max="30"
                />
              </a-form-item>

              <a-form-item label="总计">
                <a-tag color="blue">{{ totalQuestions }}道题</a-tag>
              </a-form-item>

              <a-divider>题目属性</a-divider>

              <a-form-item label="科目">
                <a-input v-model:value="questionMeta.subject" placeholder="如：计算机基础" />
              </a-form-item>

              <a-form-item label="章节">
                <a-input v-model:value="questionMeta.chapter" placeholder="如：第一章" />
              </a-form-item>

              <a-form-item>
                <a-button 
                  type="primary" 
                  block
                  @click="handleGenerateQuestions"
                  :loading="generating"
                  :disabled="!fileList.length || totalQuestions === 0"
                >
                  <RobotOutlined /> 生成试题
                </a-button>
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 生成统计 -->
          <a-card title="生成统计" v-if="generatedQuestions.length > 0" style="margin-top: 16px">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-statistic title="已生成" :value="generatedQuestions.length" suffix="题" />
              </a-col>
              <a-col :span="12">
                <a-statistic title="已审核" :value="reviewedCount" suffix="题" />
              </a-col>
            </a-row>
            
            <a-divider />
            
            <a-space direction="vertical" style="width: 100%">
              <div v-for="type in questionTypes" :key="type.key">
                <span>{{ type.label }}：</span>
                <a-progress 
                  :percent="getTypeProgress(type.key)" 
                  :status="getTypeProgress(type.key) === 100 ? 'success' : 'active'"
                />
              </div>
            </a-space>
          </a-card>
        </a-col>

        <!-- 右侧：试题预览和编辑 -->
        <a-col :span="16">
          <a-card title="试题预览和编辑">
            <!-- 空状态 -->
            <a-empty 
              v-if="generatedQuestions.length === 0"
              description="暂无生成的试题"
            >
              <template #image>
                <FileTextOutlined style="font-size: 48px; color: #ccc" />
              </template>
            </a-empty>

            <!-- 试题列表 -->
            <div v-else class="questions-list">
              <!-- 操作栏 -->
              <div class="actions-bar">
                <a-space>
                  <a-button size="small" @click="expandAll">
                    <ExpandOutlined /> 展开全部
                  </a-button>
                  <a-button size="small" @click="collapseAll">
                    <CompressOutlined /> 收起全部
                  </a-button>
                  <a-button size="small" type="primary" @click="reviewAll">
                    <CheckCircleOutlined /> 审核全部
                  </a-button>
                  <a-button size="small" danger @click="clearAll">
                    <DeleteOutlined /> 清空全部
                  </a-button>
                </a-space>
              </div>

              <!-- 试题卡片 -->
              <a-collapse v-model:activeKey="activeKeys" class="question-collapse">
                <a-collapse-panel
                  v-for="(question, index) in generatedQuestions"
                  :key="`question-${index}`"
                  :header="`${index + 1}. [${question.question_type}] ${question.question_stem.substring(0, 50)}...`"
                >
                  <template #extra>
                    <a-tag :color="getDifficultyColor(question.difficulty)">
                      {{ question.difficulty }}
                    </a-tag>
                    <a-tag :color="question.reviewed ? 'green' : 'orange'">
                      {{ question.reviewed ? '已审核' : '待审核' }}
                    </a-tag>
                  </template>

                  <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
                    <!-- 题型 -->
                    <a-form-item label="题型">
                      <a-select v-model:value="question.question_type">
                        <a-select-option value="单选题">单选题</a-select-option>
                        <a-select-option value="多选题">多选题</a-select-option>
                        <a-select-option value="判断题">判断题</a-select-option>
                      </a-select>
                    </a-form-item>

                    <!-- 题干 -->
                    <a-form-item label="题干">
                      <a-textarea
                        v-model:value="question.question_stem"
                        :rows="3"
                        placeholder="请输入题目内容"
                      />
                    </a-form-item>

                    <!-- 选项（非判断题） -->
                    <a-form-item label="选项" v-if="question.question_type !== '判断题'">
                      <div v-for="(option, oIndex) in question.options" :key="oIndex" class="option-item">
                        <a-input-group compact>
                          <a-input
                            style="width: 50px"
                            :value="`${String.fromCharCode(65 + oIndex)}.`"
                            disabled
                          />
                          <a-input
                            style="width: calc(100% - 100px)"
                            v-model:value="question.options[oIndex]"
                            placeholder="选项内容"
                          />
                          <a-button 
                            danger
                            @click="removeOption(index, oIndex)"
                            :disabled="question.options.length <= 2"
                          >
                            删除
                          </a-button>
                        </a-input-group>
                      </div>
                      <a-button 
                        type="dashed" 
                        size="small"
                        @click="addOption(index)"
                        :disabled="question.options.length >= 6"
                      >
                        <PlusOutlined /> 添加选项
                      </a-button>
                    </a-form-item>

                    <!-- 正确答案 -->
                    <a-form-item label="正确答案">
                      <!-- 单选题 -->
                      <a-radio-group 
                        v-if="question.question_type === '单选题'"
                        v-model:value="question.correct_answer"
                      >
                        <a-radio 
                          v-for="(_, oIndex) in question.options" 
                          :key="oIndex"
                          :value="String.fromCharCode(65 + oIndex)"
                        >
                          {{ String.fromCharCode(65 + oIndex) }}
                        </a-radio>
                      </a-radio-group>

                      <!-- 多选题 -->
                      <a-checkbox-group
                        v-else-if="question.question_type === '多选题'"
                        v-model:value="question.correct_answer"
                      >
                        <a-checkbox 
                          v-for="(_, oIndex) in question.options" 
                          :key="oIndex"
                          :value="String.fromCharCode(65 + oIndex)"
                        >
                          {{ String.fromCharCode(65 + oIndex) }}
                        </a-checkbox>
                      </a-checkbox-group>

                      <!-- 判断题 -->
                      <a-radio-group
                        v-else
                        v-model:value="question.correct_answer"
                      >
                        <a-radio :value="true">正确</a-radio>
                        <a-radio :value="false">错误</a-radio>
                      </a-radio-group>
                    </a-form-item>

                    <!-- 难度 -->
                    <a-form-item label="难度">
                      <a-radio-group v-model:value="question.difficulty">
                        <a-radio value="简单">简单</a-radio>
                        <a-radio value="中等">中等</a-radio>
                        <a-radio value="困难">困难</a-radio>
                      </a-radio-group>
                    </a-form-item>

                    <!-- 答案解析 -->
                    <a-form-item label="答案解析">
                      <a-textarea
                        v-model:value="question.analysis"
                        :rows="3"
                        placeholder="请输入答案解析"
                      />
                    </a-form-item>

                    <!-- 操作按钮 -->
                    <a-form-item :wrapper-col="{ offset: 4 }">
                      <a-space>
                        <a-button 
                          type="primary"
                          size="small"
                          @click="reviewQuestion(index)"
                          v-if="!question.reviewed"
                        >
                          <CheckOutlined /> 审核通过
                        </a-button>
                        <a-button 
                          size="small"
                          @click="cancelReview(index)"
                          v-else
                        >
                          <CloseOutlined /> 取消审核
                        </a-button>
                        <a-button 
                          danger
                          size="small"
                          @click="deleteQuestion(index)"
                        >
                          <DeleteOutlined /> 删除题目
                        </a-button>
                      </a-space>
                    </a-form-item>
                  </a-form>
                </a-collapse-panel>
              </a-collapse>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- Excel导出对话框 -->
    <a-modal
      v-model:open="exportDialogVisible"
      title="导出为Excel格式"
      width="800px"
      @ok="handleExportExcel"
      @cancel="exportDialogVisible = false"
    >
      <a-alert
        message="导出说明"
        description="将生成符合Excel导入模板格式的数据，您可以复制到Excel文件中进行进一步编辑"
        type="info"
        show-icon
      />
      
      <a-divider>预览数据</a-divider>
      
      <a-table
        :columns="excelColumns"
        :data-source="excelPreviewData"
        :pagination="{ pageSize: 5 }"
        size="small"
        :scroll="{ x: 1200 }"
      />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  UploadOutlined,
  RobotOutlined,
  FileTextOutlined,
  ExpandOutlined,
  CompressOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  CheckOutlined,
  CloseOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'
import {
  generateQuestionsFromFile,
  formatQuestionsForExcel,
  batchImportQuestions,
  type Question,
  type ExcelFormatData
} from '@/api/ai-generation'

const router = useRouter()

// 文件上传
const fileList = ref<any[]>([])
const uploadedFileName = ref('')

// 题目配置
const questionConfig = reactive({
  singleChoice: 10,
  multipleChoice: 5,
  trueFalse: 5
})

// 题目元数据
const questionMeta = reactive({
  subject: '',
  chapter: ''
})

// 生成的试题
const generatedQuestions = ref<Array<Question & { reviewed?: boolean }>>([])
const activeKeys = ref<string[]>([])

// 状态标志
const generating = ref(false)
const importing = ref(false)
const exportDialogVisible = ref(false)

// Excel预览数据
const excelPreviewData = ref<ExcelFormatData[]>([])

// Excel表格列
const excelColumns = [
  { title: '序号', dataIndex: '序号', width: 60, fixed: 'left' },
  { title: '题目类型', dataIndex: '题目类型', width: 100 },
  { title: '题干', dataIndex: '题干', width: 200, ellipsis: true },
  { title: '选项A', dataIndex: '选项A', width: 120, ellipsis: true },
  { title: '选项B', dataIndex: '选项B', width: 120, ellipsis: true },
  { title: '选项C', dataIndex: '选项C', width: 120, ellipsis: true },
  { title: '选项D', dataIndex: '选项D', width: 120, ellipsis: true },
  { title: '正确答案', dataIndex: '正确答案', width: 100 },
  { title: '难度', dataIndex: '难度', width: 80 },
  { title: '答案解析', dataIndex: '答案解析', width: 200, ellipsis: true }
]

// 题型配置
const questionTypes = [
  { key: 'single', label: '单选题', value: '单选题' },
  { key: 'multiple', label: '多选题', value: '多选题' },
  { key: 'trueFalse', label: '判断题', value: '判断题' }
]

// 计算属性
const totalQuestions = computed(() => {
  return questionConfig.singleChoice + questionConfig.multipleChoice + questionConfig.trueFalse
})

const hasReviewedQuestions = computed(() => {
  return generatedQuestions.value.some(q => q.reviewed)
})

const reviewedCount = computed(() => {
  return generatedQuestions.value.filter(q => q.reviewed).length
})

// 获取题型进度
const getTypeProgress = (type: string) => {
  const typeMap: Record<string, string> = {
    'single': '单选题',
    'multiple': '多选题',
    'trueFalse': '判断题'
  }
  
  const typeName = typeMap[type]
  const total = generatedQuestions.value.filter(q => q.question_type === typeName).length
  const reviewed = generatedQuestions.value.filter(q => q.question_type === typeName && q.reviewed).length
  
  return total > 0 ? Math.round((reviewed / total) * 100) : 0
}

// 获取难度颜色
const getDifficultyColor = (difficulty: string) => {
  const map: Record<string, string> = {
    '简单': 'green',
    '中等': 'orange',
    '困难': 'red'
  }
  return map[difficulty] || 'default'
}

// 文件上传前处理
const beforeUpload = (file: File) => {
  const isValidType = ['application/pdf', 'application/vnd.ms-powerpoint', 
                      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                      'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                      .includes(file.type)
  
  if (!isValidType) {
    message.error('只支持PDF、PPT、PPTX、DOC、DOCX格式的文件')
    return false
  }
  
  const isLt20M = file.size / 1024 / 1024 < 20
  if (!isLt20M) {
    message.error('文件大小不能超过20MB')
    return false
  }
  
  return false // 阻止自动上传
}

// 文件变化处理
const handleFileChange = (info: any) => {
  if (info.fileList.length > 0) {
    uploadedFileName.value = info.fileList[0].name
  }
}

// 生成试题
const handleGenerateQuestions = async () => {
  if (!fileList.value.length) {
    message.warning('请先上传文件')
    return
  }
  
  generating.value = true
  try {
    const file = fileList.value[0].originFileObj
    const result = await generateQuestionsFromFile(
      file,
      questionConfig.singleChoice,
      questionConfig.multipleChoice,
      questionConfig.trueFalse
    )
    
    if (result.code === '0000') {
      // 添加审核标记
      const questionsWithReview = result.data.questions.map(q => ({
        ...q,
        reviewed: false
      }))
      
      generatedQuestions.value = questionsWithReview
      
      // 展开前5个题目
      activeKeys.value = questionsWithReview.slice(0, 5).map((_, i) => `question-${i}`)
      
      message.success(`成功生成${result.data.statistics.total}道试题`)
    } else {
      message.error(result.message || '试题生成失败')
    }
  } catch (error) {
    message.error('试题生成失败')
    console.error(error)
  } finally {
    generating.value = false
  }
}

// 添加选项
const addOption = (questionIndex: number) => {
  const question = generatedQuestions.value[questionIndex]
  if (question.options && question.options.length < 6) {
    question.options.push('')
  }
}

// 删除选项
const removeOption = (questionIndex: number, optionIndex: number) => {
  const question = generatedQuestions.value[questionIndex]
  if (question.options && question.options.length > 2) {
    question.options.splice(optionIndex, 1)
    
    // 更新正确答案（如果需要）
    if (typeof question.correct_answer === 'string') {
      const currentIndex = question.correct_answer.charCodeAt(0) - 65
      if (currentIndex >= optionIndex) {
        question.correct_answer = String.fromCharCode(64 + currentIndex)
      }
    }
  }
}

// 审核题目
const reviewQuestion = (index: number) => {
  generatedQuestions.value[index].reviewed = true
  message.success('题目已审核')
}

// 取消审核
const cancelReview = (index: number) => {
  generatedQuestions.value[index].reviewed = false
}

// 删除题目
const deleteQuestion = (index: number) => {
  generatedQuestions.value.splice(index, 1)
  message.success('题目已删除')
}

// 展开全部
const expandAll = () => {
  activeKeys.value = generatedQuestions.value.map((_, i) => `question-${i}`)
}

// 收起全部
const collapseAll = () => {
  activeKeys.value = []
}

// 审核全部
const reviewAll = () => {
  generatedQuestions.value.forEach(q => {
    q.reviewed = true
  })
  message.success('已审核所有题目')
}

// 清空全部
const clearAll = () => {
  generatedQuestions.value = []
  activeKeys.value = []
  message.info('已清空所有题目')
}

// 批量导入
const handleBatchImport = async () => {
  const reviewedQuestions = generatedQuestions.value.filter(q => q.reviewed)
  
  if (reviewedQuestions.length === 0) {
    message.warning('没有已审核的题目')
    return
  }
  
  importing.value = true
  try {
    // 添加科目和章节信息
    const questionsWithMeta = reviewedQuestions.map(q => ({
      ...q,
      subject: questionMeta.subject || '通用',
      chapter: questionMeta.chapter || ''
    }))
    
    const result = await batchImportQuestions(questionsWithMeta)
    
    if (result.code === '0000') {
      message.success(`导入完成：成功${result.data.imported}题，失败${result.data.failed}题`)
      
      if (result.data.errors.length > 0) {
        console.error('导入错误：', result.data.errors)
      }
      
      // 清除已导入的题目
      generatedQuestions.value = generatedQuestions.value.filter(q => !q.reviewed)
      
      // 跳转到题库页面
      setTimeout(() => {
        router.push('/exam/question-library')
      }, 1500)
    } else {
      message.error(result.message || '导入失败')
    }
  } catch (error) {
    message.error('批量导入失败')
    console.error(error)
  } finally {
    importing.value = false
  }
}

// 导出Excel
const handleExportExcel = async () => {
  const reviewedQuestions = generatedQuestions.value.filter(q => q.reviewed)
  
  if (reviewedQuestions.length === 0) {
    message.warning('没有已审核的题目')
    return
  }
  
  try {
    const result = await formatQuestionsForExcel(
      reviewedQuestions,
      questionMeta.subject,
      questionMeta.chapter
    )
    
    if (result.code === '0000') {
      excelPreviewData.value = result.data.excel_format
      
      // 这里可以实现真正的Excel文件下载
      // 或者提供数据让用户复制
      message.success('格式化成功，可以复制数据到Excel')
    } else {
      message.error(result.message || '格式化失败')
    }
  } catch (error) {
    message.error('格式化失败')
    console.error(error)
  }
  
  exportDialogVisible.value = false
}

// 重置
const handleReset = () => {
  fileList.value = []
  uploadedFileName.value = ''
  generatedQuestions.value = []
  activeKeys.value = []
  questionConfig.singleChoice = 10
  questionConfig.multipleChoice = 5
  questionConfig.trueFalse = 5
  questionMeta.subject = ''
  questionMeta.chapter = ''
  message.info('已重置')
}
</script>

<style scoped lang="less">
.exam-question-generator {
  background-color: #f0f2f5;
  min-height: 100vh;
  
  .generator-content {
    padding: 24px;
  }
  
  .upload-hint {
    margin-top: 8px;
    color: #999;
    font-size: 12px;
  }
  
  .questions-list {
    .actions-bar {
      margin-bottom: 16px;
      padding: 12px;
      background: #fafafa;
      border-radius: 4px;
    }
    
    .question-collapse {
      :deep(.ant-collapse-header) {
        font-weight: 500;
      }
    }
    
    .option-item {
      margin-bottom: 8px;
    }
  }
  
  :deep(.ant-statistic-content) {
    font-size: 20px;
  }
}</style>