<template>
  <PageShell max-width="default" class="drafts-review">
    <PageHeaderBar
      title="关卡草稿审核"
      subtitle="AI 生成的实践关卡草稿，老师审核后可保存为实践课程"
      show-back
    />

    <Stack :gap="4" class="content">
      <a-alert
        v-if="loadError"
        type="error"
        :message="loadError"
        show-icon
      />

      <a-spin :spinning="loading">
        <a-empty v-if="!loading && drafts.length === 0" description="暂无草稿，请返回上一步生成" />

        <a-collapse v-else v-model:activeKey="activeKeys">
          <a-collapse-panel v-for="draft in drafts" :key="draft.id">
            <template #header>
              <a-space>
                <span class="draft-title">{{ draft.title }}</span>
                <a-tag>{{ draft.difficulty }}</a-tag>
                <a-tag :color="draft.evaluation_mode === 'auto' ? 'green' : 'orange'">
                  {{ draft.evaluation_mode === 'auto' ? '自动评测' : '人工验收' }}
                </a-tag>
              </a-space>
            </template>

            <a-descriptions :column="1" bordered size="small">
              <a-descriptions-item label="技能标签">
                <a-tag v-for="tag in draft.skill_tags_json ?? []" :key="tag">{{ tag }}</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="任务说明">
                <div class="markdown-block">{{ draft.task_markdown }}</div>
              </a-descriptions-item>
              <a-descriptions-item v-if="draft.student_files_json" label="学生任务文件模板">
                <pre class="code-block">{{ firstFileContent(draft.student_files_json) }}</pre>
              </a-descriptions-item>
              <a-descriptions-item label="可见测试集">
                {{ draft.test_cases_json?.length ?? 0 }} 条
              </a-descriptions-item>
              <a-descriptions-item label="隐藏测试集">
                {{ draft.hidden_test_cases_json?.length ?? 0 }} 条（学生不可见）
              </a-descriptions-item>
              <a-descriptions-item label="参考答案（仅教师可见）">
                <pre class="code-block reference">{{ draft.reference_answer }}</pre>
              </a-descriptions-item>
              <a-descriptions-item label="状态">
                <a-tag>{{ draft.status }}</a-tag>
              </a-descriptions-item>
            </a-descriptions>
          </a-collapse-panel>
        </a-collapse>
      </a-spin>

      <a-alert
        type="info"
        show-icon
        message="「保存为实践课程」尚未实现"
        description="需要先对接现有实践课程创建流程（practices 表体系），当前版本审核到此为止。"
      />

      <div class="actions">
        <a-button @click="() => $router.back()">上一步</a-button>
      </div>
    </Stack>
  </PageShell>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
import Stack from '@/components/common/Stack.vue'
import { getChallengeDrafts, type ChallengeDraft } from '@/api/teacher-ai'

const route = useRoute()
const jobId = route.params.jobId as string

const drafts = ref<ChallengeDraft[]>([])
const loading = ref(false)
const loadError = ref('')
const activeKeys = ref<string[]>([])

const firstFileContent = (files: Record<string, string>) => {
  const values = Object.values(files ?? {})
  return values.length > 0 ? values[0] : ''
}

onMounted(async () => {
  loading.value = true
  loadError.value = ''
  try {
    const result = await getChallengeDrafts(jobId)
    drafts.value = result as unknown as ChallengeDraft[]
    activeKeys.value = drafts.value.map((d) => d.id)
  } catch (error) {
    loadError.value = '加载关卡草稿失败，请检查后端服务是否已启动'
    console.error(error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="less">
.drafts-review {
  .draft-title {
    font-weight: 600;
    color: var(--hx-color-text-primary);
  }

  .markdown-block {
    white-space: pre-wrap;
  }

  .code-block {
    background: var(--hx-color-bg-layout);
    padding: var(--hx-space-3);
    border-radius: var(--hx-radius-sm);
    font-family: var(--hx-font-mono);
    font-size: var(--hx-font-size-sm);
    white-space: pre-wrap;
    margin: 0;

    &.reference {
      background: #fffbe6;
      border: 1px solid #ffe58f;
    }
  }

  .actions {
    display: flex;
    justify-content: center;
  }
}
</style>
