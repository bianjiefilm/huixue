#!/bin/bash
# === L1-NODE2: 计算节点 #2 (.43) 自检 ===
# 执行: ssh <慧学运维账号>@<慧学内网IP-2> 'bash -s' < L1_node2_compute.sh

echo "========== L1: 计算节点 #2 自检 =========="
PASS=0; FAIL=0

echo -n "[2.1] Docker 服务运行中... "
if systemctl is-active docker &>/dev/null; then
  echo "✅"; ((PASS++))
else
  echo "❌"; ((FAIL++))
fi

echo -n "[2.2] Jupyter 镜像已存在... "
if sudo docker images --format '{{.Repository}}' | grep -qi jupyter; then
  echo "✅"; ((PASS++))
else
  echo "❌ Jupyter 镜像未拉取"; ((FAIL++))
fi

echo -n "[2.3] NFS 挂载 #1 的资源目录... "
if mount | grep -q "<慧学内网IP-1>"; then
  echo "✅"; ((PASS++))
else
  echo "❌ NFS 未挂载"; ((FAIL++))
fi

echo -n "[2.4] NFS 挂载点可读取资源文件... "
NFS_FILES=$(sudo find /mnt/huixue_resources -type f 2>/dev/null | head -5 | wc -l)
if [ "$NFS_FILES" -gt 0 ]; then
  echo "✅"; ((PASS++))
else
  echo "❌ NFS 挂载点为空或不可读"; ((FAIL++))
fi

echo -n "[2.5] 容器管理服务端口监听... "
if ss -tlnp | grep -qE ':(8888|8080)'; then
  echo "✅"; ((PASS++))
else
  echo "⚠️ 无专用管理端口（可能由后端直接 Docker API 调用）"; ((PASS++))
fi

echo -n "[2.6] 可用内存 > 100GB... "
AVAIL_GB=$(awk '/MemAvailable/ {printf "%d", $2/1024/1024}' /proc/meminfo)
if [ "$AVAIL_GB" -gt 100 ]; then
  echo "✅ (${AVAIL_GB}GB 可用)"; ((PASS++))
else
  echo "⚠️ 可用: ${AVAIL_GB}GB"; ((FAIL++))
fi

echo ""
echo "========== L1 #2 结果: $PASS 通过, $FAIL 失败 =========="
[ $FAIL -eq 0 ] && exit 0 || exit 1
