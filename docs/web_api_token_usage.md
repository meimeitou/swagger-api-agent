# Web API Token 配置使用指南

## 概述

Swagger API Agent Web API 现在支持 API Token 认证配置。通过配置 Token，Web API 可以代表客户端自动进行 API 认证，无需在每次请求时手动处理认证。

## 启动配置

### 命令行参数

```bash
python -m src.swagger_api_agent.web_api \
  --host 0.0.0.0 \
  --port 5001 \
  --api-url "http://localhost:8080" \
  --api-token "your_api_token_here" \
  --openapi "examples/example_openapi.yaml"
```

### 参数说明

- `--host`: Web API 服务器监听地址 (默认: 127.0.0.1)
- `--port`: Web API 服务器端口 (默认: 5000)
- `--api-url`: 目标 API 的基础 URL
- `--api-token`: API 认证 Token (Bearer Token)
- `--openapi`: OpenAPI 文档文件路径
- `--debug`: 启用调试模式

### 环境变量方式

也可以通过环境变量配置：

```bash
export API_BASE_URL="http://localhost:8080"
export API_TOKEN="your_api_token_here"
export OPENAPI_FILE="examples/example_openapi.yaml"

python -m src.swagger_api_agent.web_api --host 0.0.0.0 --port 5001
```

## 完整使用示例

### 步骤 1: 启动 Mock API 服务器

```bash
python scripts/mock_server.py --host 0.0.0.0 --port 8080
```

### 步骤 2: 获取认证 Token

```bash
# 获取 API Token
TOKEN=$(curl -s -X POST http://127.0.0.1:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "zhang31@example.com", "password": "password123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "获取到的 Token: $TOKEN"
```

### 步骤 3: 启动 Web API 服务器

```bash
python -m src.swagger_api_agent.web_api \
  --host 0.0.0.0 \
  --port 5001 \
  --api-url "http://localhost:8080" \
  --api-token "$TOKEN"
```

### 步骤 4: 测试 Web API 接口

#### 4.1 健康检查

```bash
curl -X GET http://127.0.0.1:5001/health
```

#### 4.2 获取可用函数

```bash
curl -X GET http://127.0.0.1:5001/api/functions
```

#### 4.3 直接调用函数

```bash
# 获取用户列表
curl -X POST http://127.0.0.1:5001/api/call \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "getUsers",
    "parameters": {
      "page": 1,
      "limit": 3
    }
  }'

# 获取产品列表
curl -X POST http://127.0.0.1:5001/api/call \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "getProducts",
    "parameters": {
      "category": "electronics"
    }
  }'
```

#### 4.4 自然语言处理

```bash
curl -X POST http://127.0.0.1:5001/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "获取前3个用户的信息"
  }'
```

## API 接口说明

### 可用端点

- `GET /health` - 健康检查
- `GET /api/functions` - 获取可用函数列表
- `GET /api/info` - 获取 API 信息
- `POST /api/call` - 直接调用函数
- `POST /api/process` - 处理自然语言输入
- `GET /api/history` - 获取对话历史
- `DELETE /api/history` - 清空对话历史
- `POST /api/auth` - 设置 API 认证

### 响应格式

所有 API 响应都是 JSON 格式，支持 UTF-8 编码，正确显示中文字符：

```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "timestamp": "2025-06-30T11:05:03Z"
}
```

## 认证工作原理

1. **启动时配置**: Web API 服务器启动时，将 `--api-token` 参数传递给内部的 SwaggerAPIAgent
2. **自动认证**: 所有通过 Web API 发起的 API 调用都会自动添加 `Authorization: Bearer {token}` 头
3. **透明处理**: 客户端调用 Web API 时无需关心认证细节，由 Web API 服务器自动处理

## 注意事项

1. **Token 安全**: 不要在日志中记录 Token，确保 Token 的安全性
2. **Token 过期**: Mock 服务器中的 Token 有效期为 1 小时，生产环境中需要实现 Token 刷新机制
3. **错误处理**: 当 Token 过期或无效时，API 调用会返回 401 错误
4. **HTTPS**: 生产环境建议使用 HTTPS 来保护 Token 传输安全

## 测试结果

✅ **Web API 启动成功**: 服务器正常启动，Agent 初始化完成  
✅ **Token 配置生效**: API 调用自动携带认证头  
✅ **函数调用成功**: 通过 Web API 可以成功调用需要认证的 API  
✅ **中文支持完善**: 所有响应正确显示中文字符  

这验证了 Web API Token 认证功能正常工作。
