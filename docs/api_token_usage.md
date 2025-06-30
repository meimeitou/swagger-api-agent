# API Token 配置示例

## 功能说明

Swagger API Agent 现在支持 API Token 认证。当配置了 API Token 时，所有的 API 请求都会自动在请求头中添加 `Authorization: Bearer {token}`。

## 配置方式

### 1. 环境变量方式

```bash
export API_TOKEN="your_api_token_here"
```

### 2. 命令行参数方式

```bash
python -m src.swagger_api_agent.cli --api-token "your_api_token_here"
```

## 使用示例

### 步骤 1: 启动 Mock 服务器

```bash
python scripts/mock_server.py --host 0.0.0.0 --port 8080
```

### 步骤 2: 获取 API Token

```bash
# 获取登录 token
TOKEN=$(curl -s -X POST http://127.0.0.1:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "zhang31@example.com", "password": "password123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: $TOKEN"
```

### 步骤 3: 使用 Token 调用 API

```bash
# 方式 1: 使用命令行参数
python -m src.swagger_api_agent.cli \
  --api-url "http://localhost:8080" \
  --api-token "$TOKEN" \
  --call getUsers \
  --params '{"page": 1, "limit": 3}'

# 方式 2: 使用环境变量
export API_TOKEN="$TOKEN"
python -m src.swagger_api_agent.cli \
  --api-url "http://localhost:8080" \
  --call getUsers \
  --params '{"page": 1, "limit": 3}'
```

### 步骤 4: 验证无 Token 时的行为

```bash
# 不提供 token，应该返回 401 错误
python -m src.swagger_api_agent.cli \
  --api-url "http://localhost:8080" \
  --call getUsers \
  --params '{"page": 1, "limit": 3}'
```

## 配置文件说明

在 `src/swagger_api_agent/config.py` 中添加了以下配置：

```python
# OpenAPI 和 API 基础配置
DEFAULT_API_TOKEN = os.getenv("API_TOKEN")
```

## 代码修改说明

### 1. APICaller 类增强

- 新增 `auth_token` 参数
- 自动在请求头中添加 `Authorization: Bearer {token}`

### 2. SwaggerAPIAgent 类增强

- 支持通过构造函数传递 `api_token`
- 从环境变量和命令行参数加载 token

### 3. CLI 增强

- 新增 `--api-token` 命令行参数
- 支持在命令行中指定认证 token

## 注意事项

1. **安全性**: 不要在代码中硬编码 API Token，应该使用环境变量或安全的配置管理方式
2. **Token 过期**: Mock 服务器中的 token 有效期为 1 小时，过期后需要重新登录获取新 token
3. **可选认证**: 如果不设置 API_TOKEN，则不会添加认证头，这对于不需要认证的 API 是有用的

## 测试结果

✅ **有 Token 时**: API 调用成功，正确返回数据  
❌ **无 Token 时**: API 调用被拒绝，返回 401 未授权错误

这验证了 Token 认证功能正常工作。
