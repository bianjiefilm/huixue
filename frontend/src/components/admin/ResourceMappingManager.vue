<template>
  <div class="resource-mapping-manager">
    <a-space direction="vertical" style="width: 100%">
      <a-alert
        message="资源映射说明"
        description="管理课程资源目录中不同类型资源到系统模块的映射关系"
        type="info"
        show-icon
      />

      <a-row :gutter="16">
        <a-col :span="8">
          <a-card title="课程资源结构" size="small">
            <a-tree
              :tree-data="courseTreeData"
              :selected-keys="selectedKeys"
              @select="onTreeSelect"
              show-line
              :show-icon="true"
            >
              <template #icon="{ dataRef }">
                <FolderOutlined v-if="dataRef.type === 'folder'" />
                <FileTextOutlined v-else-if="dataRef.type === 'doc'" />
                <CodeOutlined v-else-if="dataRef.type === 'practice'" />
                <QuestionCircleOutlined v-else-if="dataRef.type === 'question'" />
                <ExperimentOutlined v-else-if="dataRef.type === 'training'" />
              </template>
            </a-tree>
          </a-card>
        </a-col>

        <a-col :span="16">
          <a-card title="映射配置" size="small">
            <div v-if="selectedNode">
              <a-descriptions :title="selectedNode.title" bordered :column="2">
                <a-descriptions-item label="路径">
                  {{ selectedNode.path }}
                </a-descriptions-item>
                <a-descriptions-item label="类型">
                  <a-tag :color="getTypeColor(selectedNode.type)">
                    {{ getTypeName(selectedNode.type) }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="状态" :span="2">
                  <a-badge
                    :status="selectedNode.mapped ? 'success' : 'default'"
                    :text="selectedNode.mapped ? '已映射' : '未映射'"
                  />
                </a-descriptions-item>
              </a-descriptions>

              <a-divider>映射配置</a-divider>

              <a-form :model="mappingConfig" layout="vertical">
                <a-form-item label="目标模块">
                  <a-select v-model:value="mappingConfig.targetModule" style="width: 200px">
                    <a-select-option value="practice">实践课程</a-select-option>
                    <a-select-option value="training">实训项目</a-select-option>
                    <a-select-option value="question">题库</a-select-option>
                    <a-select-option value="material">教材资源</a-select-option>
                  </a-select>
                </a-form-item>

                <a-form-item label="处理策略">
                  <a-checkbox-group v-model:value="mappingConfig.strategies">
                    <a-checkbox value="extract">提取内容</a-checkbox>
                    <a-checkbox value="transform">格式转换</a-checkbox>
                    <a-checkbox value="validate">数据验证</a-checkbox>
                    <a-checkbox value="autoImport">自动导入</a-checkbox>
                  </a-checkbox-group>
                </a-form-item>

                <a-form-item label="映射规则" v-if="mappingConfig.targetModule">
                  <a-textarea
                    v-model:value="mappingConfig.rules"
                    :rows="4"
                    placeholder="输入JSON格式的映射规则"
                  />
                </a-form-item>

                <a-form-item>
                  <a-space>
                    <a-button type="primary" @click="saveMapping">
                      保存映射
                    </a-button>
                    <a-button @click="testMapping">
                      测试映射
                    </a-button>
                    <a-button danger @click="removeMapping" v-if="selectedNode.mapped">
                      移除映射
                    </a-button>
                  </a-space>
                </a-form-item>
              </a-form>
            </div>
            <a-empty v-else description="请选择要配置的资源" />
          </a-card>
        </a-col>
      </a-row>

      <a-divider>批量操作</a-divider>

      <a-card title="批量映射规则" size="small">
        <a-space direction="vertical" style="width: 100%">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="源路径模式">
                <a-input
                  v-model:value="batchMapping.sourcePattern"
                  placeholder="如: */03-微型实验/*"
                />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="目标模块">
                <a-select v-model:value="batchMapping.targetModule" style="width: 100%">
                  <a-select-option value="practice">实践课程</a-select-option>
                  <a-select-option value="training">实训项目</a-select-option>
                  <a-select-option value="question">题库</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>

          <a-button type="primary" @click="applyBatchMapping">
            应用批量映射
          </a-button>

          <a-table
            v-if="batchMappingResult.length > 0"
            :dataSource="batchMappingResult"
            :columns="batchColumns"
            size="small"
            :pagination="{ pageSize: 10 }"
          />
        </a-space>
      </a-card>
    </a-space>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import {
  FolderOutlined,
  FileTextOutlined,
  CodeOutlined,
  QuestionCircleOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue'

// 课程资源树形数据
const courseTreeData = ref([
  {
    title: 'Python程序设计',
    key: 'python',
    type: 'folder',
    path: 'ziyuan/课程资源/Python程序设计',
    children: [
      {
        title: '01-课程文档',
        key: 'python-docs',
        type: 'doc',
        path: 'ziyuan/课程资源/Python程序设计/01-课程文档'
      },
      {
        title: '02-理论课件',
        key: 'python-theory',
        type: 'doc',
        path: 'ziyuan/课程资源/Python程序设计/02-理论课件'
      },
      {
        title: '03-微型实验',
        key: 'python-practice',
        type: 'practice',
        path: 'ziyuan/课程资源/Python程序设计/03-微型实验',
        children: [
          {
            title: '实践1-基础语法',
            key: 'python-practice-1',
            type: 'practice',
            path: 'ziyuan/课程资源/Python程序设计/03-微型实验/实践1-基础语法'
          },
          {
            title: '实践2-函数模块',
            key: 'python-practice-2',
            type: 'practice',
            path: 'ziyuan/课程资源/Python程序设计/03-微型实验/实践2-函数模块'
          }
        ]
      },
      {
        title: '04-考试评测',
        key: 'python-exam',
        type: 'question',
        path: 'ziyuan/课程资源/Python程序设计/04-考试评测'
      },
      {
        title: '05-相关实训',
        key: 'python-training',
        type: 'training',
        path: 'ziyuan/课程资源/Python程序设计/05-相关实训'
      }
    ]
  },
  {
    title: 'Spark编程基础',
    key: 'spark',
    type: 'folder',
    path: 'ziyuan/课程资源/Spark编程基础',
    children: [
      {
        title: '01-课程文档',
        key: 'spark-docs',
        type: 'doc',
        path: 'ziyuan/课程资源/Spark编程基础/01-课程文档'
      },
      {
        title: '03-微型实验',
        key: 'spark-practice',
        type: 'practice',
        path: 'ziyuan/课程资源/Spark编程基础/03-微型实验',
        children: [
          {
            title: '实践1-Spark环境与基础操作闯关',
            key: 'spark-practice-1',
            type: 'practice',
            path: 'ziyuan/课程资源/Spark编程基础/03-微型实验/实践1-Spark环境与基础操作闯关'
          }
        ]
      }
    ]
  }
])

const selectedKeys = ref([])
const selectedNode = ref(null)

const mappingConfig = reactive({
  targetModule: '',
  strategies: [],
  rules: ''
})

const batchMapping = reactive({
  sourcePattern: '',
  targetModule: ''
})

const batchMappingResult = ref([])

const batchColumns = [
  {
    title: '资源路径',
    dataIndex: 'path',
    key: 'path'
  },
  {
    title: '目标模块',
    dataIndex: 'targetModule',
    key: 'targetModule'
  },
  {
    title: '状态',
    dataIndex: 'status',
    key: 'status'
  }
]

// 选择树节点
function onTreeSelect(keys, { node }) {
  selectedKeys.value = keys
  selectedNode.value = node.dataRef || node

  // 加载已有映射配置
  loadMappingConfig(selectedNode.value)
}

// 加载映射配置
function loadMappingConfig(node) {
  // 从存储中加载已有配置
  const stored = localStorage.getItem(`mapping_${node.key}`)
  if (stored) {
    const config = JSON.parse(stored)
    mappingConfig.targetModule = config.targetModule
    mappingConfig.strategies = config.strategies
    mappingConfig.rules = config.rules
    node.mapped = true
  } else {
    // 根据类型设置默认配置
    switch (node.type) {
      case 'practice':
        mappingConfig.targetModule = 'practice'
        mappingConfig.strategies = ['extract', 'validate']
        break
      case 'question':
        mappingConfig.targetModule = 'question'
        mappingConfig.strategies = ['extract', 'transform']
        break
      case 'training':
        mappingConfig.targetModule = 'training'
        mappingConfig.strategies = ['validate', 'autoImport']
        break
      default:
        mappingConfig.targetModule = ''
        mappingConfig.strategies = []
    }
    mappingConfig.rules = ''
  }
}

// 保存映射
function saveMapping() {
  if (!selectedNode.value || !mappingConfig.targetModule) {
    message.warning('请选择目标模块')
    return
  }

  const config = {
    targetModule: mappingConfig.targetModule,
    strategies: mappingConfig.strategies,
    rules: mappingConfig.rules
  }

  localStorage.setItem(`mapping_${selectedNode.value.key}`, JSON.stringify(config))
  selectedNode.value.mapped = true
  message.success('映射配置已保存')
}

// 测试映射
async function testMapping() {
  if (!selectedNode.value) {
    message.warning('请先选择资源')
    return
  }

  message.loading('正在测试映射...')

  // 模拟测试过程
  setTimeout(() => {
    message.success('映射测试通过')
  }, 1500)
}

// 移除映射
function removeMapping() {
  if (!selectedNode.value) return

  localStorage.removeItem(`mapping_${selectedNode.value.key}`)
  selectedNode.value.mapped = false
  mappingConfig.targetModule = ''
  mappingConfig.strategies = []
  mappingConfig.rules = ''
  message.success('映射已移除')
}

// 应用批量映射
function applyBatchMapping() {
  if (!batchMapping.sourcePattern || !batchMapping.targetModule) {
    message.warning('请填写完整的批量映射规则')
    return
  }

  // 模拟批量映射结果
  batchMappingResult.value = [
    {
      path: 'ziyuan/课程资源/Python程序设计/03-微型实验/实践1',
      targetModule: batchMapping.targetModule,
      status: '成功'
    },
    {
      path: 'ziyuan/课程资源/Python程序设计/03-微型实验/实践2',
      targetModule: batchMapping.targetModule,
      status: '成功'
    },
    {
      path: 'ziyuan/课程资源/Spark编程基础/03-微型实验/实践1',
      targetModule: batchMapping.targetModule,
      status: '成功'
    }
  ]

  message.success(`批量映射完成，共处理 ${batchMappingResult.value.length} 个资源`)
}

// 获取类型颜色
function getTypeColor(type) {
  const colors = {
    folder: 'default',
    doc: 'blue',
    practice: 'green',
    question: 'orange',
    training: 'purple'
  }
  return colors[type] || 'default'
}

// 获取类型名称
function getTypeName(type) {
  const names = {
    folder: '文件夹',
    doc: '文档',
    practice: '实践',
    question: '题库',
    training: '实训'
  }
  return names[type] || type
}
</script>

<style scoped lang="less">
.resource-mapping-manager {
  .ant-tree {
    max-height: 500px;
    overflow-y: auto;
  }
}
</style>