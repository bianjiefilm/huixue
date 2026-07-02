#!/bin/bash
# === 部署验证总控脚本 ===
# 从 Mac 本地执行，依次远程运行 L1→L2→L3
# 用法: bash deploy/tests/run_all.sh
#
# 前提: Mac 已配置 SSH 免密到三台服务器

set -e

NODE1="huixueops@192.168.109.42"
NODE2="huixueops@192.168.109.43"
NODE3="huixueops@192.168.109.43"  # Relocated from .41 due to SSH hang
JUMP="huixueops@100.91.185.49"  # Tailscale 跳板

DIR="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║   慧学平台 — 部署验证测试 (44 用例)      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# L1: 数据节点
echo "▶ L1: 数据节点 #1 (.42)"
ssh -J $JUMP $NODE1 'bash -s' < "$DIR/L1_node1_data.sh" || {
  echo "⛔ L1 #1 失败，停止。先修复数据节点再继续。"
  exit 1
}
echo ""

# L1: 计算节点
echo "▶ L1: 计算节点 #2 (.43)"
ssh -J $JUMP $NODE2 'bash -s' < "$DIR/L1_node2_compute.sh" || {
  echo "⛔ L1 #2 失败，停止。先修复计算节点再继续。"
  exit 1
}
echo ""

# L1: Web 节点
echo "▶ L1: Web 节点 #3 (.43)"
ssh -J $JUMP $NODE3 'bash -s' < "$DIR/L1_node3_web.sh" || {
  echo "⛔ L1 #3 失败，停止。先修复 Web 节点再继续。"
  exit 1
}
echo ""

# L2: 节点间通信
echo "▶ L2: 节点间通信验证 (从 Web 节点执行)"
ssh -J $JUMP $NODE3 'bash -s' < "$DIR/L2_inter_node.sh" || {
  echo "⛔ L2 失败，停止。检查网络/防火墙/NFS 配置。"
  exit 1
}
echo ""

# L3: 服务集成
echo "▶ L3: 服务集成验证 (从 Web 节点执行)"
ssh -J $JUMP $NODE3 'bash -s' < "$DIR/L3_service_integration.sh" || {
  echo "⛔ L3 失败，停止。检查服务配置/DB连接/API路由。"
  exit 1
}
echo ""

echo "╔══════════════════════════════════════════╗"
echo "║   ✅ L1-L3 全部通过！                     ║"
echo "║   请进入 L4 浏览器手动冒烟测试:           ║"
echo "║   http://192.168.109.43:3000              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "L4 检查清单:"
echo "  [ ] L4.1 登录页正常渲染"
echo "  [ ] L4.2 admin 登录，15 门课程展示"
echo "  [ ] L4.3 课程教学大纲可查看"
echo "  [ ] L4.4 教学视频可播放"
echo "  [ ] L4.5 实训环境可启动"
echo "  [ ] L4.6 teacher1 课堂详情正常"
