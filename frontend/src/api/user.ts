import { request } from '@/utils/request';

export interface LoginData {
  username: string;
  password: string;
}

export interface UserInfo {
  id: string;
  username: string;
  email?: string;
  realname?: string;
  mobile?: string;
  avatar?: string;
  role: 'student' | 'teacher' | 'admin';
}

/**
 * 用户登录
 */
export function userLogin(data: LoginData) {
	return request({
		url: '/api/login',
		method: 'post',
		data: data,
	})
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
	return request<UserInfo>({
		url: '/api/user/info',
		method: 'get'
	})
}

