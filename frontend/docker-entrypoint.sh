#!/bin/sh
# 自定义 nginx 启动脚本
# 解决 /var/cache/nginx 权限问题

# 预先创建所有缓存目录
mkdir -p /var/cache/nginx/client_temp
mkdir -p /var/cache/nginx/proxy_temp
mkdir -p /var/cache/nginx/fastcgi_temp
mkdir -p /var/cache/nginx/uwsgi_temp
mkdir -p /var/cache/nginx/scgi_temp
mkdir -p /var/run

# 设置权限为 777
chmod -R 777 /var/cache/nginx /var/run

# 直接启动 nginx（不使用递归调用）
exec nginx -g "daemon off;"
