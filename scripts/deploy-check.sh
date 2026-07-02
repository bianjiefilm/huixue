#!/bin/bash
# =============================================================================
# 慧学 部署检查脚本
# 用法: ./scripts/deploy-check.sh
# =============================================================================

set -e

echo "=========================================="
echo "慧学 部署检查"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

# 1. 检查 Docker 服务
echo "【1】Docker 服务检查"
if docker info &>/dev/null; then
    check_pass "Docker 服务运行正常"
else
    check_fail "Docker 服务未运行"
    exit 1
fi

# 2. 检查 Docker Swarm
echo ""
echo "【2】Docker Swarm 检查"
if docker info 2>/dev/null | grep -q "Swarm: active"; then
    check_pass "Docker Swarm 已激活"
else
    check_fail "Docker Swarm 未激活"
    exit 1
fi

# 3. 检查 Registry 连接
echo ""
echo "【3】Registry 连接检查"
REGISTRY_URL="${REGISTRY_URL:-<慧学内网物理IP-1>:5000}"
if docker pull "$REGISTRY_URL/huixue-backend:v8" &>/dev/null; then
    check_pass "Registry 连接正常"
else
    check_warn "Registry 连接异常，可能需要推送镜像"
fi

# 4. 检查环境变量
echo ""
echo "【4】环境变量检查"
if [ -n "$HOST_MACHINE_CODE" ]; then
    check_pass "HOST_MACHINE_CODE 已设置: ${HOST_MACHINE_CODE:0:8}..."
else
    check_warn "HOST_MACHINE_CODE 未设置"
fi

# 5. 检查授权文件
echo ""
echo "【5】授权文件检查"
LICENSE_PATH="/home/dashujuyingyong/huixue-yuanban/license_node2.json"
if [ -f "$LICENSE_PATH" ]; then
    check_pass "授权文件存在: $LICENSE_PATH"
    # 检查文件内容
    if grep -q '"machine_id"' "$LICENSE_PATH"; then
        check_pass "授权文件格式正确"
    else
        check_fail "授权文件格式错误"
    fi
else
    check_fail "授权文件不存在: $LICENSE_PATH"
fi

# 6. 检查 ziyuan_data 目录
echo ""
echo "【6】课程资源检查"
ZIYUAN_PATH="/home/dashujuyingyong/huixue-yuanban/ziyuan_data"
if [ -d "$ZIYUAN_PATH" ]; then
    FILE_COUNT=$(find "$ZIYUAN_PATH" -type f 2>/dev/null | wc -l)
    check_pass "资源目录存在，包含 $FILE_COUNT 个文件"
else
    check_fail "资源目录不存在: $ZIYUAN_PATH"
fi

# 7. 检查服务状态
echo ""
echo "【7】服务状态检查"
if docker stack ps huixue &>/dev/null; then
    BACKEND_RUNNING=$(docker stack ps huixue 2>/dev/null | grep -c "Running" | head -1 || echo "0")
    check_pass "服务栈存在，后端运行副本: $BACKEND_RUNNING"
else
    check_warn "服务栈不存在，需要部署"
fi

# 8. 检查授权日志
echo ""
echo "【8】授权状态检查"
if docker service logs huixue_backend 2>&1 | grep -q "授权检查: valid"; then
    check_pass "授权验证通过"
elif docker service logs huixue_backend 2>&1 | grep -q "授权检查: disabled"; then
    check_fail "授权验证失败"
else
    check_warn "无法确定授权状态，请查看日志"
fi

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="

# 快捷命令提示
echo ""
echo "【常用命令】"
echo "  查看服务状态: docker stack ps huixue"
echo "  查看授权日志: docker service logs huixue_backend 2>&1 | grep -E '(授权|license|valid)'"
echo "  重启后端: docker service update --force huixue_backend"
echo "  更新环境变量: export HOST_MACHINE_CODE=e3336e82073d903ece613a15c25ffa4d && docker service update --env-add HOST_MACHINE_CODE=e3336e82073d903ece613a15c25ffa4d huixue_backend"
