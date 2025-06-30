# Swagger API Agent - Docker 部署指南

本文档介绍如何使用 Docker 部署和运行 Swagger API Agent。

## 📋 目录

- [快速开始](#快速开始)
- [镜像构建](#镜像构建)
- [运行模式](#运行模式)
- [Docker Compose](#docker-compose)
- [环境变量](#环境变量)
- [数据卷](#数据卷)
- [网络配置](#网络配置)
- [故障排除](#故障排除)

## 🚀 快速开始

### 1. 构建镜像

```bash
# 使用便捷脚本
./docker.sh build

# 或者直接使用 Docker
docker build -t swagger-api-agent:latest .
```

### 2. 运行应用

```bash
# CLI 模式
./docker.sh run-cli --api-key YOUR_DEEPSEEK_API_KEY

# Web API 模式
./docker.sh run-web --api-key YOUR_DEEPSEEK_API_KEY --port 5000

# Mock 服务器模式
./docker.sh run-mock --port 8080

# 使用 docker-compose 启动所有服务
export DEEPSEEK_API_KEY=YOUR_API_KEY
./docker.sh compose
```

## 🔨 镜像构建

### 构建选项

```bash
# 基础构建
docker build -t swagger-api-agent:latest .

# 指定版本标签
docker build -t swagger-api-agent:1.0.0 .

# 使用构建参数
docker build --build-arg PYTHON_VERSION=3.11 -t swagger-api-agent:latest .
```

### 多架构构建

```bash
# 构建支持多架构的镜像
docker buildx build --platform linux/amd64,linux/arm64 -t swagger-api-agent:latest .
```

## 🏃 运行模式

### CLI 模式

交互式命令行界面：

```bash
# 基础运行
docker run --rm -it \
  -e DEEPSEEK_API_KEY=your_key \
  swagger-api-agent:latest cli

# 挂载自定义 OpenAPI 文件
docker run --rm -it \
  -e DEEPSEEK_API_KEY=your_key \
  -v /path/to/your/openapi.yaml:/app/openapi.yaml:ro \
  -e OPENAPI_FILE=/app/openapi.yaml \
  swagger-api-agent:latest cli

# 传递额外参数
docker run --rm -it \
  -e DEEPSEEK_API_KEY=your_key \
  swagger-api-agent:latest cli --list-functions
```

### Web API 模式

HTTP API 服务器：

```bash
# 基础运行
docker run --rm -p 5000:5000 \
  -e DEEPSEEK_API_KEY=your_key \
  swagger-api-agent:latest web

# 自定义端口和主机
docker run --rm -p 8080:8080 \
  -e DEEPSEEK_API_KEY=your_key \
  -e FLASK_HOST=0.0.0.0 \
  -e FLASK_PORT=8080 \
  swagger-api-agent:latest web
```

访问：
- API 端点：http://localhost:5000
- 健康检查：http://localhost:5000/health

### Mock 服务器模式

API Mock 服务器：

```bash
# 基础运行
docker run --rm -p 8080:8080 \
  swagger-api-agent:latest mock

# 自定义配置
docker run --rm -p 9000:9000 \
  -e MOCK_HOST=0.0.0.0 \
  -e MOCK_PORT=9000 \
  -v /path/to/custom/openapi.yaml:/app/openapi.yaml:ro \
  -e OPENAPI_FILE=/app/openapi.yaml \
  swagger-api-agent:latest mock
```

访问：
- Mock API：http://localhost:8080
- API 文档：http://localhost:8080/docs
- 健康检查：http://localhost:8080/health

## 🐳 Docker Compose

使用 Docker Compose 同时运行多个服务：

### 基础配置

```bash
# 启动所有服务
export DEEPSEEK_API_KEY=your_api_key
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 自定义配置

创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

或者创建自定义的 `docker-compose.override.yml`：

```yaml
version: '3.8'

services:
  swagger-web:
    ports:
      - "8080:5000"  # 自定义端口映射
    environment:
      - CUSTOM_ENV_VAR=value

  mock-server:
    ports:
      - "9080:8080"  # 自定义端口映射
```

### 生产环境配置

```yaml
version: '3.8'

services:
  swagger-web:
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔧 环境变量

### 必需环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |

### 可选环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_URL` | DeepSeek API URL | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek 模型名称 | `deepseek-chat` |
| `OPENAPI_FILE` | OpenAPI 文件路径 | `/app/examples/example_openapi.yaml` |
| `FLASK_HOST` | Web API 主机地址 | `0.0.0.0` |
| `FLASK_PORT` | Web API 端口 | `5000` |
| `MOCK_HOST` | Mock 服务器主机地址 | `0.0.0.0` |
| `MOCK_PORT` | Mock 服务器端口 | `8080` |

### 环境变量文件

创建 `.env` 文件：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 应用配置
OPENAPI_FILE=/app/examples/example_openapi.yaml
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
MOCK_HOST=0.0.0.0
MOCK_PORT=8080
```

## 💾 数据卷

### 挂载 OpenAPI 文件

```bash
# 挂载单个文件
docker run --rm -it \
  -v /path/to/your/openapi.yaml:/app/custom.yaml:ro \
  -e OPENAPI_FILE=/app/custom.yaml \
  swagger-api-agent:latest

# 挂载整个目录
docker run --rm -it \
  -v /path/to/openapi/files:/app/openapi:ro \
  -e OPENAPI_FILE=/app/openapi/your-api.yaml \
  swagger-api-agent:latest
```

### 持久化日志

```bash
# 创建日志目录
mkdir -p ./logs

# 挂载日志目录
docker run --rm -it \
  -v ./logs:/app/logs \
  swagger-api-agent:latest
```

### 数据目录

```bash
# 持久化应用数据
docker run --rm -it \
  -v swagger-api-data:/app/data \
  swagger-api-agent:latest
```

## 🌐 网络配置

### 端口映射

```bash
# 映射到不同端口
docker run --rm -p 8080:5000 swagger-api-agent:latest web
docker run --rm -p 9080:8080 swagger-api-agent:latest mock

# 映射到特定网络接口
docker run --rm -p 127.0.0.1:5000:5000 swagger-api-agent:latest web
```

### 自定义网络

```bash
# 创建自定义网络
docker network create swagger-network

# 在自定义网络中运行
docker run --rm --network swagger-network \
  --name swagger-web \
  swagger-api-agent:latest web

docker run --rm --network swagger-network \
  --name swagger-mock \
  swagger-api-agent:latest mock
```

### 反向代理

使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        proxy_pass http://localhost:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /mock/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔍 健康检查

### 内置健康检查

镜像内置了健康检查：

```bash
# 查看健康状态
docker ps --format "table {{.Names}}\t{{.Status}}"

# 手动执行健康检查
docker exec container_name curl -f http://localhost:5000/health
```

### 自定义健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```

## 🚨 故障排除

### 常见问题

1. **容器无法启动**
   ```bash
   # 查看日志
   docker logs container_name
   
   # 交互式调试
   docker run --rm -it --entrypoint /bin/bash swagger-api-agent:latest
   ```

2. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :5000
   
   # 使用不同端口
   docker run --rm -p 5001:5000 swagger-api-agent:latest web
   ```

3. **权限问题**
   ```bash
   # 使用特定用户运行
   docker run --rm --user $(id -u):$(id -g) swagger-api-agent:latest
   ```

4. **API 密钥问题**
   ```bash
   # 检查环境变量
   docker run --rm -it swagger-api-agent:latest env | grep DEEPSEEK
   
   # 从文件读取密钥
   docker run --rm -e DEEPSEEK_API_KEY="$(cat api_key.txt)" swagger-api-agent:latest
   ```

### 调试模式

```bash
# 启用调试模式
docker run --rm -it \
  -e DEBUG=1 \
  -e FLASK_ENV=development \
  swagger-api-agent:latest web

# 查看详细日志
docker-compose logs -f --tail=100
```

### 性能监控

```bash
# 查看资源使用情况
docker stats

# 限制资源使用
docker run --rm \
  --memory=512m \
  --cpus=0.5 \
  swagger-api-agent:latest
```

## 📚 更多信息

- [项目 README](../README.md)
- [API 文档](../docs/api.md)
- [配置指南](../docs/configuration.md)
- [开发指南](../docs/development.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进 Docker 支持！
