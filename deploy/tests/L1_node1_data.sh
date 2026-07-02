#!/bin/bash
# === L1-NODE1: 数据节点 #1 (.42) 自检 ===
# 执行: ssh <慧学运维账号>@<慧学内网IP-1> 'bash -s' < L1_node1_data.sh

echo "========== L1: 数据节点 #1 自检 =========="
PASS=0; FAIL=0

echo -n "[1.1] Docker 服务运行中... "
if systemctl is-active docker &>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌ Docker 未运行"; ((FAIL++))
fi

echo -n "[1.2] PostgreSQL 容器运行中... "
if docker ps --format '{{.Names}}' | grep -q db; then
  echo "✅"; ((PASS++))
else
  echo "❌ PostgreSQL 容器未运行"; ((FAIL++))
fi

echo -n "[1.3] PostgreSQL 返回 15 门课程... "
COUNT=$(docker exec $(docker ps -q -f name=db) \
  psql -U huixue -d huixue -t -c "SELECT count(*) FROM courses" 2>/dev/null | tr -d ' ')
if [ "$COUNT" = "15" ]; then
  echo "✅ ($COUNT)"; ((PASS++))
else
  echo "❌ 期望15, 实际: $COUNT"; ((FAIL++))
fi

echo -n "[1.4] Redis 容器运行且可 PING... "
PONG=$(docker exec $(docker ps -q -f name=redis) redis-cli ping 2>/dev/null)
if [ "$PONG" = "PONG" ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ Redis 不可连接"; ((FAIL++))
fi

echo -n "[1.5] 资源 目录存在且有文件... "
FCOUNT=$(find /opt/huixue-yuanban/backend/static/resources -type f 2>/dev/null | wc -l)
if [ "$FCOUNT" -gt 100 ]; then
  echo "✅ ($FCOUNT 个文件)"; ((PASS++))
else
  echo "❌ 文件数: $FCOUNT"; ((FAIL++))
fi

echo -n "[1.6] NFS Server 服务运行中... "
if systemctl is-active nfs-kernel-server &>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌ NFS Server 未运行"; ((FAIL++))
fi

echo -n "[1.7] NFS exports 包含网段授权... "
if grep -q "<慧学内网网段>.0/24" /etc/exports; then
  echo "✅"; ((PASS++))
else
  echo "❌ exports 缺少节点授权"; ((FAIL++))
fi

echo -n "[1.8] PostgreSQL 5432 端口监听中... "
if ss -tlnp | grep -q ':5432'; then
  echo "✅"; ((PASS++))
else
  echo "❌ 5432 未监听"; ((FAIL++))
fi

echo ""
echo "========== L1 #1 结果: $PASS 通过, $FAIL 失败 =========="
[ $FAIL -eq 0 ] && exit 0 || exit 1
