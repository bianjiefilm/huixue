---
allowed-tools: Read, Bash, Grep, Glob
argument-hint: <课程或实训名称> [--role=teacher|student|all] [--mode=sample|deep]
description: 慧学 课程产品验收员 v2 - 学校真实环境双角色 + 双协议 + Z1 三剑客 + 分级 P0/P1/P2
---

# 慧学 Course Production Auditor v2

> **v2 重写日期**: 2026-04-29 · 取代 v0(本机 ziyuan_data 为 SSOT 的旧 SOP)
> **快照基线**: v2.7 业务快照最终态 = 8 课程实践 + 10 项目实训 BI = 18 门,外加 R5 项目实训代码关 49/49(业务课程数不等于 DB row count)

---

## CRITICAL: 三条不可破规则

1. **学校真实环境是唯一证据来源** — 本机起服务、本机 sqlite、本机 docker 跑测试**不算**验收证据。详见根目录 `CLAUDE.md` §「测试与部署铁律」。
2. **覆盖率诚实声明** — 抽样了几关就报几关,禁止用 5/12 推论 12/12。
3. **协议覆盖、Z1 三剑客必跑** — 单门验收即使抽样,当前课程涉及的 `function_call` / `pytest_module` canary + Z1 三类断言不允许跳。

---

## 0. 学校访问与账号

| 资源 | 访问方式 |
|---|---|
| Frontend | Codex Browser Use → `http://100.74.141.3:3000` |
| Backend API(nginx) | `http://100.74.141.3:3000/api/v1/...` |
| Backend API(容器内) | nginx `/api` → Docker service `http://huixue-backend:8000` |
| DB | `ssh huixueops@100.74.141.3` → `sudo docker exec 743a1e751097_node1-data_db_1 psql -U huixue -d huixue` |
| Backend 容器 | `sudo docker exec huixue-backend sh -c "..."`(musl,**无 bash**,只能 `sh`) |

| 角色 | 账号 | 密码 |
|---|---|---|
| 管理员 | `admin` | `admin123` |
| 教师 | `teacher1` | `teacher123` |
| 学生 | `student1` | `student123` |

> **本机 ziyuan_data/** 是开发素材,**不作为验收证据**。验收员只看学校 DB / API / Frontend 三者一致性。

### 0.1 v2.7 业务快照最终态(写死值)

- 课程实践: **8 门**(Python / Spark / 数据挖掘 / 数据清洗 / 数据采集 / 神经网络 / CV / 大数据)
  - 全部 v2 `function_call` 协议单关 + 5 综合关 + Spark12 `pytest_module`
  - 协议层已统一为 v2 evaluator
- 项目实训 BI: **10 门**(校情 / 人力 / 财报 / 风电 / 光伏 / 电商货品 / 电商BI / 某零售 / 公募基金 / 企业用能)
  - Stage 3 已补齐真实开源数据集引用,前端详情页均显示数据集资源
- R5 项目实训代码关: **49 关**(9 方向 + 4 扩展)
  - C0 能力层完整: `training_code_tasks` / `training_code_task_tests` / `training_code_task_evaluation_results`
  - 学生 workspace / 教师 grading / 评测结果落库均已闭环
- 合计: **18 门 + 49 R5 关**
- demo-ready: **✓ 真完美无瑕**(无 P0/P1/P2 阻塞,仅 6 个 P3 / 架构观察项)

注:大数据课程在 DB 中拆为 12 个 `practice` 行(`id=12-23`),业务计 1 门。Phase 3.2 验收使用 **published 口径**:`published_practices=20 / bi_training=10 / coding_training=0`。`published_practices` 按 `practices.direction != '项目实训'` 统计,当前真实 direction 为 `后端开发` + `大数据`,没有字面量 `课程实践`。`bi_training` 计数必须限定 `designer_type='BI'`,排除 R6+ AI/Jupyter 试点污染基线。`coding_training` 只统计 `practices.direction='项目实训'`,不查 R5 的 `training_code_tasks`。`practices` 总行数当前为 21,包含 XQ01 `id=24`、`publish_status=DRAFT`,不计入 published 基线。

---

### 0.2 已治理 commit 索引

| 主题 | Commit | 结果 |
|---|---|---|
| grading Z1 RBAC | `382010d` | 7 endpoint teacher/admin RBAC 与 path 防伪 |
| 5 综合关 `pytest_module` | `81a787b`, `0ea46ca` | MJ12 / NN12 / CV12 / WX12 / BD12 上线 |
| Spark12 `pytest_module` | `59e3613` | Spark12 31 cases 上线 |
| Python/Spark/数据采集 v2 化 | Stage 2 批次 commits | 旧协议关全部转 `function_call` |
| 教师成绩 cc_id 合同 | `60becb3` | Python / 大数据 grades UI 闭环 |
| challenge route reload | `2f8e0d1` | 直接打开 / SPA 切关均重新加载 task |
| add-to-classroom Z1 | `7ce510b` | training 加入课堂 RBAC + ownership |
| Stage A 收官签字 | `7a98f68` | 18/18 demo-ready 文档收官 |
| Stage B UAT P3 findings | `88410e3` | UAT 后仅余 P3 / 架构观察项 |
| Stage C R5 设计文档 | `a240302` | R5 49 关生产设计定稿 |
| challenge route loading race | `a1b8db1` | 课程实践直达路由 race condition 治理 |
| R5 4 按钮 UI 完整性 | `e9f46cc`, `2418113`, `97f0406` | R5 workspace 四按钮 + click 触发 + P1 清理 |
| Stage 3 数据集补全 | DB 变更 | 104 / 112 / 113 `superset_dataset_refs` 非空并前端可见 |
| R5 49 关生产 | 38+ R5 实施 commits | 9 方向 + 4 扩展全部入库并 Browser 闭环 |

### 0.3 KNOWN_ISSUES 当前索引

截至 2026-05-03,`KNOWN_ISSUES.md` 无 P0/P1/P2 阻塞项,仅 6 个 P3 / 架构观察项:

1. pytest sandbox 无网络/文件隔离(架构观察)。
2. logging WARNING 输出无 handler(可观测性)。
3. 学校 DB 容器历史漂移(运维清理)。
4. CV 课程实践 UI 无补打分入口(cosmetic)。
5. auditor Z1 示例 endpoint 路径陈旧(文档维护)。
6. add-to-classroom malformed body 先触发 422(FastAPI 一致性观察)。

### 0.4 测试覆盖维度

慧学 最终验收覆盖以下维度:

1. **评测协议层**:8 门课程实践 92 关 + R5 49 关,全部 `function_call` / `pytest_module`。
2. **数据流闭环**:8 门课程实践 grading + R5 training code grading 全闭环。
3. **Z1 安全**:6 处 RBAC / ownership / path 防伪覆盖,endpoint 防越权。
4. **UI 完整性**:直达路由、SPA 切关、Monaco 装载、提交评测、4 个编辑器按钮均完成真实 Browser UAT。
5. **开源数据集**:风电 / 光伏 / 公募基金使用真实开源数据集驱动,其余 BI 资源详情完整可见。

### 0.5 下次 session 启动条件

1. 学校 frontend / nginx API 可达:`curl -X OPTIONS http://100.74.141.3:3000/api/v1/auth/login` 返回非 `000`。
2. Phase 3.2 SQL row count 仍为 published 口径 `20 / 10 / 0`(`practices` 总行数 21 含 XQ01 DRAFT,不计入)。
3. 业务快照仍为 `18 门 + 49 R5 关`。
4. `KNOWN_ISSUES.md` 无 P0/P1/P2 阻塞项;若 UAT 发现回归,先写入后修复。

---

## 1. 双协议 evaluator(写死,以代码为准)

| 路由 | code_executor.py 入口 | 协议版本 | 适用关 |
|---|---|---|---|
| `function_call` | `:447 execute_function_call_code` | V2 fc | 课程实践单关 |
| `pytest_module` | `:748 execute_pytest_module` | V2 综合 | 6 综合关:MJ12 / NN12 / CV12 / WX12 / BD12 / Spark12 |

> Stage 2 决策:Spark12(task_id=37) 补 `pytest_module`,测试模块 `test_spark12_comprehensive.py`,学生模块 `student_spark12`,31 cases。实现约束:ref/test/student 均不 import pyspark;`estimated_size=sum(len(json.dumps(row, sort_keys=True, ensure_ascii=False)) for row in partition_rows)`;推荐权重只允许实现内部使用,handbook/docstring/test 不泄露具体数值。
> 如本节与 `code_executor.py` 不一致,**以代码为准**,并提 PR 同步本文档。

---

## 2. 3 套 grading endpoint(行号截至 2026-04-29 grep)

| Endpoint | 文件:行 | Frontend 真调 | 用途 |
|---|---|---|---|
| `GET /teachers/.../submissions` | `grading.py:52 get_submissions` | 否 | 教师拉某关提交列表 |
| `POST /teachers/.../grade` | `grading.py:84 submit_grade` | 部分 | 教师补打分写入 |
| `GET /grades/classrooms/.../grades` | `grades.py:29 get_course_grades` | 否 | 旧版课程成绩(兼容) |
| **`GET /classrooms/{cid}/courses/{cc_id}/grades`** | **`classrooms.py:1493 get_course_grades`** | **是 ✓** | **frontend `course-grades.vue` 唯一调用,Phase C-2 真融合 fc** |
| 实现层 | `crud.py:9512 get_course_grades_with_stats` | — | 融合 SCP + TaskEvaluationResult,8 status alias 在此 |

> 行号会因 commits 漂移。出现验收异常先重 grep:
> ```bash
> ssh huixueops@100.74.141.3 'sudo docker exec huixue-backend sh -c "grep -nE \"def get_submissions|def submit_grade|def get_course_grades|def get_course_grades_with_stats\" /app/app/api/v1/endpoints/grading.py /app/app/api/v1/endpoints/grades.py /app/app/api/v1/endpoints/classrooms.py /app/app/crud/crud.py"'
> ```

### 8 status filter alias(`crud.py:9512` `get_course_grades_with_stats` 的 `status` 参数)

| alias | 实际状态 | 含义 |
|---|---|---|
| `completed` | SCP COMPLETED | 已完成(任意时间) |
| `completed_on_time` | SCP COMPLETED_ON_TIME | 按时通关 |
| `completed_late` | SCP COMPLETED_LATE | 逾期完成 |
| `late_completed` | 同 `completed_late` | 别名 |
| `not_completed` | 任何非完成状态 | 未通关 |
| `not_started` | NOT_STARTED | 未开始 |
| `learning` | 部分通关 | 学习中 |
| `all` | 不过滤 | 全部 |

---

## 3. Phase 0 — 启动检查(MANDATORY)

### 3.1 Tailscale + 浏览器
```bash
# 验证学校 nginx /api 可达;404/405 也可接受,只要不是 000
curl -s -o /dev/null -w "%{http_code}" -X OPTIONS http://100.74.141.3:3000/api/v1/auth/login
# 期望: 非 000
```
然后用 Codex Browser Use `iab` backend 取当前 in-app browser tab,导航到 `http://100.74.141.3:3000`。

### 3.2 实查待审课程 row count(诊断用,不代表业务课程数)
```bash
ssh huixueops@100.74.141.3 'sudo docker exec 743a1e751097_node1-data_db_1 psql -U huixue -d huixue -c "
SELECT
  (SELECT COUNT(*) FROM practices
   WHERE direction != ''项目实训''
     AND publish_status=''PUBLISHED'') AS 实践_practice_rows,
  (SELECT COUNT(*) FROM trainings
   WHERE visibility=''PUBLIC''
     AND is_published=true
     AND designer_type=''BI'') AS 项目实训BI_rows,
  (SELECT COUNT(*) FROM practices
   WHERE direction=''项目实训''
     AND publish_status=''PUBLISHED'') AS 项目实训代码_rows;
"'
```
注:学校 DB 容器名以 `docker ps` 实查为准。若文档名与真名不一致,先用 `sudo docker ps | grep postgres` 拿真名,然后 PR 同步本文档。
注:`practices` / `trainings` 表无 `deleted_at` 字段,`publish_status` / `visibility` 即软删语义。`deleted_at IS NULL` 只用于 `tasks` 表。
注:验收值按 published 口径为 `20 / 10 / 0`;`published_practices` 按 `practices.direction != '项目实训'` 统计,当前真实 direction 为 `后端开发` + `大数据`,没有字面量 `课程实践`。`bi_training` 必须限定 `designer_type='BI'`,排除 R6+ AI/Jupyter 试点污染基线。`coding_training` 只统计 `practices.direction='项目实训'`,不查 R5 的 `training_code_tasks`(`is_published=true` 当前 49 关,属于 R5 能力层,非 Phase 3.2 三维基线)。`SELECT COUNT(*) FROM practices` 当前为 21,额外 1 行是 XQ01 `id=24` 且 `publish_status=DRAFT`,不计入 Phase 3.2 基线。R6 AI 试点入库后,`trainings` 表总行预期为 16(10 PUBLIC BI + 5 PRIVATE 历史 + 1 R6 AI 试点 FUND-CHURN),验收以 `visibility/is_published/designer_type` 三联限定为准。

期望 row count: `20 / 10 / 0`。row count != 业务课程数。大数据 1 门 = 12 个 `practice` 行。业务快照见 §0.1 最终态(`18 门 + 49 R5 关`)。若项目实训代码 rows 不为 `0`,说明项目实训代码测试包状态回漂,Phase 0 阻塞。

### 3.3 取本次待审对象的 ID
```bash
# 实践课程
ssh huixueops@100.74.141.3 'sudo docker exec 743a1e751097_node1-data_db_1 psql -U huixue -d huixue -c "
SELECT id, title, direction, publish_status FROM practices WHERE title LIKE ''%<课程名>%'';
"'

# 实训
ssh huixueops@100.74.141.3 'sudo docker exec 743a1e751097_node1-data_db_1 psql -U huixue -d huixue -c "
SELECT id, title, visibility, is_published FROM trainings WHERE title LIKE ''%<实训名>%'';
"'
```

### 3.4 产出 `.verify-checklist.md`(每次任务覆盖,不累积)
位置:仓库根 `.verify-checklist.md`(已加 .gitignore)。模板:
```markdown
# 验证清单(本次:<课程名> / <日期>)

## 预期(开测前填)
- 课程 ID / practice_id: ___
- 关数: ___
- 评测协议分布: function_call=__ / pytest_module=__
- 抽样关清单: ___
- Z1 三剑客 endpoint: ___

## 实证(逐条 ✅/❌)
- [ ] frontend 课程详情页可加载
- [ ] 学生抽样 N 关 stub canary 全部 fail (0/total)
- [ ] 学生抽样 M 关 ref 全部 pass (total/total)
- [ ] 教师 course-grades.vue 渲染 8 status filter
- [ ] Z1 匿名 401
- [ ] Z1 role 403
- [ ] Z1 path 篡改 403
```

---

## 4. Phase 1 — 教师角色验收(Codex Browser Use)

### 4.1 登录
导航到 `http://100.74.141.3:3000/login` → fill `teacher1` / `teacher123` → click 登录 → wait_for 工作台 → take_screenshot。

### 4.2 通用故事(精简,沿用 v0 风格)

| ID | 故事 | 验证方法 | 期望 |
|---|---|---|---|
| US-T-01 | 看课程列表 | DOM 抽 `.course-card` 数 | ≥ DB 真值 |
| US-T-02 | 进课程详情 | click 第 1 门,take_snapshot | 章节/关数与 DB 一致 |
| US-T-03 | 资料下载 | click handbook,wait_for 弹窗 | 非 404 |
| US-T-06 | 看实训列表 | 切实训 Tab | 列表非空 |
| US-T-07 | 进实训详情 | click,take_snapshot | datasets 列表非空 |

### 4.3 高风险细化(必跑)

#### US-T-FOCUS-1: grading 列表 + 8 status filter ⚠️
**验证页**: `course-grades.vue`(`frontend/src/views/course-grades.vue`)
**真调 endpoint**: `GET /classrooms/{cid}/courses/{cc_id}/grades`(`classrooms.py:1493` → `crud.py:9512`)

```javascript
// Legacy C2-A evaluate_script 示例;Codex Browser Use 当前无 evaluate 时使用附录 A C2-B
(function() {
  const filter = document.querySelector('select[name*="status"], .status-filter');
  return {
    filterFound: !!filter,
    options: filter ? Array.from(filter.options).map(o => o.value) : [],
    rows: document.querySelectorAll('.grade-row, tr[data-student]').length
  };
})()
```
**期望 options 含 8 个 alias**:`all / completed / completed_on_time / completed_late / not_completed / not_started / learning`(`late_completed` 是 alias 可不出现 UI)。
**逐 alias 切换**:`fill_form` 选每个 → `list_network_requests` 抓 `/grades?status=<alias>` → `get_network_request` 看 response.rows 计数,与 DB 直查比对(±0,不允许差)。

#### US-T-FOCUS-2: 教师补打分写入
**真调 endpoint**: `POST /teachers/.../grade`(`grading.py:84 submit_grade`)
- click 某学生某关 → 填分数 + 评语 → 保存
- `list_network_requests` 抓 POST 响应 200
- DB 验证:`SELECT * FROM student_course_progress WHERE student_id=X AND classroom_course_id=Y` → 看 `manual_score / graded_at / graded_by_user_id` 已写入
- 列表刷新:不刷页 reload 看分数是否更新(若需手动 refresh,记 P2)

---

## 5. Phase 2 — 学生角色验收(Codex Browser Use)

### 5.1 登录
切 Tab(或新 Page)→ `student1` / `student123` → 学生工作台。

### 5.2 通用故事

| ID | 故事 | 期望 |
|---|---|---|
| US-S-01 | 看课程列表 | 已加入课程显示 |
| US-S-02 | 进课程,看章节 | 章节顺序正确 |
| US-S-06 | 下载资料 | handbook/syllabus 200 |
| US-S-07 | 看成绩 | 数字与教师端一致 |
| US-S-08~12 | 实训(略,沿用 v0) | — |

### 5.3 高风险细化(必跑)

#### US-S-FOCUS-3: 进 task workspace + Monaco editor 提交能力
**当前(2026-04-29)工具栈状态**:Codex Browser Use `evaluate_script` 不可用(Phase 1 已验证 `hasEvaluate: undefined`),验收直接走附录 A C2-B。本节 C2-A evaluate_script 示例仅作为未来工具升级后的参考。

**验证页**: `task-detail.vue` / `workspace.vue`
- handbook_markdown 渲染 ≠ NULL
- Monaco editor 容器存在
- 当前提交动作走附录 A C2-B;未来若工具支持 evaluate_script,可参考下方 Monaco C2-A 注入:
```javascript
// Legacy C2-A evaluate_script 示例
(async function() {
  // 候选 1: window 全局
  let editor = window.__editor__ || window.editor;
  // 候选 2: 从 monaco 全局枚举
  if (!editor && window.monaco) {
    const editors = window.monaco.editor.getEditors();
    editor = editors[0];
  }
  // 候选 3: 从 Vue 组件(需要 __VUE_DEVTOOLS_GLOBAL_HOOK__ 或组件 ref 暴露)
  if (!editor) {
    const root = document.querySelector('#app').__vue_app__;
    // walk Vue tree to find editor instance — 项目首次实施时填具体路径
  }
  if (!editor) return { ok: false, reason: '无法定位 Monaco 实例,需查项目 hook 方式' };
  editor.getModel().setValue('def f(x):\n    pass');
  return { ok: true, current: editor.getValue() };
})()
```
> **当前执行**:提交按钮改用附录 A 的 SSH POST(C2-B fallback),Browser Use 只做真实 frontend 页面显示验证,记 P1 + 排期 C2-A 补打通。
> **未来工具升级**:若 evaluate 可用,再跑上面脚本确认 Monaco 路径。成功后把路径记录进项目根 `KNOWN_ISSUES.md` 「Monaco 注入路径」一节;该节截至 2026-04-29 视为 deprecated/备用入口。

#### US-S-FOCUS-4: evaluator 协议 canary(每种协议 ≥1 实证)
**对待审课程的关按协议分类,每种协议各跑 1 stub + 1 ref**:

| 路由 | stub canary 期望 | ref 期望 |
|---|---|---|
| `function_call` | `passed/total = 0/total` | `passed/total = total/total` |
| `pytest_module` | `passed/total = 0/total` | `passed/total = total/total` |

当前操作:按附录 A C2-B 用 SSH POST stub/ref,再用 Browser Use 验证真实 task workspace 显示。未来若 C2-A 可用,可升级为 Monaco 注 stub/ref → click 提交 → wait_for 评测结果 → DOM 抓 `passed/total`。
**stub/ref 两个学校 API 数字 + Browser Use 前端 task 页面证据**都贴出才算该路由 canary 通过。若前端没有最新提交结果面板,必须明示 Browser Use 只能证明页面/完成态,不能声称显示了 stub 0 分。

#### US-S-FOCUS-5: handbook / 数据集内容
- handbook_markdown 是否 NULL
- 实训 datasets 列表非空、可下载
- 任何"内容缺失"问题 → P1(列入 `KNOWN_ISSUES.md` 内容生产队列)

---

## 6. Phase 3 — Z1 安全三剑客(curl 必跑)

> 取本次课程任一 endpoint(推荐 grading 类),三剑客全跑。

### 6.0 Z1 helper(进 Phase 6 前先跑一次,缓存 token)
```bash
ANON_TOKEN=""
STUDENT_TOKEN=$(curl -s -X POST http://100.74.141.3:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"student123"}' | jq -r .access_token)
TEACHER1_TOKEN=$(curl -s -X POST http://100.74.141.3:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"teacher123"}' | jq -r .access_token)
```

### 6.1 匿名 401
```bash
curl -s -o /dev/null -w "%{http_code}" \
  http://100.74.141.3:3000/api/v1/classrooms/<cid>/courses/<cc_id>/grades
# 期望: 401
```

### 6.2 role 403(student token 调 teacher endpoint)
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  http://100.74.141.3:3000/api/v1/teachers/<tid>/practices/<pid>/tasks/<task_id>/submissions
# 期望: 403
```

### 6.3 path/query 篡改 403(teacher1 token 假冒 teacher_id)
```bash
# teacher1 真 id=4,用 teacher_id=999 假冒;不创建/删除任何测试账号
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $TEACHER1_TOKEN" \
  "http://100.74.141.3:3000/api/v1/teachers/999/practices/<pid>/tasks/<task_id>/submissions"
# 期望: 403
```

任一项 ≠ 期望状态 → **P0,整门 ❌**。

---

## 7. Phase 4 — 分级评估 + 完工判定(B6)

| 等级 | 定义 | 阻塞规则 |
|---|---|---|
| **P0** | 学生进不去 / 评测器 fail / Z1 防线漏 / 数据完全错 | **任 1 个 = 整门 ❌** |
| **P1** | 主流程 1 步卡住 / status filter 部分不工作 / Monaco 注入失败 / handbook NULL | **≥2 个 = 整门 ❌** |
| **P2** | 边角 cosmetic / 1 字段显示问题 / 需手动 refresh | 不阻塞,推 `KNOWN_ISSUES.md` |

**通过判定**:
- P0 = 0
- P1 ≤ 1
- 本门涉及的 evaluator 协议 canary 全过
- Z1 三剑客全过
- 抽样覆盖率诚实声明(例:"5/12 关 fc 抽样,7 关下次")

---

## 8. Phase 5 — 报告产出(B5)

### 8.1 飞书 Bitable(主归档)
- App token: `DobtbWMaTaClBxsmvSZcm0g4nEd`
- 表:验收记录表(若不存在新建)
- 字段:课程名 / 验收日期 / 抽样关 / 协议覆盖(function_call/pytest_module) / Z1 三剑客(✓/✗ × 3) / P0 数 / P1 数 / P2 数 / 结论(✓/✗) / 实证截图链接 / commit hash
- 写操作:`user_id_type: open_id`

### 8.2 本地 `.verify-checklist.md`
覆盖式更新(同一文件,每次新任务覆盖,不累积)。验收完后提交飞书前最后一稿。

### 8.3 报告必备实证(沿用 CLAUDE.md §1.2)
至少包含一项,**全部来自学校真实环境**:
- ✅ SSH 命令 + 学校 DB 输出原文
- ✅ Codex Browser Use 截图(教师/学生关键页面)
- ✅ `curl http://100.74.141.3:.../api/...` 真打学校 API 输出
- ✅ `docker exec 743a1e751097_node1-data_db_1 psql ...` SELECT 输出

不允许:"本地测试通过"/"代码 review 通过"/"本机单测 100%"作为产品 UAT 结论。

---

## 9. 工作流摘要

```
Phase 0: 学校可达 + Browser Use Tab + DB 实查现状 + 写 .verify-checklist.md
Phase 1: 教师角色(US-T-01..07 + FOCUS-1/2)
Phase 2: 学生角色(US-S-01..12 + FOCUS-3/4/5)
Phase 3: Z1 三剑客(curl × 3)
Phase 4: 分级 P0/P1/P2 + 完工判定
Phase 5: 飞书归档 + .verify-checklist.md 终稿
```

---

## 10. 使用示例

```
# 实践课程(默认抽样模式)
/tempo-course-auditor 神经网络与深度学习

# 项目实训
/tempo-course-auditor 某零售企业经营分析

# 仅教师端
/tempo-course-auditor 数据清洗 --role=teacher

# 全量(non-sample)
/tempo-course-auditor 数据挖掘分析 --mode=deep
```

---

## 11. 故障排除

### Codex Browser Use 连不上
1. 确认 Codex in-app browser 当前 tab 可打开 `http://100.74.141.3:3000`(Tailscale up)
2. 使用 Browser Use `iab` backend 读取当前 tab / DOM snapshot / screenshot
3. 若页面无法连接或超时,立即停下汇报阻塞,不得切到本机环境继续验收

### SSH/学校不通
**立即停下汇报阻塞**(CLAUDE.md §「工作汇报纪律」第 2 条),不得自行 fallback 到本机环境继续验收。

### Monaco 注入失败
按附录 A 的 C2-B 降级方案:SSH POST 学校 API 替代 Monaco 提交,Browser Use 只验证前端真实页面显示;并在 `KNOWN_ISSUES.md` 记 P1。

### 行号 grep 不到 / 函数改名
本文档 §2 已标"行号截至 2026-04-29 grep"。出现不一致时重跑 §2 备注里的 grep 命令,把新行号 PR 回本文档。

---

## 附录 A:C2-B 降级方案(Monaco 不可注入时)

适用条件:Codex Browser Use 能打开学校 frontend,能做真实 DOM click / screenshot,但不能执行页面 `evaluate_script` 或不能稳定注入 Monaco。此方案只替代"提交代码"动作,不替代学校真实环境验收。

### A.1 helper 模板

项目内 helper:

```bash
scripts/course_audit/c2b_helper.sh token
scripts/course_audit/c2b_helper.sh eval <task_id> <code_file> [user_id]
scripts/course_audit/c2b_helper.sh ui-template <practice_id> <task_id>
```

**注**:首次验收前若 helper 不存在,先 `mkdir -p scripts/course_audit` 并基于本节"等价核心逻辑"创建约 30 行 bash 脚本;后续验收复用同一路径。

等价核心逻辑:

```bash
ssh huixueops@100.74.141.3 '
  TOKEN=$(curl -sS -X POST http://localhost:3000/api/login \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"student1\",\"password\":\"student123\"}" |
    python3 -c "import sys,json; print(json.load(sys.stdin)[\"token\"][\"access_token\"])" )

  curl -sS -X POST "http://localhost:3000/api/v1/tasks/<task_id>/evaluate?user_id=5" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"code\": \"<json-escaped code>\"}"
'
```

说明:学校 host 当前不暴露外部 `:8000`,统一走 nginx `localhost:3000/api`。token 结构以学校真实 `/api/login` 返回为准,当前为 `token.access_token`。

### A.2 单门 9 步

1. SSH 到学校确认 API 入口:`curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/login`。
2. Browser Use 登录 `student1/student123`,确认右上角学生身份。
3. 准备 stub 代码文件与 ref 代码文件。
4. 跑 stub:`scripts/course_audit/c2b_helper.sh eval <task_id> <stub.py> | tee /tmp/<course>_stub.json`。
5. 记录学校 API JSON:`status=fail`,通过数/总数,score。
6. Browser Use 打开 `http://100.74.141.3:3000/#/course/challenge/<practice_id>/<task_id>`,截图确认 task title 与学生身份。
7. 跑 ref:`scripts/course_audit/c2b_helper.sh eval <task_id> <ref.py> | tee /tmp/<course>_ref.json`。
8. Browser Use 刷新同一 task 页面,截图确认 task title、学生身份、完成状态或可见评测结果。
9. 汇报"学校 API 输出 × Browser Use 前端显示"对照表。若前端没有提交历史/最新评测面板,必须明示限制:API JSON 是评测结果证据,Browser Use 只证明真实前端页面可访问并显示该 task/完成状态;不得声称前端显示了 stub 0 分。

### A.3 完成标准

- stub:学校 API 返回失败,且通过率 ≤20%。
- ref:学校 API 返回通过,且通过率 ≥80%。
- Browser Use:同一学生能打开真实学校 task workspace,页面标题与 task_id 对应;ref 后显示已通关或等价完成状态。
- 对已通关账号,stub 失败不会回滚前端"已通关"状态;这不是 ref 失败,但不能作为"前端显示 stub 0 分"证据。

---

## 附录 B:与 v0(本机 ziyuan_data 为 SSOT)的差异

| 维度 | v0 | v2 |
|---|---|---|
| SSOT | 本机 `ziyuan_data/` 文件 | 学校 DB / API / Frontend |
| 项目名 | Tempo(混用) | **慧学**(统一) |
| 课程数量 | 不明 | v2.7 快照 8+10=18 + 实查 SQL |
| evaluator 协议 | 未提 | function_call/pytest_module 按课程覆盖实证 |
| Z1 安全 | 未提 | 三剑客必跑 |
| grading endpoint | 未提 | 3 个全列 + 真调标识 + 行号 |
| 完工标准 | 通过/失败二元 | P0/P1/P2 分级 |
| 用户故事粒度 | 20 个全泛述 | 15 通用 + 5 高风险细化(grading×2/Monaco/协议 canary/数据缺失) |
| 报告归档 | 不明 | 飞书 + 本地 `.verify-checklist.md` |
| 工具 | 旧版 chrome-devtools + claude-in-chrome | Codex Browser Use + SSH C2-B |
