import { request } from '@/utils/request';

// 可视化组件类型
export interface VisualComponent {
  id: string;
  type: string;
  name: string;
  icon: string;
  category: string;
  description: string;
  previewUrl?: string;
}

// 组件类别
export interface ComponentCategory {
  id: string;
  name: string;
}

// 可视化配置选项
export interface VisualOption {
  id: string;
  name: string;
  type: 'color' | 'number' | 'text' | 'select' | 'switch';
  defaultValue: any;
  options?: any[];
  description?: string;
}

// 可视化主题
export interface VisualTheme {
  id: string;
  name: string;
  previewUrl: string;
  colors: string[];
}

// 图表数据
export interface ChartData {
  id: string;
  name: string;
  data: any;
}

// 实训操作手册
export interface Manual {
  id: string;
  title: string;
  content: string;
  sections: Array<{
    id: string;
    title: string;
    content: string;
  }>;
}

// 场景保存信息
export interface Scene {
  id: string;
  name: string;
  description?: string;
  components: any[];
  layout: any[];
  theme: string;
  createdAt: string;
  updatedAt: string;
}

/**
 * 获取可视化组件列表
 */
export function getVisualComponents() {
  return request<VisualComponent[]>({
    url: '/api/visual/components',
    method: 'get',
  });
}

/**
 * 获取组件类别
 */
export function getComponentCategories() {
  return request<ComponentCategory[]>({
    url: '/api/visual/categories',
    method: 'get',
  });
}

/**
 * 获取可视化主题
 */
export function getVisualThemes() {
  return request<VisualTheme[]>({
    url: '/api/visual/themes',
    method: 'get',
  });
}

/**
 * 获取可视化图表数据
 */
export function getChartData() {
  return request<ChartData[]>({
    url: '/api/visual/chart-data',
    method: 'get',
  });
}

/**
 * 获取实训操作手册
 */
export function getVisualManual() {
  return request<Manual>({
    url: '/api/visual/manual',
    method: 'get',
  });
}

/**
 * 保存场景
 */
export function saveScene(scene: Omit<Scene, 'id' | 'createdAt' | 'updatedAt'>) {
  return request<Scene>({
    url: '/api/visual/scenes',
    method: 'post',
    data: scene,
  });
}

/**
 * 获取场景
 */
export function getScene(id: string) {
  return request<Scene>({
    url: `/api/visual/scenes/${id}`,
    method: 'get',
  });
} 