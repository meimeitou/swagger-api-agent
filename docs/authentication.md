# JWT 认证系统使用指南

## 概述

Swagger API Agent 现在使用 JWT (JSON Web Token) 认证系统来保护 Web 界面和 API 端点。

## 后端配置

### 环境变量

可以通过以下环境变量配置认证参数：

```bash
# Web 界面认证
WEB_API_USERNAME=admin          # 默认: admin
WEB_API_PASSWORD=admin123       # 默认: admin123

# JWT 配置
JWT_SECRET_KEY=your-secret-key  # 默认: your-secret-key-change-this-in-production
JWT_EXPIRATION_HOURS=24         # 默认: 24 小时
```

### 启动后端服务

```bash
# 使用 poetry
poetry run python -m src.swagger_api_agent.web_api --host 0.0.0.0 --port 5000

# 或使用环境变量
WEB_API_USERNAME=myuser WEB_API_PASSWORD=mypass poetry run python -m src.swagger_api_agent.web_api
```

## 前端使用

### 启动前端开发服务器

```bash
cd web
npm install
npm run dev
```

前端服务器将在 http://localhost:5173 启动

### 登录

1. 打开浏览器访问 http://localhost:5173
2. 输入用户名和密码（默认: admin/admin123）
3. 点击登录按钮
4. 登录成功后将自动跳转到主界面

### 功能

- **自动认证**: 所有 API 请求自动包含认证 token
- **Token 管理**: Token 自动存储在浏览器本地存储中
- **过期处理**: Token 过期时自动跳转到登录页面
- **登出功能**: 点击右上角登出按钮可以退出登录

## API 端点

### 认证相关

- `POST /api/login` - 用户登录
  ```json
  {
    "username": "admin",
    "password": "admin123"
  }
  ```

- 响应:
  ```json
  {
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400,
    "message": "登录成功"
  }
  ```

### 受保护的端点

以下端点需要在请求头中包含 JWT token：

```
Authorization: Bearer <token>
```

- `POST /api/process` - 处理自然语言输入
- `POST /api/call` - 直接调用函数
- `GET /api/functions` - 获取可用函数列表
- `GET /api/info` - 获取 API 信息
- `GET /api/history` - 获取对话历史
- `DELETE /api/history` - 清空对话历史

### 公开端点

以下端点无需认证：

- `GET /health` - 健康检查
- `GET /` - API 文档

## 安全建议

1. **生产环境配置**:
   - 更改默认用户名和密码
   - 使用强密码
   - 设置复杂的 JWT 密钥

2. **JWT 密钥**:
   ```bash
   # 生成安全的密钥
   openssl rand -base64 32
   ```

3. **HTTPS**:
   - 生产环境中使用 HTTPS
   - 确保 token 传输安全

## 故障排除

### 401 Unauthorized

- 检查用户名密码是否正确
- 确认 token 是否有效且未过期
- 验证 Authorization 头格式是否正确

### 连接问题

- 确认后端服务器正在运行 (http://localhost:5000)
- 检查前端代理配置 (vite.config.ts)
- 查看浏览器开发者工具的网络选项卡

### Token 过期

- Token 默认24小时过期
- 过期后需要重新登录
- 可以通过 `JWT_EXPIRATION_HOURS` 环境变量调整过期时间
