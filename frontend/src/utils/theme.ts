import { reactive } from 'vue';
import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context';

// 自定义DeepPartial类型
type DeepPartial<T> = T extends object ? {
  [P in keyof T]?: DeepPartial<T[P]>;
} : T;

// 亮色主题（唯一主题）— 数值对齐 tokens.css / Ant Design 5 默认语义
export const lightTheme: DeepPartial<ThemeConfig> = {
  token: {
    colorPrimary: '#1677ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1677ff',
    colorText: 'rgba(0, 0, 0, 0.88)',
    colorTextSecondary: 'rgba(0, 0, 0, 0.65)',
    colorTextTertiary: 'rgba(0, 0, 0, 0.45)',
    colorBorder: '#d9d9d9',
    colorBorderSecondary: '#f0f0f0',
    colorBgLayout: '#f5f5f5',
    colorBgContainer: '#ffffff',
    borderRadius: 6,
    fontSize: 14,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
};

// 全局组件默认配置
export const componentConfig = {
  Form: {
    size: 'middle',
    validateMessages: {
      required: '${label}是必填项',
      types: {
        email: '请输入有效的邮箱',
        number: '请输入有效的数字',
      },
      pattern: {
        mismatch: '${label}格式不匹配',
      },
    },
  },
  Table: {
    size: 'middle',
    bordered: false,
  },
  Button: {
    size: 'middle',
  },
  Input: {
    size: 'middle',
  },
  Select: {
    size: 'middle',
  },
  DatePicker: {
    size: 'middle',
  },
  Modal: {
    maskClosable: false,
  },
  Avatar: {
    size: 36,
    shape: 'circle',
    gap: 4,
  },
};

// 当前主题状态（固定亮色）
export const currentTheme = reactive({
  theme: lightTheme,
  components: componentConfig,
  isDark: false,
});

// 初始化主题（仅亮色）
export function initTheme(): void {
  document.documentElement.setAttribute('data-theme', 'light');
  localStorage.removeItem('theme'); // 清除旧的主题设置
}

// 保留空函数以兼容可能的调用
export function toggleTheme(): void {
  // 不再支持主题切换，保持亮色
  console.log('暗色主题已移除，仅支持亮色模式');
}
