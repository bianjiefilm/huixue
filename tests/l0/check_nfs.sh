#!/bin/bash
# tests/l0/check_nfs.sh
# L0 - NFS 共享存储健康检查

set -e

NFS_HOST="${NFS_HOST:-<慧学服务器1-IP>}"
NFS_EXPORT="${NFS_EXPORT:-/data}"
MOUNT_POINT="${MOUNT_POINT:-/mnt/nfs}"
TIMEOUT="${TIMEOUT:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 nfs 工具
check_nfs_tools() {
    local tools=("showmount" "mount" "df")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_warn "工具 $tool 未安装"
        fi
    done
}

# 检查 NFS 导出
check_nfs_export() {
    log_info "检查 NFS 导出列表..."

    if ! command -v showmount &> /dev/null; then
        log_warn "showmount 未安装，跳过导出检查"
        return 1
    fi

    local exports
    exports=$(showmount -e "$NFS_HOST" --timeout "$TIMEOUT" 2>&1) || {
        log_warn "无法获取 NFS 导出: $exports"
        return 1
    }

    if [ -n "$exports" ]; then
        log_info "NFS 导出列表:"
        echo "$exports" | head -20
        return 0
    else
        log_warn "NFS 服务器无导出"
        return 1
    fi
}

# 检查 NFS 挂载状态
check_nfs_mount() {
    log_info "检查 NFS 挂载状态..."

    local mount_info
    mount_info=$(mount | grep -E "nfs|$NFS_HOST" 2>/dev/null || echo "")

    if [ -n "$mount_info" ]; then
        log_info "已挂载的 NFS:"
        echo "$mount_info"
    else
        log_warn "未发现已挂载的 NFS"
    fi

    # 检查目标挂载点
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        log_info "NFS 已挂载到 $MOUNT_POINT"

        # 检查读写权限
        local test_file="$MOUNT_POINT/.nfs_check_$(date +%s)"
        if touch "$test_file" 2>/dev/null; then
            rm -f "$test_file"
            log_info "NFS 读写权限正常"
            return 0
        else
            log_error "NFS 读写权限失败"
            return 1
        fi
    else
        log_warn "NFS 未挂载到 $MOUNT_POINT"
        return 1
    fi
}

# 尝试挂载 NFS（用于测试）
try_mount_nfs() {
    log_info "尝试挂载 NFS..."

    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        log_info "NFS 已挂载，跳过挂载步骤"
        return 0
    fi

    # 创建挂载点
    if [ ! -d "$MOUNT_POINT" ]; then
        log_info "创建挂载点: $MOUNT_POINT"
        mkdir -p "$MOUNT_POINT" 2>/dev/null || {
            log_error "无法创建挂载点"
            return 1
        }
    fi

    # 尝试挂载
    local mount_opts="rw,sync,hard,intr,timeo=600,retrans=2"
    if mount -t nfs -o "$mount_opts" "$NFS_HOST:$NFS_EXPORT" "$MOUNT_POINT" 2>&1; then
        log_info "NFS 挂载成功"
        return 0
    else
        log_error "NFS 挂载失败（可能需要 root 权限）"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    if mountpoint -q "$MOUNT_POINT" 2>/dev/null; then
        log_info "NFS 磁盘空间:"
        df -h "$MOUNT_POINT" 2>/dev/null || log_warn "无法获取磁盘空间"
    fi
}

# ping 检查
check_nfs_host() {
    log_info "检查 NFS 主机连通性..."

    if ping -c 1 -W "$TIMEOUT" "$NFS_HOST" &>/dev/null; then
        log_info "NFS 主机 $NFS_HOST 可达"
        return 0
    else
        log_error "NFS 主机 $NFS_HOST 不可达"
        return 1
    fi
}

# 主流程
main() {
    echo "========================================"
    echo " L0 - NFS 共享存储健康检查"
    echo "========================================"
    echo ""
    echo "  NFS Host: $NFS_HOST"
    echo "  NFS Export: $NFS_EXPORT"
    echo "  Mount Point: $MOUNT_POINT"
    echo ""

    local exit_code=0

    check_nfs_tools

    # 首先 ping 检查
    check_nfs_host || exit_code=$?

    if [ $exit_code -eq 0 ]; then
        echo ""
        check_nfs_export || log_warn "导出检查失败"
    fi

    echo ""
    check_nfs_mount || log_warn "挂载检查失败"

    echo ""
    check_disk_space

    echo ""
    echo "========================================"
    if [ $exit_code -eq 0 ]; then
        log_info "NFS 健康检查完成"
    else
        log_error "NFS 健康检查发现问题"
    fi
    echo "========================================"

    exit $exit_code
}

main "$@"
