import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { 
  getOrganizationTree as apiGetOrganizationTree,
  getOrganizationList as apiGetOrganizationList,
  createOrganization as apiCreateOrganization,
  updateOrganization as apiUpdateOrganization,
  deleteOrganization as apiDeleteOrganization,
  batchDeleteOrganizations as apiBatchDeleteOrganizations,
  batchUpdateOrganizationStatus as apiBatchUpdateOrganizationStatus,
  importOrganizations as apiImportOrganizations,
  type OrganizationItem,
  type OrganizationForm,
  type QueryParams as ApiQueryParams
} from '@/api/organizations'

// 定义组织节点类型
export type NodeType = 'school' | 'college' | 'major' | 'grade' | 'class';

// 定义组织节点接口
export interface OrganizationNode {
  key: string;
  title: string;
  nodeType: NodeType;
  children?: OrganizationNode[];
  isLeaf?: boolean;
}

// 定义表格项接口
export interface OrganizationItem {
  id: string;
  name: string;
  code: string;
  description?: string;
  status: boolean;
  createTime: string;
  majorCount?: number;
  degreeType?: 'bachelor' | 'master' | 'doctor';
  headTeacher?: string;
  studentCount?: number;
  year?: number;
}

// 定义分页列表结果
export interface PageResult<T> {
  items: T[];
  total: number;
}

// 定义查询参数
export interface QueryParams {
  parentId: string;
  type: string;
  page: number;
  pageSize: number;
  keyword?: string;
}

// 组织信息表单
export interface OrganizationForm {
  name: string;
  code: string;
  description?: string;
  parentId: string;
  type: string;
  degreeType?: 'bachelor' | 'master' | 'doctor';
  year?: number;
  headTeacher?: string;
  id?: string;
}

export const useDepartmentStore = defineStore('department', () => {
  // 获取组织树
  async function getOrganizationTree(): Promise<OrganizationNode[]> {
    try {
      const response = await apiGetOrganizationTree();
      console.log('组织树API响应:', response);
      
      // 转换org_type为nodeType
      const mapOrgTypeToNodeType = (orgType: string): NodeType => {
        const typeMap: Record<string, NodeType> = {
          'COLLEGE': 'college',
          'MAJOR': 'major',
          'GRADE': 'grade',
          'CLASS': 'class'
        };
        return typeMap[orgType] || 'college';
      };
      
      // 转换API数据为前端格式（符合Ant Design Vue Tree组件格式）
      const convertToTreeFormat = (nodes: any[]): any[] => {
        if (!Array.isArray(nodes)) {
          console.warn('组织树数据不是数组:', nodes);
          return [];
        }
        return nodes.map(node => {
          const nodeType = node.org_type ? mapOrgTypeToNodeType(node.org_type) : 'college';
          const children = node.children && Array.isArray(node.children) && node.children.length > 0 
            ? convertToTreeFormat(node.children) 
            : undefined; // Tree组件中，如果没有子节点，children应该是undefined而不是空数组
          
          return {
            key: `${nodeType}-${node.id}`,
            title: node.name || '未命名',
            nodeType: nodeType, // 保留用于业务逻辑
            children: children, // Tree组件格式
            isLeaf: !children || children.length === 0 // 保留用于业务逻辑
          };
        });
      };
      
      // 处理响应数据
      let data = response;
      if (response && response.data && Array.isArray(response.data)) {
        data = response.data;
      } else if (Array.isArray(response)) {
        data = response;
      } else {
        console.error('组织树响应格式错误:', response);
        return [];
      }
      
      console.log('原始组织树数据:', data);
      const colleges = convertToTreeFormat(data);
      console.log('转换后的学院数据:', colleges);
      
      // 添加学校根节点
      const schoolNode = {
        key: 'school-1',
        title: '慧学', // 可以从学校信息API获取
        nodeType: 'school' as NodeType,
        children: colleges.length > 0 ? colleges : undefined,
        isLeaf: colleges.length === 0
      };
      
      const result = [schoolNode];
      console.log('最终组织树数据:', result);
      return result;
    } catch (error) {
      console.error('获取组织树失败:', error);
      message.error('获取组织架构失败');
      return [];
    }
  }

  // 获取组织列表
  async function getOrganizationList(params: QueryParams): Promise<PageResult<OrganizationItem>> {
    try {
      // 将小写的nodeType转换为大写的org_type（后端期望的格式）
      const typeMap: Record<string, string> = {
        'college': 'COLLEGE',
        'major': 'MAJOR',
        'grade': 'GRADE',
        'class': 'CLASS'
      };
      const orgType = params.type ? typeMap[params.type.toLowerCase()] : undefined;
      
      const apiParams: ApiQueryParams = {
        parent_id: params.parentId ? parseInt(params.parentId) : undefined,
        type: orgType as any, // 后端期望大写字符串
        page: params.page,
        page_size: params.pageSize,
        keyword: params.keyword
      };
      
      console.log('组织列表API参数:', apiParams);
      
      const response = await apiGetOrganizationList(apiParams);
      console.log('组织列表API响应:', response);
      
      // 处理不同的响应格式
      let responseData = response;
      if (response && response.data) {
        responseData = response.data;
      } else if (response && response.list) {
        responseData = response;
      }
      
      console.log('处理后的响应数据:', responseData);
      
      // 转换API数据为前端格式
      const convertToFrontendFormat = (item: any): OrganizationItem => ({
        id: item.id.toString(),
        name: item.name,
        code: item.code || '',
        description: item.description || '',
        status: item.is_active ? 'active' : 'inactive',
        createTime: item.created_at || item.createTime || '',
        majorCount: item.major_count || 0,
        degreeType: item.degree_type || '',
        headTeacher: item.head_teacher || '',
        studentCount: item.student_count || 0,
        year: item.year || null
      });
      
      const list = responseData?.list || responseData?.items || [];
      const total = responseData?.meta?.total || responseData?.total || 0;
      
      console.log('组织列表数据:', list, '总数:', total);
      
      return {
        items: list.map(convertToFrontendFormat),
        total: total
      };
    } catch (error) {
      console.error('获取组织列表失败:', error);
      message.error('获取组织列表失败');
      return { items: [], total: 0 };
    }
  }

  // 创建组织
  async function createOrganization(data: OrganizationForm): Promise<OrganizationItem> {
    try {
      // 调试日志
      console.log('[Store] createOrganization 收到数据:', data);
      console.log('[Store] data.parentId:', data.parentId, '类型:', typeof data.parentId);
      
      // 确保 parent_id 是数字或 null（不是 undefined）
      let parentIdNum: number | null = null;
      if (data.parentId) {
        const parsed = parseInt(data.parentId);
        if (!isNaN(parsed)) {
          parentIdNum = parsed;
        }
      }
      
      const apiData: any = {
        name: data.name,
        code: data.code,
        type: data.type,  // Department.vue 已经传入大写的类型
        parent_id: parentIdNum,  // 使用处理后的值
        description: data.description,
        degree_type: data.degreeType,
        head_teacher: data.headTeacher,
        year: data.year
      };
      
      console.log('[Store] 发送到后端的数据:', apiData);
      
      const response = await apiCreateOrganization(apiData);
      
      // 调试：查看响应结构
      console.log('创建组织响应:', response);
      console.log('响应类型:', typeof response);
      console.log('响应键:', Object.keys(response || {}));
      
      // response已经被拦截器处理，直接就是data部分
      const responseData = response?.data || response;
      
      if (!responseData || !responseData.id) {
        throw new Error('创建组织成功但未返回有效数据');
      }
      
      // 转换为前端格式
      return {
        id: responseData.id.toString(),
        name: responseData.name,
        code: responseData.code,
        description: responseData.description || '',
        status: responseData.status,
        createTime: responseData.created_at,
        degreeType: responseData.degree_type,
        headTeacher: responseData.head_teacher,
        studentCount: responseData.student_count || 0,
        year: responseData.year,
        majorCount: responseData.major_count || 0
      };
    } catch (error) {
      console.error('创建组织失败:', error);
      message.error('创建组织失败');
      throw error;
    }
  }

  // 更新组织
  async function updateOrganization(data: OrganizationForm & { id: string }): Promise<OrganizationItem> {
    try {
      const apiData: any = {
        name: data.name,
        code: data.code,
        type: data.type,
        parent_id: data.parentId ? parseInt(data.parentId) : undefined,
        description: data.description,
        degree_type: data.degreeType,
        head_teacher: data.headTeacher,
        year: data.year
      };
      
      const response = await apiUpdateOrganization(parseInt(data.id), apiData);
      
      // response可能是 {code, message, data} 格式或直接是 data
      const responseData = response.data || response;
      
      // 确保 responseData 有效
      if (!responseData || !responseData.id) {
        throw new Error('更新成功但未返回有效数据');
      }
      
      // 转换为前端格式
      return {
        id: responseData.id.toString(),
        name: responseData.name,
        code: responseData.code,
        description: responseData.description,
        status: responseData.status,
        createTime: responseData.created_at,
        degreeType: responseData.degree_type,
        headTeacher: responseData.head_teacher,
        studentCount: responseData.student_count || 0,
        year: responseData.year,
        majorCount: responseData.major_count || 0
      };
    } catch (error) {
      console.error('更新组织失败:', error);
      message.error('更新组织失败');
      throw error;
    }
  }

  // 删除组织
  async function deleteOrganization(id: string): Promise<void> {
    try {
      await apiDeleteOrganization(parseInt(id));
      message.success('删除组织成功');
    } catch (error: any) {
      console.error('删除组织失败:', error);
      const errorMessage = error.response?.data?.message || '删除组织失败';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }

  // 批量删除组织
  async function batchDeleteOrganization(ids: string[]): Promise<void> {
    try {
      const numericIds = ids.map(id => parseInt(id));
      const response = await apiBatchDeleteOrganizations(numericIds);
      
      if (response.data.success) {
        message.success('批量删除组织成功');
      } else {
        const errorMessage = response.data.error_message || '批量删除组织失败';
        message.error(errorMessage);
        throw new Error(errorMessage);
      }
    } catch (error: any) {
      console.error('批量删除组织失败:', error);
      const errorMessage = error.response?.data?.message || '批量删除组织失败';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }

  // 批量更新组织状态
  async function batchUpdateOrganizationStatus(ids: string[], status: boolean): Promise<void> {
    try {
      const numericIds = ids.map(id => parseInt(id));
      await apiBatchUpdateOrganizationStatus(numericIds, status);
      message.success(`批量${status ? '启用' : '停用'}组织成功`);
    } catch (error: any) {
      console.error('批量更新组织状态失败:', error);
      const errorMessage = error.response?.data?.message || '批量更新组织状态失败';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }

  // 导入组织
  async function importOrganization(formData: FormData): Promise<void> {
    try {
      const file = formData.get('file') as File;
      if (!file) {
        throw new Error('请选择要导入的文件');
      }
      
      const response = await apiImportOrganizations(file, {
        skip_duplicates: true,
        update_existing: false
      });
      
      const { success_count, failed_count, errors } = response.data;
      
      if (failed_count > 0) {
        message.warning(`导入完成，成功 ${success_count} 条，失败 ${failed_count} 条`);
        if (errors && errors.length > 0) {
          console.error('导入错误详情:', errors);
        }
      } else {
        message.success(`导入成功，共导入 ${success_count} 条记录`);
      }
    } catch (error: any) {
      console.error('导入组织失败:', error);
      const errorMessage = error.response?.data?.message || '导入组织失败';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }

  return {
    getOrganizationTree,
    getOrganizationList,
    createOrganization,
    updateOrganization,
    deleteOrganization,
    batchDeleteOrganization,
    batchUpdateOrganizationStatus,
    importOrganization
  }
}) 