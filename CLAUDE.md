# 慧学

> 本项目于 2026-07-02 从 慧学(仓库 `huixue-yuanban`)独立分家而来,是历史全新切断的独立项目,与原仓库互不影响。项目正式名称恢复为「慧学」,工作目录为 `huixue`。本文档及一切验收/汇报场景以「慧学」为准。

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

## 工作汇报纪律 (慧学项目硬约束)

1. 声明"N 关完成"时必须附本地 DB 真实 SELECT 结果作证据(本地 Docker Compose 起的 DB 容器):
   `docker exec <本地-DB容器名> psql -U huixue -d huixue -c 'SELECT COUNT(*) FROM tasks WHERE practice_id = X;'` — 数字不对立即返工, 不允许后续补齐。

2. 遇到环境阻塞 (DB 连不上, 依赖装不上等) 必须立即停下汇报阻塞现象, 不得静默跳过继续任务、不得凭假设编造结果。

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

### 1. 测试边界:本地环境是唯一证据来源

慧学项目当前**禁止访问学校服务器**,产品测试只在本地环境执行(本地 Docker Compose 起 frontend/backend/DB):

- Web UAT: Chrome MCP 或浏览器访问本地 frontend(如 `http://localhost:3000`)
- API 测试: 打本地 backend(如 `http://localhost:8000`)
- DB 验证: 本地 `docker exec <本地-DB容器名> psql ...`
- 评测器验证: 本地 docker container 跑 v2 fc / pytest_module / io_based 三路由
- 学生/教师视角: 本地测试账号登录

**禁止行为**:
- "代码 review 通过"作为测试证据
- 声称功能通过却没有实际运行结果(命令输出/截图/DB SELECT)佐证

### 2. 开发路径:本地开发 → 本地验证 → git commit

所有产品改动遵守:

- 在本地 git 仓库写代码 / 改 SQL
- 本地通过 lint / py_compile / 单元测试 / 本地环境集成测试
- git commit(commit message 包含 scope + 修复链路 + 影响面)
- 不需要同步/部署到任何远程服务器

**禁止行为**:
- 报"已修复/已验证"却没有本地真实运行证据
- 部署日志只记 commit hash,缺本地实证

### 3. 报告纪律

Claude Code 报"已修复 / 已验证"时必须满足:

- ✅ commit hash 来自本地 git
- ✅ 实证证据来自本地真实运行(命令行输出 / Chrome MCP 截图 / 本地 API curl 返回 / 本地 DB SELECT)

任意一项缺失,Jim 直接拒收,要求 Claude Code 补齐证据重报。
