#!/bin/bash
# =============================================================================
# 慧学 三服务器部署脚本
# =============================================================================
#
# 功能：
#   1. 初始化 Docker Swarm 集群
#   2. 构建并推送镜像到本地仓库
#   3. 部署服务到集群
#
# 使用方法：
#   ./deploy.sh init        # 初始化集群
#   ./deploy.sh build       # 构建镜像
#   ./deploy.sh deploy      # 部署服务
#   ./deploy.sh start       # 完整部署（初始化+构建+部署）
#   ./deploy.sh status      # 查看服务状态
#   ./deploy.sh logs        # 查看日志
#   ./deploy.sh restart     # 重启服务
#   ./deploy.sh stop        # 停止并删除服务
#   ./deploy.sh scale       # 扩缩容
#
# =============================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 加载配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config/cluster.conf"

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# SSH 连接函数
ssh_cmd() {
    local host=$1
    local cmd=$2
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
        "${SSH_USER}@${host}" "${cmd}"
}

# 检查 SSH 连接
check_ssh() {
    echo_info "检查 SSH 连接..."
    for node in ${MANAGER_NODE} ${WORKER_NODES//,/ }; do
        if ssh_cmd "${node}" "echo 'OK'" 2>/dev/null; then
            echo_success "  ${node} - SSH 连接成功"
        else
            echo_error "  ${node} - SSH 连接失败"
            exit 1
        fi
    done
}

# 初始化 Docker Swarm
init_swarm() {
    echo_info "初始化 Docker Swarm 集群..."

    # 在管理节点初始化
    echo_info "  在 ${MANAGER_NODE} 上初始化 Swarm..."
    ssh_cmd "${MANAGER_NODE}" "docker swarm init --advertise-addr ${MANAGER_NODE}"

    # 获取管理节点 token
    MANAGER_TOKEN=$(ssh_cmd "${MANAGER_NODE}" "docker swarm join-token manager -q")
    WORKER_TOKEN=$(ssh_cmd "${MANAGER_NODE}" "docker swarm join-token worker -q")

    echo_success "  Swarm 初始化完成"

    # 将节点二加入为 Worker
    echo_info "  将 ${NODE2_IP} 加入集群..."
    ssh_cmd "${NODE2_IP}" "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_NODE}:2377"

    # 将节点三加入为 Worker
    echo_info "  将 ${NODE3_IP} 加入集群..."
    ssh_cmd "${NODE3_IP}" "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_NODE}:2377"

    echo_success "  所有节点已加入集群"
}

# 配置节点标签
configure_nodes() {
    echo_info "配置节点标签..."

    # 节点一：存储和数据库
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add storage=true --label-add db=true ${MANAGER_NODE}"
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add hostname=${NODE1_HOSTNAME} ${MANAGER_NODE}"

    # 节点二：计算和后端
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add compute=true --label-add backend=true ${NODE2_IP}"
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add hostname=${NODE2_HOSTNAME} ${NODE2_IP}"

    # 节点三：前端和管理
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add frontend=true --label-add manager=true ${NODE3_IP}"
    ssh_cmd "${MANAGER_NODE}" "docker node update --label-add hostname=${NODE3_HOSTNAME} ${NODE3_IP}"

    echo_success "  节点标签配置完成"
}

# 构建镜像
build_images() {
    echo_info "构建 Docker 镜像..."

    cd "${SCRIPT_DIR}/.."

    # 打标签本地仓库
    REGISTRY="${NODE1_IP}:5000"

    echo_info "  构建后端镜像..."
    docker build -t huixue-backend:latest ./backend
    docker tag huixue-backend:latest ${REGISTRY}/huixue-backend:latest
    docker rmi huixue-backend:latest 2>/dev/null || true

    echo_info "  构建前端镜像..."
    docker build -t huixue-frontend:latest ./frontend
    docker tag huixue-frontend:latest ${REGISTRY}/huixue-frontend:latest
    docker rmi huixue-frontend:latest 2>/dev/null || true

    echo_info "  构建 Jupyter 镜像..."
    docker build -t huixue-jupyter:latest ./jupyter
    docker tag huixue-jupyter:latest ${REGISTRY}/huixue-jupyter:latest
    docker rmi huixue-jupyter:latest 2>/dev/null || true

    echo_success "  镜像构建完成"
}

# 推送镜像到本地仓库
push_images() {
    echo_info "推送镜像到本地仓库..."

    REGISTRY="${NODE1_IP}:5000"

    echo_info "  推送 huixue-backend..."
    docker push ${REGISTRY}/huixue-backend:latest

    echo_info "  推送 huixue-frontend..."
    docker push ${REGISTRY}/huixue-frontend:latest

    echo_info "  推送 huixue-jupyter..."
    docker push ${REGISTRY}/huixue-jupyter:latest

    echo_success "  镜像推送完成"
}

# 部署服务
deploy_services() {
    echo_info "部署服务到集群..."

    cd "${SCRIPT_DIR}/config"

    # 设置环境变量
    export REGISTRY_URL="${NODE1_IP}:5000"

    # 部署 stack
    docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack deploy -c docker-stack.yml huixue

    echo_success "  服务部署完成"
}

# 查看服务状态
status() {
    echo_info "服务状态："
    docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack services huixue
}

# 查看日志
logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack logs huixue
    else
        docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack services huixue | grep "$SERVICE"
    fi
}

# 重启服务
restart() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        echo_info "重启所有服务..."
        docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack rm huixue
        sleep 5
        deploy_services
    else
        echo_info "重启服务: $SERVICE"
        docker -H ssh://${SSH_USER}@${MANAGER_NODE} service update huixue_${SERVICE} --force
    fi
}

# 停止服务
stop() {
    echo_info "停止并删除服务..."
    docker -H ssh://${SSH_USER}@${MANAGER_NODE} stack rm huixue
    echo_success "  服务已停止"
}

# 扩缩容
scale() {
    SERVICE=$1
    REPLICAS=$2
    if [ -z "$SERVICE" ] || [ -z "$REPLICAS" ]; then
        echo_error "用法: ./deploy.sh scale <service> <replicas>"
        echo_error "  例如: ./deploy.sh scale backend 3"
        exit 1
    fi
    echo_info "扩缩容 ${SERVICE} 到 ${REPLICAS} 副本..."
    docker -H ssh://${SSH_USER}@${MANAGER_NODE} service scale huixue_${SERVICE}=${REPLICAS}
}

# 显示帮助
help() {
    echo "慧学 三服务器部署脚本"
    echo ""
    echo "用法: $0 <命令> [参数]"
    echo ""
    echo "命令:"
    echo "  init        初始化 Docker Swarm 集群"
    echo "  build       构建 Docker 镜像"
    echo "  push        推送镜像到本地仓库"
    echo "  deploy      部署服务到集群"
    echo "  start       完整部署（初始化+构建+部署）"
    echo "  status      查看服务状态"
    echo "  logs [服务]  查看日志"
    echo "  restart [服务] 重启服务（可选指定服务）"
    echo "  stop        停止并删除服务"
    echo "  scale <服务> <副本数>  扩缩容"
    echo ""
    echo "示例:"
    echo "  $0 start                    # 完整部署"
    echo "  $0 scale backend 3          # 后端扩展到3副本"
    echo "  $0 restart frontend         # 重启前端"
}

# 主函数
main() {
    case "${1:-}" in
        init)
            check_ssh
            init_swarm
            configure_nodes
            ;;
        build)
            build_images
            ;;
        push)
            push_images
            ;;
        deploy)
            deploy_services
            ;;
        start)
            check_ssh
            init_swarm
            configure_nodes
            build_images
            push_images
            deploy_services
            ;;
        status)
            status
            ;;
        logs)
            logs "${2:-}"
            ;;
        restart)
            restart "${2:-}"
            ;;
        stop)
            stop
            ;;
        scale)
            scale "${2:-}" "${3:-}"
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo_error "未知命令: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
