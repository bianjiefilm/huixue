#!/bin/bash
# =============================================================================
# 慧学 远程部署脚本（直接在服务器上运行）
# =============================================================================
#
# 使用方法（在管理节点上执行）：
#   chmod +x deploy-remote.sh
#   ./deploy-remote.sh init      # 初始化集群
#   ./deploy-remote.sh build     # 构建镜像
#   ./deploy-remote.sh deploy    # 部署服务
#   ./deploy-remote.sh start     # 完整部署
#
# =============================================================================

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# 配置变量
MANAGER_IP="<慧学内网物理IP-1>"
WORKER_IPS=("<慧学内网物理IP-2备>" "<慧学内网物理IP-3备>")
NODE1_HOSTNAME="bigdata-platform"
NODE2_HOSTNAME="dashujuyingyong"
NODE3_HOSTNAME="huixuedashuju-PowerEdge-R730xd"

# 获取本机 IP
MY_IP=$(hostname -I | awk '{print $1}')

# 判断本机角色
is_manager() {
    [ "$MY_IP" = "$MANAGER_IP" ]
}

is_worker() {
    for ip in "${WORKER_IPS[@]}"; do
        if [ "$MY_IP" = "$ip" ]; then
            return 0
        fi
    done
    return 1
}

# 初始化集群（在管理节点执行）
init_cluster() {
    if ! is_manager; then
        echo_info "请在管理节点 (${MANAGER_IP}) 上执行此命令"
        exit 1
    fi

    echo_info "初始化 Docker Swarm 集群..."

    # 初始化 Swarm
    docker swarm init --advertise-addr ${MANAGER_IP}

    # 获取 token
    MANAGER_TOKEN=$(docker swarm join-token manager -q)
    WORKER_TOKEN=$(docker swarm join-token worker -q)

    echo "=== 节点加入命令 ==="
    echo ""
    echo "在节点二 (${WORKER_IPS[0]}) 上执行："
    echo "  docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377"
    echo ""
    echo "在节点三 (${WORKER_IPS[1]}) 上执行："
    echo "  docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377"
    echo ""

    # 自动加入节点二
    echo_info "尝试自动将节点二加入集群..."
    ssh -o StrictHostKeyChecking=no root@${WORKER_IPS[0]} \
        "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377" 2>/dev/null || \
        echo_warn "自动加入失败，请手动在节点二执行上述命令"

    # 自动加入节点三
    echo_info "尝试自动将节点三加入集群..."
    ssh -o StrictHostKeyChecking=no root@${WORKER_IPS[1]} \
        "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377" 2>/dev/null || \
        echo_warn "自动加入失败，请手动在节点三执行上述命令"

    # 配置节点标签
    echo_info "配置节点标签..."
    docker node update --label-add storage=true --label-add db=true ${NODE1_HOSTNAME}
    docker node update --label-add compute=true --label-add backend=true ${NODE2_HOSTNAME}
    docker node update --label-add frontend=true --label-add manager=true ${NODE3_HOSTNAME}

    echo_success "集群初始化完成"

    # 显示节点状态
    echo ""
    echo_info "节点状态："
    docker node ls
}

# 构建镜像
build_images() {
    echo_info "构建 Docker 镜像..."

    REGISTRY="${MANAGER_IP}:5000"

    # 启动本地仓库
    echo_info "启动镜像仓库..."
    docker run -d --name registry \
        --restart=always \
        -p 5000:5000 \
        -v registry-data:/var/lib/registry \
        registry:2

    # 构建后端
    echo_info "构建后端镜像..."
    cd /opt/huixue
    docker build -t huixue-backend:latest ./backend
    docker tag huixue-backend:latest ${REGISTRY}/huixue-backend:latest
    docker push ${REGISTRY}/huixue-backend:latest

    # 构建前端
    echo_info "构建前端镜像..."
    docker build -t huixue-frontend:latest ./frontend
    docker tag huixue-frontend:latest ${REGISTRY}/huixue-frontend:latest
    docker push ${REGISTRY}/huixue-frontend:latest

    # 构建 Jupyter
    echo_info "构建 Jupyter 镜像..."
    docker build -t huixue-jupyter:latest ./jupyter
    docker tag huixue-jupyter:latest ${REGISTRY}/huixue-jupyter:latest
    docker push ${REGISTRY}/huixue-jupyter:latest

    echo_success "镜像构建并推送完成"
}

# 部署服务
deploy() {
    if ! is_manager; then
        echo_info "请在管理节点 (${MANAGER_IP}) 上执行此命令"
        exit 1
    fi

    echo_info "部署服务..."

    cd /opt/huixue/deploy/config

    # 设置环境变量
    export REGISTRY_URL="${MANAGER_IP}:5000"
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-huixue123}
    export JUPYTER_TOKEN=${JUPYTER_TOKEN:-huixue_token}
    export SECRET_KEY=${SECRET_KEY:-huixue-secret-key-change-in-production}

    # 部署
    docker stack deploy -c docker-stack.yml huixue

    echo_success "服务部署完成"

    # 显示状态
    echo ""
    echo_info "服务状态："
    docker stack services huixue
}

# 查看状态
status() {
    docker stack services huixue
}

# 查看日志
logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        docker stack logs huixue
    else
        docker service logs huixue_${SERVICE}
    fi
}

# 重启服务
restart() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        echo_info "重启所有服务..."
        docker stack rm huixue
        sleep 5
        deploy
    else
        echo_info "重启服务: $SERVICE"
        docker service update huixue_${SERVICE} --force
    fi
}

# 停止服务
stop() {
    echo_info "停止服务..."
    docker stack rm huixue
    echo_success "服务已停止"
}

# 查看节点
nodes() {
    echo_info "集群节点："
    docker node ls
}

# 帮助
help() {
    echo "慧学 远程部署脚本"
    echo ""
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  init        初始化 Docker Swarm 集群（管理节点执行）"
    echo "  build       构建并推送镜像（管理节点执行）"
    echo "  deploy      部署服务（管理节点执行）"
    echo "  start       完整部署流程（管理节点执行）"
    echo "  status      查看服务状态"
    echo "  logs [服务] 查看日志"
    echo "  restart [服务] 重启服务"
    echo "  stop        停止服务"
    echo "  nodes       查看集群节点"
    echo ""
    echo "节点角色："
    echo "  管理节点: ${MANAGER_IP} (bigdata-platform)"
    echo "  工作节点: ${WORKER_IPS[0]} (dashujuyingyong)"
    echo "  工作节点: ${WORKER_IPS[1]} (huixuedashuju-PowerEdge-R730xd)"
}

main() {
    case "${1:-}" in
        init)
            init_cluster
            ;;
        build)
            build_images
            ;;
        deploy)
            deploy
            ;;
        start)
            init_cluster
            build_images
            deploy
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
        nodes)
            nodes
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo "未知命令: $1"
            help
            exit 1
            ;;
    esac
}

main "$@"
