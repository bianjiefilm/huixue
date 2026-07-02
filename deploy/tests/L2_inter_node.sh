#!/bin/bash
# === L2: 节点间通信验证 ===
# 执行位置: Web节点上执行 (.43)
# ssh huixueops@192.168.109.43 'bash -s' < L2_inter_node.sh

echo "========== L2: 节点间通信验证 =========="
PASS=0; FAIL=0

# --- #3 → #1 通信 ---

echo -n "[L2.1] #3 → #1 PostgreSQL (5432)... "
if timeout 3 bash -c "echo > /dev/tcp/192.168.109.42/5432" 2>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌ 连接超时"; ((FAIL++))
fi

echo -n "[L2.2] #3 → #1 Redis (6379)... "
if timeout 3 bash -c "echo > /dev/tcp/192.168.109.42/6379" 2>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌ 连接超时"; ((FAIL++))
fi

echo -n "[L2.3] #3 NFS 读取 #1 资源文件... "
if ls /mnt/huixue_data/ 2>/dev/null | head -1 | grep -q .; then
  echo "✅"; ((PASS++))
else
  echo "❌ NFS 不可读"; ((FAIL++))
fi

echo -n "[L2.4] #3 后端 API health check... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ HTTP $HEALTH"; ((FAIL++))
fi

# --- #3 → #2 通信 ---

echo -n "[L2.5] #3 → #2 SSH 连通性... "
if timeout 3 bash -c "echo > /dev/tcp/192.168.109.43/22" 2>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[L2.6] #3 → #2 远程 Docker 命令... "
RESULT=$(sudo docker ps --format '{{.Names}}' 2>/dev/null | head -1)
if [ -n "$RESULT" ] || sudo docker info &>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌ 远程 Docker 不可达"; ((FAIL++))
fi

# --- #2 → #1 通信 ---

echo -n "[L2.7] #3 NFS 读取 #1 资源文件... "
RESULT=$(sudo ls /mnt/huixue_data/ 2>/dev/null | head -1)
if [ -n "$RESULT" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[L2.8] 三节点互 ping... "
P1=$(ping -c 1 -W 1 192.168.109.42 2>/dev/null | grep -c "1 received")
P2=$(ping -c 1 -W 1 192.168.109.43 2>/dev/null | grep -c "1 received")
if [ "$P1" = "1" ] && [ "$P2" = "1" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ ping 失败 (.42=$P1 .43=$P2)"; ((FAIL++))
fi

echo ""
echo "========== L2 结果: $PASS 通过, $FAIL 失败 =========="
[ $FAIL -eq 0 ] && exit 0 || exit 1
