#!/bin/bash
set -e

# 函数：显示使用帮助
show_help() {
    echo "Swagger API Agent Docker Container"
    echo ""
    echo "使用方式:"
    echo "  docker run [OPTIONS] swagger-api-agent [COMMAND]"
    echo ""
    echo "可用命令:"
    echo "  cli         启动命令行界面 (默认)"
    echo "  web         启动 Web API 服务器 (端口 5000)"
    echo "  mock        启动 Mock 服务器 (端口 8080)"
    echo "  help        显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  DEEPSEEK_API_KEY     DeepSeek API 密钥 (必需)"
    echo "  DEEPSEEK_API_URL     DeepSeek API URL (可选)"
    echo "  DEEPSEEK_MODEL       DeepSeek 模型名称 (可选)"
    echo "  OPENAPI_FILE         OpenAPI 文件路径 (默认: /app/examples/example_openapi.yaml)"
    echo "  FLASK_HOST           Web API 主机地址 (默认: 0.0.0.0)"
    echo "  FLASK_PORT           Web API 端口 (默认: 5000)"
    echo "  MOCK_HOST            Mock 服务器主机地址 (默认: 0.0.0.0)"
    echo "  MOCK_PORT            Mock 服务器端口 (默认: 8080)"
    echo ""
    echo "示例:"
    echo "  docker run -e DEEPSEEK_API_KEY=your_key swagger-api-agent cli"
    echo "  docker run -p 5000:5000 -e DEEPSEEK_API_KEY=your_key swagger-api-agent web"
    echo "  docker run -p 8080:8080 swagger-api-agent mock"
}

# 检查命令
case "${1:-cli}" in
    cli)
        echo "🚀 启动 Swagger API Agent CLI..."
        exec swagger-api-agent "${@:2}"
        ;;
    web)
        echo "🌐 启动 Web API 服务器在 ${FLASK_HOST}:${FLASK_PORT}..."
        exec swagger-web-api --host "${FLASK_HOST}" --port "${FLASK_PORT}" "${@:2}"
        ;;
    mock)
        echo "🎭 启动 Mock 服务器在 ${MOCK_HOST}:${MOCK_PORT}..."
        exec python /app/scripts/mock_server.py --host "${MOCK_HOST}" --port "${MOCK_PORT}" --openapi "${OPENAPI_FILE}" "${@:2}"
        ;;
    help|--help|-h)
        show_help
        exit 0
        ;;
    *)
        echo "❌ 未知命令: $1"
        show_help
        exit 1
        ;;
esac
