#!/bin/bash
# tests/l0/run_all.sh
# L0 - 运行全部基础设施健康检查

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMEOUT="${TIMEOUT:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 颜色定义（用于汇总）
CHECK_PASSED='\033[0;32m'
CHECK_FAILED='\033[0;31m'
CHECK_SKIPPED='\033[1;33m'
CHECK_NONE='\033[0m'

# 检查结果
declare -A results

run_check() {
    local name="$1"
    local script="$2"

    echo ""
    echo ">>> 运行: $name"
    echo "----------------------------------------"

    if [ ! -f "$script" ]; then
        log_warn "脚本不存在: $script，跳过"
        results["$name"]="SKIPPED"
        return
    fi

    if "$script"; then
        results["$name"]="PASSED"
        echo -e "${CHECK_PASSED}[PASS]${NC} $name"
    else
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            results["$name"]="PASSED"
            echo -e "${CHECK_PASSED}[PASS]${NC} $name"
        elif [ $exit_code -eq 2 ]; then
            results["$name"]="SKIPPED"
            echo -e "${CHECK_SKIPPED}[SKIP]${NC} $name (需要配置)"
        else
            results["$name"]="FAILED"
            echo -e "${CHECK_FAILED}[FAIL]${NC} $name"
        fi
    fi
}

print_summary() {
    echo ""
    echo "========================================"
    echo " L0 基础设施检查汇总"
    echo "========================================"

    local total=0
    local passed=0
    local failed=0
    local skipped=0

    for name in "${!results[@]}"; do
        total=$((total + 1))
        case "${results[$name]}" in
            PASSED)  passed=$((passed + 1)) ;;
            FAILED)  failed=$((failed + 1)) ;;
            SKIPPED) skipped=$((skipped + 1)) ;;
        esac
    done

    echo ""
    echo -e "  ${CHECK_PASSED}PASSED:  $passed${NC}"
    echo -e "  ${CHECK_FAILED}FAILED:  $failed${NC}"
    echo -e "  ${CHECK_SKIPPED}SKIPPED: $skipped${NC}"
    echo -e "  总计:     $total"
    echo "========================================"

    if [ $failed -gt 0 ]; then
        log_error "有 $failed 项检查失败"
        return 1
    elif [ $passed -gt 0 ]; then
        log_info "所有检查通过！"
        return 0
    else
        log_warn "所有检查均被跳过"
        return 2
    fi
}

main() {
    echo "========================================"
    echo " 慧学云平台 - L0 基础设施健康检查"
    echo "========================================"
    echo ""
    echo "  检查目标: ${API_HOST:-<慧学服务器1-IP>}"
    echo "  超时设置: ${TIMEOUT}s"
    echo ""

    # 确保脚本可执行
    chmod +x "$SCRIPT_DIR"/*.sh 2>/dev/null || true

    # 运行各项检查
    run_check "Docker 服务"   "$SCRIPT_DIR/check_docker.sh"
    run_check "PostgreSQL"   "$SCRIPT_DIR/check_postgres.sh"
    run_check "Redis"        "$SCRIPT_DIR/check_redis.sh"
    run_check "NFS 存储"     "$SCRIPT_DIR/check_nfs.sh"

    # 打印汇总
    print_summary
}

main "$@"
