# 慧学前端 UI 系统性升级设计

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-04 |
| 仓库 | https://github.com/bianjiefilm/huixue |
| 状态 | 已评审（brainstorming 定稿） |
| 范围策略 | 全站系统性升级，分期交付；本 spec 以 **Phase 1** 为可实现边界，并给出 P2/P3 路线 |

---

## 1. 背景与问题

慧学前端为 Vue 3 + Ant Design Vue 4，约 229 个 `.vue` 文件。历史迭代优先功能，UI 细节与一致性欠账明显：

- **设计 Token 半成品**：`theme-light.css` 中有 `--copilot-*` 变量，但业务页几乎不用；间距/颜色大量硬编码。
- **间距失控**：padding/gap/margin 存在 10/14/15/20 等游离值，同角色不同页疏密不一。
- **颜色散落**：`#1890ff`、`#333/#666/#999` 等与 AntD 语义色混用。
- **遗留补丁**：`App.vue` / `responsive.css` 残留大量 `.arco-*` 的 `!important`；`package.json` 仍含 Element Plus 等死依赖痕迹。
- **布局原语弱**：有 `BasicLayout`、`PageContainer`，但多数页面自写 `.page-header` 与 padding，列表/详情节奏不统一。

目标不是「换皮重做产品」，而是建立可维护的设计底座，打磨高频路径，清除明确技术债，再分期收口全站。

---

## 2. 目标与非目标

### 2.1 Phase 1 成功标准（A + B + C）

1. **观感统一（全局底座）**：spacing / 颜色 / 圆角 / 字号以 `--hx-*` + AntD theme 为真源并在应用入口生效；AppShell（顶栏/内容底/页脚策略）与 AntD 控件观感一致。**不要求** P1 内 229 个业务页全部改完硬编码。
2. **核心场景成品化（§6 清单）**：教学主路径 + AI 面达到交付级（骨架、间距、空/加载/错误态、按钮层级）。
3. **隐患清零（§7 可验证清单）**：Arco 遗留全局补丁、死依赖、双重 padding、工作台高度与 z-index 等明确债项清零。

### 2.2 视觉方向

**轻度现代化**（在 Ant Design 骨架上）：

- 圆角略增、阴影更柔、卡片层级更清晰。
- 登录 / 顶栏 / 空状态更精致。
- 主色可微调，不重做品牌识别与导航信息架构。

### 2.3 设备优先级

- **桌面 1280–1920 为主战场**。
- 平板/手机：保证可用、不炸布局（可折叠导航、表格可横滑），不追求移动端精品。

### 2.4 明确非目标（P1）

- 暗色主题回归。
- 导航信息架构大改（菜单增减/重命名）。
- 业务逻辑 / API 重构（除非 CSS 改动直接挡验收）。
- Storybook / 完整设计站点。
- 考试全套、管理后台深打磨、ML/BI 画布交互重做。
- 手机端精品体验、i18n、运营级插画。

---

## 3. 总体架构

```
L0  Design Tokens（CSS 变量 + Ant Design Theme token）
L1  全局主题与底座 CSS（theme.ts、tokens、清理后的 antd 覆盖）
L2  布局原语（AppShell / PageShell / PageHeaderBar / ContentCard / EmptyState / Stack）
L3  业务页面 — P1 核心链路用 L2 + token 成品化
L4  长尾页 — P2/P3 逐步对齐
```

### 3.1 原则

1. **单一 UI 主库**：Ant Design Vue 为唯一业务组件源。
2. **Token 双写对齐**：CSS 变量（自写样式）与 `theme.ts`（AntD 组件）同源语义。
3. **P1 核心页改页必用原语**：禁止再发明页面外边距魔法数。
4. **清债与切片绑定**：动到的全局文件彻底清；动到的业务页优先 token 化。
5. **轻度现代化落在 L0–L2**：业务页消费 token/原语，不各自发明视觉语言。
6. **桌面优先**：原语按 1280–1920 设计；`<768` 只做防溢出与基础折叠。

### 3.2 实施路径

采用 **Token 先行 + 核心页纵向切片**（路径 1）：

1. 定 Token + Layout 原语。
2. 同步清债（Arco、死依赖、全局冲突 CSS）。
3. 按核心链路逐页打磨，每条链路可独立验收。
4. 非核心页仅通过全局层「不跑偏」。

不采用：页面优先硬编码打磨（债换皮）；大设计系统一次做完再刷全站（P1 无可见产出）。

---

## 4. Design Token

### 4.1 命名与文件

| 项 | 决策 |
|----|------|
| 新前缀 | `--hx-*`（Huixue） |
| 兼容 | `--copilot-*` 在 P1 作为 **alias 指向同一值**；P2/P3 删除 |
| 真源 | `frontend/src/assets/styles/tokens.css` |
| AntD | `frontend/src/utils/theme.ts` 与 tokens 语义对齐 |
| 瘦身 | `theme-light.css` 只保留必要全局覆盖，不再重复整套色板 |

### 4.2 间距（4px 基准，仅允许下列阶梯）

| Token | 值 | 典型用途 |
|-------|-----|----------|
| `--hx-space-0` | 0 | reset |
| `--hx-space-1` | 4px | 图标与文字、badge |
| `--hx-space-2` | 8px | 控件内小间距 |
| `--hx-space-3` | 12px | 卡片内区块、列表项 |
| `--hx-space-4` | 16px | **默认块间距** |
| `--hx-space-5` | 24px | 页面区块、卡片 padding |
| `--hx-space-6` | 32px | 大区块分隔 |
| `--hx-space-7` | 48px | 登录/空状态大留白 |

约定：

- 页面内容水平 padding：`--hx-space-5`（24）。
- 区块垂直默认 16，大节 24。
- 栅格 gutter：16。
- 核心页改造时，不在阶梯内的值改到最近合法阶梯（如 20→16 或 24，10→8 或 12）。

### 4.3 颜色（轻度现代化）

| 语义 | Token | 建议值 |
|------|-------|--------|
| 主色 | `--hx-color-primary` | `#1677ff`（由 `#1890ff` 微调） |
| 悬停/按下 | `--hx-color-primary-hover/active` | `#4096ff` / `#0958d9` |
| 成功/警告/错误 | semantic tokens | 对齐 AntD，消除散落红/绿不一致 |
| 文本 | primary / secondary / tertiary / disabled | `rgba(0,0,0,0.88/0.65/0.45/0.25)` |
| 边框 | default / muted | `#d9d9d9` / `#f0f0f0` |
| 页面底 | `--hx-color-bg-layout` | `#f5f5f5` |
| 容器底 | `--hx-color-bg-container` | `#ffffff` |

AI 面可用 accent（紫/青 dim）局部强调，必须来自 token。

### 4.4 圆角 / 阴影 / 字号

| 类别 | 决策 |
|------|------|
| 圆角 sm/md/lg | 6 / 10 / 14 |
| AntD `borderRadius` | 6（原 4） |
| 阴影 | 柔和 sm/md 两档；避免过重 hover 阴影 |
| 字号 | 12 / 13 / 14 / 16 / 20 / 24 / 32 |
| 字重 | 400 / 500 / 600；标题用 600 |

### 4.5 Ant Design Theme 映射

`theme.ts` 至少同步：`colorPrimary`、语义色、文本/边框/背景、`borderRadius: 6`、`fontSize: 14`、`fontFamily` 与 CSS 一致。组件默认 size 保持 `middle`。

### 4.6 工程约束

1. 新代码优先 `var(--hx-*)`；禁止新增裸主色/灰阶魔法数与非阶梯 spacing。
2. 存量：P1 强制核心页 + 全局底座；长尾随改随换。
3. P1 不引入 Tailwind 作为第二套间距体系。
4. stylelint 可选，P1 不阻塞，靠 review 清单。

### 4.7 Token 层验收

- P1 页主色/正文/背景来自 token 或 AntD theme。
- `:root` 可见完整 `--hx-*`；`--copilot-*` 同值可用。
- 核心页 spacing 收敛到 4/8/12/16/24/32/48。

---

## 5. 布局原语与组件

### 5.1 目录

```
frontend/src/assets/styles/tokens.css
frontend/src/assets/styles/theme-light.css   # 瘦身
frontend/src/components/layout/BasicLayout.vue  # AppShell（可保留文件名）
frontend/src/components/common/
  PageShell.vue
  PageHeaderBar.vue
  ContentCard.vue
  EmptyStateBlock.vue
  Stack.vue                    # 推荐
  PageContainer.vue            # 内部转调 PageShell，兼容旧 import
frontend/src/components/ui-system/  # token 迁 --hx-*；DarkCard 语义中立化（SurfaceCard）
```

### 5.2 原语职责

#### AppShell（BasicLayout）

- 顶栏高度与导航/用户区间距 token 化；active 态清晰。
- 内容区背景 `--hx-color-bg-layout`；与 PageShell 划分 padding 职责（D6）。
- 页脚弱化；**workspace / blank** 路由经 `meta` 隐藏 footer 或全高。
- 登录 Modal 与独立登录页视觉一致。

#### PageShell

- `maxWidth`: `default` | `wide` | `fluid`。
- 统一水平 padding 与垂直节奏。
- `PageContainer` 兼容包装，减少全量 rename。

#### PageHeaderBar

- 左：标题 + 可选副标题/返回；右：actions；底：extra（筛选/Tabs）。
- 全站一种实现；核心页替换本地 `.page-header`。

#### ContentCard

- 默认 padding 24；`sm` 为 16；radius/shadow 用 token。
- 与 `a-card`：表单/数据块优先 AntD Card；需要统一壳时用 ContentCard。
- 禁止第三套手写 card 边框体系。

#### EmptyStateBlock

- 统一图标尺寸、主/次文案、可选 CTA、留白 space-6/7。

#### Stack

- `gap` 仅接受 space 阶梯 key（1–7），减少 margin 刷屏。

### 5.3 状态约定

| 状态 | 约定 |
|------|------|
| Loading | 同类型路由统一 Spin 或 Skeleton / table loading |
| Empty | EmptyStateBlock |
| Error | Result 或 Alert + 重试 |
| 按钮 | 每区最多一个 primary |

### 5.4 与 AntD 边界

- 不封装 `HxButton` 等薄包装；token 进 theme 即可。
- 图标继续 `@ant-design/icons-vue`。

### 5.5 原语层验收

- 核心列表页使用统一 shell。
- 页内标题结构一致。
- 空列表样式统一。
- 工作台无错误双重 padding / footer 挤压。

---

## 6. Phase 1 核心页与打磨标准

### 6.1 切片顺序

```
Slice 0  底座：Token + AppShell + 原语 + 清债入口
Slice 1  登录
Slice 2  课堂列表 → 课堂详情
Slice 3  学生：课程学习 → 实训工作台 → 提交相关
Slice 4  教师：课程实践列表/我的实践 → 作业/成绩入口
Slice 5  AI：教师生成三步 + 学生 Copilot / Hint
```

### 6.2 In Scope 页面

#### 认证

| 路由 | 文件 | 深度 |
|------|------|------|
| `/login` | `views/auth/Login.vue` | L-Full |

#### 课堂

| 路由 | 文件 | 深度 |
|------|------|------|
| `/classroom` | `ClassroomListView.vue` | L-Full |
| `/classroom/:id`（含子 tab） | `detail.vue` 等 | L-Full |
| `/classroom/.../course/...` | `course-detail.vue` | L-Full |

#### 学生做题 / 实训

| 路由/场景 | 文件 | 深度 |
|-----------|------|------|
| 实训详情 | `TrainingDetailInClassroom.vue` | L-Shell |
| 实训工作台 | `TrainingWorkspace.vue` | L-Shell |
| BI 工作台 | `BiTrainingWorkspace.vue` | L-Shell（不重大改画布） |
| 作业详情 | `homework-detail.vue` | L-Shell |
| 提交详情 | `submission/SubmissionDetail.vue` | L-Shell |
| 实践挑战详情（若为高频入口） | `course/challenge/detail.vue` 等 | L-Shell |

#### 教师课程实践

| 路由 | 文件 | 深度 |
|------|------|------|
| `/course` | `course/index.vue` | L-Full |
| `/course/practice/my` | `my-practices.vue` | L-Full |
| 作业/成绩入口 | `TrainingHomework.vue`、`TrainingGrades.vue` | L-Shell |

#### AI

| 路由 | 文件 | 深度 |
|------|------|------|
| `/teacher/ai-practice-generator` | `GeneratorForm.vue` | L-Full |
| `.../knowledge` | `KnowledgeConfirm.vue` | L-Full |
| `.../drafts` | `DraftsReview.vue` | L-Full |
| `/student-dashboard` | `AICopilotDashboard.vue` | L-Full |
| `/student/ai-hint-test/:challengeId` | `HintPanel.vue` | L-Shell |
| 嵌入组件 | `components/ai-copilot/*` | token + z-index |

### 6.3 打磨深度

| 级别 | 含义 |
|------|------|
| **L-Full** | 骨架 + token + 空/载/错 + 轻度现代化细节 |
| **L-Shell** | 骨架 + token + 溢出/间距/高度修复 |
| **L-Global** | 仅吃全局 theme（P1 范围外页） |

### 6.4 页面 Definition of Done

- 使用 PageShell（或等价）+ 合法 maxWidth。
- 页内标题用 PageHeaderBar（或统一封装）。
- 无页面级非法 spacing（编辑器内部像素对齐可保留并注释）。
- 色与圆角/阴影来自 token 或 theme。
- Loading / Empty / Error 齐全；每区一个 primary。
- 1280 与 1920 无意外横向滚动（画布内部除外）。
- 主流程本地点通不因 CSS 回归挂掉。

### 6.5 P1 Out of Scope 页面类

考试全套、云盘、学习分析大屏、管理后台、ML/BI 设计器重做、项目创建向导全流程（非列表必要改动）。

---

## 7. 清债清单（P1 可验证）

| ID | 债项 | 动作 | 完成标准 |
|----|------|------|----------|
| D1 | Arco 全局补丁 | 清理 `App.vue`、`responsive.css` 等 `.arco-*` | 无业务依赖 `.arco-*`；旧页改中性/AntD class |
| D2 | Element Plus 死依赖 | 删死引用；可移除则移出 `package.json` | 无业务引用 |
| D3 | 双轨变量 | `--hx-*` 真源 + `--copilot-*` alias | 数值单点维护 |
| D4 | 过重全局覆盖 | 收敛重复 `!important` 背景 | 底色靠 token |
| D5 | 空 media 壳 | 清理 `main.css` 空规则 | 无误导空块 |
| D6 | 双重 padding | AppShell vs PageShell 职责清晰 | 核心页无失控叠 padding |
| D7 | z-index | 约定层级表（顶栏 < 菜单 < 抽屉 < Modal < AI 浮层） | 浮层不互挡 |
| D8 | 工作台与 footer | meta 控制 footer/全高 | 工作台高度可用 |

P1 不做：全量 229 页去硬编码；业务组件大重构；后端改动。

---

## 8. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 主色微调全站变色 | theme 单点；发布说明「轻度刷新」 |
| 清 Arco 后旧页回弹 | 清后扫 micro/课程相关页 |
| 工作台高度回归 | Slice 3 高度金丝雀优先 |
| AI 仍用旧变量 | alias 保底；Dashboard 验背景 |
| 范围膨胀 | §6.5 硬边界，新需求进 P2 |

---

## 9. 分期路线（全站 D 方案）

| 期 | 目标 |
|----|------|
| **P1** | Token + 原语 + D1–D8 + §6 核心页 + 轻度现代化 |
| **P2** | 考试、成绩、资源、项目实训、管理后台列表接 PageShell |
| **P3** | 长尾页、微动效、无障碍与桌面下平板增强；删除 `--copilot-*` alias |

实现计划文档仅先覆盖 **P1**；P2/P3 另开 plan 或附录增量。

---

## 10. 工程落地顺序（P1）

1. `tokens.css` + `theme.ts` 对齐 + 入口 import。
2. AppShell / 全局 CSS 清债（D1, D4, D5, D6, D8）。
3. PageShell / PageHeaderBar / EmptyStateBlock / ContentCard / Stack。
4. Slice 1→5 按页打磨。
5. 依赖清理（D2）与 z-index（D7）收尾。
6. 本地回归清单确认。

---

## 11. 测试与验收

### 11.1 环境

本地 frontend / 本地 Docker Compose。证据来自本地真实运行（本仓库纪律）。本轮不强制学校服务器。

### 11.2 层级

| 层 | 内容 | 证据 |
|----|------|------|
| 静态 | type-check / build | 命令输出 |
| Token | DevTools `--hx-*`；抽查 spacing | 抽查记录 |
| 链路 UAT | 登录→课堂→工作台；教师实践；AI 三步；学生 Dashboard | 实点结果 |
| 金丝雀 | 空列表 Empty；登录失败错误态 | 证明未粉饰 |
| 清债 | grep 无业务 `.arco-`；element-plus 无引用 | 命令输出 |

### 11.3 P1 一句话成功标准

在桌面 1280–1920 下，主教学路径与 AI 面使用统一 token 与页面骨架，间距阶梯一致，明确债项清零，观感为轻度现代化后的 Ant Design 教育产品——而不是又一套硬编码「好看页」。

禁止：以 code review 代替点检；未 build/未实点声称完成；夸大「全站 229 页已打磨」。

---

## 12. 决策记录（brainstorming）

| 决策点 | 选择 |
|--------|------|
| 总范围 | 全站系统性升级（分期） |
| P1 成功标准 | 底座统一 + 核心页成品 + 隐患清零 |
| 核心页集合 | 教学主路径 + AI 面 |
| 视觉 | 轻度现代化 |
| 设备 | 桌面优先 |
| 路径 | Token 先行 + 纵向切片 |
| 主色 | `#1677ff` |
| 圆角 | 6 / 10 / 14 |
| 仓库 | https://github.com/bianjiefilm/huixue |

---

## 13. 后续步骤

1. 用户审阅本 spec；如有修改则更新本文档。
2. 批准后进入 **writing-plans**：输出 P1 可执行实现计划（任务粒度、文件清单、验收命令）。
3. 再按 Slice 0→5 实现与本地验收。
