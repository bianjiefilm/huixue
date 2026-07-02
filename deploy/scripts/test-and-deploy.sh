#!/bin/bash
# =============================================================================
# 慧学 一键测试并部署脚本
# =============================================================================
#
# 功能：
#   1. 测试三台服务器之间的连接
#   2. 如果测试通过，自动部署
#
# 使用方法：
#   chmod +x test-and-deploy.sh
#   ./test-and-deploy.sh
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
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# 配置
NODE1_IP="172.16.100.41"
NODE2_IP="172.16.100.146"
NODE3_IP="172.16.100.176"
NODE1_NAME="bigdata-platform"
NODE2_NAME="dashujuyingyong"
NODE3_NAME="huixuedashuju"
SSH_USER="root"

# 测试 SSH 连接
test_ssh() {
    local host=$1
    local name=$2
    echo_info "测试 SSH: ${name} (${host})"

    if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
           -o BatchMode=yes \
           "${SSH_USER}@${host}" "echo 'OK'" 2>/dev/null; then
        echo_ok "  SSH 成功"
        return 0
    else
        echo_fail "  SSH 失败"
        return 1
    fi
}

# 测试 Docker
test_docker() {
    local host=$1
    local name=$2
    echo_info "测试 Docker: ${name} (${host})"

    local version=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
        "docker version --format '{{.Server.Version}}'" 2>/dev/null)

    if [ -n "$version" ]; then
        echo_ok "  Docker ${version}"
        return 0
    else
        echo_fail "  Docker 未运行"
        return 1
    fi
}

# 测试节点间连通性
test_node_connectivity() {
    local host=$1
    local name=$2
    echo_info "测试节点连通性: ${name} (${host})"

    for target in $NODE2_IP $NODE3_IP; do
        if ssh -o StrictHostKeyChecking=no "${SSH_USER}@${host}" \
            "ping -c 1 -W 1 ${target}" 2>/dev/null | grep -q "1 received"; then
            echo_ok "  → ${target} 连通"
        else
            echo_warn "  → ${target} 不通"
        fi
    done
}

# 测试端口
test_ports() {
    local host=$1
    local name=$2
    echo_info "测试关键端口: ${name} (${host})"

    # 测试 Docker 端口
    if nc -z -w 2 "$host" 2375 2>/dev/null; then
        echo_ok "  2375 (Docker) 可达"
    else
        echo_warn "  2375 (Docker) 不可达"
    fi
}

# 执行连接测试
run_connection_tests() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              连接测试                                      ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    local all_ok=true

    # 测试所有节点
    for ip in $NODE1_IP $NODE2_IP $NODE3_IP; do
        case $ip in
            $NODE1_IP) name=$NODE1_NAME ;;
            $NODE2_IP) name=$NODE2_NAME ;;
            $NODE3_IP) name=$NODE3_NAME ;;
        esac

        echo ""
        echo -e "${CYAN}--- ${name} (${ip}) ---${NC}"

        if ! test_ssh "$ip" "$name"; then
            all_ok=false
            continue
        fi

        test_docker "$ip" "$name"
        test_ports "$ip" "$name"
    done

    # 测试节点间连通性
    echo ""
    echo -e "${CYAN}--- 节点间连通性 ---${NC}"
    for ip in $NODE1_IP $NODE2_IP $NODE3_IP; do
        case $ip in
            $NODE1_IP) name=$NODE1_NAME ;;
            $NODE2_IP) name=$NODE2_NAME ;;
            $NODE3_IP) name=$NODE3_NAME ;;
        esac
        test_node_connectivity "$ip" "$name"
    done

    if ! $all_ok; then
        echo ""
        echo_fail "连接测试未通过，请检查网络和 SSH 配置"
        echo ""
        read -p "是否继续部署？(y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    echo ""
    echo_ok "连接测试完成"
}

# 初始化集群
init_cluster() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              初始化集群                                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # 获取 token
    echo_info "获取 Swarm token..."
    MANAGER_TOKEN=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker swarm join-token manager -q" 2>/dev/null)
    WORKER_TOKEN=$(ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker swarm join-token worker -q" 2>/dev/null)

    # 初始化管理节点
    echo_info "初始化管理节点 (${NODE1_IP})..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker swarm init --advertise-addr ${NODE1_IP}"

    echo_ok "管理节点初始化完成"

    # 节点二加入
    echo_info "节点二 (${NODE2_IP}) 加入集群..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE2_IP}" \
        "docker swarm join --token ${WORKER_TOKEN} ${NODE1_IP}:2377"
    echo_ok "节点二加入成功"

    # 节点三加入
    echo_info "节点三 (${NODE3_IP}) 加入集群..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE3_IP}" \
        "docker swarm join --token ${WORKER_TOKEN} ${NODE1_IP}:2377"
    echo_ok "节点三加入成功"

    # 配置标签
    echo_info "配置节点标签..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker node update --label-add storage=true --label-add db=true ${NODE1_NAME}"
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker node update --label-add compute=true --label-add backend=true ${NODE2_NAME}"
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" \
        "docker node update --label-add frontend=true --label-add manager=true ${NODE3_NAME}"

    echo_ok "标签配置完成"

    # 显示节点状态
    echo ""
    echo_info "集群节点状态："
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" "docker node ls"
}

# 构建镜像
build_images() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              构建镜像                                      ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    REGISTRY="${NODE1_IP}:5000"

    # 启动仓库
    echo_info "启动镜像仓库..."
    ssh -o StrictHostKeyChecking=no "${SSH_USER}@${NODE1_IP}" "
        docker rm -f registry 2>/dev/null
        docker run -d --name registry \
            --restart=always \
            -p 5000:5000 \
            -v registry-data:/var/lib/registry \
            registry:2
    "
    echo_ok "镜像仓库已启动"

    # 构建后端
    echo_info "构建后端镜像..."
    cd /Users/jimfu/Work/huixue
    docker build -t huixue-backend:latest ./backend
    docker tag huixue-backend:latest ${REGISTRY}/huixue-backend:latest
    docker push ${REGISTRY}/huixue-backend:latest
    echo_ok "后端镜像已推送"

    # 构建前端
    echo_info "构建前端镜像..."
    docker build -t huixue-frontend:latest ./frontend
    docker tag huixue-frontend:latest ${REGISTRY}/huixue-frontend:latest
    docker push ${REGISTRY}/huixue-frontend:latest
    echo_ok "前端镜像已推送"

    # 构建 Jupyter
    echo_info "构建 Jupyter 镜像..."
    docker build -t huixue-jupyter:latest ./jupyter
    docker tag huixue-jupyter:latest ${REGISTRY}/huixue-jupyter:latest
    docker push ${REGISTRY}/huixue-jupyter:latest
    echo_ok "Jupyter 镜像已推送"
}

# 部署服务
deploy_services() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║              部署服务                                      ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    cd /Users/jimfu/Work/huixue/deploy/config

    # 部署
    echo_info "部署服务到集群..."
    docker -H ssh://${SSH_USER}@${NODE1_IP} stack deploy -c docker-stack.yml huixue

    echo_ok "服务部署完成"

    # 等待服务启动
    echo_info "等待服务启动 (30秒)..."
    sleep 30

    # 显示状态
    echo ""
    echo_info "服务状态："
    docker -H ssh://${SSH_USER}@${NODE1_IP} stack services huixue
}

# 主函数
main() {
    # 1. 连接测试
    run_connection_tests

    # 2. 初始化集群
    read -p "是否初始化集群？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        init_cluster

        # 3. 构建镜像
        read -p "是否构建镜像？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            build_images

            # 4. 部署服务
            read -p "是否部署服务？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                deploy_services
            fi
        fi
    fi

    echo ""
    echo_ok "完成！"
}

main "$@"
