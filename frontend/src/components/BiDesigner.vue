<template>
  <div class="bi-designer-container">
    <div v-if="loading" class="loading-state">
      <a-spin size="large" tip="正在加载数据..." />
    </div>
    <div v-else-if="error" class="error-state">
      <a-empty :description="error">
        <a-button type="primary" @click="retryLoad">重试</a-button>
      </a-empty>
    </div>
    <div v-else-if="!hasData" class="error-state">
      <a-empty description="暂无数据" />
    </div>
    <div v-else class="graphic-walker-wrapper" ref="gwContainer">
      <!-- React Component will be mounted here -->
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, watch, toRaw, computed } from 'vue';
import { GraphicWalker } from '@kanaries/graphic-walker';
import { message } from 'ant-design-vue';
import React from 'react';
import ReactDOM from 'react-dom/client';

const props = defineProps({
  trainingId: {
    type: [String, Number],
    required: true
  },
  classroomId: {
    type: [String, Number],
    default: ''
  },
  readOnly: {
    type: Boolean,
    default: false
  },
  snapshot: {
    type: [Object, Array],
    default: null
  },
  initialData: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits<{
  (e: 'spec-change', spec: any): void
}>();

// 上一次的 spec 快照，用于变化检测
let lastSpecSnapshot = '';
let specCheckInterval: ReturnType<typeof setInterval> | null = null;

const loading = ref(true);
const error = ref('');
const dataSource = ref<any[]>([]);
const gwContainer = ref<HTMLDivElement | null>(null);
let root: ReactDOM.Root | null = null;
const storeRef = ref<any>(null);

const hasData = computed(() => dataSource.value && dataSource.value.length > 0);

const renderGraphicWalker = () => {
  if (!gwContainer.value) return;
  
  if (!root) {
    root = ReactDOM.createRoot(gwContainer.value);
  }
  
  // Create a mutable ref object that GraphicWalker can assign to
  const reactStoreRef = { current: null };
  storeRef.value = reactStoreRef;

  // Ensure data is a plain JS array (not Vue Proxy)
  const plainData = dataSource.value.length > 0 
    ? JSON.parse(JSON.stringify(dataSource.value))
    : [];
  
  // Explicitly construct fields from first row
  const fields = plainData.length > 0 && typeof plainData[0] === 'object'
    ? Object.keys(plainData[0]).map(key => ({
        fid: key,
        name: key,
        semanticType: typeof plainData[0][key] === 'number' ? 'quantitative' : 'nominal',
        analyticType: typeof plainData[0][key] === 'number' ? 'measure' : 'dimension'
      }))
    : [];

  console.log('GraphicWalker props - Data rows:', plainData.length, 'Fields:', fields.length);

  const gwProps: any = {
    data: plainData,
    fields: fields,
    i18nLang: 'zh-CN',
    storeRef: reactStoreRef, // Pass the ref
    toolbar: props.readOnly ? { show: false } : undefined // Hide toolbar in read-only mode if supported
  };

  root.render(
    React.createElement(GraphicWalker, gwProps)
  );
  
  // Attempt to load snapshot if provided
  if (props.snapshot) {
      // Small delay to ensure store is initialized
      setTimeout(() => {
          if (reactStoreRef.current) {
              console.log("Loading snapshot into Graphic Walker...", props.snapshot);
              try {
                  // Try to look for import method
                  // @ts-ignore
                  if (typeof reactStoreRef.current.importVizSpec === 'function') {
                      // @ts-ignore
                      reactStoreRef.current.importVizSpec(props.snapshot);
                  } else {
                      console.warn("importVizSpec method not found on Graphic Walker instance");
                  }
              } catch (e) {
                  console.error("Failed to load snapshot:", e);
              }
          }
      }, 500);
  }

  // 启动 spec 变化检测（非只读模式）
  if (!props.readOnly) {
    startSpecChangeDetection();
  }
};

// 检测 spec 变化的函数
const startSpecChangeDetection = () => {
  // 停止之前的检测
  if (specCheckInterval) {
    clearInterval(specCheckInterval);
  }

  // 每 5 秒检查一次 spec 是否变化
  specCheckInterval = setInterval(async () => {
    try {
      const currentSpec = await getSpec();
      if (currentSpec) {
        const currentSnapshot = JSON.stringify(currentSpec);
        if (currentSnapshot !== lastSpecSnapshot) {
          lastSpecSnapshot = currentSnapshot;
          console.log('[BiDesigner] Spec changed, emitting event...');
          emit('spec-change', currentSpec);
        }
      }
    } catch (e) {
      console.warn('[BiDesigner] Failed to check spec change:', e);
    }
  }, 5000);
};

// Expose method to get current visualization spec
const getSpec = async () => {
  if (storeRef.value && storeRef.value.current) {
    console.log("GWalk Store Ref:", storeRef.value.current);
    try {
      // Try exportVizSpec (returns the spec object)
      if (typeof storeRef.value.current.exportVizSpec === 'function') {
        return await storeRef.value.current.exportVizSpec();
      } 
      // Fallback or other methods if version changed
      else if (typeof storeRef.value.current.exportCode === 'function') {
        return await storeRef.value.current.exportCode();
      }
      else {
        console.warn("No export method found on GWalk store ref");
        return null;
      }
    } catch (e) {
      console.error("Failed to export spec:", e);
      return null;
    }
  }
  return null;
};

defineExpose({
  getSpec
});

const processData = () => {
  loading.value = true;
  error.value = '';
  
  // If initialData is provided, use it directly
  if (props.initialData && props.initialData.length > 0) {
      try {
          // Data Sanitization: Deep clone to remove Proxy and ensure pure JS object
          const cleanData = JSON.parse(JSON.stringify(props.initialData));
          
          // Defensive check: Ensure first row exists and is an object
          if (cleanData.length > 0 && typeof cleanData[0] === 'object') {
              console.log('BiDesigner: Data sanitized and validated.', cleanData.length, 'rows');
              console.log('BiDesigner: First row keys:', Object.keys(cleanData[0]));
              dataSource.value = cleanData;
              loading.value = false;
              
              // Render React component after Vue DOM update
              setTimeout(() => renderGraphicWalker(), 0);
          } else {
              console.warn('BiDesigner: Data is empty or invalid format', cleanData);
              error.value = '数据格式异常';
              loading.value = false;
          }
      } catch (e: any) {
          console.error('BiDesigner: Data sanitization failed', e);
          error.value = '数据处理失败: ' + e.message;
          loading.value = false;
      }
  } else {
      // Data is empty
      console.log('BiDesigner: initialData is empty.');
      dataSource.value = [];
      loading.value = false;
      // Do not render GraphicWalker if no data, show empty state instead
  }
};

const retryLoad = () => {
    // Trigger parent to reload or just re-process
    processData();
};

onMounted(() => {
  processData();
});

onUnmounted(() => {
  // 清理 spec 变化检测
  if (specCheckInterval) {
    clearInterval(specCheckInterval);
    specCheckInterval = null;
  }

  if (root) {
    root.unmount();
    root = null;
  }
});

watch(() => props.initialData, (newData) => {
    if (newData) {
        console.log('BiDesigner received data via watch:', newData.length, 'rows');
        processData();
    }
}, { immediate: true, deep: true });

</script>

<style scoped>
.bi-designer-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden; /* Manage scroll inside GraphicWalker */
}

.loading-state, .error-state {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.graphic-walker-wrapper {
  flex: 1;
  overflow: auto;
  padding: 10px;
}
</style>