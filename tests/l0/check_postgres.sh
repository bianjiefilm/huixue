#!/bin/bash
# tests/l0/check_postgres.sh
# L0 - PostgreSQL 数据库健康检查

set -e

POSTGRES_HOST="${POSTGRES_HOST:-<慧学服务器1-IP>}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-huixue}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
TIMEOUT="${TIMEOUT:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 psql 客户端
check_psql_client() {
    if ! command -v psql &> /dev/null; then
        log_warn "psql 客户端未安装，尝试使用 docker exec"
        return 1
    fi
    return 0
}

# 通过 psql 检查
check_via_psql() {
    log_info "使用 psql 检查 PostgreSQL..."

    export PGPASSWORD="$POSTGRES_PASSWORD"

    local query="SELECT 1 AS alive, version() AS version, current_database() AS db;"

    local result
    result=$(psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "$query" \
        -t \
        --connect-timeout "$TIMEOUT" \
        2>&1) || {
            log_error "psql 连接失败: $result"
            return 1
        }

    if echo "$result" | grep -q "alive"; then
        log_info "PostgreSQL 连接正常"
        echo "$result" | head -3
        return 0
    else
        log_error "PostgreSQL 查询失败: $result"
        return 1
    fi
}

# 通过 docker exec 检查
check_via_docker() {
    log_info "使用 docker exec 检查 PostgreSQL..."

    # 查找 postgres 容器
    local container
    container=$(docker ps --format "{{.Names}}" | grep -i postgres | head -1 || echo "")

    if [ -z "$container" ]; then
        log_warn "未找到 PostgreSQL 容器"
        return 1
    fi

    log_info "找到容器: $container"

    local result
    result=$(docker exec "$container" psql \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "SELECT 1 AS alive;" \
        -t 2>&1) || {
            log_error "docker exec psql 失败: $result"
            return 1
        }

    if echo "$result" | grep -q "1"; then
        log_info "PostgreSQL 连接正常"
        return 0
    else
        log_error "PostgreSQL 查询失败: $result"
        return 1
    fi
}

# 检查表结构
check_tables() {
    log_info "检查数据库表结构..."

    export PGPASSWORD="$POSTGRES_PASSWORD"

    local tables
    tables=$(psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "\dt" \
        -t 2>&1) || {
            log_warn "无法获取表列表: $tables"
            return 0
        }

    if [ -n "$tables" ]; then
        log_info "数据库表列表:"
        echo "$tables" | head -20
    else
        log_warn "数据库为空或无表"
    fi
}

# 检查连接数
check_connections() {
    log_info "检查数据库连接数..."

    export PGPASSWORD="$POSTGRES_PASSWORD"

    local result
    result=$(psql \
        -h "$POSTGRES_HOST" \
        -p "$POSTGRES_PORT" \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        -c "SELECT count(*) AS connection_count FROM pg_stat_activity;" \
        -t 2>&1) || {
            log_warn "无法获取连接数: $result"
            return 0
        }

    if echo "$result" | grep -qE "^[0-9]+$"; then
        log_info "当前连接数: $(echo $result | tr -d ' ')"
    fi
}

# 主流程
main() {
    echo "========================================"
    echo " L0 - PostgreSQL 数据库健康检查"
    echo "========================================"
    echo ""

    local exit_code=0

    # 尝试 psql 方式
    if check_psql_client; then
        check_via_psql || exit_code=$?
    else
        # 尝试 docker 方式
        check_via_docker || exit_code=$?
    fi

    if [ $exit_code -eq 0 ]; then
        echo ""
        check_tables || log_warn "表检查跳过"
        echo ""
        check_connections || log_warn "连接数检查跳过"
    fi

    echo ""
    echo "========================================"
    if [ $exit_code -eq 0 ]; then
        log_info "PostgreSQL 健康检查通过"
    else
        log_error "PostgreSQL 健康检查失败"
    fi
    echo "========================================"

    exit $exit_code
}

main "$@"
