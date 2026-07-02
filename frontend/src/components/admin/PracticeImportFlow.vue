<template>
  <div class="practice-import-flow">
    <!-- Step 2: 创建实践 -->
    <div v-if="step === 1">
      <a-space direction="vertical" style="width: 100%">
        <a-alert
          :message="`准备创建 ${practices.length} 个实践课程`"
          type="info"
          show-icon
        />

        <a-form :model="practiceConfig" layout="vertical">
          <a-form-item label="创建者ID" required>
            <a-input-number
              v-model:value="practiceConfig.creatorId"
              :min="1"
              placeholder="请输入创建者ID"
              style="width: 200px"
            />
          </a-form-item>

          <a-form-item label="实践类型">
            <a-radio-group v-model:value="practiceConfig.type">
              <a-radio value="code">编程实践</a-radio>
              <a-radio value="desktop">桌面实践</a-radio>
            </a-radio-group>
          </a-form-item>

          <a-form-item label="难度设置">
            <a-select v-model:value="practiceConfig.difficulty" style="width: 200px">
              <a-select-option value="beginner">初级</a-select-option>
              <a-select-option value="intermediate">中级</a-select-option>
              <a-select-option value="advanced">高级</a-select-option>
            </a-select>
          </a-form-item>
        </a-form>

        <div v-if="creatingPractices">
          <a-progress :percent="createProgress" />
          <div class="progress-text">
            正在创建: {{ currentPractice }} ({{ createdCount }}/{{ practices.length }})
          </div>
        </div>

        <a-space class="step-actions">
          <a-button @click="$emit('prev')">上一步</a-button>
          <a-button
            type="primary"
            @click="createPractices"
            :loading="creatingPractices"
            :disabled="!practiceConfig.creatorId"
          >
            开始创建
          </a-button>
        </a-space>
      </a-space>
    </div>

    <!-- Step 3: 创建关卡 -->
    <div v-if="step === 2">
      <a-space direction="vertical" style="width: 100%">
        <a-alert
          message="创建实践关卡"
          description="为每个实践创建对应的关卡和任务"
          type="info"
          show-icon
        />

        <a-collapse v-model:activeKey="activeKeys">
          <a-collapse-panel
            v-for="(practice, index) in createdPractices"
            :key="practice.id"
            :header="practice.title"
          >
            <a-list
              :dataSource="practice.stages"
              size="small"
            >
              <template #renderItem="{ item, index: stageIndex }">
                <a-list-item>
                  <a-list-item-meta
                    :title="`关卡${stageIndex + 1}: ${item.title}`"
                    :description="item.description"
                  />
                  <template #actions>
                    <a-button
                      size="small"
                      type="primary"
                      @click="createStage(practice.id, item)"
                      :loading="item.creating"
                    >
                      创建关卡
                    </a-button>
                  </template>
                </a-list-item>
              </template>
            </a-list>
          </a-collapse-panel>
        </a-collapse>

        <div v-if="stageProgress.show" class="stage-progress">
          <a-progress
            :percent="stageProgress.percent"
            :status="stageProgress.status"
          />
          <div class="progress-info">
            已创建 {{ stageProgress.created }} / {{ stageProgress.total }} 个关卡
          </div>
        </div>

        <a-space class="step-actions">
          <a-button @click="$emit('prev')">上一步</a-button>
          <a-button
            type="primary"
            @click="createAllStages"
            :loading="creatingStages"
          >
            批量创建关卡
          </a-button>
          <a-button
            @click="skipStages"
            :disabled="creatingStages"
          >
            跳过
          </a-button>
        </a-space>
      </a-space>
    </div>

    <!-- Step 4: 完成 -->
    <div v-if="step === 3">
      <a-result
        status="success"
        :title="`成功导入 ${importSummary.practices} 个实践`"
        :sub-title="`共创建 ${importSummary.stages} 个关卡`"
      >
        <template #extra>
          <a-space>
            <a-button type="primary" @click="finish">
              完成
            </a-button>
            <a-button @click="viewPractices">
              查看实践列表
            </a-button>
          </a-space>
        </template>
      </a-result>

      <a-card title="导入详情" size="small">
        <a-descriptions bordered :column="2">
          <a-descriptions-item label="实践总数">
            {{ importSummary.practices }}
          </a-descriptions-item>
          <a-descriptions-item label="关卡总数">
            {{ importSummary.stages }}
          </a-descriptions-item>
          <a-descriptions-item label="成功率">
            <a-progress
              :percent="importSummary.successRate"
              size="small"
              :stroke-color="{ '0%': '#108ee9', '100%': '#87d068' }"
            />
          </a-descriptions-item>
          <a-descriptions-item label="用时">
            {{ importSummary.duration }}秒
          </a-descriptions-item>
        </a-descriptions>
      </a-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  createPractice,
  createPracticeStage,
  createStageTestCases,
  createQuestionStageComplete
} from '@/api/practice'

const props = defineProps({
  practices: {
    type: Array,
    required: true
  },
  step: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['next', 'prev', 'complete'])

const router = useRouter()

// 实践配置
const practiceConfig = reactive({
  creatorId: 1,
  type: 'code',
  difficulty: 'beginner'
})

// 创建进度
const creatingPractices = ref(false)
const createProgress = ref(0)
const currentPractice = ref('')
const createdCount = ref(0)
const createdPractices = ref([])

// 关卡创建
const activeKeys = ref([])
const creatingStages = ref(false)
const stageProgress = reactive({
  show: false,
  created: 0,
  total: 0,
  percent: 0,
  status: 'active'
})

// 导入总结
const importSummary = reactive({
  practices: 0,
  stages: 0,
  successRate: 0,
  duration: 0
})

const startTime = ref(0)

// 创建实践课程
async function createPractices() {
  creatingPractices.value = true
  createdCount.value = 0
  createProgress.value = 0
  startTime.value = Date.now()

  try {
    // 使用批量导入API
    const response = await fetch('/v1/resource-import/import/practices', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      },
      body: JSON.stringify({
        practices: props.practices,
        creator_id: practiceConfig.creatorId
      })
    })

    const result = await response.json()

    if (result.code === '0000') {
      // 处理成功的实践
      result.data.success.forEach((title, index) => {
        const practice = props.practices.find(p => p.name === title)
        if (practice) {
          createdPractices.value.push({
            ...practice,
            id: index + 1, // 临时ID
            stages: practice.stages.map(stage => ({
              title: stage,
              description: `${stage} 任务`,
              creating: false
            }))
          })
          createdCount.value++
        }
      })

      createProgress.value = 100

      message.success(`成功创建 ${createdCount.value} 个实践`)
      emit('next')
    }
  } catch (error) {
    message.error('创建失败：' + error.message)
  } finally {
    creatingPractices.value = false
  }
}

// 创建单个关卡
async function createStage(practiceId, stage) {
  stage.creating = true

  try {
    // 先创建关卡
    const stageResponse = await createPracticeStage(
      practiceId,
      {
        title: stage.title,
        description: stage.description,
        order_index: 1,
        points: 10,
        time_limit: 30
      },
      practiceConfig.creatorId
    )

    if (stageResponse) {
      // 创建测试用例
      await createStageTestCases(
        stageResponse.stage_id,
        [
          {
            input: 'test input',
            expected_output: 'expected output'
          }
        ],
        practiceConfig.creatorId
      )

      stage.created = true
      stageProgress.created++
      stageProgress.percent = Math.round(stageProgress.created / stageProgress.total * 100)
      message.success(`关卡 "${stage.title}" 创建成功`)
    }
  } catch (error) {
    message.error(`创建关卡失败：${error.message}`)
  } finally {
    stage.creating = false
  }
}

// 批量创建所有关卡
async function createAllStages() {
  creatingStages.value = true
  stageProgress.show = true
  stageProgress.created = 0
  stageProgress.total = createdPractices.value.reduce((sum, p) => sum + p.stages.length, 0)
  stageProgress.percent = 0
  stageProgress.status = 'active'

  try {
    for (const practice of createdPractices.value) {
      for (const stage of practice.stages) {
        if (!stage.created) {
          await createStage(practice.id, stage)
        }
      }
    }

    stageProgress.status = 'success'
    message.success('所有关卡创建完成')

    // 准备总结数据
    prepareSummary()
    emit('next')
  } catch (error) {
    stageProgress.status = 'exception'
    message.error('批量创建失败：' + error.message)
  } finally {
    creatingStages.value = false
  }
}

// 跳过关卡创建
function skipStages() {
  prepareSummary()
  emit('next')
}

// 准备导入总结
function prepareSummary() {
  const duration = Math.round((Date.now() - startTime.value) / 1000)

  importSummary.practices = createdPractices.value.length
  importSummary.stages = stageProgress.created
  importSummary.successRate = Math.round(
    (createdPractices.value.length / props.practices.length) * 100
  )
  importSummary.duration = duration
}

// 完成导入
function finish() {
  emit('complete', {
    success: importSummary.practices,
    total: props.practices.length
  })
}

// 查看实践列表
function viewPractices() {
  router.push('/course/practice/my-practices')
}
</script>

<style scoped lang="less">
.practice-import-flow {
  .step-actions {
    margin-top: 24px;
    display: flex;
    justify-content: flex-end;
  }

  .progress-text {
    text-align: center;
    margin-top: 8px;
    color: #666;
  }

  .stage-progress {
    margin-top: 24px;

    .progress-info {
      text-align: center;
      margin-top: 8px;
      color: #666;
    }
  }
}
</style>