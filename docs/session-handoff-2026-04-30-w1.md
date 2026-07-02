# 慧学 W1 Session Handoff

日期: 2026-04-30

## 本 session 结束总结

1. W0 完成: PY01 + CV01 C2-B 双向闭环。
2. W1 完成: 4 门验收,真覆盖率 2/4(MJ + CV)。
3. Python 待修: route ID 合同错位调研定位完成,推下次。
4. Spark 文档对齐: pytest_module 5 综合关移除 Spark12,`KNOWN_ISSUES.md` 已记录。
5. CV 补打分: API 写入 SCP 落库,frontend 显示验证。
6. Tempo Course Auditor v2 文档: 全部 P0/P1 修复 + Phase 3.2 SQL schema 对齐。
7. 飞书归档表已创建: app token `O8NGb2Yaaau7RnsGhZ3cwzgOnPd`,table id `tblXiR5JUTAWwZRY`。

## 下次 session 启动条件

1. Python UI route ID 合同修复。调研已完成,可直接动手修 `frontend/src/views/classroom/course-grades.vue` 及跳转入口。
2. W2 启动: 数据采集 + 数据清洗 + 神经网络 + 大数据 4 门。
3. 飞书归档新行直接写入 `O8NGb2Yaaau7RnsGhZ3cwzgOnPd` / `tblXiR5JUTAWwZRY`。

## 下次 session 启动顺序

1. 修 Python UI route ID 合同(`course-grades.vue`)。
2. 学校 frontend 部署 + Python classroom 101 复测。
3. 启动 W2 4 门验收: 数据采集 / 数据清洗 / 神经网络 / 大数据。
4. 每门完成后写飞书归档表新行。

## Python route ID 根因摘要

- 学校 DB: classroom 101 的 `classroom_courses.id=2`, `course_id=101`, `practice_id=6`。
- 正确 API: `/api/v1/classrooms/101/courses/2/grades?teacher_id=4&status=all` 返回 `total=2`。
- 错误 UI:
  - `/classroom/101/course/2/grades`: `course-grades.vue` 用 `course.id === 2` 查列表,找不到课程。
  - `/classroom/101/course/101/grades`: 能显示课程标题,但请求 `/courses/101/grades`,把 master `course_id` 当成 `classroom_course_id`。
- 修复方向: route 参数统一为 `classroom_course_id`,展示对象映射时保留 master id 与 cc_id 两套字段,API 调用只用 cc_id。

## W2 执行提醒

- 学校真实环境仍是唯一验收证据。
- Browser Use 仅做 frontend 页面验证;提交继续按 C2-B helper 走学校 API。
- 每门必跑 Phase 3.2 SQL、三路由 canary、Z1 三剑客。
- P0 任意 1 个即该门失败并报告;不跳过证据。
