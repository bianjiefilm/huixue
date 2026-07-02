# 慧学高校大数据 FastAPI 项目

基于 Python 3.11、FastAPI 和 PostgreSQL 的后端API服务。

## ✅ 部署状态 - 已成功完成！

- ✅ Python 3.13.2 已安装
- ✅ FastAPI 0.115.12 已安装并运行
- ✅ PostgreSQL 数据库已连接 (localhost:5433/huixue_db)
- ✅ 数据库表已创建 (api_users, api_posts)
- ✅ 所有API端点正常工作
- ✅ 用户CRUD操作测试通过
- ✅ 文章CRUD操作测试通过
- ✅ API文档可访问: http://127.0.0.1:8000/docs

## 🚀 快速开始

### 1. 环境要求
- Python 3.11+
- PostgreSQL 数据库 (Docker 或本地安装)
- pip 包管理器

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 数据库配置

#### 选项A: 使用Docker (推荐)
1. 确保Docker Desktop正在运行
2. 启动PostgreSQL数据库：
```bash
docker-compose up -d
```

#### 选项B: 使用本地PostgreSQL
如果您有本地PostgreSQL安装，请确保：
- 主机: localhost
- 端口: 5433 (或修改config.py中的配置)
- 数据库: huixue_db
- 用户: postgres
- 密码: postgres

### 4. 启动应用
```bash
python run.py
```

或者直接使用 uvicorn：
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## 📋 API 端点

### 基础端点
- `GET /` - 欢迎页面 ✅ (已测试)
- `GET /health` - 健康检查和数据库连接测试 ✅ (已测试)

### 用户管理 ✅ (全部测试通过)
- `POST /users/` - 创建用户
- `GET /users/` - 获取用户列表
- `GET /users/{user_id}` - 获取特定用户
- `DELETE /users/{user_id}` - 删除用户

### 文章管理 ✅ (全部测试通过)
- `POST /posts/` - 创建文章
- `GET /posts/` - 获取文章列表
- `GET /posts/{post_id}` - 获取特定文章
- `DELETE /posts/{post_id}` - 删除文章

## 📖 API 文档
启动应用后，访问以下地址查看自动生成的API文档：
- Swagger UI: http://127.0.0.1:8000/docs ✅ (已验证)
- ReDoc: http://127.0.0.1:8000/redoc

## 🗂️ 项目结构
```
huixue_b/
├── main.py              # FastAPI 主应用
├── config.py            # 配置文件
├── database.py          # 数据库连接
├── models.py            # SQLAlchemy 模型 (api_users, api_posts)
├── schemas.py           # Pydantic 模式
├── crud.py              # 数据库操作
├── run.py               # 启动脚本
├── requirements.txt     # 依赖包
├── docker-compose.yml   # Docker配置
├── test_api.py          # API测试脚本
├── test_user.py         # 用户测试脚本
├── test_new_user.py     # 完整功能测试
├── check_db.py          # 数据库检查脚本
└── README.md            # 项目说明
```

## 🔧 配置说明
数据库连接配置在 `config.py` 文件中，您可以根据需要修改：
- 数据库URL: postgresql://postgres:postgres@localhost:5433/huixue_db
- 主机地址: localhost
- 端口号: 5433
- 数据库名称: huixue_db
- 用户名和密码: postgres/postgres

## 🧪 测试应用

### 1. 测试基本功能
```bash
# 测试根路径
curl http://127.0.0.1:8000/

# 或使用PowerShell
Invoke-WebRequest -Uri http://127.0.0.1:8000/ -UseBasicParsing
```

### 2. 测试数据库连接
```bash
# 测试健康检查
curl http://127.0.0.1:8000/health

# 或使用PowerShell
Invoke-WebRequest -Uri http://127.0.0.1:8000/health -UseBasicParsing
```

### 3. 运行完整测试
```bash
# 运行所有API测试
python test_new_user.py

# 检查数据库状态
python check_db.py
```

## 📝 示例请求

### 创建用户
```bash
curl -X POST "http://127.0.0.1:8000/users/" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "newuser",
       "email": "newuser@example.com",
       "full_name": "新用户"
     }'
```

### 获取用户列表
```bash
curl -X GET "http://127.0.0.1:8000/users/"
```

### 创建文章
```bash
curl -X POST "http://127.0.0.1:8000/posts/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "我的文章",
       "content": "文章内容...",
       "author_id": 1
     }'
```

## 🐳 Docker 命令

### 启动数据库
```bash
docker-compose up -d
```

### 停止数据库
```bash
docker-compose down
```

### 查看日志
```bash
docker-compose logs postgres
```

## 🛠️ 开发说明
- 使用 SQLAlchemy ORM 进行数据库操作
- 使用 Pydantic 进行数据验证
- 支持自动API文档生成
- 包含完整的CRUD操作示例
- 应用已成功启动并在端口8000上运行
- 数据库表使用 `api_users` 和 `api_posts` 避免与现有表冲突

## 🎉 测试结果

### 最新测试结果 (2025-05-23)
```
🚀 开始完整API测试...
==================================================
🧪 测试创建新用户...
✅ 状态码: 200 - 新用户创建成功！

🧪 测试获取用户 ID=2...
✅ 状态码: 200 - 用户详情获取成功！

🧪 测试创建文章...
✅ 状态码: 200 - 文章创建成功！

🧪 测试获取文章列表...
✅ 状态码: 200 - 文章列表获取成功！

==================================================
🎉 完整API测试完成！
```

## 🚨 故障排除

### 如果Docker无法启动
1. 确保Docker Desktop已安装并正在运行
2. 检查Docker服务状态：`docker ps`
3. 如果Docker有问题，可以安装本地PostgreSQL

### 如果端口被占用
修改 `run.py` 或使用不同端口：
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### 如果数据库表冲突
项目已配置使用 `api_users` 和 `api_posts` 表名避免与现有数据库表冲突。

## 📞 联系信息
- 项目地址: 慧学高校大数据平台
- API文档: http://127.0.0.1:8000/docs
- 健康检查: http://127.0.0.1:8000/health 