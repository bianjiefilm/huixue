import type { App } from 'vue';
import {
  Layout,
  Menu,
  Button,
  Row,
  Col,
  Card,
  Tag,
  Avatar,
  Input,
  Breadcrumb,
  Spin,
  Result,
  Empty,
  Space,
  Radio,
  Checkbox,
  Dropdown,
  Tabs,
  Form,
  ConfigProvider,
  Modal,
  List,
  Collapse,
  DatePicker,
  InputNumber,
  CheckboxGroup,
  Table,
  Select,
  Switch,
  TimePicker,
  Badge,
  Alert,
  Drawer,
  Pagination,
  Popconfirm,
  Tooltip,
  Divider,
  Progress,
  Typography,
  Tree,
  Statistic
} from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import { defineAsyncComponent } from 'vue';

// 从Ant Design Icons导入
import {
  UserOutlined,
  BookOutlined,
  RightOutlined,
  CodeOutlined,
  LikeOutlined,
  EyeOutlined,
  SearchOutlined,
  ReloadOutlined,
  StarOutlined,
  GiftOutlined,
  FileOutlined,
  CodeOutlined as CodeSandboxOutlined,
  PieChartOutlined,
  DesktopOutlined,
  TeamOutlined,
  VideoCameraOutlined,
  UploadOutlined,
  AppstoreOutlined,
  ProfileOutlined,
  FolderOutlined,
  FormOutlined,
  DownloadOutlined
} from '@ant-design/icons-vue';

// 组件映射，将Arco组件名转换为Ant Design组件名
const componentMapping = {
  // 布局组件
  'a-layout': Layout,
  'a-layout-sider': Layout.Sider,
  'a-layout-header': Layout.Header,
  'a-layout-content': Layout.Content,
  'a-layout-footer': Layout.Footer,
  
  // 导航组件
  'a-menu': Menu,
  'a-menu-item': Menu.Item,
  'a-sub-menu': Menu.SubMenu,
  'a-breadcrumb': Breadcrumb,
  'a-breadcrumb-item': Breadcrumb.Item,
  
  // 数据展示组件
  'a-card': Card,
  'a-avatar': Avatar,
  'a-tag': Tag,
  'a-spin': Spin,
  'a-empty': Empty,
  'a-result': Result,
  'a-space': Space,
  'a-list': List,
  'a-list-item': List.Item,
  'a-list-item-meta': List.Item.Meta,
  'a-collapse': Collapse,
  'a-collapse-panel': Collapse.Panel,
  
  // 表单组件
  'a-input': Input,
  'a-input-search': Input.Search,
  'a-input-number': InputNumber,
  'a-radio': Radio,
  'a-radio-group': Radio.Group,
  'a-radio-button': Radio.Button,
  'a-checkbox': Checkbox,
  'a-checkbox-group': CheckboxGroup,
  'a-form': Form,
  'a-form-item': Form.Item,
  'a-date-picker': DatePicker,
  
  // 其他组件
  'a-button': Button,
  'a-dropdown': Dropdown,
  'a-tabs': Tabs,
  'a-tab-pane': Tabs.TabPane,
  'a-config-provider': ConfigProvider,
  'a-modal': Modal,
  
  // 布局组件
  'a-row': Row,
  'a-col': Col,
  
  // 新增组件
  'a-table': Table,
  'a-select': Select,
  'a-select-option': Select.Option,
  'a-switch': Switch,
  'a-time-picker': TimePicker,
  'a-badge': Badge,
  'a-alert': Alert,
  'a-drawer': Drawer,
  'a-pagination': Pagination,
  'a-popconfirm': Popconfirm,
  'a-tooltip': Tooltip,
  'a-divider': Divider,
  'a-progress': Progress,
  'a-typography': Typography,
  'a-typography-paragraph': Typography.Paragraph,
  'a-typography-title': Typography.Title,
  'a-typography-text': Typography.Text,
  'a-tree': Tree,
  'a-statistic': Statistic
};

// 图标组件映射
const iconMapping = {
  'icon-user': UserOutlined,
  'icon-book': BookOutlined,
  'icon-right': RightOutlined,
  'icon-code-block': CodeOutlined,
  'icon-code': CodeOutlined,
  'icon-code-square': CodeSandboxOutlined,
  'icon-thumb-up': LikeOutlined,
  'icon-eye': EyeOutlined,
  'icon-search': SearchOutlined,
  'icon-refresh': ReloadOutlined,
  'icon-star': StarOutlined,
  'icon-gift': GiftOutlined,
  'icon-file': FileOutlined,
  'app-store-outlined': AppstoreOutlined,
  'profile-outlined': ProfileOutlined,
  'folder-outlined': FolderOutlined,
  'form-outlined': FormOutlined,
  'download-outlined': DownloadOutlined
};

export default {
  install: (app: App) => {
    // 全局注册组件
    app.use(Button);
    app.use(Layout);
    app.use(Menu);
    app.use(ConfigProvider);
    app.use(Input);
    app.use(Table);
    app.use(Tabs);
    app.use(Card);
    app.use(Form);
    app.use(Select);
    app.use(Checkbox);
    app.use(Radio);
    app.use(Switch);
    app.use(DatePicker);
    app.use(TimePicker);
    app.use(Avatar);
    app.use(Badge);
    app.use(Alert);
    app.use(Drawer);
    app.use(Modal);
    app.use(Dropdown);
    app.use(Pagination);
    app.use(Popconfirm);
    app.use(Tooltip);
    app.use(Spin);
    app.use(Breadcrumb);
    app.use(Divider);
    app.use(Progress);
    app.use(Tag);
    app.use(List);
    app.use(Collapse);
    app.use(Result);
    app.use(Space);
    app.use(Typography);
    app.use(Tree);
    app.use(Statistic);
    
    // 注册布局相关组件
    app.component('a-layout', Layout);
    app.component('a-layout-sider', Layout.Sider);
    app.component('a-layout-header', Layout.Header);
    app.component('a-layout-content', Layout.Content);
    app.component('a-layout-footer', Layout.Footer);
    
    // 注册导航组件
    app.component('a-menu', Menu);
    app.component('a-menu-item', Menu.Item);
    app.component('a-sub-menu', Menu.SubMenu);
    app.component('a-breadcrumb', Breadcrumb);
    app.component('a-breadcrumb-item', Breadcrumb.Item);
    
    // 注册数据展示组件
    app.component('a-card', Card);
    app.component('a-avatar', Avatar);
    app.component('a-tag', Tag);
    app.component('a-spin', Spin);
    app.component('a-empty', Empty);
    app.component('a-result', Result);
    app.component('a-space', Space);
    app.component('a-list', List);
    app.component('a-list-item', List.Item);
    app.component('a-list-item-meta', List.Item.Meta);
    app.component('a-collapse', Collapse);
    app.component('a-collapse-panel', Collapse.Panel);
    app.component('a-statistic', Statistic);
    
    // 注册表单组件
    app.component('a-input', Input);
    app.component('a-input-search', Input.Search);
    app.component('a-input-number', InputNumber);
    app.component('a-radio', Radio);
    app.component('a-radio-group', Radio.Group);
    app.component('a-radio-button', Radio.Button);
    app.component('a-checkbox', Checkbox);
    app.component('a-checkbox-group', CheckboxGroup);
    app.component('a-form', Form);
    app.component('a-form-item', Form.Item);
    app.component('a-date-picker', DatePicker);
    
    // 注册其他组件
    app.component('a-button', Button);
    app.component('a-dropdown', Dropdown);
    app.component('a-tabs', Tabs);
    app.component('a-tab-pane', Tabs.TabPane);
    app.component('a-config-provider', ConfigProvider);
    app.component('a-modal', Modal);
    
    // 注册布局组件
    app.component('a-row', Row);
    app.component('a-col', Col);
    
    // 注册新增组件
    app.component('a-table', Table);
    app.component('a-select', Select);
    app.component('a-select-option', Select.Option);
    app.component('a-switch', Switch);
    app.component('a-time-picker', TimePicker);
    app.component('a-badge', Badge);
    app.component('a-alert', Alert);
    app.component('a-drawer', Drawer);
    app.component('a-pagination', Pagination);
    app.component('a-popconfirm', Popconfirm);
    app.component('a-tooltip', Tooltip);
    app.component('a-divider', Divider);
    app.component('a-progress', Progress);
    app.component('a-typography', Typography);
    app.component('a-typography-paragraph', Typography.Paragraph);
    app.component('a-typography-title', Typography.Title);
    app.component('a-typography-text', Typography.Text);
    app.component('a-tree', Tree);
    
    // 注册图标组件
    Object.entries(iconMapping).forEach(([key, component]) => {
      app.component(key, component);
    });
    
    // 全局注册 DAGBoard 组件别名
    app.component('DAGBoard', defineAsyncComponent(() => 
      import('../components/ml/DAGBoard.vue')
    ));
    
    // 全局注册 NodeBus 组件别名
    app.component('node-bus', defineAsyncComponent(() =>
      import('../components/ml/NodeBus.vue')
    ));
  }
}; 