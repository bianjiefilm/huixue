import { request } from '@/utils/request';

/**
 * 部门树
 */
export function	departTreeList(data: {}) {
	return request({
		url: '/api/v1/classes/departlists',
		method: 'get',
		params: data,
	})
}
/**
 * 班级学生列表
 */
export function	classStuList(data: {}) {
	return request({
		url: '/api/v1/classes/classtulists',
		method: 'get',
		params: data,
	})
}
