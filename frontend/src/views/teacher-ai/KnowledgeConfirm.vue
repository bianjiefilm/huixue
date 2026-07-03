<template>
  <div class="knowledge-confirm">
    <a-page-header
      title="知识点确认"
      sub-title="确认 AI 拆解出的知识点，删除无关项后进入关卡生成"
      @back="() => $router.back()"
    />

    <div class="content">
      <a-alert
        message="当前为占位数据"
        description="本页展示的知识点为 mock 假数据，用于走通交互与布局。后续接入 @/api/teacher-ai.ts 的 getKnowledgePoints / confirmKnowledgePoints 接口后替换为真实数据。"
        type="warning"
        show-icon
        style="margin-bottom: 16px"
      />

      <a-card title="知识点列表">
        <a-table
          :columns="columns"
          :data-source="knowledgePoints"
          :pagination="false"
          row-key="knowledge_point_id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'source'">
              {{ record.source.document_title }} · {{ record.source.location }}
            </template>
            <template v-else-if="column.key === 'suggested_for_challenge'">
              <a-tag :color="record.suggested_for_challenge ? 'green' : 'default'">
                {{ record.suggested_for_challenge ? '建议生成关卡' : '仅背景知识' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.confirmed ? 'blue' : 'red'">
                {{ record.confirmed ? '已保留' : '已删除' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  :disabled="record.confirmed"
                  @click="handleConfirm(record)"
                >
                  确认
                </a-button>
                <a-button
                  type="link"
                  danger
                  size="small"
                  :disabled="!record.confirmed"
                  @click="handleRemove(record)"
                >
                  删除
                </a-button>
              </a-space>
            </template>
          </template>
        </a-table>
      </a-card>

      <div class="actions">
        <a-button @click="() => $router.back()">上一步</a-button>
        <a-button type="primary" :disabled="confirmedCount === 0" @click="handleNext">
          下一步：生成关卡草稿（{{ confirmedCount }} 个知识点）
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import type { KnowledgePoint } from '@/api/teacher-ai'
// TODO: 接入真实接口后替换 mock 数据：
// import { getKnowledgePoints, confirmKnowledgePoints } from '@/api/teacher-ai'

const route = useRoute()
const router = useRouter()

const jobId = route.params.jobId as string

const columns = [
  { title: '知识点名称', dataIndex: 'name', key: 'name' },
  { title: '简要说明', dataIndex: 'summary', key: 'summary' },
  { title: '来源位置', key: 'source' },
  { title: '建议难度', dataIndex: 'suggested_difficulty', key: 'suggested_difficulty', width: 100 },
  { title: '建议生成关卡', key: 'suggested_for_challenge', width: 140 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 140 }
]

// TODO: mock 数据，接入 getKnowledgePoints(jobId) 后删除
const knowledgePoints = ref<KnowledgePoint[]>([
  {
    knowledge_point_id: 'kp_1',
    name: 'CSV 文件读取',
    summary: '使用 pandas 读取 CSV 文件并预览数据结构',
    source: { document_id: 'doc_1', document_title: '数据分析基础课件', location: '第 3 页' },
    suggested_difficulty: '零基础',
    suggested_for_challenge: true,
    confirmed: true
  },
  {
    knowledge_point_id: 'kp_2',
    name: '缺失值处理',
    summary: '识别并处理数据集中的缺失值（删除/填充）',
    source: { document_id: 'doc_1', document_title: '数据分析基础课件', location: '第 7 页' },
    suggested_difficulty: '入门',
    suggested_for_challenge: true,
    confirmed: true
  },
  {
    knowledge_point_id: 'kp_3',
    name: '字段清洗',
    summary: '统一字段格式、去除异常字符、类型转换',
    source: { document_id: 'doc_1', document_title: '数据分析基础课件', location: '第 9 页' },
    suggested_difficulty: '入门',
    suggested_for_challenge: true,
    confirmed: true
  },
  {
    knowledge_point_id: 'kp_4',
    name: '数据分析发展史',
    summary: '数据分析学科的历史背景介绍',
    source: { document_id: 'doc_1', document_title: '数据分析基础课件', location: '第 1 页' },
    suggested_difficulty: '零基础',
    suggested_for_challenge: false,
    confirmed: false
  },
  {
    knowledge_point_id: 'kp_5',
    name: '基础可视化',
    summary: '使用 matplotlib 绘制柱状图、折线图展示清洗后的数据',
    source: { document_id: 'doc_1', document_title: '数据分析基础课件', location: '第 14 页' },
    suggested_difficulty: '中等',
    suggested_for_challenge: true,
    confirmed: true
  }
])

const confirmedCount = computed(
  () => knowledgePoints.value.filter((kp) => kp.confirmed).length
)

const handleConfirm = (record: KnowledgePoint) => {
  record.confirmed = true
  // TODO: 调用 confirmKnowledgePoints(jobId, { confirmed_ids: [...], removed_ids: [...] })
}

const handleRemove = (record: KnowledgePoint) => {
  record.confirmed = false
  // TODO: 调用 confirmKnowledgePoints(jobId, { confirmed_ids: [...], removed_ids: [...] })
}

const handleNext = () => {
  // TODO: 调用 generateChallengeDrafts(jobId) 后跳转草稿审核页
  message.info('关卡草稿生成/审核页尚未实现，敬请期待')
  router.push(`/teacher/ai-practice-generator/${jobId}/drafts`)
}
</script>

<style scoped lang="less">
.knowledge-confirm {
  background-color: #f0f2f5;
  min-height: 100vh;

  .content {
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .actions {
    margin-top: 24px;
    text-align: center;

    button {
      margin: 0 8px;
    }
  }
}
</style>
