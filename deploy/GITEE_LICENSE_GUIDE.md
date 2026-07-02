# Gitee 授权配置指南

## 仓库信息
- **仓库地址**: https://gitee.com/noderead/huixuejson
- **状态**: 私有仓库

## 第一步：创建 Gitee Token

1. 访问: https://gitee.com/profile/personal_access_tokens
2. 点击「生成新令牌」
3. 令牌描述: `tempo-license`
4. 权限: 勾选 `repo`（仓库操作）
5. 点击「提交」并保存 Token

## 第二步：运行配置脚本

```bash
cd deploy/scripts

# 生成机器码并创建授权
python setup_gitee_license.py --token 你的Token --expire 2026-12-31

# 示例
python setup_gitee_license.py --token abc123xyz --expire 2026-12-31
```

## 第三步：配置服务器环境变量

在 **三台服务器** 上执行：

```bash
# 编辑环境变量文件
nano ~/.bashrc

# 添加以下内容（替换为实际值）
export LICENSE_URL="https://gitee.com/noderead/huixuejson/raw/main/license.json"
export LICENSE_TOKEN="你的GiteeToken"

# 使生效
source ~/.bashrc
```

或在 `docker-stack.yml` 中配置：
```yaml
environment:
  - LICENSE_URL=https://gitee.com/noderead/huixuejson/raw/main/license.json
  - LICENSE_TOKEN=你的GiteeToken
```

## 管理命令

```bash
# 查看机器码（用于多服务器授权）
python setup_gitee_license.py --token 你的Token --machine

# 检查授权状态
python setup_gitee_license.py --token 你的Token --check

# 停用服务（授权失效）
python setup_gitee_license.py --token 你的Token --disable

# 启用服务（授权恢复）
python setup_gitee_license.py --token 你的Token --enable
```

## license.json 文件格式

```json
{
  "enabled": true,
  "machine_code": "服务器的机器码",
  "expire_date": "2026-12-31",
  "message": "授权正常"
}
```

## 控制服务

| 操作 | 说明 |
|------|------|
| 停用服务 | 设置 `"enabled": false` |
| 启用服务 | 设置 `"enabled": true` |
| 设置过期 | 修改 `"expire_date"` |

## 故障排除

### 授权检查失败
- 检查 `LICENSE_URL` 是否正确
- 私有仓库需要设置 `LICENSE_TOKEN`
- 确认 Token 有 `repo` 权限

### 机器码不匹配
- 每台服务器的机器码不同
- 如需多服务器授权，修改 `machine_code` 字段为空或删除该字段

### 服务未停止
- 授权检查间隔为 7 天（604800 秒）
- 如需立即生效，重启后端容器
