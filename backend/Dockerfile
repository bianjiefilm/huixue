# =============================================================================
# 构建阶段：安装依赖
# =============================================================================
FROM python:3.9-alpine AS builder

# 使用阿里云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app

# 安装构建依赖
RUN apk add --no-cache gcc g++ musl-dev libpq-dev libmagic tiff-dev poppler-utils tesseract-ocr

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# =============================================================================
# 生产阶段：最小化镜像
# =============================================================================
FROM python:3.9-alpine

# 使用阿里云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app

# 安装运行时依赖
RUN apk add --no-cache libpq libmagic tiff poppler-utils tesseract-ocr

# 从构建阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 复制应用代码
COPY app ./app

# 注意：ziyuan_data 通过 bind mount 挂载，不包含在镜像中

# 创建必要的目录
RUN mkdir -p ziyuan/实训资源/ai_generated \
    ziyuan/实训资源/templates \
    ziyuan/实训资源/datasets \
    ziyuan/实训资源/notebooks \
    ziyuan/实训资源/assets \
    uploads

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/

# 暴露端口
EXPOSE 8000

# 启动命令（生产模式，不使用 --reload）
# 注意：开发时如果需要热重载，可以在运行时添加 --reload 标志
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
