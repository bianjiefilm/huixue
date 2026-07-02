# =============================================================================
# 构建阶段：安装依赖并构建前端
# =============================================================================
FROM node:18-alpine AS builder

# 使用阿里云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app

# 增加 Node.js 内存限制，跳过 puppeteer 下载 Chromium
ENV NODE_OPTIONS="--max-old-space-size=4096" \
    npm_config_registry=https://registry.npmmirror.com \
    PUPPETEER_SKIP_DOWNLOAD=true \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci --prefer-offline --no-audit || npm install --prefer-offline --no-audit

# 复制源代码（排除 .git、node_modules 等）
COPY . .

# 构建应用
RUN npm run build

# =============================================================================
# 生产阶段：最小化 Nginx 镜像
# =============================================================================
FROM nginx:alpine

# 使用阿里云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 预创建所有需要的目录（777 权限确保可写）
RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp \
    /var/run \
    && chmod -R 777 /var/cache/nginx /var/run

# 移除 nginx 默认页面和日志
RUN rm -rf /usr/share/nginx/html/* \
    /var/log/nginx/* \
    /etc/nginx/conf.d/default.conf

# 以 root 身份运行
USER root

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制自定义启动脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 确保静态文件权限正确
RUN chmod -R 644 /usr/share/nginx/html/* \
    && find /usr/share/nginx/html -type d -exec chmod 755 {} \;

# 暴露端口
EXPOSE 80

# 使用自定义启动脚本
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
