# 后端服务启动指南

## 方法1：使用 Python 直接启动（推荐）

### 基本启动命令
```bash
# 进入后端目录
cd /Users/jimfu/Desktop/huixue/backend

# 使用 run_server.py 启动（推荐）
python3 run_server.py

# 或者使用 uvicorn 直接启动
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 服务将在以下地址运行
- API服务：http://localhost:8000
- API文档：http://localhost:8000/docs
- ReDoc文档：http://localhost:8000/redoc

## 方法2：使用 UV 包管理器（高性能选项）

UV 是一个用 Rust 编写的极快的 Python 包管理器，比 pip 快 10-100 倍。

### 安装 UV
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv

# 或使用 Homebrew (macOS)
brew install uv
```

### 使用 UV 管理项目

#### 1. 创建虚拟环境
```bash
# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows
```

#### 2. 安装依赖
```bash
# 使用 uv 安装依赖（超快速）
uv pip install -r requirements.txt

# 同步安装（确保环境干净）
uv pip sync requirements.txt
```

#### 3. 启动服务
```bash
# 在 uv 环境中启动
uv run python run_server.py

# 或直接运行
python run_server.py  # 如果已激活虚拟环境
```

## 方法3：使用 Docker（容器化部署）

```bash
# 构建镜像
docker build -t huixue-backend .

# 运行容器
docker run -p 8000:8000 huixue-backend
```

## 常用启动参数说明

### Uvicorn 参数
- `--host`: 绑定的主机地址（0.0.0.0 允许外部访问）
- `--port`: 端口号（默认8000）
- `--reload`: 自动重载（开发模式）
- `--workers`: 工作进程数（生产环境）
- `--log-level`: 日志级别（debug/info/warning/error）

### 示例命令
```bash
# 开发模式（自动重载）
python3 -m uvicorn app.main:app --reload --log-level debug

# 生产模式（多工作进程）
python3 -m uvicorn app.main:app --workers 4 --log-level info

# 自定义端口
python3 -m uvicorn app.main:app --port 8080
```

## 环境变量配置

创建 `.env` 文件设置环境变量：
```bash
# .env
DATABASE_URL=sqlite:///./huixue_local.db
SECRET_KEY=your-secret-key
DEBUG=True
```

## 故障排查

### 1. 端口被占用
```bash
# 查找占用8000端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 2. 模块导入错误
```bash
# 确保在项目根目录运行
cd /Users/jimfu/Desktop/huixue/backend

# 安装缺失的依赖
pip install -r requirements.txt
```

### 3. 数据库连接错误
```bash
# 初始化数据库
python3 init_db.py

# 添加测试数据
python3 add_test_trainings.py
```

## UV 的优势

1. **极速安装**：比 pip 快 10-100 倍
2. **确定性解析**：生成锁文件确保一致性
3. **磁盘空间优化**：全局缓存，避免重复下载
4. **内存效率**：Rust 实现，内存占用低
5. **兼容性好**：完全兼容 pip 和 requirements.txt

## 推荐工作流

### 开发环境
```bash
# 1. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 创建并激活虚拟环境
uv venv && source .venv/bin/activate

# 3. 安装依赖
uv pip sync requirements.txt

# 4. 启动开发服务器
python run_server.py
```

### 生产环境
```bash
# 使用 gunicorn + uvicorn worker
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 快速命令总结

```bash
# 最简单的启动方式
cd /Users/jimfu/Desktop/huixue/backend
python3 run_server.py

# 查看服务状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

## 注意事项

1. 确保 Python 版本 >= 3.9
2. 首次运行需要初始化数据库
3. 开发模式下使用 `--reload` 自动重载
4. 生产环境建议使用 gunicorn + uvicorn
5. 定期更新依赖包以获取安全更新