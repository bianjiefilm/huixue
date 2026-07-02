"""
tests/playwright_full_audit.py
慧学平台 — 全角色全路由 Playwright 审计脚本
覆盖: admin / teacher1 / student1 三角色，收集 console errors/warnings、network failures、JS exceptions

用法:
    # 本地开发环境（Mac Docker Desktop）
    BASE_URL=http://localhost:3000 python -m pytest tests/playwright_full_audit.py -v

    # 远程服务器
    BASE_URL=http://<慧学服务器1-IP>:3000 python -m pytest tests/playwright_full_audit.py -v

    # 仅运行 admin 角色
    python -m pytest tests/playwright_full_audit.py -v -k "admin"

    # 生成 HTML 报告
    python -m pytest tests/playwright_full_audit.py -v --html=playwright_report.html --self-contained-html
"""

import os
import sys
import time
import json
import re
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict

import pytest

# Playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, ConsoleMessage, Request, Response
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL: str = os.environ.get("BASE_URL", "http://localhost:3000")
API_URL: str = os.environ.get("API_URL", "http://localhost:8000")

# 三个角色的登录凭据（与 conftest.py 保持一致）
ACCOUNTS = {
    "admin":    {"username": "admin",     "password": "admin123"},
    "teacher":  {"username": "teacher1",  "password": "teacher123"},
    "student":  {"username": "student1",  "password": "student123"},
}

# 等待配置
NAVIGATION_TIMEOUT_MS = 20000   # 20s per page
DOM_CONTENT_LOADED_MS = 10000  # 10s for DOM ready
NETWORK_IDLE_MS = 8000         # 8s network idle

# 控制哪些路由需要真实 classroom/training ID（从 API 动态获取）
FETCH_DYNAMIC_IDS = True  # 开启时自动从 API 获取真实数据


# ─────────────────────────────────────────────────────────────────────────────
# 数据结构
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PageResult:
    role: str
    route: str
    full_url: str
    status: str           # "ok" | "warning" | "error" | "crash"
    status_code: Optional[int]
    http_errors: list = field(default_factory=list)   # [{url, status, type}]
    console_errors: list = field(default_factory=list)  # [{type, text, location}]
    js_exceptions: list = field(default_factory=list)  # [{message, stack}]
    warnings: list = field(default_factory=list)
    load_time_ms: Optional[float] = None
    error_msg: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# 结果收集器（per-page）
# ─────────────────────────────────────────────────────────────────────────────

class AuditListener:
    """注入到每个 Playwright Page 的监听器"""

    def __init__(self, role: str, route: str, url: str):
        self.role = role
        self.route = route
        self.url = url
        self.http_errors: list[dict] = []
        self.console_errors: list[dict] = []
        self.js_exceptions: list[dict] = []
        self.warnings: list[dict] = []
        self.response_status: Optional[int] = None
        self.load_time_ms: Optional[float] = None
        self.crashed = False
        self.error_msg: Optional[str] = None
        self._start_time: Optional[float] = None

    def _fmt_location(self, location: str) -> str:
        """裁剪长的控制台消息位置"""
        if not location:
            return ""
        # "http://localhost:3000/js/app.abc123.js:1:9999" → "js/app.abc123.js:1"
        match = re.search(r'(/[^:]+):\d+', location)
        return match.group(1) if match else location[:80]

    def on_console(self, msg: ConsoleMessage):
        t = msg.type
        txt = msg.text
        loc = self._fmt_location(msg.location.get("url", ""))
        entry = {"type": t, "text": txt[:300], "location": loc}

        if t == "error":
            # 过滤无关紧要的浏览器噪音
            skip_patterns = [
                r"favicon",
                r"net::ERR_BLOCKED",
                r"chrome-extension",
                r"fonts\.googleapis",   # Google Fonts 被墙在某些环境
                r"www\.googleapis",    # 同上
            ]
            if any(re.search(p, txt, re.I) for p in skip_patterns):
                return
            self.console_errors.append(entry)
        elif t in ("warning", "warn"):
            self.warnings.append(entry)
        elif t == "log":
            pass  # debug 日志默认跳过

    def on_request_failed(self, request: Request):
        url = request.url
        failure = request.failure
        err_text = failure.error if failure else "unknown"
        # 跳过静态资源加载失败（字体等）
        skip_ext = (".woff2", ".woff", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico")
        if any(url.lower().endswith(ext) for ext in skip_ext):
            return
        self.http_errors.append({
            "url": url,
            "status": 0,
            "type": "request_failed",
            "reason": err_text,
        })

    def on_response(self, response: Response):
        url = response.url
        status = response.status
        # 记录 HTML 文档请求的状态
        if self.url.rstrip("/") == url.rstrip("/") or url == self.url.split("#")[0] + "#" + self.route:
            self.response_status = status
        # 非 2xx/3xx 算 HTTP 错误（但只记录 API/HTML 请求，不记录静态资源）
        if status >= 400:
            skip_static = any(
                re.search(p, url) for p in [
                    r'\.(js|css|woff2?|ttf|otf|png|jpg|jpeg|gif|svg|ico|map)$',
                    r'/static/',
                    r'/assets/',
                ]
            )
            if not skip_static:
                self.http_errors.append({
                    "url": url,
                    "status": status,
                    "type": "http_error",
                })

    def on_crash(self):
        self.crashed = True

    def build_result(self) -> PageResult:
        if self.crashed:
            status = "crash"
        elif self.http_errors or self.console_errors or self.js_exceptions:
            status = "warning" if len(self.console_errors) <= 2 and not self.js_exceptions else "error"
        else:
            status = "ok"

        return PageResult(
            role=self.role,
            route=self.route,
            full_url=self.url,
            status=status,
            status_code=self.response_status,
            http_errors=self.http_errors,
            console_errors=self.console_errors,
            js_exceptions=self.js_exceptions,
            warnings=self.warnings,
            load_time_ms=self.load_time_ms,
            error_msg=self.error_msg,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 路由清单
# ─────────────────────────────────────────────────────────────────────────────

def get_routes_by_role() -> dict[str, list[str]]:
    """
    返回每个角色需要审计的路由列表（不含 BASE_URL 前缀，hash history）
    路由分为两类:
      - 固定路由: 直接列出
      - 动态路由: 标记 {classroomId} / {trainingId}，由 fetch_dynamic_ids() 替换
    """

    # ── Admin-only routes ──────────────────────────────────────────────────
    admin_routes = [
        # 固定路由
        "#/admin/dashboard",
        "#/admin/resource-import",
        "#/admin/organization/school-info",
        "#/admin/organization/department",
        "#/admin/user/teacher",
        "#/admin/user/student",
        "#/admin/user/role",
        "#/admin/user/teacher/add",
        "#/admin/course/practice",
        "#/admin/course/training",
        "#/admin/course/practice-approval",
        "#/admin/course/training-approval",
        "#/admin/exam-management",
        "#/admin/ai-generation",
        "#/admin/ai-generation/practice",
        "#/admin/ai-generation/exam",
        "#/admin/ai-generation/training",
        "#/admin/ai-generation/batch",
        "#/admin/resource/environment",
        "#/admin/resource/experiment",
        "#/admin/ai-test",
        "#/admin/logs/course",
        "#/admin/logs/practice",
        "#/admin/logs/training",
        "#/admin/logs/teacher",
        "#/admin/logs/student",
        # 动态 ID 路由
        "#/admin/user/teacher/edit/{teacherId}",
        "#/admin/user/student/edit/{studentId}",
        "#/admin/course/detail/{courseId}",
        "#/admin/logs/course/{courseId}",
        "#/admin/logs/practice/{courseId}",
        "#/admin/logs/training/{courseId}",
    ]

    # ── Teacher routes (teacher + admin) ─────────────────────────────────
    teacher_routes = [
        "#/home",
        "#/classroom",
        "#/course",
        "#/course/training/library",
        "#/course/training/create",
        "#/course/training/{trainingId}/edit",
        "#/course/practice/my",
        "#/course/practice/create",
        "#/course/practice/{practiceId}/edit",
        "#/course/resource",
        "#/course/micro",
        "#/course/challenge/{courseId}/{taskId}",
        "#/ml",
        "#/ml/manual",
        "#/exam",
        "#/exam/paper-bank",
        "#/exam/question-bank",
        "#/exam/create-question",
        "#/exam/edit-question",
        "#/exam/edit-paper",
        "#/exam/template-paper",
        "#/project",
        "#/project/jupyter",
        "#/project/{projectId}",
        "#/project/jupyter/{projectId}",
        "#/visual",
        "#/visual/preview",
        "#/profile",
        # 动态 ID 路由
        "#/classroom/{classroomId}",
        "#/classroom/{classroomId}/status",
        "#/classroom/{classroomId}/student-status",
        "#/classroom/{classroomId}/student-grades",
        "#/classroom/{classroomId}/edit",
        "#/classroom/{classroomId}/learning-analytics",
        "#/classroom/{classroomId}/exams",
        "#/classroom/{classroomId}/exam/create",
        "#/classroom/{classroomId}/training/{trainingId}",
        "#/classroom/{classroomId}/training/{trainingId}/grades",
        "#/classroom/{classroomId}/training/{trainingId}/homework",
        "#/classroom/{classroomId}/training/{trainingId}/workspace",
        "#/classroom/{classroomId}/bi-training/{trainingId}/workspace",
        "#/classroom/{classroomId}/bi-training/{trainingId}/review/{studentId}",
        "#/classroom/{classroomId}/course/{courseId}",
        "#/classroom/{classroomId}/course/{courseId}/exams",
        "#/classroom/{classroomId}/course/{courseId}/grades/{studentId}",
        "#/classroom/{classroomId}/course/{courseId}/homework/{studentId}",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}/marking",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}/detail",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}/results",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}/paper/{studentId}",
        "#/classroom/{classroomId}/exam/{examId}/marking",
        "#/classroom/{classroomId}/exam/{examId}/paper/{studentId}",
        "#/classroom/{classroomId}/exam/{examId}/results",
        "#/classroom/{classroomId}/exam/{examId}/my-result",
        "#/course/micro/{courseId}",
        "#/course/resource/{resourceId}",
        "#/classroom/submission/{progressId}",
        "#/practice/{practiceId}/stage/{stageId}/test",
    ]

    # ── Student routes (student + teacher share most) ───────────────────────
    student_routes = [
        "#/home",
        "#/classroom",
        "#/student-dashboard",
        "#/course",
        "#/course/practice/my",
        "#/course/training/my",
        "#/course/training/library",
        "#/course/resource",
        "#/course/micro",
        "#/course/micro/{courseId}",
        "#/course/challenge/{courseId}/{taskId}",
        "#/ml",
        "#/exam",
        "#/exam/my-exams",
        "#/exam/paper-bank",
        "#/project",
        "#/project/jupyter",
        "#/project/{projectId}",
        "#/project/jupyter/{projectId}",
        "#/profile",
        # 动态 ID 路由
        "#/classroom/{classroomId}",
        "#/classroom/{classroomId}/status",
        "#/classroom/{classroomId}/course/{courseId}",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}",
        "#/classroom/{classroomId}/course/{courseId}/exam/{examId}/my-result",
        "#/classroom/{classroomId}/course/{courseId}/homework/{studentId}",
        "#/classroom/{classroomId}/course/{courseId}/grades/{studentId}",
        "#/classroom/{classroomId}/course/{courseId}/exams",
        "#/classroom/{classroomId}/training/{trainingId}",
        "#/classroom/{classroomId}/training/{trainingId}/workspace",
        "#/classroom/{classroomId}/bi-training/{trainingId}/workspace",
        "#/classroom/{classroomId}/exam/{examId}/take",
        "#/classroom/{classroomId}/exam/{examId}/my-result",
        "#/course/resource/{resourceId}",
    ]

    # ── Shared (any authenticated role) ────────────────────────────────────
    shared_routes = [
        "#/designer/bi",
        "#/designer/bi/{biId}",
        "#/designer/ml",
        "#/designer/ml/{mlId}",
    ]

    # teacher inherits shared; student inherits shared
    all_routes = {
        "admin":   admin_routes,
        "teacher": teacher_routes + shared_routes,
        "student": student_routes + shared_routes,
    }
    return all_routes


# ─────────────────────────────────────────────────────────────────────────────
# 动态 ID 获取（从真实 API）
# ─────────────────────────────────────────────────────────────────────────────

def fetch_dynamic_ids(api_url: str, token: str) -> dict[str, list]:
    """从 API 获取真实 classroom/training/course ID 列表"""
    headers = {"Authorization": f"Bearer {token}"}
    ids: dict[str, list] = {
        "classroomIds": [],
        "trainingIds": [],
        "courseIds": [],
        "practiceIds": [],
        "resourceIds": [],
        "studentIds": [],
        "teacherIds": [],
        "projectIds": [],
        "examIds": [],
        "progressIds": [],
        "biIds": [],
        "mlIds": [],
        "stageIds": [],
    }

    import requests as _req

    # 获取 classroom 列表
    try:
        r = _req.get(f"{api_url}/api/v1/classrooms", headers=headers, timeout=10)
        if r.ok:
            data = r.json()
            items = data.get("data") or data.get("classrooms") or []
            ids["classroomIds"] = [str(x["id"] if isinstance(x, dict) else x) for x in items[:5]]
    except Exception:
        pass

    # 获取 training 列表
    try:
        r = _req.get(f"{api_url}/api/v1/trainings", headers=headers, timeout=10, params={"page_size": 10})
        if r.ok:
            data = r.json()
            items = data.get("data") or data.get("trainings") or []
            ids["trainingIds"] = [str(x["id"] if isinstance(x, dict) else x) for x in items[:5]]
    except Exception:
        pass

    # 获取 practice courses
    try:
        r = _req.get(f"{api_url}/api/v1/course-management/practice-courses", headers=headers, timeout=10)
        if r.ok:
            data = r.json()
            items = data.get("data") or data.get("courses") or []
            ids["courseIds"] = [str(x["id"] if isinstance(x, dict) else x) for x in items[:5]]
            ids["practiceIds"] = ids["courseIds"][:]
    except Exception:
        pass

    # 获取 resource files
    try:
        r = _req.get(f"{api_url}/api/v1/teaching-resources", headers=headers, timeout=10, params={"page_size": 5})
        if r.ok:
            data = r.json()
            items = data.get("data") or []
            ids["resourceIds"] = [str(x.get("id", x)) if isinstance(x, dict) else str(x) for x in items[:5]]
    except Exception:
        pass

    # 获取 project 列表
    try:
        r = _req.get(f"{api_url}/api/v1/students/projects", headers=headers, timeout=10, params={"page_size": 5})
        if r.ok:
            data = r.json()
            items = data.get("data") or data.get("projects") or []
            ids["projectIds"] = [str(x.get("id", x)) if isinstance(x, dict) else str(x) for x in items[:5]]
    except Exception:
        pass

    # 获取 exam 列表
    try:
        r = _req.get(f"{api_url}/api/v1/exams", headers=headers, timeout=10, params={"page_size": 5})
        if r.ok:
            data = r.json()
            items = data.get("data") or data.get("exams") or []
            ids["examIds"] = [str(x.get("id", x)) if isinstance(x, dict) else str(x) for x in items[:5]]
    except Exception:
        pass

    # Fallback: 使用常见测试 ID
    if not ids["classroomIds"]:
        ids["classroomIds"] = ["1", "2"]
    if not ids["trainingIds"]:
        ids["trainingIds"] = ["1", "100"]
    if not ids["courseIds"]:
        ids["courseIds"] = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    if not ids["practiceIds"]:
        ids["practiceIds"] = ["1", "2"]
    if not ids["resourceIds"]:
        ids["resourceIds"] = ["1"]
    if not ids["studentIds"]:
        ids["studentIds"] = ["1", "2", "30"]
    if not ids["teacherIds"]:
        ids["teacherIds"] = ["1", "2"]
    if not ids["projectIds"]:
        ids["projectIds"] = ["1"]
    if not ids["examIds"]:
        ids["examIds"] = ["1"]
    if not ids["progressIds"]:
        ids["progressIds"] = ["1"]
    if not ids["biIds"]:
        ids["biIds"] = ["1", "100"]
    if not ids["mlIds"]:
        ids["mlIds"] = ["1"]
    if not ids["stageIds"]:
        ids["stageIds"] = ["1"]

    return ids


def expand_routes(routes: list[str], ids: dict[str, list]) -> list[str]:
    """将路由中的占位符替换为真实 ID"""

    def replace_one(route: str) -> list[str]:
        # 找第一个未替换的占位符
        m = re.search(r'\{(\w+)\}', route)
        if not m:
            return [route]
        key = m.group(1) + "Ids"
        vals = ids.get(key, ["1"])
        results = []
        for val in vals:
            results.extend(replace_one(route.replace("{" + m.group(1) + "}", val, 1)))
        return results

    expanded = []
    for route in routes:
        expanded.extend(replace_one(route))
    return expanded


# ─────────────────────────────────────────────────────────────────────────────
# Playwright 核心：登录
# ─────────────────────────────────────────────────────────────────────────────

def _get_token_via_api(username: str, password: str) -> tuple[str, dict]:
    """
    通过直接 API 调用获取 token（绕过 502 代理问题）。
    返回 (token, user_info) 元组。
    """
    import requests as _req
    _token = ""
    _user_info = {}

    # 尝试直接后端 API（绕过前端 nginx 代理）
    for _ep in [f"{API_URL}/api/v1/login", f"{API_URL}/api/login"]:
        try:
            _r = _req.post(_ep, json={"username": username, "password": password}, timeout=10)
            if _r.ok:
                _data = _r.json()
                _d = _data.get("data") or _data
                _token = (
                    (_d.get("token") or {}).get("access_token")
                    if isinstance(_d.get("token"), dict)
                    else _d.get("token")
                    or _data.get("token", {}).get("access_token")
                    or _data.get("access_token")
                )
                _user_info = _d.get("user") or {}
                if _token:
                    break
        except Exception:
            pass

    return _token, _user_info


def do_login(page: Page, username: str, password: str) -> bool:
    """
    通过直接 API 获取 token 并注入 sessionStorage，跳过浏览器表单提效。
    解决前端 nginx 502 代理问题。
    """
    token, user_info = _get_token_via_api(username, password)
    if not token:
        return False

    try:
        # 先访问任意页面，建立正确的 origin（带重试，应对网络抖动）
        for attempt in range(3):
            try:
                page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
                break
            except Exception as nav_err:
                if attempt == 2:
                    raise nav_err
        page.wait_for_timeout(500)

        # 注入 token → sessionStorage（非安全上下文）
        page.evaluate(
            f"(vals) => {{"
            f"  sessionStorage.setItem('huixue_token', vals.t);"
            f"  localStorage.setItem('huixue_user', JSON.stringify(vals.u || {{}}));"
            f"}}",
            {"t": token, "u": user_info},
        )
        # 验证注入是否成功
        stored = page.evaluate("() => sessionStorage.getItem('huixue_token')")
        if stored:
            return True
        else:
            print(f"      [!] token 注入后验证失败（storage 中未找到）")
            return False
    except Exception as e:
        print(f"      [!] sessionStorage 注入失败: {type(e).__name__}: {e}")
        return False


def is_logged_in(page: Page) -> bool:
    """检测是否已登录（URL 不在登录页且有内容）"""
    url = page.url
    if "#/login" in url or "/login" in url:
        return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Playwright 核心：访问单个路由
# ─────────────────────────────────────────────────────────────────────────────

def audit_page(
    browser: Browser,
    role: str,
    route: str,
    username: str,
    password: str,
) -> PageResult:
    """
    在独立 Context 中打开一个路由，收集 console / network / exception 数据
    """
    listener = AuditListener(role, route, f"{BASE_URL}/{route.lstrip('#')}")

    # 每个路由独立 Context（避免 cookie 污染）
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        locale="zh-CN",
        extra_http_headers={"Accept-Language": "zh-CN,zh;q=0.9"},
    )
    page = ctx.new_page()

    # ── 注入监听器 ────────────────────────────────────────────────────────
    page.on("console", listener.on_console)
    page.on("requestfailed", listener.on_request_failed)
    page.on("response", listener.on_response)
    page.on("crash", listener.on_crash)

    # ── 捕获 JS 异常 ─────────────────────────────────────────────────────
    page.on("pageerror", lambda exc: listener.js_exceptions.append({
        "message": str(exc)[:300],
        "stack": (exc.stack or "")[:300] if hasattr(exc, "stack") else "",
    }))

    start_time = time.monotonic()

    try:
        # 先登录（通过 API + sessionStorage 注入，绕过 502 代理问题）
        login_ok = do_login(page, username, password)
        if not login_ok:
            listener.error_msg = f"Login failed for {username}"
            result = listener.build_result()
            ctx.close()
            return result

        # 导航到目标路由
        target_url = f"{BASE_URL}/{route.lstrip('#')}"
        response = page.goto(target_url, wait_until="domcontentloaded", timeout=NAVIGATION_TIMEOUT_MS)
        listener.response_status = response.status if response else None

        # 等待页面稳定（部分 SPA 异步加载内容）
        try:
            page.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_MS)
        except Exception:
            pass  # 超时不一定是问题

        # 等待 DOM 可交互
        try:
            page.wait_for_timeout(1500)
        except Exception:
            pass

        listener.load_time_ms = round((time.monotonic() - start_time) * 1000, 1)

    except Exception as e:
        listener.error_msg = str(e)[:200]
        listener.load_time_ms = round((time.monotonic() - start_time) * 1000, 1)
        listener.crashed = True
    finally:
        result = listener.build_result()
        ctx.close()
        return result


# ─────────────────────────────────────────────────────────────────────────────
# 报告生成
# ─────────────────────────────────────────────────────────────────────────────

def generate_report(results: list[PageResult], output_path: str = "playwright_audit_report.json"):
    """将审计结果写入 JSON + 文本摘要"""

    total = len(results)
    ok = sum(1 for r in results if r.passed)
    warning = sum(1 for r in results if r.status == "warning")
    error = sum(1 for r in results if r.status == "error")
    crash = sum(1 for r in results if r.status == "crash")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total_pages": total,
        "ok": ok,
        "warning": warning,
        "error": error,
        "crash": crash,
        "pass_rate": f"{round(ok / total * 100, 1)}%" if total else "0%",
        "by_role": {},
    }

    for role in ("admin", "teacher", "student"):
        role_results = [r for r in results if r.role == role]
        role_ok = sum(1 for r in role_results if r.passed)
        summary["by_role"][role] = {
            "total": len(role_results),
            "ok": role_ok,
            "pass_rate": f"{round(role_ok / len(role_results) * 100, 1) if role_results else 0}%" ,
        }

    # JSON 报告
    report_data = {
        "summary": summary,
        "results": [asdict(r) for r in results],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # 文本摘要
    txt_path = output_path.replace(".json", "_summary.txt")
    lines = [
        "═" * 80,
        f"  慧学平台 Playwright 全路由审计报告",
        f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  目标地址: {BASE_URL}",
        "═" * 80,
        f"  总计页面: {total}  |  通过: {ok}  |  警告: {warning}  |  错误: {error}  |  崩溃: {crash}",
        f"  整体通过率: {summary['pass_rate']}",
        "─" * 80,
    ]

    for role, stats in summary["by_role"].items():
        role_label = {"admin": "管理员", "teacher": "教师", "student": "学生"}[role]
        lines.append(
            f"  {role_label} ({role}): {stats['total']} 页面"
            f"  |  通过 {stats['ok']}  |  {stats['pass_rate']}"
        )

    lines.append("─" * 80)

    # 列出有问题的页面
    problems = [r for r in results if not r.passed]
    if problems:
        lines.append(f"  问题页面列表（共 {len(problems)} 个）:")
        for r in problems:
            role_label = {"admin": "管理员", "teacher": "教师", "student": "学生"}[r.role]
            err_count = len(r.console_errors)
            js_count = len(r.js_exceptions)
            http_count = len(r.http_errors)
            lines.append(
                f"  [{r.status.upper()}] {role_label} | {r.route}"
                f"  | HTTP:{r.status_code or '-'} | console_err:{err_count} | js_exc:{js_count} | http_err:{http_count}"
            )
            if r.error_msg:
                lines.append(f"           错误: {r.error_msg}")
            for e in r.console_errors[:2]:
                lines.append(f"           CONSOLE ERROR: {e['text'][:100]}")

    lines.append("═" * 80)
    lines.append(f"  完整报告已保存: {output_path}")
    lines.append(f"  摘要报告已保存: {txt_path}")

    txt_content = "\n".join(lines)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt_content)

    print()
    print(txt_content)
    print(f"\n  详细 JSON 报告: {output_path}")
    print(f"  摘要报告:      {txt_path}")

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Pytest Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def browser_instance():
    """Module-scoped Playwright browser instance"""
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-web-security",
        ],
    )
    yield browser
    browser.close()
    pw.stop()


@pytest.fixture(scope="module")
def auth_tokens() -> dict[str, str]:
    """从 API 获取三个角色的 JWT token"""
    import requests

    tokens = {}
    for role, creds in ACCOUNTS.items():
        try:
            # Try both endpoint variants
            for endpoint in ["/api/v1/login", "/api/login"]:
                r = requests.post(
                    f"{API_URL}{endpoint}",
                    json={"username": creds["username"], "password": creds["password"]},
                    timeout=10,
                )
                if r.ok:
                    break
            if r.ok:
                data = r.json()
                _d = data.get("data") or data
                token = (
                    (_d.get("token") or {}).get("access_token")
                    if isinstance(_d.get("token"), dict)
                    else _d.get("token")
                    or data.get("token", {}).get("access_token")
                    or data.get("access_token")
                )
                if token:
                    tokens[role] = token
                    print(f"  [{role}] token obtained: {token[:20]}...")
        except Exception as e:
            print(f"  [!] [{role}] login failed: {e}")
    return tokens


@pytest.fixture(scope="module")
def dynamic_ids(auth_tokens) -> dict[str, list]:
    """从 API 获取动态 ID（供路由参数替换）"""
    # 用 admin token 获取最多数据
    token = auth_tokens.get("admin") or auth_tokens.get("teacher") or ""
    if not token:
        return {}
    return fetch_dynamic_ids(API_URL, token)


# ─────────────────────────────────────────────────────────────────────────────
# 测试用例（按角色分组）
# ─────────────────────────────────────────────────────────────────────────────

def _build_test(role: str, route: str, username: str, password: str):
    """动态创建测试函数"""

    @pytest.mark.parametrize("route", [route])
    def test_page(browser_instance, report_page_result, request):
        result = audit_page(
            browser=browser_instance,
            role=role,
            route=route,
            username=username,
            password=password,
        )
        # 存到 request.config 以便收集
        report_page_result(request, result)
        # 软断言：只 WARNING，不阻塞
        if result.status == "crash":
            pytest.fail(f"Page CRASHED: {result.route} — {result.error_msg}")
        elif result.status == "error" and len(result.console_errors) > 5:
            pytest.fail(
                f"Too many console errors ({len(result.console_errors)}) on {result.route}: "
                f"{[e['text'][:80] for e in result.console_errors[:3]]}"
            )

    test_page.__name__ = f"test_{role}_{request.param_clean if hasattr(request, 'param_clean') else role}_{route.lstrip('#/').replace('/', '_').replace('-', '_')}"
    test_page.__doc__ = f"[{role.upper()}] {route}"
    return test_page


# 全局结果收集器（跨所有测试函数共享）
_page_results: list[PageResult] = []


def pytest_configure(config):
    config.addinivalue_line("markers", "audit: full-playwright-audit")


def pytest_collection_modifyitems(config, items):
    # 所有测试标记
    for item in items:
        item.add_marker(pytest.mark.audit)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    # 将 result 附加到 item（由 report_page_result fixture 使用）
    item._result = outcome.get_result()


@pytest.fixture
def report_page_result():
    """收集每个 PageResult 到全局列表"""
    global _page_results
    return lambda request, result: _page_results.append(result)


# ─────────────────────────────────────────────────────────────────────────────
# 动态生成测试用例
# ─────────────────────────────────────────────────────────────────────────────

def pytest_generate_tests(metafunc):
    if "route" not in metafunc.fixturenames:
        return

    # 从 metafunc 获取当前测试的 role/username/password
    # 我们用 id 解析: "test_<role>_<route>"
    # 但更可靠的方式是动态注入

    role = getattr(metafunc.function, "_audit_role", None)
    username = getattr(metafunc.function, "_audit_username", None)
    password = getattr(metafunc.function, "_audit_password", None)

    if not role:
        return

    all_routes = get_routes_by_role()
    role_routes = all_routes.get(role, [])
    if not role_routes:
        return

    metafunc.parametrize("route", role_routes, ids=lambda r: r.lstrip("#/").replace("/", "_").replace("{", "").replace("}", ""))


# 手动注册所有测试
# Pytest 的 parametrize 机制不能动态生成，所以用 exec 生成

import pytest

_EXCLUDED_ROUTES = {
    "#/login",          # 不测登录页本身
    "#/redirect",       # 纯重定向
    "#/",               # 根重定向，无内容
}


def _generate_all_tests():
    """在 import 时注册所有测试用例到 pytest"""
    all_routes = get_routes_by_role()

    for role, creds in ACCOUNTS.items():
        role_routes = all_routes.get(role, [])
        for route in role_routes:
            if route in _EXCLUDED_ROUTES:
                continue

            test_name = f"test_{role}_{route.lstrip('#/').replace('/', '_').replace('{', '').replace('}', '').replace('-', '_')[:60]}"

            def make_test(r: str, rl: str, u: str, p: str):
                def _test(browser_instance, report_page_result):
                    result = audit_page(
                        browser=browser_instance,
                        role=rl,
                        route=r,
                        username=u,
                        password=p,
                    )
                    report_page_result(None, result)
                    if result.status == "crash":
                        pytest.fail(f"CRASH on {r}: {result.error_msg}")
                _test.__doc__ = f"[{rl.upper()}] {r}"
                _test._audit_role = rl
                return _test

            globals()[test_name] = make_test(route, role, creds["username"], creds["password"])


_generate_all_tests()


# ─────────────────────────────────────────────────────────────────────────────
# 钩子：生成报告
# ─────────────────────────────────────────────────────────────────────────────

def pytest_sessionfinish(session, exitstatus):
    global _page_results
    if _page_results:
        generate_report(_page_results, "playwright_audit_report.json")


# ─────────────────────────────────────────────────────────────────────────────
# CLI 入口（直接运行，非 pytest）
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("慧学平台 Playwright 全路由审计")
    print(f"目标: {BASE_URL}")
    print("=" * 60)

    results: list[PageResult] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        # ── 获取 token（用于动态 ID）──────────────────────────────
        token = ""
        try:
            import requests
            for endpoint in ["/api/v1/login", "/api/login"]:
                r = requests.post(
                    f"{API_URL}{endpoint}",
                    json={"username": "admin", "password": "admin123"},
                    timeout=10,
                )
                if r.ok:
                    break
            if r.ok:
                data = r.json()
                _d = data.get("data") or data
                token = (
                    (_d.get("token") or {}).get("access_token")
                    if isinstance(_d.get("token"), dict)
                    else _d.get("token")
                    or data.get("token", {}).get("access_token")
                    or data.get("access_token")
                    or ""
                )
        except Exception as e:
            print(f"[!] 无法获取 token（用于动态 ID）: {e}")

        ids = fetch_dynamic_ids(API_URL, token) if token else {}
        print(f"[i] 动态 IDs: { {k: v[:2] for k, v in ids.items()} }")
        print()

        # ── 按角色登录并审计 ────────────────────────────────────
        all_routes = get_routes_by_role()

        for role, creds in ACCOUNTS.items():
            print(f"\n{'─' * 60}")
            print(f"  角色: {role} ({creds['username']})")
            print(f"{'─' * 60}")

            # 每个角色一个 Context（cookie 共享）
            ctx = browser.new_context(
                viewport={"width": 1440, "height": 900},
                locale="zh-CN",
            )
            page = ctx.new_page()

            # 注入监听器
            listener = AuditListener(role, "login", f"{BASE_URL}/#/")
            page.on("console", listener.on_console)
            page.on("pageerror", lambda e, _l=listener: _l.js_exceptions.append({"message": str(e)[:200]}))

            # 登录
            login_ok = do_login(page, creds["username"], creds["password"])
            url_after = page.url
            if not login_ok:
                print(f"  [!] 登录失败（do_login=False），当前URL: {url_after}")
                ctx.close()
                continue
            if not is_logged_in(page):
                print(f"  [!] 登录失败（is_logged_in=False），当前URL: {url_after}")
                ctx.close()
                continue

            print(f"  [✓] 登录成功")

            # 审计路由
            role_routes = expand_routes(all_routes.get(role, []), ids)
            print(f"  [i] 共 {len(role_routes)} 个路由（含动态 ID 展开）")
            print()

            for route in role_routes:
                if route in _EXCLUDED_ROUTES:
                    continue

                # 每个路由独立 page（避免状态污染）
                p = ctx.new_page()
                l = AuditListener(role, route, f"{BASE_URL}/{route.lstrip('#')}")
                p.on("console", l.on_console)
                p.on("requestfailed", l.on_request_failed)
                p.on("response", l.on_response)
                p.on("crash", l.on_crash)
                p.on("pageerror", lambda e, _l=l: _l.js_exceptions.append({"message": str(e)[:200]}))

                start = time.monotonic()
                try:
                    resp = p.goto(f"{BASE_URL}/{route.lstrip('#')}",
                                  wait_until="domcontentloaded",
                                  timeout=NAVIGATION_TIMEOUT_MS)
                    l.response_status = resp.status if resp else None
                    try:
                        p.wait_for_load_state("networkidle", timeout=NETWORK_IDLE_MS)
                    except Exception:
                        pass
                    p.wait_for_timeout(1500)
                except Exception as e:
                    l.error_msg = str(e)[:200]
                    l.crashed = True
                finally:
                    l.load_time_ms = round((time.monotonic() - start) * 1000, 1)
                    result = l.build_result()
                    results.append(result)
                    p.close()

                    status_icon = {"ok": "✓", "warning": "⚠", "error": "✗", "crash": "☠"}[result.status]
                    http_s = f" HTTP:{result.status_code}" if result.status_code else ""
                    err_s = f" | {len(result.console_errors)} console_err" if result.console_errors else ""
                    js_s = f" | {len(result.js_exceptions)} js_exc" if result.js_exceptions else ""
                    print(f"  {status_icon} {result.route:<60}{http_s}{err_s}{js_s}")

            ctx.close()

        browser.close()

    # ── 生成报告 ────────────────────────────────────────────────
    print()
    generate_report(results, "playwright_audit_report.json")
