# Known Issues

> Last reviewed: 2026-05-06 (post-batch-2 handover cleanup). All R6 AI training data (1547-1551) + test users/classrooms cleared. Active items below; full history archived in KNOWN_ISSUES_ARCHIVE.md.

## Dev Tool Note

`.codex/` and `.claude/` contain development-phase tool configs (Codex/Claude Code commands, prompts, auditor scripts). Production does not depend on these directories. They are checked in for development continuity only.

---

## Deployment Log: Learning analytics 401 frontend fix

- **Status**: Deployed and verified on school environment, 2026-05-07 10:51 CST.
- **Deployed commit**: `9769db6` (`fix(frontend): stabilize learning analytics auth`).
- **Artifact**: `oss://huixuekeijxueyuan/deploy/huixue/20260507104940-9769db6-frontend.tgz`.
- **Integrity**: local and school sha256 `9f9488f8891d41455f152d134ee44ca3eb88b94ae753b2d454dffb0d890e767a`; school download verified with `sha256sum -c`.
- **School frontend**: `index-BLTOgNVo.js`, `LearningAnalytics-DepgkwqA.js`; old `LearningAnalytics-DloZfLCk.js` now returns 404.
- **School DB evidence**: `SELECT c.id, c.name, c.teacher_id, u.username ... WHERE c.id=1703;` returned `1703 | 某电商货品销售分析案例实验班 | 6 | school_admin`.
- **Browser UAT**: Browser Use opened `http://100.74.141.3:3000/#/classroom/1703/learning-analytics`; network showed `GET /api/v1/classrooms/1703/learning/overview?teacher_id=6 => 200`; console summary: `Errors: 0, Warnings: 0`; page did not show `未授权`.

## Deployment Log: Phase J frontend classroom navigation fix

- **Status**: Deployed and verified on school environment, 2026-05-06 21:53 CST.
- **Deployed commit**: `1239af5` (`phase-j: fix ClassroomListView reload + atomic frontend deploy`).
- **Artifact**: `oss://huixuekeijxueyuan/deploy/huixue/huixue-frontend-1778074991-1239af5.tgz`.
- **Integrity**: local and school sha256 `b395f952fbfbf85d1885b3e2a198d37fa08fc0a46d5b36c8cc54cef1edafcc76`; school download verified with `sha256sum -c`.
- **School frontend**: `index-DokYba3Y.js`, 400 assets in `huixue-frontend:/usr/share/nginx/html/assets`.
- **Evidence**: school DB `SELECT COUNT(*) FROM tasks;` returned `92`; sampled assets `BasicLayout-BhH7_2gS.js`, `detail-BCvv3ztS.js`, `practice-DghvxFlO.js`, `challenge-5UZ3MWpM.js`, `EnvironmentConflictDialog-x3nVFexU.js`, `MonacoEditor-DqqGmrLn.js`, and `ClassroomListView-PWRmSDFL.js` returned HTTP 200.
- **Browser UAT**: school frontend login as `school_admin`; classroom 1696, 1703, 1704, and 1705 all navigated to detail pages with 0 console errors/warnings and 200 network responses.

---

## P3: Browser Use/Playwright 真鼠标点击 AI Designer 节点不稳

- **Status**: 工具边界确认，等待 Jim 真浏览器最终判定。
- **Observed**: `browser_click` / Playwright locator click AI Designer 节点后 `selected=null`，`.config-panel display=none`；DOM `.click()` 触发后 Vue 真选中并显示配置面板。完整拖拽 + 表单逐项配置 + 真点保存未作为闭环依据。
- **Likely**: 工具边界。当前 AI Designer 节点交互依赖 Vue 事件链和 pointer/mouse 事件组合，学生真浏览器使用大概率正常。
- **Resolution**: Jim 真浏览器测试如通过，关闭此 P3；如不通过，R6 后续修真实 click 事件链。

## P3 (Resolved): Dashboard 课程总数 15 vs "18 门课" 规划估算

- **Status**: Resolved（接受现状，选项 1）。
- **真因**: courses 表真 15 行，dashboard SQL `db.query(Course).count()` 无 bug，显示 15 正确。"18 门课" 是规划估算（后端开发 8 + 大数据 10 = 18 = practices 真 direction 分布）；后端开发 8 门 practices 历史 import 时未同步写入 courses 表。
- **Impact**: 学校老师 dashboard 看到"课程总数 15"，与"18 门课"宣传文档有视觉差。
- **Resolution**: 接受现状。学校反馈再决定补录 courses 行或改文案。Jim 拍板 2026-05-06。

## P3: pytest sandbox 无网络/文件隔离

- **Status**: 架构治理项，不阻塞当前课程实践与项目实训 demo。
- **Location**: `backend/app/services/code_executor.py` 的 `pytest_module` 执行路径。
- **Risk**: 当前 pytest_module 在 backend 进程空间执行学生代码，后续面向不可信公开提交需要容器级 `--network=none`、文件系统隔离与资源限制。
- **Next**: 进入下一轮安全架构治理时，优先评估复用 Docker sandbox / container manager。

## P3: logging WARNING 输出无 handler 抓取

- **Status**: 可观测性优化项，不影响功能正确性。
- **Location**: backend root logger / app loggers。
- **Next**: 在 `app/main.py` 或 uvicorn log config 中统一配置 StreamHandler。

## P3: 学校 DB 容器历史漂移

- **Status**: 运维清理项，不影响产品运行。
- **Observed**: `huixue-db` stopped 容器与当前运行中 `743a1e751097_node1-data_db_1` 同存。
- **Policy**: 文档与验收命令以 `docker ps` 实查为准；不擅自删除 stopped 容器。
- **Next**: 由运维窗口统一清点历史容器。

## P3: CV 课程实践 UI 无补打分入口

- **Status**: 教师体验 cosmetic，不阻塞 demo。
- **Next**: 后续产品体验迭代时补 modal + form。

## P3: auditor Z1 示例 endpoint 路径陈旧

- **Status**: 文档/验收脚本维护项，不影响产品功能。
- **Observed**: 旧示例 `/api/v1/teachers/{teacher_id}/practices/{practice_id}/tasks/{task_id}/submissions` 返回 404；学校真实 route 为 `/api/v1/teachers/{teacher_id}/classrooms/{classroom_id}/courses/{course_id}/submissions`。
- **Next**: 下次文档维护时同步 `.codex/commands/tempo-course-auditor.md` 与 `.claude/commands/tempo-course-auditor.md` 的 Z1 示例。

## P3: add-to-classroom malformed body 先触发 422

- **Status**: FastAPI 请求体验/安全一致性观察项，不影响有效请求 RBAC。
- **Observed**: `POST /api/v1/trainings/library/{training_id}/add-to-classroom/{classroom_id}` 缺少 `start_time/end_time` 时返回 422；提供合法 body 后，student 为 403，teacher 操作非己课堂为 403。
- **Next**: 若要做到无效 body 也先走 RBAC，需将请求体改为延迟校验或在依赖层前置认证包装。

## P3: 命令行实践内容缺失

- **Status**: 内容覆盖观察项，不阻塞当前 demo。
- **Observed**: 学校 DB published tasks 中无 `env_type` 为 `shell` / `bash` / `terminal` / `cmd` / `cli` 的命令行实践 task；前端 `TerminalEmulator.vue` 已有 `envType === 'shell'` UI。
- **Next**: 若产品路线需要命令行实践，先补真实 `shell` 类内容与后端 reset-terminal 链路，再按学校真实环境重跑 UAT。

## P3: 云桌面实践内容缺失

- **Status**: 内容覆盖观察项，不阻塞当前 demo。
- **Observed**: 学校 DB published tasks 中无 `env_type` 为 `desktop` / `vnc` / `cloud` / `vm` 的云桌面实践 task；前端 `challenge/detail.vue` 已有 `envType === 'desktop'` UI。
- **Next**: 若产品路线需要云桌面实践，先补真实 `desktop` 类内容和可启动环境资源，再按学校真实环境重跑 UAT。

## P3: AI Designer 算子库缺少显式"类别编码"算子

- **Status**: 算子覆盖差距，不阻塞 AI Designer 主体功能。
- **Next**: R6 后续迭代评估是否新增"类别编码"算子，或把类别编码作为特征工程节点的明确配置项。

## P3: AI Designer 画布按钮命中被节点遮挡

- **Status**: UI 风险观察项。
- **Observed**: 真鼠标点击顶部"保存"/"运行"按钮时，Playwright 报按钮被画布节点/header 命中拦截。
- **Next**: R6 后续迭代修 `z-index` / toolbar 层级，确保真实鼠标点击顶部按钮不被画布节点遮挡。

## 部署日志: 补齐「某公司应收账款分析案例」实训 (2026-07-02)

- **背景**: 18 门课程标准清单核对发现学校环境缺失第 8 个实训「某公司应收账款分析案例」(trainings 表无行、`实训资源/` 磁盘无目录)。
- **素材来源**: 本地 `ziyuan_normalized/A_Interactive_Courses/trainings/08-accounts-receivable/` (handbook.md 65KB + ar_aging_analysis.ipynb) + `ziyuan_data` (cover、ar_invoices.csv、ar_sample_data.csv)。
- **部署路径**: 本地打包 tgz → OSS `deploy/huixue/20260702-ar-training.tgz` (sha256 a52a8d6b…) → 学校 curl 下载校验一致 → 解压至 `/opt/huixue-yuanban/backend/static/resources/实训资源/08-某公司应收账款分析案例/`。
- **DB 变更** (脚本 OSS `deploy/huixue/20260702-insert_ar.py`, 于 huixue-backend 容器内执行): trainings id=1552 (JUPYTER / env 1 / PUBLISHED / PUBLIC), training_datasets id=56,57, courses id=125 `[实训]某公司应收账款分析案例`。
- **实证**: teacher1 登录后 `GET /api/v1/trainings/library` 返回 1552;`/trainings/1552/handbook` 返回 45,597 字符;`/trainings/1552/datasets` 返回 2 个数据集 (1,307,395 / 3,765 bytes)。标准 10 实训在 library 全部可见。
- **遗留**: Spark编程基础缺 7 个视频 (标准 23 / 实有 16)、Python程序设计缺 7 个 (29/22);本机全盘检索无源文件 (Spark 本地 16 个已 ≈7.0GB,与标准 7.1GB 吻合),需向原始素材交付方索取后再补传。

## 部署日志: 补齐 5 个实训 Jupyter Notebook (2026-07-02)

- **背景**: 18 门标准清单二次核对,实训侧缺 5 个 ipynb (校情/人力薪酬/财务报表/风电/光伏),源文件在本地 `ziyuan_normalized/A_Interactive_Courses/trainings/*/jupyter/`。
- **部署**: OSS `deploy/huixue/20260702-training-notebooks.tgz` (sha256 e078ebaa…) → 学校 curl 校验一致 → 解压至各实训 `jupyter/` 子目录,清理 AppleDouble 文件。
- **实证**: `docker exec huixue-backend find /app/static/resources/实训资源 -name '*.ipynb'` 返回 10 个,标准 10 实训中需 ipynb 的 7 个 (06/07/08/09/10/11/12) 全部就位。
- **口径结论**: 其余标准清单差额 (Spark/Python 各 7 视频、个别实训数据集数) 本地源素材同样不存在,判定为原盘点统计口径出入,经 Jim 确认不再补充。

## 部署日志: course_resources 重复入库清理 (2026-07-02)

- **背景**: 8 门课程包 course_resources 表存在同 (course_id, url) 重复入库,最严重的单条视频重复 6 次 (Python 课程多条)。
- **操作** (学校 `743a1e751097_node1-data_db_1` psql 直接执行,无需 OSS 中转 — 纯 DB 操作):
  1. 备份: `CREATE TABLE backup_course_resources_dedupe_20260702 AS SELECT * FROM course_resources;` (2049 行全量备份)
  2. 确认 `course_resources.id` 无被其他表外键引用 (pg_constraint 查询为空,删除安全)
  3. 去重: `DELETE FROM course_resources WHERE id NOT IN (SELECT MIN(id) FROM course_resources GROUP BY course_id, url);` 删除 634 行
- **实证**: 去重后总数 2049→1415;`GROUP BY course_id,url HAVING COUNT(*)>1` 返回 0 行;8 门课程包逐一计数与此前"去重后 URL 数"统计完全吻合 (如 Python 354、Spark 337);teacher1 真账号调用 `GET /api/v1/courses/101/resources` 返回 354 条、354 个不同 URL,前端资源列表确认无重复。
- **回滚方式**: 如需恢复,`INSERT INTO course_resources SELECT * FROM backup_course_resources_dedupe_20260702 WHERE id NOT IN (SELECT id FROM course_resources);` 备份表暂留,确认无问题后可清理。

## 部署日志: AI 功能总开关上线(默认关闭) + 硬编码密钥移除 (2026-07-02)

- **Commit**: 65b9769 (PR #3, CI L0 pass), 部署包 OSS `deploy/huixue/20260702-65b9769-ai-gate-{backend,frontend-dist}.tgz` (sha256 d529881c… / 567bb745…), 学校下载校验一致。
- **后端**: 7 个 py 文件替换至 `/opt/huixue-yuanban/backend/`,`.env` 追加 `AI_FEATURES_ENABLED=false`,restart。
- **前端**: dist 全量 docker cp 进 huixue-frontend,served index hash `index-CrSFo4Bq.js` 与本地构建一致。
- **关闭态实证**: `/api/v1/ai/chat` → 403 `AI_DISABLED`;`/api/v1/generation/*` → 403;`/ai-features/status` → 200 `available:false`;非 AI 主流程 login/trainings library 200 无回归。
- **打开态实证**(临时开 → 验证 → 关回): status `available:true`;doubao 链路报干净的"缺少 ARK_API_KEY 环境变量"(硬编码已拔)。双向切换验证通过。
- **重新打开方法**: 学校 `.env` 改 `AI_FEATURES_ENABLED=true` + `docker restart huixue-backend`(doubao 链路还需配 `ARK_API_KEY`)。
- **待办(P1)**: ① 旧 ARK key `aba5befb…` 已在 git 历史泄露,需火山方舟控制台作废/轮换,新 key 只写学校 `.env`;② AgentPilot key 建议一并轮换;③ ai_service chat 错误路径响应缺 quota_info 导致 500 包装(历史小 bug,不影响开关)。

## 部署日志: quota_info 500 bug 修复 (2026-07-02)

- **Commit**: 0939b72 (PR #4, CI L0 pass),部署包 OSS `deploy/huixue/20260702-0939b72-quota-fix.tgz` (sha256 7bf19ee9…),学校下载校验一致,替换 2 个文件后 restart。
- **修复内容**: `chat_with_ai` 异常分支补 `quota_info`(pydantic 必填字段缺失曾导致 500 校验错误);`check_question_quality` 额度用尽/异常分支同样缺 `quota_info`/`detailed_analysis`/`success`;顺带修复该路径下既有 bug `quota_manager.get_user_role(user_id)` 方法不存在(新增公开方法委托给已有私有方法)。
- **实证**(临时开 `AI_FEATURES_ENABLED=true` → 验证 → 关回 `false`):`POST /api/v1/ai/chat` 从"500 validation error" 变为 `200 {"reply":"AI助手暂时无法回复...","quota_info":{...}}`;`POST /api/v1/ai/check-quality` 同样 200 + 完整字段。关回开关后 `ai/chat` 恢复 403 `AI_DISABLED`,`trainings/library` 200 无回归。
