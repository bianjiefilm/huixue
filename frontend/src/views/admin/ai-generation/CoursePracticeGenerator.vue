<template>
  <div class="course-practice-generator">
    <!-- 页面标题 -->
    <a-page-header
      title="AI辅助课程实践生成"
      sub-title="通过上传教学文件，智能生成课程实践内容"
      @back="() => $router.back()"
    >
      <template #extra>
        <a-space>
          <a-button @click="handleReset">重置</a-button>
          <a-button type="primary" @click="handleSaveAll" :disabled="!hasGeneratedContent">
            保存所有内容
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <!-- 主体内容 -->
    <div class="generator-content">
      <!-- 步骤条 -->
      <a-steps :current="currentStep" class="steps-container">
        <a-step title="上传文件" description="上传教学PDF或PPT文件" />
        <a-step title="生成大纲" description="AI分析并生成课程大纲" />
        <a-step title="审核调整" description="审核并调整生成的大纲" />
        <a-step title="生成内容" description="为每个关卡生成详细内容" />
        <a-step title="最终确认" description="确认并保存到系统" />
      </a-steps>

      <!-- 步骤1：文件上传 -->
      <div v-if="currentStep === 0" class="step-content">
        <a-card title="上传教学文件">
          <a-upload-dragger
            v-model:file-list="fileList"
            :max-count="1"
            :before-upload="beforeUpload"
            @change="handleFileChange"
          >
            <p class="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p class="ant-upload-hint">
              支持PDF、PPT、PPTX、DOC、DOCX格式，文件大小不超过20MB
            </p>
          </a-upload-dragger>

          <div v-if="extractedText" class="extracted-text-preview">
            <a-divider>提取的文本预览</a-divider>
            <a-card size="small">
              <pre>{{ extractedText.substring(0, 500) }}...</pre>
              <a-tag color="blue">共 {{ extractedText.length }} 字符</a-tag>
            </a-card>
          </div>

          <div class="step-actions">
            <a-button 
              type="primary" 
              @click="handleExtractText"
              :loading="extracting"
              :disabled="!fileList.length"
            >
              提取文本并继续
            </a-button>
          </div>
        </a-card>
      </div>

      <!-- 步骤2：生成大纲 -->
      <div v-if="currentStep === 1" class="step-content">
        <a-card title="AI生成课程大纲">
          <a-alert
            message="AI正在分析文档内容，生成课程实践大纲..."
            type="info"
            show-icon
            v-if="generatingOutline"
          />

          <div v-if="!generatingOutline && practiceOutline.length > 0">
            <a-alert
              message="大纲生成成功"
              description="AI已根据文档内容生成了课程实践大纲，请继续下一步进行审核和调整"
              type="success"
              show-icon
              closable
            />

            <a-divider>生成的大纲预览</a-divider>
            
            <a-timeline>
              <a-timeline-item v-for="(item, index) in practiceOutline" :key="index">
                <template #dot>
                  <div :class="['timeline-dot', getDifficultyClass(item.difficulty)]">
                    {{ index + 1 }}
                  </div>
                </template>
                <div class="outline-item-preview">
                  <h4>{{ item.level_title }}</h4>
                  <a-space>
                    <a-tag>{{ item.suggested_type }}</a-tag>
                    <a-tag :color="getDifficultyColor(item.difficulty)">
                      {{ item.difficulty }}
                    </a-tag>
                    <a-tag color="blue">
                      <ClockCircleOutlined /> {{ item.estimated_time }}分钟
                    </a-tag>
                  </a-space>
                  <p>{{ item.core_knowledge }}</p>
                </div>
              </a-timeline-item>
            </a-timeline>
          </div>

          <div class="step-actions">
            <a-button @click="currentStep--">上一步</a-button>
            <a-button 
              type="primary" 
              @click="handleGenerateOutline"
              :loading="generatingOutline"
              v-if="practiceOutline.length === 0"
            >
              生成大纲
            </a-button>
            <a-button 
              type="primary" 
              @click="currentStep++"
              v-if="practiceOutline.length > 0"
            >
              下一步：审核调整
            </a-button>
          </div>
        </a-card>
      </div>

      <!-- 步骤3：审核调整大纲 -->
      <div v-if="currentStep === 2" class="step-content">
        <a-card title="审核和调整大纲">
          <div class="outline-editor">
            <a-space direction="vertical" style="width: 100%">
              <div v-for="(item, index) in editableOutline" :key="index" class="outline-item-editor">
                <a-card size="small">
                  <template #title>
                    <a-space>
                      <span>关卡 {{ index + 1 }}</span>
                      <a-button 
                        type="link" 
                        danger 
                        size="small"
                        @click="removeOutlineItem(index)"
                      >
                        <DeleteOutlined /> 删除
                      </a-button>
                    </a-space>
                  </template>

                  <a-form :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
                    <a-form-item label="关卡标题">
                      <a-input v-model:value="item.level_title" />
                    </a-form-item>
                    
                    <a-form-item label="核心知识">
                      <a-textarea 
                        v-model:value="item.core_knowledge" 
                        :rows="2"
                      />
                    </a-form-item>
                    
                    <a-form-item label="实践描述">
                      <a-textarea 
                        v-model:value="item.practice_description" 
                        :rows="2"
                      />
                    </a-form-item>
                    
                    <a-form-item label="题型">
                      <a-select v-model:value="item.suggested_type">
                        <a-select-option value="实践题">实践题</a-select-option>
                        <a-select-option value="选择题">选择题</a-select-option>
                        <a-select-option value="判断题">判断题</a-select-option>
                      </a-select>
                    </a-form-item>
                    
                    <a-form-item label="难度">
                      <a-radio-group v-model:value="item.difficulty">
                        <a-radio value="初级">初级</a-radio>
                        <a-radio value="中级">中级</a-radio>
                        <a-radio value="高级">高级</a-radio>
                      </a-radio-group>
                    </a-form-item>
                    
                    <a-form-item label="预计时间">
                      <a-input-number 
                        v-model:value="item.estimated_time" 
                        :min="5" 
                        :max="120"
                        :step="5"
                      />
                      <span class="ant-form-text"> 分钟</span>
                    </a-form-item>
                  </a-form>
                </a-card>
              </div>

              <a-button type="dashed" block @click="addOutlineItem">
                <PlusOutlined /> 添加新关卡
              </a-button>
            </a-space>
          </div>

          <div class="step-actions">
            <a-button @click="currentStep--">上一步</a-button>
            <a-button type="primary" @click="currentStep++">
              下一步：生成内容
            </a-button>
          </div>
        </a-card>
      </div>

      <!-- 步骤4：生成内容 -->
      <div v-if="currentStep === 3" class="step-content">
        <a-card title="生成关卡内容">
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane 
              v-for="(item, index) in editableOutline" 
              :key="`level-${index}`"
              :tab="`关卡${index + 1}: ${item.level_title}`"
            >
              <div class="level-content-generator">
                <!-- 生成按钮 -->
                <div v-if="!generatedContent[index]" class="generate-prompt">
                  <a-empty description="尚未生成内容">
                    <a-button 
                      type="primary" 
                      @click="handleGenerateLevelContent(index)"
                      :loading="generatingLevel === index"
                    >
                      <RobotOutlined /> AI生成关卡内容
                    </a-button>
                  </a-empty>
                </div>

                <!-- 已生成的内容 -->
                <div v-else class="generated-content">
                  <a-space direction="vertical" style="width: 100%">
                    <!-- 实践题内容 -->
                    <template v-if="item.suggested_type === '实践题'">
                      <!-- 任务手册 -->
                      <a-card size="small" title="任务手册">
                        <template #extra>
                          <a-button 
                            type="link" 
                            @click="handleAIAssist('task_handbook', index)"
                          >
                            <BulbOutlined /> AI辅助
                          </a-button>
                        </template>
                        <a-textarea
                          v-model:value="generatedContent[index].task_handbook"
                          :rows="10"
                          placeholder="任务说明..."
                        />
                      </a-card>

                      <!-- 学生模板 -->
                      <a-card size="small" title="学生代码模板">
                        <template #extra>
                          <a-button 
                            type="link" 
                            @click="handleAIAssist('student_template', index)"
                          >
                            <BulbOutlined /> AI辅助
                          </a-button>
                        </template>
                        <a-textarea
                          v-model:value="generatedContent[index].student_template"
                          :rows="10"
                          placeholder="学生代码模板..."
                          style="font-family: monospace"
                        />
                      </a-card>

                      <!-- 评测脚本 -->
                      <a-card size="small" title="评测脚本">
                        <template #extra>
                          <a-button 
                            type="link" 
                            @click="handleAIAssist('judge_script', index)"
                          >
                            <BulbOutlined /> AI辅助
                          </a-button>
                        </template>
                        <a-textarea
                          v-model:value="generatedContent[index].judge_script"
                          :rows="10"
                          placeholder="评测脚本..."
                          style="font-family: monospace"
                        />
                      </a-card>

                      <!-- 测试用例 -->
                      <a-card size="small" title="测试用例">
                        <a-button 
                          type="dashed" 
                          size="small"
                          @click="addTestCase(index)"
                        >
                          <PlusOutlined /> 添加测试用例
                        </a-button>
                        <div v-for="(test, tIndex) in generatedContent[index].test_cases" :key="tIndex">
                          <a-divider />
                          <a-form :label-col="{ span: 4 }">
                            <a-form-item label="输入">
                              <a-input v-model:value="test.input" />
                            </a-form-item>
                            <a-form-item label="期望输出">
                              <a-input v-model:value="test.expected_output" />
                            </a-form-item>
                            <a-form-item label="隐藏">
                              <a-switch v-model:checked="test.is_hidden" />
                            </a-form-item>
                          </a-form>
                        </div>
                      </a-card>

                      <!-- 参考答案 -->
                      <a-card size="small" title="参考答案">
                        <a-textarea
                          v-model:value="generatedContent[index].reference_answer"
                          :rows="10"
                          placeholder="参考答案代码..."
                          style="font-family: monospace"
                        />
                      </a-card>
                    </template>

                    <!-- 选择题/判断题内容 -->
                    <template v-else>
                      <a-card 
                        size="small" 
                        v-for="(q, qIndex) in generatedContent[index].questions" 
                        :key="qIndex"
                        :title="`题目 ${qIndex + 1}`"
                      >
                        <a-form :label-col="{ span: 4 }">
                          <a-form-item label="题干">
                            <a-textarea v-model:value="q.question_stem" :rows="3" />
                          </a-form-item>
                          
                          <a-form-item label="选项" v-if="item.suggested_type === '选择题'">
                            <a-input 
                              v-for="(opt, oIndex) in q.options" 
                              :key="oIndex"
                              v-model:value="q.options[oIndex]"
                              style="margin-bottom: 8px"
                            />
                          </a-form-item>
                          
                          <a-form-item label="正确答案">
                            <a-input v-model:value="q.correct_answer" />
                          </a-form-item>
                          
                          <a-form-item label="解析">
                            <a-textarea v-model:value="q.analysis" :rows="3" />
                          </a-form-item>
                        </a-form>
                      </a-card>
                    </template>

                    <!-- 重新生成按钮 -->
                    <a-button 
                      type="default"
                      @click="handleRegenerateLevelContent(index)"
                      :loading="generatingLevel === index"
                    >
                      <RedoOutlined /> 重新生成
                    </a-button>
                  </a-space>
                </div>
              </div>
            </a-tab-pane>
          </a-tabs>

          <div class="step-actions">
            <a-button @click="currentStep--">上一步</a-button>
            <a-button 
              type="primary" 
              @click="currentStep++"
              :disabled="Object.keys(generatedContent).length === 0"
            >
              下一步：最终确认
            </a-button>
          </div>
        </a-card>
      </div>

      <!-- 步骤5：最终确认 -->
      <div v-if="currentStep === 4" class="step-content">
        <a-card title="最终确认">
          <a-alert
            message="内容生成完成"
            description="请确认所有内容无误后，点击保存按钮将内容保存到系统中"
            type="success"
            show-icon
          />

          <a-divider>内容摘要</a-divider>

          <a-descriptions bordered>
            <a-descriptions-item label="文件名">
              {{ uploadedFileName }}
            </a-descriptions-item>
            <a-descriptions-item label="关卡数量">
              {{ editableOutline.length }}
            </a-descriptions-item>
            <a-descriptions-item label="总预计时长">
              {{ totalEstimatedTime }}分钟
            </a-descriptions-item>
            <a-descriptions-item label="包含题型" :span="3">
              <a-tag v-for="type in uniqueTypes" :key="type">{{ type }}</a-tag>
            </a-descriptions-item>
          </a-descriptions>

          <a-divider>关卡列表</a-divider>

          <a-table :columns="summaryColumns" :data-source="summaryData" :pagination="false">
            <template #status="{ record }">
              <a-tag :color="record.generated ? 'green' : 'red'">
                {{ record.generated ? '已生成' : '未生成' }}
              </a-tag>
            </template>
          </a-table>

          <div class="step-actions">
            <a-button @click="currentStep--">上一步</a-button>
            <a-button type="primary" @click="handleFinalSave" :loading="saving">
              <SaveOutlined /> 保存到系统
            </a-button>
          </div>
        </a-card>
      </div>
    </div>

    <!-- AI辅助对话框 -->
    <a-modal
      v-model:open="aiAssistVisible"
      title="AI辅助生成"
      width="800px"
      @ok="handleAIAssistConfirm"
      @cancel="aiAssistVisible = false"
    >
      <a-form :label-col="{ span: 4 }">
        <a-form-item label="指令">
          <a-textarea
            v-model:value="aiAssistInstruction"
            :rows="4"
            placeholder="请输入您的需求，例如：生成一个计算两数之和的函数模板"
          />
        </a-form-item>
        
        <a-form-item label="上下文">
          <a-textarea
            v-model:value="aiAssistContext"
            :rows="4"
            placeholder="可选：提供额外的上下文信息"
          />
        </a-form-item>

        <a-form-item>
          <a-button type="primary" @click="handleGenerateSnippet" :loading="generatingSnippet">
            生成代码
          </a-button>
        </a-form-item>

        <a-form-item label="生成结果" v-if="aiAssistResult">
          <a-textarea
            v-model:value="aiAssistResult"
            :rows="10"
            style="font-family: monospace"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  InboxOutlined,
  ClockCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
  RobotOutlined,
  BulbOutlined,
  RedoOutlined,
  SaveOutlined
} from '@ant-design/icons-vue'
import {
  extractTextFromFile,
  generatePracticeOutlineFromFile,
  generatePracticeLevelContent,
  suggestCodeSnippet,
  type PracticeOutlineItem,
  type PracticeLevelContent
} from '@/api/ai-generation'

const router = useRouter()

// 当前步骤
const currentStep = ref(0)

// 文件上传
const fileList = ref<any[]>([])
const uploadedFileName = ref('')
const extractedText = ref('')
const extracting = ref(false)

// 大纲相关
const practiceOutline = ref<PracticeOutlineItem[]>([])
const editableOutline = ref<PracticeOutlineItem[]>([])
const generatingOutline = ref(false)

// 内容生成
const activeTab = ref('level-0')
const generatedContent = ref<Record<number, PracticeLevelContent>>({})
const generatingLevel = ref<number | null>(null)

// AI辅助
const aiAssistVisible = ref(false)
const aiAssistTarget = ref({ type: '', index: 0 })
const aiAssistInstruction = ref('')
const aiAssistContext = ref('')
const aiAssistResult = ref('')
const generatingSnippet = ref(false)

// 保存
const saving = ref(false)

// 计算属性
const hasGeneratedContent = computed(() => Object.keys(generatedContent.value).length > 0)

const totalEstimatedTime = computed(() => {
  return editableOutline.value.reduce((sum, item) => sum + item.estimated_time, 0)
})

const uniqueTypes = computed(() => {
  return [...new Set(editableOutline.value.map(item => item.suggested_type))]
})

const summaryData = computed(() => {
  return editableOutline.value.map((item, index) => ({
    key: index,
    title: item.level_title,
    type: item.suggested_type,
    difficulty: item.difficulty,
    time: item.estimated_time,
    generated: !!generatedContent.value[index]
  }))
})

// 表格列定义
const summaryColumns = [
  { title: '序号', dataIndex: 'key', width: 80 },
  { title: '关卡标题', dataIndex: 'title' },
  { title: '题型', dataIndex: 'type', width: 100 },
  { title: '难度', dataIndex: 'difficulty', width: 80 },
  { title: '时长(分钟)', dataIndex: 'time', width: 100 },
  { title: '状态', key: 'status', width: 100, slots: { customRender: 'status' } }
]

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

// 提取文本
const handleExtractText = async () => {
  if (!fileList.value.length) {
    message.warning('请先上传文件')
    return
  }
  
  extracting.value = true
  try {
    const file = fileList.value[0].originFileObj
    const result = await extractTextFromFile(file)
    
    if (result.code === '0000') {
      extractedText.value = result.data.text_content
      message.success('文本提取成功')
      currentStep.value++
    } else {
      message.error(result.message || '文本提取失败')
    }
  } catch (error) {
    message.error('文本提取失败')
    console.error(error)
  } finally {
    extracting.value = false
  }
}

// 生成大纲
const handleGenerateOutline = async () => {
  generatingOutline.value = true
  try {
    const file = fileList.value[0].originFileObj
    const result = await generatePracticeOutlineFromFile(file)
    
    if (result.code === '0000') {
      practiceOutline.value = result.data.outline
      editableOutline.value = JSON.parse(JSON.stringify(result.data.outline))
      extractedText.value = result.data.original_text
      message.success('大纲生成成功')
    } else {
      message.error(result.message || '大纲生成失败')
    }
  } catch (error) {
    message.error('大纲生成失败')
    console.error(error)
  } finally {
    generatingOutline.value = false
  }
}

// 添加大纲项
const addOutlineItem = () => {
  editableOutline.value.push({
    level_title: '新关卡',
    core_knowledge: '',
    practice_description: '',
    suggested_type: '实践题',
    difficulty: '中级',
    estimated_time: 30
  })
}

// 删除大纲项
const removeOutlineItem = (index: number) => {
  editableOutline.value.splice(index, 1)
  delete generatedContent.value[index]
}

// 生成关卡内容
const handleGenerateLevelContent = async (index: number) => {
  generatingLevel.value = index
  try {
    const levelInfo = editableOutline.value[index]
    const result = await generatePracticeLevelContent(levelInfo, extractedText.value)
    
    if (result.code === '0000') {
      generatedContent.value[index] = result.data.content
      message.success('内容生成成功')
    } else {
      message.error(result.message || '内容生成失败')
    }
  } catch (error) {
    message.error('内容生成失败')
    console.error(error)
  } finally {
    generatingLevel.value = null
  }
}

// 重新生成关卡内容
const handleRegenerateLevelContent = (index: number) => {
  handleGenerateLevelContent(index)
}

// 添加测试用例
const addTestCase = (index: number) => {
  if (!generatedContent.value[index].test_cases) {
    generatedContent.value[index].test_cases = []
  }
  generatedContent.value[index].test_cases!.push({
    input: '',
    expected_output: '',
    is_hidden: false,
    description: ''
  })
}

// AI辅助
const handleAIAssist = (type: string, index: number) => {
  aiAssistTarget.value = { type, index }
  aiAssistInstruction.value = ''
  aiAssistContext.value = editableOutline.value[index].core_knowledge
  aiAssistResult.value = ''
  aiAssistVisible.value = true
}

// 生成代码片段
const handleGenerateSnippet = async () => {
  if (!aiAssistInstruction.value) {
    message.warning('请输入指令')
    return
  }
  
  generatingSnippet.value = true
  try {
    const result = await suggestCodeSnippet(
      aiAssistInstruction.value,
      aiAssistTarget.value.type,
      aiAssistContext.value,
      'python'
    )
    
    if (result.code === '0000') {
      aiAssistResult.value = result.data.code
      message.success('代码生成成功')
    } else {
      message.error(result.message || '代码生成失败')
    }
  } catch (error) {
    message.error('代码生成失败')
    console.error(error)
  } finally {
    generatingSnippet.value = false
  }
}

// AI辅助确认
const handleAIAssistConfirm = () => {
  if (aiAssistResult.value) {
    const { type, index } = aiAssistTarget.value
    if (!generatedContent.value[index]) {
      generatedContent.value[index] = {}
    }
    
    // 根据类型插入到对应字段
    if (type === 'task_handbook') {
      generatedContent.value[index].task_handbook = aiAssistResult.value
    } else if (type === 'student_template') {
      generatedContent.value[index].student_template = aiAssistResult.value
    } else if (type === 'judge_script') {
      generatedContent.value[index].judge_script = aiAssistResult.value
    }
  }
  
  aiAssistVisible.value = false
}

// 保存所有内容
const handleSaveAll = () => {
  handleFinalSave()
}

// 最终保存
const handleFinalSave = async () => {
  saving.value = true
  try {
    // TODO: 调用保存API，将生成的内容保存到数据库
    // 这里需要根据实际的后端API进行调整
    
    message.success('保存成功')
    setTimeout(() => {
      router.push('/course/practice')
    }, 1500)
  } catch (error) {
    message.error('保存失败')
    console.error(error)
  } finally {
    saving.value = false
  }
}

// 重置
const handleReset = () => {
  currentStep.value = 0
  fileList.value = []
  uploadedFileName.value = ''
  extractedText.value = ''
  practiceOutline.value = []
  editableOutline.value = []
  generatedContent.value = {}
  message.info('已重置')
}

// 获取难度样式类
const getDifficultyClass = (difficulty: string) => {
  const map: Record<string, string> = {
    '初级': 'difficulty-easy',
    '中级': 'difficulty-medium',
    '高级': 'difficulty-hard'
  }
  return map[difficulty] || ''
}

// 获取难度颜色
const getDifficultyColor = (difficulty: string) => {
  const map: Record<string, string> = {
    '初级': 'green',
    '中级': 'orange',
    '高级': 'red'
  }
  return map[difficulty] || 'default'
}
</script>

<style scoped lang="less">
.course-practice-generator {
  background-color: #f0f2f5;
  min-height: 100vh;
  
  .generator-content {
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
  }
  
  .steps-container {
    margin-bottom: 24px;
    background: white;
    padding: 24px;
    border-radius: 8px;
  }
  
  .step-content {
    background: white;
    border-radius: 8px;
    
    .step-actions {
      margin-top: 24px;
      text-align: center;
      
      button {
        margin: 0 8px;
      }
    }
  }
  
  .extracted-text-preview {
    margin-top: 24px;
    
    pre {
      white-space: pre-wrap;
      word-wrap: break-word;
      max-height: 200px;
      overflow-y: auto;
    }
  }
  
  .timeline-dot {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #1890ff;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
    
    &.difficulty-easy {
      background: #52c41a;
    }
    
    &.difficulty-medium {
      background: #faad14;
    }
    
    &.difficulty-hard {
      background: #f5222d;
    }
  }
  
  .outline-item-preview {
    h4 {
      margin-bottom: 8px;
    }
    
    p {
      margin-top: 8px;
      color: #666;
    }
  }
  
  .outline-editor {
    .outline-item-editor {
      margin-bottom: 16px;
    }
  }
  
  .level-content-generator {
    .generate-prompt {
      padding: 48px;
      text-align: center;
    }
    
    .generated-content {
      .ant-card {
        margin-bottom: 16px;
      }
    }
  }
}
</style>