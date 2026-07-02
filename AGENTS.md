# 慧学

> 项目英文/内部名 慧学,中文工作目录沿用 `huixue-yuanban`(历史遗留)。本文档及一切验收/汇报场景以 慧学 为准,不再使用「慧学」/「慧学元伴」中文名。

AI 教学平台后端 + 前端。

## 技术栈

- 后端: Python/FastAPI + PostgreSQL + Redis
- 前端: Vue.js + TypeScript
- 部署: Docker Compose

## 项目结构

```
backend/          FastAPI 应用
frontend/         Vue.js 前端
deploy/           部署脚本和 Docker 配置
tests/            自动化测试
content_orchestrator/  内容编排系统
scripts/          工具脚本
```

## 工作汇报纪律 (慧学 项目硬约束)

1. 声明"N 关完成"时必须附学校 DB 真实 SELECT 结果作证据:
   `ssh <慧学运维账号>@<慧学服务器1-IP> "sudo docker exec <慧学-DB容器名> psql -U huixue -d huixue -c 'SELECT COUNT(*) FROM tasks WHERE practice_id = X;'"` — 数字不对立即返工, 不允许后续补齐。

2. 遇到环境阻塞 (SSH 断, DB 连不上, 网络超时等) 必须立即停下汇报阻塞现象, 不得自行 fallback 到本地环境继续任务。fallback 本地继续 = 伪造完成汇报。

3. 汇报中不得使用措辞宽泛的状态描述 (如"DB 容器被重置"、"从零重装") 而没有具体证据。必须贴具体命令输出。

---
## Evaluator 攻击验证标准 (慧学 v2 自动循环)

每关 evaluator 入库前必须通过 4 种攻击验证 + 5 条 test_cases 红线。
不达标即视为 evaluator 不合格, 必须重写, 不允许入库。

### 4 种攻击全过 (每个 ≥80% test fail)

| 类型 | 学生提交模式 | 期望 |
|------|------------|------|
| A. Stub | pass / return None | 100% fail |
| B. Hardcode | 数值常量 / dict 全 0 / array zeros | ≥80% fail |
| C. Shape-only | 对的 shape 错的内容 (eye/zeros) | ≥80% fail |
| D. Identity | transform 类直接 return X 不变换 | ≥80% fail |

### 5 条 test_cases 红线

1. 每函数至少 3 个独立输入 (不只测 1 个边界)
2. 每函数至少 1 个边界用例 (空 / None / 极值 / 单元素 / 全相等)
3. 每函数至少 1 个负例 type 断言 (错类型应 raise / 特定 sentinel)
4. 数值断言用 `abs(x - expected) < tolerance`, 禁止 `==` 浮点严格相等
5. dict / list 返回断言所有 key / element, 不只验长度

### 每关 evaluator 必输出 2 张表

[关卡 X] 攻击表 (Pass / Fail / 通过阈值)
[关卡 X] 红线表 (5 列 × 每个测试函数, ✓ / ✗)

入库前贴这 2 张表, 哪一格 ✗ 就重写。

### 跨关泄题红线 (handbook + docstring)

- 学生 docstring 不写算法公式 / 算法步骤 (如 K-Means++ 伪代码、AdaBoost 权重更新公式), 只写"返回什么"
- 关 N 的 handbook 不出现关 N+k 的算法名称 (如 MJ01 不提 XGBoost / K-Means / Apriori 等后续算法)
- handbook 不内嵌完整可运行参考实现, 只用伪代码 + 公式 + 提示
---

## fc 协议下 student 函数约定 (阶段 2 P1 决策)

JSON 反序列化限制导致以下 type 边界:

- args/kwargs 总是 JSON 反序列化产物 (list 不是 tuple, dict 不是 frozenset)
- student 函数不做严格 `isinstance(args, tuple)` / `isinstance(args, frozenset)` 检查
- 接受 (list, tuple) / (list, set, frozenset) 双/多类型 duck typing
- 学生函数内部如需 frozenset/tuple 用 `frozenset(args)` / `tuple(args)` 转换

测试用例在 fc 协议下无意义不入 task_tests:

- `raises_on_non_<strict_type>` 类 (如 `raises_on_non_tuple`, `raises_on_non_set`) — 协议下 input 永远是 list, 此 case 无意义
- type-strict 反例 (test_xxx_wrong_type) 同理

frozenset/set 处理:

- 输入端: 学生函数内部 frozenset() 转 (handbook 教学合理)
- 输出端: fc 协议当前不支持 frozenset 返回值 (待阶段 3 _values_equal 升级)
- 输出 frozenset 的关 (如 MJ09 F4) 推迟阶段 3 与 5 综合关一起处理

tuple-key dict 输出限制 (E 类):

JSON 不支持 tuple 作 dict key (`json.dumps({(a,b): 1})` 抛 TypeError)。
fc 协议下学生函数返回 `Dict[tuple, V]` 不可表达。

修法: 函数跳过 task_tests, 推迟阶段 3 _values_equal 升级。
不要把 tuple key 改成字符串 key (例如 `"a|b"`) — 破坏 handbook 教学语义。
已知触发关: BD05 F4 compute_co_occurrence (返回 `Dict[Tuple[str,str], int]`)。
---

## 测试与部署铁律(不可商讨)

### Codex 课程产品验收命令

当用户要求验收课程/实训,或调用 `/huixue-course-auditor <课程或实训名称>` 时,必须使用项目内规则文件:

- Codex 镜像: `.codex/commands/huixue-course-auditor.md`
- Claude Code 原命令: `.claude/commands/huixue-course-auditor.md`

该命令的硬约束高于普通本地测试习惯:学校真实环境是唯一验收证据来源,覆盖率必须诚实声明,三路由 canary 与 Z1 三剑客必须执行。若 SSH、学校 API、Codex Browser Use/Tailscale 任一阻塞,立即停下汇报阻塞现象,不得 fallback 到本机环境继续验收。

### 1. 测试边界:学校服务器是唯一证据来源

慧学 产品测试**必须在学校真实环境执行**,通过 Tailscale 隧道访问:

- Web UAT: Codex Browser Use 访问 `http://<慧学服务器1-IP>:3000`(学校 frontend 真实地址)
- API 测试: 真打学校 backend `<慧学服务器1-IP>:8000`(或 nginx proxy)
- DB 验证: SSH `<慧学运维账号>@<慧学服务器1-IP>` → `docker exec huixue-db psql ...`
- 评测器验证: 学校真实 docker container 跑 v2 fc / pytest_module / io_based 三路由
- 学生/教师视角: student1 / teacher1 / admin 真账号在学校 frontend 登录

**禁止行为**:
- 本机起 backend / 本机 sqlite / 本机 docker 跑测试,然后报"功能验证通过"
- 用 mock 数据 / fixture 数据替代学校真实 DB 查询结果
- "代码 review 通过"作为测试证据
- "本地单元测试 100% 通过"作为产品 UAT 结论

**理由**:学校真实环境含 musl 容器 / 真实 DB schema / 真实 classroom_courses 数据 / 真实 frontend nginx 路由 / 真实 Tailscale 网络。任何本地环境差异(镜像不同 / 包版本不同 / DB 数据不同 / 路由配置不同)都会让本地测试结论与生产结论脱钩。本 session 多次"backend 修了 frontend 不调"问题就是脱钩典型,只有学校真实环境验证才能发现。

### 2. 修复路径:本地开发 → 同步学校 → 学校部署

所有产品改动严格遵守三步:

**Step 1 — 本地开发**
- 在本地 git 仓库写代码 / 改 SQL
- 本地通过 lint / py_compile / 单元测试基本检查
- git commit(commit message 包含 scope + 修复链路 + 影响面)

**Step 2 — 同步学校**
- 所有更新统一使用阿里云 OSS 中转,禁止再用 `scp` / `rsync` / SSH stdin 直传大文件到学校服务器。
- 本地先将部署包上传到 OSS,学校服务器再通过 `curl`/`ossutil` 从 OSS 下载到 `/tmp`,并用 sha256 校验后部署。
- OSS bucket: `<慧学OSS-Bucket>`
- OSS endpoint: `oss-cn-chengdu.aliyuncs.com`
- OSS bucket domain: `<慧学OSS-Bucket域名>`
- CNAME domain: `<慧学OSS-CNAME域名>`
- OSS 凭据只从本机私有配置或环境变量读取,不得写入 git 文档/commit/日志。建议变量名:
  `ALIYUN_OSS_ACCESS_KEY_ID`, `ALIYUN_OSS_ACCESS_KEY_SECRET`, `ALIYUN_OSS_ENDPOINT`, `ALIYUN_OSS_BUCKET`。
- backend/frontend/SQL 部署包建议命名为:
  `oss://<慧学OSS-Bucket>/deploy/huixue/<timestamp>-<commit>-<artifact>.tgz`。

**Step 3 — 学校部署 + 实证**
- backend: `docker restart huixue-backend` + `curl /health` + canary 真跑(任意 v2 fc 关 stub 0/total)
- frontend: nginx assets 替换 + 验证 Codex Browser Use 看到新 hash 文件
- SQL: 学校 docker exec psql 跑 + SELECT 验证结果
- 写入飞书 / KNOWN_ISSUES.md 部署日志:commit hash + 部署时间 + 实证证据

**禁止行为**:
- SSH 进学校容器直接 vim 改文件(无 git 追溯,下次部署被覆盖)
- 本地改 + 本地起服务测试 + 报"修复完成"(没经过学校部署)
- 部署后跳过 canary 直接报"已部署"
- 部署日志只记 commit hash,缺学校实证

**理由**:本 session 经历过容器版本与本地 git HEAD drift 36+ 行的 ImportError 部署事故。本地 git 必须是真相唯一源,学校部署必须可重现可回滚,部署后必须真实证据(SSH 输出 / Codex Browser Use 截图或 DOM 证据 / API 200 + 数据正确)。

### 3. 报告纪律

Codex 报"已修复 / 已验证"时必须满足:

- ✅ commit hash 来自本地 git
- ✅ 部署命令明示是学校真容器(`<慧学运维账号>@<慧学服务器1-IP>` 或 `docker exec huixue-backend`)
- ✅ 实证证据来自学校真实环境(SSH 输出 / Codex Browser Use 截图或 DOM 证据 / 学校 API curl 返回 / 学校 DB SELECT)

任意一项缺失,Jim 直接拒收,要求 Codex 走完整三步重测重报。

---

## 本地 Web 测试闭环（当前工作树执行约束）

当你要求在当前工作树里进行端到端验收时，先按以下顺序执行：

1) **本地真实浏览器链路（browser-harness）**
- 优先使用本机真实 Chrome/CDP 打开环境地址并逐步完成用户操作。
- 目标必须是“真实用户链路走通”，包括：打开页面、登录、执行动作、触发接口、等待结果、确认可见状态。
- 需要记录每一步的真实观察（文本、按钮状态、弹窗、返回内容）。
- 发现特殊组件/交互后，优先沉淀到 `agent_helpers.py` 或 `domain-skills/huixue/`，并说明为什么需要 helper（普通 DOM 操作不稳）。
- 严禁用 helper 跳过业务流程（不能改 DB / localStorage / 前端状态 / evaluator 接口）来伪造成功。

2) **Playwright MCP 结构化确认**
- 在关键页面读取可访问性快照，确认稳定可用的定位方式（优先 role/name/label/text/testid）。
- 用于确认可复用 locator、toast、modal、表单、列表、导航等关键元素。
- 页面定位器不稳定时，在报告里明确说明，并仅建议添加 `data-testid`，不主动为了通过测试修改业务代码（除非本轮明确要求修代码）。

3) **Playwright Test/CLI 作为最终闸口**
- 使用真实用户入口生成或更新 `tests/e2e/*.spec.ts`（示例名保留 `tests/e2e/...spec.ts`）。
- 仅将最终 PASS 建立在 Playwright Test 的实际执行结果上。
- 用例必须包含真实断言，不得只判断 URL 或页面存在；不得只看“未崩溃”。
- 失败时保留可复现线索（trace/screenshot/console/network）。

4) **失败时诊断（Chrome DevTools MCP / Trace）**
- 若链路或 spec 失败，至少检查：
  - console error
  - network failed/非 2xx
  - HTTP status
  - request payload / response body
  - DOM 跳转与状态变更
  - toast/modal/error、evaluator 返回
- 优先判断是登录态、权限、数据、路由、nginx、后端容器、数据库字段、前端状态问题中的哪类。

5) **金丝雀诚实度验证**
- 以下场景必须执行至少一次最小金丝雀失败验证（以确认未绕过失败）：
  - 首次接入新环境
  - 首次测试该类关卡
  - 新 helper/domain-skills 修改
  - 测试基础设施变化
- 方法可包括：故意错误答案触发失败、无权限账号验证拒绝访问、故意断言错误结果，要求能诚实返回失败。

6) **验收产物（最终输出）**
- 结论必须只选其一：`真实通过` / `真实失败` / `工具或环境阻塞，无法判断`。
- 必须列出执行链路、工具使用记录、证据清单、沉淀资产、失败分析（若失败）。
- 失败分析至少包含：失败步骤、用户可见症状、证据、最可能根因、修复建议、建议重跑测试。
- 证据优先级：真实 UI 结果 > DOM/快照 > network/控制台 > Playwright CLI 日志。

7) **环境边界说明（当前工作树）**
- 本轮在本地工作树中完成本地浏览器 + 本地服务链路验证，不在学校服务器上执行。
- 以上规则用于此轮验收流程执行；涉及学校生产/真实环境约束的规则仍保留原有优先级，不在当前轮次强制执行学校链路验证。
