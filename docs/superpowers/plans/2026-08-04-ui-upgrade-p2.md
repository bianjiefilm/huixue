# 慧学前端 UI 升级 Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 P1 的 token + 布局原语底座上，把考试、成绩、资源、项目实训、管理后台等次高频面接入统一壳层，并收口 P1 遗留（detail 内部 token、全屏 hideFooter、硬编码主色）。

**Architecture:** 复用 `PageShell` / `PageHeaderBar` / `EmptyStateBlock` / `Stack` / `--hx-*`；不新增设计体系。全屏作答/Jupyter 走 workspace 高度模式（无 PageShell 大 padding）。Admin 先定 padding 归属再批量改子页。规格：`docs/superpowers/specs/2026-08-04-ui-upgrade-design.md` **§14**。

**Tech Stack:** Vue 3、Ant Design Vue 4、TypeScript、Vite、已有 hx tokens；仓库 https://github.com/bianjiefilm/huixue

## Global Constraints

- 继承 P1：主色 `#1677ff`；间距阶梯 `0/4/8/12/16/24/32/48`；圆角 6/10/14；仅 Ant Design Vue；无 Tailwind
- 新代码只用 `var(--hx-*)`；禁止新增裸 `#1890ff` / 非阶梯 spacing
- 不改业务 API、导航 IA、考试内核、ML/BI 画布交互
- 桌面 1280–1920 优先
- 全屏页（作答/Jupyter/预览）：`meta.hideFooter: true` + 禁止用默认 PageShell 24px 压高度
- 每 Task 独立 commit；`cd frontend && npm run build-only` + `node scripts/check-hx-tokens.mjs` 绿
- 禁止无浏览器证据宣称「验收通过」；环境阻塞须在报告标明 BLOCKED

## Prerequisites

- P1 已合入或本分支基于含 P1 的 tip（至少含 `tokens.css`、`PageShell.vue`、`PageHeaderBar.vue`、BasicLayout `hideFooter`）
- 确认：

```bash
test -f frontend/src/assets/styles/tokens.css && test -f frontend/src/components/common/PageShell.vue
cd frontend && node scripts/check-hx-tokens.mjs
```

---

## File Structure（P2 主要触达）

| 区域 | 路径 |
|------|------|
| 路由 meta | `frontend/src/router/index.ts` |
| P1 收口 | `views/classroom/detail.vue`、`TrainingWorkspace.vue`、`BiTrainingWorkspace.vue` |
| 考试中心 | `views/exam/*.vue` |
| 课堂考试/成绩 | `views/classroom/ClassroomExams.vue`、`ClassroomExam*.vue`、`exam-*.vue`、`course-grades.vue`、`student-grades.vue`、`course-status.vue`、`student-course-status.vue`、`course-exam.vue` |
| 资源/云盘/分析 | `views/course/resource/*`、`ResourcesList.vue`、`CloudDisk.vue`、`LearningAnalytics.vue` |
| 项目实训 | `views/project/*` |
| 管理后台 | `views/admin/**`、`views/system/*` |
| 可选死文件 | `assets/antd-theme.css`（仅 test 引用则标注或删） |

---

### Task 1: P2-Slice 0 — P1 遗留收口 + hideFooter 补全

**Files:**
- Modify: `frontend/src/views/classroom/detail.vue`
- Modify: `frontend/src/views/classroom/TrainingWorkspace.vue`
- Modify: `frontend/src/views/classroom/BiTrainingWorkspace.vue`
- Modify: `frontend/src/router/index.ts`
- Optional: `frontend/src/components/common/PageHeaderBar.vue`（返回图标统一）

**Interfaces:**
- Consumes: `--hx-*`、已有 `meta.hideFooter`、`PageHeaderBar.backTo`
- Produces: 全屏路由 meta 列表扩展；detail 标准视图无 cyan 暗色 hover 语言

- [ ] **Step 1: hideFooter 审计并补全**

在 `router/index.ts` 为下列 **name**（若存在）合并 `meta: { hideFooter: true }`：

- `ExamTake`
- `TrainingWorkspace` / `BiTrainingWorkspace`（应已有，核对）
- `JupyterTraining` / `PublicJupyterTraining`
- `VisualPreview` / `BIPreviewFullscreen`
- `ProjectTrainingCodeTask`
- `ClassroomBIDesigner` / `PublicBIDesigner` / `PublicAIDesigner` / `MachineLearningDesigner` / `VisualAnalysisDesigner`
- 其他 `workspace` / `embed` / `preview` 全屏路由

验证：

```bash
cd frontend && grep -n "hideFooter" src/router/index.ts
```

- [ ] **Step 2: detail.vue 内部 token 扫尾**

仅改 **style + 明显 class 色**，不改业务 script：

1. 非法 spacing → 最近阶梯：`15px`→12/16，`5px`→4/8，`10px`→8/12
2. `border-radius: 4px` → `var(--hx-radius-sm)`（6）或保持组件默认
3. 删除/替换 cyan 暗色 hover：`rgba(0, 198, 255, …)`、`#00c6ff` 回退 → `var(--hx-color-primary)` / `var(--hx-color-primary-dim)`
4. `#1890ff` → `var(--hx-color-primary)`
5. 保留 workspace 全屏分支结构（勿把 workspace 包进 PageShell 大 padding）

- [ ] **Step 3: 工作台残留硬编码**

`TrainingWorkspace.vue` / `BiTrainingWorkspace.vue`：

```bash
grep -nE '#1890ff|padding:\s*10px|padding:\s*20px' \
  src/views/classroom/TrainingWorkspace.vue \
  src/views/classroom/BiTrainingWorkspace.vue
```

能 token 化的改掉；编辑器内部像素对齐可保留并加注释 `/* editor pixel align */`。

- [ ] **Step 4: 验证与 commit**

```bash
cd frontend && node scripts/check-hx-tokens.mjs && npm run build-only
git add frontend/src/router/index.ts \
  frontend/src/views/classroom/detail.vue \
  frontend/src/views/classroom/TrainingWorkspace.vue \
  frontend/src/views/classroom/BiTrainingWorkspace.vue
git commit -m "style(ui): p2 slice0 close p1 leftovers and fullscreen hideFooter"
```

---

### Task 2: P2-Slice 1 — 考试中心壳

**Files:**
- Modify: `frontend/src/views/exam/index.vue`
- Modify: `frontend/src/views/exam/question-bank.vue`
- Modify: `frontend/src/views/exam/paper-bank.vue`
- Modify: `frontend/src/views/exam/my-exams.vue`
- Modify: `frontend/src/views/exam/create-question.vue`
- Modify: `frontend/src/views/exam/edit-question.vue`
- Modify: `frontend/src/views/exam/edit-paper.vue`（仅外壳）
- Modify: `frontend/src/views/exam/template-paper.vue`（仅外壳）

**Interfaces:**
- Consumes: `PageShell`、`PageHeaderBar`、`EmptyStateBlock`、`Stack`
- Produces: `/exam/*` 列表 L-Full；表单/编辑 L-Shell

- [ ] **Step 1: 列表四页模板模式**

每页根结构：

```vue
<template>
  <PageShell max-width="wide">
    <PageHeaderBar :title="PAGE_TITLE" :subtitle="optionalStats">
      <template #actions>
        <!-- 唯一 type="primary" 主操作 -->
      </template>
      <template #extra>
        <Stack direction="horizontal" :gap="3">
          <!-- 搜索 / 筛选 -->
        </Stack>
      </template>
    </PageHeaderBar>
    <EmptyStateBlock v-if="!loading && isEmpty" description="暂无数据" />
    <a-table v-else ... />
  </PageShell>
</template>

<script setup lang="ts">
import PageShell from '@/components/common/PageShell.vue'
import PageHeaderBar from '@/components/common/PageHeaderBar.vue'
import EmptyStateBlock from '@/components/common/EmptyStateBlock.vue'
import Stack from '@/components/common/Stack.vue'
</script>
```

标题约定：

| 文件 | title |
|------|-------|
| `index.vue` | 考试中心（或保持原入口文案） |
| `question-bank.vue` | 题库 |
| `paper-bank.vue` | 试卷库 |
| `my-exams.vue` | 我的考试 |

- [ ] **Step 2: 去掉双 padding**

删除页面根 `padding: 24px` / 自建 max-width 容器与 PageShell 重叠的样式。

- [ ] **Step 3: 表单/编辑页 L-Shell**

`create-question` / `edit-question` / `template-paper`：

- PageShell `default` 或 `wide`
- PageHeaderBar + `show-back`（`backTo` 指回题库/试卷库路径，勿只靠 `router.back()` 若域内跳转明确）
- **禁止** 重写题目编辑器/组卷拖拽逻辑；只动外层与 spacing token

`edit-paper.vue`（~1.2k 行）：只改根节点与页头/外边距；内部画布 class 不动。

- [ ] **Step 4: build + commit**

```bash
cd frontend && npm run build-only
git add frontend/src/views/exam
git commit -m "style(ui): p2 shell exam center lists and forms"
```

---

### Task 3: P2-Slice 2 — 课堂考试 / 成绩 / 作答壳

**Files:**
- Modify: `ClassroomExams.vue`、`ClassroomExamList.vue`、`ClassroomExamCreate.vue`
- Modify: `course-exam.vue`、`exam-detail.vue`、`exam-results.vue`、`exam-statistics.vue`、`exam-my-result.vue`
- Modify: `exam-marking-list.vue`、`exam-marking-detail.vue`、`exam-marking.vue`、`exam-paper-view.vue`
- Modify: `exam-take.vue`（高度敏感）
- Modify: `course-grades.vue`、`student-grades.vue`、`course-status.vue`、`student-course-status.vue`

**Interfaces:**
- Consumes: 原语 + `hideFooter` on ExamTake
- Produces: 列表壳统一；`exam-take` 全高可用

- [ ] **Step 1: 列表/成绩页**

模式同 Task 2：`PageShell wide` + `PageHeaderBar` + 表格/卡片 + Empty。  
成绩页保持 `a-table`；toolbar 与 table 间距 `var(--hx-space-4)`。  
`back-to` 指回课堂或课程路径（带 id）。

- [ ] **Step 2: 批改 / 答卷 L-Shell**

PageHeaderBar + 内容区 gap token；侧栏固定评分若存在，参考 SubmissionDetail：宽屏 fixed + 窄屏 static，**勿引入非法 spacing**。

- [ ] **Step 3: exam-take 全高（Critical）**

**不要** 使用默认 PageShell 大 padding。推荐：

```vue
<div class="hx-exam-take">
  <header class="hx-exam-take__toolbar">...</header>
  <div class="hx-exam-take__body">...</div>
</div>
```

```css
.hx-exam-take {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--hx-header-height));
  background: var(--hx-color-bg-layout);
  overflow: hidden;
}
.hx-exam-take__toolbar {
  flex: 0 0 auto;
  padding: var(--hx-space-2) var(--hx-space-4);
  background: var(--hx-color-bg-container);
  border-bottom: 1px solid var(--hx-color-border-muted);
}
.hx-exam-take__body {
  flex: 1 1 auto;
  min-height: 0;
  overflow: auto;
  padding: var(--hx-space-4);
}
```

确认路由 `ExamTake` 已 `hideFooter: true`。不改计时/交卷逻辑。

- [ ] **Step 4: build + commit**

```bash
cd frontend && npm run build-only
git add frontend/src/views/classroom/ClassroomExam*.vue \
  frontend/src/views/classroom/exam-*.vue \
  frontend/src/views/classroom/course-exam.vue \
  frontend/src/views/classroom/course-grades.vue \
  frontend/src/views/classroom/student-grades.vue \
  frontend/src/views/classroom/course-status.vue \
  frontend/src/views/classroom/student-course-status.vue
git commit -m "style(ui): p2 shell classroom exams grades and exam-take"
```

---

### Task 4: P2-Slice 3 — 资源 / 云盘 / 学习分析

**Files:**
- Modify: `frontend/src/views/course/resource/index.vue`
- Modify: `frontend/src/views/course/resource/detail.vue`
- Modify: `frontend/src/views/classroom/ResourcesList.vue`
- Modify: `frontend/src/views/classroom/CloudDisk.vue`
- Modify: `frontend/src/views/classroom/LearningAnalytics.vue`

- [ ] **Step 1: 资源列表 L-Full**

`course/resource/index.vue`：PageShell + Header + 筛选 Stack + 卡片/列表 gutter 16 + EmptyStateBlock。

- [ ] **Step 2: 资源详情 / 课堂资源 / 云盘 L-Shell**

统一页头与内容间距；上传主按钮唯一 primary；文件表格/树不重写逻辑。

- [ ] **Step 3: LearningAnalytics**

- 外层 PageShell wide + PageHeaderBar  
- 图表卡片 gap `var(--hx-space-4)`  
- **不**强制重写 echarts 配色；若有写死 `#1890ff` 可改为 primary token 字符串 `'#1677ff'` 或从 CSS 变量读（注意 echarts 不解析 css var 时用常量对齐 theme）

- [ ] **Step 4: build + commit**

```bash
cd frontend && npm run build-only
git add frontend/src/views/course/resource \
  frontend/src/views/classroom/ResourcesList.vue \
  frontend/src/views/classroom/CloudDisk.vue \
  frontend/src/views/classroom/LearningAnalytics.vue
git commit -m "style(ui): p2 shell resources drive and analytics"
```

---

### Task 5: P2-Slice 4 — 项目实训

**Files:**
- Modify: `frontend/src/views/project/index.vue`
- Modify: `frontend/src/views/project/detail-new.vue`（若路由用此文件；否则 `detail.vue`）
- Modify: `frontend/src/views/project/myprojects.vue`（若仍挂载）
- Modify: create 流程相关 vue（仅壳）
- Modify: `jupyter-training.vue`、`code-task.vue`、`ProjectTraining.vue`

- [ ] **Step 1: 列表/详情 L-Full/L-Shell**

`/project`：与 `/course` 同节奏（PageShell wide、Header、卡片 gutter 16、Empty）。  
详情：Header + actions 一个 primary（如「进入实训」）。

- [ ] **Step 2: Jupyter / code 全高**

同 exam-take / TrainingWorkspace：

- `hideFooter` 已在 Task 1  
- 根 `height: calc(100vh - var(--hx-header-height))`  
- 无外层 padding 24  

不改 Jupyter/iframe 业务。

- [ ] **Step 3: build + commit**

```bash
cd frontend && npm run build-only
git add frontend/src/views/project
git commit -m "style(ui): p2 shell project training list and workspaces"
```

---

### Task 6: P2-Slice 5 — 管理后台

**Files:**
- Modify: `frontend/src/views/admin/index.vue`（layout padding 策略）
- Modify: `frontend/src/views/admin/dashboard/index.vue`
- Modify: `frontend/src/views/system/teacher-management.vue`
- Modify: `frontend/src/views/admin/user/Student.vue`
- Modify: `frontend/src/views/admin/user/Role.vue`
- Modify: `frontend/src/views/system/school-info.vue`
- Modify: `frontend/src/views/admin/organization/Department.vue`
- Modify: `frontend/src/views/admin/course/*.vue`
- Modify: `frontend/src/views/admin/resource-import.vue`
- Optional: `frontend/src/views/admin/logs/` 下 1–2 个最高频列表

**Interfaces:**
- Produces: Admin 内容区 **单一 padding 来源**；列表页壳统一

- [ ] **Step 1: 定 padding 归属（先写注释再改）**

打开 `admin/index.vue`：

- 若 layout content 已有 `padding: 24px`，则子页 **不要** 再包 `PageShell` 的默认 padding：子页用 `PageShell max-width="fluid"` 并扩展 PageShell 支持 `noPadding` **或** 子页只用 Header 不用 PageShell。
- **推荐（少改原语）：** layout 保留 padding；子页使用：

```vue
<div class="admin-page">
  <PageHeaderBar title="..." />
  <Stack :gap="4">...</Stack>
</div>
```

```css
.admin-page { width: 100%; } /* 无额外 padding */
```

若 layout **无** padding：子页用 `PageShell max-width="wide"`。

在 `admin/index.vue` 顶部注释写明选择：`/* P2: content padding owned by layout|page */`。

- [ ] **Step 2: Dashboard L-Full**

卡片栅格 `gutter` 16；统计数字色 token；去掉散落 `#1890ff`。

- [ ] **Step 3: 用户/组织/课程列表 L-Full/L-Shell**

统一：

1. PageHeaderBar 标题 + 一个 primary（新建/导入）  
2. 筛选 Stack horizontal gap 3  
3. `a-table` + loading  
4. 空数据 EmptyStateBlock  

- [ ] **Step 4: 资源导入 L-Shell**

步骤条/表单区块 gap space-4；主 CTA 唯一 primary。

- [ ] **Step 5: build + commit**

```bash
cd frontend && npm run build-only
git add frontend/src/views/admin frontend/src/views/system
git commit -m "style(ui): p2 shell admin dashboard and management lists"
```

---

### Task 7: P2-Slice 6 — 回归清单 + 可选死代码

**Files:**
- Optional: `frontend/src/assets/antd-theme.css`、引用方 `main-test.ts`
- Report: `.superpowers/sdd/task-p2-regression.md`（可 gitignore 目录）

- [ ] **Step 1: 静态门禁**

```bash
cd frontend
node scripts/check-hx-tokens.mjs
npm run build-only
# P2 新改文件抽查
grep -rn '#1890ff' src/views/exam src/views/admin src/views/project \
  src/views/classroom/exam-take.vue src/views/classroom/detail.vue | head -40 || true
grep -n hideFooter src/router/index.ts | head -40
```

- [ ] **Step 2: 回归表（执行并填结果）**

| # | 路径 | 期望 | 结果 |
|---|------|------|------|
| 1 | P1 `/login` | token 卡片 | |
| 2 | P1 `/classroom` | PageShell | |
| 3 | P1 工作台 | 无 footer、高度够 | |
| 4 | `/exam/question-bank` | Header+Table+Empty | |
| 5 | 课堂考试列表 | 壳统一 | |
| 6 | 考试作答 | 全高、可滚动题面 | |
| 7 | `/project` | 列表节奏 | |
| 8 | `/admin/dashboard` | 卡片栅格 | |
| 9 | 教师/学生管理 | 表头+筛选+表 | |
| 10 | 1280/1920 | 无意外横滚 | |

环境不可达 → 结构静态 + BLOCKED，不得写「真实通过」。

- [ ] **Step 3: 可选 antd-theme.css**

若仅 `main-test.ts` 引用：删除 import 或文件加文件头 `/* legacy test-only; prefer tokens.css */`。主 `main.ts` 禁止引入。

- [ ] **Step 4: commit**

```bash
git add -A frontend/src frontend/scripts  # 仅实际改动
git commit -m "chore(ui): p2 regression gates and leftover css hygiene"
```

若无文件变更，写报告即可不空 commit。

---

## Self-Review（plan vs design §14）

| §14 要求 | Task |
|----------|------|
| Slice 0 遗留 + hideFooter | Task 1 |
| 考试中心 | Task 2 |
| 课堂考试/成绩/作答 | Task 3 |
| 资源/云盘/分析 | Task 4 |
| 项目实训 | Task 5 |
| 管理后台 | Task 6 |
| 回归 | Task 7 |
| 不作 ML/BI 内核、不删 copilot alias（P3） | 全 plan 遵守 |
| exam-take 高度 | Task 3 Step 3 |
| Admin 双 padding | Task 6 Step 1 |

---

## 执行方式

1. **Subagent-Driven（推荐）** — 每 Task 独立 subagent + review  
2. **Inline Execution** — 本会话连续执行  

**建议分支：** `feat/ui-upgrade-p2`（从已含 P1 的 `main` 或 `feat/ui-upgrade-p1` tip 拉出）。
