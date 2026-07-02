// 用户认证单元测试文件 - 浏览器环境执行
console.log('🔍 开始测试用户认证功能...\n');

// 创建axios实例
const api = axios.create({
  baseURL: '/',
  timeout: 5000
});

// 测试用户凭据
const testUsers = [
  { username: 'admin', password: 'admin123' },
  { username: 'teacher', password: 'teacher123' },
  { username: 'student', password: 'student123' }
];

// 错误的用户凭据
const wrongUserCredentials = { username: 'wrong', password: 'wrong123' };

// 日志输出元素
let logElement;

// 初始化日志显示
function initLogDisplay() {
  logElement = document.getElementById('log');
  if (!logElement) {
    logElement = document.createElement('div');
    logElement.id = 'log';
    logElement.style.fontFamily = 'monospace';
    logElement.style.whiteSpace = 'pre-wrap';
    logElement.style.padding = '10px';
    logElement.style.border = '1px solid #ccc';
    logElement.style.borderRadius = '5px';
    logElement.style.margin = '10px';
    logElement.style.backgroundColor = '#f5f5f5';
    logElement.style.height = '500px';
    logElement.style.overflow = 'auto';
    document.body.appendChild(logElement);
  }
}

// 自定义日志功能
function log(message, type = 'info') {
  const now = new Date();
  const timestamp = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
  
  let color = 'black';
  if (type === 'success') color = 'green';
  if (type === 'error') color = 'red';
  if (type === 'warn') color = 'orange';
  if (type === 'highlight') color = 'blue';
  
  console.log(`[${timestamp}] ${message}`);
  
  if (logElement) {
    const logLine = document.createElement('div');
    logLine.innerHTML = `<span style="color:gray">[${timestamp}]</span> <span style="color:${color}">${message}</span>`;
    logElement.appendChild(logLine);
    logElement.scrollTop = logElement.scrollHeight;
  }
}

// 执行登录测试
async function testLogin() {
  log('======= 开始测试登录接口 =======', 'highlight');
  
  // 测试成功登录
  for (const user of testUsers) {
    try {
      log(`测试用户 ${user.username} 登录...`);
      const response = await api.post('/api/login', user);
      
      if (response.data.success && response.data.code === 200) {
        log('✅ 登录成功！', 'success');
        log(`- 获取到Token: ${response.data.data.token}`);
        log(`- 用户信息: ${JSON.stringify(response.data.data.user)}`);
      } else {
        log(`❌ 登录失败！${response.data.message}`, 'error');
      }
    } catch (error) {
      log(`❌ 请求出错: ${error.message}`, 'error');
    }
    log('------------------------');
  }
  
  // 测试失败登录
  try {
    log(`测试错误凭据登录...`);
    const response = await api.post('/api/login', wrongUserCredentials);
    
    if (!response.data.success && response.data.code === 401) {
      log('✅ 测试成功：系统正确拒绝了错误的凭据', 'success');
    } else {
      log('❌ 测试失败：系统未能拒绝错误的凭据', 'error');
    }
  } catch (error) {
    log(`❌ 请求出错: ${error.message}`, 'error');
  }
  
  log('======= 登录接口测试完成 =======\n', 'highlight');
}

// 执行获取用户信息测试
async function testGetUserInfo(token) {
  log('======= 开始测试获取用户信息接口 =======', 'highlight');
  
  try {
    // 使用token参数（在实际应用中通常是通过headers传递）
    const response = await api.get(`/api/user/info?token=${token}`);
    
    if (response.data.success && response.data.code === 200) {
      log('✅ 获取用户信息成功！', 'success');
      log(`- 用户信息: ${JSON.stringify(response.data.data)}`);
    } else {
      log(`❌ 获取用户信息失败！${response.data.message}`, 'error');
    }
  } catch (error) {
    log(`❌ 请求出错: ${error.message}`, 'error');
  }
  
  // 测试无效Token
  try {
    const response = await api.get('/api/user/info?token=invalid_token');
    
    if (!response.data.success && response.data.code === 401) {
      log('✅ 测试成功：系统正确拒绝了无效的Token', 'success');
    } else {
      log('❌ 测试失败：系统未能拒绝无效的Token', 'error');
    }
  } catch (error) {
    log(`❌ 请求出错: ${error.message}`, 'error');
  }
  
  log('======= 获取用户信息接口测试完成 =======\n', 'highlight');
}

// 执行登出测试
async function testLogout(token) {
  log('======= 开始测试登出接口 =======', 'highlight');
  
  try {
    const response = await api.post(`/api/logout?token=${token}`);
    
    if (response.data.success && response.data.code === 200) {
      log('✅ 登出成功！', 'success');
    } else {
      log(`❌ 登出失败！${response.data.message}`, 'error');
    }
  } catch (error) {
    log(`❌ 请求出错: ${error.message}`, 'error');
  }
  
  // 测试登出后使用相同Token
  try {
    const response = await api.get(`/api/user/info?token=${token}`);
    
    if (!response.data.success && response.data.code === 401) {
      log('✅ 测试成功：登出后Token已失效', 'success');
    } else {
      log('❌ 测试失败：登出后Token仍然有效', 'error');
    }
  } catch (error) {
    log(`❌ 请求出错: ${error.message}`, 'error');
  }
  
  log('======= 登出接口测试完成 =======\n', 'highlight');
}

// 主测试函数
async function runTests() {
  log('🔍 开始测试用户认证功能...\n', 'highlight');
  
  // 执行登录测试并保存token
  let token = '';
  
  try {
    const loginResponse = await api.post('/api/login', testUsers[0]);
    if (loginResponse.data.success) {
      token = loginResponse.data.data.token;
      log(`👤 以管理员身份登录成功，获取到token: ${token}`, 'success');
    }
  } catch (error) {
    log(`登录失败，无法继续测试: ${error.message}`, 'error');
    return;
  }
  
  // 顺序测试所有接口
  await testLogin();
  
  if (token) {
    await testGetUserInfo(token);
    await testLogout(token);
  }
  
  log('✨ 所有测试完成！', 'highlight');
}

// 执行测试
runTests(); 