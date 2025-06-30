#!/bin/bash

# Mock服务器启动脚本

echo "🚀 启动OpenAPI Mock服务器..."

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
python3 -c "import flask, flask_cors, yaml, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  缺少依赖，正在安装..."
    pip3 install flask flask-cors pyyaml requests
fi

# 设置默认参数
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8080}
OPENAPI_FILE=${OPENAPI_FILE:-example_openapi.yaml}

# 检查OpenAPI文件是否存在
if [ ! -f "$OPENAPI_FILE" ]; then
    echo "❌ 错误: OpenAPI文件 '$OPENAPI_FILE' 不存在"
    exit 1
fi

echo "📋 配置信息:"
echo "   主机: $HOST"
echo "   端口: $PORT"
echo "   OpenAPI文件: $OPENAPI_FILE"
echo ""

# 启动服务器
python3 mock_server.py --host "$HOST" --port "$PORT" --openapi "$OPENAPI_FILE" "$@"
