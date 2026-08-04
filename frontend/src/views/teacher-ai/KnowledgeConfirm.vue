<template>
  <PageShell max-width="default" class="knowledge-confirm">
    <PageHeaderBar
      title="知识点确认"
      subtitle="确认 AI 拆解出的知识点，删除无关项后进入关卡生成"
      show-back
    />

    <Stack :gap="4" class="content">
      <a-alert
        v-if="loadError"
        type="error"
        :message="loadError"
        show-icon
      />

      <a-card title="知识点列表">
        <a-table
          :columns="columns"
          :data-source="knowledgePoints"
          :loading="loading"
          :pagination="false"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'source'">
              {{ record.source_refs_json?.[0]?.chunk_id }} · {{ record.source_refs_json?.[0]?.location }}
            </template>
            <template v-else-if="column.key === 'suggested_challenge_type'">
              <a-tag :color="record.suggested_challenge_type === 'auto' ? 'green' : 'default'">
                {{ record.suggested_challenge_type === 'auto' ? '建议生成关卡' : '仅背景知识' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'status'">
              <a-tag :color="record.selected ? 'blue' : 'red'">
                {{ record.selected ? '已保留' : '已删除' }}
              </a-tag>
            </template>
            <template v-else-if="column.key === 'actions'">
              <a-space>
                <a-button
                  type="link"
                  size="small"
                  :disabled="record.selected"
                  @click="handleConfirm(record)"
                >
                  确认
                </a-button>
                <a-button
                  type="link"
                  danger
                  size="small"
                  :disabled="!record.selected"
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
        <a-button
          type="primary"
          :loading="generating"
          :disabled="confirmedCount === 0"
          @click="handleNext"
        >
          下一步：生成关卡草稿（{{ confirmedCount }} 个知识点）
        </a-button>
      </div>
    </Stack>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRoute, useRouter } from 'vue-router'
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
import Stack from '@/components/common/Stack.vue'
import {
  getKnowledgePoints,
  confirmKnowledgePoints,
  generateChallengeDrafts,
  type KnowledgePoint
} from '@/api/teacher-ai'

const route = useRoute()
const router = useRouter()

const jobId = route.params.jobId as string

const columns = [
  { title: '知识点名称', dataIndex: 'title', key: 'title' },
  { title: '简要说明', dataIndex: 'summary', key: 'summary' },
  { title: '来源位置', key: 'source' },
  { title: '建议难度', dataIndex: 'suggested_difficulty', key: 'suggested_difficulty', width: 100 },
  { title: '建议生成关卡', key: 'suggested_challenge_type', width: 140 },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'actions', width: 140 }
]

const knowledgePoints = ref<KnowledgePoint[]>([])
const loading = ref(false)
const generating = ref(false)
const loadError = ref('')

const loadKnowledgePoints = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const result = await getKnowledgePoints(jobId)
    knowledgePoints.value = result as unknown as KnowledgePoint[]
  } catch (error) {
    loadError.value = '加载知识点失败，请检查后端服务是否已启动'
    console.error(error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadKnowledgePoints()
})

const confirmedCount = computed(
  () => knowledgePoints.value.filter((kp) => kp.selected).length
)

const persistSelection = async () => {
  const selectedIds = knowledgePoints.value.filter((kp) => kp.selected).map((kp) => kp.id)
  try {
    await confirmKnowledgePoints(jobId, selectedIds)
  } catch (error) {
    message.error('保存知识点确认状态失败')
    console.error(error)
  }
}

const handleConfirm = (record: KnowledgePoint) => {
  record.selected = true
  persistSelection()
}

const handleRemove = (record: KnowledgePoint) => {
  record.selected = false
  persistSelection()
}

const handleNext = async () => {
  generating.value = true
  try {
    const drafts = await generateChallengeDrafts(jobId, confirmedCount.value)
    message.success(`AI 生成了 ${(drafts as any)?.length ?? 0} 个关卡草稿`)
    router.push(`/teacher/ai-practice-generator/${jobId}/drafts`)
  } catch (error) {
    message.error('生成关卡草稿失败，请检查后端服务是否已启动')
    console.error(error)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped lang="less">
.knowledge-confirm {
  .actions {
    display: flex;
    justify-content: center;
    gap: var(--hx-space-4);
    flex-wrap: wrap;
  }
}
</style>
