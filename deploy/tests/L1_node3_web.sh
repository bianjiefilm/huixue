#!/bin/bash
# === L1-NODE3: Web 节点 #3 (.41) 自检 ===
# 执行: ssh huixueops@192.168.109.41 'bash -s' < L1_node3_web.sh

echo "========== L1: Web 节点 #3 自检 =========="
PASS=0; FAIL=0

echo -n "[3.1] Docker 服务运行中... "
if pgrep -x dockerd &>/dev/null || pgrep -f "dockerd" &>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[3.2] Frontend 容器运行中... "
if sudo docker ps --format '{{.Names}}' | grep -qi frontend; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[3.3] FastAPI(后端) 容器运行中... "
if sudo docker ps --format '{{.Names}}' | grep -qi backend; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[3.4] 前端端口 3000 监听中... "
if ss -tlnp | grep -q ':3000'; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[3.5] 后端端口 8000 监听中... "
if ss -tlnp | grep -q ':8000'; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[3.6] NFS 挂载 #1 的资源目录... "
if mount | grep -q "192.168.109.42"; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo ""
echo "========== L1 #3 结果: $PASS 通过, $FAIL 失败 =========="
[ $FAIL -eq 0 ] && exit 0 || exit 1
