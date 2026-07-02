#!/bin/bash
# tests/l0/check_redis.sh
# L0 - Redis 缓存服务健康检查

set -e

REDIS_HOST="${REDIS_HOST:-<慧学服务器1-IP>}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
TIMEOUT="${TIMEOUT:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 redis-cli 客户端
check_redis_cli() {
    if ! command -v redis-cli &> /dev/null; then
        log_warn "redis-cli 客户端未安装，尝试其他方式"
        return 1
    fi
    return 0
}

# 构建 redis-cli 命令
redis_cmd() {
    local cmd="redis-cli -h $REDIS_HOST -p $REDIS_PORT"
    if [ -n "$REDIS_PASSWORD" ]; then
        cmd="$cmd -a $REDIS_PASSWORD"
    fi
    echo "$cmd"
}

# 通过 redis-cli 检查
check_via_cli() {
    log_info "使用 redis-cli 检查 Redis..."

    local rc
    rc=$(redis_cmd)
    local result

    result=$(echo "PING" | $rc --no-auth-warning 2>&1) || {
        log_error "redis-cli 连接失败: $result"
        return 1
    }

    if echo "$result" | grep -qi "PONG\|connected"; then
        log_info "Redis 连接正常: $result"
        return 0
    else
        log_error "Redis PING 失败: $result"
        return 1
    fi
}

# 通过 docker exec 检查
check_via_docker() {
    log_info "使用 docker exec 检查 Redis..."

    local container
    container=$(docker ps --format "{{.Names}}" | grep -i redis | head -1 || echo "")

    if [ -z "$container" ]; then
        log_warn "未找到 Redis 容器"
        return 1
    fi

    log_info "找到容器: $container"

    local result
    result=$(docker exec "$container" redis-cli PING 2>&1) || {
        log_error "docker exec redis-cli 失败: $result"
        return 1
    }

    if echo "$result" | grep -q "PONG"; then
        log_info "Redis 连接正常"
        return 0
    else
        log_error "Redis PING 失败: $result"
        return 1
    fi
}

# 通过 nc/telnet 检查
check_via_tcp() {
    log_info "使用 TCP 连接检查 Redis..."

    if command -v nc &> /dev/null; then
        local result
        result=$(echo "PING\r\nQUIT\r\n" | nc -w "$TIMEOUT" "$REDIS_HOST" "$REDIS_PORT" 2>&1) || {
            log_error "nc 连接失败: $result"
            return 1
        }

        if echo "$result" | grep -q "PONG"; then
            log_info "Redis TCP 连接正常"
            return 0
        else
            log_error "Redis TCP 响应异常: $result"
            return 1
        fi
    elif command -v timeout &> /dev/null; then
        # 使用 bash /dev/tcp
        local result
        result=$(timeout "$TIMEOUT" bash -c \
            "exec 3<>/dev/tcp/$REDIS_HOST/$REDIS_PORT && \
             echo -e 'PING\r\nQUIT\r\n' >&3 && \
             cat <&3" 2>&1) || {
            log_error "TCP 连接失败: $result"
            return 1
        }

        if echo "$result" | grep -q "PONG"; then
            log_info "Redis TCP 连接正常"
            return 0
        fi
    fi

    log_error "无法找到 nc 或 timeout 工具"
    return 1
}

# 获取 Redis 信息
get_redis_info() {
    log_info "获取 Redis 信息..."

    if check_redis_cli; then
        local rc
        rc=$(redis_cmd)

        local info
        info=$(echo "INFO" | $rc --no-auth-warning 2>&1 | head -30) || {
            log_warn "无法获取 Redis INFO: $info"
            return 0
        }

        echo "$info" | grep -E "^#|redis_version|used_memory_human|connected_clients|uptime_in_days" | head -10
    fi
}

# 检查键数量
check_keys() {
    log_info "检查 Redis 键数量..."

    if check_redis_cli; then
        local rc
        rc=$(redis_cmd)

        local count
        count=$(echo "DBSIZE" | $rc --no-auth-warning 2>&1 | grep -E "^[0-9]+" || echo "0") || {
            log_warn "无法获取键数量"
            return 0
        }

        log_info "当前键数量: $count"
    fi
}

# 主流程
main() {
    echo "========================================"
    echo " L0 - Redis 缓存服务健康检查"
    echo "========================================"
    echo ""
    echo "  Host: $REDIS_HOST:$REDIS_PORT"
    echo ""

    local exit_code=0

    # 尝试多种连接方式
    if check_redis_cli; then
        check_via_cli || exit_code=$?
    fi

    if [ $exit_code -ne 0 ]; then
        check_via_docker || check_via_tcp || exit_code=$?
    fi

    if [ $exit_code -eq 0 ]; then
        echo ""
        get_redis_info || log_warn "INFO 检查跳过"
        echo ""
        check_keys || log_warn "键检查跳过"
    fi

    echo ""
    echo "========================================"
    if [ $exit_code -eq 0 ]; then
        log_info "Redis 健康检查通过"
    else
        log_error "Redis 健康检查失败"
    fi
    echo "========================================"

    exit $exit_code
}

main "$@"
