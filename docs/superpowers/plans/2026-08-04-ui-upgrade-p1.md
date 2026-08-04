# 慧学前端 UI 升级 Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 `--hx-*` 设计 token、布局原语与可验证清债，并将教学主路径 + AI 面打磨到桌面端成品级（轻度现代化）。

**Architecture:** Token 真源 `tokens.css` 与 `theme.ts` 对齐；AppShell（BasicLayout）+ PageShell/PageHeaderBar 等原语统一页面骨架；按 Slice 0→5 纵向改造核心页；Arco/死依赖等债项按 D1–D8 清单清零。规格见 `docs/superpowers/specs/2026-08-04-ui-upgrade-design.md`。

**Tech Stack:** Vue 3、Ant Design Vue 4、TypeScript、Vite、CSS 变量；仓库 https://github.com/bianjiefilm/huixue

## Global Constraints

- 主色：`#1677ff`（替代散落 `#1890ff` 时优先用 token）
- 间距阶梯仅：`0/4/8/12/16/24/32/48`（`--hx-space-0` … `--hx-space-7`）
- 圆角：sm/md/lg = `6/10/14`；AntD `borderRadius: 6`
- 设备：桌面 1280–1920 优先；不追求手机精品
- 单一 UI 库：Ant Design Vue；不引入 Tailwind 第二套间距
- `--copilot-*` P1 仅作 alias 指向 `--hx-*` 同值；新代码只用 `--hx-*`
- 不改业务 API/导航信息架构；工作台只做 L-Shell（高度与 gap），不重做 Monaco/BI 画布
- 验收证据：本地 `npm run build` / 实点 / grep；禁止无证据宣称完成
- 每 Task 结束单独 commit；commit message 含 scope

---

## File Structure（新建 / 修改职责）

| 路径 | 职责 |
|------|------|
| `frontend/src/assets/styles/tokens.css` | **新建** L0 token 真源 + z-index 变量 + `--copilot-*` alias |
| `frontend/src/assets/styles/theme-light.css` | 瘦身：依赖 tokens，去掉重复色板定义 |
| `frontend/src/utils/theme.ts` | AntD ThemeConfig 与 token 数值对齐 |
| `frontend/src/main.ts` | 在 theme-light 前 import tokens.css |
| `frontend/src/App.vue` | 删除 Arco `!important` 堆（D1） |
| `frontend/src/assets/responsive.css` | 删除/改写 `.arco-*` 规则（D1）；保留有用断点时改中性选择器 |
| `frontend/src/assets/antd-theme.css` | 仅在仍被引用时收敛；当前主入口未引则不动或删除死文件引用 |
| `frontend/src/components/layout/BasicLayout.vue` | AppShell：token 化样式；`meta.hideFooter` / workspace 高度（D6/D8） |
| `frontend/src/components/common/PageShell.vue` | **新建** 页面容器 |
| `frontend/src/components/common/PageHeaderBar.vue` | **新建** 页内标题 |
| `frontend/src/components/common/ContentCard.vue` | **新建** 内容卡片壳 |
| `frontend/src/components/common/EmptyStateBlock.vue` | **新建** 空状态 |
| `frontend/src/components/common/Stack.vue` | **新建** 间距工具 |
| `frontend/src/components/common/PageContainer.vue` | 内部转调 PageShell |
| `frontend/src/components/ui-system/*` | `--copilot-*` → `--hx-*`；减弱默认 glow |
| `frontend/src/router/index.ts` | 工作台路由 `meta: { hideFooter: true }`；清理 element-plus 注释（D2） |
| `frontend/src/views/auth/Login.vue` | Slice 1 |
| `frontend/src/views/classroom/ClassroomListView.vue` | Slice 2 |
| `frontend/src/views/classroom/detail.vue` | Slice 2 |
| `frontend/src/views/classroom/course-detail.vue` | Slice 2 |
| `frontend/src/views/classroom/TrainingDetailInClassroom.vue` | Slice 3 |
| `frontend/src/views/classroom/TrainingWorkspace.vue` | Slice 3 |
| `frontend/src/views/classroom/BiTrainingWorkspace.vue` | Slice 3 |
| `frontend/src/views/classroom/homework-detail.vue` | Slice 3 |
| `frontend/src/views/classroom/submission/SubmissionDetail.vue` | Slice 3 |
| `frontend/src/views/course/index.vue` | Slice 4 |
| `frontend/src/views/course/practice/my-practices.vue` | Slice 4 |
| `frontend/src/views/classroom/TrainingHomework.vue` | Slice 4 |
| `frontend/src/views/classroom/TrainingGrades.vue` | Slice 4 |
| `frontend/src/views/teacher-ai/*.vue` | Slice 5 |
| `frontend/src/views/student/AICopilotDashboard.vue` | Slice 5 |
| `frontend/src/views/student-ai/HintPanel.vue` | Slice 5 |
| `frontend/src/components/ai-copilot/*` | Slice 5 token/z-index |
| `frontend/scripts/check-hx-tokens.mjs` | **新建** token 存在性校验脚本 |
| `frontend/package.json` | 可选：移除 element-plus 依赖（D2 确认无引用后） |

---

### Task 1: Design Tokens + AntD Theme 对齐

**Files:**
- Create: `frontend/src/assets/styles/tokens.css`
- Create: `frontend/scripts/check-hx-tokens.mjs`
- Modify: `frontend/src/utils/theme.ts`
- Modify: `frontend/src/main.ts`
- Modify: `frontend/src/assets/styles/theme-light.css`

**Interfaces:**
- Consumes: 无
- Produces: CSS 变量 `--hx-space-*`、`--hx-color-*`、`--hx-radius-*`、`--hx-shadow-*`、`--hx-font-*`、`--hx-z-*`；`--copilot-*` alias；`lightTheme.token` 与上表数值一致

- [ ] **Step 1: 写 token 校验脚本（先失败）**

创建 `frontend/scripts/check-hx-tokens.mjs`：

```js
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const tokensPath = path.join(__dirname, '../src/assets/styles/tokens.css')
const required = [
  '--hx-space-1', '--hx-space-2', '--hx-space-3', '--hx-space-4',
  '--hx-space-5', '--hx-space-6', '--hx-space-7',
  '--hx-color-primary', '--hx-color-bg-layout', '--hx-color-bg-container',
  '--hx-color-text-primary', '--hx-color-text-secondary',
  '--hx-radius-sm', '--hx-radius-md', '--hx-radius-lg',
  '--hx-shadow-sm', '--hx-shadow-md',
  '--hx-z-header', '--hx-z-dropdown', '--hx-z-drawer', '--hx-z-modal', '--hx-z-ai-float',
  '--copilot-spacing-sm', // alias 保活
]

if (!fs.existsSync(tokensPath)) {
  console.error('FAIL: tokens.css missing at', tokensPath)
  process.exit(1)
}
const css = fs.readFileSync(tokensPath, 'utf8')
const missing = required.filter((k) => !css.includes(k))
if (missing.length) {
  console.error('FAIL: missing tokens:', missing.join(', '))
  process.exit(1)
}
if (!css.includes('#1677ff')) {
  console.error('FAIL: primary #1677ff not found')
  process.exit(1)
}
console.log('PASS: hx tokens present')
```

- [ ] **Step 2: 运行校验，确认失败**

Run:

```bash
cd frontend && node scripts/check-hx-tokens.mjs
```

Expected: `FAIL: tokens.css missing`（或 missing tokens）

- [ ] **Step 3: 创建 `tokens.css`**

写入完整 `:root`（数值必须与 spec 一致）：

```css
/* frontend/src/assets/styles/tokens.css — 慧学 Design Token 真源 */
:root {
  /* Spacing (4px base) */
  --hx-space-0: 0;
  --hx-space-1: 4px;
  --hx-space-2: 8px;
  --hx-space-3: 12px;
  --hx-space-4: 16px;
  --hx-space-5: 24px;
  --hx-space-6: 32px;
  --hx-space-7: 48px;

  /* Color */
  --hx-color-primary: #1677ff;
  --hx-color-primary-hover: #4096ff;
  --hx-color-primary-active: #0958d9;
  --hx-color-success: #52c41a;
  --hx-color-warning: #faad14;
  --hx-color-error: #ff4d4f;
  --hx-color-info: #1677ff;

  --hx-color-text-primary: rgba(0, 0, 0, 0.88);
  --hx-color-text-secondary: rgba(0, 0, 0, 0.65);
  --hx-color-text-tertiary: rgba(0, 0, 0, 0.45);
  --hx-color-text-disabled: rgba(0, 0, 0, 0.25);

  --hx-color-border: #d9d9d9;
  --hx-color-border-muted: #f0f0f0;
  --hx-color-bg-layout: #f5f5f5;
  --hx-color-bg-container: #ffffff;
  --hx-color-bg-elevated: #ffffff;
  --hx-color-bg-hover: rgba(0, 0, 0, 0.04);

  --hx-color-accent-purple: #722ed1;
  --hx-color-accent-purple-dim: rgba(114, 46, 209, 0.1);
  --hx-color-primary-dim: rgba(22, 119, 255, 0.12);

  /* Radius */
  --hx-radius-sm: 6px;
  --hx-radius-md: 10px;
  --hx-radius-lg: 14px;
  --hx-radius-full: 9999px;

  /* Shadow */
  --hx-shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --hx-shadow-md: 0 4px 12px rgba(0, 0, 0, 0.06);
  --hx-shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.08);

  /* Typography */
  --hx-font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --hx-font-mono: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  --hx-font-size-xs: 12px;
  --hx-font-size-sm: 13px;
  --hx-font-size-base: 14px;
  --hx-font-size-md: 16px;
  --hx-font-size-lg: 20px;
  --hx-font-size-xl: 24px;
  --hx-font-size-2xl: 32px;

  /* Motion */
  --hx-transition-fast: 150ms ease;
  --hx-transition-normal: 250ms ease;

  /* Layout chrome */
  --hx-header-height: 64px;
  --hx-footer-height: 64px;

  /* z-index scale (D7) */
  --hx-z-header: 100;
  --hx-z-dropdown: 1050;
  --hx-z-drawer: 1000;
  --hx-z-modal: 1000;
  --hx-z-ai-float: 1100;

  /* ---------- copilot aliases (P1 compat) ---------- */
  --copilot-bg-primary: var(--hx-color-bg-layout);
  --copilot-bg-secondary: var(--hx-color-bg-container);
  --copilot-bg-tertiary: #fafafa;
  --copilot-bg-elevated: var(--hx-color-bg-elevated);
  --copilot-bg-hover: var(--hx-color-bg-hover);
  --copilot-text-primary: var(--hx-color-text-primary);
  --copilot-text-secondary: var(--hx-color-text-secondary);
  --copilot-text-tertiary: var(--hx-color-text-tertiary);
  --copilot-text-muted: var(--hx-color-text-disabled);
  --copilot-border-default: var(--hx-color-border);
  --copilot-border-muted: var(--hx-color-border-muted);
  --copilot-border-accent: var(--hx-color-primary);
  --copilot-border-highlight: rgba(22, 119, 255, 0.5);
  --copilot-brand-primary: var(--hx-color-primary);
  --copilot-brand-hover: var(--hx-color-primary-hover);
  --copilot-brand-active: var(--hx-color-primary-active);
  --copilot-brand-primary-alpha-20: var(--hx-color-primary-dim);
  --copilot-accent-cyan: var(--hx-color-primary);
  --copilot-accent-cyan-dim: var(--hx-color-primary-dim);
  --copilot-accent-green: var(--hx-color-success);
  --copilot-accent-green-dim: rgba(82, 196, 26, 0.1);
  --copilot-accent-yellow: var(--hx-color-warning);
  --copilot-accent-yellow-dim: rgba(250, 173, 20, 0.1);
  --copilot-accent-pink: #eb2f96;
  --copilot-accent-pink-dim: rgba(235, 47, 150, 0.1);
  --copilot-accent-purple: var(--hx-color-accent-purple);
  --copilot-accent-purple-dim: var(--hx-color-accent-purple-dim);
  --copilot-semantic-success: var(--hx-color-success);
  --copilot-semantic-warning: var(--hx-color-warning);
  --copilot-semantic-error: var(--hx-color-error);
  --copilot-semantic-info: var(--hx-color-info);
  --copilot-sidebar-bg: var(--hx-color-bg-container);
  --copilot-sidebar-border: var(--hx-color-border-muted);
  --copilot-sidebar-width-collapsed: 64px;
  --copilot-sidebar-width-expanded: 240px;
  --copilot-sidebar-padding: var(--hx-space-3);
  --copilot-font-size-xs: var(--hx-font-size-xs);
  --copilot-font-size-sm: var(--hx-font-size-sm);
  --copilot-font-size-base: var(--hx-font-size-base);
  --copilot-font-size-lg: var(--hx-font-size-lg);
  --copilot-font-size-xl: var(--hx-font-size-xl);
  --copilot-font-size-2xl: var(--hx-font-size-2xl);
  --copilot-font-family: var(--hx-font-family);
  --copilot-font-mono: var(--hx-font-mono);
  --copilot-spacing-xs: var(--hx-space-1);
  --copilot-spacing-sm: var(--hx-space-2);
  --copilot-spacing-md: var(--hx-space-3);
  --copilot-spacing-lg: var(--hx-space-4);
  --copilot-spacing-xl: var(--hx-space-5);
  --copilot-radius-sm: var(--hx-radius-sm);
  --copilot-radius-md: var(--hx-radius-md);
  --copilot-radius-lg: var(--hx-radius-lg);
  --copilot-radius-full: var(--hx-radius-full);
  --copilot-shadow-sm: var(--hx-shadow-sm);
  --copilot-shadow-md: var(--hx-shadow-md);
  --copilot-shadow-lg: var(--hx-shadow-lg);
  --copilot-shadow-glow-cyan: 0 0 20px rgba(22, 119, 255, 0.15);
  --copilot-gradient-primary: linear-gradient(135deg, #1677ff 0%, #722ed1 100%);
  --copilot-gradient-card: linear-gradient(135deg, #ffffff 0%, #fafafa 100%);
  --copilot-gradient-progress: linear-gradient(90deg, #1677ff 0%, #52c41a 100%);
  --copilot-transition-fast: var(--hx-transition-fast);
  --copilot-transition-normal: var(--hx-transition-normal);
  --copilot-breakpoint-mobile: 768px;
  --copilot-breakpoint-tablet: 1024px;
  --copilot-breakpoint-desktop: 1280px;
}
```

- [ ] **Step 4: 更新 `theme.ts`**

将 `lightTheme.token` 改为：

```ts
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
```

`componentConfig` 保持 middle size；不必改逻辑。

- [ ] **Step 5: `main.ts` 先加载 tokens**

在 theme-light 之前：

```ts
import './assets/styles/tokens.css'
import './assets/styles/theme-light.css'
```

- [ ] **Step 6: 瘦身 `theme-light.css`**

删除文件顶部重复的整套 `--copilot-*` 定义（已由 tokens alias 提供）。保留全局布局覆盖，但改为变量：

```css
html, body {
  background-color: var(--hx-color-bg-layout);
  font-family: var(--hx-font-family);
  color: var(--hx-color-text-primary);
}

#app {
  background-color: var(--hx-color-bg-layout);
  min-height: 100vh;
}

.ant-layout {
  background-color: var(--hx-color-bg-layout);
}

.ant-layout-content {
  background-color: var(--hx-color-bg-layout);
}

.ant-layout-sider-trigger {
  background: var(--hx-color-bg-layout) !important;
  color: var(--hx-color-text-secondary) !important;
  border-top: 1px solid var(--hx-color-border-muted) !important;
}

.ant-layout-sider-trigger:hover {
  background: var(--hx-color-bg-hover) !important;
  color: var(--hx-color-text-primary) !important;
}

/* 兼容旧 copilot-theme 类 */
.copilot-theme {
  background-color: var(--hx-color-bg-layout);
  color: var(--hx-color-text-primary);
}
```

去掉会把所有 `[class*="copilot"]` 背景强制 `inherit` 的危险规则（易弄坏 AI 卡片）；若必须保留，加注释并仅在回归失败时恢复。

- [ ] **Step 7: 校验通过 + build**

```bash
cd frontend && node scripts/check-hx-tokens.mjs
cd frontend && npm run build-only
```

Expected: `PASS: hx tokens present`；build 成功（允许既有无关 warning）。

- [ ] **Step 8: Commit**

```bash
git add frontend/src/assets/styles/tokens.css \
  frontend/src/assets/styles/theme-light.css \
  frontend/src/utils/theme.ts \
  frontend/src/main.ts \
  frontend/scripts/check-hx-tokens.mjs
git commit -m "feat(ui): add hx design tokens and align Ant Design theme"
```

---

### Task 2: 清债 D1/D4/D5 + AppShell token 化（Slice 0 壳）

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/assets/responsive.css`
- Modify: `frontend/src/components/layout/BasicLayout.vue`
- Modify: `frontend/src/router/index.ts`（工作台 meta）
- Modify: `frontend/src/assets/main.css`（若仍被引用则清空 media；主入口未用可只删空规则）

**Interfaces:**
- Consumes: `--hx-*` tokens
- Produces: 无 Arco 业务选择器；BasicLayout 支持 `route.meta.hideFooter`；content 背景用 token

- [ ] **Step 1: 基线 grep（记录债）**

```bash
cd frontend && grep -rn '\.arco-' src --include='*.vue' --include='*.css' --include='*.ts' | grep -v node_modules | wc -l
```

记下数字；本 Task 结束后应显著下降（目标业务样式 **0** 条 `.arco-` 规则，或仅注释）。

- [ ] **Step 2: 清理 `App.vue` 全局 Arco 补丁**

删除 `<style>` 中所有 `.arco-tag`、`.arco-row`、`.arco-col`、`.arco-radio-*` 等规则块（约 57–150 行一带）。保留：

```css
html, body {
  margin: 0;
  padding: 0;
  font-family: var(--hx-font-family);
  text-orientation: mixed !important;
  writing-mode: horizontal-tb !important;
  direction: ltr !important;
}

#app {
  width: 100%;
  height: 100%;
  overflow-x: hidden;
}

a {
  text-decoration: none;
  color: inherit;
}

.course-card {
  height: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  width: 100% !important;
}
```

（`course-card` 若后续进 ContentCard 可再删。）

- [ ] **Step 3: 清理 `responsive.css`**

1. 所有 `.arco-*` 选择器：删除，或改为实际仍使用的中性 class（先 `grep -n arco` 该文件）。
2. 若 `views/course/micro/index.vue` 仍依赖 Arco class 名：在 **本 Task 或紧随的 micro 小修** 中把模板改为 `a-row`/`a-col` 或普通 `div` + flex；P1 不深打磨 micro，只保证清债后不白屏。

- [ ] **Step 4: BasicLayout 样式 token 化**

将 scoped 样式中硬编码改为变量，关键片段：

```css
.global-layout {
  min-height: 100vh;
  background: var(--hx-color-bg-layout);
}

.page-header {
  position: sticky;
  top: 0;
  z-index: var(--hx-z-header);
  height: var(--hx-header-height);
  line-height: var(--hx-header-height);
  padding: 0 var(--hx-space-5);
  background: var(--hx-color-bg-container);
  border-bottom: 1px solid var(--hx-color-border-muted);
}

.logo-link:hover,
.top-nav-item:hover,
.top-nav-item.active {
  color: var(--hx-color-primary);
}

.top-nav-item.active {
  border-bottom-color: var(--hx-color-primary);
}

.top-nav-item {
  padding: 0 var(--hx-space-4); /* 16，替代 20 */
  height: var(--hx-header-height);
  gap: var(--hx-space-2);
}

.page-content {
  min-height: calc(100vh - var(--hx-header-height) - var(--hx-footer-height));
  padding: 0;
  background-color: var(--hx-color-bg-layout);
}

.page-footer {
  text-align: center;
  padding: var(--hx-space-5) 0;
  background: var(--hx-color-bg-layout);
  color: var(--hx-color-text-tertiary);
}
```

模板：footer 按 meta 隐藏：

```vue
<a-layout-footer v-if="!hideFooter" class="page-footer">
  ...
  <p>© {{ new Date().getFullYear() }} 慧学. All Rights Reserved.</p>
</a-layout-footer>
```

script：

```ts
const hideFooter = computed(() => Boolean(route.meta.hideFooter))
```

当 `hideFooter` 时：

```css
.global-layout--workspace .page-content {
  min-height: calc(100vh - var(--hx-header-height));
}
```

`:class` 绑定 `global-layout--workspace` 当 `hideFooter`。

- [ ] **Step 5: 路由 meta**

在 `router/index.ts` 为下列 route 增加 `meta: { hideFooter: true }`（合并已有 meta）：

- `TrainingWorkspace`
- `BiTrainingWorkspace`
- 以及已有全屏 BI/Jupyter 类若被 footer 挤压，同样加上

示例：

```ts
{
  path: 'classroom/:classroomId/training/:trainingId/workspace',
  name: 'TrainingWorkspace',
  component: () => import('../views/classroom/TrainingWorkspace.vue'),
  meta: { hideFooter: true },
},
```

- [ ] **Step 6: 验证**

```bash
cd frontend && grep -rn '\.arco-' src --include='*.vue' --include='*.css' | grep -v node_modules || true
cd frontend && npm run build-only
```

Expected: 无残留业务 `.arco-` 规则（micro 已改）；build 通过。

- [ ] **Step 7: Commit**

```bash
git add frontend/src/App.vue frontend/src/assets/responsive.css \
  frontend/src/components/layout/BasicLayout.vue frontend/src/router/index.ts \
  frontend/src/assets/main.css frontend/src/views/course/micro/index.vue
git commit -m "refactor(ui): strip Arco legacy CSS and token-ize AppShell"
```

---

### Task 3: 布局原语 PageShell / PageHeaderBar / ContentCard / EmptyStateBlock / Stack

**Files:**
- Create: `frontend/src/components/common/PageShell.vue`
- Create: `frontend/src/components/common/PageHeaderBar.vue`
- Create: `frontend/src/components/common/ContentCard.vue`
- Create: `frontend/src/components/common/EmptyStateBlock.vue`
- Create: `frontend/src/components/common/Stack.vue`
- Modify: `frontend/src/components/common/PageContainer.vue`
- Modify: `frontend/src/components/ui-system/DarkCard.vue`（变量与 glow 默认）
- Modify: `frontend/src/components/ui-system/ProgressBar.vue`（若仍用 copilot spacing，可改 hx 或依赖 alias）

**Interfaces:**
- Consumes: `--hx-space-*`、`--hx-radius-*`、`--hx-color-*`、`--hx-shadow-*`
- Produces:
  - `PageShell` props: `maxWidth?: 'default' | 'wide' | 'fluid'`（默认 `default`）
  - `PageHeaderBar` props: `title: string`, `subtitle?: string`, `showBack?: boolean`；slots: `actions`, `extra`, `default`（可选副区）
  - `ContentCard` props: `size?: 'sm' | 'md'`, `hoverable?: boolean`
  - `EmptyStateBlock` props: `description: string`, `title?: string`；slot `action`
  - `Stack` props: `gap?: 1|2|3|4|5|6|7`（默认 4）, `direction?: 'vertical' | 'horizontal'`, `align?: string`

- [ ] **Step 1: 实现 `PageShell.vue`**

```vue
<template>
  <div class="hx-page-shell" :class="`hx-page-shell--${maxWidth}`">
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ maxWidth?: 'default' | 'wide' | 'fluid' }>(),
  { maxWidth: 'default' }
)
</script>

<style scoped>
.hx-page-shell {
  width: 100%;
  margin: 0 auto;
  padding: var(--hx-space-5);
  box-sizing: border-box;
}
.hx-page-shell--default {
  max-width: 1200px;
}
.hx-page-shell--wide {
  max-width: 1440px;
}
.hx-page-shell--fluid {
  max-width: none;
}
@media (max-width: 768px) {
  .hx-page-shell {
    padding: var(--hx-space-3);
  }
}
</style>
```

- [ ] **Step 2: 实现 `PageHeaderBar.vue`**

```vue
<template>
  <div class="hx-page-header">
    <div class="hx-page-header__row">
      <div class="hx-page-header__titles">
        <a-button v-if="showBack" type="text" class="hx-page-header__back" @click="onBack">
          ← 返回
        </a-button>
        <div>
          <h1 class="hx-page-header__title">{{ title }}</h1>
          <p v-if="subtitle" class="hx-page-header__subtitle">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.actions" class="hx-page-header__actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="$slots.extra" class="hx-page-header__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const props = withDefaults(
  defineProps<{ title: string; subtitle?: string; showBack?: boolean }>(),
  { showBack: false }
)
const router = useRouter()
const onBack = () => router.back()
</script>

<style scoped>
.hx-page-header {
  margin-bottom: var(--hx-space-5);
}
.hx-page-header__row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--hx-space-4);
  flex-wrap: wrap;
}
.hx-page-header__titles {
  display: flex;
  align-items: flex-start;
  gap: var(--hx-space-2);
  min-width: 0;
}
.hx-page-header__title {
  margin: 0;
  font-size: var(--hx-font-size-lg);
  font-weight: 600;
  color: var(--hx-color-text-primary);
  line-height: 1.3;
}
.hx-page-header__subtitle {
  margin: var(--hx-space-1) 0 0;
  font-size: var(--hx-font-size-base);
  color: var(--hx-color-text-secondary);
}
.hx-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--hx-space-2);
  align-items: center;
}
.hx-page-header__extra {
  margin-top: var(--hx-space-4);
}
</style>
```

- [ ] **Step 3: 实现 `ContentCard.vue` / `EmptyStateBlock.vue` / `Stack.vue`**

`ContentCard.vue`：

```vue
<template>
  <div
    class="hx-content-card"
    :class="[
      `hx-content-card--${size}`,
      { 'hx-content-card--hoverable': hoverable },
    ]"
  >
    <div v-if="$slots.header" class="hx-content-card__header">
      <slot name="header" />
    </div>
    <div class="hx-content-card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="hx-content-card__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ size?: 'sm' | 'md'; hoverable?: boolean }>(),
  { size: 'md', hoverable: false }
)
</script>

<style scoped>
.hx-content-card {
  background: var(--hx-color-bg-container);
  border: 1px solid var(--hx-color-border-muted);
  border-radius: var(--hx-radius-md);
  box-shadow: var(--hx-shadow-sm);
  overflow: hidden;
}
.hx-content-card--md .hx-content-card__body,
.hx-content-card--md .hx-content-card__header,
.hx-content-card--md .hx-content-card__footer {
  padding: var(--hx-space-5);
}
.hx-content-card--sm .hx-content-card__body,
.hx-content-card--sm .hx-content-card__header,
.hx-content-card--sm .hx-content-card__footer {
  padding: var(--hx-space-4);
}
.hx-content-card__header {
  border-bottom: 1px solid var(--hx-color-border-muted);
}
.hx-content-card__footer {
  border-top: 1px solid var(--hx-color-border-muted);
}
.hx-content-card--hoverable {
  transition: box-shadow var(--hx-transition-normal), transform var(--hx-transition-fast);
}
.hx-content-card--hoverable:hover {
  box-shadow: var(--hx-shadow-md);
  transform: translateY(-1px);
}
</style>
```

`EmptyStateBlock.vue`：

```vue
<template>
  <div class="hx-empty">
    <a-empty :description="description">
      <template v-if="title" #image>
        <span class="hx-empty__title">{{ title }}</span>
      </template>
      <div v-if="$slots.action" class="hx-empty__action">
        <slot name="action" />
      </div>
    </a-empty>
  </div>
</template>

<script setup lang="ts">
defineProps<{ description: string; title?: string }>()
</script>

<style scoped>
.hx-empty {
  padding: var(--hx-space-7) var(--hx-space-5);
}
.hx-empty__title {
  font-size: var(--hx-font-size-md);
  color: var(--hx-color-text-secondary);
}
.hx-empty__action {
  margin-top: var(--hx-space-4);
}
</style>
```

`Stack.vue`：

```vue
<template>
  <div
    class="hx-stack"
    :class="`hx-stack--${direction}`"
    :style="{ gap: `var(--hx-space-${gap})`, alignItems: align }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    gap?: 1 | 2 | 3 | 4 | 5 | 6 | 7
    direction?: 'vertical' | 'horizontal'
    align?: string
  }>(),
  { gap: 4, direction: 'vertical', align: 'stretch' }
)
</script>

<style scoped>
.hx-stack {
  display: flex;
}
.hx-stack--vertical {
  flex-direction: column;
}
.hx-stack--horizontal {
  flex-direction: row;
  flex-wrap: wrap;
}
</style>
```

- [ ] **Step 4: `PageContainer.vue` 兼容转调**

```vue
<template>
  <PageShell max-width="default">
    <slot />
  </PageShell>
</template>

<script setup lang="ts">
import PageShell from './PageShell.vue'
</script>
```

- [ ] **Step 5: DarkCard 减弱 glow 默认、优先 hx（alias 已够用则可只改 hover 硬编码青光）**

`DarkCard.vue` 中：

```css
.dark-card--glow:hover {
  box-shadow: var(--copilot-shadow-glow-cyan);
}
```

删除 `0 0 30px rgba(0, 217, 255, 0.4)` 硬编码。`glow` 默认保持 `false`。

- [ ] **Step 6: Build**

```bash
cd frontend && npm run build-only
```

Expected: PASS。

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/common/PageShell.vue \
  frontend/src/components/common/PageHeaderBar.vue \
  frontend/src/components/common/ContentCard.vue \
  frontend/src/components/common/EmptyStateBlock.vue \
  frontend/src/components/common/Stack.vue \
  frontend/src/components/common/PageContainer.vue \
  frontend/src/components/ui-system/DarkCard.vue
git commit -m "feat(ui): add PageShell layout primitives for hx design system"
```

---

### Task 4: Slice 1 — 登录页 L-Full

**Files:**
- Modify: `frontend/src/views/auth/Login.vue`

**Interfaces:**
- Consumes: `--hx-*`；可选 ContentCard 或自写 card 用 token
- Produces: 登录页无硬编码 `#f0f2f5` / `#1890ff` 主视觉

- [ ] **Step 1: 替换 scoped 样式为 token**

```css
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: var(--hx-space-5);
  background: var(--hx-color-bg-layout);
  box-sizing: border-box;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: var(--hx-space-6) var(--hx-space-5);
  background: var(--hx-color-bg-container);
  border-radius: var(--hx-radius-lg);
  box-shadow: var(--hx-shadow-md);
  border: 1px solid var(--hx-color-border-muted);
}

.logo-area {
  text-align: center;
  margin-bottom: var(--hx-space-6);
}

.logo {
  height: 64px;
  margin-bottom: var(--hx-space-4);
}

.platform-title {
  font-size: var(--hx-font-size-xl);
  font-weight: 600;
  color: var(--hx-color-text-primary);
  margin: 0;
}

.login-form-button {
  width: 100%;
}
```

- [ ] **Step 2: 模板微调**

- 主按钮保持 `type="primary" size="large"` 且 `class="login-form-button"` 全宽。
- 不要改登录 API 逻辑。

- [ ] **Step 3: 本地实点**

```bash
cd frontend && npm run dev
```

浏览器打开 `/login`：卡片居中、圆角与主色为新蓝；错误密码出现 message.error。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/auth/Login.vue
git commit -m "style(ui): polish login page with hx tokens"
```

---

### Task 5: Slice 2 — 课堂列表 + 详情 + 课程详情

**Files:**
- Modify: `frontend/src/views/classroom/ClassroomListView.vue`
- Modify: `frontend/src/views/classroom/detail.vue`
- Modify: `frontend/src/views/classroom/course-detail.vue`
- 按需修改同目录子组件（`ClassroomHeader.vue`、`CourseList.vue` 等）仅当 padding/页头冲突时

**Interfaces:**
- Consumes: `PageShell`, `PageHeaderBar`, `EmptyStateBlock`, `Stack`
- Produces: 三页 L-Full 骨架；空列表走 EmptyStateBlock

- [ ] **Step 1: ClassroomListView 包 PageShell**

在根模板外包：

```vue
<PageShell max-width="wide">
  <PageHeaderBar title="我的课堂">
    <template #actions>
      <!-- 将原有「创建课堂」等主按钮移入；保证仅一个 primary -->
    </template>
    <template #extra>
      <!-- 原 Tab / 筛选条 -->
    </template>
  </PageHeaderBar>
  <!-- 原列表；空态替换 -->
  <EmptyStateBlock
    v-if="/* 对应分段空 */"
    description="暂无课堂"
  />
  ...
</PageShell>
```

script 增加：

```ts
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue'
```

- [ ] **Step 2: 收敛列表间距**

在该文件 `<style>` 中：

- `padding: 20px` → `var(--hx-space-4)` 或删掉（已由 PageShell 提供）
- `gap: 10px/20px` → `var(--hx-space-3)` / `var(--hx-space-5)`
- 卡片栅格 gutter 用 16（space-4）
- `#1890ff` / `#666` 改为 `var(--hx-color-primary)` / `var(--hx-color-text-secondary)`

若 PageShell 与页面根已有 padding，**删除页面根重复 padding**（D6）。

- [ ] **Step 3: detail.vue（文件大，只做骨架与间距）**

1. 根节点用 `<PageShell max-width="fluid">` 或 `wide`（课堂详情内容多时用 `wide`/`fluid`）。
2. 顶部标题区改为 `PageHeaderBar`（title=课堂名，actions=原操作按钮）。
3. Tab 内容区间距 `margin-top: var(--hx-space-4)`。
4. 不重写业务逻辑、不拆 2000 行文件（YAGNI）；只改 template 外层与 style 中明显非法 spacing。

- [ ] **Step 4: course-detail.vue**

同模式：PageShell + PageHeaderBar；章节列表 gap token 化；Loading 用 `a-spin` 包裹列表区（若尚无）。

- [ ] **Step 5: 验收**

```bash
cd frontend && npm run build-only
```

本地实点：`/classroom` → 进入某课堂 → 某课程详情。检查：无双重大空白、Tab 不贴边、空课堂 Empty 统一。

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/classroom/ClassroomListView.vue \
  frontend/src/views/classroom/detail.vue \
  frontend/src/views/classroom/course-detail.vue
git commit -m "style(ui): polish classroom list and detail shells"
```

---

### Task 6: Slice 3 — 学生实训 / 工作台 / 作业提交（L-Shell）

**Files:**
- Modify: `frontend/src/views/classroom/TrainingDetailInClassroom.vue`
- Modify: `frontend/src/views/classroom/TrainingWorkspace.vue`
- Modify: `frontend/src/views/classroom/BiTrainingWorkspace.vue`
- Modify: `frontend/src/views/classroom/homework-detail.vue`
- Modify: `frontend/src/views/classroom/submission/SubmissionDetail.vue`

**Interfaces:**
- Consumes: `hideFooter` meta（Task 2）、token、PageShell（详情/作业用；**工作台用 fluid 且 padding 缩小**）

- [ ] **Step 1: 实训详情 / 作业 / 提交**

对 `TrainingDetailInClassroom.vue`、`homework-detail.vue`、`SubmissionDetail.vue`：

1. 外层 `PageShell max-width="wide"`。
2. 替换本地 `.page-header` 为 `PageHeaderBar`（提交详情可 `show-back`）。
3. 主 CTA 仅一个 `type="primary"`。
4. spacing 收敛到阶梯。

- [ ] **Step 2: TrainingWorkspace 高度金丝雀**

**禁止**给工作台根再加 `padding: 24px` 导致编辑器变矮。推荐结构：

```vue
<div class="hx-workspace">
  <header class="hx-workspace__toolbar">...</header>
  <div class="hx-workspace__body">
    <!-- 原编辑器 / 分栏 -->
  </div>
</div>
```

```css
.hx-workspace {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--hx-header-height));
  background: var(--hx-color-bg-layout);
  overflow: hidden;
}
.hx-workspace__toolbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: var(--hx-space-2);
  padding: var(--hx-space-2) var(--hx-space-4);
  background: var(--hx-color-bg-container);
  border-bottom: 1px solid var(--hx-color-border-muted);
}
.hx-workspace__body {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  gap: var(--hx-space-2);
}
```

面板之间 gap 用 `var(--hx-space-2)` 或 `3`。不要改 Monaco 初始化逻辑。

- [ ] **Step 3: BiTrainingWorkspace**

同样工具条 + 全高 body；画布内部不重排业务。

- [ ] **Step 4: 实点金丝雀**

1. 打开实训工作台：编辑区高度应接近视口，**不被 footer 挡住**（meta hideFooter）。
2. 作业详情加载/空提交态可见。

```bash
cd frontend && npm run build-only
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/classroom/TrainingDetailInClassroom.vue \
  frontend/src/views/classroom/TrainingWorkspace.vue \
  frontend/src/views/classroom/BiTrainingWorkspace.vue \
  frontend/src/views/classroom/homework-detail.vue \
  frontend/src/views/classroom/submission/SubmissionDetail.vue
git commit -m "style(ui): shell student training workspace and homework pages"
```

---

### Task 7: Slice 4 — 教师课程实践列表与作业入口

**Files:**
- Modify: `frontend/src/views/course/index.vue`
- Modify: `frontend/src/views/course/practice/my-practices.vue`
- Modify: `frontend/src/views/classroom/TrainingHomework.vue`
- Modify: `frontend/src/views/classroom/TrainingGrades.vue`

**Interfaces:**
- Consumes: PageShell, PageHeaderBar, EmptyStateBlock

- [ ] **Step 1: `/course` 与 my-practices L-Full**

1. 根 `PageShell max-width="wide"`。
2. `PageHeaderBar` 标题「课程实践」/「我创建的实践」；创建按钮进 actions（一个 primary）。
3. 筛选行用 `Stack direction="horizontal" :gap="3"`。
4. 空数据 `EmptyStateBlock`。
5. 卡片/表格间距 token 化；删除与 PageShell 重复的外层 padding。

- [ ] **Step 2: TrainingHomework / TrainingGrades L-Shell**

PageShell + PageHeaderBar；表格 `a-table` 保持；toolbar 与表格间距 `var(--hx-space-4)`。

- [ ] **Step 3: Build + 点检**

```bash
cd frontend && npm run build-only
```

教师账号：`/course`、`/course/practice/my`、课堂内作业/成绩入口页布局整齐。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/course/index.vue \
  frontend/src/views/course/practice/my-practices.vue \
  frontend/src/views/classroom/TrainingHomework.vue \
  frontend/src/views/classroom/TrainingGrades.vue
git commit -m "style(ui): polish teacher practice list and grade shells"
```

---

### Task 8: Slice 5 — AI 教师三步 + 学生 Copilot / Hint

**Files:**
- Modify: `frontend/src/views/teacher-ai/GeneratorForm.vue`
- Modify: `frontend/src/views/teacher-ai/KnowledgeConfirm.vue`
- Modify: `frontend/src/views/teacher-ai/DraftsReview.vue`
- Modify: `frontend/src/views/student/AICopilotDashboard.vue`
- Modify: `frontend/src/views/student-ai/HintPanel.vue`
- Modify: `frontend/src/components/ai-copilot/AIChatWidget.vue`（及同目录用到的浮层组件）
- Modify: `frontend/src/components/ui-system/*` 若 Dashboard 使用

**Interfaces:**
- Consumes: tokens、PageShell、ContentCard/DarkCard、`--hx-z-ai-float`

- [ ] **Step 1: 教师 AI 三页**

每页：

```vue
<PageShell max-width="default">
  <PageHeaderBar :title="..." :subtitle="..." />
  <!-- 原表单/内容；区块用 Stack :gap="4" 或 ContentCard -->
</PageShell>
```

`GeneratorForm`：主提交按钮唯一 primary。  
`KnowledgeConfirm` / `DraftsReview`：列表与操作区间距 space-4；状态 Tag 用 AntD 默认色。

- [ ] **Step 2: AICopilotDashboard**

1. PageShell `wide`。
2. 栅格 gap `var(--hx-space-4)`。
3. 卡片统一 ContentCard 或 DarkCard（alias 已亮色）。
4. 背景必须是 layout 浅灰/白，**禁止残留深色满屏**（验 `background` 计算样式）。

- [ ] **Step 3: HintPanel + AIChatWidget z-index**

```css
.ai-chat-widget /* 或实际根 class */ {
  z-index: var(--hx-z-ai-float);
}
```

确认不盖死 Modal（AntD Modal 默认 1000；浮层 1100 仅用于右下角助手，打开 Modal 时助手可被盖或可接受——若冲突则浮层 1000、Modal 保持默认，助手低于 Modal）。

**裁决（写死）：** AI 浮层 `--hx-z-ai-float: 1100`；若挡住 Modal 确认框，则改为 `1000` 并保证助手 `pointer-events` 正常。以「Modal 可点确认」优先。

- [ ] **Step 4: 实点**

- `/teacher/ai-practice-generator` 三步页面骨架一致。
- `/student-dashboard` 卡片对齐、浅色。
- 打开 Chat 浮层再开任意 Modal：确认按钮可点。

```bash
cd frontend && npm run build-only && node scripts/check-hx-tokens.mjs
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/views/teacher-ai frontend/src/views/student \
  frontend/src/views/student-ai frontend/src/components/ai-copilot \
  frontend/src/components/ui-system
git commit -m "style(ui): polish AI generator and student copilot surfaces"
```

---

### Task 9: 清债收尾 D2/D7 复核 + P1 回归清单

**Files:**
- Modify: `frontend/src/router/index.ts`（删除 `// import { ElMessage } from 'element-plus'`）
- Modify: `frontend/package.json` / `package-lock.json`（**仅当**确认无引用）
- 可选: `frontend/src/assets/styles/tokens.css`（微调 z-index 若 Task 8 裁决变更）

**Interfaces:**
- Consumes: 全 P1 改动
- Produces: 回归证据；element-plus 无业务引用

- [ ] **Step 1: Element Plus 引用扫描**

```bash
cd frontend && grep -rn "element-plus\|ElMessage\|ElButton\|@element-plus" src --include='*.vue' --include='*.ts' || true
```

若仅注释：删除注释。若 `package.json` 的 `element-plus` / `@element-plus/icons-vue` 无任何引用：

```bash
cd frontend && npm uninstall element-plus @element-plus/icons-vue
```

若仍有隐藏引用：**不要卸载**，只删死注释并在 commit message 说明保留原因。

- [ ] **Step 2: Arco / 双 padding 抽查**

```bash
cd frontend && grep -rn '\.arco-' src --include='*.css' --include='*.vue' || true
cd frontend && node scripts/check-hx-tokens.mjs
cd frontend && npm run build-only
```

- [ ] **Step 3: 手写回归清单（执行并勾选）**

| # | 步骤 | 期望 |
|---|------|------|
| 1 | `/login` 错误密码 | error message；卡片 token 样式 |
| 2 | 正确登录 | 按角色跳转 |
| 3 | `/classroom` | PageShell 节奏；空态统一 |
| 4 | 进课堂详情 | 页头/Tab 间距正常 |
| 5 | 课程详情 | 列表可读 |
| 6 | 实训工作台 | 无 footer；编辑区足够高 |
| 7 | `/course` 与 my practices | 筛选+列表+一个 primary |
| 8 | AI generator 首页 | 表单分组清晰 |
| 9 | student-dashboard | 浅色网格卡片 |
| 10 | 1280 与 1920 窗口 | 无意外横向滚动（画布除外） |

- [ ] **Step 4: Commit**

```bash
git add frontend/src/router/index.ts frontend/package.json frontend/package-lock.json \
  frontend/src/assets/styles/tokens.css
git commit -m "chore(ui): finish P1 debt cleanup and dependency prune"
```

若无 package 变更则只提交实际改动文件。

---

## Self-Review（plan vs spec）

| Spec 要求 | 对应 Task |
|-----------|-----------|
| L0 tokens + AntD 对齐 | Task 1 |
| `--copilot-*` alias | Task 1 |
| AppShell / D1 D4 D5 D6 D8 | Task 2 |
| 布局原语 | Task 3 |
| 登录 | Task 4 |
| 课堂列表/详情/课程详情 | Task 5 |
| 学生工作台/作业/提交 | Task 6 |
| 教师实践/作业成绩 | Task 7 |
| AI 三步 + Copilot + Hint | Task 8 |
| D2 D7 + 回归 | Task 9 |
| 轻度现代化（主色/圆角/阴影） | Task 1 + 各页消费 |
| P2/P3 考试管理等 | **不在本 plan**（spec 明确） |
| challenge/detail 若高频 | Task 6 实点时若入口命中，同 L-Shell 补改并写入 commit body |

无 TBD/TODO 占位；组件 props 名在 Task 3 定义，后续 Task 引用一致。

---

## 执行方式

Plan 已保存后，实现阶段二选一：

1. **Subagent-Driven（推荐）** — 每 Task 新 subagent，Task 间 review  
2. **Inline Execution** — 本会话按 executing-plans 连续做并设检查点  
