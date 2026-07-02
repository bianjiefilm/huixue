# Known Issues

> Last reviewed: 2026-05-05. 在线编码 UI 四按钮抽样测试的课程实践 P0 已由 `a1b8db1` 治理；R5 training code workspace P1 已由 `e9f46cc` + `2418113` 治理。BI designer 数据集下拉挂载已由 `4b0c808` 治理；真实 BI 字段绑定、画布渲染、预览、课堂保存与 reload 持久化已由 `8feee39` + `84babe1` 治理并在学校真实环境抽样验证。R6 Session N 已由 `0dacf1d` 完成 AI designer payload contract 与 training datasets 挂载修治；R6 AI Designer 真闭环 P1 已由 `f23bef1` + `45b0f16` + `e5ca918` + `799c14d` + `739f19a` 治理并经 Jim 复核截图通过。R6 Phase A/B/C 已完成第一阶段扩展: `0870398` backend 通用 `setRole` target 支持,`1548` 风电 + `1549` 校情 AI trainings 入库,并在学校真实环境完成 saved pipeline 加载、页面运行按钮、DB、logs、insights 闭环。

## Resolved: BI designer 真实 BI 闭环

- **Completed**:
  - `4b0c808 fix(bi-designer): load training datasets in workspace`
  - `8feee39 fix(bi-designer): render real dataset charts and classroom drafts`
  - `84babe1 fix(bi-designer): limit BI dataset payload for workspace rendering`
- **School Evidence**:
  - 学校 frontend: `index-C-edzrCd.js`、`bi-designer-B5WS_YUA.js`、`preview-M7VM603u.js` 均返回 `application/javascript`。
  - 学校 backend: `GET /api/v1/trainings/{id}/bi-dataset?limit=500` 返回真实 `columns + data`,避免 3MB+ 首屏阻塞。
  - 抽样 `112/104/109` 均通过 Browser Use DOM 真测: `canvasItemCount=1`, `chartCanvasCount=1`,字段列表显示真实列。
  - 抽样真值: `风电齿轮箱预警分析` 字段 `fault_id/turbine_id/...`; `公募基金精准营销案例` 字段 `customer_id/age/...`; `某高校校情管理分析案例` 字段 `course_id/credits/...`。
  - 预览页 `/preview/bi/109` 真渲染保存场景: `componentCount=1`, `chartCanvasCount=1`。
  - 课堂路径 `/classroom/100/training/109/bi-designer` 显示保存按钮,`POST /api/v1/bi/109/save` 成功落库 `training_bi_drafts id=69`, `snapshot_len=7124`; reload 后 `GET /api/v1/bi/109/detail?...student_id=5` 恢复图表。
- **Tool Boundary**: Tailscale/HTTP 下载较慢,本轮使用 Browser Use DOM、Performance resource、页面截图、学校 DB SELECT 组合证据；不使用本地环境替代学校验收。

## P3: pytest sandbox 无网络/文件隔离

- **Status**: 架构治理项,不阻塞当前课程实践与项目实训 demo。
- **Location**: `backend/app/services/code_executor.py` 的 `pytest_module` 执行路径。
- **Risk**: 当前 pytest_module 在 backend 进程空间执行学生代码,后续若面向不可信公开提交,需要容器级 `--network=none`、文件系统隔离与资源限制。
- **Next**: 进入下一轮安全架构治理时,优先评估复用 Docker sandbox / container manager。

## P3: logging WARNING 输出无 handler 抓取

- **Status**: 可观测性优化项,不影响功能正确性。
- **Location**: backend root logger / app loggers。
- **Risk**: `logger.warning()` 在部分路径中没有统一 stdout handler,攻击审计与异常提示不够稳定。
- **Next**: 在 `app/main.py` 或 uvicorn log config 中统一配置 StreamHandler。

## P3: 学校 DB 容器历史漂移

- **Status**: 运维清理项,不影响产品运行。
- **Observed**: `huixue-db` stopped 容器与当前运行中 `<慧学-DB容器名>` 同存。
- **Policy**: 文档与验收命令以 `docker ps` 实查为准；不擅自删除 stopped 容器。
- **Next**: 由运维窗口统一清点历史容器。

## P3: CV 课程实践 UI 无补打分入口

- **Status**: 教师体验 cosmetic,不阻塞 demo。
- **Observed**: CV `course-grades` 页详情按钮仍偏弱；API 补打分链路和成绩落库已验证可用。
- **Next**: 后续产品体验迭代时补 modal + form。

## P3: auditor Z1 示例 endpoint 路径陈旧

- **Status**: 文档/验收脚本维护项,不影响产品功能。
- **Observed**: Stage B UAT 中旧示例 `/api/v1/teachers/{teacher_id}/practices/{practice_id}/tasks/{task_id}/submissions` 返回 404；学校真实 route 为 `/api/v1/teachers/{teacher_id}/classrooms/{classroom_id}/courses/{course_id}/submissions`。
- **Evidence**: 真实 route 已验证匿名 401、student 403、teacher fake id 403。
- **Next**: 下次文档维护时同步 `.codex/commands/huixue-course-auditor.md` 与 `.claude/commands/huixue-course-auditor.md` 的 Z1 示例。

## P3: add-to-classroom malformed body 先触发 422

- **Status**: FastAPI 请求体验/安全一致性观察项,不影响有效请求 RBAC。
- **Observed**: `POST /api/v1/trainings/library/{training_id}/add-to-classroom/{classroom_id}` 缺少 `start_time/end_time` 时返回 422；提供合法 body 后,student 为 403,teacher 操作非己课堂为 403。
- **Next**: 若要做到无效 body 也先走 RBAC,需将请求体改为延迟校验或在依赖层前置认证包装。

## P3: 命令行实践内容缺失

- **Status**: 内容覆盖观察项,不阻塞当前 demo。
- **Observed**: 学校 DB published tasks 中无 `env_type` 为 `shell` / `bash` / `terminal` / `cmd` / `cli` 的命令行实践 task,也无命令行/终端/Linux/运维方向课程命中。
- **Frontend Evidence**: `frontend/src/views/course/challenge/detail.vue` 与 `frontend/src/components/editor/TerminalEmulator.vue` 已有 `envType === 'shell'` 的命令行终端 UI 和“重置命令行”入口。
- **Impact**: 当前无法在学校真实环境执行命令行实践“重置命令行”UAT;不应造测试 task 伪造覆盖。
- **Next**: 若产品路线需要命令行实践,先补真实 `shell` 类内容与后端 reset-terminal 链路,再按学校真实环境重跑 UAT。

## P3: 云桌面实践内容缺失

- **Status**: 内容覆盖观察项,不阻塞当前 demo。
- **Observed**: 学校 DB published tasks 中无 `env_type` 为 `desktop` / `vnc` / `cloud` / `vm` / `gui` 的云桌面实践 task,也无云桌面/桌面/VNC 方向课程命中。
- **Frontend Evidence**: `frontend/src/views/course/challenge/detail.vue` 已有 `envType === 'desktop'` 的云桌面 UI,包含延时、剪切板、重置环境、重置任务、VDI iframe 等入口。
- **Resource Control Evidence**: 前端有实验资源管理、环境冲突弹窗、返回该实验/进入本实验流程;后端有 active environment 与多环境开关配置。但当前学校无云桌面/命令行 task,没有真实环境对象可执行资源控制 UAT。
- **Impact**: 当前无法在学校真实环境执行云桌面 4 按钮和多实验环境资源控制 UAT;不应造测试 task 或临时改资源配置伪造覆盖。
- **Next**: 若产品路线需要云桌面实践,先补真实 `desktop` 类内容和可启动环境资源,再按学校真实环境重跑云桌面与资源控制 UAT。

## P3: XQ01 历史遗留

- **Status**: Jim 已决议。项目实训校情入口真源 = `trainings.id=109` + `EDU-01~05` `training_code_tasks`。
- **Decision**: `practice id=24` + `task id=142` 保持 `publish_status=DRAFT`,不回灌前端,不新建 training,不双读。
- **Phase 3.2 Baseline**: `practices` 总行 21,`published` 20;XQ01 不计入 Phase 3.2 基线。

## P1 (Resolved): R6 AI Designer 真闭环

- **Status**: Resolved by `f23bef1` + `45b0f16` + `e5ca918` + `799c14d` + `739f19a`,Jim 复核截图通过。
- **累积修治**:
  - Backend run engine: `f23bef1` 实现 DAG 拓扑排序、节点状态推进、`node_executions` 落库。
  - Backend label leakage: `45b0f16` 修 `churn=1-subscribed` 时移除 `subscribed` 特征泄漏。
  - Backend GET pipeline + run fallback: `e5ca918` 收紧为 `status='saved'` 限定。
  - Frontend SVG/nodes-layer: `799c14d` 包回 `.flow-canvas` 并修 `transform-origin`。
  - Frontend layout: `739f19a` 把 `.config-panel` 放回 `.designer-body` 三列布局。
- **Jim 复核证据**:
  - 截图 `r6-n5-layout-fixed-739f19a.png` + `r6-n5-config-panel-739f19a.png` 通过。
  - 画布布局合理: 算子库左 / 画布中 (`1180x796`; 配置面板打开时 `860x796`) / 配置面板右 (`320x880`) / 底部 `flow-tabs` + 日志栏。
  - 6 节点位置在画布主体可视区,saved `y=90` 视觉合理,zoom=`86%`。
  - 5 条边真连线。
  - 配置面板真显示,字段绑定 `fund_customers.csv - 公募基金客户流失预测`。
- **跨 N+2/N+3/N+4/N+5 四轮复核记录**:
  - N+2 后端 run 修完,但 frontend 不加载 saved pipeline;Jim 复核截图发现。
  - N+3 frontend 加载 saved pipeline,但坐标错位;Jim 复核截图发现。
  - N+4 SVG 包回画布,但整体布局塌陷;Jim 复核截图发现。
  - N+5 layout 全修;Jim 复核截图通过。
- **现场保留**: FUND-CHURN `training_id=1547`, `saved_run_id=89ab7e54-221a-46a9-a270-1a67689bbf12` / `aa07a8d2`,saved scene 为 6 nodes / 5 edges。

## P3: Browser Use/Playwright 真鼠标点击节点不稳

- **Status**: 工具边界确认,等待 Jim 真浏览器最终判定。
- **Observed**: Codex N+5 中 `browser_click` / Playwright locator click 节点后 `selected=null`,`.config-panel display=none`;DOM `.click()` 触发后 Vue 真选中并显示配置面板。R6 Phase C 仍延续该边界,完整拖拽 + 表单逐项配置 + 真点保存未作为闭环依据。
- **R6 Follow-up Evidence**: Codex Playwright 真鼠标拖拽“读取数据”到 `.flow-canvas` 后节点数 `7 -> 7`;`browser_drop` 投递 `application/json` / `text/plain` 后节点数仍 `7`;真鼠标点击“设置角色”节点后 `.config-panel display=none`。
- **Likely**: 工具边界。当前 AI Designer 节点交互依赖 Vue 事件链和 pointer/mouse 事件组合,学生真浏览器使用大概率正常。
- **Resolution**: Jim 真浏览器测试如通过,关闭此 P3;如不通过,R6 后续修真实 click 事件链。
- **现场保留**: FUND-CHURN `training_id=1547` + saved runs `89ab7e54` / `aa07a8d2`。

## P3 (Resolved): R6 校情 1549 metrics 全 1.0 疑似标签泄漏

- **Status**: Resolved by `c265463 feat(ai-designer): support setRole features for explicit feature selection`。
- **Observed**: R6 Phase C 学校真测 `run_id=0559ebc0-e80a-4f9b-84d1-534715591dc6`,校情 `training_id=1549` 的 `accuracy / precision / recall / f1 / auc` 全部为 `1.0`。
- **Contrast**: 风电 `training_id=1548` 同一 backend 通用化链路返回合理指标: `accuracy=0.8989507154`, `auc=0.8555905983`。因此 backend `setRole + featureExtract + dataSplit + logisticReg + modelEval` 技术链路本身可运行。
- **Root Cause**: 学校真实 `scores.csv` 中 `grade_point > 0` 对 `pass` 为 `0` mismatch,`score >= 60` 只有 `2/30000` mismatch;原链路自动纳入 `score/grade_point`,导致标签泄漏。
- **Resolution**: backend `setRole.config.features` 真生效;`setRole` 记录显式特征列,`featureExtract` 若收到显式特征则只使用这些列,否则保留原自动特征逻辑。
- **School Evidence**:
  - 临时 `1549` saved DAG 使用 `setRole.config.features=['semester','is_retake','course_id']`,排除 `score/grade_point`。
  - run `5e893913-d32d-4bee-b802-2068b97ccb49` 学校真测 `success`,7 nodes completed。
  - metrics 不再全 `1.0`: `accuracy=0.8691666667`, `precision=0.8691666667`, `recall=1.0`, `f1=0.9300044583`, `auc=0.5922450550`。accuracy 偏高来自 `pass=True` 占比约 `86.7%`;AUC 已回到弱预测合理区间。
  - 兼容回归: `1548` 不传 features run `22792e0c-0987-4489-bd3f-6b8d65dadbd8` 仍 success,metrics 与原风电一致;`1547` 不传 features run `8a3b8cca-397b-465b-b742-080d8e47c48e` success。
  - 临时 saved/run 已清理: 删除 `6` 条 `pipeline_runs` 与 `21` 条 `node_executions`。

## P3: 财报 111 + 用能 103 AI 派生标签已入库并真测

- **Status**: Phase A+B+C 真闭环。财报 `1550` 真预测能力成立;用能 `1551` 技术链路闭环,教学价值另列 P3 优化。
- **Phase B 入库**: 本会话学校 SQL 直入,无产品代码 commit。Phase 3.2 基线 `20/10/0/18/3` → `20/10/0/20/5`。
- **财报 1550**: `[R6-AI-PILOT] 财报风险预警`,派生 `financial_statements_with_label.csv`。规则: `risk_label = debt_ratio > 0.65 OR roe < 0.08 OR interest_coverage < 3`;正样本 `631/5000`,比例 `12.62%`。
- **用能 1551**: `[R6-AI-PILOT] 用能异常检测`,派生 `energy_monitoring_with_anomaly.csv`。规则: `anomaly_flag = pm25 > 100 OR so2_ppm > 0.08`;正样本 `2059/50000`,比例 `4.12%`。
- **Phase C 财报真测**: run `7cc40726-b3e9-4373-9d3e-4614b61c533d`,`status=success`,7 nodes / 6 edges,7 个 `node_executions` completed。metrics: `accuracy=0.887`, `precision=1.0`, `recall=0.017391304347826087`, `f1=0.03418803418803419`, `auc=0.8731515598133137`。Jim 复核: AUC 0.873 为真预测,类别不均衡下默认阈值 recall 低可接受。
- **Phase C 用能真测**: run `cfd92ff8-f182-46da-a806-c748ec22187c`,`status=success`,7 nodes / 6 edges,7 个 `node_executions` completed。metrics: `accuracy=0.9552`, `precision=0.0`, `recall=0.0`, `f1=0.0`, `auc=0.5001465194274947`。Jim 复核: 技术真闭环,但教学价值需 handbook/标签设计优化。
- **数据源 UI 证据**: `r6-finance-1550-dataset-config.png` 显示 `financial_statements_with_label - 财报风险预警`;`r6-energy-1551-dataset-config.png` 显示 `energy_monitoring_with_anomaly - 用能异常检测`。
- **清理**: 本轮 1550/1551 Phase C 临时 saved/success runs 已清理: 删除 `4` 条 `pipeline_runs` 与 `14` 条 `node_executions`;长期保留 `1550/1551` training 与派生 datasets。
- **AI trainings 真状态**: `1547` 公募 + `1548` 风电 + `1549` 校情 + `1550` 财报 + `1551` 用能 = `5` 个 R6-AI-PILOT 已入库并完成技术闭环。

## Resolved: 用能 1551 教学价值优化

- **Resolved by**: 本会话学校 SQL UPDATE `trainings.id=1551.handbook_content`。handbook 是 DB 内容,无产品代码 commit。
- **Status**: Resolved。handbook 已改写为两阶段对比教学法。
- **Resolution**: 阶段 1 不排除 `pm25/so2_ppm` 直接派生字段,观察 metrics 接近 `1.0` 并学习派生标签泄漏;阶段 2 排除 `pm25/so2_ppm`,观察 AUC / recall / f1 退化,学习类别不均衡与真信号识别。
- **Cross-training positioning**: 与 `1547` 公募、`1548` 风电、`1549` 校情、`1550` 财报单阶段建模不同,`1551` 作为进阶练习使用。
- **School Evidence**: `trainings.id=1551` handbook length `2113`,updated_at `2026-05-05 11:08:45.743423+00`;Browser Use `/#/ai-designer/1551` 案例手册显示“两阶段对比”“派生标签泄漏”“阶段 1”“阶段 2”等关键词,截图 `r6-energy-1551-handbook-contrast.png`。

## P3: AI Designer 算子库缺少显式“类别编码”算子

- **Status**: 算子覆盖差距,不阻塞 R6 FUND-CHURN 试点闭环。
- **Observed**: R6 Session N+1 学校 `/#/ai-designer/1547` 真测时,算子库可用算子包括读取数据、标准化、数据拆分、逻辑回归、模型评估等,但没有字面量“类别编码”算子。
- **Workaround**: 本次 FUND-CHURN pipeline 用“特征工程”类节点命名为“类别编码/特征工程”承接该步骤,但功能差距未真验证。
- **Next**: R6 后续迭代评估是否新增“类别编码”算子,或把类别编码作为特征工程节点的明确配置项。

## P3: R5 教材生产工作流 output/ 遗留

- **Status**: 已归档。`output/` 是早期 R5 教材生产试点流水线本地产物,`.gitignore` 忽略,无 git 历史。
- **Resolution**: 路径 B 调研确认学校 `tasks` 真范围为 `4-142` (`count=93`),`training_code_tasks` 真范围为 `1-49` (`count=49`),不存在 `task_id=205/201/202`;已加 `output/README.md` 标注遗留状态,防止后续 session 误识。
- **Policy**: 不入库,不映射到学校 `task_id=4`,不删除历史 `stage_*.json`。
- **Bug 6**: 仓库内 grep `"Bug 6|bug 6|BUG 6"` 0 命中,视为遗留计划文本,不实施。

## P3: AI Designer 画布按钮命中被节点遮挡

- **Status**: UI 风险观察项。
- **Observed**: R6 Session N+1 真鼠标点击顶部“保存”/“运行”按钮时,Playwright 报按钮被画布节点/header 命中拦截;最终使用 DOM click 触发同一按钮事件完成 API/DB 验证。
- **Impact**: 学生真用学期可能遇到按钮点不到或需要调整画布视图,体验降级。
- **Next**: R6 后续迭代修 `z-index` / toolbar 层级 / 画布节点边界,确保真实鼠标点击顶部按钮不被画布节点遮挡。

## Resolved: AI designer frontend 与 backend payload contract 对齐

- **Resolved by**: `0dacf1d fix(ai-designer): align run_id/execution_id/models payload contracts`
- **Status**: R6 Session N 已闭环。
- **Observed Before Fix**: Codex Phase A 调研发现:
  - frontend `handleRun()` 用 `response.data.run_id`,但 API wrapper 已返回 `response.data`,应为 `response.run_id`。
  - frontend single-step 后端返回 `execution_id/status/node_id`,但前端读 `result.run_id`,字段名不匹配。
  - frontend `getModelList()` 后端返回 `{ models, total }` object,前端类型期望 array。
- **School Evidence**:
  - 学校 curl 真测 `/api/v1/ai/models` 返回 `{ models, total }` object,frontend 已兼容。
  - 学校 curl 真测 `/api/v1/ai/{pipeline_id}/run` 返回 `data.run_id`,frontend 已按 `response.run_id` 读取。
  - 学校 curl 真测 `/api/v1/ai/{pipeline_id}/single-step` 返回 `data.execution_id`,frontend 已按 `result.execution_id || result.run_id` 读取。
  - 临时 `pipeline_runs/node_executions` 已清理,学校 DB 残留为 0。
  - Jim 复核 Browser UI: `/#/ai-designer/104` 的读取数据节点数据集下拉真展示 `数据集 1 - 公募基金精准营销案例` / `数据集 2 - 公募基金精准营销案例`。

## P3: AI 设计器实训内容扩展进行中

- **Status**: Phase A + B + C 真闭环。R6 Session N 已完成协议层与数据集挂载;Session N+1 已入库并保留 `FUND-CHURN training_id=1547`;Session N+2 已完成 run engine 真闭环;R6 Phase B 已完成 backend 通用化 + 风电/校情 AI trainings 入库;R6 Phase C 已完成风电 + 校情 saved pipeline 加载、页面运行按钮、DB、logs、insights 真测;财报/用能扩展已入库并真测。
- **Frontend Evidence**:
  - `frontend/src/views/ml/ai-designer.vue` 3589 行,真实现算子库/模型库/画布/拖拽/保存/运行 UI。
  - 路由 `/#/ai-designer/:id` 与 `/#/designer/ml/:id?` 真存在。
  - 项目详情页 `designer_type='AI'` 分流真生效。
- **Backend Evidence**: `/api/v1/ai/{pipeline_id}/{run,save,logs,single-step,insights}` + `/api/v1/ai/models` CRUD 真存在。
- **Session N Progress**:
  - `0dacf1d` 已修 3 个 payload contract: `run_id` / `execution_id` / `{ models, total }`。
  - `frontend/src/views/ml/ai-designer.vue` 已调用 `/api/v1/trainings/{id}/datasets` 加载 training datasets。
  - `iris` / `boston` 等示例数据集保留为 fallback,兼容旧路径和无 training id 场景。
  - 学校 Browser UI 已验证 `/#/ai-designer/104` 读取数据节点下拉显示公募基金真实数据集名称。
- **Session N+1 Progress**:
  - `training_id=1547` 已入库并保留现场,作为 AI 试点复测与后续扩展样板。
  - 数据源下拉、pipeline 画布、保存落库均已在学校环境真测通过。
- **Session N+2 Progress**:
  - `f23bef1` + `45b0f16` 已让 `/api/v1/ai/1547/run` 真执行 6 节点 DAG。
  - 学校 DB 真测 `pipeline_runs.status='success'`, `node_executions completed=6`, `logs/insights` 返回评估指标。
- **R6 Phase B Progress**:
  - `0870398` 已完成 backend AI run engine 通用化: `setRole` 真执行,`featureExtract` 支持通用二分类目标映射,`dataSplit` 按上游 target 拆分。
  - 学校真测过 `1547` 兼容 run: `run_id=8855b982-0c6e-4d65-b2c7-0543ad41f512`,status=`success`,6 nodes,metrics 真返。
  - 学校真测过风电 `anomaly_label` 临时 saved DAG: `run_id=159ad6a4-47ee-411c-9866-9f5ecc11cb61`,status=`success`,7 nodes,accuracy=`0.8989`,auc=`0.8556`;临时 `pipeline_runs/node_executions` 已清理。
  - 已入库 AI trainings: `1547` 公募基金客户流失预测 → `1548` 风电齿轮箱故障预测 + `1549` 校情学业预测。
  - Phase 3.2 基线: `20/10/0/16/1` → `20/10/0/18/3`;风电 datasets=`3`,校情 datasets=`4`。
- **R6 Phase C Progress**:
  - 风电 `1548`: 干净导航到 `/#/ai-designer/1548`,saved pipeline 真加载 7 nodes / 6 edges,页面运行按钮触发 run `a3eca1bf-07b2-49b6-b43e-dccb765ba49c`,学校 DB `status='success'`,7 个 `node_executions` 全 completed,`/logs` 与 `/insights` 真返。metrics: `accuracy=0.8989507154`, `precision=1.0`, `recall=0.1676270299`, `f1=0.2871242710`, `auc=0.8555905983`。
  - 校情 `1549`: 干净导航到 `/#/ai-designer/1549`,saved pipeline 真加载 7 nodes / 6 edges,页面运行按钮触发 run `0559ebc0-e80a-4f9b-84d1-534715591dc6`,学校 DB `status='success'`,7 个 `node_executions` 全 completed,`/logs` 与 `/insights` 真返。metrics 全 `1.0`,已单列 P3 疑似标签泄漏。
  - 证据截图: `r6-phase-c-1548-clean-loaded.png`, `r6-phase-c-1548-success.png`, `r6-phase-c-1549-clean-loaded.png`, `r6-phase-c-1549-success.png`。
  - 边界: 完整拖拽 + 表单逐项配置 + 真点保存仍受 Browser Use/Playwright 节点点击工具边界影响,未作为本轮通过依据;真鼠标 UI 测试推后续。
- **R6 Feature Selection Follow-up**:
  - `c265463` 已让 backend `setRole.config.features` 真生效,用于显式排除泄漏特征。
  - 校情 `1549` 使用 `features=['semester','is_retake','course_id']` 学校真测 success,`AUC=0.5922450550`,不再全指标 1.0。
  - 临时 feature-selection runs 已从学校 DB 清理。
- **Remaining Gap**:
  - 无 `/api/v1/ai/{scene_id}/preview-url`,无独立算子库 endpoint。
  - 风电 `1548` 与校情 `1549` 已完成 saved pipeline 加载 + 页面运行 + DB/logs/insights 闭环;完整拖拽配置 UI 真测待 Jim 真浏览器或后续专门交互测试。
  - 财报风险预警 `1550` 与用能异常检测 `1551` 已完成派生 CSV 入库与技术闭环真测;用能教学价值优化另列 P3。
- **R6 Current AI Trainings**:
  - `1547` 公募基金客户流失预测: fund_customers/fund_transactions,目标 `subscribed/churn`。
  - `1548` 风电齿轮箱故障预测: fault_log/scada_readings/turbine_specs,目标 `anomaly_label`。
  - `1549` 校情学业预测: courses/scores/students/teachers,目标 `pass`。
  - `1550` 财报风险预警: financial_statements_with_label,目标 `risk_label`。
  - `1551` 用能异常检测: energy_monitoring_with_anomaly,目标 `anomaly_flag`。
- **Next**: 用能 `1551` 教学价值优化;完整拖拽配置 UI 等 Jim 真浏览器判定。
