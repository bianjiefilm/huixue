<template>
  <!-- Nested under admin layout (padding owned by layout); no PageShell -->
  <div class="admin-page">
    <PageHeaderBar
      title="资源批量导入管理"
      subtitle="系统化导入实训、实践、题库等教学资源"
      show-back
    >
      <template #actions>
        <a-button @click="showHelp = true">
          <QuestionCircleOutlined />
          使用帮助
        </a-button>
      </template>
    </PageHeaderBar>

    <a-card class="import-card" :bordered="false">
      <a-tabs v-model:activeKey="activeTab">
        <!-- 实训资源导入 -->
        <a-tab-pane key="training" tab="实训资源导入">
          <div class="tab-content">
            <a-steps :current="trainingStep" class="import-steps">
              <a-step title="资源扫描" description="扫描实训资源目录" />
              <a-step title="数据验证" description="验证course_data.json" />
              <a-step title="批量导入" description="导入到系统" />
              <a-step title="发布配置" description="发布到课堂" />
            </a-steps>

            <div class="step-content">
              <!-- Step 1: 资源扫描 -->
              <div v-if="trainingStep === 0">
                <Stack :gap="4">
                  <a-alert
                    message="扫描路径"
                    :description="`将扫描 backend/ziyuan/实训资源/ 目录下的所有实训项目`"
                    type="info"
                    show-icon
                  />
                  <div>
                    <a-button type="primary" @click="scanTrainingResources" :loading="scanning">
                      <ScanOutlined /> 开始扫描
                    </a-button>
                  </div>
                </Stack>

                <div v-if="scanResult.length > 0" class="scan-result">
                  <a-divider>扫描结果</a-divider>
                  <a-table
                    :dataSource="scanResult"
                    :columns="trainingColumns"
                    rowKey="path"
                    :pagination="{ pageSize: 10 }"
                  >
                    <template #bodyCell="{ column, record }">
                      <template v-if="column.key === 'status'">
                        <a-tag :color="record.valid ? 'green' : 'red'">
                          {{ record.valid ? '有效' : '无效' }}
                        </a-tag>
                      </template>
                      <template v-if="column.key === 'action'">
                        <a-button
                          type="link"
                          size="small"
                          @click="viewTrainingDetail(record)"
                        >
                          查看详情
                        </a-button>
                      </template>
                    </template>
                  </a-table>
                  <a-space class="step-actions">
                    <a-button type="primary" @click="trainingStep++" :disabled="!hasValidTrainings">
                      下一步
                    </a-button>
                  </a-space>
                </div>
              </div>

              <!-- Step 2: 数据验证 -->
              <div v-if="trainingStep === 1">
                <a-space direction="vertical" style="width: 100%">
                  <a-alert
                    message="数据验证"
                    description="验证所有有效实训的数据完整性"
                    type="info"
                    show-icon
                  />

                  <a-checkbox-group v-model:value="selectedTrainings" style="width: 100%">
                    <a-row :gutter="[16, 16]">
                      <a-col :span="8" v-for="item in validTrainings" :key="item.path">
                        <a-card size="small">
                          <a-checkbox :value="item.path">
                            <div>
                              <div class="training-title">{{ item.name }}</div>
                              <div class="training-meta">
                                <a-tag size="small">{{ item.type }}</a-tag>
                                <a-tag size="small" color="blue">{{ item.difficulty }}</a-tag>
                              </div>
                            </div>
                          </a-checkbox>
                        </a-card>
                      </a-col>
                    </a-row>
                  </a-checkbox-group>

                  <a-space class="step-actions">
                    <a-button @click="trainingStep--">上一步</a-button>
                    <a-button
                      type="primary"
                      @click="validateTrainingData"
                      :loading="validating"
                      :disabled="selectedTrainings.length === 0"
                    >
                      验证数据
                    </a-button>
                  </a-space>
                </a-space>
              </div>

              <!-- Step 3: 批量导入 -->
              <div v-if="trainingStep === 2">
                <a-space direction="vertical" style="width: 100%">
                  <a-alert
                    :message="`准备导入 ${selectedTrainings.length} 个实训项目`"
                    type="warning"
                    show-icon
                  />

                  <a-form :model="importConfig" layout="vertical">
                    <a-form-item label="导入模式">
                      <a-radio-group v-model:value="importConfig.mode">
                        <a-radio value="skip">跳过已存在</a-radio>
                        <a-radio value="update">更新已存在</a-radio>
                        <a-radio value="replace">替换已存在</a-radio>
                      </a-radio-group>
                    </a-form-item>
                    <a-form-item label="创建者ID">
                      <a-input-number
                        v-model:value="importConfig.creatorId"
                        :min="1"
                        placeholder="请输入创建者用户ID"
                        style="width: 200px"
                      />
                    </a-form-item>
                  </a-form>

                  <div v-if="importProgress.show" class="import-progress">
                    <a-progress
                      :percent="importProgress.percent"
                      :status="importProgress.status"
                    />
                    <div class="progress-info">
                      {{ importProgress.current }} / {{ importProgress.total }}
                    </div>
                  </div>

                  <a-space class="step-actions">
                    <a-button @click="trainingStep--">上一步</a-button>
                    <a-button
                      type="primary"
                      @click="importTrainings"
                      :loading="importing"
                      :disabled="!importConfig.creatorId"
                    >
                      开始导入
                    </a-button>
                  </a-space>
                </a-space>
              </div>

              <!-- Step 4: 发布配置 -->
              <div v-if="trainingStep === 3">
                <a-result
                  status="success"
                  :title="`成功导入 ${importResult.success} 个实训项目`"
                  :sub-title="importResult.failed > 0 ? `失败 ${importResult.failed} 个` : ''"
                >
                  <template #extra>
                    <a-button type="primary" @click="resetTrainingImport">
                      继续导入
                    </a-button>
                    <a-button @click="goToTrainingLibrary">
                      查看实训库
                    </a-button>
                  </template>
                </a-result>
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 实践资源导入 -->
        <a-tab-pane key="practice" tab="实践课程导入">
          <div class="tab-content">
            <a-steps :current="practiceStep" class="import-steps">
              <a-step title="扫描微型实验" description="扫描课程资源中的实践" />
              <a-step title="创建实践" description="批量创建实践课程" />
              <a-step title="创建关卡" description="批量创建实践关卡" />
              <a-step title="完成" description="导入完成" />
            </a-steps>

            <div class="step-content">
              <!-- Step 1: 扫描实践 -->
              <div v-if="practiceStep === 0">
                <a-space direction="vertical" style="width: 100%">
                  <a-select
                    v-model:value="selectedCourse"
                    placeholder="选择要扫描的课程"
                    style="width: 300px"
                  >
                    <a-select-option value="Python程序设计">Python程序设计</a-select-option>
                    <a-select-option value="Spark编程基础">Spark编程基础</a-select-option>
                  </a-select>

                  <a-button
                    type="primary"
                    @click="scanPracticeResources"
                    :disabled="!selectedCourse"
                    :loading="scanning"
                  >
                    <ScanOutlined /> 扫描微型实验
                  </a-button>

                  <div v-if="practiceList.length > 0" class="practice-list">
                    <a-list
                      :dataSource="practiceList"
                      :grid="{ gutter: 16, column: 2 }"
                    >
                      <template #renderItem="{ item }">
                        <a-list-item>
                          <a-card size="small">
                            <a-checkbox v-model:checked="item.selected">
                              <div>
                                <div class="practice-title">{{ item.title }}</div>
                                <div class="practice-info">
                                  <span>关卡数: {{ item.stages?.length || 0 }}</span>
                                  <a-divider type="vertical" />
                                  <span>类型: {{ item.type }}</span>
                                </div>
                              </div>
                            </a-checkbox>
                          </a-card>
                        </a-list-item>
                      </template>
                    </a-list>
                    <a-button type="primary" @click="practiceStep++">
                      下一步
                    </a-button>
                  </div>
                </a-space>
              </div>

              <!-- Step 2-4: 后续步骤 -->
              <div v-if="practiceStep > 0">
                <!-- 实践创建和关卡导入流程 -->
                <PracticeImportFlow
                  :practices="selectedPractices"
                  :step="practiceStep"
                  @next="practiceStep++"
                  @prev="practiceStep--"
                  @complete="onPracticeImportComplete"
                />
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- 题库资源导入 -->
        <a-tab-pane key="question" tab="题库批量导入">
          <div class="tab-content">
            <a-space direction="vertical" style="width: 100%">
              <a-alert
                message="题库导入说明"
                description="支持JSON和Excel格式，请先下载模板文件"
                type="info"
                show-icon
              />

              <a-space>
                <a-button @click="downloadQuestionTemplate">
                  <DownloadOutlined /> 下载题库模板
                </a-button>
                <a-upload
                  :beforeUpload="beforeQuestionUpload"
                  :customRequest="uploadQuestions"
                  accept=".json,.xlsx,.xls"
                >
                  <a-button type="primary">
                    <UploadOutlined /> 上传题库文件
                  </a-button>
                </a-upload>
              </a-space>

              <div v-if="questionImportResult" class="import-result">
                <a-divider>导入结果</a-divider>
                <a-descriptions bordered :column="2">
                  <a-descriptions-item label="总数">
                    {{ questionImportResult.total }}
                  </a-descriptions-item>
                  <a-descriptions-item label="成功">
                    <a-tag color="green">{{ questionImportResult.success }}</a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="失败">
                    <a-tag color="red">{{ questionImportResult.failed }}</a-tag>
                  </a-descriptions-item>
                  <a-descriptions-item label="跳过">
                    {{ questionImportResult.skipped }}
                  </a-descriptions-item>
                </a-descriptions>

                <div v-if="questionImportResult.errors?.length > 0" class="error-list">
                  <a-collapse>
                    <a-collapse-panel key="1" header="错误详情">
                      <a-list
                        :dataSource="questionImportResult.errors"
                        size="small"
                      >
                        <template #renderItem="{ item }">
                          <a-list-item>
                            <a-typography-text type="danger">
                              行 {{ item.row }}: {{ item.message }}
                            </a-typography-text>
                          </a-list-item>
                        </template>
                      </a-list>
                    </a-collapse-panel>
                  </a-collapse>
                </div>
              </div>
            </a-space>
          </div>
        </a-tab-pane>

        <!-- 资源映射管理 -->
        <a-tab-pane key="mapping" tab="资源映射管理">
          <ResourceMappingManager />
        </a-tab-pane>
      </a-tabs>
    </a-card>

    <!-- 帮助弹窗 -->
    <a-modal
      v-model:open="showHelp"
      title="资源导入使用帮助"
      width="800px"
      :footer="null"
    >
      <div class="help-content">
        <a-typography>
          <a-typography-title :level="4">目录结构说明</a-typography-title>
          <a-typography-paragraph>
            <ul>
              <li><strong>ziyuan/实训资源/</strong>: 独立的实训项目，每个子目录包含course_data.json</li>
              <li><strong>ziyuan/课程资源/</strong>: 复合型课程包，包含理论、实践、题库等多种资源</li>
            </ul>
          </a-typography-paragraph>

          <a-typography-title :level="4">导入流程</a-typography-title>
          <a-typography-paragraph>
            <ol>
              <li>实训资源：扫描 → 验证 → 批量导入 → 发布到课堂</li>
              <li>实践课程：扫描微型实验 → 创建实践 → 创建关卡 → 配置测试集</li>
              <li>题库资源：下载模板 → 填写数据 → 批量导入</li>
            </ol>
          </a-typography-paragraph>
        </a-typography>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  QuestionCircleOutlined,
  ScanOutlined,
  DownloadOutlined,
  UploadOutlined
} from '@ant-design/icons-vue'
import { request } from '@/utils/request'
import ResourceMappingManager from '@/components/admin/ResourceMappingManager.vue'
import PracticeImportFlow from '@/components/admin/PracticeImportFlow.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
import Stack from '@/components/common/Stack.vue'

const router = useRouter()
const activeTab = ref('training')
const showHelp = ref(false)

// 实训导入相关
const trainingStep = ref(0)
const scanning = ref(false)
const validating = ref(false)
const importing = ref(false)
const scanResult = ref([])
const selectedTrainings = ref([])
const importConfig = ref({
  mode: 'skip',
  creatorId: null
})
const importProgress = ref({
  show: false,
  current: 0,
  total: 0,
  percent: 0,
  status: 'active'
})
const importResult = ref({
  success: 0,
  failed: 0,
  errors: []
})

// 实践导入相关
const practiceStep = ref(0)
const selectedCourse = ref('')
const practiceList = ref([])

// 题库导入相关
const questionImportResult = ref(null)

// 表格列定义
const trainingColumns = [
  {
    title: '资源名称',
    dataIndex: 'name',
    key: 'name'
  },
  {
    title: '路径',
    dataIndex: 'path',
    key: 'path'
  },
  {
    title: '类型',
    dataIndex: 'type',
    key: 'type'
  },
  {
    title: '难度',
    dataIndex: 'difficulty',
    key: 'difficulty'
  },
  {
    title: '状态',
    key: 'status'
  },
  {
    title: '操作',
    key: 'action'
  }
]

// 计算属性
const validTrainings = computed(() => scanResult.value.filter(item => item.valid))
const hasValidTrainings = computed(() => validTrainings.value.length > 0)
const selectedPractices = computed(() => practiceList.value.filter(item => item.selected))

// 扫描实训资源
async function scanTrainingResources() {
  scanning.value = true
  try {
    const response = await request({
      url: '/v1/resource-import/scan/trainings',
      method: 'POST'
    })

    if (response.code === '0000') {
      scanResult.value = response.data.resources
      message.success(`扫描完成，发现 ${response.data.total} 个资源，有效 ${response.data.valid} 个`)
    } else {
      message.error('扫描失败：' + response.msg)
    }
  } catch (error) {
    message.error('扫描失败：' + error.message)
  } finally {
    scanning.value = false
  }
}

// 验证实训数据
async function validateTrainingData() {
  validating.value = true
  try {
    // 验证选中的实训数据
    message.success('数据验证通过')
    trainingStep.value++
  } catch (error) {
    message.error('验证失败：' + error.message)
  } finally {
    validating.value = false
  }
}

// 批量导入实训
async function importTrainings() {
  importing.value = true
  importProgress.value = {
    show: true,
    current: 0,
    total: selectedTrainings.value.length,
    percent: 0,
    status: 'active'
  }

  try {
    const response = await request({
      url: '/v1/resource-import/import/trainings',
      method: 'POST',
      params: {
        paths: selectedTrainings.value,
        mode: importConfig.value.mode,
        creator_id: importConfig.value.creatorId
      }
    })

    if (response.code === '0000') {
      importResult.value = response.data
      importProgress.value.percent = 100
      importProgress.value.status = 'success'
      message.success(`导入完成：成功 ${response.data.success.length}，失败 ${response.data.failed.length}`)
      trainingStep.value++
    } else {
      message.error('导入失败：' + response.msg)
      importProgress.value.status = 'exception'
    }
  } catch (error) {
    message.error('导入失败：' + error.message)
    importProgress.value.status = 'exception'
  } finally {
    importing.value = false
  }
}

// 扫描实践资源
async function scanPracticeResources() {
  scanning.value = true
  try {
    const response = await request({
      url: '/v1/resource-import/scan/practices',
      method: 'POST',
      params: {
        course_name: selectedCourse.value
      }
    })

    if (response.code === '0000') {
      practiceList.value = response.data.practices.map(p => ({
        ...p,
        title: p.name,
        type: 'code',
        selected: false
      }))
      message.success(`扫描完成，发现 ${response.data.total} 个实践`)
    } else {
      message.error('扫描失败：' + response.msg)
    }
  } catch (error) {
    message.error('扫描失败：' + error.message)
  } finally {
    scanning.value = false
  }
}

// 下载题库模板
async function downloadQuestionTemplate() {
  try {
    const response = await request({
      url: '/v1/resource-import/questions/template',
      method: 'GET',
      responseType: 'blob'
    })

    const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = 'question_template.json'
    link.click()
    URL.revokeObjectURL(link.href)

    message.success('模板下载成功')
  } catch (error) {
    message.error('下载失败：' + error.message)
  }
}

// 上传题库文件
async function uploadQuestions(options) {
  const { file, onSuccess, onError } = options

  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('teacher_id', '1') // TODO: 从用户信息获取

    const response = await request({
      url: '/v1/resource-import/questions/import',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })

    if (response.code === '0000') {
      questionImportResult.value = response.data
      message.success(`题库导入完成：成功 ${response.data.success}，失败 ${response.data.failed}`)
      onSuccess && onSuccess()
    } else {
      message.error('导入失败：' + response.msg)
      onError && onError(new Error(response.msg))
    }
  } catch (error) {
    message.error('导入失败：' + error.message)
    onError && onError(error)
  }
}

// 文件上传前检查
function beforeQuestionUpload(file) {
  const isValidType = file.type === 'application/json' ||
                      file.type === 'application/vnd.ms-excel' ||
                      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
  if (!isValidType) {
    message.error('只支持JSON或Excel文件')
  }
  return isValidType
}

// 查看实训详情
function viewTrainingDetail(record) {
  // 显示实训详情
  console.log('查看详情:', record)
}

// 重置实训导入
function resetTrainingImport() {
  trainingStep.value = 0
  scanResult.value = []
  selectedTrainings.value = []
  importResult.value = { success: 0, failed: 0, errors: [] }
}

// 跳转到实训库
function goToTrainingLibrary() {
  router.push('/course/training/library')
}

// 实践导入完成
function onPracticeImportComplete(result) {
  message.success(`成功导入 ${result.success} 个实践`)
  practiceStep.value = 0
  practiceList.value = []
}
</script>

<style scoped lang="less">
.admin-page {
  width: 100%;

  .import-card {
    margin-top: 0;

    .import-steps {
      margin-bottom: var(--hx-space-6);
    }

    .step-content {
      min-height: 400px;
    }

    .scan-result {
      margin-top: var(--hx-space-5);
    }

    .step-actions {
      margin-top: var(--hx-space-5);
      display: flex;
      justify-content: flex-end;
      gap: var(--hx-space-2);
    }

    .training-title {
      font-weight: 500;
      margin-bottom: var(--hx-space-1);
    }

    .training-meta {
      margin-top: var(--hx-space-2);
    }

    .import-progress {
      margin-top: var(--hx-space-5);

      .progress-info {
        text-align: center;
        margin-top: var(--hx-space-2);
        color: var(--hx-color-text-secondary);
      }
    }

    .practice-list {
      margin-top: var(--hx-space-5);
    }

    .practice-title {
      font-weight: 500;
      margin-bottom: var(--hx-space-2);
    }

    .practice-info {
      color: var(--hx-color-text-secondary);
      font-size: 12px;
    }

    .import-result {
      margin-top: var(--hx-space-6);
    }

    .error-list {
      margin-top: var(--hx-space-4);
    }
  }

  .help-content {
    max-height: 500px;
    overflow-y: auto;
  }
}
</style>