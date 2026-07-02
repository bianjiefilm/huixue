<template>
  <div class="repo-tab-container">
    <!-- 代码仓库未开启时的提示 -->
    <div v-if="!repoInfo" class="repo-init-container">
      <a-empty description="代码仓库未开启">
        <template #image>
          <FolderOpenOutlined style="font-size: 64px; color: #d9d9d9" />
        </template>
        <a-button type="primary" @click="initRepository">
          <template #icon><FolderAddOutlined /></template>
          开启代码仓库
        </a-button>
      </a-empty>
      <a-alert
        message="提示"
        description="代码仓库创建后不可关闭，创建代码仓库会增加课程加载时间，如课程中只设置了选择题、判断题则不需要开启代码仓库"
        type="info"
        show-icon
        style="margin-top: 24px; max-width: 600px; margin-left: auto; margin-right: auto"
      />
    </div>

    <!-- 代码仓库已开启 -->
    <div v-else class="repo-content">
      <div class="repo-layout">
        <!-- 左侧文件树 -->
        <div class="repo-sidebar">
          <div class="sidebar-header">
            <h4>文件目录</h4>
            <a-space>
              <a-tooltip title="新建文件">
                <a-button size="small" type="text" @click="showCreateFile">
                  <template #icon><FileAddOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="新建文件夹">
                <a-button size="small" type="text" @click="showCreateFolder">
                  <template #icon><FolderAddOutlined /></template>
                </a-button>
              </a-tooltip>
              <a-tooltip title="上传文件">
                <a-button size="small" type="text" @click="showUploadModal = true">
                  <template #icon><UploadOutlined /></template>
                </a-button>
              </a-tooltip>
            </a-space>
          </div>
          
          <div class="file-tree">
            <a-tree
              v-if="fileTree.length > 0"
              :tree-data="fileTree"
              :default-expand-all="true"
              @select="onFileSelect"
            >
              <template #icon="{ dataRef }">
                <FolderOutlined v-if="dataRef.type === 'directory'" />
                <FileOutlined v-else />
              </template>
            </a-tree>
            <a-empty v-else description="暂无文件" />
          </div>
        </div>

        <!-- 右侧编辑器 -->
        <div class="repo-main">
          <div v-if="openedFiles.length > 0" class="editor-container">
            <!-- 文件标签页 -->
            <div class="editor-tabs">
              <a-tabs
                v-model:activeKey="activeFileKey"
                type="editable-card"
                hide-add
                @edit="onTabEdit"
              >
                <a-tab-pane
                  v-for="file in openedFiles"
                  :key="file.path"
                  :closable="true"
                >
                  <template #tab>
                    <span>
                      <span v-if="file.isModified" class="file-modified-dot">●</span>
                      {{ file.name }}
                    </span>
                  </template>
                </a-tab-pane>
              </a-tabs>
              
              <div class="editor-actions">
                <a-button size="small" type="primary" @click="saveCurrentFile" :disabled="!currentFile?.isModified">
                  保存当前页
                </a-button>
                <a-button size="small" @click="saveAllFiles" :disabled="!hasModifiedFiles">
                  保存全部
                </a-button>
                <a-button size="small" @click="commitChanges" :disabled="!hasModifiedFiles">
                  提交修改
                </a-button>
              </div>
            </div>

            <!-- 代码编辑器 -->
            <div class="code-editor">
              <a-textarea
                v-if="currentFile"
                v-model:value="currentFile.content"
                :placeholder="'编辑 ' + currentFile.name"
                :auto-size="{ minRows: 20, maxRows: 40 }"
                style="font-family: 'Consolas', 'Monaco', monospace"
                @change="onContentChange"
              />
            </div>
          </div>
          
          <a-empty v-else description="请选择文件进行编辑" />
        </div>
      </div>
    </div>

    <!-- 新建文件/文件夹模态框 -->
    <a-modal
      v-model:open="createModal.visible"
      :title="createModal.isDirectory ? '新建文件夹' : '新建文件'"
      @ok="handleCreate"
      @cancel="createModal.visible = false"
    >
      <a-form :model="createModal" layout="vertical">
        <a-form-item label="路径" required>
          <a-input
            v-model:value="createModal.path"
            :placeholder="createModal.isDirectory ? '例如：src/components' : '例如：src/main.py'"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 上传文件模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传文件"
      :footer="null"
      width="600px"
    >
      <a-upload-dragger
        :multiple="true"
        :before-upload="beforeUpload"
        :custom-request="handleUpload"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">支持单个或批量上传</p>
      </a-upload-dragger>
    </a-modal>

    <!-- 提交修改模态框 -->
    <a-modal
      v-model:open="commitModal.visible"
      title="提交代码修改"
      @ok="handleCommit"
      @cancel="commitModal.visible = false"
    >
      <a-form :model="commitModal" layout="vertical">
        <a-form-item label="提交类型" required>
          <a-radio-group v-model:value="commitModal.type">
            <a-radio value="all">提交全部修改</a-radio>
            <a-radio value="current">仅提交当前文件</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="提交信息" required>
          <a-textarea
            v-model:value="commitModal.message"
            placeholder="请输入提交信息"
            :rows="4"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { message } from 'ant-design-vue';
import {
  FolderOpenOutlined,
  FolderAddOutlined,
  FileAddOutlined,
  FolderOutlined,
  FileOutlined,
  UploadOutlined,
  InboxOutlined
} from '@ant-design/icons-vue';
import {
  initPracticeRepository,
  getRepositoryStatus,
  getRepositoryFiles,
  createRepoFile,
  getFileContent,
  saveFileContent,
  commitChanges,
  type RepoInfo,
  type RepoFile
} from '@/api/practice';
import { useUserStore } from '@/stores/user';

const props = defineProps<{
  practiceId: number;
}>();

const userStore = useUserStore();
const creatorId = computed(() => userStore.userInfo.id);

// 代码仓库信息
const repoInfo = ref<RepoInfo | null>(null);
const fileTree = ref<any[]>([]);
const openedFiles = ref<Array<{
  path: string;
  name: string;
  content: string;
  originalContent: string;
  isModified: boolean;
}>>([]);
const activeFileKey = ref<string>('');

// 当前文件
const currentFile = computed(() => {
  return openedFiles.value.find(f => f.path === activeFileKey.value);
});

// 是否有修改的文件
const hasModifiedFiles = computed(() => {
  return openedFiles.value.some(f => f.isModified);
});

// 创建文件/文件夹模态框
const createModal = reactive({
  visible: false,
  isDirectory: false,
  path: ''
});

// 上传模态框
const showUploadModal = ref(false);

// 提交模态框
const commitModal = reactive({
  visible: false,
  type: 'all',
  message: '保存修改'
});

// 初始化代码仓库
const initRepository = async () => {
  try {
    const result = await initPracticeRepository(props.practiceId, creatorId.value);
    if (result) {
      repoInfo.value = result;
      message.success('代码仓库开启成功');
      loadFileTree();
    } else {
      message.error('代码仓库开启失败');
    }
  } catch (error) {
    message.error('代码仓库开启失败');
  }
};

// 加载文件树
const loadFileTree = async () => {
  try {
    const files = await getRepositoryFiles(props.practiceId, '', creatorId.value);
    fileTree.value = convertToTreeData(files);
  } catch (error) {
    message.error('加载文件列表失败');
  }
};

// 转换文件列表为树形数据
const convertToTreeData = (files: RepoFile[]) => {
  const map: any = {};
  const roots: any[] = [];
  
  // 创建所有节点
  files.forEach(file => {
    const node = {
      key: file.path,
      title: file.name,
      type: file.type,
      children: []
    };
    map[file.path] = node;
  });
  
  // 构建树形结构
  files.forEach(file => {
    const parentPath = file.path.substring(0, file.path.lastIndexOf('/'));
    if (parentPath && map[parentPath]) {
      map[parentPath].children.push(map[file.path]);
    } else {
      roots.push(map[file.path]);
    }
  });
  
  return roots;
};

// 选择文件
const onFileSelect = async (selectedKeys: string[], info: any) => {
  if (selectedKeys.length === 0) return;
  
  const path = selectedKeys[0];
  const node = info.node;
  
  // 如果是目录，不处理
  if (node.type === 'directory') return;
  
  // 检查文件是否已打开
  const existingFile = openedFiles.value.find(f => f.path === path);
  if (existingFile) {
    activeFileKey.value = path;
    return;
  }
  
  // 加载文件内容
  try {
    const content = await getFileContent(props.practiceId, path, creatorId.value);
    if (content !== null) {
      openedFiles.value.push({
        path,
        name: node.title,
        content,
        originalContent: content,
        isModified: false
      });
      activeFileKey.value = path;
    }
  } catch (error) {
    message.error('加载文件内容失败');
  }
};

// 内容改变
const onContentChange = () => {
  if (currentFile.value) {
    currentFile.value.isModified = currentFile.value.content !== currentFile.value.originalContent;
  }
};

// 标签页编辑
const onTabEdit = (targetKey: string, action: string) => {
  if (action === 'remove') {
    const index = openedFiles.value.findIndex(f => f.path === targetKey);
    if (index !== -1) {
      openedFiles.value.splice(index, 1);
      if (openedFiles.value.length > 0) {
        activeFileKey.value = openedFiles.value[0].path;
      }
    }
  }
};

// 显示创建文件对话框
const showCreateFile = () => {
  createModal.isDirectory = false;
  createModal.path = '';
  createModal.visible = true;
};

// 显示创建文件夹对话框
const showCreateFolder = () => {
  createModal.isDirectory = true;
  createModal.path = '';
  createModal.visible = true;
};

// 处理创建
const handleCreate = async () => {
  if (!createModal.path) {
    message.warning('请输入路径');
    return;
  }
  
  try {
    const success = await createRepoFile(
      props.practiceId,
      createModal.path,
      createModal.isDirectory,
      '',
      creatorId.value
    );
    
    if (success) {
      message.success(createModal.isDirectory ? '文件夹创建成功' : '文件创建成功');
      createModal.visible = false;
      loadFileTree();
    } else {
      message.error('创建失败');
    }
  } catch (error) {
    message.error('创建失败');
  }
};

// 上传前检查
const beforeUpload = (file: any) => {
  return false; // 手动上传
};

// 处理上传
const handleUpload = async (options: any) => {
  const { file, onSuccess, onError } = options;
  
  try {
    // 读取文件内容
    const reader = new FileReader();
    reader.onload = async (e) => {
      const content = e.target?.result as string;
      const filePath = file.name;
      
      const success = await createRepoFile(
        props.practiceId,
        filePath,
        false,
        content,
        creatorId.value
      );
      
      if (success) {
        onSuccess();
        message.success(`${file.name} 上传成功`);
        loadFileTree();
      } else {
        onError();
        message.error(`${file.name} 上传失败`);
      }
    };
    reader.readAsText(file);
  } catch (error) {
    onError();
    message.error('上传失败');
  }
};

// 保存当前文件
const saveCurrentFile = async () => {
  if (!currentFile.value || !currentFile.value.isModified) return;
  
  try {
    const success = await saveFileContent(
      props.practiceId,
      currentFile.value.path,
      currentFile.value.content,
      creatorId.value
    );
    
    if (success) {
      currentFile.value.originalContent = currentFile.value.content;
      currentFile.value.isModified = false;
      message.success('文件保存成功');
    } else {
      message.error('文件保存失败');
    }
  } catch (error) {
    message.error('文件保存失败');
  }
};

// 保存所有文件
const saveAllFiles = async () => {
  const modifiedFiles = openedFiles.value.filter(f => f.isModified);
  
  for (const file of modifiedFiles) {
    try {
      const success = await saveFileContent(
        props.practiceId,
        file.path,
        file.content,
        creatorId.value
      );
      
      if (success) {
        file.originalContent = file.content;
        file.isModified = false;
      }
    } catch (error) {
      message.error(`文件 ${file.name} 保存失败`);
    }
  }
  
  message.success('所有文件保存成功');
};

// 提交修改
const commitChanges = () => {
  commitModal.visible = true;
};

// 处理提交
const handleCommit = async () => {
  try {
    const filePaths = commitModal.type === 'current' && currentFile.value
      ? [currentFile.value.path]
      : [];
    
    const success = await commitChanges(
      props.practiceId,
      commitModal.type as 'all' | 'current',
      filePaths,
      commitModal.message,
      creatorId.value
    );
    
    if (success) {
      message.success('代码提交成功');
      commitModal.visible = false;
      
      // 更新文件状态
      if (commitModal.type === 'all') {
        openedFiles.value.forEach(f => {
          f.originalContent = f.content;
          f.isModified = false;
        });
      } else if (currentFile.value) {
        currentFile.value.originalContent = currentFile.value.content;
        currentFile.value.isModified = false;
      }
    } else {
      message.error('代码提交失败');
    }
  } catch (error) {
    message.error('代码提交失败');
  }
};

// 检查仓库状态并加载文件
const checkRepoStatus = async () => {
  try {
    const status = await getRepositoryStatus(props.practiceId, creatorId.value);
    if (status && status.is_enabled) {
      repoInfo.value = status;
      loadFileTree();
    }
  } catch (error) {
    console.error('检查仓库状态失败:', error);
  }
};

// 初始化
onMounted(() => {
  // 检查代码仓库是否已开启
  checkRepoStatus();
});
</script>

<style scoped>
.repo-tab-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.repo-init-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 40px;
}

.repo-content {
  flex: 1;
  overflow: hidden;
}

.repo-layout {
  display: flex;
  height: 100%;
  gap: 16px;
}

.repo-sidebar {
  width: 300px;
  background: #fafafa;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 12px 16px;
  border-bottom: 1px solid #d9d9d9;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sidebar-header h4 {
  margin: 0;
}

.file-tree {
  flex: 1;
  overflow: auto;
  padding: 8px;
}

.repo-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.editor-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

.editor-tabs {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #d9d9d9;
}

.editor-tabs :deep(.ant-tabs) {
  flex: 1;
  margin-bottom: 0;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.file-modified-dot {
  color: #faad14;
  margin-right: 4px;
}

.code-editor {
  flex: 1;
  padding: 16px;
  overflow: auto;
}

.code-editor :deep(.ant-input-textarea-show-count::after) {
  display: none;
}
</style>