#!/bin/bash
# Docker 构建和运行脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目信息
PROJECT_NAME="swagger-api-agent"
VERSION="1.0.0"
IMAGE_NAME="${PROJECT_NAME}:${VERSION}"
LATEST_IMAGE="${PROJECT_NAME}:latest"

# 函数：打印帮助信息
show_help() {
    echo -e "${BLUE}Swagger API Agent Docker 管理脚本${NC}"
    echo ""
    echo "用法: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo -e "${YELLOW}命令:${NC}"
    echo "  build      构建 Docker 镜像"
    echo "  run-cli    运行 CLI 模式"
    echo "  run-web    运行 Web API 服务器"
    echo "  run-mock   运行 Mock 服务器"
    echo "  compose    使用 docker-compose 启动所有服务"
    echo "  stop       停止 docker-compose 服务"
    echo "  clean      清理 Docker 镜像和容器"
    echo "  push       推送镜像到注册表"
    echo "  help       显示此帮助信息"
    echo ""
    echo -e "${YELLOW}选项:${NC}"
    echo "  --api-key KEY    设置 DeepSeek API 密钥"
    echo "  --openapi FILE   指定 OpenAPI 文件路径"
    echo "  --port PORT      指定端口号"
    echo "  --host HOST      指定主机地址"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 build"
    echo "  $0 run-cli --api-key your_key"
    echo "  $0 run-web --port 5000"
    echo "  $0 run-mock --port 8080"
    echo "  $0 compose"
}

# 函数：构建镜像
build_image() {
    echo -e "${BLUE}🔨 构建 Docker 镜像...${NC}"
    
    # 检查 Dockerfile 是否存在
    if [ ! -f "Dockerfile" ]; then
        echo -e "${RED}❌ 未找到 Dockerfile${NC}"
        exit 1
    fi
    
    # 构建镜像
    docker build -t "${IMAGE_NAME}" -t "${LATEST_IMAGE}" .
    
    echo -e "${GREEN}✅ 镜像构建完成: ${IMAGE_NAME}${NC}"
    
    # 显示镜像信息
    echo -e "${BLUE}📋 镜像信息:${NC}"
    docker images "${PROJECT_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
}

# 函数：运行 CLI
run_cli() {
    local api_key=""
    local openapi_file="/app/examples/example_openapi.yaml"
    local extra_args=""
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-key)
                api_key="$2"
                shift 2
                ;;
            --openapi)
                openapi_file="$2"
                shift 2
                ;;
            *)
                extra_args="$extra_args $1"
                shift
                ;;
        esac
    done
    
    local env_args=""
    if [ -n "$api_key" ]; then
        env_args="-e DEEPSEEK_API_KEY=$api_key"
    fi
    
    echo -e "${BLUE}🚀 启动 CLI 模式...${NC}"
    docker run --rm -it \
        $env_args \
        -e OPENAPI_FILE="$openapi_file" \
        -v "$(pwd)/examples:/app/examples:ro" \
        "${LATEST_IMAGE}" cli $extra_args
}

# 函数：运行 Web API
run_web() {
    local api_key=""
    local port="5000"
    local host="0.0.0.0"
    local openapi_file="/app/examples/example_openapi.yaml"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-key)
                api_key="$2"
                shift 2
                ;;
            --port)
                port="$2"
                shift 2
                ;;
            --host)
                host="$2"
                shift 2
                ;;
            --openapi)
                openapi_file="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    local env_args=""
    if [ -n "$api_key" ]; then
        env_args="-e DEEPSEEK_API_KEY=$api_key"
    fi
    
    echo -e "${BLUE}🌐 启动 Web API 服务器在端口 $port...${NC}"
    docker run --rm -it \
        -p "$port:5000" \
        $env_args \
        -e FLASK_HOST="$host" \
        -e FLASK_PORT=5000 \
        -e OPENAPI_FILE="$openapi_file" \
        -v "$(pwd)/examples:/app/examples:ro" \
        "${LATEST_IMAGE}" web
}

# 函数：运行 Mock 服务器
run_mock() {
    local port="8080"
    local host="0.0.0.0"
    local openapi_file="/app/examples/example_openapi.yaml"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                port="$2"
                shift 2
                ;;
            --host)
                host="$2"
                shift 2
                ;;
            --openapi)
                openapi_file="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    echo -e "${BLUE}🎭 启动 Mock 服务器在端口 $port...${NC}"
    docker run --rm -it \
        -p "$port:8080" \
        -e MOCK_HOST="$host" \
        -e MOCK_PORT=8080 \
        -e OPENAPI_FILE="$openapi_file" \
        -v "$(pwd)/examples:/app/examples:ro" \
        "${LATEST_IMAGE}" mock
}

# 函数：使用 docker-compose 启动
compose_up() {
    echo -e "${BLUE}🚀 使用 docker-compose 启动所有服务...${NC}"
    
    # 检查环境变量
    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo -e "${YELLOW}⚠️  未设置 DEEPSEEK_API_KEY 环境变量${NC}"
        echo -e "${YELLOW}   Web API 服务可能无法正常工作${NC}"
    fi
    
    docker-compose up --build -d swagger-web mock-server
    
    echo -e "${GREEN}✅ 服务启动完成${NC}"
    echo -e "${BLUE}📍 Web API: http://localhost:5000${NC}"
    echo -e "${BLUE}📍 Mock Server: http://localhost:8080${NC}"
    echo -e "${BLUE}📍 Mock API 文档: http://localhost:8080/docs${NC}"
    
    # 显示日志
    echo -e "${BLUE}📋 实时日志 (Ctrl+C 退出):${NC}"
    docker-compose logs -f
}

# 函数：停止服务
compose_down() {
    echo -e "${BLUE}🛑 停止 docker-compose 服务...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 函数：清理
clean() {
    echo -e "${BLUE}🧹 清理 Docker 资源...${NC}"
    
    # 停止并删除容器
    docker-compose down --remove-orphans 2>/dev/null || true
    
    # 删除镜像
    docker rmi "${IMAGE_NAME}" "${LATEST_IMAGE}" 2>/dev/null || true
    
    # 清理未使用的资源
    docker system prune -f
    
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 函数：推送镜像
push_image() {
    echo -e "${BLUE}📤 推送镜像到注册表...${NC}"
    
    # 这里需要根据实际的注册表地址修改
    # docker tag "${LATEST_IMAGE}" "your-registry.com/${PROJECT_NAME}:${VERSION}"
    # docker push "your-registry.com/${PROJECT_NAME}:${VERSION}"
    
    echo -e "${YELLOW}⚠️  请先配置 Docker 注册表地址${NC}"
    echo -e "${YELLOW}   修改脚本中的推送逻辑${NC}"
}

# 主函数
main() {
    case "${1:-help}" in
        build)
            build_image
            ;;
        run-cli)
            shift
            run_cli "$@"
            ;;
        run-web)
            shift
            run_web "$@"
            ;;
        run-mock)
            shift
            run_mock "$@"
            ;;
        compose)
            compose_up
            ;;
        stop)
            compose_down
            ;;
        clean)
            clean
            ;;
        push)
            push_image
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装或未在 PATH 中${NC}"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠️  docker-compose 未安装，部分功能可能不可用${NC}"
fi

# 执行主函数
main "$@"
