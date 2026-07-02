# =============================================================================
# 慧学高校大数据平台 - Jupyter 实训环境 (简化版)
# =============================================================================
# 使用更小的基础镜像，只安装必要的包
# =============================================================================

FROM python:3.9-slim

LABEL maintainer="Huixue Platform <admin@huixue.edu>"
LABEL description="Lightweight Jupyter environment for Huixue Platform"

WORKDIR /home/jovyan/work

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 中文字体
    fonts-wqy-zenhei \
    # 常用工具
    vim \
    curl \
    wget \
    git \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 包
RUN pip install --no-cache-dir \
    notebook \
    jupyterlab \
    numpy \
    pandas \
    matplotlib \
    seaborn \
    scikit-learn \
    jieba \
    openpyxl \
    lxml \
    requests \
    beautifulsoup4 \
    && pip cache purge

# 刷新字体缓存
RUN fc-cache -fv

# 配置 Matplotlib 使用中文字体
RUN mkdir -p /home/jovyan/.config/matplotlib && \
    echo "font.sans-serif: WenQuanYi Zen Hei, WenQuanYi Micro Hei, Noto Sans CJK SC, DejaVu Sans" > /home/jovyan/.config/matplotlib/matplotlibrc && \
    echo "axes.unicode_minus: False" >> /home/jovyan/.config/matplotlib/matplotlibrc

# 创建jovyan用户（后端初始化需要）
RUN groupadd -g 1000 jovyan && useradd -u 1000 -g 1000 -m -s /bin/bash jovyan

# 设置工作目录权限
RUN chown -R jovyan:jovyan /home/jovyan

EXPOSE 8888

USER jovyan

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--NotebookApp.token=huixue_token", "--allow-root"]
