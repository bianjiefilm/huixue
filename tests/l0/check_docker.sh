#!/bin/bash
# tests/l0/check_docker.sh
# L0 - Docker 服务健康检查

set -e

API_HOST="${API_HOST:-<慧学服务器1-IP>}"
API_PORT="${API_PORT:-8000}"
TIMEOUT="${TIMEOUT:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 Docker 服务是否运行
check_docker_running() {
    log_info "检查 Docker 服务状态..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行或权限不足"
        exit 1
    fi

    log_info "Docker 服务运行正常"
}

# 检查容器状态
check_containers() {
    log_info "检查应用容器状态..."

    # 列出关键容器
    local containers=$(docker ps --format "{{.Names}}:{{.Status}}" 2>/dev/null || echo "")

    if [ -z "$containers" ]; then
        log_warn "未发现运行中的容器（可能使用 docker-compose 以外的方式部署）"
        return 0
    fi

    echo "$containers"

    # 检查是否包含关键服务
    local key_services=("backend" "frontend" "postgres" "redis" "nginx")
    for service in "${key_services[@]}"; do
        if echo "$containers" | grep -q "$service"; then
            log_info "  - $service: 运行中"
        fi
    done
}

# 检查容器健康状态
check_container_health() {
    log_info "检查容器健康状态..."

    local unhealthy=$(docker ps --filter "health=unhealthy" --format "{{.Names}}" 2>/dev/null || echo "")

    if [ -n "$unhealthy" ]; then
        log_error "以下容器健康检查失败:"
        echo "$unhealthy" | while read -r name; do
            echo "  - $name"
            docker logs --tail 20 "$name" 2>&1 | tail -5
        done
        exit 1
    fi

    log_info "所有容器健康状态正常"
}

# 检查 API 服务响应
check_api_endpoint() {
    log_info "检查 API 服务端点响应..."

    local url="http://${API_HOST}:${API_PORT}/api/login"
    local response
    local http_code

    response=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout "$TIMEOUT" \
        --max-time "$TIMEOUT" \
        "$url" 2>/dev/null || echo "000")

    if [ "$http_code" = "000" ]; then
        log_error "API 服务无响应 ($url)"
        return 1
    elif [ "$http_code" -ge 200 ] && [ "$http_code" -lt 500 ]; then
        log_info "API 服务响应正常 (HTTP $http_code)"
        return 0
    else
        log_error "API 服务返回异常状态 (HTTP $http_code)"
        return 1
    fi
}

# 主流程
main() {
    echo "========================================"
    echo " L0 - Docker 服务健康检查"
    echo "========================================"
    echo ""

    local exit_code=0

    check_docker_running || exit_code=$?
    if [ $exit_code -ne 0 ]; then exit $exit_code; fi

    echo ""
    check_containers || log_warn "容器检查跳过"

    echo ""
    check_container_health || log_warn "健康检查跳过（可能容器未配置健康检查）"

    echo ""
    check_api_endpoint || exit_code=$?

    echo ""
    echo "========================================"
    if [ $exit_code -eq 0 ]; then
        log_info "Docker 健康检查全部通过"
    else
        log_error "Docker 健康检查发现问题"
    fi
    echo "========================================"

    exit $exit_code
}

main "$@"
