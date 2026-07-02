#!/bin/bash
# =============================================================================
# 慧学 本地连接测试（测试本机到三台服务器）
# =============================================================================
#
# 使用方法：
#   chmod +x test-local.sh
#   ./test-local.sh
#
# =============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_fail() { echo -e "${RED}[FAIL]${NC} $1"; }

# 配置
NODES=(
    "172.16.100.41:bigdata-platform"
    "172.16.100.146:dashujuyingyong"
    "172.16.100.176:huixuedashuju"
)

SSH_USER="root"
SSH_PASSWORD="12345678"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       慧学 本地连接测试                           ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 测试 SSH 连接
test_ssh() {
    local ip=$1
    local name=$2
    echo_info "测试 SSH: ${name} (${ip})"

    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
           -o BatchMode=yes \
           "${SSH_USER}@${ip}" "echo 'OK'" 2>/dev/null; then
        echo_ok "  SSH 成功"

        # 获取 Docker 版本
        local docker_version=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${ip}" \
            "docker version --format '{{.Server.Version}}'" 2>/dev/null)
        echo "  Docker: ${docker_version}"

        # 获取 Swarm 状态
        local swarm_state=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${ip}" \
            "docker info --format '{{.Swarm.LocalNodeState}}'" 2>/dev/null)
        echo "  Swarm: ${swarm_state}"

        return 0
    else
        echo_fail "  SSH 失败"
        return 1
    fi
}

# 测试端口
test_ports() {
    local ip=$1
    local name=$2
    echo_info "测试端口: ${name} (${ip})"

    # 定义需要测试的端口
    local ports="22 2375 2377 5000 5432 6379 8000 8888 3000"

    for port in $ports; do
        if nc -z -w 2 "$ip" "$port" 2>/dev/null; then
            echo_ok "  ${port} 端口可达"
        else
            echo "  ${port} 端口不可达"
        fi
    done
}

# 测试 API 服务
test_api() {
    local ip=$1
    local name=$2
    echo_info "测试 API: ${name} (${ip})"

    # 测试后端健康检查
    if curl -s -o /dev/null -w "%{http_code}" "http://${ip}:8000/health" 2>/dev/null | grep -q "200"; then
        echo_ok "  后端健康检查: 200 OK"
    else
        echo_warn "  后端健康检查: 失败"
    fi
}

# 测试 Web 服务
test_web() {
    local ip=$1
    local name=$2
    echo_info "测试 Web: ${name} (${ip})"

    if curl -s -o /dev/null -w "%{http_code}" "http://${ip}:3000" 2>/dev/null | grep -q "200"; then
        echo_ok "  Web 前端: 可访问"
    else
        echo_warn "  Web 前端: 不可访问"
    fi
}

# 获取节点信息
get_node_info() {
    local ip=$1
    local name=$2
    echo_info "节点信息: ${name} (${ip})"

    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${ip}" "
        echo '  主机名: ' \$(hostname)
        echo '  IP: ' \$(hostname -I | awk '{print \$1}')
        echo '  CPU: ' \$(nproc) 核
        echo '  内存: ' \$(free -h | grep Mem | awk '{print \$2}')
        echo '  磁盘: ' \$(df -h / | tail -1 | awk '{print \$2}')
        echo '  Docker: ' \$(docker version --format '{{.Server.Version}}')
        echo '  容器数: ' \$(docker ps -q | wc -l)
    " 2>/dev/null
}

# 主测试
run_tests() {
    for node in "${NODES[@]}"; do
        ip=$(echo "$node" | cut -d: -f1)
        name=$(echo "$node" | cut -d: -f2)

        echo ""
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${CYAN}  ${name} (${ip})                                     ${NC}"
        echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""

        test_ssh "$ip" "$name" || true
        test_ports "$ip" "$name" || true
    done

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  服务可用性测试                                        ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    test_api "$NODE2_IP" "后端服务"
    test_web "$NODE3_IP" "Web前端"

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  测试完成                                              ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

main() {
    run_tests
}

main
