"""
慧学高校大数据API主应用
"""
# Verification successful: Indexing is now fast with selective binary exclusion for 13GB data.

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.ai_gate import require_ai_enabled
import logging
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局缓存：存储最近的 training_id/user_id 对，用于 fallback 机制
# 格式：{session_key: {"training_id": id, "user_id": id, "timestamp": time}}
_session_params_cache = {}

# 创建FastAPI应用
# 触发重载
app = FastAPI(
    title="慧学 API主应用",
    description="基于FastAPI和PostgreSQL的后端API - 课程实践模块",
    version="1.0.0"
)

# 配置CORS - 允许前端访问（包括视频流式播放）
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Vite开发服务器
        "http://127.0.0.1:3001",
        "http://localhost:3005",  # Playwright E2E测试服务器
        "http://127.0.0.1:3005",
        "http://localhost:5173",  # Vite 测试服务器
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],  # 视频流式播放需要
)

# 添加中间件来捕获路由解析错误
@app.middleware("http")
async def catch_routing_errors(request: Request, call_next):
    """
    捕获路由解析错误，特别是 "Not enough segments" 错误
    """
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        error_msg = str(e)
        if "Not enough segments" in error_msg or "not enough segments" in error_msg.lower():
            logger.error(f"[路由错误] ❌ 路由解析失败: {error_msg}")
            logger.error(f"[路由错误] ❌ 请求URL: {request.url}")
            logger.error(f"[路由错误] ❌ 请求路径: {request.url.path}")
            logger.error(f"[路由错误] ❌ 请求方法: {request.method}")
            import traceback
            logger.error(f"[路由错误] ❌ 错误堆栈: {traceback.format_exc()}")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=422,
                content={"detail": f"路由解析失败: {error_msg}", "msg": "Not enough segments", "url": str(request.url)}
            )
        raise

# 导入并注册路由器
from app.api import auth
from app.api.v1.endpoints import health
from app.api.v1.endpoints import users
from app.api.v1.endpoints import posts
from app.api.v1.endpoints import courses
from app.api.v1.endpoints import practices
from app.api.v1.endpoints import tasks
from app.api.v1.endpoints import stages
from app.api.v1.endpoints import classrooms
from app.api.v1.endpoints import students
from app.api.v1.endpoints import grades
from app.api.v1.endpoints import exams
from app.api.v1.endpoints import resources
from app.api.v1.endpoints import analytics
from app.api.v1.endpoints import sessions
import mimetypes

mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
mimetypes.add_type('application/vnd.ms-powerpoint', '.ppt')
mimetypes.add_type('video/mp4', '.mp4')

from app.api.v1.endpoints import question_library
from app.api.v1.endpoints import organization
from app.api.v1.endpoints import paper_library
from app.api.v1.endpoints import course_materials
from app.api.v1.endpoints import practice_materials
from app.api.v1.endpoints import trainings
from app.api.v1.endpoints import system_management
from app.api.v1.endpoints import file_upload
from app.api.v1.endpoints import file_serve
# from app.api.v1.endpoints import debug_resources
from app.api.v1.endpoints import generation
from app.api.v1.endpoints import storage
from app.api.v1.endpoints import compatibility
from app.api.v1.endpoints import text_explain
from app.api.v1.endpoints import ai_assistant
from app.api.v1.endpoints import ai_features
from app.api.v1.endpoints import ai_generation
# from app.api.v1.endpoints import course_resources
from app.api.v1.endpoints import common
from app.api.v1.endpoints import resource_import
from app.api.v1.endpoints import training_environments
from app.api.v1.endpoints import course_management
from app.api.v1.endpoints import teaching_resources
from app.api.v1.endpoints import usage_statistics
from app.api.v1.endpoints import student_dashboard
from app.api.v1.endpoints import project_canvas
from app.api.v1.endpoints import grading

# 注册路由器
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(health.router)
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(posts.router, prefix="/api/v1", tags=["posts"])
app.include_router(courses.router, prefix="/api/v1", tags=["courses"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(stages.router, prefix="/api/v1", tags=["stages"])
app.include_router(classrooms.router, prefix="/api/v1", tags=["classrooms"])
app.include_router(students.router, prefix="/api/v1", tags=["students"])
app.include_router(grades.router, prefix="/api/v1", tags=["grades"])
app.include_router(exams.router, tags=["exams"])
app.include_router(resources.router, prefix="/api/v1", tags=["resources"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])
app.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
app.include_router(question_library.router, prefix="/api/v1/question-library", tags=["试题库"])
app.include_router(organization.router, prefix="/api/v1/organization", tags=["组织架构"])
app.include_router(paper_library.router, tags=["试卷库"])
app.include_router(course_materials.router, prefix="/api", tags=["课程教材"])
app.include_router(practice_materials.router, prefix="/api", tags=["微型实验"])
app.include_router(trainings.router, prefix="/api/v1/trainings", tags=["实训管理"])
app.include_router(system_management.router, prefix="/api/v1/system", tags=["系统管理"])
app.include_router(file_upload.router, prefix="/api/v1/files", tags=["文件上传"])
app.include_router(file_serve.router, prefix="/api/v1/files", tags=["文件服务"])
# app.include_router(debug_resources.router, prefix="/api/v1", tags=["资源调试"])
# app.include_router(course_resources.router, prefix="/api/v1", tags=["课程资源"])
app.include_router(generation.router, prefix="/api/v1", tags=["关卡生成"], dependencies=[Depends(require_ai_enabled)])
app.include_router(storage.router, prefix="/api/v1/storage", tags=["对象存储"])
app.include_router(compatibility.router, prefix="/api/v1", tags=["兼容性路由"])
app.include_router(common.router, tags=["通用API"])
app.include_router(text_explain.router, prefix="/api/v1/text-explain", tags=["文本解释"], dependencies=[Depends(require_ai_enabled)])
# 测试路由
@app.post("/api/v1/ai/test")
async def test_ai():
    return {"message": "AI test route works"}

app.include_router(ai_assistant.router, prefix="/api/v1", tags=["AI助教"], dependencies=[Depends(require_ai_enabled)])
app.include_router(ai_features.router, prefix="/api/v1", tags=["AI Features"])
app.include_router(ai_generation.router, prefix="/api/v1", tags=["AI 实践课生成器"])
app.include_router(resource_import.router, prefix="/api/v1", tags=["资源导入"])
app.include_router(training_environments.router, prefix="/api/v1", tags=["实训环境"])
app.include_router(practices.router, prefix="/api/v1", tags=["practices"])
app.include_router(course_management.router, prefix="/api/v1/course-management", tags=["课程管理"])
app.include_router(teaching_resources.router, prefix="/api/v1/teaching-resources", tags=["教学资源管理"])
app.include_router(usage_statistics.router, prefix="/api/v1/usage-statistics", tags=["使用统计"])
app.include_router(student_dashboard.router, prefix="/api/v1/student", tags=["学生仪表板"])
app.include_router(project_canvas.router, prefix="/api/v1/project-canvas", tags=["项目画布"])
app.include_router(grading.router, prefix="/api/v1", tags=["成绩管理"])

# 添加通配路由，将未匹配的 /api/v1/* 请求转发到代理端点（用于 Superset API）
# 注意：这个路由必须在其他路由之后注册，作为最后的fallback
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.api_route("/api/v1/environments/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], include_in_schema=False)
async def catch_all_api_proxy(request: Request, path: str):
    """
    代理 Superset API 请求到相应的容器
    只处理 /api/v1/environments/proxy/* 路径
    """
    import os
    # 立即写入stderr
    import sys
    sys.stderr.write(f"[CATCH_ALL] PID={os.getpid()} path={path} called\n")
    sys.stderr.flush()

    # 写入文件
    try:
        with open("/tmp/catch_all.log", "a") as f:
            f.write(f"PID={os.getpid()} path={path} called\n")
            f.flush()
    except Exception:
        pass

    logger = logging.getLogger(__name__)
    logger.info(f"[通配路由] ========== 通配路由被触发 ==========")
    logger.info(f"[通配路由] 请求URL: {request.url}")
    logger.info(f"[通配路由] 请求路径: {request.url.path}")
    logger.info(f"[通配路由] URL路径段数: {len(request.url.path.split('/'))}")
    logger.info(f"[通配路由] URL路径段: {request.url.path.split('/')}")
    logger.info(f"[通配路由] 路径参数: {repr(path)}")
    logger.info(f"[通配路由] 路径参数类型: {type(path)}")
    logger.info(f"[通配路由] 路径参数长度: {len(path) if path else 0}")
    logger.info(f"[通配路由] 查询参数: {dict(request.query_params)}")

    # 关键修复：处理代理路径并转发到正确的处理器
    if path.startswith("proxy/"):
        logger.info(f"[通配路由] 🔄 转发代理路径到代理端点: {path}")
        # 提取代理路径后面的部分
        proxy_path = path.replace("proxy/", "", 1)
        logger.info(f"[通配路由] 🔄 提取的代理路径: {proxy_path}")
        
        # 导入所需模块
        from app.core.database import get_db, SessionLocal
        from app.services.container_manager import container_manager
        import httpx
        
        try:
            # 从查询参数中获取training_id和user_id
            training_id = request.query_params.get("training_id")
            user_id = request.query_params.get("user_id")
            referer = request.headers.get("referer", "")
            
            # 如果没有参数，从referer中提取
            if not training_id or not user_id:
                import re
                training_match = re.search(r'training_id=(\d+)', referer)
                user_match = re.search(r'user_id=(\d+)', referer)
                if training_match:
                    training_id = training_match.group(1)
                if user_match:
                    user_id = user_match.group(1)
            
            if not training_id or not user_id:
                logger.warning(f"[通配路由-代理] ⚠️ 缺少training_id或user_id")
                return JSONResponse(
                    status_code=400,
                    content={"detail": "缺少training_id或user_id参数"}
                )
            
            # 获取数据库会话
            db_session = SessionLocal()
            
            # 获取容器信息
            status_info = container_manager.get_container_status_by_training(int(training_id), int(user_id), db_session)
            if status_info["status"] != "running":
                logger.warning(f"[通配路由-代理] ⚠️ 容器未运行: {status_info['status']}")
                return JSONResponse(
                    status_code=503,
                    content={"detail": f"容器未运行: {status_info['status']}"}
                )
            
            # 获取容器端口
            port = status_info.get("host_port")
            if not port:
                logger.warning(f"[通配路由-代理] ⚠️ 无法获取容器端口")
                return JSONResponse(
                    status_code=500,
                    content={"detail": "无法获取容器端口"}
                )
            
            # 构建目标URL
            target_url = f"http://localhost:{port}/{proxy_path}"
            if request.url.query:
                # 移除training_id和user_id参数
                query_params = dict(request.query_params)
                query_params.pop("training_id", None)
                query_params.pop("user_id", None)
                if query_params:
                    from urllib.parse import urlencode
                    target_url += f"?{urlencode(query_params)}"
            
            logger.info(f"[通配路由-代理] 🔄 转发请求到: {target_url}")
            
            # 获取请求体
            body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
            
            # 转发请求（使用持久化 cookie 的 client）
            cookies = {}
            async with httpx.AsyncClient(timeout=30.0, cookies=cookies) as client:
                headers = dict(request.headers)
                headers.pop("host", None)
                headers.pop("connection", None)
                headers["accept-encoding"] = "identity"
                
                # 第一次请求
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=body,
                    follow_redirects=False
                )
                
                logger.info(f"[通配路由-代理] 第一次请求状态: {response.status_code}")
                
                # 如果是重定向，自动跟随并维持 cookie
                redirect_count = 0
                while response.status_code in [301, 302, 303, 307, 308] and redirect_count < 10:
                    redirect_url = response.headers.get("location")
                    if not redirect_url:
                        break
                    
                    redirect_count += 1
                    
                    # 处理相对重定向URL
                    if redirect_url.startswith("/"):
                        # 相对路径，需要转换为绝对路径（Superset容器地址）
                        redirect_url = f"http://localhost:{port}{redirect_url}"
                    
                    logger.info(f"[通配路由-代理] 跟随重定向 {redirect_count}: {redirect_url}")
                    
                    # 根据状态码决定下一个请求的方法与body
                    use_get = response.status_code in [301, 302, 303]
                    next_method = "GET" if use_get else request.method
                    next_body = body if not use_get and request.method in ["POST", "PUT", "PATCH"] else None
                    next_headers = dict(headers)
                    if use_get:
                        next_headers.pop("content-length", None)
                
                    # 保留 cookie 进行下一次请求
                    response = await client.request(
                        method=next_method,
                        url=redirect_url,
                        headers=next_headers,
                        content=next_body,
                        follow_redirects=False
                    )
                    logger.info(f"[通配路由-代理] 重定向后状态: {response.status_code}")
                
                # 返回最终响应（保持 Superset 原始字节流，避免重复解压导致乱码）
                from fastapi.responses import Response
                
                final_headers = dict(response.headers)
                content = response.content
                
                # 移除可能导致问题的 headers
                final_headers.pop("transfer-encoding", None)  # FastAPI 会自动处理分块传输
                final_headers.pop("content-encoding", None)  # httpx 已自动解压，避免浏览器重复解码
                final_headers.pop("content-length", None)  # 交由 FastAPI 根据实际字节计算
                
                # 修复CSP frame-ancestors限制（允许所有源嵌入）
                csp = final_headers.get("content-security-policy", "")
                if "frame-ancestors" in csp:
                    # 移除 frame-ancestors 指令，允许任何源嵌入
                    csp = "; ".join([part for part in csp.split(";") if "frame-ancestors" not in part])
                    if csp.strip():
                        final_headers["content-security-policy"] = csp
                    else:
                        final_headers.pop("content-security-policy", None)
                
                # 添加防缓存头确保浏览器不会使用旧的二进制数据
                final_headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0, public"
                final_headers["Pragma"] = "no-cache"
                final_headers["Expires"] = "0"
                
                content_type = final_headers.get("content-type", "")
                if (
                    content
                    and content_type
                    and "text/html" in content_type.lower()
                ):
                    try:
                        html_text = content.decode("utf-8", errors="ignore")
                        from urllib.parse import urlsplit, urlencode, parse_qsl
                        
                        proxy_prefix = "/api/v1/environments/proxy"
                        static_prefixes = ("/static/", "/assets/", "/appbuilder/")
                        
                        def build_proxy_path(original_path: str) -> str:
                            if not original_path or original_path.startswith(proxy_prefix):
                                return original_path
                            split_result = urlsplit(original_path)
                            if not split_result.path.startswith(static_prefixes):
                                return original_path
                            query_pairs = dict(parse_qsl(split_result.query))
                            if training_id:
                                query_pairs.setdefault("training_id", training_id)
                            if user_id:
                                query_pairs.setdefault("user_id", user_id)
                            proxied_path = f"{proxy_prefix}{split_result.path}"
                            if query_pairs:
                                proxied_path = f"{proxied_path}?{urlencode(query_pairs, doseq=True)}"
                            return proxied_path
                        
                        import re
                        attr_pattern = re.compile(
                            r'(?P<attr>(?:href|src)=)(?P<quote>["\'])(?P<path>/(?:static|assets|appbuilder)/[^"\']+)(?P=quote)',
                            flags=re.IGNORECASE
                        )
                        url_pattern = re.compile(
                            r'url\((?P<quote>["\']?)(?P<path>/(?:static|assets|appbuilder)/[^)\'"]+)(?P=quote)\)',
                            flags=re.IGNORECASE
                        )
                        
                        def replace_attr(match):
                            attr = match.group("attr")
                            quote = match.group("quote")
                            path_value = match.group("path")
                            proxied = build_proxy_path(path_value)
                            return f'{attr}{quote}{proxied}{quote}'
                        
                        rewritten_html = attr_pattern.sub(replace_attr, html_text)
                        rewritten_html = url_pattern.sub(
                            lambda m: f"url({m.group('quote')}{build_proxy_path(m.group('path'))}{m.group('quote')})",
                            rewritten_html
                        )
                        
                        if rewritten_html != html_text:
                            content = rewritten_html.encode("utf-8")
                            final_headers["content-length"] = str(len(content))
                            logger.info("[通配路由-代理] ✅ 已在HTML中重写静态资源路径为代理地址")
                    except Exception as rewrite_err:
                        logger.warning("[通配路由-代理] ⚠️ HTML 静态资源重写失败: %s", rewrite_err, exc_info=True)
                
                logger.info(f"[通配路由-代理] 最终响应状态: {response.status_code}, 内容长度: {len(content)}")
                logger.info(f"[通配路由-代理] 响应 cookie: {response.cookies}")
                logger.info(f"[通配路由-代理] 修改后的CSP: {final_headers.get('content-security-policy', 'N/A')}")
                logger.info(f"[通配路由-代理] 防缓存头已添加")
                
                return Response(
                    content=content,
                    status_code=response.status_code,
                    headers=final_headers
                )
        
        except Exception as e:
            logger.error(f"[通配路由-代理] ❌ 代理请求失败: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"detail": f"代理请求失败: {str(e)}"}
            )
        finally:
            try:
                db_session.close()
            except Exception:
                pass
    
    
    # 已知的 API 路由前缀（这些应该由其他路由处理，不应被通配路由拦截）
    known_api_prefixes = [
        "stages",
        "practices",
        "courses",
        "classrooms",
        "students",
        "teachers",
        "trainings",
        "custom-practices",
        "jupyter",  # Jupyter environment endpoints
        "environments",  # Environment management endpoints
        "bi",  # BI endpoints
        "ai",  # AI endpoints
        "teaching-resources",  # Teaching resources endpoints
        "users",
        "posts",
        "health",
        "grades",
        "exams",
        "resources",
        "analytics",
        "sessions",
        "question-library",
        "organization",
        "paper-library",
        "course-materials",
        "practice-materials",
        "system",
        "files",
        "generation",
        "storage",
        "text-explain",
        "ai/test",
        "ai-assistant",
        "ai-features",
        "resource-import",
        "course-management",
        "usage-statistics",
        "student",
        "project-canvas",
    ]

    # 检查是否是已知的 API 路由
    is_known_api = any(path.startswith(prefix) for prefix in known_api_prefixes)
    if is_known_api:
        # 如果是已知的 API 路由，返回 None 让 FastAPI 继续匹配其他路由
        logger.info(f"[通配路由] ➡️ 已知 API 路由，返回 None 让 FastAPI 继续匹配: /api/v1/{path}")
        return None

    # 检查是否是 Superset API 路径（path 不包含 /api/v1/ 前缀）
    superset_api_prefixes = [
        "dashboard",
        "chart",
        "dataset",
        "database",
        "query",
        "explore",
        "security",
        "csrf",
        "log",
    ]

    # 检查路径是否匹配 Superset API（path 应该以这些前缀开头）
    is_superset_api = any(path.startswith(prefix) for prefix in superset_api_prefixes)
    
    if is_superset_api:
        # 从查询参数或 referer 中提取 training_id 和 user_id
        training_id = request.query_params.get("training_id")
        user_id = request.query_params.get("user_id")
        
        # 如果没有，尝试从 referer 中提取
        if not training_id or not user_id:
            referer = request.headers.get("referer", "")
            if referer:
                import re
                training_match = re.search(r'training_id=(\d+)', referer)
                user_match = re.search(r'user_id=(\d+)', referer)
                if training_match:
                    training_id = training_match.group(1)
                if user_match:
                    user_id = user_match.group(1)
        
        # 如果仍然没有，尝试从 iframe 的原始 URL 中提取（通过检查父窗口的 iframe src）
        # 注意：这需要前端配合，在请求头中添加 x-iframe-src 或类似的头部
        if not training_id or not user_id:
            iframe_src = request.headers.get("x-iframe-src", "")
            if iframe_src:
                import re
                training_match = re.search(r'training_id=(\d+)', iframe_src)
                user_match = re.search(r'user_id=(\d+)', iframe_src)
                if training_match:
                    training_id = training_match.group(1)
                if user_match:
                    user_id = user_match.group(1)
        
        # 如果仍然没有，尝试从当前请求的完整 URL 中提取
        if not training_id or not user_id:
            full_url = str(request.url)
            import re
            training_match = re.search(r'training_id=(\d+)', full_url)
            user_match = re.search(r'user_id=(\d+)', full_url)
            if training_match:
                training_id = training_match.group(1)
            if user_match:
                user_id = user_match.group(1)
        
        # 如果仍然没有，尝试从自定义请求头中提取
        # 前端注入脚本可能会添加 X-Training-Id 和 X-User-Id 头
        if not training_id or not user_id:
            training_id_header = request.headers.get("x-training-id") or request.headers.get("X-Training-Id")
            user_id_header = request.headers.get("x-user-id") or request.headers.get("X-User-Id")
            if training_id_header:
                training_id = training_id_header
            if user_id_header:
                user_id = user_id_header
            if training_id_header or user_id_header:
                logger.info(f"[通配路由] ✅ 从自定义请求头中提取: training_id={training_id}, user_id={user_id}")
        
        # 最后的 fallback：如果仍然没有，尝试从缓存中恢复
        if not training_id or not user_id:
            # 尝试从 session cache 中获取最近的 training_id/user_id
            # 使用 IP + user-agent 作为 session key
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            session_key = f"{client_ip}_{hash(user_agent)}"
            
            if session_key in _session_params_cache:
                cached = _session_params_cache[session_key]
                if not training_id and "training_id" in cached:
                    training_id = cached["training_id"]
                if not user_id and "user_id" in cached:
                    user_id = cached["user_id"]
                logger.info(f"[通配路由] ✅ 从缓存中恢复: training_id={training_id}, user_id={user_id}")
            else:
                logger.info(f"[通配路由] ⚠️ 无法从请求参数、referer、自定义头或缓存中提取 training_id/user_id")
                logger.info(f"[通配路由] ⚠️ 这可能是因为 iframe 内的 Superset 代码直接调用了 API，没有经过前端拦截器")
        
        # 如果成功提取到参数，保存到缓存中以供后续使用
        if training_id and user_id:
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "")
            session_key = f"{client_ip}_{hash(user_agent)}"
            from datetime import datetime
            _session_params_cache[session_key] = {
                "training_id": training_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"[通配路由] 💾 将参数保存到缓存: {session_key}")
        
        logger.info(f"[通配路由] is_superset_api={is_superset_api}, training_id={training_id}, user_id={user_id}")
        
        if training_id and user_id:
            # 重定向到代理端点
            from fastapi.responses import RedirectResponse
            # path 格式可能是 "dashboard/..." 或 "/api/v1/dashboard/..."
            # 确保 path 以 / 开头
            if not path.startswith("/"):
                path = "/" + path
            # 如果 path 以 /api/v1/ 开头，去掉这个前缀（因为代理端点期望的是 dashboard/...）
            if path.startswith("/api/v1/"):
                path = path[len("/api/v1/"):]
            # 构建代理URL：/api/v1/environments/proxy/dashboard/...
            proxy_url = f"/api/v1/environments/proxy/{path}?training_id={training_id}&user_id={user_id}"
            if request.url.query:
                # 如果 query 中已经有 training_id 或 user_id，需要避免重复
                query_params = dict(request.query_params)
                query_params.pop("training_id", None)
                query_params.pop("user_id", None)
                if query_params:
                    from urllib.parse import urlencode
                    proxy_url += f"&{urlencode(query_params)}"
            logger.info(f"[通配路由] ✅ 重定向 Superset API 请求: {request.url.path} -> {proxy_url}")
            return RedirectResponse(url=proxy_url, status_code=307)
        elif is_superset_api:
            logger.warning(f"[通配路由] ⚠️ 检测到 Superset API 但缺少参数: training_id={training_id}, user_id={user_id}")
            logger.warning(f"[通配路由] ⚠️ 请求URL: {request.url}")
            logger.warning(f"[通配路由] ⚠️ 请求头: {dict(request.headers)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Missing training_id or user_id for Superset API request: /api/v1/{path}"}
            )
    
    # 如果不是 Superset API，返回 404
    logger.info(f"[通配路由] 🚫 不是 Superset API 请求，返回 404: /api/v1/{path}")
    return JSONResponse(
        status_code=404,
        content={"detail": f"API endpoint not found: /api/v1/{path}"}
    )

# 应用启动和关闭事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("应用启动中...")

    # 启动数据一致性监控（临时禁用以排查问题）
    # try:
    #     from app.utils.consistency_scheduler import start_consistency_monitoring
    #     start_consistency_monitoring()
    #     logger.info("数据一致性监控服务已启动")
    # except Exception as e:
    #     logger.error(f"启动数据一致性监控失败: {e}")
    logger.info("数据一致性监控服务已禁用（调试模式）")

    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("应用关闭中...")

    # 停止数据一致性监控
    try:
        from app.utils.consistency_scheduler import stop_consistency_monitoring
        stop_consistency_monitoring()
        logger.info("数据一致性监控服务已停止")
    except Exception as e:
        logger.error(f"停止数据一致性监控失败: {e}")

    logger.info("应用关闭完成")

# 配置静态文件服务
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/api/static", StaticFiles(directory=static_path), name="static")

# 挂载课程资源目录
# 优先使用环境变量，然后 static/resources (主)，再 ziyuan_data (兼容)
ziyuan_data_path = os.environ.get("HUIXUE_RESOURCE_DIR") or os.environ.get("RESOURCE_BASE_DIR")
if not ziyuan_data_path:
    # 优先使用 backend/static/resources, 然后 ziyuan_data
    _backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _static_res = os.path.join(_backend_dir, "static", "resources")
    _ziyuan = os.path.join(os.path.dirname(_backend_dir), "ziyuan_data")
    ziyuan_data_path = _static_res if os.path.exists(_static_res) else _ziyuan
ziyuan_data_path = os.path.abspath(ziyuan_data_path)

if os.path.exists(ziyuan_data_path):
    # 创建一个子应用来提供静态文件，以便应用CORS中间件
    # FastAPI默认的CORSMiddleware不适用于挂载的Starlette应用
    static_app = FastAPI(title="Static Resources")
    static_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
    )
    static_app.mount("/", StaticFiles(directory=ziyuan_data_path, follow_symlink=True), name="ziyuan_resources")
    app.mount("/static/resources", static_app)
    logger.info(f"已挂载资源目录并启用CORS: {ziyuan_data_path} -> /static/resources")
else:
    logger.warning(f"资源目录不存在: {ziyuan_data_path}")

# 自定义OpenAPI生成函数，修复practice相关的tags
def custom_openapi():
    """自定义OpenAPI生成函数，修复tags中的旧术语"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("自定义OpenAPI函数被调用")
    
    # 强制清除缓存，每次都重新生成
    app.openapi_schema = None
    
    from fastapi.openapi.utils import get_openapi
    
    # 生成OpenAPI规范
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    logger.info(f"生成的OpenAPI规范包含 {len(openapi_schema.get('paths', {}))} 个路径")
    
    # 修复practice相关的tags
    paths = openapi_schema.get('paths', {})
    fixed_count = 0
    for path, methods in paths.items():
        if 'practice' in path.lower() and path.startswith('/api/practice'):
            for method, details in methods.items():
                tags = details.get('tags', [])
                if tags:
                    old_tags = tags.copy()
                    # 移除旧术语"元子实践"和"practice-materials"
                    new_tags = [tag for tag in tags if '元子' not in str(tag) and tag != 'practice-materials']
                    # 确保有新术语"微型实验"
                    if '微型实验' not in new_tags:
                        new_tags.insert(0, '微型实验')  # 放在第一位
                    details['tags'] = new_tags
                    
                    if old_tags != new_tags:
                        fixed_count += 1
                        logger.info(f"修复路径 {method.upper()} {path}: {old_tags} -> {new_tags}")
                    
                    # 修复description中的旧术语
                    if 'description' in details:
                        description = details['description']
                        old_desc = description
                        description = description.replace('元子实践', '微型实验')
                        description = description.replace('元子课', '微课')
                        details['description'] = description
                        if old_desc != description:
                            logger.info(f"修复description: {path}")
                    
                    # 修复summary中的旧术语
                    if 'summary' in details:
                        summary = details['summary']
                        old_summary = summary
                        summary = summary.replace('元子实践', '微型实验')
                        summary = summary.replace('元子课', '微课')
                        details['summary'] = summary
                        if old_summary != summary:
                            logger.info(f"修复summary: {path}")
    
    logger.info(f"共修复 {fixed_count} 个路径的tags")
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# 替换默认的openapi函数
app.openapi = custom_openapi

# 确保/openapi.json路由也使用自定义函数
# FastAPI在setup时会创建/openapi.json路由，需要重新设置
for route in app.routes:
    if hasattr(route, 'path') and route.path == '/openapi.json':
        # 创建包装函数，确保调用自定义函数
        def openapi_wrapper():
            return custom_openapi()
        route.endpoint = openapi_wrapper
        logger.info("已替换/openapi.json路由的端点为自定义函数")
        break
