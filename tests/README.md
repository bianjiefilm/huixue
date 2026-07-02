# 慧学云平台 - 测试套件

慧学云平台自动化测试代码，覆盖 L1（API 合约测试）、L2（UI 交互测试）和 L0（基础设施检查）。

## 环境配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `TEST_BASE_URL` | `http://100.74.141.3:3000` | 前端地址 |
| `TEST_API_URL` | `http://100.74.141.3:8000` | 后端 API 地址 |
| `TEST_JUPYTER_URL` | `http://100.74.141.3:8888` | Jupyter 服务地址 |
| `PLAYWRIGHT_HEADLESS` | `true` | Playwright 是否无头模式 |
| `PLAYWRIGHT_SLOWMO` | `0` | Playwright 操作延迟（毫秒） |
| `PLAYWRIGHT_VIEWPORT_WIDTH` | `1920` | 浏览器视口宽度 |
| `PLAYWRIGHT_VIEWPORT_HEIGHT` | `1080` | 浏览器视口高度 |

### 覆盖网络要求

测试通过 Tailscale VPN 网络执行，已配置超时：
- `TIMEOUT_SHORT = 15s` - 简单 GET 请求
- `TIMEOUT_MEDIUM = 30s` - POST / PATCH 请求
- `TIMEOUT_LONG = 60s` - 文件下载、容器启动

## 安装依赖

```bash
cd tests
pip install -r requirements_test.txt

# 安装 Playwright 浏览器
playwright install chromium
```

## 执行测试

### 全部测试

```bash
cd /Users/jimfu/Work/huixue
pytest tests/ -v
```

### 按层级执行

```bash
# L1 API 合约测试
pytest tests/l1/ -v

# L2 UI 交互测试
pytest tests/l2/ -v --browser chromium

# L0 基础设施检查
bash tests/l0/run_all.sh
```

### 按模块执行

```bash
# 课堂管理 API
pytest tests/l1/test_m14_classroom_api.py -v
pytest tests/l1/test_m15_classroom_detail_api.py -v

# BI 可视化
pytest tests/l1/test_m11_bi_api.py -v
pytest tests/l2/test_m11_bi_ui.py -v

# Jupyter 编码训练
pytest tests/l1/test_m13_jupyter_api.py -v
pytest tests/l2/test_m13_jupyter_ui.py -v
```

### 按 marker 执行

```bash
pytest tests/ -m "l1 and not slow" -v     # 快速 L1 测试
pytest tests/ -m l2 -v                      # 所有 L2 测试
pytest tests/ -m classroom -v                # 课堂相关测试
pytest tests/ -m bi -v                      # BI 相关测试
pytest tests/ -m jupyter -v                 # Jupyter 相关测试
```

### Playwright UI 测试（特定环境变量）

```bash
PLAYWRIGHT_HEADLESS=false TEST_BASE_URL=http://localhost:3000 pytest tests/l2/ -v
```

## 测试账户

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher1 | teacher123 |
| 学生 | student1 | student123 |

## 测试层次结构

```
tests/
├── conftest.py           # 全局 fixtures（认证、客户端、URL 配置）
├── requirements_test.txt  # 测试依赖
├── pytest.ini            # pytest 配置
│
├── l0/                   # 基础设施检查（Shell 脚本）
│   ├── check_docker.sh
│   ├── check_postgres.sh
│   ├── check_redis.sh
│   ├── check_nfs.sh
│   └── run_all.sh
│
├── l1/                   # API 合约测试（pytest + requests）
│   ├── conftest.py       # L1 专用 fixtures（测试课堂等）
│   ├── test_m11_bi_api.py
│   ├── test_m13_jupyter_api.py
│   ├── test_m14_classroom_api.py
│   └── test_m15_classroom_detail_api.py
│
└── l2/                   # UI 交互测试（Playwright）
    ├── conftest.py       # Playwright fixtures
    ├── test_m11_bi_ui.py
    ├── test_m13_jupyter_ui.py
    └── test_m14_classroom_ui.py
```

## 并发安全

每个测试使用 `unique_suffix` fixture 生成独立的数据隔离后缀：

```python
# 格式: {run_id}_{8位hash}
# 示例: a1b2c3d4_12345678
```

测试数据命名示例：
- `Jupyter测试_a1b2c3d4_12345678`
- `BI场景_a1b2c3d4_87654321`

## API 多路径兼容

测试自动尝试多个 API 路径前缀，避免因路径不一致导致失败：

```python
# 课堂 API
"/api/v1/classrooms"
"/api/classrooms"

# BI API
"/api/bi/scenes"
"/api/v1/bi/scenes"
"/api/visual/scenes"

# Jupyter API
"/api/jupyter/sessions"
"/api/v1/jupyter/sessions"
"/api/environments/sessions"
```

如果所有路径均返回 5xx，测试自动跳过（`pytest.skip`）。

## 认证机制

测试通过 `POST /api/login` 获取 JWT token：

```python
POST /api/login
Body: {"username": "admin", "password": "admin123"}
Response: {"token": {"access_token": "..."}, "user": {...}}
```

Token 通过 `localStorage.setItem('access_token', token)` 或 `Authorization: Bearer` header 注入。

## 清理机制

- L1 API 测试：使用 `yield` fixture + teardown 自动清理
- L2 UI 测试：每个测试使用独立的浏览器上下文（`function` scope）
- 测试账户独立：`test_run_id` session scope，确保同一测试运行内数据隔离

## 故障排查

### 测试跳过（SKIPPED）

检查原因：
```bash
pytest tests/ -v -r s  # 显示跳过原因
```

### 查看测试报告

```bash
# 生成 HTML 报告
pytest tests/ --html=tests/report.html --self-contained-html
# 报告保存到 tests/report.html，用浏览器打开即可查看

# 生成 JUnit XML（供 CI 系统使用）
pytest tests/ -o junit_family=xunit2 --junitxml=tests/junit.xml
```

### 调试跳过的测试

```bash
# 显示所有跳过的测试及其原因
pytest tests/ -v -r s

# 运行指定测试并显示完整输出
pytest tests/l1/test_m11_bi_api.py::test_bi_scene_detail -v -s

# 查看后端是否实现了对应端点
curl -s http://100.74.141.3:8000/api/bi/scenes/1/detail | head -20
curl -s http://100.74.141.3:8000/api/jupyter/1/url | head -20
```

### 连接超时

确认 Tailscale VPN 已连接，且目标服务器可达：
```bash
ping 100.74.141.3
curl http://100.74.141.3:8000/api/login
```

### Playwright 无法启动

```bash
playwright install chromium
# 或
playwright install --with-deps chromium
```

### 认证失败

检查后端登录接口：
```bash
curl -X POST http://100.74.141.3:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 测试报告

完整测试执行报告请参考 `TEST_REPORT.md`，包含按模块分组的详细结果、跳过原因分析以及后续行动项。

### 生成 HTML 报告

```bash
pip install pytest-html
pytest tests/ --html=tests/report.html --self-contained-html
# 打开 tests/report.html 查看可视化报告
```
