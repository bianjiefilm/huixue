import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { 
  getVisualComponents, 
  getComponentCategories, 
  getVisualThemes, 
  getChartData, 
  getVisualManual,
  saveScene,
  getScene
} from '../api/visual';
import type { 
  VisualComponent, 
  ComponentCategory, 
  VisualTheme, 
  ChartData, 
  Manual, 
  Scene
} from '../api/visual';

export const useVisualStore = defineStore('visual', () => {
  // 状态
  const components = ref<VisualComponent[]>([]);
  const categories = ref<ComponentCategory[]>([]);
  const themes = ref<VisualTheme[]>([]);
  const chartData = ref<ChartData[]>([]);
  const manual = ref<Manual | null>(null);
  const currentScene = ref<Scene | null>(null);
  
  // 状态加载标志
  const loading = ref({
    components: false,
    categories: false,
    themes: false,
    chartData: false,
    manual: false,
    scene: false
  });
  
  // 编辑器状态
  const currentTheme = ref<string>('default');
  const canvasComponents = ref<any[]>([]);
  const canvasLayout = ref<any[]>([]);
  const selectedComponentId = ref<string | null>(null);
  const showManual = ref<boolean>(false);
  const manualActiveKey = ref<string>('section-1');
  
  // 计算属性
  const selectedComponent = computed(() => {
    if (!selectedComponentId.value) return null;
    return canvasComponents.value.find(c => c.id === selectedComponentId.value) || null;
  });
  
  const currentThemeObject = computed(() => {
    return themes.value.find(t => t.id === currentTheme.value) || null;
  });
  
  // 方法
  // 加载组件列表
  const fetchComponents = async () => {
    try {
      loading.value.components = true;
      components.value = await getVisualComponents();
    } catch (error) {
      console.error('获取可视化组件失败:', error);
    } finally {
      loading.value.components = false;
    }
  };
  
  // 加载组件类别
  const fetchCategories = async () => {
    try {
      loading.value.categories = true;
      categories.value = await getComponentCategories();
    } catch (error) {
      console.error('获取组件类别失败:', error);
    } finally {
      loading.value.categories = false;
    }
  };
  
  // 加载主题
  const fetchThemes = async () => {
    try {
      loading.value.themes = true;
      themes.value = await getVisualThemes();
    } catch (error) {
      console.error('获取主题失败:', error);
    } finally {
      loading.value.themes = false;
    }
  };
  
  // 加载图表数据
  const fetchChartData = async () => {
    try {
      loading.value.chartData = true;
      chartData.value = await getChartData();
    } catch (error) {
      console.error('获取图表数据失败:', error);
    } finally {
      loading.value.chartData = false;
    }
  };
  
  // 加载手册
  const fetchManual = async () => {
    try {
      loading.value.manual = true;
      manual.value = await getVisualManual();
    } catch (error) {
      console.error('获取操作手册失败:', error);
    } finally {
      loading.value.manual = false;
    }
  };
  
  // 加载场景
  const fetchScene = async (id: string) => {
    try {
      loading.value.scene = true;
      currentScene.value = await getScene(id);
      
      // 更新编辑器状态
      if (currentScene.value) {
        canvasComponents.value = currentScene.value.components;
        canvasLayout.value = currentScene.value.layout;
        currentTheme.value = currentScene.value.theme;
      }
    } catch (error) {
      console.error('获取场景失败:', error);
    } finally {
      loading.value.scene = false;
    }
  };
  
  // 保存当前场景
  const saveCurrentScene = async (name: string, description?: string) => {
    try {
      loading.value.scene = true;
      const sceneData = {
        name,
        description,
        components: canvasComponents.value,
        layout: canvasLayout.value,
        theme: currentTheme.value
      };
      
      currentScene.value = await saveScene(sceneData);
      return currentScene.value;
    } catch (error) {
      console.error('保存场景失败:', error);
      throw error;
    } finally {
      loading.value.scene = false;
    }
  };
  
  // 添加组件到画布
  const addComponent = (componentType: string, position: { x: number, y: number }) => {
    const component = components.value.find(c => c.id === componentType);
    if (!component) return;
    
    const newComponentId = `component-${Date.now()}`;
    
    // 创建新组件
    canvasComponents.value.push({
      id: newComponentId,
      type: component.type,
      name: component.name,
      config: {},
      dataSource: chartData.value.length > 0 ? chartData.value[0].id : null
    });
    
    // 添加到布局
    canvasLayout.value.push({
      i: newComponentId,
      x: position.x,
      y: position.y,
      w: 12,
      h: 8
    });
    
    // 选中新组件
    selectedComponentId.value = newComponentId;
  };
  
  // 删除组件
  const removeComponent = (componentId: string) => {
    canvasComponents.value = canvasComponents.value.filter(c => c.id !== componentId);
    canvasLayout.value = canvasLayout.value.filter(l => l.i !== componentId);
    
    if (selectedComponentId.value === componentId) {
      selectedComponentId.value = null;
    }
  };
  
  // 更新组件配置
  const updateComponentConfig = (componentId: string, config: any) => {
    const component = canvasComponents.value.find(c => c.id === componentId);
    if (component) {
      component.config = { ...component.config, ...config };
    }
  };
  
  // 更新组件数据源
  const updateComponentDataSource = (componentId: string, dataSourceId: string) => {
    const component = canvasComponents.value.find(c => c.id === componentId);
    if (component) {
      component.dataSource = dataSourceId;
    }
  };
  
  // 更新布局
  const updateLayout = (newLayout: any[]) => {
    canvasLayout.value = newLayout;
  };
  
  // 设置当前主题
  const setCurrentTheme = (themeId: string) => {
    currentTheme.value = themeId;
  };
  
  // 设置选中组件
  const setSelectedComponent = (componentId: string | null) => {
    selectedComponentId.value = componentId;
  };
  
  // 切换手册显示状态
  const toggleManual = () => {
    showManual.value = !showManual.value;
  };
  
  // 设置手册活动章节
  const setManualActiveKey = (key: string) => {
    manualActiveKey.value = key;
  };
  
  // 清空画布
  const clearCanvas = () => {
    canvasComponents.value = [];
    canvasLayout.value = [];
    selectedComponentId.value = null;
  };
  
  return {
    // 状态
    components,
    categories,
    themes,
    chartData,
    manual,
    currentScene,
    loading,
    currentTheme,
    canvasComponents,
    canvasLayout,
    selectedComponentId,
    showManual,
    manualActiveKey,
    
    // 计算属性
    selectedComponent,
    currentThemeObject,
    
    // 方法
    fetchComponents,
    fetchCategories,
    fetchThemes,
    fetchChartData,
    fetchManual,
    fetchScene,
    saveCurrentScene,
    addComponent,
    removeComponent,
    updateComponentConfig,
    updateComponentDataSource,
    updateLayout,
    setCurrentTheme,
    setSelectedComponent,
    toggleManual,
    setManualActiveKey,
    clearCanvas
  };
}); 