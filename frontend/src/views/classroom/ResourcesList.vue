<template>
	<div class="teaching-resources">
		<PageHeaderBar
			title="教学资源"
			subtitle="教师可上传 PDF、DOC、DOCX、PPT、PPTX、MP4 格式的教学资源供学生学习"
		>
			<template #actions>
				<a-button type="primary" @click="openAddModuleDialog">
					<template #icon><PlusOutlined /></template>
					添加模块
				</a-button>
			</template>
		</PageHeaderBar>

		<!-- 模块列表 -->
		<EmptyStateBlock
			v-if="modulesList.length === 0"
			description="暂无教学资源模块，请先创建模块来组织您的教学资源"
		>
			<template #action>
				<a-button type="primary" @click="openAddModuleDialog">创建第一个模块</a-button>
			</template>
		</EmptyStateBlock>

		<div v-else class="modules-container">
			<!-- 模块卡片 -->
			<div
				v-for="module in modulesList"
				:key="module.id"
				class="module-card"
			>
				<div class="module-header">
					<div class="module-info">
						<h3>{{ module.name }}</h3>
						<span class="file-count">{{ module.file_count }} 个文件</span>
					</div>
					<div class="module-actions">
						<a-button
							size="small"
							@click="openUploadDialog(module)"
						>
							<template #icon><UploadOutlined /></template>
							上传
						</a-button>
						<a-dropdown :trigger="['click']">
							<a-button size="small">
								<template #icon><MoreOutlined /></template>
							</a-button>
							<template #overlay>
								<a-menu>
									<a-menu-item @click="openRenameModuleDialog(module)">
										<template #icon><EditOutlined /></template>
										重命名
									</a-menu-item>
									<a-menu-item danger @click="handleDeleteModule(module)">
										<template #icon><DeleteOutlined /></template>
										删除模块
									</a-menu-item>
								</a-menu>
							</template>
						</a-dropdown>
					</div>
				</div>

				<!-- 模块内的文件列表 -->
				<div v-if="module.files && module.files.length > 0" class="files-list">
					<div
						v-for="file in module.files"
						:key="file.id"
						class="file-item"
					>
						<div class="file-info">
							<component :is="getFileTypeIcon(file.file_type)" class="file-icon" />
							<div class="file-details">
								<div class="file-name">{{ file.name }}</div>
								<div class="file-meta">
									{{ formatFileSize(file.file_size) }} · {{ file.uploader_name }} · {{ formatTime(file.created_at) }}
								</div>
							</div>
						</div>
						<div class="file-actions">
							<a-button
								type="link"
								size="small"
								@click="previewFile(file)"
							>
								预览
							</a-button>
							<a-button
								type="link"
								size="small"
								danger
								@click="handleDeleteFile(file)"
							>
								删除
							</a-button>
						</div>
					</div>
				</div>

				<div v-else class="empty-module">
					<p>该模块暂无文件，点击"上传"按钮添加教学资源</p>
				</div>
			</div>
		</div>

		<!-- 添加模块对话框 -->
		<a-modal
			v-model:open="addModuleModalVisible"
			title="添加模块"
			@ok="handleAddModule"
			:confirmLoading="moduleLoading"
		>
			<a-form :model="moduleForm" layout="vertical">
				<a-form-item
					label="模块名称"
					name="name"
					:rules="[{ required: true, message: '请输入模块名称' }]"
				>
					<a-input
						v-model:value="moduleForm.name"
						placeholder="请输入模块名称"
					/>
				</a-form-item>
				<a-form-item
					label="模块描述"
					name="description"
				>
					<a-textarea
						v-model:value="moduleForm.description"
						placeholder="请输入模块描述（可选）"
						:rows="3"
					/>
				</a-form-item>
			</a-form>
		</a-modal>

		<!-- 重命名模块对话框 -->
		<a-modal
			v-model:open="renameModuleModalVisible"
			title="重命名模块"
			@ok="handleRenameModule"
			:confirmLoading="moduleLoading"
		>
			<a-form :model="renameForm" layout="vertical">
				<a-form-item
					label="模块名称"
					name="name"
					:rules="[{ required: true, message: '请输入模块名称' }]"
				>
					<a-input
						v-model:value="renameForm.name"
						placeholder="请输入新的模块名称"
					/>
				</a-form-item>
			</a-form>
		</a-modal>

		<!-- 上传文件对话框 -->
		<a-modal
			v-model:open="uploadModalVisible"
			title="上传教学资源"
			width="600px"
			:confirmLoading="uploadLoading"
			@cancel="handleUploadCancel"
		>
			<div class="upload-modal-content">
				<div class="upload-info">
					<p><strong>当前模块：</strong>{{ currentModule?.name }}</p>
					<p><strong>支持格式：</strong>PDF、DOC、DOCX、PPT、PPTX、MP4</p>
					<p><strong>文件大小限制：</strong>单个文件不超过2GB</p>
				</div>

				<a-upload-dragger
					v-model:fileList="fileList"
					:multiple="true"
					:accept="'.pdf,.doc,.docx,.ppt,.pptx,.mp4'"
					:beforeUpload="beforeUpload"
					:remove="handleRemoveFile"
					:disabled="uploadLoading"
				>
					<p class="ant-upload-drag-icon">
						<InboxOutlined />
					</p>
					<p class="ant-upload-text">点击或拖拽文件到此处上传</p>
					<p class="ant-upload-hint">
						支持PDF、DOC、DOCX、PPT、PPTX、MP4格式文件
					</p>
				</a-upload-dragger>
			</div>
			<template #footer>
				<a-button @click="handleUploadCancel">取消</a-button>
				<a-button
					type="primary"
					@click="handleUploadFiles"
					:loading="uploadLoading"
					:disabled="fileList.length === 0"
				>
					开始上传
				</a-button>
			</template>
		</a-modal>

		<!-- 文件预览对话框 -->
		<a-modal
			v-model:open="previewModalVisible"
			:title="`预览 - ${currentFile?.name}`"
			width="90%"
			:footer="null"
			:destroyOnClose="true"
		>
			<div class="file-preview">
				<template v-if="isPdfFile(currentFile?.file_type)">
					<iframe
						:src="getPreviewUrl(currentFile?.url || '')"
						class="pdf-viewer"
						width="100%"
						height="600px"
					></iframe>
				</template>
				<template v-else-if="isVideoFile(currentFile?.file_type)">
					<video
						:src="getPreviewUrl(currentFile?.url || '')"
						controls
						class="video-player"
						style="width: 100%; max-height: 600px;"
					></video>
				</template>
				<template v-else-if="isPPTFile(currentFile)">
					<div style="background-color: white; width: 100%; height: 600px; position: relative" v-loading="pptxLoading" element-loading-text="正在加载课件...">
						<vue-office-pptx
							v-if="pptxBuffer"
							:src="pptxBuffer"
							style="width: 100%; height: 600px;"
							@rendered="onPptxRendered"
							@error="onPptxError"
						/>
					</div>
				</template>
				<template v-else-if="isOfficeFile(currentFile?.file_type)">
					<div class="office-preview">
						<div class="preview-header">
							<p>此文件类型暂不支持在线预览，请下载后查看</p>
							<a-button type="primary" :href="currentFile?.url || ''" target="_blank">
								<template #icon><DownloadOutlined /></template>
								下载文件
							</a-button>
						</div>
					</div>
				</template>
				<template v-else>
					<div class="unsupported-preview">
						<p>不支持预览此类型的文件</p>
					</div>
				</template>
			</div>
		</a-modal>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { message, Modal } from 'ant-design-vue';
import VueOfficePptx from '@vue-office/pptx';
import {
	PlusOutlined,
	UploadOutlined,
	MoreOutlined,
	EditOutlined,
	DeleteOutlined,
	DownloadOutlined,
	FolderOpenOutlined,
	InboxOutlined,
	FileTextOutlined,
	FilePdfOutlined,
	PlayCircleOutlined,
	FileWordOutlined,
	FilePptOutlined
} from '@ant-design/icons-vue';
import {
	getResourceModules,
	createResourceModule,
	updateResourceModule,
	deleteResourceModule,
	uploadResourceFile,
	deleteResourceFile
} from '../../api/resources';
import type { ResourceModule, ResourceFile } from '../../api/resources';
import { useUserStore } from '../../stores/user';
import PageHeaderBar from '@/components/common/PageHeaderBar.vue';
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue';

interface Props {
	classroomId: string;
}
const props = defineProps<Props>();

const userStore = useUserStore();
const currentUserId = computed(() => userStore.userInfo.id);
const currentUserRole = computed(() => userStore.userInfo.role);

// 模块列表相关
const modulesList = ref<ResourceModule[]>([]);
const loading = ref(false);
const moduleLoading = ref(false);

// 添加模块相关
const addModuleModalVisible = ref(false);
const moduleForm = ref({
	name: '',
	description: ''
});

// 重命名模块相关
const renameModuleModalVisible = ref(false);
const currentModule = ref<ResourceModule | null>(null);
const renameForm = ref({
	name: ''
});

// 上传文件相关
const uploadModalVisible = ref(false);
const uploadLoading = ref(false);
const fileList = ref<any[]>([]);

// 文件预览相关
const previewModalVisible = ref(false);
const currentFile = ref<ResourceFile | null>(null);

// 文件类型图标映射
const getFileTypeIcon = (fileType: string) => {
	const iconMap: Record<string, any> = {
		pdf: FilePdfOutlined,
		doc: FileWordOutlined,
		docx: FileWordOutlined,
		ppt: FilePptOutlined,
		pptx: FilePptOutlined,
		mp4: PlayCircleOutlined
	};
	return iconMap[fileType] || FileTextOutlined;
};

// 工具函数
const formatFileSize = (bytes: number): string => {
	if (bytes === 0) return '0 B';
	const k = 1024;
	const sizes = ['B', 'KB', 'MB', 'GB'];
	const i = Math.floor(Math.log(bytes) / Math.log(k));
	return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatTime = (dateString: string): string => {
	return new Date(dateString).toLocaleString('zh-CN');
};

const isPdfFile = (fileType?: string): boolean => {
	const ft = fileType?.toLowerCase() || '';
	return ft === 'pdf' || ft.includes('pdf');
};

const isVideoFile = (fileType?: string): boolean => {
	const ft = fileType?.toLowerCase() || '';
	return ft.includes('mp4') || ft.includes('video');
};

const isOfficeFile = (fileType?: string): boolean => {
	const ft = fileType?.toLowerCase() || '';
	return ft === 'doc' || ft === 'docx' || ft === 'ppt' || ft === 'pptx'
		|| ft.includes('msword') || ft.includes('wordprocessing')
		|| ft.includes('powerpoint') || ft.includes('presentation');
};

const getPreviewUrl = (url?: string): string => {
    if (!url) return '';
    if (url.startsWith('/static/')) {
        const backendBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
        const baseOrigin = backendBaseUrl.replace(/\/api\/v1\/?$/, '');
        return `${baseOrigin}${url}`;
    }
    return url;
};

// 加载模块列表
const loadModules = async () => {
	console.log('--- loadModules CALLED! ---');
	loading.value = true;
	try {
		const params: any = {
			classroom_id: parseInt(props.classroomId)
		};
		// 根据角色传递不同的ID，以支持后端的多角色权限校验
		if (currentUserRole.value === 'student') {
			params.student_id = currentUserId.value;
		} else {
			params.teacher_id = currentUserId.value;
		}

		console.log('--- Calling getResourceModules with params:', params);
		const response = await getResourceModules(params);
		console.log('--- getResourceModules RETURNED:', response);

		if (response.code === '0000') {
			modulesList.value = response.data.modules || [];
		} else {
			message.error(response.message || '加载模块列表失败');
		}
	} catch (error) {
		console.error('加载模块列表失败:', error);
		message.error('加载模块列表失败');
	} finally {
		loading.value = false;
	}
};

// 添加模块相关函数
const openAddModuleDialog = () => {
	addModuleModalVisible.value = true;
	moduleForm.value = {
		name: '',
		description: ''
	};
};

const handleAddModule = async () => {
	if (!moduleForm.value.name.trim()) {
		message.error('请输入模块名称');
		return;
	}

	moduleLoading.value = true;
	try {
		const response = await createResourceModule({
			classroom_id: Number(props.classroomId),
			teacher_id: Number(currentUserId.value),
			data: {
				name: moduleForm.value.name,
				description: moduleForm.value.description
			}
		});

		if (response.code === '0000') {
			message.success('模块创建成功');
			addModuleModalVisible.value = false;
			loadModules(); // 重新加载模块列表
		} else {
			message.error(response.message || '创建模块失败');
		}
	} catch (error) {
		console.error('创建模块失败:', error);
		message.error('创建模块失败');
	} finally {
		moduleLoading.value = false;
	}
};

// 重命名模块相关函数
const openRenameModuleDialog = (module: ResourceModule) => {
	currentModule.value = module;
	renameForm.value = {
		name: module.name
	};
	renameModuleModalVisible.value = true;
};

const handleRenameModule = async () => {
	if (!renameForm.value.name.trim()) {
		message.error('请输入模块名称');
		return;
	}

	if (!currentModule.value) return;

	moduleLoading.value = true;
	try {
		const response = await updateResourceModule({
			module_id: Number(currentModule.value.id),
			teacher_id: Number(currentUserId.value),
			data: {
				name: renameForm.value.name
			}
		});

		if (response.code === '0000') {
			message.success('模块重命名成功');
			renameModuleModalVisible.value = false;
			loadModules(); // 重新加载模块列表
		} else {
			message.error(response.message || '重命名模块失败');
		}
	} catch (error) {
		console.error('重命名模块失败:', error);
		message.error('重命名模块失败');
	} finally {
		moduleLoading.value = false;
	}
};

// 删除模块
const handleDeleteModule = async (module: ResourceModule) => {
	Modal.confirm({
		title: '确认删除',
		content: `确定要删除模块"${module.name}"吗？删除后该模块下的所有文件也将被删除。`,
		okText: '确认删除',
		cancelText: '取消',
		okType: 'danger',
		onOk: async () => {
			try {
				const response = await deleteResourceModule({
					module_id: Number(module.id),
					teacher_id: Number(currentUserId.value)
				});

				if (response.code === '0000') {
					message.success('模块删除成功');
					loadModules(); // 重新加载模块列表
				} else {
					message.error(response.message || '删除模块失败');
				}
			} catch (error) {
				console.error('删除模块失败:', error);
				message.error('删除模块失败');
			}
		}
	});
};

// 上传文件相关函数
const openUploadDialog = (module: ResourceModule) => {
	currentModule.value = module;
	uploadModalVisible.value = true;
	fileList.value = [];
};

const beforeUpload = (file: File) => {
	// 检查文件类型
	const allowedTypes = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.mp4'];
	const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

	if (!allowedTypes.includes(fileExtension)) {
		message.error(`不支持的文件类型。支持的格式：${allowedTypes.join('、')}`);
		return false;
	}

	// 检查文件大小 (2GB = 2 * 1024 * 1024 * 1024 bytes)
	const maxSize = 2 * 1024 * 1024 * 1024;
	if (file.size > maxSize) {
		message.error('文件大小不能超过2GB');
		return false;
	}

	return false; // 阻止自动上传
};

const handleRemoveFile = (file: any) => {
	const index = fileList.value.indexOf(file);
	if (index > -1) {
		fileList.value.splice(index, 1);
	}
};

const handleUploadCancel = () => {
	uploadModalVisible.value = false;
	fileList.value = [];
};

const handleUploadFiles = async () => {
	if (fileList.value.length === 0) {
		message.error('请先选择要上传的文件');
		return;
	}

	if (!currentModule.value) {
		message.error('未选择目标模块');
		return;
	}

	uploadLoading.value = true;
	let successCount = 0;
	let failCount = 0;

	try {
		for (const fileItem of fileList.value) {
			const file = fileItem.originFileObj || fileItem;
			const fileExtension = file.name.split('.').pop()?.toLowerCase() || '';

			try {
				// 使用FormData上传真实文件
				const formData = new FormData();
				formData.append('file', file);
				formData.append('module_id', String(currentModule.value.id));
				formData.append('teacher_id', String(currentUserId.value));
				formData.append('file_name', file.name);
				formData.append('file_type', fileExtension.toUpperCase());
				const uploadResponse = await request.post('/api/v1/files/upload/teaching-resource', formData);

				if (uploadResponse.code === '0000') {
					successCount++;
				} else {
					failCount++;
					console.error(`文件 ${file.name} 上传失败:`, uploadResponse.message);
				}
			} catch (err) {
				failCount++;
				console.error(`文件 ${file.name} 上传失败:`, err);
			}
		}

		if (successCount > 0) {
			message.success(`成功上传 ${successCount} 个文件`);
		}
		if (failCount > 0) {
			message.warning(`${failCount} 个文件上传失败`);
		}

		uploadModalVisible.value = false;
		fileList.value = [];
		loadModules(); // 重新加载模块列表
	} catch (error) {
		console.error('上传文件失败:', error);
		message.error('上传文件失败');
	} finally {
		uploadLoading.value = false;
	}
};

import axios from 'axios';
import request from '@/utils/request';

// 文件预览
const pptxBuffer = ref<ArrayBuffer | null>(null);
const pptxLoading = ref<boolean>(false);

const previewFile = async (file: ResourceFile) => {
	currentFile.value = file;
	pptxBuffer.value = null;
	previewModalVisible.value = true;
	
	if (isPPTFile(file)) {
		pptxLoading.value = true;
		try {
			const res = await axios.get(getPreviewUrl(file.url || ''), { responseType: 'arraybuffer' });
			// 延迟绑定，确保 a-modal 动画渲染完全完成且 DOM 尺寸绝对稳定
			setTimeout(() => {
				pptxBuffer.value = res.data;
				pptxLoading.value = false;
			}, 800);
		} catch (error) {
			console.error('获取PPT课件失败:', error);
			message.error('无法加载课件');
			pptxLoading.value = false;
		}
	}
};

const onPptxRendered = () => {
	console.log('PPTX 渲染成功');
};

const onPptxError = (e: any) => {
	console.error('PPTX 渲染失败', e);
};

// 判断是否为PPT文件
const isPPTFile = (file: ResourceFile | undefined | null) => {
	if (!file) return false;
	const type = file.file_type?.toLowerCase() || '';
	// Cover legacy and modern PPTX mimetypes
	if (type.includes('ppt') || type.includes('powerpoint') || type.includes('presentation') || ['ppt', 'pptx'].includes(type)) return true;
	
	// fallback to filename extension (most reliable)
	if (file.name) {
		const ext = file.name.split('.').pop()?.toLowerCase();
		if (ext && ['ppt', 'pptx'].includes(ext)) return true;
	}
	
	// fallback to url extension, strip query params if any
	if (file.url) {
		const cleanUrl = file.url.split('?')[0];
		const ext = cleanUrl.split('.').pop()?.toLowerCase();
		return ['ppt', 'pptx'].includes(ext || '');
	}
	return false;
};

// 删除文件
const handleDeleteFile = async (file: ResourceFile) => {
	Modal.confirm({
		title: '确认删除',
		content: `确定要删除文件"${file.name}"吗？`,
		okText: '确认删除',
		cancelText: '取消',
		okType: 'danger',
		onOk: async () => {
			try {
				const response = await deleteResourceFile({
					file_id: Number(file.id),
					teacher_id: Number(currentUserId.value)
				});

				if (response.code === '0000') {
					message.success('文件删除成功');
					loadModules(); // 重新加载模块列表
				} else {
					message.error(response.message || '删除文件失败');
				}
			} catch (error) {
				console.error('删除文件失败:', error);
				message.error('删除文件失败');
			}
		}
	});
};

// 生命周期钩子
onMounted(() => {
	console.log('--- ResourcesList MOUNTED! ---');
	loadModules();
});

watch(() => props.classroomId, (newId, oldId) => {
	if (newId && newId !== oldId) {
		console.log('--- ResourcesList classroomId changed from', oldId, 'to', newId);
		loadModules();
	}
});
</script>

<style scoped>
.teaching-resources {
  /* nested in classroom detail PageShell — no extra outer padding */
}

.modules-container {
  display: flex;
  flex-direction: column;
  gap: var(--hx-space-5);
}

.module-card {
  background: var(--hx-color-bg-container, #fff);
  border: 1px solid var(--hx-color-border, #d9d9d9);
  border-radius: var(--hx-radius-md, 10px);
  overflow: hidden;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--hx-space-4) var(--hx-space-5);
  background: var(--hx-color-bg-elevated, #fafafa);
  border-bottom: 1px solid var(--hx-color-border, #f0f0f0);
}

.module-info h3 {
  margin: 0 0 var(--hx-space-1) 0;
  color: var(--hx-color-text-primary, #262626);
  font-size: var(--hx-font-size-md, 16px);
  font-weight: 600;
}

.file-count {
  color: var(--hx-color-text-secondary, #666);
  font-size: 12px;
}

.module-actions {
  display: flex;
  gap: var(--hx-space-2);
}

.files-list {
  padding: 0;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--hx-space-3) var(--hx-space-5);
  border-bottom: 1px solid var(--hx-color-border, #f0f0f0);
  transition: background-color 0.2s;
}

.file-item:hover {
  background: var(--hx-color-bg-elevated, #f5f5f5);
}

.file-item:last-child {
  border-bottom: none;
}

.file-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.file-icon {
  margin-right: var(--hx-space-3);
  font-size: 16px;
  color: var(--hx-color-text-secondary, #666);
}

.file-details {
  flex: 1;
}

.file-name {
  color: var(--hx-color-text-primary, #262626);
  font-weight: 500;
  margin-bottom: 2px;
}

.file-meta {
  color: var(--hx-color-text-secondary, #666);
  font-size: 12px;
}

.file-actions {
  display: flex;
  gap: var(--hx-space-2);
}

.empty-module {
  padding: var(--hx-space-5);
  text-align: center;
  color: var(--hx-color-text-tertiary, #999);
  font-size: var(--hx-font-size-base, 14px);
}

.upload-modal-content {
  padding: var(--hx-space-4) 0;
}

.upload-info {
  margin-bottom: var(--hx-space-4);
  padding: var(--hx-space-4);
  background: var(--hx-color-bg-elevated, #f6f6f6);
  border-radius: var(--hx-radius-sm, 6px);
}

.upload-info p {
  margin: 0 0 var(--hx-space-2) 0;
  font-size: var(--hx-font-size-base, 14px);
  color: var(--hx-color-text-secondary, #666);
}

.upload-info p:last-child {
  margin-bottom: 0;
}

.file-preview iframe {
  border: none;
  width: 100%;
  height: 600px;
}

.video-player {
  max-width: 100%;
  border-radius: var(--hx-radius-sm, 6px);
}

.office-preview,
.unsupported-preview {
  padding: var(--hx-space-6);
  text-align: center;
  color: var(--hx-color-text-secondary, #666);
}

.preview-header {
  margin-bottom: var(--hx-space-4);
}
</style>