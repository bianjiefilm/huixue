# 慧学前端 UI 系统性升级设计

| 项 | 内容 |
|----|------|
| 日期 | 2026-08-04 |
| 仓库 | https://github.com/bianjiefilm/huixue |
| 状态 | 已评审；**§14 Phase 2 已展开**（2026-08-04） |
| 范围策略 | 全站系统性升级，分期交付；P1 见实现分支；**P2 详见 §14** 与 `plans/2026-08-04-ui-upgrade-p2.md` |

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

| 期 | 目标 | 计划文档 |
|----|------|----------|
| **P1** | Token + 原语 + D1–D8 + §6 核心页 + 轻度现代化 | `docs/superpowers/plans/2026-08-04-ui-upgrade-p1.md`（已实现于 `feat/ui-upgrade-p1`） |
| **P2** | 次高频业务面接入原语 + P1 遗留收口（见 **§14**） | `docs/superpowers/plans/2026-08-04-ui-upgrade-p2.md` |
| **P3** | 长尾页、微动效、无障碍与桌面下平板增强；删除 `--copilot-*` alias | 另开 |

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

1. ~~用户审阅本 spec；P1 writing-plans + 实现~~（P1 代码在 `feat/ui-upgrade-p1`）。
2. 审阅 **§14 P2 范围** 与 `docs/superpowers/plans/2026-08-04-ui-upgrade-p2.md`。
3. 批准后按 P2 plan 切片实现；补一次 P1 浏览器 UAT（若仍未跑）。
4. P3 另开 design 增量。

---

## 14. Phase 2 详细范围（次高频业务面）

> **前置条件：** P1 的 L0 Token、L1 AppShell、L2 原语（`PageShell` / `PageHeaderBar` / `EmptyStateBlock` / `Stack` / `ContentCard`）已存在。P2 **不** 再造设计系统，只做 **接入 + 收口 + 表格/表单页节奏统一**。

### 14.1 P2 成功标准

1. **次高频业务面壳统一：** 考试中心、课堂内考试/成绩、资源与云盘、项目实训列表/详情、管理后台列表与仪表盘，全部使用 PageShell + PageHeaderBar（或等价），间距阶梯与空态统一。
2. **P1 遗留收口：** `detail.vue` 内部 token 扫尾；工作台/作业页残留硬编码主色清理；全屏路由 `hideFooter` 补全（考试作答、Jupyter、BI 预览等）。
3. **管理后台可辨识：** Admin 布局与内容区 padding 不与 PageShell 双重叠；列表页筛选 + 表格 + 一个 primary 的节奏一致。
4. **不重做：** 试卷编辑器画布逻辑、考试计时内核、ML/BI 设计器交互、审批业务规则。

### 14.2 继承约束（与 P1 相同）

- Token：`--hx-*`；间距仅 0/4/8/12/16/24/32/48；主色 `#1677ff`；圆角 6/10/14。
- 新代码禁止裸 `#1890ff` / 非阶梯 padding；优先 `var(--hx-*)`。
- 桌面 1280–1920 优先；手机仅防炸。
- 不改 API / 导航信息架构（菜单项不增删重命名）。
- 每 Task 独立 commit；本地 build + 结构/可点检证据。

### 14.3 切片顺序

```
P2-Slice 0  P1 遗留收口（detail 内 token、hideFooter 补全、硬编码主色扫核心残留）
     ↓
P2-Slice 1  考试中心（题库 / 试卷库 / 我的考试 / 出题表单壳）
P2-Slice 2  课堂内考试 + 成绩 + 作答/批改壳
P2-Slice 3  资源 / 云盘 / 学习分析（壳 + 空态；大屏不重设计）
P2-Slice 4  项目实训（列表 / 详情 / 创建编辑壳；Jupyter 全高）
P2-Slice 5  管理后台（仪表盘 + 用户/组织/课程列表 + 资源导入壳）
P2-Slice 6  回归清单（含 P1 路径抽检 + P2 新路径）
```

### 14.4 页面清单与深度

#### P2-Slice 0 — P1 遗留（先做，成本低收益高）

| 项 | 文件 / 动作 | 深度 |
|----|-------------|------|
| 课堂详情内样式 | `views/classroom/detail.vue` | 内部 spacing/颜色 token 化；去掉 cyan 暗色 hover 语言 |
| 工作台残留主色 | `TrainingWorkspace.vue`、`BiTrainingWorkspace.vue` | `#1890ff` / 非法 padding → token |
| hideFooter 补全 | `router/index.ts` | `ExamTake`、`exam-take` 相关、`JupyterTraining`、`PublicJupyterTraining`、`VisualPreview`、`BIPreviewFullscreen`、`ProjectTrainingCodeTask`、`MachineLearningDesigner` 等全屏页 |
| 可选 | `PageHeaderBar` 返回文案/图标统一 | 小改 |

#### P2-Slice 1 — 考试中心（`/exam/*`）

| 路由 | 文件 | 深度 |
|------|------|------|
| `/exam` | `views/exam/index.vue` | L-Full（入口/导航壳） |
| `/exam/question-bank` | `question-bank.vue` | L-Full |
| `/exam/paper-bank` | `paper-bank.vue` | L-Full |
| `/exam/my-exams` | `my-exams.vue` | L-Full |
| `/exam/create-question`、`edit-question` | 对应 vue | L-Shell（表单页头 + 区块间距） |
| `/exam/edit-paper`、`template-paper` | 对应 vue | L-Shell（**不**重做拖拽出卷内核） |

#### P2-Slice 2 — 课堂内考试 / 成绩

| 路由 / 场景 | 文件 | 深度 |
|-------------|------|------|
| 课堂考试列表 | `ClassroomExams.vue`、`ClassroomExamList.vue` | L-Full |
| 创建考试 | `ClassroomExamCreate.vue` | L-Shell |
| 课程考试 | `course-exam.vue` | L-Shell |
| 考试详情 / 结果 / 统计 | `exam-detail.vue`、`exam-results.vue`、`exam-statistics.vue`、`exam-my-result.vue` | L-Shell |
| 批改列表 / 详情 | `exam-marking-list.vue`、`exam-marking-detail.vue`、`exam-marking.vue` | L-Shell |
| 答卷查看 | `exam-paper-view.vue` | L-Shell |
| **学生作答** | `exam-take.vue` | L-Shell + **hideFooter** + 顶栏/题区高度可用（类似工作台，勿 PageShell 大 padding） |
| 课程成绩 / 学生成绩 | `course-grades.vue`、`student-grades.vue`、`course-status.vue`、`student-course-status.vue` | L-Shell |

#### P2-Slice 3 — 资源 / 云盘 / 分析

| 路由 / 场景 | 文件 | 深度 |
|-------------|------|------|
| 课程资源库 | `views/course/resource/index.vue`、`detail.vue` | L-Full / L-Shell |
| 课堂资源 Tab | `ResourcesList.vue`（及 detail 内嵌） | L-Shell |
| 云盘 | `CloudDisk.vue` | L-Shell |
| 学习分析 | `LearningAnalytics.vue` | L-Shell（图表容器间距；**不**重设计图表主题，除非 echarts 色可单点映射 primary） |

#### P2-Slice 4 — 项目实训

| 路由 | 文件 | 深度 |
|------|------|------|
| `/project` | `views/project/index.vue` | L-Full |
| `/project/:id` | `detail-new.vue`（或当前生效详情） | L-Full / L-Shell |
| 创建/我的 | `create/*`、`myprojects.vue` 若入口存活 | L-Shell |
| Jupyter / code task | `jupyter-training.vue`、`code-task.vue`、`ProjectTraining.vue` | L-Shell 全高 + hideFooter；**不**改内核 |

#### P2-Slice 5 — 管理后台

Admin 使用 `views/admin/index.vue` 自有 layout；P2 要求：

- 内容区与子页 **约定唯一 padding 责任**（layout 或 PageShell 二选一，禁止双 24）。
- 列表页统一：PageHeaderBar（或 admin 内同等页头）+ 筛选 Stack + `a-table` + EmptyStateBlock。

| 路由 | 文件 | 深度 |
|------|------|------|
| `/admin/dashboard` | `admin/dashboard/index.vue` | L-Full（卡片栅格 gap token） |
| 教师/学生/角色 | `system/teacher-management.vue`、`admin/user/Student.vue`、`Role.vue` | L-Full |
| 学校/院系 | `system/school-info.vue`、`admin/organization/Department.vue` | L-Shell |
| 实践/实训课程管理与审批 | `admin/course/*.vue` | L-Shell |
| 资源导入 | `admin/resource-import.vue` | L-Shell |
| 日志类（若常用） | `admin/logs/*` **抽 1–2 高频列表** | L-Shell；其余 L-Global |

#### 明确 Out of Scope（P2）

- ML 画布 / BI 设计器交互重做（仅 hideFooter + 外层不炸）。
- 试卷拖拽编辑器内核、评分算法、导入解析逻辑。
- P3：全量长尾、删 `--copilot-*` alias、无障碍 AA、微动效体系。
- 暗色主题、移动端精品。

### 14.5 深度与 DoD（复用 §6.3 / §6.4）

| 类型 | 深度 | 要点 |
|------|------|------|
| 列表 / 题库 / 管理表 | L-Full | Shell + Header + Empty + 筛选间距 + 一 primary |
| 表单 / 批改 / 详情 | L-Shell | Shell + Header + 区块 gap；业务控件不重写 |
| 作答 / Jupyter / 预览全屏 | L-Shell 全高 | **禁止** PageShell 默认 24 全包；用 workspace 模式或 `maxWidth=fluid` + 零/小 padding |
| 分析大屏 | L-Shell | 容器与标题齐；图表内部可保持 |

页面标完成仍须满足 §6.4 清单（骨架、token、三态、桌面宽度、主流程不因 CSS 挂）。

### 14.6 P2 清债增量

| ID | 项 | 完成标准 |
|----|-----|----------|
| D9 | P1 页残留 `#1890ff` / 非法 spacing（已改文件） | 核心 P1 文件 grep 显著下降 |
| D10 | 全屏路由 hideFooter 覆盖 | 作答/Jupyter/预览无 footer 挤高度 |
| D11 | Admin 双 padding | 子页抽查无 48px 观感 |
| D12 | （可选）死 CSS 文件 `antd-theme.css` | 主入口未用则删除或标注 only test |

### 14.7 风险

| 风险 | 缓解 |
|------|------|
| 考试页极多、易 scope 膨胀 | 严格 L-Shell；edit-paper 只动壳 |
| exam-take 高度被 Shell 压矮 | 单独 workspace 模式，参考 TrainingWorkspace |
| Admin 自有 layout 与 PageShell 冲突 | 先定 padding 归属再批量改子页 |
| 无本地账号无法 UAT | 静态 + build 可合代码；验收通过必须补浏览器 |

### 14.8 P2 一句话成功标准

在 P1 底座之上，考试 / 成绩 / 资源 / 项目实训 / 管理后台次高频面与主路径 **同一套页面骨架与间距语言**；全屏作答与 Jupyter 高度可用；P1 已知半吊子页（尤其课堂 detail 内部）收口——仍不宣称全站 229 页完成。

### 14.9 工程落地顺序（P2）

1. P2-Slice 0 遗留收口。  
2. Slice 1→5 按域接入原语。  
3. Slice 6 回归（P1 抽检 + P2 新路径 + build + token check）。  
4. 浏览器 UAT（有本地栈时必跑）。  

详细任务拆解见：`docs/superpowers/plans/2026-08-04-ui-upgrade-p2.md`。
