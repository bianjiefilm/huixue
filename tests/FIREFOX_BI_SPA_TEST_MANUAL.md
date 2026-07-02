# Firefox BI 实训工作台 SPA 切换测试手册

## 测试环境
- **浏览器**: Firefox（最新版，推荐 >= 120）
- **URL**: http://100.74.141.3
- **账号**: student1 / student123
- **课堂**: 100（A股上市公司销售额分析实验班）
- **测试机器**: 校内机器（能访问 100.74.141.3 的任意终端，推荐程龙的开发机）

## 前置条件
1. Firefox 已安装且更新到最新版本
2. 能访问 http://100.74.141.3
3. 用 student1 账号登录，确保 classroom 100 中有实训 11（A股）、17（客户流失）、24（分布式光伏）

## 测试用例

### Case 1: SPA 内连续切换（核心用例）

**步骤：**
1. 用 student1 登录 → 进入课堂 100
2. 点击"开启实训"进入 **workspace A**（A股上市公司销售额分析，ct_id=11）
3. 等待 Graphic Walker 画布完全加载（能看到字段列表）
4. **不刷新页面**，点击浏览器左上角的"返回"按钮或页面内的面包屑，返回实训列表
5. 点击 **workspace B**（客户流失模型预测，ct_id=17）
6. 等待完全加载后，记录：标题是否为"客户流失模型预测"、数据集名称是否为 B 对应的数据集
7. 返回列表，点击 **workspace C**（分布式光伏出力预测，ct_id=24）
8. 等待完全加载，记录同上

**断言（每个切换后检查）：**
- [ ] 页面标题已更新为当前实训名称（不是上一个的）
- [ ] 数据集名称/数量对应当前实训（可以用"数一数字段列表有几项"粗略验证）
- [ ] Graphic Walker 画布能正常显示（不是白屏或报错）
- [ ] 无弹出 error 弹窗
- [ ] Console（F12 → Console）无红色 ERROR 级别的 Vue 报错

**截图要求：** 每个 workspace 加载稳定后截一张，3 张截图附在测试报告里。

---

### Case 2: 快速连续切换（race condition 压测）

**步骤：**
1. 进入 workspace A（ct_id=11）
2. 快速返回列表（<500ms 内）→ 点击 B（<500ms）→ 返回（<500ms）→ 点击 A（<500ms）→ 返回（<500ms）→ 点击 C（ct_id=24）
3. 最终停在 workspace C，记录最终状态

**断言：**
- [ ] 最终页面显示的是 workspace C（分布式光伏），不是 A 或 B
- [ ] 数据对应对应 C 的数据集
- [ ] 无 Console ERROR

**截图：** 最终状态截图 1 张。

---

### Case 3: 同一 workspace 重复点击

**步骤：**
1. 进入 workspace A（ct_id=11）
2. 返回列表
3. 再次点击 workspace A
4. 等待加载

**断言：**
- [ ] 能正常加载 A（不是白屏）
- [ ] 无 Console ERROR
- [ ] 数据正确

**截图：** 第二次加载后截图 1 张。

---

## 额外关注点（Firefox 特有）

以下为 iframe postMessage 兼容性重点检查，Chrome 上通过不代表 Firefox 没问题：

- [ ] Graphic Walker 画布在拖拽字段后能正确渲染图表（不报 `postMessage: permission denied` 或跨域错误）
- [ ] 图表切换（柱状图/折线图/散点图等）正常响应
- [ ] 画布自适应浏览器窗口大小（resize 不断裂）

## 测试结果模板

```
测试人：
测试日期：
Firefox 版本：
测试机器 IP：

| Case | 结果 | 截图文件 | 备注 |
|------|------|----------|------|
| Case 1: A→B→C | PASS/FAIL | case1.png | |
| Case 2: 快切 | PASS/FAIL | case2.png | |
| Case 3: 重复点击 | PASS/FAIL | case3.png | |

Firefox 特有检查:
| 检查项 | 结果 | 备注 |
|--------|------|------|
| iframe postMessage | PASS/FAIL | |
| 图表拖拽渲染 | PASS/FAIL | |
| resize 自适应 | PASS/FAIL | |

Console 错误日志（如果有）:
[粘贴 Console 中的红色 ERROR 行]

备注:
```

## 注意事项

- 不要用 Ctrl+R 或 F5 刷新页面测试 watch——那走的是 onMounted 冷加载路径
- 必须通过 UI 点击（返回按钮、面包屑、列表点击）来触发 SPA 路由切换
- 如果遇到网络超时导致某次加载慢，不要人为干预重试，记录"超时，等待手动重试该步骤"即可
