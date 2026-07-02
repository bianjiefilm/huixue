<template>
  <a-drawer
    :open="visible"
    title="组件属性设置"
    placement="right"
    width="350"
    :mask="false"
    @close="handleClose"
  >
    <template v-if="selectedComponent">
      <a-form layout="vertical">
        <a-form-item label="组件名称">
          <a-input v-model:value="componentData.title" @change="handleTitleChange" />
        </a-form-item>
        
        <a-divider />
        
        <a-tabs v-model:activeKey="activeTabKey">
          <!-- 数据设置选项卡 -->
          <a-tab-pane key="data" tab="数据">
            <a-form-item label="数据源">
              <a-select 
                v-model:value="componentData.dataSource" 
                style="width: 100%"
                @change="handleDataSourceChange"
              >
                <a-select-option value="dataset1">示例数据集1</a-select-option>
                <a-select-option value="dataset2">示例数据集2</a-select-option>
                <a-select-option value="dataset3">示例数据集3</a-select-option>
                <a-select-option value="custom">自定义数据</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item v-if="componentData.dataSource === 'custom'" label="自定义数据">
              <a-textarea
                v-model:value="componentData.customData"
                :rows="6"
                placeholder="请输入JSON格式的数据"
                @change="handleCustomDataChange"
              />
            </a-form-item>
            
            <a-form-item label="数据刷新间隔">
              <a-input-number
                v-model:value="componentData.refreshInterval"
                addon-after="秒"
                :min="0"
                style="width: 100%"
                @change="handleRefreshIntervalChange"
              />
              <div class="form-item-help">设置为0表示不自动刷新</div>
            </a-form-item>
          </a-tab-pane>
          
          <!-- 样式设置选项卡 -->
          <a-tab-pane key="style" tab="样式">
            <a-form-item label="位置和大小">
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-input-number
                    v-model:value="componentData.position.x"
                    addon-before="X"
                    style="width: 100%"
                    @change="handlePositionChange"
                  />
                </a-col>
                <a-col :span="12">
                  <a-input-number
                    v-model:value="componentData.position.y"
                    addon-before="Y"
                    style="width: 100%"
                    @change="handlePositionChange"
                  />
                </a-col>
              </a-row>
              <a-row :gutter="8" style="margin-top: 8px">
                <a-col :span="12">
                  <a-input-number
                    v-model:value="componentData.size.width"
                    addon-before="宽"
                    :min="50"
                    style="width: 100%"
                    @change="handleSizeChange"
                  />
                </a-col>
                <a-col :span="12">
                  <a-input-number
                    v-model:value="componentData.size.height"
                    addon-before="高"
                    :min="50"
                    style="width: 100%"
                    @change="handleSizeChange"
                  />
                </a-col>
              </a-row>
            </a-form-item>
            
            <a-form-item label="背景颜色">
              <a-input
                v-model:value="componentData.style.backgroundColor"
                addon-before="#"
                @change="handleStyleChange"
              />
            </a-form-item>
            
            <a-form-item label="边框">
              <a-row :gutter="8">
                <a-col :span="12">
                  <a-select
                    v-model:value="componentData.style.borderStyle"
                    style="width: 100%"
                    @change="handleStyleChange"
                  >
                    <a-select-option value="none">无</a-select-option>
                    <a-select-option value="solid">实线</a-select-option>
                    <a-select-option value="dashed">虚线</a-select-option>
                    <a-select-option value="dotted">点线</a-select-option>
                  </a-select>
                </a-col>
                <a-col :span="12">
                  <a-input-number
                    v-model:value="componentData.style.borderWidth"
                    addon-after="px"
                    :min="0"
                    :max="10"
                    style="width: 100%"
                    @change="handleStyleChange"
                  />
                </a-col>
              </a-row>
            </a-form-item>
            
            <a-form-item label="圆角">
              <a-input-number
                v-model:value="componentData.style.borderRadius"
                addon-after="px"
                :min="0"
                style="width: 100%"
                @change="handleStyleChange"
              />
            </a-form-item>
            
            <a-form-item label="阴影">
              <a-select
                v-model:value="componentData.style.boxShadow"
                style="width: 100%"
                @change="handleStyleChange"
              >
                <a-select-option value="none">无</a-select-option>
                <a-select-option value="light">浅色</a-select-option>
                <a-select-option value="medium">中等</a-select-option>
                <a-select-option value="dark">深色</a-select-option>
              </a-select>
            </a-form-item>
          </a-tab-pane>
          
          <!-- 高级选项卡 -->
          <a-tab-pane key="advanced" tab="高级">
            <a-form-item label="层级顺序">
              <a-input-number
                v-model:value="componentData.zIndex"
                :min="0"
                style="width: 100%"
                @change="handleZIndexChange"
              />
            </a-form-item>
            
            <a-form-item label="透明度">
              <a-slider
                v-model:value="componentData.style.opacity"
                :min="0"
                :max="1"
                :step="0.1"
                @change="handleStyleChange"
              />
            </a-form-item>
            
            <a-form-item label="可见性">
              <a-switch
                v-model:checked="componentData.visible"
                @change="handleVisibilityChange"
              />
            </a-form-item>
          </a-tab-pane>
        </a-tabs>
        
        <a-divider />
        
        <a-form-item>
          <a-button type="primary" block @click="handleApply">应用更改</a-button>
        </a-form-item>
        
        <a-form-item>
          <a-button danger block @click="handleDelete">删除组件</a-button>
        </a-form-item>
      </a-form>
    </template>
    <a-empty v-else description="请选择一个组件进行编辑" />
  </a-drawer>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue';
import { message } from 'ant-design-vue';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  selectedComponent: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:visible', 'update:properties', 'delete']);

// 活动选项卡
const activeTabKey = ref('data');

// 组件数据（副本）
const componentData = reactive({
  id: '',
  title: '',
  type: '',
  dataSource: 'dataset1',
  customData: '',
  refreshInterval: 0,
  position: { x: 0, y: 0 },
  size: { width: 300, height: 200 },
  zIndex: 0,
  visible: true,
  style: {
    backgroundColor: 'ffffff',
    borderStyle: 'none',
    borderWidth: 0,
    borderRadius: 0,
    boxShadow: 'none',
    opacity: 1
  }
});

// 监听选中组件变化
watch(() => props.selectedComponent, (newVal) => {
  if (newVal) {
    // 复制选中组件的属性到本地状态
    Object.assign(componentData, JSON.parse(JSON.stringify(newVal)));
    
    // 确保所有必要的属性都存在
    if (!componentData.style) {
      componentData.style = {
        backgroundColor: 'ffffff',
        borderStyle: 'none',
        borderWidth: 0,
        borderRadius: 0,
        boxShadow: 'none',
        opacity: 1
      };
    }
  }
}, { deep: true, immediate: true });

// 关闭面板
const handleClose = () => {
  emit('update:visible', false);
};

// 处理标题变更
const handleTitleChange = () => {
  updateProperties();
};

// 处理数据源变更
const handleDataSourceChange = () => {
  updateProperties();
};

// 处理自定义数据变更
const handleCustomDataChange = () => {
  try {
    // 尝试解析JSON以验证格式
    if (componentData.customData) {
      JSON.parse(componentData.customData);
    }
    updateProperties();
  } catch (e) {
    message.error('自定义数据格式错误，请输入有效的JSON');
  }
};

// 处理刷新间隔变更
const handleRefreshIntervalChange = () => {
  updateProperties();
};

// 处理位置变更
const handlePositionChange = () => {
  updateProperties();
};

// 处理大小变更
const handleSizeChange = () => {
  updateProperties();
};

// 处理样式变更
const handleStyleChange = () => {
  updateProperties();
};

// 处理层级变更
const handleZIndexChange = () => {
  updateProperties();
};

// 处理可见性变更
const handleVisibilityChange = () => {
  updateProperties();
};

// 应用更改
const handleApply = () => {
  updateProperties();
  message.success('已应用更改');
};

// 更新属性
const updateProperties = () => {
  emit('update:properties', componentData.id, componentData);
};

// 删除组件
const handleDelete = () => {
  emit('delete', componentData.id);
  emit('update:visible', false);
};
</script>

<style scoped>
.property-panel {
  background-color: #fff;
}

.form-item-help {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-top: 4px;
}
</style> 