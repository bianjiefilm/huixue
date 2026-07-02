import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { CodingChallenge, CodeFile } from '../api/challenge';

// 编码挑战状态存储
export const useChallengeStore = defineStore('challenge', () => {
  // 状态
  const currentChallenge = ref<CodingChallenge | null>(null);
  const activeFileId = ref<string>('');
  const activeFile = ref<CodeFile | null>(null);
  const htmlPreviewVisible = ref(false);
  const fileContents = ref<Record<string, string>>({});
  const originalFileContents = ref<Record<string, string>>({});
  
  // 计算属性
  const isHtmlChallenge = computed(() => {
    return currentChallenge.value?.envType === 'html';
  });
  
  const htmlFiles = computed(() => {
    if (!currentChallenge.value || !isHtmlChallenge.value) return [];
    
    // 递归查找所有HTML文件
    const result: CodeFile[] = [];
    
    const findHtmlFiles = (files: CodeFile[]) => {
      files.forEach(file => {
        if (file.isDirectory && file.children) {
          findHtmlFiles(file.children);
        } else if (!file.isDirectory && file.language === 'html') {
          result.push(file);
        }
      });
    };
    
    if (currentChallenge.value.codeFiles && currentChallenge.value.codeFiles.length > 0) {
      findHtmlFiles(currentChallenge.value.codeFiles);
    }
    
    return result;
  });
  
  // 获取主HTML文件内容（用于预览）
  const mainHtmlContent = computed(() => {
    if (!isHtmlChallenge.value || htmlFiles.value.length === 0) return '';
    
    // 优先使用index.html
    const indexHtml = htmlFiles.value.find(file => file.name.toLowerCase() === 'index.html');
    if (indexHtml && indexHtml.id && fileContents.value[indexHtml.id]) {
      return fileContents.value[indexHtml.id];
    }
    
    // 否则使用第一个HTML文件
    if (htmlFiles.value[0].id && fileContents.value[htmlFiles.value[0].id]) {
      return fileContents.value[htmlFiles.value[0].id];
    }
    
    return '';
  });
  
  // 方法
  function setCurrentChallenge(challenge: CodingChallenge) {
    currentChallenge.value = challenge;
    
    // 初始化文件内容
    fileContents.value = {};
    originalFileContents.value = {};
    
    // 递归提取文件内容
    const extractFileContents = (files: CodeFile[]) => {
      files.forEach(file => {
        if (file.isDirectory && file.children) {
          extractFileContents(file.children);
        } else if (!file.isDirectory && file.content) {
          fileContents.value[file.id] = file.content;
          originalFileContents.value[file.id] = file.content;
        }
      });
    };
    
    if (challenge.codeFiles && challenge.codeFiles.length > 0) {
      extractFileContents(challenge.codeFiles);
    }
    
    // 设置默认活动文件
    if (isHtmlChallenge.value && htmlFiles.value.length > 0) {
      setActiveFile(htmlFiles.value[0].id);
    } else if (challenge.codeFiles && challenge.codeFiles.length > 0) {
      // 查找第一个非目录文件
      const findFirstFile = (files: CodeFile[]): string | null => {
        for (const file of files) {
          if (file.isDirectory && file.children) {
            const childId = findFirstFile(file.children);
            if (childId) return childId;
          } else if (!file.isDirectory) {
            return file.id;
          }
        }
        return null;
      };
      
      const firstFileId = findFirstFile(challenge.codeFiles);
      if (firstFileId) {
        setActiveFile(firstFileId);
      }
    }
  }
  
  function setActiveFile(fileId: string) {
    activeFileId.value = fileId;
    
    // 找到对应的文件对象
    const findFile = (files: CodeFile[]): CodeFile | null => {
      for (const file of files) {
        if (file.id === fileId) return file;
        if (file.isDirectory && file.children) {
          const found = findFile(file.children);
          if (found) return found;
        }
      }
      return null;
    };
    
    if (currentChallenge.value?.codeFiles) {
      activeFile.value = findFile(currentChallenge.value.codeFiles);
    }
  }
  
  function updateFileContent(fileId: string, content: string) {
    if (fileId in fileContents.value) {
      fileContents.value[fileId] = content;
      
      // 如果是当前活动文件，同步更新活动文件的内容
      if (activeFile.value && activeFile.value.id === fileId) {
        activeFile.value.content = content;
      }
      
      // 如果是HTML文件且预览正在显示，可能需要更新预览
      if (isHtmlChallenge.value && htmlPreviewVisible.value) {
        // HTML预览逻辑...
      }
    }
  }
  
  function resetFile(fileId: string) {
    if (fileId in originalFileContents.value) {
      fileContents.value[fileId] = originalFileContents.value[fileId];
      
      // 如果是当前活动文件，同步更新活动文件的内容
      if (activeFile.value && activeFile.value.id === fileId) {
        activeFile.value.content = originalFileContents.value[fileId];
      }
    }
  }
  
  function resetAllFiles() {
    Object.keys(originalFileContents.value).forEach(fileId => {
      fileContents.value[fileId] = originalFileContents.value[fileId];
    });
    
    // 更新当前活动文件
    if (activeFile.value && activeFile.value.id in originalFileContents.value) {
      activeFile.value.content = originalFileContents.value[activeFile.value.id];
    }
  }
  
  function toggleHtmlPreview() {
    htmlPreviewVisible.value = !htmlPreviewVisible.value;
  }
  
  // 返回存储的状态和方法
  return {
    // 状态
    currentChallenge,
    activeFileId,
    activeFile,
    htmlPreviewVisible,
    fileContents,
    // 计算属性
    isHtmlChallenge,
    htmlFiles,
    mainHtmlContent,
    // 方法
    setCurrentChallenge,
    setActiveFile,
    updateFileContent,
    resetFile,
    resetAllFiles,
    toggleHtmlPreview
  };
}); 