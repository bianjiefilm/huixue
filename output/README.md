# output/ — 历史 R5 教材生产试点流水线遗留

## 真状态 (2026-05-05 路径 B 调研结论)

本目录 `.gitignore` 忽略,无 git 历史。是早期 R5 教材生产试点流水线的本地产物,已弃用。

## 不入库

学校 DB 真状态:

- `tasks` 表 id 范围 `4-142` (`count=93`),不存在 `task_id=205/201/202`
- `training_code_tasks` 表 id 范围 `1-49` (`count=49`),不存在 `205`

本目录文件 (含 `stage_02_control_flow.json task_id=205` 等) 的 ID 是本地试点编号空间,不对应学校 DB 真值。

## 当前活跃流水线

- R5 49 关教材生产: `training_code_tasks` 表,评测器线,`49/49` 真闭环 (commit `7dcd80f` + `cfeb942` + 历史)
- `backend/scripts/import_ai_stages.py` 真使用: `stage_python_1-5_fixed.json` + `stage_python_6-12.json` + `stage_nn_*`,创建 `courses/practices/tasks` (与 R5 49 关是不同维度)
- 不使用本目录的 `stage_02_control_flow.json` / `stage_02_current.json` / `stage_03_function_scope.json` / `stage_04_dict_set.json`

## "Bug 6" 上下文

仓库内 grep `"Bug 6|bug 6|BUG 6"` 0 命中,无真凭据是哪个 session 的真任务。视为遗留计划文本,不实施。

## 处置规则

后续 session 中若 Codex 再次将本目录文件识别为活跃任务,应停下并询问 Jim。不擅自入库 / 不擅自映射到 `task_id=4` / 不擅自删除。
