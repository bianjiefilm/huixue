# 资源同步服务 V2.0 - 测试套件

这是一个完整的测试套件，用于验证资源同步服务V2.0的功能、性能和稳定性。

## 📁 测试结构

```
tests/
├── __init__.py                      # 测试包初始化
├── conftest.py                      # 测试配置和fixtures
├── test_resource_sync_service.py    # 核心服务单元测试
├── test_sync_task_manager.py        # 任务管理器单元测试
├── test_sync_crud.py                # CRUD操作单元测试
├── test_data_consistency_manager.py # 一致性管理器单元测试
├── test_api_endpoints.py            # API端点集成测试
├── test_integration_e2e.py          # 端到端集成测试
├── test_performance_load.py         # 性能和负载测试
└── README.md                        # 测试说明文档
```

## 🚀 快速开始

### 运行所有测试
```bash
# 运行完整测试套件（跳过慢测试）
python run_tests.py all

# 运行所有测试包括慢测试
python run_tests.py all --include-slow

# 生成覆盖率报告
python run_tests.py all --coverage --report
```

### 运行特定类型的测试
```bash
# 单元测试
python run_tests.py unit

# API集成测试
python run_tests.py api

# 端到端集成测试
python run_tests.py integration

# 性能测试
python run_tests.py performance --include-slow
```

### 并行运行测试
```bash
# 并行运行所有测试
python run_tests.py all --parallel
```

## 🧪 测试类型说明

### 1. 单元测试 (Unit Tests)
- **文件**: `test_resource_sync_service.py`, `test_sync_task_manager.py`, etc.
- **目的**: 测试单个组件的功能
- **范围**: 类方法、函数逻辑、数据验证
- **运行**: `python run_tests.py unit`

### 2. 集成测试 (Integration Tests)
- **文件**: `test_api_endpoints.py`
- **目的**: 测试组件间的交互
- **范围**: API端点、数据库操作、外部服务集成
- **运行**: `python run_tests.py api`

### 3. 端到端测试 (E2E Tests)
- **文件**: `test_integration_e2e.py`
- **目的**: 测试完整的工作流程
- **范围**: 上传→处理→导入→审计的完整流程
- **运行**: `python run_tests.py integration`

### 4. 性能测试 (Performance Tests)
- **文件**: `test_performance_load.py`
- **目的**: 测试系统在负载下的表现
- **范围**: 响应时间、并发处理、资源使用
- **运行**: `python run_tests.py performance --include-slow`

## 📊 测试覆盖范围

### 核心组件覆盖
- ✅ 资源同步服务 (ResourceSyncService)
- ✅ 清单验证器 (ManifestValidator)
- ✅ 任务管理器 (SyncTaskManager)
- ✅ CRUD操作 (SyncTaskCRUD, AuditReportCRUD, etc.)
- ✅ 数据一致性管理器 (DataConsistencyManager)

### API端点覆盖
- ✅ 任务管理 API (`/v2/tasks/*`)
- ✅ 审计 API (`/v2/audit/*`)
- ✅ 清单管理 API (`/v2/manifests/*`)
- ✅ 文件上传 API (`/v2/upload`)
- ✅ 统计 API (`/v2/stats`)
- ✅ 健康检查 API (`/v2/health`)

### 数据库操作覆盖
- ✅ 同步任务表操作
- ✅ 审计报告表操作
- ✅ 资源清单表操作
- ✅ 待处理文件表操作

### 业务逻辑覆盖
- ✅ 课程包验证和解析
- ✅ 资源文件上传和管理
- ✅ 任务状态跟踪和并发控制
- ✅ 数据一致性审计和修复
- ✅ 错误处理和回滚机制

## 🔧 测试工具和依赖

### 必需依赖
```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-html>=3.1.0
pytest-xdist>=3.0.0
psutil>=5.9.0
```

### 安装测试依赖
```bash
pip install -r requirements-dev.txt
```

## 🎯 测试数据和Mock

### 测试Fixtures
- `sample_manifest`: 示例manifest数据
- `valid_course_manifest`: 有效的课程清单对象
- `sample_course_package`: 示例课程包目录
- `mock_storage_manager`: 模拟存储管理器
- `mock_task_manager`: 模拟任务管理器
- `db_session`: 数据库会话
- `temp_dir`: 临时目录

### Mock策略
- **外部服务**: 存储服务、文件系统操作
- **数据库**: 复杂查询和外部依赖
- **时间**: 定时任务和超时逻辑
- **网络**: API调用和外部请求

## 📈 性能基准

### API响应时间
- **平均响应时间**: < 500ms
- **95%响应时间**: < 1秒
- **成功率**: > 95%

### 并发性能
- **并发用户**: 20用户
- **QPS**: > 50请求/秒
- **成功率**: > 90%

### 数据库性能
- **查询响应时间**: < 100ms
- **批量操作**: < 5秒 (1000条记录)

### 资源使用
- **内存增长**: < 50MB (1000操作后)
- **文件描述符**: < 10个泄漏

## 🚨 测试标记

### 跳过标记
```python
@pytest.mark.slow  # 慢测试（性能、压力测试）
@pytest.mark.skipif  # 条件跳过
@pytest.mark.parametrize  # 参数化测试
```

### 运行特定标记的测试
```bash
# 只运行慢测试
pytest -m slow

# 跳过慢测试
pytest -m "not slow"

# 运行特定标记
pytest -m "performance and load"
```

## 📋 测试报告

### HTML报告
```bash
python run_tests.py all --report
# 生成: reports/test_report.html
```

### 覆盖率报告
```bash
python run_tests.py all --coverage
# 生成: htmlcov/index.html
```

### JUnit XML报告
```bash
pytest --junitxml=reports/junit.xml
```

## 🔍 调试测试

### 详细输出
```bash
# 详细测试输出
pytest -v -s

# 显示打印输出
pytest -s --capture=no
```

### 调试失败测试
```bash
# 只运行失败的测试
pytest --lf

# 只运行上次失败后通过的测试
pytest --ff
```

### 特定测试调试
```bash
# 运行特定测试类
pytest tests/test_resource_sync_service.py::TestManifestValidator

# 运行特定测试方法
pytest tests/test_resource_sync_service.py::TestManifestValidator::test_validate_manifest_valid
```

## 🐛 常见问题

### 数据库连接问题
```bash
# 设置测试数据库
python run_tests.py all --setup-db
```

### 内存不足
```bash
# 减少并发数
pytest -n 2

# 跳过内存密集测试
pytest -m "not performance"
```

### 超时问题
```bash
# 增加超时时间
pytest --timeout=600

# 或者在pytest.ini中设置
timeout = 600
```

### Mock问题
```bash
# 检查mock是否正确设置
pytest -v --tb=long
```

## 📝 编写新测试

### 单元测试模板
```python
import pytest
from app.services.your_service import YourService

class TestYourService:
    """测试YourService"""

    def test_your_method(self, db_session):
        """测试your_method方法"""
        service = YourService()

        # 执行测试
        result = service.your_method("test_input")

        # 断言
        assert result == "expected_output"
```

### API测试模板
```python
def test_your_api(self, client, auth_headers):
    """测试your_api端点"""
    response = client.post(
        "/api/v1/your/endpoint",
        json={"key": "value"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == "0000"
```

### 性能测试模板
```python
@pytest.mark.slow
def test_performance_under_load(self, client, auth_headers, performance_metrics):
    """测试负载下性能"""
    # 执行操作并测量性能
    # performance_metrics 会自动收集指标
    pass
```

## 🎯 测试最佳实践

1. **测试命名**: `test_描述_预期行为`
2. **测试隔离**: 每个测试独立运行
3. **Mock外部依赖**: 不要依赖外部服务
4. **清理资源**: 测试后清理创建的资源
5. **断言明确**: 清楚说明期望行为
6. **覆盖边界情况**: 包括错误情况和边界值
7. **性能基准**: 为性能测试设置合理的阈值

## 📞 支持

如果遇到测试问题，请：

1. 检查测试输出和错误信息
2. 查看相关日志文件
3. 确认测试环境配置正确
4. 查看测试文档和示例

测试套件会随着代码的发展持续更新，确保系统的质量和稳定性！

