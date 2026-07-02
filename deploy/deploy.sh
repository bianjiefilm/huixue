#!/bin/bash
# =============================================================================
# 慧学平台 — 部署脚本
# =============================================================================
# 用法: bash deploy/deploy.sh
#
# 部署架构:
#   #1 (.42) 数据节点: PostgreSQL + Redis + 资源文件 (NFS Server)
#   #2 (.43) 计算节点: Jupyter/BI 容器运行
#   #3 (.41) Web 节点:  后端(FastAPI) + 前端(Nginx)
#
# 前提:
#   - Mac 已配置 SSH 免密到三台服务器 (<慧学运维账号>)
#   - 三台服务器已安装 Docker + Docker Compose
# =============================================================================

set -euo pipefail

# === 配置 ===
# Tailscale IPs (校园内网不通时使用)
NODE1="<慧学运维账号>@<慧学服务器1-IP>"    # 数据节点 (#1 bigdata-platform)
NODE2="<慧学运维账号>@<慧学服务器2-IP>"   # 计算节点 (#2 dashujuyingyong)
NODE3="<慧学运维账号>@<慧学服务器3-IP>"     # Web 节点  (#3 huixuedashuju)

REMOTE_DIR="/opt/huixue-yuanban"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# 排除不需要上传的目录
EXCLUDES=(
  --exclude='.git'
  --exclude='node_modules'
  --exclude='__pycache__'
  --exclude='.venv'
  --exclude='*.pyc'
  --exclude='.DS_Store'
  --exclude='_temp_gstack'
  --exclude='test-evidence'
  --exclude='*.png'
  --exclude='*.mjs'
  --exclude='huixue_local.db'
  --exclude='ziyuan_normalized'
  # 课程资源通过 NFS 挂载，不随代码同步
  --exclude='backend/static/resources/'
)

echo "╔══════════════════════════════════════════╗"
echo "║       慧学平台 — 三节点部署              ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "项目目录: $PROJECT_ROOT"
echo ""

# =============================================================================
# 检查 PostgreSQL 连通性（通过已建立的 SSH 隧道）
# =============================================================================
check_pg_tunnel() {
    local TUNNEL_PORT=${1:-15432}
    echo -n "  [pre-flight] PostgreSQL 隧道检查 (localhost:$TUNNEL_PORT)... "
    if nc -z -w 5 localhost $TUNNEL_PORT 2>/dev/null; then
        echo "✅"
        return 0
    else
        echo "❌ 隧道未就绪或 PostgreSQL 未监听"
        return 1
    fi
}

# =============================================================================
# cmd_migrate: 仅执行迁移（独立命令）
# =============================================================================
cmd_migrate() {
    echo "▶ 阶段 2b: 迁移 SQLite → PostgreSQL"
    echo "  建立 SSH 隧道到 #1 PostgreSQL..."
    ssh -f -N -L 15432:localhost:5432 $NODE1
    sleep 1

    if ! check_pg_tunnel 15432; then
        echo "❌ PostgreSQL 隧道不可达，终止迁移"
        pkill -f "ssh.*15432:localhost:5432" 2>/dev/null || true
        exit 1
    fi

    DATABASE_URL="postgresql://huixue:huixue123@localhost:15432/huixue" \
      python3 "$PROJECT_ROOT/deploy/scripts/migrate_sqlite_to_pg.py"

    pkill -f "ssh.*15432:localhost:5432" 2>/dev/null || true

    echo ""
    echo "▶ L1 验证: 数据节点"
    ssh $NODE1 'bash -s' < "$PROJECT_ROOT/deploy/tests/L1_node1_data.sh" || {
        echo "⛔ L1 #1 失败"; exit 1
    }
    echo "✅ 迁移完成"
}

# =============================================================================
# cmd_start: 完整三节点部署
# =============================================================================
cmd_start() {

# =============================================================================
# 阶段 1: 同步代码到各节点
# =============================================================================
echo "▶ 阶段 1: 同步代码"

echo -n "  [1/3] 同步到 #1 数据节点 (.42)... "
ssh $NODE1 "sudo mkdir -p $REMOTE_DIR && sudo chown <慧学运维账号>:<慧学运维账号> $REMOTE_DIR"
rsync -az --delete "${EXCLUDES[@]}" \
  --exclude='ziyuan_data/' \
  "$PROJECT_ROOT/" "$NODE1:$REMOTE_DIR/" 2>/dev/null
echo "✅"

echo -n "  [2/3] 同步到 #2 计算节点 (.43)... "
ssh $NODE2 "sudo mkdir -p $REMOTE_DIR && sudo chown <慧学运维账号>:<慧学运维账号> $REMOTE_DIR"
rsync -az --delete "${EXCLUDES[@]}" \
  --exclude='ziyuan_data/' \
  "$PROJECT_ROOT/" "$NODE2:$REMOTE_DIR/" 2>/dev/null
echo "✅ (不含资源文件，用 NFS)"

echo -n "  [3/3] 同步到 #3 Web 节点 (.41)... "
ssh $NODE3 "sudo mkdir -p $REMOTE_DIR && sudo chown <慧学运维账号>:<慧学运维账号> $REMOTE_DIR"
rsync -az --delete "${EXCLUDES[@]}" \
  --exclude='ziyuan_data/' \
  "$PROJECT_ROOT/" "$NODE3:$REMOTE_DIR/" 2>/dev/null
echo "✅"

# =============================================================================
# 阶段 2: 部署 #1 数据节点 — PostgreSQL + Redis + NFS
# =============================================================================
echo ""
echo "▶ 阶段 2: 部署 #1 数据节点 (.42)"

ssh $NODE1 << 'EOF'
set -e
cd /opt/huixue-yuanban

# 资源文件目录
sudo mkdir -p /data/huixue_storage/ziyuan_data
# 如果 ziyuan_data 在项目里，软链或复制
if [ -d "ziyuan_data" ] && [ ! -L "/data/huixue_storage/ziyuan_data" ]; then
  sudo rsync -a ziyuan_data/ /data/huixue_storage/ziyuan_data/
fi
if [ -d "backend/static/resources" ]; then
  sudo rsync -a backend/static/resources/ /data/huixue_storage/ziyuan_data/
fi

# 启动 PostgreSQL + Redis
docker compose up -d db redis

# 等待 PostgreSQL 就绪
echo -n "  等待 PostgreSQL 就绪..."
for i in $(seq 1 30); do
  if docker compose exec -T db pg_isready -U huixue &>/dev/null; then
    echo " ✅"
    break
  fi
  sleep 1
  echo -n "."
done

echo "  #1 数据节点部署完成"
EOF

echo "  ✅ #1 数据节点就绪"

# 迁移 SQLite → PostgreSQL (从 Mac 本地执行，通过 SSH 隧道连 #1 的 PG)
echo ""
echo "▶ 阶段 2b: 迁移 SQLite → PostgreSQL"
echo "  建立 SSH 隧道到 #1 PostgreSQL..."
ssh -f -N -L 15432:localhost:5432 $NODE1
sleep 1

# 前置检查：隧道是否就绪
if ! check_pg_tunnel 15432; then
    echo_error "  PostgreSQL 隧道不可达，终止迁移"
    pkill -f "ssh.*15432:localhost:5432" 2>/dev/null || true
    exit 1
fi

DATABASE_URL="postgresql://huixue:huixue123@localhost:15432/huixue" \
  python3 "$PROJECT_ROOT/deploy/scripts/migrate_sqlite_to_pg.py"

# 关闭隧道
pkill -f "ssh.*15432:localhost:5432" 2>/dev/null || true

# 运行 L1 验证
echo ""
echo "▶ L1 验证: 数据节点"
ssh $NODE1 'bash -s' < "$PROJECT_ROOT/deploy/tests/L1_node1_data.sh" || {
  echo "⛔ L1 #1 失败，停止部署"; exit 1
}

# =============================================================================
# 阶段 3: 部署 #2 计算节点 — NFS 挂载 + Docker
# =============================================================================
echo ""
echo "▶ 阶段 3: 部署 #2 计算节点 (.43)"

ssh $NODE2 << 'EOF'
set -e

# 挂载 NFS
sudo mkdir -p /mnt/huixue_data
if ! mount | grep -q "<慧学内网IP-1>"; then
  sudo mount -t nfs <慧学内网IP-1>:/data/huixue_storage/ziyuan_data /mnt/huixue_data
  # 写入 fstab 持久化
  grep -q "<慧学内网IP-1>" /etc/fstab || \
    echo "<慧学内网IP-1>:/data/huixue_storage/ziyuan_data /mnt/huixue_data nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
fi

# 构建/拉取 Jupyter 镜像
cd /opt/huixue-yuanban
if [ -f jupyter/Dockerfile ]; then
  docker build -t huixue-jupyter:latest jupyter/
fi

echo "  #2 计算节点部署完成"
EOF

echo "  ✅ #2 计算节点就绪"

echo ""
echo "▶ L1 验证: 计算节点"
ssh $NODE2 'bash -s' < "$PROJECT_ROOT/deploy/tests/L1_node2_compute.sh" || {
  echo "⛔ L1 #2 失败，停止部署"; exit 1
}

# =============================================================================
# 阶段 4: 部署 #3 Web 节点 — 后端 + 前端
# =============================================================================
echo ""
echo "▶ 阶段 4: 部署 #3 Web 节点 (.41)"

ssh $NODE3 << 'WEBEOF'
set -e
cd /opt/huixue-yuanban

# NFS 挂载资源目录
sudo mkdir -p /mnt/huixue_data
if ! mount | grep -q "<慧学内网IP-1>"; then
  sudo mount -t nfs <慧学内网IP-1>:/data/huixue_storage/ziyuan_data /mnt/huixue_data
  grep -q "<慧学内网IP-1>" /etc/fstab || \
    echo "<慧学内网IP-1>:/data/huixue_storage/ziyuan_data /mnt/huixue_data nfs defaults,_netdev 0 0" | sudo tee -a /etc/fstab
fi

# 创建 .env 指向 #1 的数据库
cat > .env << 'ENVEOF'
# Database (#1 数据节点)
POSTGRES_DB=huixue
POSTGRES_USER=huixue
POSTGRES_PASSWORD=huixue123
DATABASE_URL=postgresql://huixue:huixue123@<慧学内网IP-1>:5432/huixue

# Redis (#1 数据节点)
REDIS_HOST=<慧学内网IP-1>
REDIS_PORT=6379

# 资源目录 (NFS 挂载)
HUIXUE_RESOURCE_DIR=/mnt/huixue_data

# Docker (#2 计算节点)
DOCKER_HOST=ssh://<慧学运维账号>@<慧学内网IP-2>

# JWT
SECRET_KEY=huixue_production_secret_key_2026

# 其他
BI_PROXY_ENABLED=true
BI_PARENT_ORIGIN=http://<慧学内网IP-3>:3000
JUPYTER_BASE_URL=http://<慧学内网IP-2>
ENVEOF

# 构建后端镜像
docker build -t huixue-backend:latest -f backend/Dockerfile backend/

# 构建前端镜像
docker build -t huixue-frontend:latest -f frontend/Dockerfile frontend/

# 启动后端 + 前端（不启动 db/redis，它们在 #1）
docker compose up -d backend frontend

echo "  #3 Web 节点部署完成"
WEBEOF

echo "  ✅ #3 Web 节点就绪"

echo ""
echo "▶ L1 验证: Web 节点"
ssh $NODE3 'bash -s' < "$PROJECT_ROOT/deploy/tests/L1_node3_web.sh" || {
  echo "⛔ L1 #3 失败，停止部署"; exit 1
}

# =============================================================================
# 阶段 5: L2 + L3 验证
# =============================================================================
echo ""
echo "▶ L2 验证: 节点间通信"
ssh $NODE3 'bash -s' < "$PROJECT_ROOT/deploy/tests/L2_inter_node.sh" || {
  echo "⛔ L2 失败"; exit 1
}

echo ""
echo "▶ L3 验证: 服务集成"
ssh $NODE3 'bash -s' < "$PROJECT_ROOT/deploy/tests/L3_service_integration.sh" || {
  echo "⛔ L3 失败"; exit 1
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅ 部署完成！L1-L3 全部通过            ║"
echo "║                                          ║"
echo "║   平台地址: http://<慧学内网IP-3>:3000    ║"
echo "║   后端 API: http://<慧学内网IP-3>:8000    ║"
echo "║                                          ║"
echo "║   请进入 L4 浏览器冒烟测试               ║"
echo "╚══════════════════════════════════════════╝"
}

# === 命令分发 ===
case "${1:-start}" in
    migrate)
        cmd_migrate; exit $?
        ;;
    start|"")
        cmd_start
        ;;
    *)
        echo "用法: $0 {start|migrate}"
        exit 1
        ;;
esac
