import { request } from '@/utils/request';

/**
 * 用户登录
 */
export function	materialList(data: {}) {
	return request({
		url: '/api/coursematerial/lists',
		method: 'get',
		params: data,
	})
}
export function	materialDetail(id: number | string) {
	return request({
		url: `/api/coursematerial/${id}`,
		method: 'get',
	})
}
//实践课程列表（微型实验）
export function	microList(data: {}) {
	return request({
		url: '/api/v1/practices',
		method: 'get',
		params: data,
	})
}
export function	microDetail(id: number | string) {
	return request({
		url: `/api/v1/practices/${id}`,
		method: 'get',
	})
}