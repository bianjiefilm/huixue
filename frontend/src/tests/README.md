# 用户认证与角色 Mock API 测试

本测试模块用于验证用户认证相关的Mock API功能，包括登录、获取用户信息和登出。

## 测试内容

测试覆盖以下API端点：

1. **登录接口** - `/api/login`
   - 方法：POST
   - 请求体：`{ username: 'xxx', password: 'xxx' }`
   - 测试用例：成功登录、失败登录（错误凭据）

2. **获取用户信息接口** - `/api/user/info`
   - 方法：GET
   - 需携带Token参数：`?token=xxx`
   - 测试用例：有效Token获取信息、无效Token拒绝访问

3. **登出接口** - `/api/logout`
   - 方法：POST
   - 需携带Token参数：`?token=xxx`
   - 测试用例：成功登出、登出后Token失效

## 预设账号

测试使用以下预设账号：

| 用户名 | 密码 | 角色 |
|-------|------|------|
| admin | admin123 | 管理员 |
| teacher | teacher123 | 教师 |
| student | student123 | 学生 |

## 运行测试

有两种方式运行测试：

### 方式一：通过npm脚本

```bash
npm run test:auth
```

这将启动一个Vite开发服务器并打开测试页面。

### 方式二：手动打开HTML文件

直接在浏览器中打开 `src/tests/auth-test.html` 文件。

## 测试实现说明

1. 测试使用纯浏览器环境，不依赖Node.js进行运行
2. Mock.js用于拦截Ajax请求并模拟服务器响应
3. 使用内存中的tokenStore来模拟服务器session存储
4. 测试结果会在页面上实时显示

## 集成到应用

如需将此认证Mock集成到应用中：

1. 确保`src/mock/auth.ts`已被导入到main.ts中
2. 确保请求拦截器中设置了Token（如有需要）
3. 使用Pinia状态管理(stores/user.ts)保存登录状态和用户信息 

# 试卷库与试题库 Mock API 测试

本测试模块验证了试卷库和试题库相关的Mock API功能，用于支持系统的在线考试功能。

## 测试内容

测试覆盖以下API端点：

### 试卷库
1. **获取试卷列表** - `GET /api/exam/papers`
   - 查询参数：关键词、分类、难度、来源、分页信息等
   - 测试用例：各种过滤条件组合下的试卷列表获取

2. **创建试卷** - `POST /api/exam/papers`
   - 请求体：包含试卷基本信息
   - 测试用例：创建手动试卷、根据模板创建

3. **获取试卷详情** - `GET /api/exam/papers/{id}`
   - 测试用例：获取存在的试卷、获取不存在的试卷

4. **更新试卷** - `PUT /api/exam/papers/{id}`
   - 请求体：包含需要更新的字段
   - 测试用例：更新基本信息、更新题目列表

5. **复制试卷** - `POST /api/exam/papers/{id}/copy`
   - 测试用例：复制系统试卷、复制个人试卷

6. **删除试卷** - `DELETE /api/exam/papers/{id}`
   - 测试用例：删除个人试卷、尝试删除系统试卷（应失败）

7. **创建考试** - `POST /api/exam/papers/create-exam`
   - 请求体：包含考试设置信息
   - 测试用例：使用有效的参数创建考试

### 试题库
1. **获取试题列表** - `GET /api/exam/questions`
   - 查询参数：关键词、类型、分类、难度、来源、分页信息等
   - 测试用例：各种过滤条件组合下的试题列表获取

2. **创建试题** - `POST /api/exam/questions`
   - 请求体：包含试题信息
   - 测试用例：创建各种类型的试题（单选、多选、判断、简答）

3. **获取试题详情** - `GET /api/exam/questions/{id}`
   - 测试用例：获取存在的试题、获取不存在的试题

4. **编辑试题** - `PUT /api/exam/questions/{id}`
   - 请求体：包含需要更新的字段
   - 测试用例：编辑个人试题、尝试编辑系统试题（应失败）

5. **复制试题** - `POST /api/exam/questions/{id}/copy`
   - 测试用例：复制系统试题、复制个人试题

6. **删除试题** - `DELETE /api/exam/questions/{id}`
   - 测试用例：删除个人试题、尝试删除系统试题（应失败）

7. **批量删除试题** - `POST /api/exam/questions/batch-delete`
   - 请求体：包含试题ID列表
   - 测试用例：批量删除个人试题

### 试卷模板
1. **获取模板列表** - `GET /api/exam/paper-templates`
   - 测试用例：获取所有模板

2. **使用模板生成试卷** - `POST /api/exam/papers/generate-from-template`
   - 请求体：包含模板规则和过滤条件
   - 测试用例：使用有效规则生成试卷

## 运行测试

有两种方式运行测试：

### 方式一：通过npm脚本

```bash
npm run test:exam-bank
```

这将启动一个Vite开发服务器并打开测试页面。

### 方式二：手动打开HTML文件

直接在浏览器中打开 `src/tests/exam-bank-test.html` 文件。

## 测试实现说明

1. 测试使用纯浏览器环境，不依赖Node.js进行运行
2. Mock.js用于拦截Ajax请求并模拟服务器响应
3. 数据模型包括试卷(PaperDetail/PaperSummary)和试题(QuestionDetail/QuestionInput)
4. 支持各种过滤条件和分页查询

## 集成到应用

如需将此Mock集成到应用中：

1. 确保`src/mock/exam-bank.ts`和`src/mock/question-bank.ts`已被导入到main.ts中
2. 接口参数严格遵循API合约`src/api/system_management_api.json`中的定义
3. 可以配合Pinia状态管理来实现前端的试卷库和试题库功能 

# 课程和挑战模块 Mock API 测试

本测试模块验证了课程资源、微型实验课程和编码挑战相关的Mock API功能，测试各个模块的数据获取、筛选和操作能力。

## 测试内容

测试覆盖以下API端点：

### 课程资源
1. **获取课程资源列表** - `GET /api/courses/resources`
   - 查询参数：关键词、标签
   - 测试用例：根据关键词和标签筛选资源列表

2. **获取课程资源详情** - `GET /api/courses/resources/{id}`
   - 测试用例：获取包含章节、实践等完整信息的课程详情

3. **获取课程标签** - `GET /api/courses/tags`
   - 测试用例：获取所有课程标签，用于筛选

### 微型实验课程
1. **获取微型实验列表** - `GET /api/courses/micro`
   - 查询参数：关键词、方向、分类、难度级别
   - 测试用例：根据不同条件组合筛选课程列表

2. **获取微型实验详情** - `GET /api/courses/micro/{id}`
   - 测试用例：获取包含任务列表和技能标签的课程详情

3. **获取推荐课程** - `GET /api/courses/micro/{id}/recommended`
   - 测试用例：基于当前课程获取相关推荐课程

4. **获取方向和分类** - `GET /api/courses/micro/directions` 和 `GET /api/courses/micro/categories`
   - 测试用例：获取所有方向和分类，用于筛选

### 编码挑战
1. **获取挑战详情** - `GET /api/challenges/{id}`
   - 测试用例：获取不同环境类型（code、html、command、desktop）的挑战详情

2. **评测代码** - `POST /api/challenges/evaluate`
   - 请求体：包含代码和测试用例
   - 测试用例：测试代码对单个测试用例的评测结果

## 运行测试

有两种方式运行测试：

### 方式一：通过npm脚本

```bash
npm run test:course
```

这将启动一个Vite开发服务器并打开测试页面。

### 方式二：手动打开HTML文件

直接在浏览器中打开 `src/tests/course-test.html` 文件。

## 测试实现说明

1. 测试使用纯浏览器环境，不依赖Node.js进行运行
2. Mock.js用于拦截Ajax请求并模拟服务器响应
3. 数据模型包括课程资源(CourseResource/CourseDetail)、微型实验(MicroCourse)和编码挑战(CodingChallenge)
4. 支持基于关键词、标签、方向、分类和难度级别的多维度筛选
5. 支持暗色/亮色主题切换，展示系统主题功能

## 集成到应用

如需将此Mock集成到应用中：

1. 确保`src/mock/course.ts`和`src/mock/challenge.ts`已被导入到main.ts中
2. 接口参数严格遵循API合约`src/api/course_api.json`中的定义
3. 数据模型遵循`src/api/schema.json`中的规范
4. 可以配合Pinia状态管理来实现前端的课程浏览和学习功能

每种环境类型都有相应的测试用例和评测方法，支持更丰富的学习场景。 

# 机器学习画布 Mock API 测试

本测试模块验证了机器学习画布相关的Mock API功能，测试节点类型、工作流模板、工作流管理和执行等功能。

## 测试内容

测试覆盖以下API端点：

### 节点类型API
1. **获取节点类型** - `GET /api/ml/node-types`
   - 测试用例：获取所有可用的节点类型和类别

### 工作流模板API
1. **获取工作流模板** - `GET /api/ml/workflow-templates`
   - 测试用例：获取预定义的工作流模板列表

### 用户工作流API
1. **获取用户工作流列表** - `GET /api/ml/workflows`
   - 查询参数：用户ID、项目ID
   - 测试用例：获取指定用户的工作流列表

2. **获取工作流详情** - `GET /api/ml/workflows/{id}`
   - 测试用例：获取包含节点和连接边的完整工作流信息

3. **保存工作流** - `POST /api/ml/workflows`
   - 请求体：包含工作流定义（节点和边）
   - 测试用例：创建新工作流

4. **执行工作流** - `POST /api/ml/workflows/execute`
   - 请求体：包含工作流ID
   - 测试用例：运行工作流并获取执行结果

5. **删除工作流** - `DELETE /api/ml/workflows/{id}`
   - 测试用例：删除现有工作流

## 运行测试

有两种方式运行测试：

### 方式一：通过npm脚本

```bash
npm run test:ml-canvas
```

这将启动一个Vite开发服务器并打开测试页面。

### 方式二：手动打开HTML文件

直接在浏览器中打开 `src/tests/ml-canvas-test.html` 文件。

## 测试实现说明

1. 测试使用纯浏览器环境，不依赖Node.js进行运行
2. Mock.js用于拦截Ajax请求并模拟服务器响应
3. 数据模型包括节点类型、工作流模板和用户工作流
4. 支持可视化工作流的操作，包括创建、保存、执行和删除
5. 支持暗色/亮色主题切换，与系统整体主题保持一致

## 集成到应用

如需将此Mock集成到应用中：

1. 确保`src/mock/ml.ts`已被导入到main.ts中
2. 使用MLCanvas组件需要以下相关组件：
   - MLCanvas: 主要画布组件
   - MLNodePalette: 节点库组件
   - MLNodeDetail: 节点详情配置组件
   - MLManualDrawer: 机器学习操作手册组件
3. 可以配合Pinia状态管理来实现前端的机器学习工作流设计和执行功能

机器学习画布组件支持多种节点类型：数据处理节点、预处理节点、特征工程节点、机器学习模型节点、深度学习节点和评估节点。用户可以通过拖拽节点并连接它们来创建完整的机器学习工作流。

## 最近修复记录

1. **2023-10-20**：修复了以下测试页面错误：
   - 修复 antd 未定义的问题，使用 Ant 作为全局引用
   - 添加 dayjs 依赖以解决日期格式化问题
   - 使用 Vue 的生产版本 (vue.global.prod.js) 提高性能
   - 创建了统一的 mock 模块导入机制 (src/mock/index.ts)，简化测试文件的导入

2. **2023-10-21**：解决了测试页面加载顺序相关问题：
   - 重新调整了脚本加载顺序，确保 Vue 先加载
   - 正确初始化 dayjs，通过 `window.dayjs = dayjs` 使其全局可用
   - 正确引用 antd，通过 `const antd = window.antd` 获取全局引用
   - 修复了所有与组件库相关的引用，确保使用统一的 `antd` 对象名 

3. **2023-10-25**：修复了机器学习画布测试页面的运行时错误：
   - 调整了脚本加载顺序，先加载 Vue，然后是 axios 和 mockjs，再加载 Ant Design，最后加载 dayjs
   - 移除了使用 ConfigProvider 的主题配置，改为使用简化的 CSS 类切换方式实现主题切换
   - 直接使用 window.antd 引用，而不是尝试重新分配变量
   - 将 Vue 组件设计模式从选项式 API 更改为使用对象模板和 setup 方法的组合式 API
   - 修复了消息提示调用，确保使用 window.antd.message 调用 

4. **2023-10-26**：解决了dayjs和Ant Design主题相关问题：
   - 修改了脚本加载顺序，确保先加载dayjs，再加载其他依赖
   - 添加了window.dayjs = dayjs初始化代码以确保dayjs全局可用
   - 移除了themeConfig配置和a-config-provider包装器
   - 简化了主题切换逻辑，直接使用CSS类来实现暗黑/亮色主题
   - 修复了a-switch组件的属性，移除了不必要的checkedValue和unCheckedValue属性 

5. **2023-10-27**：彻底修复消息通知和加载问题：
   - 为解决`Cannot read properties of undefined (reading 'message')`错误，实现了自定义消息通知组件
   - 添加了完整的消息样式，支持成功、错误和信息三种类型的通知
   - 修复了dayjs路径，使用完整路径`dist/dayjs.min.js`确保正确加载
   - 优化了Ant Design Vue的检测方式，使用`typeof antd === 'undefined'`代替window对象引用
   - 为暗黑主题下的消息通知添加了专门的样式，提高用户体验
   - 增强了错误处理，确保即使Ant Design Vue加载失败，测试页面仍能正常运行 

# 学生管理模块 Mock API 测试

本测试模块验证了学生管理相关的Mock API功能，用于支持系统的学生信息管理和组织架构管理。

## 测试内容

测试覆盖以下API端点：

### 学生管理
1. **获取学生列表** - `GET /api/students`
   - 查询参数：组织ID、关键词、分页信息等
   - 测试用例：按组织架构层级(学校、学院、专业、年级、班级)获取学生列表

2. **获取学生详情** - `GET /api/students/{id}`
   - 测试用例：获取学生的详细信息

3. **创建学生** - `POST /api/students`
   - 请求体：包含学生基本信息
   - 测试用例：创建新学生账号

4. **更新学生** - `PUT /api/students/{id}`
   - 请求体：包含需要更新的字段
   - 测试用例：更新学生基本信息

5. **删除学生** - `DELETE /api/students/{id}`
   - 测试用例：删除学生账号

6. **批量操作** - `/api/students/batch-*`
   - 批量删除: `POST /api/students/batch-delete`
   - 批量更新状态: `POST /api/students/batch-update-status`
   - 学生调动: `POST /api/students/transfer`
   - 测试用例：对多个学生执行批量操作

### 组织架构
1. **获取组织架构树** - `GET /api/organization/tree`
   - 测试用例：获取完整的组织架构树（学校→学院→专业→年级→班级）

## 运行测试

有两种方式运行测试：

### 方式一：通过npm脚本

```bash
npm run test:student
```

这将启动一个Vite开发服务器并打开测试页面。

### 方式二：手动打开HTML文件

直接在浏览器中打开 `src/tests/student-test.html` 文件。

## 测试实现说明

1. 测试使用纯浏览器环境，不依赖Node.js进行运行
2. Mock.js用于拦截Ajax请求并模拟服务器响应
3. 数据模型包括学生(Student)和组织架构(OrganizationNode)
4. 基于组织架构实现了层级化的学生管理，支持按组织筛选学生
5. 支持暗色/亮色主题切换，与系统整体主题保持一致

## 集成到应用

如需将此Mock集成到应用中：

1. 确保`src/mock/student.ts`和`src/mock/department.ts`已被导入到main.ts中
2. 使用Pinia状态管理(stores/student.ts和stores/department.ts)保存相关数据
3. 组件中使用stores中提供的方法进行学生信息管理和组织架构管理

## 最近修复记录

1. **2023-11-10**：创建学生管理模块测试页面q
   - 实现了完整的学生管理API模拟，包括CRUD操作和批量操作
   - 添加了组织架构树API模拟，支持层级化的数据管理
   - 使用与其他测试页面一致的样式和主题切换功能
   - 优化了错误处理和消息提示，提高用户体验 