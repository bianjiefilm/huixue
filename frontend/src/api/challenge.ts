import { request } from '../utils/request';

// 类型定义
export interface CodingChallenge {
  id: string;
  title: string;
  taskContent: string;
  envType: string;
  difficulty: string;
  coin: number;
  coins: number;
  type: string;
  skills: string[];
  testCases: TestCase[];
  referenceAnswer: string;
  codeFiles: CodeFile[];
}

export interface TestCase {
  id: string;
  title: string;
  input: string;
  expectedOutput: string;
  hidden: boolean;
}

export interface CodeFile {
  id: string;
  name: string;
  content: string;
  language: string;
  isDirectory?: boolean;
  children?: CodeFile[];
}

// 获取任务详情
export async function getTaskDetail(taskId: string, userId?: number) {
  return await request({
    url: `/api/v1/tasks/${taskId}`,
    method: 'get',
    params: { user_id: userId }
  });
}

// 获取实践的任务列表
export async function getPracticeTasks(practiceId: string) {
  return await request({
    url: `/api/v1/practices/${practiceId}/tasks`,
    method: 'get',
    params: { page: 1, page_size: 100 }
  });
}

// 获取任务测试集
export async function getTaskTests(taskId: string, revealAll: boolean = false, userRole: string = 'student') {
  return await request({
    url: `/api/v1/tasks/${taskId}/tests`,
    method: 'get',
    params: { revealAll, user_role: userRole }
  });
}

// 获取参考答案
export async function getTaskAnswer(taskId: string, userId: number, userRole: string = 'student') {
  return await request({
    url: `/api/v1/tasks/${taskId}/answer`,
    method: 'get',
    params: { user_id: userId, user_role: userRole }
  });
}

// 保存代码快照
export async function saveCodeSnapshot(taskId: string, userId: number, repoHash: string, files: any) {
  return await request({
    url: `/api/v1/tasks/${taskId}/snapshots`,
    method: 'post',
    params: { user_id: userId },
    data: { repo_hash: repoHash, files }
  });
}

// 获取通关时代码快照
export async function getPassedCodeSnapshot(taskId: string, userId: number) {
  return await request({
    url: `/api/v1/tasks/${taskId}/passed-snapshot`,
    method: 'get',
    params: { user_id: userId }
  });
}

// 评测任务
export async function evaluateTask(taskId: string, userId: number, data: {
  answer?: string;
  code?: string;
  codeRepoHash?: string;
  files?: any;
}) {
  return await request({
    url: `/api/v1/tasks/${taskId}/evaluate`,
    method: 'post',
    params: { user_id: userId },
    data,
    timeout: 120000
  });
}

// 获取挑战信息 - 使用真实API
export async function getChallenge(id: string): Promise<CodingChallenge> {
  // 使用 getTaskDetail API 获取任务详情
  const response = await getTaskDetail(id);
  const taskData = response?.data?.data || response?.data || response;
  
  // 转换为 CodingChallenge 格式
  return {
    id: taskData.taskId?.toString() || id,
    title: taskData.title || '',
    taskContent: taskData.handbookMd || '',
    envType: taskData.envType || 'code',
    difficulty: taskData.difficulty || 'intermediate',
    coin: taskData.coin || 0,
    coins: taskData.coin || 0,
    type: 'practice',
    skills: taskData.skills || [],
    testCases: [],
    referenceAnswer: '',
    codeFiles: []
  };
}

// 重置命令行环境
export async function resetTerminalEnvironment(taskId: string, userId: number) {
  return await request({
    url: `/api/v1/tasks/${taskId}/reset-terminal`,
    method: 'post',
    params: { user_id: userId }
  });
}

// 评测代码
export async function evaluateCodeWithTestCase(code: string, testCase: TestCase, taskId?: string, userId?: number) {
  // 如果有 taskId，使用真实的评测 API
  if (taskId && userId) {
    const response = await evaluateTask(taskId, userId, {
      code,
      answer: JSON.stringify({ testCaseId: testCase.id, input: testCase.input })
    });
    
    return {
      passed: response.data?.passed || false,
      actualOutput: response.data?.output || '',
      error: response.data?.error
    };
  }
  
  // 否则返回模拟结果
  return {
    passed: false,
    actualOutput: '',
    error: '需要提供 taskId 和 userId 进行评测'
  };
}

// 使用所有测试用例评测代码
export async function evaluateCodeWithAllTestCases(code: string, testCases: TestCase[], taskId?: string, userId?: number) {
  // 如果有 taskId，使用真实的批量评测 API
  if (taskId && userId) {
    const response = await evaluateTask(taskId, userId, {
      code,
      answer: JSON.stringify({ evaluateAll: true })
    });
    
    // 根据响应构建结果
    const evaluationResults = response.data?.results || [];
    return testCases.map((testCase, index) => {
      const result = evaluationResults[index] || {};
      return {
        id: testCase.id,
        title: testCase.title,
        passed: result.passed || false,
        actualOutput: result.output || '',
        expectedOutput: testCase.expectedOutput,
        error: result.error,
        hidden: testCase.hidden
      };
    });
  }
  
  // 否则返回错误结果
  return testCases.map(testCase => ({
    id: testCase.id,
    title: testCase.title,
    passed: false,
    actualOutput: '',
    expectedOutput: testCase.expectedOutput,
    error: '需要提供 taskId 和 userId 进行评测',
    hidden: testCase.hidden
  }));
}

// 验证HTML挑战
export async function validateHtmlChallenge(htmlContent: string, testCases: TestCase[]) {
  // 真实环境下使用post请求
  // return await post('/api/challenges/validate-html', { htmlContent, testCases });
  
  // 在实际应用中，这里可能会调用服务端API来验证HTML代码
  // 这里我们使用模拟实现
  
  const results = [];
  for (const testCase of testCases) {
    // 简单的验证实现，实际应用中可能会更复杂
    let passed = true;
    let error = '';
    
    // 基本HTML结构测试
    if (testCase.id === '1') {
      passed = htmlContent.includes('<!DOCTYPE html>') && 
               htmlContent.includes('<html') && 
               htmlContent.includes('<head') && 
               htmlContent.includes('<body');
      
      if (!passed) {
        error = '缺少必要的HTML文档结构标签';
      }
    }
    // 内容完整性测试
    else if (testCase.id === '2') {
      // 个人简介页面测试
      if (testCase.input.includes('个人信息') || testCase.input.includes('个人简介')) {
        const hasPersonalInfo = htmlContent.includes('个人') || htmlContent.includes('简介') || htmlContent.includes('信息');
        const hasEducation = htmlContent.includes('教育') || htmlContent.includes('学历') || htmlContent.includes('学位');
        const hasInterests = htmlContent.includes('兴趣') || htmlContent.includes('爱好');
        const hasContact = htmlContent.includes('联系') || htmlContent.includes('邮箱') || htmlContent.includes('email');
        
        passed = hasPersonalInfo && hasEducation && hasInterests && hasContact;
        
        if (!passed) {
          error = '页面缺少必要的内容信息（个人信息、教育背景、兴趣爱好或联系方式）';
        }
      } 
      // 响应式布局测试
      else if (testCase.input.includes('响应式布局') || testCase.input.includes('不同宽度')) {
        passed = htmlContent.includes('width') && htmlContent.includes('media');
        
        if (!passed) {
          error = '页面缺少响应式布局相关代码';
        }
      }
      // 交互组件测试
      else if (testCase.input.includes('轮播图') || testCase.input.includes('模态框')) {
        passed = htmlContent.includes('addEventListener') || 
                htmlContent.includes('onclick') || 
                htmlContent.includes('function');
        
        if (!passed) {
          error = '页面缺少必要的JavaScript交互代码';
        }
      }
    }
    // 样式测试
    else if (testCase.id === '3') {
      if (testCase.input.includes('相对单位')) {
        passed = htmlContent.includes('em') || 
                htmlContent.includes('rem') || 
                htmlContent.includes('%') ||
                htmlContent.includes('vh') ||
                htmlContent.includes('vw');
        
        if (!passed) {
          error = '页面样式未使用相对单位';
        }
      }
      else {
        passed = htmlContent.includes('<style') || htmlContent.includes('class=') || htmlContent.includes('style=');
        
        if (!passed) {
          error = '页面缺少基本样式';
        }
      }
    }
    
    results.push({
      id: testCase.id,
      title: testCase.title,
      passed,
      actualOutput: '预览窗口中显示的内容',
      expectedOutput: testCase.expectedOutput,
      error,
      hidden: testCase.hidden
    });
  }
  
  return results;
} 