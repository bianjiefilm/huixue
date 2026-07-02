# API路由开发规范

## 生效日期
2024年1月

## 目的
建立清晰的API路由组织规范，防止路由冲突，提高代码可维护性。

## 核心原则

### 1. 单一职责原则
每个资源的所有端点应归属于其专属的路由文件。

**正确示例：**
- `/api/v1/trainings/*` → `trainings.py`
- `/api/v1/courses/*` → `courses.py`
- `/api/v1/users/*` → `users.py`

**错误示例：**
- ❌ 在 `resources.py` 中定义 `/trainings/library`
- ❌ 在多个文件中定义相同资源的端点

### 2. 路由命名规范

#### RESTful 资源路径
```
GET    /api/v1/{resource}          # 列表
POST   /api/v1/{resource}          # 创建
GET    /api/v1/{resource}/{id}     # 详情
PUT    /api/v1/{resource}/{id}     # 更新
DELETE /api/v1/{resource}/{id}     # 删除
```

#### 特殊操作路径
```
POST   /api/v1/{resource}/{id}/{action}     # 资源操作
GET    /api/v1/{resource}/{subcollection}   # 子集合
```

### 3. 文件组织结构
```
app/api/v1/endpoints/
├── trainings.py       # 所有 /trainings/* 端点
├── courses.py         # 所有 /courses/* 端点
├── users.py          # 所有 /users/* 端点
├── auth.py           # 认证相关端点
└── common.py         # 通用工具端点（health, version等）
```

### 4. 禁止事项

#### 4.1 禁止路由重复定义
- 同一路径不能在多个文件中定义
- 使用 `@router.get("/path")` 装饰器时必须确保唯一性

#### 4.2 禁止在通用文件中定义专属路由
- `resources.py` 不应包含具体资源的CRUD操作
- `common.py` 只能包含系统级通用端点

### 5. 路由前缀管理

在 `main.py` 中统一管理路由前缀：
```python
app.include_router(trainings.router, prefix="/api/v1/trainings", tags=["实训管理"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["课程管理"])
```

### 6. 路由冲突检查

#### 开发时检查
1. 新增路由前，全局搜索路径是否已存在
2. 使用命令：`grep -r "@router.get.*library" app/api/`

#### Code Review 要点
- [ ] 路由路径是否唯一
- [ ] 路由是否在正确的文件中
- [ ] 是否遵循RESTful规范
- [ ] 路由前缀是否正确

### 7. 异常处理
所有路由必须正确处理异常：
```python
try:
    # 业务逻辑
    return ApiResponse(code="0000", message="成功")
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"操作失败: {str(e)}")
    raise HTTPException(status_code=500, detail="服务器内部错误")
```

## 执行和监督

### 立即执行
- 本规范自发布之日起立即生效
- 现有代码逐步重构以符合规范

### 监督机制
1. **Code Review**：所有PR必须检查路由规范
2. **自动化检查**：CI中加入路由唯一性检查
3. **定期审计**：每月检查一次路由组织情况

## 版本历史
- v1.0 (2024-01) - 初始版本，解决路由冲突问题