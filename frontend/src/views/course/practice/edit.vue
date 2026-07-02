<template>
  <div class="practice-edit-page">
    <div class="page-header">
      <a-page-header
        :title="practiceInfo.name"
        :sub-title="getDifficultyText(practiceInfo.difficulty)"
        :backIcon="false"
      >
        <template #extra>
          <!-- 基础信息编辑按钮 -->
          <a-button @click="showEditBasicInfo">
            <template #icon><EditOutlined /></template>
            编辑
          </a-button>
          <a-button @click="goBackToList">返回列表</a-button>
          <!-- 未发布状态显示发布按钮 -->
          <a-button v-if="canPublish" type="primary" @click="showPublishModal">发布</a-button>
          <!-- 已发布状态显示添加到课堂和下架按钮 -->
          <template v-if="isPublished">
            <a-button type="primary" @click="showAddToClassroomModal">添加到课堂</a-button>
            <a-button danger @click="showUnpublishConfirm">下架</a-button>
          </template>
          <!-- 审核中状态显示状态标签 -->
          <a-tag v-if="isPending" color="orange">审核中</a-tag>
        </template>
        <template #footer>
          <a-tabs v-model:activeKey="activeTab">
            <a-tab-pane key="task" tab="任务"></a-tab-pane>
            <a-tab-pane key="repo" tab="代码仓库"></a-tab-pane>
            <a-tab-pane key="data" tab="数据集"></a-tab-pane>
            <a-tab-pane key="config" tab="配置"></a-tab-pane>
          </a-tabs>
        </template>
      </a-page-header>
    </div>

    <div class="page-content">
      <a-card>
        <div v-if="activeTab === 'task'">
          <div class="task-header">
            <a-space direction="vertical" style="width: 100%">
              <div class="intro-header">
                <h3>实践介绍</h3>
                <p>{{ practiceInfo.introduction || '暂无实践介绍' }}</p>
              </div>
              <a-button type="primary" @click="showAddTask">
                <template #icon><PlusOutlined /></template>
                新增实践任务
              </a-button>
            </a-space>
          </div>
          <div class="task-list">
            <a-spin :spinning="loadingStages">
              <div v-if="stages.length > 0" class="stages-container">
                <a-list
                  :data-source="stages"
                  :grid="{ gutter: 16, xs: 1, sm: 1, md: 2, lg: 2, xl: 3, xxl: 3 }"
                >
                  <template #renderItem="{ item, index }">
                    <a-list-item
                      :draggable="true"
                      @dragstart="handleDragStart($event, index)"
                      @dragend="handleDragEnd"
                      @dragover="handleDragOver"
                      @drop="handleDrop($event, index)"
                      :class="{ 'dragging': draggedIndex === index }"
                      style="cursor: move;"
                    >
                      <a-card hoverable>
                        <template #title>
                          <div class="stage-card-title">
                            <span>第{{ index + 1 }}关：{{ item.title }}</span>
                            <a-tag :color="getDifficultyColor(item.difficulty)">
                              {{ getDifficultyText(item.difficulty) }}
                            </a-tag>
                          </div>
                        </template>
                        <template #extra>
                          <a-dropdown>
                            <a-button type="text" size="small">
                              <template #icon><EllipsisOutlined /></template>
                            </a-button>
                            <template #overlay>
                              <a-menu>
                                <a-menu-item @click="testStage(item)">
                                  <PlayCircleOutlined /> 测试
                                </a-menu-item>
                                <a-menu-item @click="editStage(item)">
                                  <EditOutlined /> 编辑
                                </a-menu-item>
                                <a-menu-item @click="deleteStage(item)" danger>
                                  <DeleteOutlined /> 删除
                                </a-menu-item>
                              </a-menu>
                            </template>
                          </a-dropdown>
                        </template>
                        
                        <div class="stage-card-content">
                          <div class="stage-type">
                            <span>题型：</span>
                            <a-tag>{{ getTaskTypeText(item.task_type) }}</a-tag>
                          </div>
                          
                          <div v-if="item.skills && item.skills.length > 0" class="stage-skills">
                            <span>技能：</span>
                            <a-tag v-for="skill in item.skills" :key="skill" size="small">
                              {{ skill }}
                            </a-tag>
                          </div>
                          
                          <div class="stage-coin">
                            <span>金币：</span>
                            <span class="coin-value">{{ item.coin || 0 }}</span>
                          </div>
                        </div>
                      </a-card>
                    </a-list-item>
                  </template>
                </a-list>
              </div>
              <a-empty v-else description="暂无实践任务，点击上方按钮添加" />
            </a-spin>
          </div>
        </div>

        <div v-else-if="activeTab === 'repo'">
          <RepoTab :practice-id="practiceId" />
        </div>

        <div v-else-if="activeTab === 'data'">
          <DatasetTab :practice-id="practiceId" />
        </div>

        <div v-else-if="activeTab === 'config'">
          <div class="config-container">
            <h3 class="config-title">实践环境配置</h3>
            <a-divider />
            
            <a-form :model="configForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 14 }">
              <a-form-item label="代码编辑器">
                <a-switch v-model:checked="configForm.codeEditor" />
                <span class="form-item-hint">{{ configForm.codeEditor ? '已开启' : '已关闭' }}，默认开启，若课程只需要使用命令行不需要代码编辑器则可以关闭</span>
              </a-form-item>
              
              <a-form-item label="命令行">
                <a-switch v-model:checked="configForm.commandLine" />
                <span class="form-item-hint">{{ configForm.commandLine ? '已开启' : '已关闭' }}，默认关闭，若课程需要使用命令行则需手动开启</span>
              </a-form-item>
              
              <a-divider />
              <h3 class="config-title">实践交互配置</h3>
              
              <a-form-item label="代码仓库文件可见性">
                <a-radio-group v-model:value="configForm.repoVisibility">
                  <a-radio value="visible">可见</a-radio>
                  <a-radio value="hidden">不可见</a-radio>
                </a-radio-group>
                <div class="form-item-hint">
                  选择不可见时，在关卡练习页面不可查看代码仓库，仅可在每一关中查看到该关卡设置的学生代码文件
                </div>
              </a-form-item>
              
              <a-form-item label="实践关卡跳关">
                <a-radio-group v-model:value="configForm.allowSkip">
                  <a-radio value="allow">允许跳关</a-radio>
                  <a-radio value="disallow">不允许跳关</a-radio>
                </a-radio-group>
                <div class="form-item-hint">
                  默认允许跳关，学生做题时可自由切换关卡，自主选择做题顺序；设置不允许跳关后，学生只能按顺序进行实践练习，在前一关通关后才可开启下一关，建议在课程关卡前后有强关联时设置不允许跳关
                </div>
              </a-form-item>
              
              <a-form-item :wrapper-col="{ offset: 6 }">
                <a-button type="primary" @click="saveConfig" :loading="configLoading">保存配置</a-button>
              </a-form-item>
            </a-form>
          </div>
        </div>
      </a-card>
    </div>

    <!-- 添加/编辑任务的模态框 -->
    <a-modal
      v-model:open="addTaskVisible"
      :title="editingStage ? '编辑实践任务' : '新增实践任务'"
      width="1000px"
      :footer="null"
      :destroyOnClose="true"
      @cancel="handleCancelEdit"
    >
      <StageEditor
        :practice-id="practiceId"
        :stage-id="editingStage?.id"
        @success="handleStageSuccess"
        @cancel="handleCancelEdit"
      />
    </a-modal>
    
    <!-- 发布实践的模态框 -->
    <a-modal
      v-model:open="publishModalVisible"
      title="发布实践课程"
      width="500px"
      :footer="null"
      @cancel="publishModalVisible = false"
    >
      <div class="publish-modal-content">
        <p class="publish-description">请选择发布方式：</p>
        
        <a-radio-group v-model:value="publishForm.visibility" class="publish-options">
          <a-space direction="vertical">
            <a-radio value="public">
              <div class="publish-option">
                <div class="publish-option-title">公开发布</div>
                <div class="publish-option-desc">公开发布需经过后台审核，审核通过后该实践将加入实践课程库，对所有用户可见</div>
              </div>
            </a-radio>
            
            <a-radio value="private">
              <div class="publish-option">
                <div class="publish-option-title">仅自己可见</div>
                <div class="publish-option-desc">选择仅自己可见发布则不需要进行后台审核，课程发布后仅可自己使用</div>
              </div>
            </a-radio>
          </a-space>
        </a-radio-group>
        
        <div class="publish-footer">
          <a-space>
            <a-button @click="publishModalVisible = false">取消</a-button>
            <a-button type="primary" @click="publishPracticeHandler" :loading="publishLoading">确认发布</a-button>
          </a-space>
        </div>
      </div>
    </a-modal>

    <!-- 添加到课堂模态框 -->
    <a-modal
      v-model:open="addToClassroomVisible"
      title="添加到课堂"
      width="500px"
      :confirmLoading="addToClassroomLoading"
      @ok="handleAddToClassroom"
      @cancel="addToClassroomVisible = false"
    >
      <a-spin :spinning="addToClassroomLoading">
        <div class="classroom-select">
          <p>请选择要添加到的课堂：</p>
          <a-select
            v-model:value="selectedClassroomId"
            placeholder="请选择课堂"
            style="width: 100%"
            :options="classroomList.map(c => ({ value: c.id, label: c.name || c.title }))"
          />
        </div>
      </a-spin>
    </a-modal>

    <!-- 基础信息编辑模态框 -->
    <a-modal
      v-model:open="editBasicInfoVisible"
      title="编辑实践课程信息"
      width="600px"
      :confirmLoading="savingBasicInfo"
      @ok="handleSaveBasicInfo"
      @cancel="editBasicInfoVisible = false"
    >
      <a-form :model="basicInfoForm" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="实践名称" required>
          <a-input
            v-model:value="basicInfoForm.name"
            placeholder="请输入实践课程名称"
            :maxLength="50"
            show-count
          />
        </a-form-item>
        <a-form-item label="实践类型" required>
          <a-radio-group v-model:value="basicInfoForm.type">
            <a-radio value="code">在线编码实践</a-radio>
            <a-radio value="desktop">云桌面实践</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="难易程度" required>
          <a-radio-group v-model:value="basicInfoForm.difficulty">
            <a-radio value="easy">初级</a-radio>
            <a-radio value="intermediate">中级</a-radio>
            <a-radio value="advanced">高级</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="实践介绍" required>
          <a-textarea
            v-model:value="basicInfoForm.introduction"
            placeholder="请输入实践课程介绍"
            :rows="4"
            :maxLength="500"
            show-count
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { message, Modal } from 'ant-design-vue';
import { get } from '@/utils/request';
import { PlusOutlined, ExclamationCircleOutlined, EditOutlined, DeleteOutlined, EllipsisOutlined, PlayCircleOutlined } from '@ant-design/icons-vue';
import RepoTab from '../../../components/practice/RepoTab.vue';
import DatasetTab from '../../../components/practice/DatasetTab.vue';
import StageEditor from '../../../components/practice/StageEditor.vue';
import { useUserStore } from '../../../stores/user';
import {
  getPracticeStages,
  deletePracticeStage,
  updateStageOrder,
  getPracticeConfig,
  updatePracticeConfig,
  publishPractice,
  updatePracticeBasicInfo,
  type PracticeStage,
  type PracticeConfig,
  type PublishRequest,
  type BasicInfoRequest
} from '../../../api/practice';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const activeTab = ref('task');
const addTaskVisible = ref(false);
const publishModalVisible = ref(false);
const publishLoading = ref(false);

// 获取实践ID
const practiceId = computed(() => Number(route.params.id));
const creatorId = computed(() => userStore.userInfo.id);

const requireCurrentUserId = () => {
  const userId = userStore.userId;
  if (!userId) {
    message.warning('请先登录后再管理实践课程');
    router.push('/login?redirect=' + encodeURIComponent(route.fullPath));
    throw new Error('Missing current user id');
  }
  return userId;
};

// 关卡数据
const stages = ref<PracticeStage[]>([]);
const loadingStages = ref(false);
const editingStage = ref<PracticeStage | null>(null);

// 拖拽相关
const draggedIndex = ref<number | null>(null);
const isDragging = ref(false);

// 模拟的实践信息
const practiceInfo = reactive({
  id: route.params.id as string,
  name: '实践课程名称',
  introduction: '这是一个实践课程的介绍，详细描述了实践的主要内容和学习目标。',
  type: 'code',
  difficulty: 'beginner',
  status: 'draft', // 草稿状态: draft, editing, published, pending
  visibility: '' // 可见性: PRIVATE, PUBLIC
});

// 发布状态计算属性
const canPublish = computed(() => {
  return practiceInfo.status === 'draft' || practiceInfo.status === 'editing';
});

const isPublished = computed(() => {
  return practiceInfo.status === 'published' || practiceInfo.status === 'published_personal';
});

const isPending = computed(() => {
  return practiceInfo.status === 'pending' || practiceInfo.status === 'auditing';
});

// 添加到课堂模态框
const addToClassroomVisible = ref(false);
const classroomList = ref<any[]>([]);
const selectedClassroomId = ref<string | null>(null);
const addToClassroomLoading = ref(false);

// 配置表单
const configForm = reactive({
  codeEditor: true, // 代码编辑器，默认开启
  commandLine: false, // 命令行，默认关闭
  repoVisibility: 'visible', // 代码仓库可见性，默认可见
  allowSkip: 'allow' // 是否允许跳关，默认允许
});

// 配置加载状态
const configLoading = ref(false);

// 发布表单
const publishForm = reactive({
  visibility: 'public' // 发布可见性，默认公开
});

// 基础信息编辑表单
const editBasicInfoVisible = ref(false);
const savingBasicInfo = ref(false);
const basicInfoForm = reactive({
  name: '',
  type: 'code',
  difficulty: 'easy',
  introduction: ''
});

// 显示基础信息编辑模态框
const showEditBasicInfo = () => {
  // 填充当前数据
  basicInfoForm.name = practiceInfo.name;
  basicInfoForm.type = practiceInfo.type;
  basicInfoForm.difficulty = practiceInfo.difficulty;
  basicInfoForm.introduction = practiceInfo.introduction;
  editBasicInfoVisible.value = true;
};

// 保存基础信息
const handleSaveBasicInfo = async () => {
  if (!basicInfoForm.name.trim()) {
    message.warning('请输入实践课程名称');
    return;
  }
  if (!basicInfoForm.introduction.trim()) {
    message.warning('请输入实践课程介绍');
    return;
  }

  savingBasicInfo.value = true;
  try {
    const success = await updatePracticeBasicInfo(practiceId.value, {
      name: basicInfoForm.name,
      type: basicInfoForm.type,
      difficulty: basicInfoForm.difficulty,
      introduction: basicInfoForm.introduction
    } as BasicInfoRequest);

    if (success) {
      // 更新本地数据
      practiceInfo.name = basicInfoForm.name;
      practiceInfo.type = basicInfoForm.type;
      practiceInfo.difficulty = basicInfoForm.difficulty;
      practiceInfo.introduction = basicInfoForm.introduction;

      message.success('基础信息保存成功');
      editBasicInfoVisible.value = false;
    } else {
      message.error('保存失败，请稍后重试');
    }
  } catch (error) {
    console.error('保存基础信息失败:', error);
    message.error('保存失败，请稍后重试');
  } finally {
    savingBasicInfo.value = false;
  }
};

// 显示添加任务弹窗
const showAddTask = () => {
  editingStage.value = null;
  addTaskVisible.value = true;
};

// 编辑关卡
const editStage = (stage: PracticeStage) => {
  editingStage.value = stage;
  addTaskVisible.value = true;
};

// 测试关卡
const testStage = (stage: PracticeStage) => {
  // 打开新窗口进行测试（使用hash路由）
  const testUrl = `/#/practice/${practiceId.value}/stage/${stage.id}/test`;
  window.open(testUrl, '_blank');
};

// 删除关卡
const deleteStage = (stage: PracticeStage) => {
  // 检查是否只剩一个关卡
  if (stages.value.length <= 1) {
    message.warning('实践课程至少需要保留一个关卡');
    return;
  }
  
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除关卡“${stage.title}”吗？`,
    okText: '确定',
    cancelText: '取消',
    onOk: async () => {
      try {
        const success = await deletePracticeStage(stage.id, creatorId.value);
        if (success) {
          message.success('关卡删除成功');
          loadStages();
        } else {
          message.error('关卡删除失败');
        }
      } catch (error) {
        message.error('删除失败');
      }
    }
  });
};

// 处理关卡编辑成功
const handleStageSuccess = () => {
  addTaskVisible.value = false;
  editingStage.value = null;
  loadStages();
};

// 处理取消编辑
const handleCancelEdit = () => {
  addTaskVisible.value = false;
  editingStage.value = null;
};

// 加载关卡列表
const loadStages = async () => {
  loadingStages.value = true;
  try {
    const data = await getPracticeStages(practiceId.value, creatorId.value);
    stages.value = data;
  } catch (error) {
    message.error('加载关卡列表失败');
  } finally {
    loadingStages.value = false;
  }
};

// 获取难度颜色
const getDifficultyColor = (difficulty?: string) => {
  const colors: Record<string, string> = {
    'easy': 'green',
    'intermediate': 'orange',
    'advanced': 'red'
  };
  return colors[difficulty || 'easy'] || 'green';
};

// 获取难度文本
const getDifficultyText = (difficulty?: string) => {
  const texts: Record<string, string> = {
    'easy': '初级',
    'intermediate': '中级',
    'advanced': '高级'
  };
  return texts[difficulty || 'easy'] || '初级';
};

// 获取题型文本
const getTaskTypeText = (taskType: string) => {
  const texts: Record<string, string> = {
    'PRACTICE': '实践题',
    'CHOICE': '选择题',
    'JUDGEMENT': '判断题'
  };
  return texts[taskType] || taskType;
};

// 显示发布模态框
const showPublishModal = () => {
  // 检查是否有任务
  if (!hasAnyTasks()) {
    message.warning('请先添加至少一个实践任务后再发布');
    return;
  }
  
  publishModalVisible.value = true;
};

// 返回列表页
const goBackToList = () => {
  router.push('/course');
};

// 加载配置
const loadConfig = async () => {
  configLoading.value = true;
  try {
    const config = await getPracticeConfig(practiceId.value);
    if (config) {
      configForm.codeEditor = config.editor;
      configForm.commandLine = config.shell;
      configForm.repoVisibility = config.repoVisible ? 'visible' : 'hidden';
      configForm.allowSkip = config.allowSkip ? 'allow' : 'disallow';
    }
  } catch (error) {
    console.error('加载配置失败:', error);
    message.error('加载配置失败');
  } finally {
    configLoading.value = false;
  }
};

// 保存配置
const saveConfig = async () => {
  // 验证：代码编辑器和命令行不能都关闭
  if (!configForm.codeEditor && !configForm.commandLine) {
    message.error('代码编辑器和命令行不能同时关闭');
    return;
  }

  configLoading.value = true;
  try {
    const configData: PracticeConfig = {
      editor: configForm.codeEditor,
      shell: configForm.commandLine,
      repoVisible: configForm.repoVisibility === 'visible',
      allowSkip: configForm.allowSkip === 'allow'
    };
    
    const success = await updatePracticeConfig(practiceId.value, configData);
    if (success) {
      message.success('配置保存成功');
    } else {
      message.error('配置保存失败');
    }
  } catch (error) {
    console.error('保存配置失败:', error);
    message.error('保存配置失败');
  } finally {
    configLoading.value = false;
  }
};

// 发布实践
const publishPracticeHandler = async () => {
  // 检查是否有任务
  if (!hasAnyTasks()) {
    message.error('发布前需要至少添加一个任务关卡');
    return;
  }

  publishLoading.value = true;
  
  try {
    const publishData: PublishRequest = {
      visibility: publishForm.visibility as 'public' | 'private'
    };
    
    const success = await publishPractice(practiceId.value, publishData);
    
    if (success) {
      // 更新状态
      practiceInfo.status = publishForm.visibility === 'public' ? 'pending' : 'published';
      
      message.success(`实践课程发布成功！${publishForm.visibility === 'public' ? '等待后台审核' : '现在可以在课堂中使用该实践课程'}`);
      publishModalVisible.value = false;
      
      // 发布成功后导航到课程列表页
      setTimeout(() => {
        router.push('/course');
      }, 1500);
    } else {
      message.error('发布失败，请稍后重试');
    }
  } catch (error) {
    console.error('发布失败:', error);
    message.error('发布失败，请稍后重试');
  } finally {
    publishLoading.value = false;
  }
};

// 检查是否有任务
const hasAnyTasks = () => {
  return stages.value.length > 0;
};

// 显示添加到课堂模态框
const showAddToClassroomModal = async () => {
  addToClassroomVisible.value = true;
  addToClassroomLoading.value = true;
  try {
    const currentUserId = requireCurrentUserId();
    // 获取教师名下的课堂列表
    const response = await fetch(`/api/v1/classrooms?creator_id=${currentUserId}`);
    if (response.ok) {
      const data = await response.json();
      classroomList.value = data.items || data || [];
    }
  } catch (error) {
    console.error('获取课堂列表失败:', error);
    message.error('获取课堂列表失败');
  } finally {
    addToClassroomLoading.value = false;
  }
};

// 添加到课堂
const handleAddToClassroom = async () => {
  if (!selectedClassroomId.value) {
    message.warning('请选择一个课堂');
    return;
  }

  addToClassroomLoading.value = true;
  try {
    // 调用API将实践添加到课堂
    const response = await fetch(`/api/v1/classrooms/${selectedClassroomId.value}/practices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ practice_id: practiceId.value })
    });

    if (response.ok) {
      message.success('成功添加到课堂');
      addToClassroomVisible.value = false;
      selectedClassroomId.value = null;
    } else {
      message.error('添加失败，请稍后重试');
    }
  } catch (error) {
    console.error('添加到课堂失败:', error);
    message.error('添加到课堂失败');
  } finally {
    addToClassroomLoading.value = false;
  }
};

// 显示下架确认
const showUnpublishConfirm = () => {
  Modal.confirm({
    title: '确认下架',
    content: `确定要下架「${practiceInfo.name}」吗？下架后该实践将变为"编辑中"状态，仅自己可见，无法被学生访问。`,
    okText: '确认下架',
    okType: 'danger',
    cancelText: '取消',
    onOk: handleUnpublish
  });
};

// 处理下架
const handleUnpublish = async () => {
  try {
    const response = await fetch(`/api/v1/practices/${practiceId.value}/unpublish`, {
      method: 'POST'
    });

    if (response.ok) {
      practiceInfo.status = 'editing';
      message.success('实践课程已下架');
    } else {
      message.error('下架失败，请稍后重试');
    }
  } catch (error) {
    console.error('下架失败:', error);
    message.error('下架失败，请稍后重试');
  }
};

// 拖拽开始
const handleDragStart = (e: DragEvent, index: number) => {
  draggedIndex.value = index;
  isDragging.value = true;
  if (e.dataTransfer) {
    e.dataTransfer.effectAllowed = 'move';
  }
};

// 拖拽结束
const handleDragEnd = () => {
  draggedIndex.value = null;
  isDragging.value = false;
};

// 拖拽经过
const handleDragOver = (e: DragEvent) => {
  e.preventDefault();
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = 'move';
  }
};

// 拖拽放下
const handleDrop = async (e: DragEvent, dropIndex: number) => {
  e.preventDefault();
  
  if (draggedIndex.value === null || draggedIndex.value === dropIndex) {
    return;
  }
  
  // 重新排序stages数组
  const newStages = [...stages.value];
  const draggedStage = newStages.splice(draggedIndex.value, 1)[0];
  newStages.splice(dropIndex, 0, draggedStage);
  
  // 更新order_in_practice
  const stageOrders = newStages.map((stage, index) => ({
    stage_id: stage.id,
    order_in_practice: index + 1
  }));
  
  // 更新本地数据
  stages.value = newStages;
  
  // 调用API更新后端
  try {
    const success = await updateStageOrder(practiceId.value, stageOrders, creatorId.value);
    if (success) {
      message.success('关卡顺序已更新');
    } else {
      message.error('更新关卡顺序失败');
      // 恢复原顺序
      loadStages();
    }
  } catch (error) {
    message.error('更新关卡顺序失败');
    loadStages();
  }
  
  handleDragEnd();
};

// 页面初始化
onMounted(async () => {
  try {
    const currentUserId = requireCurrentUserId();
    // 加载实践详情
    const response = await get(`/api/v1/custom-practices/${practiceInfo.id}?creator_id=${currentUserId}`);

    if (response.code === '0000' && response.data) {
      // 更新实践信息，从后端获取实际状态
      // 后端返回 publish_status 字段：DRAFT, PUBLISHED, PENDING等
      const publishStatus = response.data.publish_status || response.data.status || 'DRAFT';
      Object.assign(practiceInfo, {
        name: response.data.title,
        introduction: response.data.intro || response.data.description,
        type: response.data.practice_type,
        difficulty: response.data.difficulty,
        status: publishStatus.toLowerCase(), // 转为小写: published, pending, draft
        visibility: response.data.visibility // PRIVATE or PUBLIC
      });

      console.log('实践信息已加载:', practiceInfo, '发布状态:', publishStatus);
    } else {
      message.error('加载实践信息失败');
      console.error('API响应:', response);
    }
  } catch (error) {
    message.error('加载实践信息失败');
    console.error('加载实践详情失败:', error);
  }

  // 加载关卡列表
  if (activeTab.value === 'task') {
    loadStages();
  }

  // 加载配置信息
  loadConfig();
});

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'task' && stages.value.length === 0) {
    loadStages();
  }
});
</script>

<style scoped>
.practice-edit-page {
  min-height: 100vh;
  background-color: #f0f2f5;
}

.page-header {
  background-color: #fff;
}

.page-content {
  padding: 24px;
}

.task-header {
  margin-bottom: 24px;
}

.intro-header {
  margin-bottom: 16px;
}

.intro-header h3 {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
}

.intro-header p {
  color: rgba(0, 0, 0, 0.65);
}

.task-list {
  margin-top: 16px;
  padding: 0 24px 24px;
}

.stages-container {
  padding: 16px 0;
}

.stage-card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.stage-card-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stage-type,
.stage-skills,
.stage-coin {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-skills .ant-tag {
  margin: 0;
}

.coin-value {
  font-weight: 600;
  color: #faad14;
}

/* 配置相关样式 */
.config-container {
  padding: 0 16px;
}

.config-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 16px;
}

.form-item-hint {
  margin-left: 8px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 14px;
}

/* 发布模态框样式 */
.publish-modal-content {
  padding: 0 16px;
}

.publish-description {
  margin-bottom: 16px;
  font-size: 14px;
  color: rgba(0, 0, 0, 0.65);
}

.publish-options {
  width: 100%;
  margin-bottom: 24px;
}

.publish-option {
  margin-left: 8px;
  padding: 8px 0;
}

.publish-option-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.publish-option-desc {
  font-size: 13px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}

.publish-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

/* 拖拽相关样式 */
.ant-list-item {
  transition: all 0.2s;
}

.ant-list-item.dragging {
  opacity: 0.5;
}

.ant-list-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
</style> 
