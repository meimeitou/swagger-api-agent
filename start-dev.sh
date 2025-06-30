#!/bin/bash

# 启动前后端服务的脚本
echo "启动 Swagger API Agent 前后端服务..."

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "错误: Docker 未运行，请启动 Docker 服务"
    exit 1
fi

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "警告: DEEPSEEK_API_KEY 环境变量未设置"
    echo "请设置 DEEPSEEK_API_KEY 环境变量，例如:"
    echo "export DEEPSEEK_API_KEY='your-api-key'"
fi

echo "启动后端服务..."
# 启动后端Docker服务
docker-compose up -d swagger-web

echo "等待后端服务启动..."
sleep 5

# 检查后端服务是否启动成功
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✓ 后端服务启动成功"
else
    echo "✗ 后端服务启动失败，请检查 Docker 日志"
    docker-compose logs swagger-web
    exit 1
fi

echo "启动前端开发服务器..."
# 启动前端开发服务器
cd web
npm run dev &
FRONTEND_PID=$!
cd ..

echo "服务启动完成!"
echo "前端地址: http://localhost:5173"
echo "后端地址: http://localhost:5000"
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap "echo '正在停止服务...'; kill $FRONTEND_PID; docker-compose down; exit 0" INT

# 保持脚本运行
wait $FRONTEND_PID
