import axios from 'axios';
import type { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig, AxiosRequestConfig } from 'axios';
import { useGlobalFeedbackStore } from '@/stores/globalFeedback';
import { useUserStore } from '@/stores/user';
import router from '@/router';
import { getToken, clearAuth } from '@/utils/auth';

// 创建axios实例
const request: AxiosInstance = axios.create({
  // baseURL通过vite代理配置，不在这里设置
  timeout: 10000, // 请求超时时间
  withCredentials: true, // 允许发送cookies
  headers: {
    'Content-Type': 'application/json',
  }
});

// 获取反馈store实例
const getFeedbackStore = () => {
  return useGlobalFeedbackStore();
};

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 在发送请求之前做些什么
    const token = getToken();
    console.log('Request interceptor - URL:', config.url, 'Token:', !!token);
    if (token) {
      config.headers.set('Authorization', `Bearer ${token}`);
      console.log('Authorization header set');
    } else {
      console.log('No token found, Authorization header not set');
    }
    return config;
  },
  (error) => {
    // 对请求错误做些什么
    console.error('请求发送失败', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 对响应数据做些什么
    const data = response.data;
    console.log('Response URL:', response.config.url);
    console.log('Response data:', data);
    
    // 特殊处理登录接口（直接返回数据）
    if (response.config.url?.includes('/api/login')) {
      console.log('Login response detected, returning data directly');
      return data;
    }

    
    // 根据后端接口规范判断请求是否成功
    if ((data.code === 1 || data.code === "0000") && response.status === 200) {
      return data; // 统一返回完整响应对象
    }else if(data.code === 401013 || data.code ===401){
		clearAuth();
		const feedbackStore = getFeedbackStore();
		feedbackStore.error(data.msg || '请求失败');
		// 避免重复跳转到登录页
		if (router.currentRoute.value.path !== '/login') {
			router.push({
				path: '/login',
				query: { redirect: router.currentRoute.value.fullPath }
			});
		}
    } else if (response.status === 200 && !data.code) {
      // 如果状态码是200但没有code字段，检查是否是HTML响应
      const contentType = response.headers['content-type'] || '';
      if (contentType.includes('text/html')) {
        console.error('Received HTML instead of JSON:', response.config.url);
        const feedbackStore = getFeedbackStore();
        feedbackStore.error('服务器返回了HTML页面，可能是API路径错误');
        return Promise.reject(new Error('Invalid response format: HTML received instead of JSON'));
      }
      // 如果响应是数组或对象（但不是HTML），直接返回数据
      if (Array.isArray(data) || (typeof data === 'object' && data !== null && !data.toString().startsWith('<!DOCTYPE'))) {
        console.log('Status 200 without code field, returning data directly');
        return data;
      }
      // 否则认为是错误
      const feedbackStore = getFeedbackStore();
      feedbackStore.error('响应格式错误');
      return Promise.reject(new Error('Invalid response format'));
    } else if (response.status === 422 && data.detail) {
      // 处理Pydantic验证错误，将详细错误信息传递给组件
      console.log('Pydantic validation error detected:', data.detail);
      const feedbackStore = getFeedbackStore();

      // 提取具体的验证错误信息
      let errorMessage = '输入信息有误，请检查后重新提交';
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const firstError = data.detail[0];
        if (firstError.msg) {
          errorMessage = firstError.msg;
        }
      }

      feedbackStore.error(errorMessage);
      return Promise.reject({
        type: 'validation_error',
        errors: data.detail,
        message: errorMessage,
        originalError: error
      });
    } else {
      const feedbackStore = getFeedbackStore();
      const errorMessage = data.message || data.msg || `请求失败 (${response.status})`;
      feedbackStore.error(errorMessage);
      return Promise.reject(new Error(errorMessage));
    }
  },
  (error) => {
    // 对响应错误做些什么
    let errorMsg = '网络错误，请稍后重试';

    console.error('API请求错误详情:', {
      message: error.message,
      code: error.code,
      config: error.config,
      response: error.response ? {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data
      } : null
    });

    // AI 功能被总开关关闭时后端返回 403 + code=AI_DISABLED,静默处理不弹全局错误
    if (error.response?.status === 403 && error.response?.data?.detail?.code === 'AI_DISABLED') {
      console.info('AI 功能未开放,已静默处理:', error.config?.url);
      return Promise.reject(error);
    }

    // 处理网络连接错误
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      errorMsg = '无法连接到服务器，请检查后端服务是否已启动';
      console.error('Backend service is not running on', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000');
    } else if (error.response) {
      const { status } = error.response;
      
      // 根据状态码定制错误信息
      switch (status) {
        case 400:
          errorMsg = '请求错误';
          break;
        case 401:
          errorMsg = '未授权，请重新登录';
          // 可以在这里处理登出逻辑
          // logout();
          break;
        case 403:
          errorMsg = '拒绝访问';
          break;
        case 404:
          errorMsg = '请求地址出错';
          break;
        case 408:
          errorMsg = '请求超时';
          break;
        case 500:
          errorMsg = '服务器内部错误';
          break;
        case 501:
          errorMsg = '服务未实现';
          break;
        case 502:
          errorMsg = '网关错误';
          break;
        case 503:
          errorMsg = '服务不可用';
          break;
        case 504:
          errorMsg = '网关超时';
          break;
        case 505:
          errorMsg = 'HTTP版本不受支持';
          break;
        default:
          errorMsg = `未知错误：${status}`;
      }
    }
    
    const feedbackStore = getFeedbackStore();
    feedbackStore.error(errorMsg);
    console.error(errorMsg, error);
    return Promise.reject(error);
  }
);

// 封装GET请求
export const get = <T = any>(url: string, params?: object): Promise<T> => {
  return request.get(url, { params });
};

// 封装POST请求
export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post(url, data, config);
};

// 封装PUT请求
export const put = <T = any>(url: string, data?: object): Promise<T> => {
  return request.put(url, data);
};

// 封装DELETE请求
export const del = <T = any>(url: string, params?: object): Promise<T> => {
  return request.delete(url, { params });
};

// 封装PATCH请求
export const patch = <T = any>(url: string, data?: object): Promise<T> => {
  return request.patch(url, data);
};

// 导出默认请求实例
export default request;
export { request }; 