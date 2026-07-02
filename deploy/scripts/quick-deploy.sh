#!/bin/bash
# =============================================================================
# 慧学 一键部署脚本
# =============================================================================
#
# 使用方法：
# 1. 将项目复制到节点一（172.16.100.41）
# 2. SSH 到节点一执行此脚本
#
# =============================================================================

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_fail() { echo -e "${RED}[FAIL]${NC} $1"; }

# 配置
MANAGER_IP="172.16.100.41"
NODE2_IP="172.16.100.146"
NODE3_IP="172.16.100.176"
NODE1_NAME="bigdata-platform"
NODE2_NAME="dashujuyingyong"
NODE3_NAME="huixuedashuju-PowerEdge-R730xd"

PROJECT_DIR="/opt/huixue-yuanban"
DEPLOY_DIR="${PROJECT_DIR}/deploy"
SCRIPTS_DIR="${DEPLOY_DIR}/scripts"
CONFIG_DIR="${DEPLOY_DIR}/config"

# 获取本机 IP
MY_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "未知")

banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║       慧学 一键部署脚本                          ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo_info "管理节点: ${MANAGER_IP} (${NODE1_NAME})"
    echo_info "本机 IP:  ${MY_IP}"
    echo ""
}

# 检查 Docker
check_docker() {
    echo_info "检查 Docker..."
    if ! command -v docker &> /dev/null; then
        echo_fail "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "未运行")
    echo_ok "Docker 版本: ${DOCKER_VERSION}"

    # 检查是否是管理节点
    if [ "$MY_IP" = "$MANAGER_IP" ]; then
        echo_ok "当前节点是管理节点"
        return 0
    else
        echo_warn "当前节点不是管理节点，某些功能不可用"
        return 1
    fi
}

# 初始化集群
init_cluster() {
    banner
    echo_info "=== 步骤 1: 初始化 Docker Swarm 集群 ==="
    echo ""

    if [ "$MY_IP" != "$MANAGER_IP" ]; then
        echo_fail "请在管理节点 (${MANAGER_IP}) 上执行此操作"
        exit 1
    fi

    # 检查是否已经是 Swarm 节点
    SWARM_STATE=$(docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null || echo "unknown")
    if [ "$SWARM_STATE" = "active" ]; then
        echo_ok "Swarm 集群已初始化"
        echo_info "节点状态："
        docker node ls
        return 0
    fi

    # 初始化 Swarm
    echo_info "初始化 Swarm..."
    docker swarm init --advertise-addr ${MANAGER_IP}

    # 获取 token
    WORKER_TOKEN=$(docker swarm join-token worker -q)

    echo ""
    echo_info "Swarm 初始化成功！"
    echo ""
    echo "=== 节点加入命令 ==="
    echo ""
    echo "节点二 (${NODE2_IP}):"
    echo "  docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377"
    echo ""
    echo "节点三 (${NODE3_IP}):"
    echo "  docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377"
    echo ""

    # 自动加入节点二
    echo_info "尝试将节点二加入集群..."
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@${NODE2_IP} \
        "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377" 2>/dev/null
    sleep 2

    # 自动加入节点三
    echo_info "尝试将节点三加入集群..."
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@${NODE3_IP} \
        "docker swarm join --token ${WORKER_TOKEN} ${MANAGER_IP}:2377" 2>/dev/null
    sleep 2

    # 配置节点标签
    echo_info "配置节点标签..."
    docker node update --label-add storage=true --label-add db=true ${NODE1_NAME}
    docker node update --label-add compute=true --label-add backend=true ${NODE2_NAME}
    docker node update --label-add frontend=true --label-add manager=true ${NODE3_NAME}

    echo ""
    echo_ok "集群初始化完成！"
    echo ""
    echo_info "节点状态："
    docker node ls
}

# 构建镜像
build_images() {
    banner
    echo_info "=== 步骤 2: 构建并推送镜像 ==="
    echo ""

    if [ "$MY_IP" != "$MANAGER_IP" ]; then
        echo_fail "请在管理节点上执行"
        exit 1
    fi

    cd ${PROJECT_DIR}

    REGISTRY="${MANAGER_IP}:5000"

    # 启动本地镜像仓库
    echo_info "启动镜像仓库..."
    if ! docker ps --format '{{.Names}}' | grep -q "^registry$"; then
        docker rm -f registry 2>/dev/null || true
        docker run -d --name registry \
            --restart=always \
            -p 5000:5000 \
            -v registry-data:/var/lib/registry \
            registry:2
        echo_ok "镜像仓库已启动"
    else
        echo_ok "镜像仓库已在运行"
    fi

    sleep 2

    # 构建后端
    echo_info "构建后端镜像..."
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

    echo ""
    echo_ok "所有镜像构建并推送完成！"
}

# 部署服务
deploy() {
    banner
    echo_info "=== 步骤 3: 部署服务 ==="
    echo ""

    if [ "$MY_IP" != "$MANAGER_IP" ]; then
        echo_fail "请在管理节点上执行"
        exit 1
    fi

    cd ${CONFIG_DIR}

    # 设置环境变量
    export REGISTRY_URL="${MANAGER_IP}:5000"
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-huixue123}
    export JUPYTER_TOKEN=${JUPYTER_TOKEN:-huixue_token}
    export SECRET_KEY=${SECRET_KEY:-huixue-secret-key-change-in-production}
    # 授权配置（Gitee 方案）
    export LICENSE_URL="${LICENSE_URL:-https://gitee.com/noderead/huixuejson/raw/master/license.json}"
    export LICENSE_TOKEN="${LICENSE_TOKEN:-60e1ef7adc97e693caca52beacd24b57}"
    export LICENSE_CHECK_INTERVAL=604800

    # 部署
    echo_info "部署服务到集群..."
    docker stack deploy -c docker-stack.yml huixue

    echo ""
    echo_ok "服务部署完成！"
    echo ""
    echo_info "服务状态："
    docker stack services huixue
}

# 查看状态
status() {
    banner
    echo_info "=== 服务状态 ==="
    echo ""

    if docker stack services huixue &>/dev/null; then
        docker stack services huixue
    else
        echo_warn "服务未部署或已停止"
    fi

    echo ""
    echo_info "节点状态："
    docker node ls 2>/dev/null || echo_warn "无法获取节点状态"

    echo ""
    echo "=== 访问地址 ==="
    echo "  Web前端: http://${NODE3_IP}:3000"
    echo "  Jupyter: http://${NODE2_IP}:8888"
    echo "  API:     http://${NODE2_IP}:8000/docs"
    echo "  VDI:     http://${NODE3_IP}:6080"
}

# 查看日志
logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        echo_info "查看所有服务日志..."
        docker stack logs huixue 2>&1 | tail -100
    else
        echo_info "查看服务 ${SERVICE} 日志..."
        docker service logs huixue_${SERVICE} 2>&1 | tail -50
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
    echo_info "停止所有服务..."
    docker stack rm huixue
    echo_ok "服务已停止"
}

# 一键完整部署
start() {
    banner
    echo_info "=== 开始完整部署 ==="
    echo ""

    check_docker || exit 1
    echo ""

    read -p "确认开始部署? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已取消"
        exit 0
    fi

    init_cluster
    echo ""

    read -p "继续构建镜像? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已跳过构建"
    else
        build_images
        echo ""
    fi

    read -p "继续部署服务? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "已跳过部署"
    else
        deploy
    fi

    echo ""
    echo_ok "部署完成！"
    status
}

# 帮助
help() {
    banner
    echo "用法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  init        初始化 Docker Swarm 集群"
    echo "  build       构建并推送镜像"
    echo "  deploy      部署服务"
    echo "  start       完整部署（初始化+构建+部署）"
    echo "  status      查看服务状态"
    echo "  logs [服务] 查看日志"
    echo "  restart     重启服务"
    echo "  stop        停止服务"
    echo ""
    echo "节点配置:"
    echo "  管理节点: ${MANAGER_IP} (${NODE1_NAME}) - DB, Redis, Registry"
    echo "  计算节点: ${NODE2_IP} (${NODE2_NAME}) - Backend, Jupyter"
    echo "  Web节点:  ${NODE3_IP} (${NODE3_NAME}) - Frontend, VDI"
    echo ""
}

# 主函数
main() {
    COMMAND=${1:-help}

    case $COMMAND in
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
            start
            ;;
        status)
            status
            ;;
        logs)
            logs $2
            ;;
        restart)
            restart $2
            ;;
        stop)
            stop
            ;;
        help|--help|-h)
            help
            ;;
        *)
            echo_fail "未知命令: $COMMAND"
            help
            exit 1
            ;;
    esac
}

main "$@"
