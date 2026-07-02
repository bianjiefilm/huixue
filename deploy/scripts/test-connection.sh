#!/bin/bash
# =============================================================================
# 慧学 局域网连通性测试脚本
# =============================================================================
#
# 使用方法：
#   chmod +x test-connection.sh
#   ./test-connection.sh
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

# 配置
NODE1_IP="<慧学内网物理IP-1>"
NODE2_IP="<慧学内网物理IP-2备>"
NODE3_IP="<慧学内网物理IP-3备>"
SSH_USER="root"
SSH_PASSWORD="12345678"

NODE1_NAME="bigdata-platform"
NODE2_NAME="dashujuyingyong"
NODE3_NAME="huixuedashuju"

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_fail() { echo -e "${RED}[FAIL]${NC} $1"; }

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║       慧学 局域网连通性测试                       ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# 测试 SSH 连接
test_ssh() {
    local host=$1
    local name=$2
    echo_info "测试 SSH 连接: ${name} (${host})"

    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
           -o BatchMode=yes \
           "${SSH_USER}@${host}" "echo 'OK'" 2>/dev/null; then
        echo_ok "  SSH 连接成功"
        return 0
    else
        echo_fail "  SSH 连接失败"
        return 1
    fi
}

# 测试端口可达性
test_port() {
    local host=$1
    local port=$2
    local name=$3

    if nc -z -w 3 "${host}" "${port}" 2>/dev/null; then
        echo_ok "  ${port} 端口可达"
        return 0
    else
        echo_warn "  ${port} 端口不可达"
        return 1
    fi
}

# 测试 Docker
test_docker() {
    local host=$1
    local name=$2
    echo_info "测试 Docker 服务: ${name} (${host})"

    local version=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
        "docker version --format '{{.Server.Version}}'" 2>/dev/null)

    if [ -n "$version" ]; then
        echo_ok "  Docker 版本: ${version}"
        return 0
    else
        echo_fail "  Docker 未运行或无响应"
        return 1
    fi
}

# 测试 Docker Swarm
test_swarm() {
    local host=$1
    local name=$2
    echo_info "测试 Docker Swarm: ${name} (${host})"

    local status=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
        "docker info --format '{{.Swarm.LocalNodeState}}'" 2>/dev/null)

    if [ "$status" = "active" ]; then
        echo_ok "  Swarm 状态: active"

        local role=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
            "docker info --format '{{.Swarm.ControlAvailable}}'" 2>/dev/null)

        if [ "$role" = "true" ]; then
            echo "    角色: Manager"
        else
            echo "    角色: Worker"
        fi
        return 0
    else
        echo_warn "  Swarm 状态: ${status} (可能未初始化)"
        return 1
    fi
}

# 测试本地服务
test_local_services() {
    local host=$1
    local name=$2
    echo_info "测试本地服务: ${name} (${host})"

    # 测试 Docker Socket
    if ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
        "test -S /var/run/docker.sock && echo 'OK'" 2>/dev/null; then
        echo_ok "  Docker Socket 可用"
    else
        echo_warn "  Docker Socket 不可用"
    fi

    # 测试 Docker 命令
    local containers=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
        "docker ps -q 2>/dev/null | wc -l" 2>/dev/null)
    echo "  运行中容器: ${containers} 个"
}

# 交叉测试节点间通信
test_node_to_node() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  节点间通信测试                                          ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    local nodes=("${NODE1_IP}:${NODE1_NAME}" "${NODE2_IP}:${NODE2_NAME}" "${NODE3_IP}:${NODE3_NAME}")

    for node1 in "${nodes[@]}"; do
        local ip1=$(echo "$node1" | cut -d: -f1)
        local name1=$(echo "$node1" | cut -d: -f2)

        for node2 in "${nodes[@]}"; do
            local ip2=$(echo "$node2" | cut -d: -f1)
            local name2=$(echo "$node2" | cut -d: -f2)

            if [ "$ip1" != "$ip2" ]; then
                echo_info "${name1} → ${name2} (${ip2})"

                # 测试基本连通性
                if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 \
                       "${SSH_USER}@${ip1}" "ping -c 1 -W 1 ${ip2}" 2>/dev/null | grep -q "1 received"; then
                    echo_ok "  ICMP 连通"
                else
                    echo_warn "  ICMP 不通"
                fi

                # 测试 Docker 端口
                if ssh -o StrictHostKeyChecking=no "${SSH_USER}@${ip1}" \
                    "nc -z -w 2 ${ip2} 2375 2>/dev/null"; then
                    echo_ok "  Docker 端口 (2375) 可达"
                else
                    echo_warn "  Docker 端口 (2375) 不可达"
                fi
            fi
        done
    done
}

# 测试镜像仓库
test_registry() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  镜像仓库测试                                          ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    echo_info "测试镜像仓库: ${NODE1_IP}:5000"

    # 测试仓库可达性
    if nc -z -w 3 "${NODE1_IP}" 5000 2>/dev/null; then
        echo_ok "  仓库端口可达"

        # 获取仓库目录
        local catalog=$(curl -s "http://${NODE1_IP}:5000/v2/_catalog" 2>/dev/null)
        if [ -n "$catalog" ]; then
            echo "  仓库目录: ${catalog}"
        else
            echo_warn "  无法获取仓库目录"
        fi
    else
        echo_warn "  仓库端口不可达"
    fi
}

# 测试服务端口
test_service_ports() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  服务端口测试                                          ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━��━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # PostgreSQL
    echo_info "PostgreSQL (5432)"
    for ip in $NODE1_IP $NODE2_IP $NODE3_IP; do
        nc -z -w 2 $ip 5432 2>/dev/null && echo_ok "  ${ip}:5432 可达" || echo_warn "  ${ip}:5432 不可达"
    done

    # Redis
    echo_info "Redis (6379)"
    for ip in $NODE1_IP $NODE2_IP $NODE3_IP; do
        nc -z -w 2 $ip 6379 2>/dev/null && echo_ok "  ${ip}:6379 可达" || echo_warn "  ${ip}:6379 不可达"
    done
}

# 主测试流程
run_tests() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  SSH 连接测试                                          ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    test_ssh "${NODE1_IP}" "${NODE1_NAME}" || true
    test_ssh "${NODE2_IP}" "${NODE2_NAME}" || true
    test_ssh "${NODE3_IP}" "${NODE3_NAME}" || true

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  Docker 服务测试                                      ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    test_docker "${NODE1_IP}" "${NODE1_NAME}"
    test_docker "${NODE2_IP}" "${NODE2_NAME}"
    test_docker "${NODE3_IP}" "${NODE3_NAME}"

    # 测试 Swarm
    echo ""
    test_swarm "${NODE1_IP}" "${NODE1_NAME}"
    test_swarm "${NODE2_IP}" "${NODE2_NAME}"
    test_swarm "${NODE3_IP}" "${NODE3_NAME}"

    # 测试节点间通信
    test_node_to_node

    # 测试镜像仓库
    test_registry

    # 测试服务端口
    test_service_ports

    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  测试完成                                              ${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 快速测试（仅 SSH 和 Docker）
quick_test() {
    echo_info "快速测试..."

    all_ok=true

    for ip in $NODE1_IP $NODE2_IP $NODE3_IP; do
        if ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
                -o BatchMode=yes \
                "${SSH_USER}@${ip}" "echo 'OK'" 2>/dev/null; then
            echo_fail "SSH 失败: ${ip}"
            all_ok=false
        fi
    done

    if $all_ok; then
        echo_ok "所有节点 SSH 连接正常"
    fi
}

# 主函数
main() {
    case "${1:-}" in
        quick)
            quick_test
            ;;
        *)
            run_tests
            ;;
    esac
}

main "$@"
