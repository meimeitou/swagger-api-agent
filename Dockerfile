# Multi-stage build Dockerfile for Swagger API Agent
# 使用多阶段构建优化镜像大小

# 第一阶段：构建阶段
FROM python:3.11-slim-bookworm as builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
ENV POETRY_HOME="/opt/poetry"
ENV POETRY_CACHE_DIR="/opt/poetry/cache"
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VERSION=1.7.1

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# 复制项目配置文件
COPY pyproject.toml poetry.lock* ./

# 创建 requirements.txt 用于生产环境
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --only=main

# 第二阶段：运行时镜像
FROM python:3.11-slim-bookworm as runtime

# 设置非root用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 复制 requirements.txt 并安装依赖
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/
COPY examples/ ./examples/
COPY scripts/ ./scripts/
COPY README.md LICENSE pyproject.toml ./

# 安装项目本身
RUN pip install --no-cache-dir -e .

# 设置环境变量
ENV PYTHONPATH="/app/src:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 复制环境变量模板
COPY .env.example .env.example

# 复制启动脚本
COPY scripts/entrypoint.sh /app/entrypoint.sh

# 创建必要的目录
RUN mkdir -p /app/logs /app/data

# 设置文件权限
RUN chown -R appuser:appuser /app && \
    chmod +x /app/entrypoint.sh

USER appuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 暴露端口
EXPOSE 5000 8080

# 设置默认环境变量
ENV OPENAPI_FILE=/app/examples/example_openapi.yaml
ENV FLASK_ENV=production
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV MOCK_HOST=0.0.0.0
ENV MOCK_PORT=8080

# 设置入口点
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["cli"]
