# 资源批量导入操作手册

## 目录
1. [系统概述](#系统概述)
2. [资源目录结构](#资源目录结构)
3. [五阶段导入流程](#五阶段导入流程)
4. [前端操作指南](#前端操作指南)
5. [后端脚本使用](#后端脚本使用)
6. [API接口清单](#api接口清单)
7. [常见问题](#常见问题)

## 系统概述

本系统提供了完整的教学资源批量导入解决方案，支持：
- 🎯 实训资源批量导入
- 📚 实践课程和关卡创建
- ❓ 题库批量导入
- 🗂️ 课程资源映射管理
- ✅ 端到端验证

## 资源目录结构

```
backend/ziyuan/
├── 实训资源/          # 独立实训项目
│   ├── 项目1/
│   │   ├── course_data.json    # 必需：课程配置
│   │   ├── datasets/           # 数据集文件
│   │   └── README.md
│   └── 项目2/
│       └── ...
│
└── 课程资源/          # 复合型课程包
    ├── Python程序设计/
    │   ├── 01-课程文档/        # 理论文档
    │   ├── 02-理论课件/        # PPT等
    │   ├── 03-微型实验/        # 实践关卡
    │   │   ├── 实践1/
    │   │   │   ├── 关卡1/
    │   │   │   │   ├── README.md
    │   │   │   │   ├── student.py
    │   │   │   │   └── test_evaluator.py
    │   │   │   └── 关卡2/
    │   │   └── 实践2/
    │   ├── 04-考试评测/        # 题库文件
    │   │   └── questions.json
    │   └── 05-相关实训/        # 内嵌实训
    └── Spark编程基础/
        └── ...
```

## 五阶段导入流程

### 第一阶段：资源盘点
扫描并验证所有资源文件的完整性。

### 第二阶段：数据处理与录入
将资源数据导入到系统数据库。

### 第三阶段：系统配置与关联
创建课堂结构，组织课程和章节。

### 第四阶段：端到端测试
验证导入的资源可以正常使用。

### 第五阶段：优化与文档
生成导入报告，记录问题和优化建议。

## 前端操作指南

### 1. 访问资源导入界面

管理员登录后，访问：
```
/admin/resource-import
```

### 2. 实训资源导入

#### 步骤1：扫描资源
- 点击"实训资源导入"标签
- 点击"开始扫描"按钮
- 系统将自动扫描 `backend/ziyuan/实训资源/` 目录

#### 步骤2：验证数据
- 选择要导入的实训项目
- 点击"验证数据"

#### 步骤3：批量导入
- 设置导入模式（跳过/更新/替换）
- 输入创建者ID
- 点击"开始导入"

#### 步骤4：发布配置
- 导入完成后可直接发布到课堂

### 3. 实践课程导入

#### 步骤1：选择课程
- 点击"实践课程导入"标签
- 选择要扫描的课程（如Python程序设计）

#### 步骤2：扫描实践
- 点击"扫描微型实验"
- 系统将列出所有实践和关卡

#### 步骤3：创建实践
- 选择要导入的实践
- 设置实践类型和难度
- 点击"开始创建"

#### 步骤4：创建关卡
- 为每个实践创建对应的关卡
- 可以批量创建或逐个创建

### 4. 题库批量导入

#### 步骤1：下载模板
- 点击"题库批量导入"标签
- 点击"下载题库模板"

#### 步骤2：准备数据
按模板格式准备题库数据（支持JSON和Excel）

#### 步骤3：上传导入
- 点击"上传题库文件"
- 选择准备好的文件
- 系统将自动导入并显示结果

### 5. 资源映射管理

配置课程资源目录到系统模块的映射关系：

- 选择资源目录
- 设置目标模块（实践/实训/题库/教材）
- 配置映射规则
- 支持批量映射

## 后端脚本使用

### 1. 完整导入脚本

```bash
# 进入后端目录
cd backend

# 执行完整导入
python import_all_resources.py

# 仅扫描不导入
python import_all_resources.py --scan-only

# 指定导入类型
python import_all_resources.py --type training
python import_all_resources.py --type practice
python import_all_resources.py --type question

# 指定用户ID
python import_all_resources.py --teacher-id 1 --creator-id 1
```

### 2. 端到端测试

```bash
# 运行端到端测试
python test_e2e_import.py
```

测试将自动：
- 扫描资源
- 导入数据
- 创建课堂
- 验证学生访问
- 生成测试报告

## API接口清单

### 实训相关

```http
# 扫描测试
POST /api/v1/trainings/seed/test

# 批量导入
POST /api/v1/trainings/seed?creator_id={id}

# 创建自定义实训
POST /api/v1/custom-trainings?creator_id={id}

# 发布实训
POST /api/v1/custom-trainings/{training_id}/publish
```

### 实践相关

```http
# 创建自定义实践
POST /api/v1/custom-practices?creator_id={id}

# 创建关卡（三步法）
POST /api/v1/practices/{practice_id}/stages/step1?creator_id={id}
PUT /api/v1/stages/{stage_id}/step2?creator_id={id}
PUT /api/v1/stages/{stage_id}/step3?creator_id={id}

# 创建关卡（一步法）
POST /api/v1/practices/{practice_id}/stages/complete?creator_id={id}
```

### 题库相关

```http
# 下载模板
GET /api/v1/question-library/questions/template

# 批量导入
POST /api/v1/question-library/questions/import?teacher_id={id}
```

### 课堂管理

```http
# 创建课堂
POST /api/v1/classrooms?teacher_id={id}

# 添加课程
POST /api/v1/classrooms/{classroom_id}/courses/add-practice?teacher_id={id}
POST /api/v1/classrooms/{classroom_id}/courses/add-training?teacher_id={id}

# 发布课程
POST /api/v1/classrooms/{classroom_id}/courses/publish-all?teacher_id={id}
```

## 常见问题

### Q1: 实训资源导入失败
**原因**：course_data.json 格式错误或缺少必要字段
**解决**：检查JSON格式，确保包含title、description等必要字段

### Q2: 实践关卡创建失败
**原因**：缺少测试文件或格式不正确
**解决**：确保每个关卡目录包含：
- README.md（任务说明）
- student.py（学生代码模板）
- test_evaluator.py（测试代码）

### Q3: 题库导入部分失败
**原因**：题目格式不符合要求
**解决**：
- 使用模板文件准备数据
- 检查题目类型是否正确
- 确保答案格式匹配题型

### Q4: 课程无法发布
**原因**：课程未完成配置或缺少必要信息
**解决**：
- 确保课程已添加到课堂
- 检查是否设置了章节
- 验证课程内容完整性

### Q5: 学生无法访问课程
**原因**：课程未发布或权限问题
**解决**：
- 确认课程已发布
- 检查学生是否已加入课堂
- 验证课堂是否激活

## 数据标准

### 难度等级映射
- `beginner` / `easy` → 初级
- `intermediate` / `medium` → 中级
- `advanced` / `hard` → 高级

### 实训类型映射
- `jupyter` → `CODING`
- `bi` / `ai` → `DRAG_DROP`

### 实践类型
- `code` → `coding`（编程类）
- `desktop` → `desktop`（桌面类）

### 题目类型
- `single_choice` - 单选题
- `multiple_choice` - 多选题
- `true_false` - 判断题
- `fill_blank` - 填空题
- `short_answer` - 简答题
- `coding` - 编程题

## 最佳实践

1. **分批导入**：大量资源建议分批导入，避免超时
2. **预先验证**：使用扫描功能预先验证资源完整性
3. **备份数据**：导入前备份数据库
4. **测试环境**：先在测试环境验证导入流程
5. **监控日志**：导入过程中关注日志输出
6. **保存报告**：每次导入后保存报告以备查询

## 支持与反馈

如遇到问题，请：
1. 查看导入日志：`import_resources_*.log`
2. 查看测试报告：`e2e_test_report_*.json`
3. 联系技术支持并提供错误信息

---

*文档版本：1.0.0*
*更新日期：2024-01-20*