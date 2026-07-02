import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'ant-design-vue';

// 创建axios实例
const instance: AxiosInstance = axios.create({
  // baseURL通过vite代理配置，不在这里设置
  timeout: 10000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  },
  paramsSerializer: (params) => {
    // 使用 URLSearchParams 正确序列化参数
    const searchParams = new URLSearchParams();
    for (const key in params) {
      if (params[key] !== undefined && params[key] !== null) {
        searchParams.append(key, params[key].toString());
      }
    }
    return searchParams.toString();
  }
});

// 请求拦截器
instance.interceptors.request.use(
  (config) => {
    // 在发送请求之前做一些处理
    // 例如，添加token到请求头
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    // 处理请求错误
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
instance.interceptors.response.use(
  (response) => {
    // 对响应数据做一些处理
    const res = response.data;
    
    // 如果是Mock数据直接返回
    if (process.env.NODE_ENV === 'development') {
      return res;
    }
    
    // 处理真实API的返回格式
    // 返回完整的响应对象，让调用方自己处理
    return res;
  },
  (error) => {
    // 处理HTTP错误
    console.error('Response error:', error);
    
    // 处理HTTP状态码
    if (error.response) {
      const status = error.response.status;
      
      switch (status) {
        case 401:
          // 未授权，清除token并跳转到登录页
          localStorage.removeItem('token');
          message.error('登录已过期，请重新登录');
          // 如果有路由实例可以在这里跳转
          // router.push('/login');
          break;
        case 403:
          message.error('没有权限访问该资源');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器错误，请稍后再试');
          break;
        default:
          message.error(`请求错误: ${error.message}`);
      }
    } else {
      // 处理网络错误
      if (error.message.includes('timeout')) {
        message.error('请求超时，请检查网络连接');
      } else {
        message.error(`网络错误: ${error.message}`);
      }
    }
    
    return Promise.reject(error);
  }
);

// 封装GET请求
function get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return instance.get(url, config);
}

// 封装POST请求
function post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return instance.post(url, data, config);
}

// 封装PUT请求
function put<T = any>(url: string, data?: any): Promise<T> {
  return instance.put(url, data);
}

// 封装PATCH请求
function patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
  return instance.patch(url, data, config);
}

// 封装DELETE请求
function del<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return instance.delete(url, config);
}

// 导出HTTP工具
export default {
  get,
  post,
  put,
  patch,
  delete: del
}; 